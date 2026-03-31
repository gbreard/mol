# M-08 — Conectar Fuentes Declaradas con ESCO (v2)

> **Estado:** ⬜ No iniciado
> **Prioridad:** ALTO
> **Fase:** -1, Nivel 2
> **Alcance:** A — Conector puro (sin generación de nuevos grupos de equivalencia)
> **Prerequisito de:** M-08b (equivalencias), M-13 (Tipo C), M-14 (retroalimentar extractor)
> **Supersede:** SPEC_M08_DECLARED_SKILLS.md (v1, corregida por ajustes en query SQL y punto de inserción)

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

## Correcciones respecto a v1

La v1 tenía 2 problemas identificados al verificar contra el código real:

1. **Query SQL no trae las 4 listas:** `run_matching_pipeline()` construye
   `oferta_nlp` con solo 6 campos (titulo_limpio, titulo, tareas_explicitas,
   area_funcional, nivel_seniority, sector_empresa). Las 4 listas declaradas
   no se incluyen en el SELECT ni en el dict. Hay 3 queries a modificar
   (líneas 1806, 1817, 1830) y el dict constructor (línea 1890).

2. **Punto de inserción incorrecto:** La v1 decía "después de
   extract_skills_dual()". Pero en el código real hay 3 pasos entre la
   extracción y la persistencia de skills: match de ocupación, categorización
   L1/L2, y save_matching_result. El punto correcto es después de match()
   y antes de categorize_batch(), para que las skills declaradas también
   reciban categorías L1/L2.

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

M-08 se inserta en `match_and_persist()` después del matching de
ocupación y antes de la categorización L1/L2. Esto garantiza que
las skills declaradas reciban categorías igual que las de tareas.

```
match_and_persist()
    1. extract_skills_dual()           ← sin cambios (skills de tareas)
       _persist_skill_failures()       ← M-06 sin cambios
    2. self.match(oferta_nlp)          ← sin cambios (matching ISCO)
    3. extract_declared_skills()       ← NUEVO (M-08)
    4. merge skills + declared         ← NUEVO (M-08)
    5. categorize_batch()              ← sin cambios, ahora incluye declaradas
    6. save_matching_result()          ← sin cambios
    7. save_skills_detalle()           ← sin cambios, recibe el merge
```

### Datos disponibles en oferta_nlp

**Actualmente** `run_matching_pipeline()` construye `oferta_nlp` con:
```python
oferta_nlp = {
    'titulo_limpio': ..., 'titulo': ..., 'tareas_explicitas': ...,
    'area_funcional': ..., 'nivel_seniority': ..., 'sector_empresa': ...
}
```

**Hay que agregar** (query SQL + dict):
```python
oferta_nlp = {
    ...,  # campos existentes
    'skills_tecnicas_list': oferta['skills_tecnicas_list'] or '',
    'tecnologias_list': oferta['tecnologias_list'] or '',
    'herramientas_list': oferta['herramientas_list'] or '',
    'soft_skills_list': oferta['soft_skills_list'] or '',
}
```

Los 3 queries en `run_matching_pipeline()` (líneas 1806, 1817, 1830)
necesitan agregar esos 4 campos al SELECT.

### Deduplicación entre fuentes

Una skill puede aparecer en múltiples fuentes para la misma oferta
("Excel" en tecnologias_list y herramientas_list). Después de
procesar las 4 fuentes, se deduplica por grupo de equivalencia antes
de mergear con las skills de tareas. Si una skill ya está en las
skills de tareas (vino de extract_skills_dual), no se duplica.

### Umbral

Se mantiene el umbral actual de 0.40. No se baja para M-08 — la
decisión de bajar el umbral requiere análisis separado con datos
limpios.

---

## Componentes

### 1. Modificar queries en run_matching_pipeline()

**Archivo:** `database/match_ofertas_v3.py`

**3 queries** (líneas 1806, 1817, 1830) — agregar al SELECT:
```sql
n.skills_tecnicas_list, n.tecnologias_list,
n.herramientas_list, n.soft_skills_list
```

**Dict constructor** (línea 1890) — agregar 4 campos:
```python
'skills_tecnicas_list': oferta['skills_tecnicas_list'] or '',
'tecnologias_list': oferta['tecnologias_list'] or '',
'herramientas_list': oferta['herramientas_list'] or '',
'soft_skills_list': oferta['soft_skills_list'] or '',
```

### 2. Parser normalizado por fuente

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
    → max 15 items

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
    → max 20 items
