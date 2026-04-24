# SPEC: Corrección sistémica de clasificación de operarios

**Fecha:** 2026-04-24
**Autores del feedback:** Cynthia Vázquez, Diego Schleser
**Issues fuente:** 32 pendientes Cynthia + 8 pendientes Diego (23-24/4)
**Estado:** Draft — pendiente aprobación antes de implementar

---

## 1. Contexto y problema

El matcher clasifica **todas las ofertas de operarios (excepto alimentos) con ISCO 8160 ("operario de prensado de fruta")** como default catch-all. Este ISCO se dispara vía diccionario argentino porque no hay reglas que distingan tipos de operario, y el semantic matcher cae ahí por la palabra "operario".

**18 ofertas confirmadas con este patrón** (11 de Cynthia + 8 de Diego, con 1 compartida).

### Por qué importa

- 8160 es para prensado de fruta específicamente (ESCO label literal).
- Afecta todas las ocupaciones operarias: CNC, metalúrgica, plástico, envasado, logística, armas, manufactura general, despacho.
- **Alcance no limitado a 18 ofertas**: toda oferta nueva con título "Operario X" cae en 8160 si no hay regla específica.
- Además genera efectos secundarios:
  - Skills irrelevantes (semantic matcher inventa dominios al azar cuando no hay pistas)
  - Sector "Otro" (el NLP no identifica el rubro real)
  - Experiencia 0 (la regla de experiencia actual no captura todos los patrones)

### Efectos secundarios detectados

1. **Skills ruido en descripciones cortas** — ejemplo oferta 1118219210 (Operario bebidas) tiene asignadas 20 skills random como "controlar pacientes de oncología aguda", "terapéutica aplicada a la medicina", "transferir peces", "ordenación pesquera". El semantic matcher cae en skills irrelevantes de cualquier dominio.
2. **Tareas contaminadas** — en 3 ofertas el LLM guardó texto de otros avisos scrapeados en la misma página HTML: `"Grupo Gestión"`, `"Hace 2 días"`, `"San Martín, Buenos Aires-GBA"`, `"Importante empresa metalúrgica..."`.
3. **Sector siempre "Otro"** — el NLP no identifica rubros metalúrgico, plástico, neumáticos.

---

## 2. Cambios propuestos

### 2.1 Reglas de matching nuevas (8 reglas en `config/matching_rules_business.json`)

| ID | Patrón título | ISCO target | ESCO label |
|---|---|---|---|
| `R345_operario_cnc` | "operario cnc", "operador cnc", "cnc" | **7223** | operador de máquinas-herramienta de control numérico por computadora |
| `R346_operario_corte_laser` | "corte láser", "corte laser" + operario | **7223** | igual que R345 |
| `R347_operario_metalurgico` | "operario metalúrgico/a", "metalúrgica/o" + operario | **7214** | montador de estructuras metálicas |
| `R348_operario_plastico_soplado` | "flex blow", "moldeo por soplado", "operario plástico" + soplado/inyección | **8142** | operador de máquinas de moldear plástico |
| `R349_operario_envasado` | "envasado", "embotellado", "línea de llenado" | **8183** | operario envasado y embotellado |
| `R350_operario_deposito_logistica` | "pickeador", "operario de depósito", "operario logístico", "mozo de almacén", "operarios/as de depósito" | **9333** | mozo de almacén / peón de carga |
| `R351_operario_despacho` | "operario despacho", "despacho metalúrgico", "auxiliar despacho" | **4321** | auxiliar de despacho y expedición |
| `R352_operario_ensamble_armas` | "ensamble armas", "ensamblador armamento" | **7223** | montador de armamento |

**Prioridad:** todas con `prioridad: 0` para sobrescribir la regla genérica que cae en 8160.

**Verificación obligatoria antes de implementar:** confirmar que cada `esco_label` existe EXACTO en `esco_occupations` (bug conocido: si no existe, la regla se descarta silenciosamente — ver commit `43ae1ed5`).

### 2.2 Reglas NLP sector nuevas (en `config/nlp_correction_rules.json`)

```json
{
  "id": "sector_metalurgico_metalmecanico",
  "descripcion_contiene_alguno": [
    "metalúrgica", "metalurgica", "metalmecánica", "metalmecanica",
    "montaje de estructuras", "soldadura estructural", "fabricación de piezas metálicas"
  ],
  "titulo_contiene_alguno": ["operario", "operador", "técnico", "tecnico"],
  "override_si_actual_es": ["Otro", null, ""],
  "resultado": "Industria"
},
{
  "id": "sector_plastico",
  "descripcion_contiene_alguno": [
    "fabricación de plástico", "industria plástica", "moldeo por inyección",
    "flex blow", "soplado de plástico", "bidones plásticos", "productos plásticos"
  ],
  "override_si_actual_es": ["Otro", null, ""],
  "resultado": "Industria"
},
{
  "id": "sector_neumaticos_autopartes",
  "descripcion_contiene_alguno": [
    "neumáticos", "autopartes", "industria automotriz", "fabricación de cubiertas"
  ],
  "override_si_actual_es": ["Otro", null, ""],
  "resultado": "Industria"
}
```

