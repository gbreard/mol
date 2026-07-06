## feat(spec-s1c-puente): sugeridor + escritura git-first + primera tanda (mesa de Cyn, fase 1)

Reconstruye el puente validación→diccionario: reemplaza al `get_rule_suggestions` roto
(error 42804) por un sugeridor que lee las correcciones del wizard de Cyn, las clasifica
con un clasificador ajustado en seco, y las presenta en una bandeja mínima sobre la que
Gerardo confirma. Las confirmadas se escriben **git-first** al diccionario argentino que
el matcher lee. **Es G3 automatizado**: lo que antes era Excel a mano + carga por Claude,
ahora las correcciones del wizard auto-proponen las mismas entradas denominación→esco_code
con preview + confirmación.

Encuadre: **triage seguro + bandeja ordenada, no carga masiva.** Se industrializa la
generación de candidatas; la decisión es humana, caso por caso.

### P1 — Clasificador congelado + fixture-contrato
`config/clasificador_candidatas.json` (v2.0). Separa correcciones en VOCABULARIO / CONDICIONAL
/ RUIDO. Validado en seco: **0 falsos vocabulario sobre 34 casos** (barra pasada). Señales:
S1(familias azules de la taxonomía de Cyn + 12 blancas) → S1b(dict-contextos dinámico) →
S3(conflicto retroactivo) → guard-profundidad(≥2pts) → S2(forma). Head anclado.
Fixture con juicio humano atribuido (versionable, no se pisa) + test que la reproduce exacta.

**Estatus del clasificador: AJUSTADO sin contraejemplos sobre 34 casos — NO validado
out-of-sample.** Los ajustes se diseñaron mirando los 5 errores de la v1 y se midieron sobre
las mismas 34. La generalización se audita en operación: **las primeras 20 correcciones
nuevas se auditan contra el clasificador** (política documentada).

### P2 — Sugeridor (C1) + bandeja mínima
`scripts/puente/sugeridor_candidatas.py`. Lee `validacion_correcciones` por presencia de
`ocupacion_corregida` (no por flag; se guardan con `validacion_humana='revisar'`), resuelve
`esco_uuid→esco_code` contra el catálogo (patrón G3, irresoluble=PENDIENTE, nunca inventa),
clasifica, detecta conflicto retroactivo. Emite `bandeja_<fecha>.md` ordenada por señal con
preview de impacto (`preview_rule_impact`) y **solape de pileta** (skills envenenadas de
terminologia pendientes de reproceso, D1/F0.4b — contaminación visible).

Corrida: 34 → **1 AUTO + 4 A-CONFIRMAR + 29 CONDICIONAL**. 0 divergencias vs la fixture.

### P3 — Los 29 condicionales pre-procesados para el traductor
`exports/puente/condicionales_para_traductor_2026-07-03.md`, cruzados con los árboles de Cyn:

| | N |
|---|---|
| **CUBIERTO-POR-ÁRBOL** | **7** (operario 4 + técnico 3 — Cyn ya escribió el árbol) |
| **FAMILIA-NUEVA** | **22** (blancas + dict-contexto + forma + guard — sin árbol) |

**⭐ El 7/22 es la agenda de la sesión con Cyn — el dato que ordena el Eje 4.** El traductor
arranca por las 7 CUBIERTO (especificación de Cyn ya hecha); las 22 FAMILIA-NUEVA son el
orden de trabajo: familias sin árbol que necesitan que ella defina el contexto.

### P4 — Escritura git-first (C3) + reconciliación del CHECK
`aplicar_candidata` escribe candidatas confirmadas con esquema post-G3 (esco_code validado,
`_linaje` por entrada), respeta longest-match (rechazo ruidoso ante colisión), squash por
sesión = 1 commit. **Git-first por construcción**: el matcher lee el JSON local; el editor de
Sinónimos (que stripea esco_code) NO es alcanzable (test estructural por AST).