```

### 3. Extractor de fuentes declaradas

**Archivo:** `database/skills_implicit_extractor.py` — método nuevo
`extract_declared_skills(oferta_nlp, track_failures=False)`

Para cada una de las 4 fuentes:
1. Llamar a `_parse_declared_source()` → lista de strings
2. Para cada item de la lista:
   - Generar embedding con BGE-M3 (`self.model.encode()`)
   - Calcular coseno contra los 14,247 embeddings ESCO (`np.dot()`)
   - Tomar top 1 (no top 3 — las declaradas son más específicas)
   - Aplicar `round(score, 4)` antes de comparar (fix del bug de redondeo)
   - Si score >= 0.40 → skill matcheada, aplicar equivalencias
   - Si score < 0.40 y track_failures → acumular en lista de failures
3. Retornar tupla:
   ```python
   (declared_skills, declared_failures)
   ```
   Donde `declared_skills` es lista de dicts con `skill_tipo_fuente`
   diferenciado por origen, y `declared_failures` es lista para M-06.

**¿Por qué top 1 en vez de top 3?**
Las fuentes declaradas son términos específicos ("Excel", "liderazgo")
— no frases descriptivas de tareas. El top 1 es el match más
relevante. Top 3 introduciría skills marginalmente relacionadas.

### 4. Integración en match_and_persist()

**Archivo:** `database/match_ofertas_v3.py`

Después del matching de ocupación (paso 2) y antes de categorización
(paso 5 actual), agregar:

```python
# 3. M-08: Extraer skills de fuentes declaradas
declared_result = self.skills_extractor.extract_declared_skills(
    oferta_nlp, track_failures=True
)
declared_skills, declared_failures = declared_result

# M-06: Persistir failures de declaradas
if declared_failures:
    self._persist_skill_failures(id_oferta, run_id, declared_failures)

# 4. Merge: skills de tareas + declaradas (dedup por equiv_group)
existing_keys = set()
for s in skills_extracted:
    uri = s.get("skill_uri", "")
    group = self.skills_extractor.equiv_lookup.get(uri, uri)
    existing_keys.add(group)

for s in declared_skills:
    uri = s.get("skill_uri", "")
    group = self.skills_extractor.equiv_lookup.get(uri, uri)
    if group not in existing_keys:
        existing_keys.add(group)
        skills_extracted.append(s)
```

El merge usa `equiv_group` como clave de deduplicación. Si una
skill declarada ya apareció en las skills de tareas (mismo grupo de
equivalencia), se descarta. Si es nueva, se agrega con su
`skill_tipo_fuente` diferenciado.

### 5. Registro de failures de fuentes declaradas

Las skills declaradas que no superan el umbral 0.40 se registran en
`skills_extraction_failures` con `tarea_origen` indicando la fuente:

```
'skills_nlp_declarada'
'tecnologia_declarada'
'herramienta_declarada'
'soft_skill_declarada'
```

---

## Impacto esperado

Con base en el diagnóstico previo:

```
skills_tecnicas_list → labels casi ESCO → tasa de éxito estimada: 70-80%
soft_skills_list     → frases descriptivas → tasa estimada: 60-70%
tecnologias_list     → nombres propios → tasa estimada: 40-60%
herramientas_list    → nombres propios → tasa estimada: 40-60%
```

Las ~42,000 ofertas que tienen estas listas van a tener más skills en
`ofertas_esco_skills_detalle`. Las ofertas que hoy tienen 0 skills
de tareas pero tienen skills declaradas van a poder alimentar el
Perfil Argentino por primera vez.

---

## Cambios por archivo

```
database/match_ofertas_v3.py
    → 3 queries: agregar 4 campos al SELECT
    → dict oferta_nlp: agregar 4 campos
    → match_and_persist(): agregar extract_declared + merge + persist failures

database/skills_implicit_extractor.py
    → _parse_declared_source(): parser por formato
    → extract_declared_skills(): embedding + coseno + top 1 + equivalencias

tests/test_m08_declared_skills.py
    → 6 unitarios parser + 4 unitarios extractor + 3 integración + 2 regresión
```

---

## Estrategia de Tests

### Estructura de archivos

```
tests/test_m08_declared_skills.py     ← unitarios + integración + regresión
```

Usa el mismo fixture `MockExtractor` de M-06 (mock de BGE-M3 con
embeddings controlados). No necesita BD real para unitarios — SQLite
en memoria para integración.

### Fixtures

```
fixture: extractor_m08
    → Mismo mock de M-06 (SkillsImplicitExtractor con embeddings de dim 32)
    → Agregar equiv_lookup mock: {"http://esco/skill/001": "EQ-001"}
    → Agregar equiv_groups mock: {"EQ-001": {"label": "instalar cableado"}}
    → Permite controlar qué matchea y qué no