**Nota:** Los 3 sectores mapean al canónico `Industria`. Si en el futuro quieren subsectores más específicos (metalúrgico, plástico, neumáticos como sectores independientes en el dashboard) se puede ajustar.

### 2.3 Ampliar regla de experiencia

**Actual:** `experiencia_min_1_si_con_exp` solo captura `"con experiencia"`, `"experiencia comprobable"`, `"experiencia previa"`.

**Faltan keywords según feedback Cynthia:**
- "experiencia deseable"
- "experiencia en puesto similar"
- "exige experiencia"
- "experiencia en el rubro"
- "experiencia mínima en"
- "experiencia en industrias"

### 2.4 Diccionario argentino — nuevos términos

Agregar a `config/sinonimos_skills_argentinos.json`:

```json
"picking de mercadería": "preparar pedidos",
"procedimientos de recepción": "recibir mercancías",
"operar equipamiento en línea de llenado": "manejar máquinas de envasado",
"etiquetar componentes": "etiquetar productos",
"controlar máquinas de llenado": "manejar máquinas de envasado",
"asistir en el embotellado": "embalar mercancías",
"operar inyectoras plásticas": "manejar máquinas de moldeo"
```

### 2.5 Política para skills en descripciones cortas (NUEVO)

**Problema:** cuando `descripcion_muy_corta` + `sin_skills_desc_larga`, el semantic matcher asigna skills de cualquier dominio con score bajo (0.5-0.7) — skills ruido.

**Propuesta:** en `skills_implicit_extractor.py`, agregar gating:
- Si `len(descripcion) < 400` AND `tareas_explicitas` vacía → threshold mínimo score = 0.80 (vs 0.55 actual).
- Si no hay skills arriba del threshold, asignar cero skills + marcar en errores "baja confianza".

**Requiere:** revisar el script, proponer PR aparte (fuera del alcance de este spec).

### 2.6 Tareas contaminadas (FUERA DE ALCANCE)

**Problema:** LLM extrae texto de otras ofertas de la misma página HTML (Computrabajo embedea múltiples ofertas en una página de búsqueda).

**Posibles soluciones (investigar aparte):**
- Verificar que el scraper de Computrabajo fetchea la página DE DETALLE (no el listado).
- Ampliar filtros del prompt del LLM para que descarte texto fuera del contenido principal.
- Agregar postprocessor que detecte patrones: nombres de empresas conocidas, "Hace X días", ubicaciones sueltas.

**Decisión:** no resolver en este spec. Abrir issue separado.

---

## 3. Implementación

### Fase 1 — Fixes de configuración
1. Agregar 8 reglas R345-R352 a `matching_rules_business.json` (con `esco_label` verificado).
2. Agregar 3 reglas de sector a `nlp_correction_rules.json`.
3. Ampliar keywords de `experiencia_min_1_si_con_exp`.
4. Agregar 7 términos al diccionario argentino.

### Fase 2 — Reprocesar las 18 ofertas pendientes
```bash
python scripts/reapply_rules_to_validated.py --ids <lista-18>
python scripts/reapply_nlp_to_validated.py --ids <lista-18>
```

### Fase 3 — Verificación
Para cada una de las 18 ofertas:
- ISCO actual debe coincidir con el sugerido por Cynthia/Diego.
- Sector no debe ser "Otro".
- Experiencia no debe ser 0 si el aviso pide experiencia.

### Fase 4 — Cerrar issues
- Marcar las 32 + 8 = 40 issues manuales como `resuelto` en Supabase.
- `solucion_aplicada`: explicación con regla aplicada.

### Fase 5 — Propagación a ofertas ya validadas (clave)

Esto es lo que más impacto tiene a mediano plazo.

Para cada regla ISCO nueva (R345-R352), correr:
```bash
python scripts/reapply_rules_to_validated.py --regla R345_operario_cnc --dry-run
# revisar cuántas ofertas matchean
python scripts/reapply_rules_to_validated.py --regla R345_operario_cnc
```

Esto corrige todas las ofertas **YA VALIDADAS** que caen en el patrón (estimado: varios cientos por regla). El script preserva `estado_validacion='validado_claude'` pero actualiza ISCO + skills.

**Ofertas candidatas estimadas (basado en pipeline corridas previas):**
- `R345_operario_cnc` (CNC): ~20-40 ofertas
- `R346_operario_corte_laser`: ~10-20
- `R347_operario_metalurgico`: ~100-200 (palabra muy común)
- `R350_operario_deposito`: ~200-500 (pickeador/depósito/logística es común)
- `R349_operario_envasado`: ~50-100

Si se estima **>500 ofertas afectadas** en total, hacer sync incremental a Supabase después de aplicar cada regla, no todo junto.

### Fase 6 — Re-corrida NLP sobre validadas propagadas

Tras propagar las reglas ISCO, correr:
```bash
python scripts/reapply_nlp_to_validated.py --from-issues
```
(ya no desde issues, pero el comando también acepta `--ids` si tenemos el universo).

Esto corrige sector/experiencia/seniority de las ofertas ya validadas que entran en los nuevos patrones.

