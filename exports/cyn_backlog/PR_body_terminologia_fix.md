## fix: terminologia_argentina_skills envenenada — migración al canal sano + fallo-ruidoso

`config/terminologia_argentina_skills.json` estaba **VIVO en el camino de decisión** (PASO 0 de skills, prioridad 0.95 sobre semántico) con **48 de 49 URIs fabricadas**. Blast-radius medido: **30.402 skills persistidas / 12.841 ofertas** con origen terminologia (café verde vivo, a escala). Decisión de Gerardo: **variante migración** — mover el núcleo logístico válido a `skills_rules.json` (fuente única sana de skill-forcing) y vaciar terminologia. Primera ejecución del mapa de consolidación: un repositorio menos.

### Paso 1 — Veredicto de las 13 URIs fabricadas huérfanas
De 61 URIs fabricadas persistidas, 48 son de terminologia. Las otras 13:
- **10 = desync catálogo/embeddings** (URIs reales en embeddings 14.257 pero ausentes de `esco_skills` SQLite 14.247). NO es fabricación → deuda SY-02 (D3).
- **3 = fabricadas de verdad** (`a1a1a1a1-0000`, `f2f2f2f2-0000`, `1e47a5a8` → "lavar platos"/"preparar ingredientes"/"mantener limpieza"), origen `regla`, provienen de **`skills_rules.json.pre_spec_l_simple_124702.bak`** (backup viejo).

**Veredicto:** vaciar terminologia **cierra el grifo del café verde de skills**. El `skills_rules.json` actual tiene **0 URIs fabricadas** (38 reales, verificado) — el grifo de reglas ya se había cerrado en SPEC-L; los 3 rows son residuo histórico. No queda ninguna fuente **viva** de fabricación.

### Paso 2 — Los 15 pares migrados (aprobados por Gerardo)
10 reglas nuevas `RS28..RS37` en `skills_rules.json`, 15 skills, **todas con URI real resuelta por preferred-label exacto** (patrón G3). `cross docking → logística` se excluyó (a emergentes, término genérico). Se descartaron 5 sub-skills que no resolvían (no se fabrica). Bare `"rf"` se dejó fuera de los triggers (landmine de substring: matchea "surf"/"performance") — se conservan sus aliases específicos (pistola rf, scanner rf, radiofrecuencia).

| regla | trigger (título o tareas) | skills forzadas (URI real) |
|---|---|---|
| RS28_picking | picking | preparar pedidos · gestionar el inventario |
| RS29_rf | pistola rf, scanner rf, lector rf, radiofrecuencia | utilizar aparatos para escanear el código de barras |
| RS30_armado_de_pedidos | armado de pedidos, preparacion de pedidos, order picking | preparar pedidos · empaquetar mercancías |
| RS31_paqueteria | paqueteria, empaque, embalaje, packaging | empaquetar mercancías · procedimientos de empaquetado |
| RS32_e_commerce | e-commerce, ecommerce, tienda online, venta online | sistemas de comercio electrónico · negocio electrónico |
| RS33_carga_y_descarga | carga y descarga, descarga, estiba, desestiba | realizar operaciones de carga y descarga · mover objetos |
| RS34_zorra | zorra, zorras, transpaleta, traspalet | realizar operaciones de carga y descarga |
| RS35_autoelevador | autoelevador, clark, montacargas, elevador, carretilla elevadora | manejar carretillas elevadoras |
| RS36_fifo | fifo, lifo, fefo | gestionar el inventario |
| RS37_pallets | pallets, pallet, tarima, europallet | apilar mercancías |

### Paso 3 — terminologia vaciado + fallo-ruidoso
- `terminologia_argentina_skills.json`: `terminos = {}`, marcado `_DEPRECADO`.
- `skills_implicit_extractor._extract_terminology_skills`: **fallo-ruidoso** (patrón Paso 0 G3) — si el canal se repuebla, una URI fuera del catálogo ESCO real **NO entra** al matching y se loguea `WARNING` visible. Helper `_valid_skill_uris()` valida contra la metadata de embeddings.
- **14 términos irreparables + cross docking → semilla de emergentes** (`exports/cyn_backlog/emergentes_terminologia_seed.json`). NO se tiran, NO se fabrican. Promover a `emergentes_pendientes` (Supabase) queda como paso siguiente (write a prod, flujo emergentes hoy dormido). Los 6 redundantes (deposito, stock, guardia, prepaga, community manager, crm) se **retiran** (ya cubiertos por keywords de skills_rules), no duplican.

### Paso 4 — Regresión en TEST (18/93 ofertas afectadas), matriz de 3 estados
Corrida del extractor de skills antes/después sobre las 18 ofertas del TEST que contienen algún término:

| estado | N | lectura |
|---|---|---|
| **perdió-fabricada** (bien, el objetivo) | **48** | exactamente las 48 URIs fabricadas removidas |
| **perdió-válida** (mal) | **1** | oferta 7347150394: label "preparar pedidos" (24c4beb4) |
| **ganó** (nuevas después) | **15** | **0 fabricadas** — todas reales (11 vía regla, 4 vía semántico) |
| **re-resolvió a disparate** (el peligroso) | **0** | ninguna oferta re-resolvió por semántico a algo incoherente |

**La única perdió-válida es benigna:** la oferta 7347150394 ("Operarios de deposito … picking") matchea primero `RS21_almacen_deposito` (regla existente), y por **first-match-wins** (D4) no dispara `RS28_picking`. Pero el semántico surfacea **"preparar los pedidos para el envío"** (ee5e2297, hermano de "preparar pedidos") + un **"realizar operaciones de carga y descarga" REAL** que reemplaza al fabricado. Concepto preservado, veneno eliminado. Las otras 8 ofertas afectadas recibieron sus skills forzadas vía las reglas nuevas.

"Cero URIs fabricadas" es tautológico — lo que importa es que **lo que quedó es correcto**: 0 re-resoluciones a disparate, 15 ganancias todas reales, 1 cambio de label con concepto preservado.

### Deudas registradas (con número) — `exports/cyn_backlog/DEUDAS_fix_terminologia.md`
- **D1 La pileta:** 36.809 filas fabricadas en ~15.986 ofertas persistidas. El fix corta el grifo, no vacía la pileta. Coordinar con candado F0.4b (no reprocesar acá).
- **D2 Observabilidad (→ índice harness):** `match_method`/`origen_tipo` hardcodeados; el origen real vive en `skill_tipo_fuente`. Casi produjo un diagnóstico falso de "canal muerto".
- **D3 Desync SY-02:** embeddings 14.257 vs `esco_skills` 14.247 = 10 URIs reales que fallan el JOIN. Cuantificado.
- **D4 first-match-wins:** skills_rules aplica 1 regla/oferta; migración additive→exclusive puede quedar sombreada (benigno, semántico cubre).

### Tests
`tests/matching/test_terminologia_veneno_fix.py` — 4 tests (terminologia vacía+deprecada; 10 reglas migradas con URI real; skills_rules sin ninguna URI fabricada; fallo-ruidoso rechaza URI no-catálogo). Todos pasan.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
