# M-08 — Conectar Fuentes Declaradas con ESCO

> **Estado:** ⬜ No iniciado  
> **Prioridad:** ALTO  
> **Fase:** -1, Nivel 2  
> **Alcance:** A — Conector puro (sin generación de nuevos grupos de equivalencia)  
> **Prerequisito de:** M-08b (equivalencias), M-13 (Tipo C), M-14 (retroalimentar extractor)

---

## Problema que resuelve

El sistema extrae cuatro fuentes de competencias declaradas por las
empresas en cada oferta. Ninguna llega a ESCO ni al Perfil Argentino:

```
skills_tecnicas_list   322.222 valores   10.979 únicos  → texto libre
tecnologias_list        39.697 valores    8.707 únicos  → texto libre
herramientas_list       22.716 valores    6.717 únicos  → texto libre
soft_skills_list        ~31K ofertas     22.082 únicos  → texto libre
─────────────────────────────────────────────────────────────────────
Total combinado        ~384.635 valores  23.157 únicos  → nunca comparados con ESCO
```

Estas son competencias que las empresas declaran explícitamente —
ground truth del mercado — y el sistema no puede usarlas para el
Perfil Argentino ni para análisis de skills.

**El diagnóstico previo mostró:**
- `skills_tecnicas_list` contiene labels casi textuales de ESCO
  ("trabajar en equipo", "gestionar el inventario") — matchearía con
  scores altos
- `tecnologias_list` y `herramientas_list` tienen nombres propios
  (SAP, Excel, Python) — matcheo parcial
- `soft_skills_list` tiene frases largas con múltiples skills pegadas
  — necesita split previo

---

## Decisiones de diseño

### Procesamiento separado por fuente (Opción B)

Las 4 fuentes tienen naturaleza distinta. Se procesan en pasos
separados para mantener trazabilidad de origen. El campo
`skill_tipo_fuente` en `ofertas_esco_skills_detalle` ya soporta
valores libres — se agregan 4 nuevos:

```
'skills_nlp_declarada'   ← de skills_tecnicas_list
'tecnologia_declarada'   ← de tecnologias_list
'herramienta_declarada'  ← de herramientas_list
'soft_skill_declarada'   ← de soft_skills_list
```

### Integración con equivalencias

El extractor ya carga `equiv_lookup` en `__init__` como singleton.
M-08 usa el mismo mecanismo que `extract_skills()` — después de
encontrar un match, busca el representante canónico del grupo de
equivalencia si existe.

No se generan nuevos grupos de equivalencia en este spec — eso es
M-08b.

### Punto de inserción en el pipeline

M-08 corre como un paso nuevo después de `extract_skills_dual()` en
`match_and_persist()`. No modifica el procesamiento de tareas
existente — es estrictamente aditivo.

```
match_and_persist()
    → extract_skills_dual()          ← sin cambios
    → extract_declared_skills()      ← NUEVO (M-08)
    → merge_and_deduplicate()        ← NUEVO (M-08)
    → save_skills_detalle()          ← sin cambios, recibe el merge
```

### Deduplicación entre fuentes

Una skill puede aparecer en múltiples fuentes para la misma oferta
("Excel" en tecnologias_list y herramientas_list). Después de
procesar las 4 fuentes, se deduplica por grupo de equivalencia antes
de persistir. Si una skill ya está en `ofertas_esco_skills_detalle`
para esa oferta (vino de tareas), no se duplica — se registra el
origen adicional en un campo separado.

### Umbral

Se mantiene el umbral actual de 0.40. No se baja para M-08 — la
decisión de bajar el umbral requiere análisis separado con datos
limpios (decisión tomada al analizar failures).

---

## Componentes

### 1. Parser normalizado por fuente

**Archivo:** `database/skills_implicit_extractor.py` — método nuevo
`_parse_declared_source(campo, texto)`