fixture: oferta_nlp_completa
    → Dict con los 10 campos (6 existentes + 4 nuevos):
    {
      "titulo_limpio": "Técnico electromecánico",
      "tareas_explicitas": "instalar cableado industrial; mantener equipos",
      "area_funcional": "mantenimiento",
      "nivel_seniority": "semi_senior",
      "sector_empresa": "industria",
      "skills_tecnicas_list": '["trabajar en equipo", "gestionar inventario"]',
      "tecnologias_list": "SAP; Excel; Power BI",
      "herramientas_list": "AutoCAD; herramientas manuales",
      "soft_skills_list": "liderazgo, comunicación, trabajo en equipo"
    }

fixture: db_m08 (integración)
    → SQLite en memoria con:
      ofertas_esco_skills_detalle (vacía)
      skills_extraction_failures (vacía)
      ofertas_esco_matching (vacía)
```

---

### Nivel 1 — Unitarios: Parser

```
test_parse_json_array
    Tipo: unitario
    Qué verifica:
      - '["Excel", "SAP", "Power BI"]' → ["Excel", "SAP", "Power BI"]
    Input: JSON array string, campo="skills_tecnicas_list"
    Output: lista de 3 strings

test_parse_semicolon
    Tipo: unitario
    Qué verifica:
      - "Excel; SAP; Power BI" → ["Excel", "SAP", "Power BI"]
    Input: semicolon string, campo="tecnologias_list"
    Output: lista de 3 strings, nombres propios preservados (no lowercase)

test_parse_comma_soft_skills
    Tipo: unitario
    Qué verifica:
      - "liderazgo, trabajo en equipo, comunicación"
        → ["liderazgo", "trabajo en equipo", "comunicación"]
    Input: comma string, campo="soft_skills_list"
    Output: lista de 3, lowercase

test_parse_soft_skills_split_y
    Tipo: unitario
    Qué verifica:
      - "liderazgo y capacidad de negociación"
        → ["liderazgo", "capacidad de negociación"]
    Input: string con ' y ', campo="soft_skills_list"
    Output: 2 items separados

test_parse_max_items
    Tipo: unitario
    Qué verifica:
      - Lista con 25 items → max 15 para skills_tecnicas, max 20 para soft_skills
    Input: string largo con muchos items
    Output: truncado al max correspondiente

test_parse_vacio
    Tipo: unitario
    Qué verifica:
      - None → []
      - "" → []
      - "[]" → []
      - "null" → []
    Input: valores vacíos/nulos
    Output: lista vacía, sin excepción

test_parse_mixto_json_con_objetos
    Tipo: unitario
    Qué verifica:
      - '[{"valor": "Excel"}, "SAP"]' → ["Excel", "SAP"]
      - Maneja JSON arrays con mix de strings y objetos (formato legacy)
    Input: JSON con objetos
    Output: extrae valores correctamente

test_parse_tecnologias_no_lowercase
    Tipo: unitario
    Qué verifica:
      - "SAP; Python; AWS" → ["SAP", "Python", "AWS"] (no "sap", "python")
    Input: tecnologias con nombres propios
    Output: case preservado
```

---

### Nivel 2 — Unitarios: Extractor

```
test_extract_declared_retorna_4_fuentes
    Tipo: unitario
    Qué verifica:
      - Dado oferta_nlp con las 4 listas populadas
      - Retorna tupla (declared_skills, declared_failures)
      - declared_skills tiene items con skill_tipo_fuente diferenciado
    Input: extractor_m08 + oferta_nlp_completa
    Output: tupla con listas no vacías

test_skill_tipo_fuente_correcto
    Tipo: unitario
    Qué verifica:
      - Skills de skills_tecnicas_list → skill_tipo_fuente = 'skills_nlp_declarada'
      - Skills de tecnologias_list → 'tecnologia_declarada'
      - Skills de herramientas_list → 'herramienta_declarada'
      - Skills de soft_skills_list → 'soft_skill_declarada'
    Input: extractor_m08 + oferta con 1 item por fuente (controlado)
    Output: cada skill tiene el tipo correcto

