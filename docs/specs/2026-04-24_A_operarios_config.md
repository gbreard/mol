# SPEC A: Corrección sistémica ISCO/Sector/Experiencia — operarios

**Fecha:** 2026-04-24
**Autor feedback:** Cynthia Vázquez, Diego Schleser
**Estado:** Draft — pendiente aprobación
**Scope:** Solo cambios de configuración (sin código).
**Specs relacionados:**
- `2026-04-24_B_skills_noise.md` — skills ruido (independiente, paralelo)
- `2026-04-24_C_tareas_contaminadas.md` — bug scraper/LLM (independiente)

---

## 1. Problema

El matcher clasifica **todas las ofertas de operarios (excepto alimentos) con ISCO 8160 ("operario de prensado de fruta")** como default catch-all.

**18 ofertas confirmadas con este patrón** (11 de Cynthia + 8 de Diego, con 1 compartida).

### Por qué importa

- 8160 es para prensado de fruta específicamente (ESCO label literal).
- Afecta todas las ocupaciones operarias: CNC, metalúrgica, plástico, envasado, logística, armas, manufactura general, despacho.
- **Alcance no limitado a 18 ofertas**: toda oferta nueva con título "Operario X" cae en 8160 si no hay regla específica.
- Efectos secundarios detectados:
  - Sector siempre "Otro" porque no hay keywords de metalúrgico/plástico/neumáticos en NLP
  - Experiencia `0` cuando el aviso pide experiencia pero con keywords que la regla actual no captura

### Fuera del scope de este spec

- Skills random en descripciones cortas → Spec B
- Tareas contaminadas con texto de otros avisos → Spec C

---

## 2. Cambios propuestos

### 2.1 Reglas de matching nuevas (8 reglas en `config/matching_rules_business.json`)

| ID | Patrón título | ISCO target | ESCO label candidato |
|---|---|---|---|
| `R345_operario_cnc` | "operario cnc", "operador cnc", "cnc" | **7223** | operador de máquinas-herramienta de control numérico por computadora |
| `R346_operario_corte_laser` | "corte láser", "corte laser" + operario | **7223** | igual que R345 |
| `R347_operario_metalurgico` | "operario metalúrgico/a", "metalúrgica/o" + operario | **7214** | montador de estructuras metálicas |
| `R348_operario_plastico_soplado` | "flex blow", "moldeo por soplado", "operario plástico" + soplado/inyección | **8142** | operador de máquinas de moldear plástico |
| `R349_operario_envasado` | "envasado", "embotellado", "línea de llenado" | **8183** | operario envasado y embotellado |
| `R350_operario_deposito_logistica` | "pickeador", "operario de depósito", "operario logístico", "mozo de almacén", "operarios/as de depósito" | **9333** | mozo de almacén / peón de carga |
| `R351_operario_despacho` | "operario despacho", "despacho metalúrgico", "auxiliar despacho" | **4321** | auxiliar de despacho y expedición |
| `R352_operario_ensamble_armas` | "ensamble armas", "ensamblador armamento" | **7223** | montador de armamento |

**Prioridad:** todas con `prioridad: 0` para sobrescribir la regla genérica.

**Verificación obligatoria:** confirmar que cada `esco_label` existe EXACTO en `esco_occupations`. Bug conocido (commit `43ae1ed5`): si no existe, la regla se descarta silenciosamente.

### 2.2 Reglas NLP sector nuevas (`config/nlp_correction_rules.json`)

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

**Nota:** los 3 mapean a `Industria`. Si en el futuro se quieren subsectores en el dashboard, se ajusta.

### 2.3 Ampliar regla de experiencia

**Actual:** `experiencia_min_1_si_con_exp` solo captura `"con experiencia"`, `"experiencia comprobable"`, `"experiencia previa"`.

**Ampliar con:**
- "experiencia deseable"
- "experiencia en puesto similar"
- "exige experiencia"
- "experiencia en el rubro"
- "experiencia mínima en"
- "experiencia en industrias"

### 2.4 Diccionario argentino — términos nuevos

Agregar a `config/sinonimos_skills_argentinos.json` sección `tareas_a_skills`:

```json
"picking de mercadería": "preparar pedidos",
"procedimientos de recepción": "recibir mercancías",
"operar equipamiento en línea de llenado": "manejar máquinas de envasado",
"etiquetar componentes": "etiquetar productos",
"controlar máquinas de llenado": "manejar máquinas de envasado",
"asistir en el embotellado": "embalar mercancías",
"operar inyectoras plásticas": "manejar máquinas de moldeo"
```

