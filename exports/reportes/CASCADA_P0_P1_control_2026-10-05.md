# [CASCADA v12.4] P0 completo + P1 estimado — PUNTO DE CONTROL (2026-10-05)

**Estado: P0 hecho. P1 medido con 1 tanda. ME DETENGO en el gate de P1.** La re-extracción
TOTAL (multi-día) NO arranca sin tu OK. Branch `ops/cascada-tareas-v124` (por plumbing, HEAD
en sesión ajena). Protegidos intactos.

---

## P0 — Snapshot, época y censo (hecho)

### Snapshot pre-cascada (el camino de vuelta)
`exports/cohorts/snapshot_pre_cascada_2026-10-05_*` — 3 capas congeladas + manifiesto con sha256:

| Capa | Filas | Tamaño | Qué preserva |
|---|---|---|---|
| tareas_v11 | 98.709 | 11,2 MB | las tareas que se van a reemplazar |
| matching | 97.124 | 3,9 MB | el matching pre-re-matching (para el candado + cohort JOIN) |
| skills | 2.826.638 | 169,0 MB | skills v11 (NO se re-derivan acá — ventana abierta hasta frente O) |

Los `.gz` quedan EN DISCO (184 MB, no viajan a git); el `MANIFIESTO.json` con sha256 sí se commitea (patrón del L). **Candado F0.4b registrado: 6.326** (validado 6.275 + en_revisión 38 + rule_manual_fix 13).

### Época (laudo d — el linaje roto, declarado)
Mecanismo barato aplicado (O(1), sin reescribir 2,8M filas): `ALTER TABLE
ofertas_esco_skills_detalle ADD COLUMN skills_epoca TEXT DEFAULT 'tareas_v11'` → las 2.826.638
skills quedan marcadas `tareas_v11`. Más una tabla `cascada_meta` (key/value) que declara el
linaje y deja la nota para el frente O (debe setear `skills_epoca='tareas_v124'` al re-derivar).

### Censo de entrada

| Población | Conteo | Trato en la cascada |
|---|---|---|
| ofertas_nlp total | 98.709 | — |
| **primarias con descripción procesable (>80 ch)** | **~98.168** | **re-extraen (universo P1)** |
| con tareas v11 no vacías | 94.463 | se reemplazan |
| sub-ofertas multi-position (ids `X_2`…) | 541 | **trato aparte** (heredan desc del padre; ver nota) |
| inertes título-only (desc ≤80 ch) | ~0 | no re-extraen (censadas aparte) |
| **candado — validadas humanas** | **6.326** | **sus TAREAS SÍ re-extraen** (el candado protege DECISIONES de matching en P4, no inputs — laudo) |
| nlp_version actual | 11.3.0 (69.767) + 11.3.1 (28.942) | todo v11 |
| matching_version actual | 3.6.0 (90.785) + 3.5.2 (6.301) + spec_h (38) | base del re-matching P4 |

> Nota sub-ofertas: las 541 tienen id `padre_N` y descripción heredada del padre. Re-extraerlas
> por separado re-correría el mismo cuerpo → decisión pendiente (¿re-extraer solo el padre y
> re-derivar el split, o dejarlas?). Lo marco para P1-paso-2, no bloquea la medición.

---

## P1 — La re-extracción (medida con 1 tanda, NO ejecutada en total)

Pipeline **N1 (limpiar_chrome) → prompt v12.4 → N3 (postfiltro)**, modelo **qwen2.5:14b**.
Runner nuevo: `scripts/ops/reextraccion_tareas_v124.py` — escribe a tabla de **STAGING**
(`ofertas_nlp_tareas_v124`), NO a `tareas_explicitas` viva. Resumible (saltea lo ya hecho).
Orden: más recientes primero (`scrapeado_en DESC`).

### 1-tanda checkpoint (40 ofertas, con la GPU "libre")
```
40 ofertas en 4,0 min = 602 of/h   (ramp 480→602: las primeras 10 incluyen la carga del 14b)
vacías = 8 (20,0%)   errores = 0
n_tareas: media_global 5,40 · media_no_vacío 6,75 · max 13
```
Calidad: la media de ~6,8 tareas en avisos no vacíos y el 20% de vacías coinciden con el
re-gate y el contraste — el método se comporta igual en producción. 0 errores.

### Estimación honesta de duración
A **602 of/h** (y no observé que la GPU "libre" fuera más rápida que el ~650 contended de antes
— tomo 602 como el número real, no uno optimista):

| Universo | A 602 of/h |
|---|---|
| ~98.168 primarias | **~163 h ≈ 6,8 días continuos** |
| (si sube a ~650 steady) | ~151 h ≈ 6,3 días |

Es un run de **~1 semana de GPU**. Resumible por tandas (background, tmpfs, `run_con_tmpfs.sh`),
así que puede correr en ventanas sin bloquear otras cosas, pero el reloj de pared es ese.

---

## EL GATE — necesito tu decisión antes de P1-total

1. **¿GO a la re-extracción TOTAL (~98K, ~6,8 días)?** ¿O una **dirigida** (p. ej. solo las
   que hoy abstienen / las familias con más error / las más recientes N)? El título dice TOTAL;
   confirmo antes de comprometer la semana de GPU.
2. **¿Reemplazo en vivo o staging primero?** Mi diseño escribe a staging; el swap a
   `tareas_explicitas` sería un paso posterior con otro OK (así el P1-cierre te muestra censo +
   distribución + muestra de 15 ANTES de pisar las tareas vivas). Confirmá que preferís ese orden.
3. **Sub-ofertas (541):** ¿re-extraer solo padres y re-derivar el split, o incluirlas?

Nada de P2/P3/P4/P5 arranca hasta cerrar P1. **Cada transición, tu OK.**

---

## PARALELO (hecho, no bloquea): fronteras para Cyn
`exports/cyn_backlog/N_fronteras_v124_2026-10-05.md` — las 4 fronteras con evidencia trazable:
(1) compliance-seguridad caso-4 vs RG-TAR-009 (las dos prosas tuyas lado a lado), (2) contador
junior → [] (función genérica en "Experiencia:"), (3) multipuesto inline RG-TAR-003 (textil
8126765799), (4) los 5 REVISAR con su tabla. Listo para convertir a Excel.