Convierte cualquier formato de entrada a `List[str]` limpia:

```
skills_tecnicas_list:
    JSON array → parsear con json.loads()
    semicolon  → split(';')
    comma      → split(',')
    texto libre → split(';') con fallback a split(',')
    → limpiar cada item: strip, lowercase, eliminar vacíos
    → max 15 items (límite existente de _limpiar_skills())

tecnologias_list:
    semicolon (64%) → split(';')
    texto libre (36%) → split(';') con fallback
    → NO lowercase — nombres propios (SAP, Excel, Python)

herramientas_list:
    semicolon (47%) → split(';')
    texto libre (53%) → split(';') con fallback
    → NO lowercase — nombres propios

soft_skills_list:
    comma (93%) → split(',')
    → split adicional por ' y ' para frases compuestas
      "liderazgo y trabajo en equipo" → ["liderazgo", "trabajo en equipo"]
    → lowercase
    → max 20 items (más que skills técnicas porque son más granulares)
```

### 2. Extractor de fuentes declaradas

**Archivo:** `database/skills_implicit_extractor.py` — método nuevo
`extract_declared_skills(oferta_nlp, run_id=None)`

Para cada una de las 4 fuentes:
1. Llamar a `_parse_declared_source()` → lista de strings
2. Para cada item de la lista:
   - Generar embedding con BGE-M3
   - Calcular coseno contra los 14.247 embeddings ESCO
   - Tomar top 1 (no top 3 — las declaradas son más específicas)
   - Si score >= 0.40 → skill matcheada
   - Si score < 0.40 → registrar en `skills_extraction_failures`
     con `tarea_origen` = nombre de la fuente
3. Aplicar equivalencias al resultado
4. Retornar dict con 4 listas:
   ```python
   {
     'skills_nlp_declarada': [...],
     'tecnologia_declarada': [...],
     'herramienta_declarada': [...],
     'soft_skill_declarada': [...]
   }
   ```

**¿Por qué top 1 en vez de top 3?**
Las fuentes declaradas son términos específicos ("Excel", "liderazgo")
— no frases descriptivas de tareas. El top 1 es el match más
relevante. Top 3 introduciría skills marginalmente relacionadas con
mayor probabilidad que en tareas.

### 3. Merge y deduplicación

**Archivo:** `database/match_ofertas_v3.py` — método nuevo en
`match_and_persist()`

Después de `extract_skills_dual()` y `extract_declared_skills()`:

1. Tomar las skills de tareas (resultado existente)
2. Para cada skill de las 4 fuentes declaradas:
   - Si su `equiv_group` ya está en las skills de tareas → skip
   - Si no está → agregar con su `skill_tipo_fuente` correspondiente
3. El resultado mergeado pasa a `save_skills_detalle()` sin cambios

### 4. Registro de failures de fuentes declaradas

Las skills declaradas que no superan el umbral 0.40 se registran en
`skills_extraction_failures` con el campo `tarea_origen` indicando
la fuente:

```
'skills_nlp_declarada_failure'
'tecnologia_declarada_failure'
'herramienta_declarada_failure'
'soft_skill_declarada_failure'
```

Esto permite analizar separadamente qué fuente tiene más pérdida y
por qué.

---

## Impacto esperado

Con base en el diagnóstico previo:

```
skills_tecnicas_list → labels casi ESCO → tasa de éxito estimada: 70-80%
soft_skills_list     → frases descriptivas → tasa estimada: 60-70%
tecnologias_list     → nombres propios → tasa estimada: 40-60%
herramientas_list    → nombres propios → tasa estimada: 40-60%
```

Las ~42.000 ofertas que tienen estas listas van a tener más skills en
`ofertas_esco_skills_detalle`. Las ofertas que hoy tienen 0 skills
de tareas pero tienen skills declaradas van a poder alimentar el
Perfil Argentino por primera vez.

---

## Lo que NO hace este spec

