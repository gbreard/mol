# [FRENTE B — COSECHA] Material de Cyn procesado: taxonomía v2, tanda de cosecha al diccionario, evidencia Eje 4

Procesa los dos documentos que devolvió Cyn — la sesión Gerardo+Cyn (`docs/Sesion_Cyn_familias.docx`,
julio 2026, texto + 7 imágenes EMF transcriptas y verificadas) y el lote de
construcción/instalaciones que trabajó por su cuenta (`docs/REGLAS-v2.xlsx`, 73 filas +
24 grupos consolidados). **Precedencia: donde ambos tocan la misma familia, el Word manda.
La prosa de Cyn es la verdad de dominio: se estructura y rutea, textual, sin reescribir.**

## Qué entra

### 1 · Taxonomía v2 — el insumo del traductor (`exports/cyn_backlog/taxonomia_contexto_cyn.md`)

De 6 a **32 familias-raíz (28 definidas / 4 pendientes-Cyn, incluida «monitoreo»)**. Estructura por familia:
raíz · árbol (prosa textual de Cyn) · casos de evidencia (matcher dijo → Cyn corrigió) ·
fuente · estado.

- Del Word: conducción (gerente/encargado/responsable/jefe) · operador/programador ·
  analista · asesor/advisor/consultor · **vendedor** (árbol del caso viajante) + 5
  mini-familias de los casos sueltos NO estables.
- Del Excel: administrativo · electricista · encargado de edificio · facilities ·
  aprendiz/verticales · sobrestante · instalador · ayudante · colocador ·
  mampostero/albañil + ramas nuevas en técnico/arquitecto/pintor/herrero/operario.
- De la respuesta post-punto-de-control: **desarrollador** (2512.4) y **chofer/conductor**
  (8332.8, el árbol más ramificado del material — complementa sin pisar los deslindes de
  operario/depósito).
- Fusiones Word-manda: supervisor de instalación (Word más fino) · analista de oficina
  técnica (rama del árbol de analista del Word). Las 6 familias v1 conservadas tal cual.

### 2 · Cosecha al diccionario — 153 entradas nuevas (72 → 225)

Bandeja completa con **dry-run exacto** (réplica del resolver real: normalización +
longest-match + contextos + resolución por esco_code, sobre 69.794 ofertas; el motor
reprodujo el 141 histórico de vendedor viajante): `exports/puente/bandeja_cosecha_2026-07-13.md`.

- 148 candidatas de la bandeja original + 22 de la respuesta de Cyn; códigos 100%
  validados contra catálogo (G4/G13 «7412 técnico de ascensores» → `7412.7` por label,
  flageado; jamás inventado).
- **Confirmadas por Gerardo en el punto de control** → 3 tandas de 50 + tanda 4 de 3 vía
  `aplicar_candidata` (squash por tanda: `c3afb3ff` / `47cc2019` / `c0970528`), TEST verde
  entre tandas, 0 rechazos, 0 no-op, `_linaje` por entrada.
- **vendedor viajante → 3322.1 (blast 141)**: HOLD de P5 DESTRABADO por decisión escrita
  de Cyn (criterio textual en taxonomía, familia «vendedor»).
- Discrepancias resueltas por Cyn: desarrollador python 2512.9→**2512.4** · chofer de
  recolección de residuos 8332.2→**8332.8** (cargadas con el código corregido).
- HOLDs ≥50: **NO cargadas** técnico electromecánico (334) · jefe de obra (181) · técnico
  electrónico (162) · empleado administrativo (61) · auxiliar de depósito (53) — raíces
  cubiertas por árboles, material del traductor (así marcadas en la bandeja).
- **Tanda 4** (`cosecha-2026-07-13-t4-holds`) — decisión final de Gerardo con las muestras
  de 10 a la vista: **CARGADAS** electricista industrial (63) · operario de carga y
  descarga (60) · operario de logística (65, incluye el caso «con habilitación de
  autoelevador»: requisito accesorio, no tarea principal). **NO cargada** operador de
  monitoreo (54): la heterogeneidad de la muestra (NOC/plataformas vs CCTV/seguridad vs
  satelital/flota) la define como CONDICIONAL → familia pendiente «monitoreo» en taxonomía
  + devoluciones para que Cyn escriba el árbol. Diccionario final: **225 entradas**.

