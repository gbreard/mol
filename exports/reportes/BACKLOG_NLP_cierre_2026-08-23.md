# [BACKLOG NLP] Corrida dedicada del backlog histórico — cierre (2026-08-19 → 2026-08-23)

La corrida tipo FRENTE D que quedó anotada como pendiente en el informe del 2026-08-18
("la semanal de 2.000 acompaña el flujo fresco pero NO come el histórico — eso pide una
corrida dedicada, a laudar aparte").

## Resultado

| | Al arrancar (19/08) | Al cerrar (23/08) |
|---|---|---|
| Ofertas totales | 111.171 | 112.857 |
| Con NLP | 84.967 | **98.770** |
| Backlog sin NLP | 26.647 | 14.628 |
| **Backlog PROCESABLE** | **8.732** | **48** |

**13.803 ofertas procesadas** en 6 tandas, todas con NLP v11.3.1 + gate + multi-position +
matching v3.6.0 completo. Las 48 pendientes entraron por scraping después del cierre.

Verificación de matching en la ventana de la operación: **90.826 filas con `isco_code` y
`esco_occupation_uri` poblados al 100%, cero nulos** (incluye el re-matching del frente L).
Este backlog **no necesita re-matching posterior**.

## Tandas

| Tanda | Procesadas | Min | Of/h | Aprovech. | Avisos hasta |
|---|---|---|---|---|---|
| 1 (19/08) | 2.288/2.500 | 460 | 298 | 92% | 2026-08-11 |
| 2 (20/08) | 1.877/2.500 | 369 | 305 | 75% | 2026-08-05 |
| 3 (20/08) | 2.500/2.500 | 487 | 308 | 100% | 2026-07-30 |
| — | *pausa por frente L (re-matching, prioridad de secuencia)* | | | | |
| 4 (22/08) | 2.500/2.500 | 506 | 296 | 100% | 2026-07-28 |
| 5 (22/08) | 2.500/2.500 | 490 | 306 | 100% | 2026-07-20 |
| 6 (23/08) | 2.020/2.020 | 395 | 307 | 100% | 2024-01-15 |

Ritmo entre 296 y 308 of/h en días distintos, con y sin otro frente compitiendo por la
máquina. **Cero ofertas perdidas**: el reporte final registra "no procesadas dentro de las
tandas: 0".

## Los tres hallazgos

### 1. Desajuste de afinidad de tipos: 15 min → 0,1 s

`ofertas.id_oferta` es **INTEGER**; en `ofertas_nlp` y `ofertas_esco_matching` es **TEXT**.
La comparación cruza afinidades, ningún índice sirve para seek y el LEFT JOIN degenera en
nested loop de 111K × 83K (~9.200 millones de comparaciones). Medido: >15 min sin terminar.

```sql
-- antes:  SCAN o / SCAN m LEFT-JOIN          -> +15 min
-- después: SEARCH ... USING INDEX            -> 0,1 s
WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n
                  WHERE n.id_oferta = CAST(o.id_oferta AS TEXT))
```

Mismo conjunto exacto (26.647 verificado contra el join original).

> **Pendiente para producción:** `get_ids_without_nlp()` (`run_validated_pipeline.py:176`) y
> `get_ids_with_nlp_errors()` (:160) tienen el mismo join sin CAST. No se tocaron — es
> código de producción fuera del encargo — pero pagan este costo en cada corrida.

### 2. El 63% del backlog es inerte

El extractor filtra en `process_nlp_from_db_v11.py:622`:
`descripcion IS NOT NULL AND LENGTH(descripcion) > 100`. Lo que no pasa, **se descarta en
silencio**.

De las 23.672 del backlog al día 2: **14.940 inertes (63%)**, casi todas de computrabajo
(14.399 de 15.664) — los walls de Cloudflare/JSON-LD ausente ya documentados el 2026-08-18
como "NULLs honestos".

Sin corregir la selección, las inertes quedaban arriba del orden por fecha y se
re-seleccionaban en cada tanda: el aprovechamiento ya venía cayendo 92% → 75%, y las últimas
tandas habrían seleccionado 2.500 inertes y procesado 0 girando en falso. Con la selección
alineada al predicado del extractor, **100% en las cuatro tandas siguientes**.

Las 14.580 inertes que quedan son materia del scraper, no de esta corrida.

### 3. Hueco de reintento en la ventana de sync-back ajeno

El bucle reintentaba ante "BD en uso" y "ya es un symlink", pero no ante **"BD no
encontrada"** — que es justo lo que ocurre durante el sync-back de otro frente: el wrapper
borra el symlink, copia 4,6 GB a `.sync_tmp`, verifica sha256 y recién ahí hace el `mv`.
Durante esos ~8 min la BD **no existe en disco** (observado en vivo en el traspaso del
2026-08-20 20:07).

Corregido: las 4 condiciones transitorias esperan; las 2 reales (`falta el comando`,
`hash de copia no coincide` — corrupción) siguen matando la corrida.

## Convivencia entre frentes

La pausa del 2026-08-20 13:05 (prioridad al re-matching del frente L por la fecha del lunes)
y la reanudación automática del 2026-08-22 03:05 funcionaron sin intervención: la corrida se
relanzó armada y esperó **36 reintentos de 10 min** hasta que el L liberó la BD.

El arbitraje por tmpfs (la BD vuelve a disco entre tandas) resultó ser el mecanismo de
coordinación efectivo entre sesiones.

## Herramientas (sin commitear, en el working tree)

| Archivo | Función |
|---|---|
| `scripts/ops/backlog_nlp_run.sh` | Bucle: salud → tanda con tmpfs → reporte → respiro |
| `scripts/ops/backlog_nlp_tanda.py` | Una tanda: selección por frescura → pipeline → checkpoint |
| `scripts/ops/backlog_nlp_reporte.py` | Progreso, ritmo y proyección |

El checkpoint es la BD misma: una oferta con NLP desaparece de la selección, así que la
corrida es reanudable por construcción, sin estado externo que se pueda desincronizar.

## Limpieza pendiente (manual)

- `database/bumeran_scraping.db.bak_tmpfs` — ~5 GB, respaldo que el wrapper deja a propósito
- `exports/validation/Pipeline_completo_validacion_2026082*.xlsx` — uno por tanda

## Decisión no tomada

El pipeline gasta ~14% de cada tanda re-procesando NLP de ofertas ya aprobadas por el gate
(tanda 1: re-NLP de 426 ofertas, 3.103 s, más una segunda pasada de matching). No converge
nada: son errores escalados que necesitan reglas, no reprocesamiento.
`--max-nlp-iterations 1` lo saltaría. No se aplicó: cambia semántica del pipeline, no es
parámetro de operación.