### Fase 7 — Sync final a Supabase
```bash
python scripts/exports/sync_to_supabase.py
```

---

## 4. Verificación del bug `esco_label` inexistente (precaución)

Antes de escribir cada regla, ejecutar:

```bash
python3 -c "
import sqlite3
c = sqlite3.connect('database/bumeran_scraping.db').cursor()
labels = [
    'operador de máquinas-herramienta de control numérico por computadora/...',
    'montador de estructuras metálicas/montadora de estructuras metálicas',
    # ... todos los 8 labels
]
for l in labels:
    c.execute('SELECT 1 FROM esco_occupations WHERE LOWER(preferred_label_es) = LOWER(?)', (l,))
    print(('OK ' if c.fetchone() else 'NO ') + l[:70])
"
```

Si alguno NO existe, buscar el label real vía:
```bash
python3 -c "
import sqlite3
c = sqlite3.connect('database/bumeran_scraping.db').cursor()
c.execute(\"SELECT preferred_label_es FROM esco_occupations WHERE isco_code = 'C7223' LIMIT 5\")
for r in c.fetchall(): print(r[0])
"
```

Usar el label exacto que sí exista.

---

## 5. Tests / verificación

### Caso por caso (18 ofertas)

Para cada oferta, después de Fase 2:

| Oferta | ISCO esperado | Sector esperado | Experiencia esperada |
|---|---|---|---|
| 7942527874 (Operario CNC) | 7223 | Industria | ≥1 |
| 7937139991 (Operario cnc) | 7223 | Industria | ≥0 |
| 7985222956 (Operario pickeador) | 9333 | Logistica/Industria | ≥0 |
| 7347150394 (Operarios depósito) | 9333 | Logistica | ≥0 |
| 6866505508 (Operarios/as depósito) | 9333 | Logistica | ≥0 |
| 7272678691 (Producción bidones plástico) | 8219 | Industria | ≥1 |
| 9255109063 (Flex blow) | 8142 | Industria | ≥0 |
| 1118219210 (Producción bebidas) | 8183 | Industria/Alimentacion | ≥1 |
| 7907119232 (Metalúrgico) | 7214 | Industria | ≥0 |
| 7245178831 (Mantenimiento metalúrgica) | 7214 o mantener 8160 | Industria | ≥1 |
| 8090263692 (Corte láser) | 7223 | Industria | ≥0 |
| 7879857202 (Ensamble armas) | 7223 | Industria | ≥0 |
| 8299423434 (Despacho metalúrgico) | 4321 | Logistica | ≥0 |
| 6786905097 (Habilidad manual) | 9319 | Industria | ≥0 |
| 7057631179 (Maquinista alimentos) | 8160 (mantener) | Alimentacion | ≥0 |
| 7171410854 (Producción alimenticia) | 8160 (mantener) | Alimentacion | ≥1 |
| 7938726540 (Producción línea alimentos) | 8160 (mantener) | Alimentacion | ≥0 |
| 7965889050 (Operarios y operarias) | 8160 (mantener, genérico) | - | ≥1 |

### Tests de regresión

Correr gold set post-cambios:
```bash
pytest tests/matching/test_gold_set_manual.py -v
```
**NO se debe romper ningún caso existente del gold set.** Si alguna regla nueva afecta ofertas del gold set, ajustar la regla con `titulo_no_contiene_alguno` para excluir casos.

---

## 6. Riesgos

1. **Reglas muy amplias pueden capturar falsos positivos.**
   - `"operario"` + `"metalúrgica"` podría capturar "operario en empresa metalúrgica" donde el puesto real es otro (ej: administrativo).
   - Mitigación: usar condición combinada (`titulo_original_contiene_alguno` + keywords específicas).

2. **Label ESCO inexistente → regla silenciosa.**
   - Mitigación: verificación previa obligatoria (sección 4).

3. **Propagación masiva podría alterar ofertas bien clasificadas.**
   - Mitigación: `--dry-run` obligatorio + revisar sample de 10 antes de aplicar masivamente.

4. **Skills ruido persiste aún con ISCO corregido.**
   - La regla de matching arregla el ISCO, pero las skills siguen siendo las del semantic matcher (random).
   - Solución parcial: agregar `skills_rules.json` por ISCO forzando skills correctas.
   - Solución completa: Fase 2.5 (fuera de scope).

---

## 7. Criterios de éxito

- ✅ 18 de 18 ofertas operarios pendientes con ISCO correcto tras Fase 2.
- ✅ 40 issues manuales cerrados en Supabase.
- ✅ >80% de ofertas validadas con patrón operario propagado correctamente.
- ✅ Gold set no rompe.
- ✅ Dashboard Supabase actualizado.

---

## 8. Orden de decisión

**Pregunta al usuario antes de ejecutar:**
1. ¿Avanzamos con las 8 reglas ISCO (Fase 1)?
2. ¿También las 3 de sector + experiencia (Fase 1 completa)?
3. ¿Incluimos propagación a validadas (Fase 5)?
4. ¿Skills ruido queda fuera de scope (solución parcial con skills_rules.json o espera fix estructural)?
5. ¿Tareas contaminadas → issue separado?
