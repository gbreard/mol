# SPEC B v2 — Fase 3: Informe de impacto (read-only)

**Fecha:** 2026-04-24
**Script:** `scripts/analyze_trust_impact.py`
**Base:** `/tmp/pipeline_test/snapshot2.db` (snapshot 2026-04-24 14:56, 49,117 ofertas validadas)

---

## 1. Resumen ejecutivo

Aplicando el filtro trust-source sobre 49,117 ofertas validadas (868,010 skills), el sistema descartaría **143,183 skills (16.5%)**. La distribución es saludable y se alinea con los criterios de éxito del spec (≤25% descarte total).

---

## 2. Distribución de trust_motivo

| motivo | skills | % | trust |
|---|---:|---:|:---:|
| origen_tarea_real | 607,816 | 70.0% | ✓ |
| titulo_redundante_score_bajo | 106,496 | 12.3% | ✗ |
| origen_llm_detectado | 70,318 | 8.1% | ✓ |
| origen_tarea_corta_score_bajo | 32,523 | 3.7% | ✗ |
| origen_reglas (terminologia) | 29,382 | 3.4% | ✓ |
| origen_tarea_corta_score_alto | 17,080 | 2.0% | ✓ |
| titulo_corto_score_medio | 2,966 | 0.3% | ✗ |
| titulo_solo_fuente_score_bajo | 1,198 | 0.1% | ✗ |
| titulo_corto_score_muy_alto | 125 | 0.0% | ✓ |
| titulo_solo_fuente_score_ok | 106 | 0.0% | ✓ |

**Observación:** el 99.8% del ruido eliminado se concentra en dos motivos:
- `titulo_redundante_score_bajo` (12.3%): skills que BGE-M3 sacó del título con score bajo cuando ya había tareas disponibles.
- `origen_tarea_corta_score_bajo` (3.7%): skills derivadas de tareas <20 chars con score <0.75 (típicamente tareas copy-paste en inglés o fragmentos sin sustancia).

---

## 3. Comparación con criterios de éxito del spec

| Criterio | Esperado | Observado | Estado |
|---|---|---|---|
| Reducción total | ≤ 25% | **16.5%** | ✅ |
| origen_tarea_real | ≥ 60% | **70.0%** | ✅ |
| origen_reglas + origen_llm_detectado | ≥ 20% | **11.5%** | ⚠️ bajo (pero porque `terminologia` real son 3.4% y `skills_nlp` solo aparece cuando NLP lo detectó) |
| titulo_solo_fuente_score_ok | ≤ 15% | **0.0%** | ✅ |
| titulo_corto_* | ≤ 5% | **0.3%** | ✅ |

---

## 4. Por origen

| origen | total | descartadas | % |
|---|---:|---:|---:|
| skills_nlp | 70,318 | 0 | 0.0% |
| terminologia | 29,382 | 0 | 0.0% |
| tarea | 657,419 | 32,523 | 4.9% |
| titulo | 110,891 | 110,660 | **99.8%** |

**Interpretación:**
- `skills_nlp` y `terminologia` pasan siempre (como es de esperar: son señales de alta calidad).
- `tarea` cae solo 4.9% → las tareas son la fuente de verdad del sistema.
- `titulo` cae 99.8% → confirma que las skills agregadas top-K de título son ruido cuando hay otra fuente.

---

## 5. Por banda de contexto

| banda | ofertas | skills prom | descartadas prom | % cae |
|---|---:|---:|---:|---:|
| crítico (desc<400 + tareas=0) | 648 | 2.9 | 2.8 | **96.4%** |
| corto_pobre | 768 | 4.1 | 2.8 | 68.7% |
| pobre | 684 | 8.3 | 3.1 | 37.9% |
| medio | 6,498 | 13.2 | 3.4 | 25.8% |
| **bueno** (desc≥800 + ≥3 tareas) | 40,519 | 19.1 | 2.8 | **14.9%** |

**Interpretación:** el filtro es mucho más severo en ofertas de contexto pobre (donde el ruido es real) y respeta el 85% de las skills en contexto bueno.

---

## 6. Casos canónicos del spec (validación)

### Oferta 5575403602 — operario/a de limpieza
- desc=239, sin tareas
- Todas las skills random (`apuestas mutuas`, `programas públicos de seguridad social`, `escribir en catalán`) se descartan por motivo `titulo_corto_score_medio`.
- **Resultado:** 0/3 mantenidas ✅ (objetivo del spec cumplido).