test_skill_matcheada_usa_equivalencia
    Tipo: unitario
    Qué verifica:
      - Skill que matchea URI en equiv_lookup
      - Resultado usa label del representante canónico
      - Deduplicación por equiv_group funciona
    Input: extractor_m08 con equiv_lookup configurado
    Output: label del representante, no del match directo

test_top_1_no_top_3
    Tipo: unitario
    Qué verifica:
      - Por cada item declarado, solo se retorna 1 skill ESCO (la mejor)
      - No 3 como en extract_skills() de tareas
    Input: extractor_m08 + item que matchea múltiples skills
    Output: exactamente 1 skill por item de entrada (que supere umbral)

test_failures_diferenciados_por_fuente
    Tipo: unitario
    Qué verifica:
      - Skills bajo umbral van a failures con tarea_origen correcto:
        'skills_nlp_declarada', 'tecnologia_declarada', etc.
    Input: extractor_m08 + items que no matchean por fuente
    Output: cada failure tiene tarea_origen de su fuente

test_fuente_vacia_no_rompe
    Tipo: unitario
    Qué verifica:
      - oferta_nlp con tecnologias_list="" y herramientas_list=None
      - No lanza excepción, retorna skills de las fuentes que sí tienen datos
    Input: oferta_nlp parcialmente vacía
    Output: tupla válida, sin error

test_track_failures_false_no_retorna_failures
    Tipo: unitario
    Qué verifica:
      - Con track_failures=False, declared_failures es lista vacía
    Input: extractor_m08 + oferta con items que fallan
    Output: failures = []
```

---

### Nivel 3 — Integración

```
test_merge_deduplica_con_tareas
    Tipo: integración
    Qué verifica:
      - Skill que ya vino de tareas (extract_skills_dual) no se duplica
      - Skill nueva de declaradas sí se agrega
      - Deduplicación usa equiv_group, no label textual
    Datos: mock extractor que retorna skill "instalar cableado" de tareas
           + oferta_nlp con skills_tecnicas_list que contiene lo mismo
    Verificación: ofertas_esco_skills_detalle tiene 1 entrada, no 2

test_pipeline_completo_agrega_declaradas
    Tipo: integración (mock BD)
    Qué verifica:
      - match_and_persist() con oferta que tiene tareas + declaradas
      - ofertas_esco_skills_detalle tiene skills de ambas fuentes
      - skill_tipo_fuente tiene valores de tareas ('tarea', 'titulo')
        Y de declaradas ('skills_nlp_declarada', 'tecnologia_declarada')
    Datos: db_m08 + extractor_m08 + oferta_nlp_completa
    Verificación: SELECT skill_tipo_fuente, COUNT(*) GROUP BY 1

test_failures_declaradas_en_bd
    Tipo: integración (mock BD)
    Qué verifica:
      - Items declarados bajo umbral aparecen en skills_extraction_failures
      - tarea_origen distingue fuente declarada
      - run_id presente si se pasó
    Datos: db_m08 + extractor_m08 + oferta con items que no matchean
    Verificación: SELECT * FROM skills_extraction_failures WHERE tarea_origen LIKE '%declarada%'

test_categorias_l1_l2_en_declaradas
    Tipo: integración
    Qué verifica:
      - Las skills declaradas pasan por categorize_batch() igual que las de tareas
      - Tienen L1/L2 asignados en el resultado
    Datos: oferta con declaradas que matchean
    Verificación: source_classification no es NULL en skills declaradas
```

---

### Nivel 4 — Regresión

```
test_tareas_no_afectadas
    Tipo: regresión
    Qué verifica:
      - Skills de tareas existentes tienen mismo resultado con y sin M-08
      - Misma cantidad, mismos labels, mismos scores
    Datos: oferta procesada con match_and_persist()
    Verificación: comparar skills con skill_tipo_fuente IN ('tarea', 'titulo', 'semantico')
                  antes y después de M-08

test_no_duplicados_en_detalle
    Tipo: regresión
    Qué verifica:
      - Ninguna oferta tiene el mismo equiv_group dos veces
      - Verificar con GROUP BY id_oferta, skill_uri HAVING COUNT > 1
    Datos: oferta con overlap entre tareas y declaradas
    Verificación: query de duplicados retorna 0 filas

test_match_result_no_cambia
    Tipo: regresión
    Qué verifica:
      - El MatchResult (isco_code, score, metodo) no cambia por M-08
      - M-08 agrega skills pero no afecta matching de ocupación
    Datos: oferta con y sin M-08
    Verificación: mismo isco_code, mismo score

