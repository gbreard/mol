# [FRENTE L] P3 — Medición del re-matching masivo (GATE del sync)

**Corrida:** 2026-08-20 20:09 → 2026-08-22 03:02 (tandas de 2.500 bajo tmpfs, `--skip-nlp`, TEST del evaluador cada 4 chunks — **todos 35/35**). Universo censado 77.040; **83.786 ofertas quedan con matching 3.6.x** (incluye las nacidas por el backlog NLP durante la ventana). **Candado intacto: 6.275 `validado`** + `en_revision` + `rule_manual_fix` sin tocar (verificado post sync-back).

## KPI de canales — proyección vs real

| Canal | Baseline post-K3 (proyección) | Dry-run 2.000 | **Real (re-matcheadas 3.6.x)** |
|---|---|---|---|
| semántico | 37,4% | 38,0% | **36,7%** |
| regla plana | 47,6% (todas las reglas) | 30,4% | **31,5%** |
| diccionario | 10,9% | 14,5% | **14,0%** |
| regla L3 | — | 8,6% | **8,5%** |
| regla subordinada | — | 5,1% | **5,3%** |
| **árbol (traductor)** | 4,1% | 3,3% | **4,0%** |

El dry-run predijo la corrida real con desvíos ≤1,3pp en todos los canales. Canal reglas total (plana+L3+subordinada): **45,3%** — coherente con el 47,6% proyectado post-K3 (la diferencia son las des-forzadas que ahora caen a dict/semántico al re-decidirse de cero).

## El cambio: 44,4% del corpus comparable cambió de destino

Sobre **77.027 comparables** (universo ∩ snapshot): **34.236 cambiaron de destino ESCO (44,4%)** — el dry-run proyectaba 45,0%. Cero pérdidas de cobertura (0 sin decisión).

### Desglose del 44% por causa — sobre las 34.236 (población completa, no solo muestra)

| Causa | Ofertas | % |
|---|---|---|
| **Corrección K/K2/K3** (misma regla, destino corregido por Cyn) | 9.527 | 27,8% |
| **Retiro-desforzada** (regla retirada → decide otro canal) | 8.970 | 26,2% |
| **Semántico-mejorado** (semántico antes y ahora, mejor destino) | 7.821 | 22,8% |
| Reordenamiento de canal (dict/otra regla precede) | 4.375 | 12,8% |
| **Reordenamiento: el traductor decide** (árbol) | 1.766 | 5,2% |
| Restricción-desforzada (regla restringida → cae a semántico) | 676 | 2,0% |
| Captura nueva (regla/dict toma lo que era semántico) | 453 | 1,3% |
| Otro (p.ej. entradas dict retiradas) | 648 | 1,9% |

**Lectura:** más de la mitad del cambio (54%) es la auditoría de Cyn materializándose (correcciones + retiros); un quinto es el semántico re-decidiendo mejor (post-limpieza de canales); y el traductor aporta su 5% quirúrgico.

### Matriz canal→canal (top)

`regla→regla` 23.911 (mayormente mismas reglas con destino corregido) · `sem→sem` 20.679 · `regla→semántico` 6.611 (des-forzadas) · `regla→dict` 5.133 · `subordinada→árbol` 1.458 (la subordinación L4 operando).

## Spot-check 30 (seed 42, clasificado)

30/30 revisadas una a una (detalle en `l_p3_resultados.json`): 10 corrección-K (R181→mantenedor, R309→jefe de almacén, R111→vendedor, R306→electricista industrial, R274→coordinador de transporte, R76, R225, R155, R238, R169→R242…), 4 traductor (call center→teleoperador 5244.1, vendedor corporativo/técnico→representante comercial), 8-9 semántico-mejorado (casos groseros reparados: "Lead fullstack"→desarrollador (antes: director de laboratorio médico), "Contracts manager"→gestor de contratos), 1 retiro-desforzada con **resultado malo**: «Asistente legal bilingüe» (R17 retirada) → semántico dice "conductor de ambulancia" — el costo conocido de des-forzar sin regla de reemplazo; alimenta la próxima ronda de la mesa.

## JOIN de recuperación (3 cohorts de retiros)

| Cohort | N | Semántico | Regla | Dict | Árbol/L3/sub | Siguen en destino retirado |
|---|---|---|---|---|---|---|
| K-T1 (7 reglas) | 4.686 | 71% | 23% | 6% | <1% | **13%** (por otros canales, legítimo) |
| K2-auxiliares | 548 | 47% | 37% | 7% | 9% | 22% |
| K3-retiros | 160 | 68% | 23% | 7% | 2% | **1%** |

Cero sin decisión en los 3 cohorts: nadie quedó huérfano por los retiros.

## Telemetría del árbol y caso testigo

- **3.345 decisiones del traductor** por hub: 16 (1.467), 51 (1.427), 2 (201), 1 (175), 4 (40), 15 (28), 3 (7).
- **Caso testigo G3 reparado:** `1118027524` «Intendente de obra» → `diccionario_argentino_intendente_de_obra` → **capataz de construcción** (la corrección de Cyn de junio, que el corpus histórico había perdido, quedó restaurada). ✓

## Remanente e incidencias operativas

- **Remanente 13 ofertas** sin re-matchear: estados de revisión humana intermedia (5 `validado_claude`, 7 `pendiente_humano_C1`, 1 `pendiente`) que el propio pipeline protege — coherente con el candado. El selector del universo las incluía; la guarda del pipeline las defendió. Documentadas, sin acción.
- Incidencias de la corrida (todas con fix commiteado): rc=1 del pipeline tratado como crash (falso positivo, chunk 1 re-corrido); **loop estancado** al agotarse el universo (las 13 protegidas re-seleccionadas ~1.950 veces durante 3,5 h, sin escrituras) → guarda anti-estancamiento agregada al inner; corte con sync-back verificado por hash.
- Multi-perfil corrió degradado a SINGLE a propósito (sin OLLAMA_HOST): el frente re-decide SOLO matching, sub-ofertas nuevas hubieran contaminado universo y cohorts.

## Estado del gate

**La medición está completa ANTES del sync.** P4 (sync a dashboard + spot 10 en Supabase + PR) queda a la espera del punto de control.