Migración **058** reconcilia el drift del CHECK de `pipeline_commands`: el comando que
faltaba era **`scrape_indeed`** (el poller ya lo manejaba, la tabla lo rechazaba). Agrega
`aplicar_candidata`. CHECK 13→15, alineado con el COMMAND_MAP.

Control P4 verificado: candidata sintética end-to-end (poller wiring → aplica → linaje →
commit → espejo → matcher resuelve en memoria → revert limpio, protegidos intactos).

### P5 — Primera tanda real (dry-run exacto + HOLD)
Dry-run de blast por **denominación exacta** vía el resolver real (normalización + longest-
match, entrada en memoria, ofertas que *cambian* — no substring):

| candidata | esco_code | blast exacto | resultado |
|---|---|---|---|
| vigilador/a | 5414.1 | — | **NO-OP** (ya en dict desde G3, mismo código) |
| técnico de ascensores | 7412.7 | 14 | **WRITE** (<50; su preview dio timeout → dry-run es su único blast) |
| asesor bienes raíces | 3334.3 | 3 | **WRITE** (<50; la variante amplia 'asesor inmobiliario' se excluyó, subía a 121) |
| vendedor viajante | 3322.1 | **141** | **HOLD ≥50** (no escrita — reportada) |
| office host coworking | 4226.1 | 0 | **REDUNDANTE** (ya cubierta por 'office host - red de espacios de coworking → 4226.1') |

**Tanda real escrita = 2** (técnico de ascensores, asesor bienes raíces), un commit (squash).
El HOLD de vendedor viajante y la redundancia de office host son el safeguard funcionando:
la tanda esperada de 4 writes se redujo a 2 por el dry-run exacto + regla HOLD + idempotencia.

Verificación de dominio 1×1 de las 5: vigilador/a=vigilante de seguridad ✓ · técnico de
ascensores=técnico de ascensores ✓ · asesor bienes raíces=agente inmobiliario ✓ · vendedor
viajante=representante comercial (HOLD, correcto pero alto blast) · office host=recepcionista
(ya cubierta) ✓.

**Regresión TEST reservado: 0** — ninguna de las 93 ofertas del split TEST es tocada por las
2 entradas nuevas (no-recurrencia → no-romper, probado sin correr el matcher pesado).

### Deudas registradas del puente
- **(a)** El preview-por-head se cae por timeout **justo en heads amplios** (los de mayor
  riesgo, ej. `tecnico`=921) → el mecanismo confiable para el flujo continuo es el **dry-run
  local por variante exacta**. El preview Supabase queda best-effort.
- **(b)** El HOLD debería disparar también por **heterogeneidad** de las ofertas matcheadas
  (sectores/ISCOs dispares), no solo por conteo — el "operario de producción → 72" era
  peligroso por amplitud semántica, no por frecuencia.

### Nota — las 13 URIs huérfanas (condición del harness, ya resuelta en PR #50)
Rastreadas como paso 1 del fix de terminologia (PR #50, mergeado): 10 NO son fabricadas
(URIs reales en embeddings 14.257, ausentes de SQLite 14.247 — desync SY-02, deuda
registrada); 3 son residuo de un backup viejo (`skills_rules.json.pre_spec_l...bak`). El
`skills_rules.json` actual tiene 0 fabricadas. **No queda fuente viva de fabricación de URIs.**

### Diferido
**C2 (UI de bandeja)** NO se construye acá — a demanda real post-sesión con Cyn. Su E2E
(Playwright) saldaría la deuda E2E del wizard.

### Tests
68 verdes (clasificador 9 · sugeridor 8 · aplicar_candidata 10 · poller 20 · G3/SPEC-J/
terminologia regresión 20 + 1). Vitest territorio Fábrica/pipeline_commands: 50 verdes.
`tests/harness/` no ejecutado (reservado). Política de operación:
`docs/operaciones/POLITICA_PUENTE_MESA_CYN.md`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