test_oferta_sin_declaradas_igual_que_antes
    Tipo: regresión
    Qué verifica:
      - Oferta con las 4 listas vacías produce exactamente el mismo resultado
      - M-08 no agrega overhead ni cambia nada si no hay datos
    Datos: oferta_nlp con skills_tecnicas_list="", tecnologias_list=None, etc.
    Verificación: resultado idéntico al de antes de M-08
```

---

### Casos borde no cubiertos en v1

```
test_skill_tecnica_ya_es_label_esco
    Tipo: caso borde
    Qué verifica:
      - "trabajar en equipo" (ya es label ESCO textual) matchea con score > 0.90
      - Se registra correctamente como 'skills_nlp_declarada'
    Razón: el top de skills_tecnicas_list tiene labels casi ESCO.
    Si el match es 0.99, no debería ser failure.

test_tecnologia_nombre_propio_corto
    Tipo: caso borde
    Qué verifica:
      - "R" (lenguaje de programación) como ítem de tecnologias_list
      - No crashea por string muy corto
      - Puede no matchear (score bajo) → va a failures correctamente
    Razón: items de 1-2 caracteres son comunes en tecnologías

test_soft_skill_frase_larga_con_multiples
    Tipo: caso borde
    Qué verifica:
      - "capacidad de organización, planificacion, atencion al detalle, autonomia"
        → split produce 4 items, cada uno se procesa independientemente
    Razón: 93% de soft_skills_list viene separada por coma, con múltiples
    skills en un solo campo

test_json_malformado
    Tipo: caso borde
    Qué verifica:
      - skills_tecnicas_list = "[Excel, SAP]" (JSON inválido sin comillas)
      - Fallback a split por comma → ["[Excel", "SAP]"] → limpia brackets
    Razón: datos legacy del LLM con formato inconsistente

test_item_duplicado_en_misma_fuente
    Tipo: caso borde
    Qué verifica:
      - tecnologias_list = "Excel; SAP; Excel" → dedup antes de embeddear
      - No genera 2 embeddings para el mismo item
    Razón: optimización de performance (evitar embeddings redundantes)
```

---

### Implementabilidad con infraestructura existente

| Aspecto | Estado |
|---------|--------|
| Mock extractor (BGE-M3) | ✅ Existe en `tests/test_m06_skills_failures.py` — reusar |
| Mock equiv_lookup | ✅ Ya incluido en fixture de M-06 |
| SQLite en memoria | ✅ Usado en `tests/test_m06_integration.py` |
| `_persist_skill_failures()` | ✅ Ya existe en MatcherV3 (M-06) |
| Supabase mock (MSW) | ✅ No necesario — M-08 es solo SQLite local |
| `SkillCategorizer` mock | ⚠️ Necesita mock para test de L1/L2 — importar con try/except |

**Todos los tests son implementables** con la infraestructura existente.
El mock extractor de M-06 se reutiliza directamente. Solo hay que
agregar `_parse_declared_source()` al mock si se quiere testear
aislado, pero al ser un método del extractor real, se puede testear
directamente sin mock.

---

## Criterio de done

```
□ 3 queries en run_matching_pipeline() actualizados con 4 campos nuevos
□ Dict oferta_nlp incluye las 4 listas declaradas
□ _parse_declared_source() implementado para los 4 formatos
□ extract_declared_skills() implementado con top_k=1 + equivalencias
□ Integración en match_and_persist() después de match(), antes de categorize
□ Merge con deduplicación por equiv_group
□ Failures de declaradas registrados con tarea_origen diferenciado
□ 4 nuevos valores de skill_tipo_fuente en producción
□ 23 tests pasando (8 parser + 7 extractor + 4 integración + 4 regresión)
□ Correr pipeline sobre 10 ofertas reales → verificar:
  - skills de tareas intactas (regresión)
  - skills declaradas presentes con skill_tipo_fuente correcto
  - no hay duplicados por equiv_group
  - failures de declaradas en skills_extraction_failures
□ No regresión: tests Python existentes (39+) en verde
□ No regresión: tests React existentes (933+) en verde
```

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

## Secuencia de implementación sugerida

```
1. Modificar queries + dict en run_matching_pipeline()
2. _parse_declared_source() + tests unitarios del parser
3. extract_declared_skills() con BGE-M3 + equivalencias + failures
4. Tests unitarios del extractor
5. Integración en match_and_persist() + merge + dedup
6. Tests de integración
7. Smoke test sobre ofertas reales
8. Tests de regresión
9. Commit
```
