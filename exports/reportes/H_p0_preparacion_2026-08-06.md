# [FRENTE H — P0] Preparación — 2026-08-06

Branch `spec/e4-traductor-piloto`. Incluye la bajada del re-laudo P0.a.4 (hub-set).

## P0.a.1 — Material y baseline
Fuente primaria + molde + mapeo + taxonomía + fixture de las 34 verificados presentes.
Fixture de las 34: **verde (9 tests), intocable**. Suite general: baseline conocido del
frente F (42F+81E preexistentes en main, ambientales) — sin cambios introducidos.

## P0.a.4 — Re-laudo bajado (hub-set)
- `config/hubs_activos.json`: hub-set del piloto **declarado NO activo** — 10 hubs:
  contable {1,2,3,4,15} + vecinos-hub directos {36 auditor forense, 58 empleado de
  oficina} + vendedor {16,51,52}. Activo gobierna el TRIGGER, no el destino.
- Grafo de las 900 aristas → `exports/analisis/grafo_D_88_2026-08-06.json` (artefacto
  de análisis: 284 hub→hub + 616 hub→satélite). `clusters_traductor.json` eliminado.
- **Nota de sizing declarada**: el hub-set completo porta 120 reglas; el "~25 a
  compilar" del laudo se sostiene compilando las PORTANTES (hub 1 ya compilado,
  inclusiones de vecinos + D críticas) y dejando la cola como `regla_sin_compilar`
  (telemetría, test 12) — se explicita en el informe de P2.
- Pendiente: `RELAUDO_HARNESS_clusters_hubset.md` aún no está en el repo (lo ubica
  Gerardo) — se commiteará junto a este registro al llegar.
- **Lección de método (del re-laudo, para la adenda del índice):** una estructura
  estática derivada del material experto debe validarse contra el grafo real ANTES de
  volverse precondición de runtime.

## P0.a.2 — Observabilidad
Migración `026_arbol_contexto_observabilidad.sql` APLICADA: columnas `arbol_hub_id`,
`arbol_regla_id`, `arbol_camino`, `arbol_traza_json` (+índice) en
`ofertas_esco_matching`; persistencia del matcher extendida (30/30 columnas-placeholders
verificado); **MATCHER 3.5.9**. La traza registra el campo de cada match (guarda b).

## P0.a.3 — Limpiezas (con dos hallazgos que valen más que la limpieza)
- **`técnico oficial` retirada del diccionario** (a `_retiradas`, con motivo y evidencia
  FRENTE F: denominación inestable, target hiper-específico, matcheó de más).
- **P-01: verificado ya-seco** (S1C-G3 enterró la inversa LIMIT-1; hoy mapeo explícito
  + fallo ruidoso). Blast actual: 0 esco_code muertos en dict; 21 entradas pre-G3 sin
  esco_code (granularidad, conocidas).
- **"4 target-muerto": NO identificables en el repo actual** — las tres verificaciones
  (código-existe / label-exacto / código≠ISCO) dan 0. O ya se corrigieron o la lista
  vive en el hilo del harness — pedirla si sigue vigente.
- **Hallazgo 1 (drift silencioso)**: el matcher v3 evalúa un set FIJO de claves e
  ignora las desconocidas EN SILENCIO. `tests/matching/test_rules_schema.py` (nuevo)
  lo congela: regla nueva con clave no-implementada FALLA.
- **Hallazgo 2 (guardas jamás aplicadas)**: **R94** (`nlp_sector_es`) y **R95**
  (`nlp_area_es`) tienen guardas NLP escritas que v3 nunca evaluó — **disparan más
  ancho que su diseño** desde siempre. Documentadas en `GUARDAS_NO_APLICADAS`
  (pendiente Eje 4: implementar la guarda o revalidar con Cyn); NO se bendijo el
  comportamiento ancho retirando las claves. R4/R6/R7/R9 son priorización legacy
  (rama aparte), R10/R11 ya inactivas. R49: clave de acción inerte retirada (cero
  cambio de comportamiento).
- **Método**: mi primera detección estática casi desactiva 4 reglas VIVAS (R4 decidió
  694 ofertas del lote de julio) — la verificación de blast en BD antes de tocar la
  frenó. Queda como recordatorio del protocolo.

## P0.a.5 — Auditoría de los títulos compartidos: PUNTO DE CONTROL PENDIENTE
Son **76** (no 62 — el conteo viejo venía del bug de extracción «X o Y» del G).
Recomendación: 45 INEQUÍVOCO / 31 CONTEXTUAL, con la frontera discutible señalada.
**Esperando la decisión de Gerardo** (`H_p0a5_auditoria_62_2026-08-06.md`). Nada
retirado: los CONTEXTUAL se retiran recién en el commit de activación de su hub (P4).

## P0.a.6 — Diff estático de destinos (unidad: grupo/hub-set)
**23 destinos presentes en el árbol viejo y ausentes de las 88**, concentrados en
**operario (44 brutos → cola textil/mecatrónica/impresión)** y técnico (10). Van a
validación por casos con ambas fuentes (`scratchpad/diff_destinos_p0a6.json`).
Electricista, herrero y albañil: 0 divergencias — las 88 los absorben completos.

## P0.b — Despachado
`exports/cyn_backlog/conflictos_y_preguntas_cyn_2026-08-06.md`: los 5 conflictos con
ambas fuentes citadas + trazabilidad 904→900 + la regla 11 con 0 D. Las 5 entradas en
conflicto NO compilan hasta respuesta de Cyn.