- No baja el umbral de 0.40
- No genera nuevos grupos de equivalencia (M-08b)
- No modifica el procesamiento de tareas existente
- No conecta con el Perfil Argentino directamente —
  eso ocurre automáticamente porque ya usa ofertas_skills
- No procesa ofertas históricas en batch — las declaradas se procesan
  en el próximo run normal de cada oferta

---

## Tests requeridos

```
tests/test_m08_declared_skills.py

Unitarios — Parser:
test_parse_json_array()
    → "[\"Excel\", \"SAP\"]" → ["Excel", "SAP"]

test_parse_semicolon()
    → "Excel; SAP; Power BI" → ["Excel", "SAP", "Power BI"]

test_parse_comma()
    → "liderazgo, trabajo en equipo" → ["liderazgo", "trabajo en equipo"]

test_parse_soft_skills_split_y()
    → "liderazgo y capacidad de negociación" 
    → ["liderazgo", "capacidad de negociación"]

test_parse_max_items()
    → lista con 20 items → respeta límite de 15 para skills técnicas

test_parse_vacio()
    → None, "", "[]" → [] sin excepción

Unitarios — Extractor:
test_extract_declared_retorna_4_fuentes()
    → dado oferta_nlp con las 4 listas populadas
    → retorna dict con 4 keys

test_skill_matcheada_usa_equivalencia()
    → skill que matchea URI_B (variante)
    → resultado usa label del representante canónico

test_skill_bajo_umbral_va_a_failures()
    → skill con score < 0.40
    → aparece en skills_extraction_failures
    → tarea_origen indica la fuente correcta

test_top_1_no_top_3()
    → verificar que se toma solo el mejor match por item

Integración:
test_merge_deduplica_con_tareas()
    → skill que ya vino de tareas no se duplica
    → skill nueva de declaradas sí se agrega

test_skill_tipo_fuente_correcto()
    → cada skill en ofertas_esco_skills_detalle
    → tiene el skill_tipo_fuente correcto por origen

test_pipeline_completo_con_m08()
    → correr match_and_persist() sobre oferta real
    → verificar que ofertas_esco_skills_detalle tiene
      skills de tareas + skills de declaradas
    → verificar que no hay duplicados por equiv_group

Regresión:
test_tareas_no_afectadas()
    → skills de tareas existentes tienen mismo resultado
    → con y sin M-08 activo

test_no_duplicados_en_detalle()
    → ninguna oferta tiene el mismo equiv_group
      dos veces en ofertas_esco_skills_detalle
```

---

## Criterio de done

```
□ _parse_declared_source() implementado para los 4 formatos
□ extract_declared_skills() implementado con top_k=1
□ Equivalencias aplicadas en extract_declared_skills()
□ Failures de declaradas registrados en skills_extraction_failures
  con tarea_origen diferenciado por fuente
□ merge_and_deduplicate() implementado en match_and_persist()
□ save_skills_detalle() recibe el merge sin cambios
□ 4 nuevos valores de skill_tipo_fuente en producción
□ 15 tests pasando
□ Correr pipeline sobre 10 ofertas reales → verificar:
  - skills de tareas intactas (regresión)
  - skills declaradas presentes con skill_tipo_fuente correcto
  - no hay duplicados por equiv_group
  - failures de declaradas en skills_extraction_failures
□ Verificar que Perfil Argentino recibe más datos
  (recalcular_emergentes() detecta nuevas candidatas)
□ No regresión: 39 tests Python existentes en verde
□ No regresión: 933 tests React en verde
```

---

## Secuencia de implementación sugerida

```
1. _parse_declared_source() + tests unitarios del parser
2. extract_declared_skills() con BGE-M3 + equivalencias
3. Tests unitarios del extractor
4. Integración en match_and_persist() + merge
5. Tests de integración
6. Smoke test sobre ofertas reales
7. Tests de regresión
8. Commit
```