### 3 · Re-juicio versionado en la fixture (sin pisar)

`tests/fixtures/clasificador_candidatas_fixture_2026-07-03.json` — HJ v1 conservado en
`juicio_humano_historial`, v2 con `juzgado_por: Cyn`:

- **Estudiante de Abogacía**: 3411.4 → 3411.7 (asistente jurídico), sigue CONDICIONAL.
- **Medio Oficial de Mantenimiento**: 7233.8.1 SOLO maquinaria agrícola, sigue CONDICIONAL.
- **Desarrollador Python Sr**: 2512.9 → 2512.4, estable (VOCABULARIO); señal esperada pasa
  a `S3-conflicto` — la corrección histórica choca con la entrada nueva del dict: es la
  detección retroactiva funcionando, documentada en el caso.

**La matriz del clasificador NO cambia** (33 CONDICIONAL / 1 VOCABULARIO) — tests verdes.

### 4 · Evidencia Eje 4

`exports/puente/evidencia_errores_matcher_REGLAS_2026-07-13.md` — **57 pares**
(esco extraído por el sistema → esco correcto de Cyn) con raíz, denominación y título
ejemplo (la columna id_oferta vino vacía en todo el lote). Mismo molde que los 104
override-duro. Patrón consistente con F0.6: error mayormente intra-familia técnica
(7412↔7411↔3114) + cruces de ISCO-1 completos (vendedor→encuadernador, agrónomo→NOC).

### 5 · Devoluciones para Cyn

`exports/cyn_backlog/devoluciones_para_cyn_2026-07-13.md` (formato para reenviar):
2 MAL EXTRAIDA (sumadas al issue NLP `2026-06-30_bug_limpieza_titulo_nlp_ruido.md`) ·
REQUIERE REVISION (montador de hormigón, con su nota citada) · 13 filas incompletas de
Hoja 1 · inconsistencia fila 60 (código dice ingeniero 2153, árbol dice técnico 3522.1) +
G24 sin variantes. Las 2 discrepancias NO van (ya resueltas).

## Decisión C2 de Cyn (registro — se diseña en spec aparte, acá NO se construye)

Cyn dijo **SÍ** a la bandeja UI. Requisitos textuales: *«la denominación, la ocupación
propuesta, el código ESCO, cuántas ofertas afectaría y algunos ejemplos de avisos reales.
También me serviría ver las tareas principales del aviso, porque muchas veces el título solo
no alcanza para confirmar una ocupación. No le agregaría demasiadas cosas para que no quede
cargada ni difícil de usar.»* Freno de alto impacto se mantiene: *«me parece importante que
las propuestas de alto impacto queden frenadas para revisar antes de que entren al
diccionario.»* Ubicación: *«dentro de la pantalla de Validación… como "Propuestas del
diccionario" o "Correcciones para confirmar".»*

## Verificación

- Tests del puente (27) + G3/SPEC-J (16): **verdes** antes, entre tandas y al cierre.
- Suite amplia (`tests/` sin harness/scraping): 562 passed; los 29 failed + 66 errors son
  **preexistentes** — verificado por experimento de aislamiento: los gold-set de matching
  fallan idéntico (4/49) con el diccionario de main y con el de la cosecha; el resto es
  ambiental (red, tablas de BD locales, drift de configs NLP no tocadas por este spec).
- **Regresión TEST reservado (93): 1 oferta tocada** — `1117951568` (Desarrollador PYTHON
  Sr), movimiento `sin-dict` → `2512.4`, exactamente el target que Cyn dictó en su
  respuesta. No es fuga: la entrada no se generó desde el TEST sino desde la consolidada
  de Cyn; es recurrencia del vocabulario (el loop funcionando). Resto del TEST: 0 tocadas (tanda 4 incluida: 0).
- Working tree blindado: adds explícitos; protegidos (`config/training_pairs.json`,
  `metrics/gold_set_history.json`) y ~40 sin-trackear preexistentes intactos.
- Wizard, matcher, reglas de matching y canal de skills: sin tocar. `tests/harness/`: solo lectura.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01HHRZkW8Liq29FEBPPCow9p
