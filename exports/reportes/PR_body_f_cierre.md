# [FRENTE F] Cierre post-lote + pre-spec traductor

Junta los restos de verificación del lote (FRENTE D), las dos condiciones pre-spec
del traductor y los fixes chicos en cola. **Nada toca matcher, config de matching,
diccionario ni wizard.** Reporte completo: `exports/reportes/F_cierre_postlote_2026-08-03.md`.

## Lo medido (read-only)

- **P1 — precisión de la cosecha:** las 27 ofertas decididas por entradas nuevas del
  diccionario, verificadas una por una → **24/27 correctas**. Las 2 malas son
  diagnósticas: una entrada de denominación inestable (`técnico oficial`) que matcheó
  de más, y un caso de contexto comercial invisible al diccionario plano (la clase que
  el traductor resuelve).
- **P2 — gate de compilación labels→código:** parse reproducido de los árboles de Cyn
  (462 ramas): **68,4% resuelve a código único**, 12,1% multi-URI, 11,3% destino-abierto,
  8,2% no resuelve. **Piloto: técnico 74,5% única (arranca con pre-trabajo); vendedor NO
  TIENE ÁRBOL — no puede compilar** (decisión de spec pendiente).

## Artefactos y fixes (4 commits + docs)

- `exports/cyn_backlog/preguntas_destino_abierto_2026-08-03.md` — 52 preguntas listas
  para Cyn (chofer/conductor aparte: familia entera espera sesión). NO enviado.
- `fix(sy02)`: las 10 URIs del drift son conceptos ESCO **obsoletos** (sin label ES);
  insertadas al catálogo con `status='obsolete'` → +29.745 filas de skills con JOIN
  resuelto. Fix estructural (sacarlas del índice de embeddings) queda como deuda.
- `feat(traductor)`: `config/mapeo_reglas_familias.json` — las 357 reglas clasificadas
  (CUBIERTA/AMBIGUA/HUÉRFANA) con dudosas marcadas; CUBIERTA pondera 28,1% vs 26,1%
  de la referencia M1.
- `feat(ops)`: `scripts/ops/run_con_tmpfs.sh` — patrón anti-9p con guardas y sha256,
  smoke-test OK. Prerequisito de la corrida semanal de NLP.
- `docs`: drift de versiones en CLAUDE.md corregido (NLP 11.3.1 / Matcher 3.5.8).

## Tests

Baseline riguroso en worktree limpio: **main y este branch dan EXACTAMENTE lo mismo
(42 failed + 81 errors) — cero fallas introducidas por el PR.** El drift es preexistente:
tests que pinean el config v1.1.0 (35 reglas) contra el override Supabase vigente (51),
3 casos gold-set que pinean `titulo_esco_code` de filas viejas que nunca lo tuvieron, y
fixtures locales no versionadas. Detalle y evidencia en el reporte. La suite necesita su
propio frente de saneamiento.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