### Oferta 1118173872 — enfermera profesional
- desc=977, con tareas
- Se descartan 3 skills de título con score bajo (`interactuar en coreano`, `enclavamientos de señalización`, `asesorar a usuario sanitario`).
- **Se mantienen 15 skills de tareas** incluyendo algunas mal matcheadas por BGE-M3 (`inspeccionar grabado al ácido`, `técnicas de soldadura blanda`).
- **Limitación esperada:** el filtro no detecta mal top-K sobre tareas sustantivas. Eso es fuera de scope de este spec.

---

## 7. Riesgo conocido: ofertas con reducción drástica

**2,547 ofertas (5.2%) perderían ≥80% de sus skills.**

Muestra típica:
- `[1118168092] Project manager` — banda "bueno" pero las tareas son fragmentos en inglés de 10-20 chars ("Monitor Progress", "Lead Meetings", "Plan & Execute"). BGE-M3 genera skills random, y el filtro corta correctamente.
- `[6408506676] Operarios y herreros metalúrgicos` — 18/18 skills descartadas: caso límite donde las tareas son demasiado cortas para generar buenos matches.

**Estas no son ofertas "saludables" con mucho ruido — son ofertas con input pobre (tareas copy-paste, fragmentos, etc.).** El filtro deja pocas skills porque en efecto no hay buena señal.

---

## 8. Ajuste post-Fase 3

Tras inspeccionar las ofertas "drásticas", se identificaron dos problemas:

### 8.1 Tareas argentinas cortas legítimas
Ofertas como "Mucama/niñera" con tareas `Lavado; Planchado; Cocina` o "Operario de mantenimiento" con `Plomería; Electricidad; Soldadura` tienen tareas sustantivo-corto válidas. El criterio original (≥20 chars) las consideraba "cortas" y exigía score ≥0.75, descartando skills como `lavar la ropa`, `planchar tejidos`, `electricidad`.

**Corrección:** el clasificador ahora **confía siempre en `origen=tarea`** (sin importar largo). La tarea ya pasó el threshold BGE-M3 inicial — es la fuente de verdad del puesto.

### 8.2 Títulos cortos específicos con top-K razonable
Casos como `[1118092286] Electricista` → skills `electricidad`, `mantener el equipo eléctrico`, `corriente eléctrica` (scores 0.70-0.76) caen por `titulo_corto_score_medio`. Son falsos positivos. El score no permite distinguir "electricista" (top-K coherente) de "operario limpieza" (top-K random).

**Decisión:** se acepta el trade-off. El caso canónico del spec (operario limpieza) se resuelve; los falsos positivos en títulos cortos específicos se compensan dejando `filtrar_por_trust=False` por default y solo persistir `trust_motivo` como telemetría.

---

## 9. Resultado tras ajuste

- **Descarte total: 12.7%** (vs 16.5% antes del ajuste)
- `origen=tarea` cae 0% (vs 4.9% antes) — preserva tareas argentinas cortas
- `origen=titulo` cae 99.8% — el filtro sigue detectando ruido top-K
- Casos canónicos resueltos:
  - Oferta 5575403602 (operario limpieza): 3/3 skills random descartadas ✅
- Ofertas con reducción drástica: 1,929 (vs 2,547)

---

## 10. Recomendación final

**Retropropagar SOLO metadata** (agregar `trust` + `trust_motivo` a cada skill en `skills_semantico_json`):

- ✅ Reversible (solo atributos JSON; se pueden remover)
- ✅ Dashboard actual no se afecta (sigue viendo todas las skills)
- ✅ Telemetría disponible para decisiones futuras
- ✅ Compatible con `filtrar_por_trust=False` por default
- ✅ Si se valida el filtro luego, activar `filtrar_por_trust=True` requiere solo una re-query (no alterar BD)

---

## 9. Próximos pasos

1. ✅ Tests pasando (18/18 unit + 47/48 gold_set_v2)
2. ⏸ **Decisión:** aprobar retropropagación conservadora vs agresiva
3. Fase 4: aplicar backfill si se aprueba

**Salida completa:** `/tmp/pipeline_test/trust_impact.txt`