**Verificación:** cada label destino debe existir en `esco_skills.preferred_label_es`. Usar `scripts/search_esco_skill.py` para confirmar.

---

## 3. Plan de implementación (7 fases)

### Fase 1 — Fixes de configuración
1. Verificar que los 8 `esco_label` existen en `esco_occupations`.
2. Agregar R345-R352 a `matching_rules_business.json`.
3. Agregar 3 reglas de sector a `nlp_correction_rules.json`.
4. Ampliar keywords de `experiencia_min_1_si_con_exp`.
5. Agregar 7 términos al diccionario argentino + correr `import_argentine_skill_labels.py`.

### Fase 2 — Reprocesar las 18 ofertas pendientes

```bash
IDS="7985222956,7272678691,7245178831,1118219210,7171410854,7965889050,7938726540,8090263692,7057631179,7347150394,7942527874,7907119232,7937139991,9255109063,6866505508,7879857202,6786905097,8299423434"
python scripts/reapply_rules_to_validated.py --ids "$IDS"
python scripts/reapply_nlp_to_validated.py --ids "$IDS"
```

### Fase 3 — Verificación caso por caso

| Oferta | ISCO esperado | Sector esperado |
|---|---|---|
| 7942527874 (Operario CNC) | 7223 | Industria |
| 7937139991 (Operario cnc) | 7223 | Industria |
| 7985222956 (Operario pickeador) | 9333 | Logistica/Industria |
| 7347150394 (Operarios depósito) | 9333 | Logistica |
| 6866505508 (Operarios/as depósito) | 9333 | Logistica |
| 7272678691 (Producción bidones plástico) | 8219 | Industria |
| 9255109063 (Flex blow) | 8142 | Industria |
| 1118219210 (Producción bebidas) | 8183 | Industria/Alimentacion |
| 7907119232 (Metalúrgico) | 7214 | Industria |
| 7245178831 (Mantenimiento metalúrgica) | 7214 o mantener 8160 | Industria |
| 8090263692 (Corte láser) | 7223 | Industria |
| 7879857202 (Ensamble armas) | 7223 | Industria |
| 8299423434 (Despacho metalúrgico) | 4321 | Logistica |
| 6786905097 (Habilidad manual) | 9319 | Industria |
| 7057631179 (Maquinista alimentos) | 8160 (mantener) | Alimentacion |
| 7171410854 (Producción alimenticia) | 8160 (mantener) | Alimentacion |
| 7938726540 (Producción línea alimentos) | 8160 (mantener) | Alimentacion |
| 7965889050 (Operarios y operarias) | 8160 (mantener, genérico) | - |

### Fase 4 — Cerrar issues

40 issues manuales (32 Cynthia + 8 Diego) → marcar `estado=resuelto` con `solucion_aplicada` descriptiva.

### Fase 5 — Propagación a ofertas ya validadas

**Esto es lo de mayor impacto.** Para cada regla ISCO nueva:

```bash
python scripts/reapply_rules_to_validated.py --regla R345_operario_cnc --dry-run
# revisar cuántas afecta
python scripts/reapply_rules_to_validated.py --regla R345_operario_cnc
```

Estimados (basado en patrones históricos):
- `R345_operario_cnc`: ~20-40 ofertas
- `R346_operario_corte_laser`: ~10-20
- `R347_operario_metalurgico`: ~100-200 (palabra común)
- `R350_operario_deposito`: ~200-500 (muy común)
- `R349_operario_envasado`: ~50-100

**Regla operativa:** si una regla afecta >100 ofertas, revisar primero 10 al azar del `--dry-run` antes de aplicar.

### Fase 6 — Re-corrida NLP sobre validadas propagadas

```bash
# Para cada batch de IDs afectados por Fase 5:
python scripts/reapply_nlp_to_validated.py --ids <IDs>
```

### Fase 7 — Sync final a Supabase

```bash
python scripts/exports/sync_to_supabase.py
```

---

## 4. Verificación pre-deploy del bug `esco_label` inexistente

Antes de escribir cada regla, ejecutar:

```python
import sqlite3
c = sqlite3.connect('database/bumeran_scraping.db').cursor()
labels_candidatos = [
    'operador de máquinas-herramienta de control numérico por computadora/operadora de máquinas-herramienta de control numérico por computadora',
    'montador de estructuras metálicas/montadora de estructuras metálicas',
    'operador de máquinas de moldear plástico por soplado/operadora de máquinas de moldear plástico por soplado',
    'operario de línea de envasado y embotellado/operaria de línea de envasado y embotellado',
    'mozo de almacén/mozos de almacén',
    'auxiliar de despacho y expedición',
    'montador de armamento/montadora de armamento',
    'peón de la industria manufacturera no clasificado bajo otros epígrafes',
]
for l in labels_candidatos:
    c.execute('SELECT 1 FROM esco_occupations WHERE LOWER(preferred_label_es) = LOWER(?)', (l,))
    print(('OK ' if c.fetchone() else 'MISS ') + l[:80])
```

Si alguno NO existe, buscar el real:
```python
c.execute("SELECT preferred_label_es FROM esco_occupations WHERE isco_code = 'C7223' LIMIT 10")
```

Usar el label exacto que sí exista.

---

## 5. Tests de regresión

```bash
# Gold set v2 (casos verificados por Cyn + Diego con isco_esperado explícito)
pytest tests/matching/test_gold_set_v2_verified.py -v

# Baseline antes de Spec A: 26 passed (R324-R344 verified) + 22 failed (Spec A pending)
# Después de Spec A: 48 passed, 0 failed
```

El test está parametrizado por caso: pytest reporta cada oferta individual con ISCO actual vs esperado. Tests agrupados por regla (`TestReglasOperariosSpecA::test_r345_operario_cnc`) permiten ver rápido qué regla falta aplicar.

**NO usar `tests/matching/test_gold_set_manual.py` (v1)** — está desactualizado (49 casos con solo `esco_ok: true/false`, sin ISCO esperado explícito). Puede dar falsos positivos si una regla nueva cambia legítimamente el ISCO.

Si una regla nueva rompe un caso verified, revisar:
1. ¿El ISCO esperado en gold_set_v2.json sigue siendo correcto tras la regla? Si no, actualizar JSON.
2. ¿La nueva regla pisa un caso legítimo? Agregar `titulo_no_contiene_alguno` para excluir.

---

## 6. Riesgos

1. **Reglas muy amplias → falsos positivos.** Ejemplo: `"operario"` + `"metalúrgica"` podría capturar "administrativo en empresa metalúrgica". Mitigación: usar `titulo_original_contiene_alguno` con keywords específicas + `titulo_no_contiene_alguno` para excluir admin/contable/etc.

2. **Label ESCO inexistente → regla silenciosa.** Mitigación: verificación previa obligatoria (sección 4).

3. **Propagación masiva podría alterar ofertas bien clasificadas.** Mitigación: `--dry-run` obligatorio + sample de 10 antes de aplicar.

4. **Skills irrelevantes persisten.** Este spec corrige ISCO/Sector/Experiencia. Skills ruido queda para Spec B.

---

## 7. Criterios de éxito

- ✅ 18/18 ofertas operarios pendientes con ISCO correcto tras Fase 3.
- ✅ 40 issues manuales cerrados en Supabase (Fase 4).
- ✅ >80% de ofertas validadas con patrón operario propagado correctamente (Fase 5).
- ✅ Gold set no rompe.
- ✅ Dashboard Supabase actualizado (Fase 7).

---

## 8. Checklist antes de ejecutar

- [ ] Usuario aprueba el plan
- [ ] Labels ESCO verificados existentes en BD
- [ ] Script `reapply_rules_to_validated.py --regla <X> --dry-run` probado con al menos 1 regla
- [ ] Plan de rollback: si una regla propaga mal, revertir commit del JSON + re-run rules con el estado previo del matching rules (requiere historial git)

---

## 9. Orden de ejecución sugerido

1. Verificar labels ESCO (5 min)
2. Escribir las 8 reglas matching (10 min)
3. Escribir 3 reglas sector + ampliar experiencia (5 min)
4. Agregar 7 términos diccionario + importar (5 min)
5. Fase 2 reproceso 18 ofertas (5 min)
6. Verificar Fase 3 (10 min)
7. Cerrar issues Fase 4 (5 min)
8. Propagación por regla Fase 5 (~30 min con dry-run de cada)
9. Re-NLP Fase 6 (5-10 min)
10. Sync Supabase Fase 7 (~15 min)

**Total estimado:** 90-120 min de trabajo activo + tiempos de reproceso.
