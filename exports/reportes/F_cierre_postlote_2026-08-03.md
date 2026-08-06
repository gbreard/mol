# [FRENTE F] Cierre post-lote + pre-spec traductor — 2026-08-03

> Primer reporte bajo la regla nueva: el resultado de cada frente vive TAMBIÉN como
> archivo commiteado, nunca solo en el chat. Branch `chore/f-cierre-postlote`.

## P1 — Verificación de las 27 (precisión de la cosecha)

**Resultado: 24/27 correctas (88,9%), 2 mal, 1 dudosa.** Revisadas una por una
(título + tareas vs destino asignado; detalle en `scratchpad` del frente, ids abajo).

| Veredicto | id_oferta | Caso | Caracterización |
|---|---|---|---|
| ✗ MAL | 8268897316 | "Técnico Oficial Múltiple" → especialista en trabajos verticales 7119.4 | **Entrada de denominación NO estable** («técnico oficial») cargada con target hiper-específico de un contexto puntual. Las tareas son de ayudante de mantenimiento general. Matcheó de más — exactamente el riesgo que la regla G3 ("alto blast solo en denominación ESTABLE") anticipaba. |
| ✗ MAL | 2184448 | "Arquitecto Junior con Perfil Comercial" → arquitecto 2161.1 | Tareas 100% comerciales (presupuestos, clientes, estrategia). **Límite estructural del diccionario plano**: decide por título y el contexto invierte el rol. El traductor (tareas) es el fix de esta clase. |
| ? DUDOSA | 2182150 | "Ingeniero Electricos - Especialista Energia Utilidad" → ingeniero eléctrico 2151.1 | Tareas de análisis documental/regulatorio (BPO energético), no de ingeniería eléctrica. Misma clase que la anterior, con menos certeza. |
| ✓ (24) | resto | electricista industrial ×6, operador NOC ×4, ingeniero eléctrico/electricista ×5, director/coordinador de obra ×4, instrumentación, electricista de planta ×2, arquitecto dibujante ×2, administrativo de mantenimiento, arquitecto proyectista | Correctas — incluye varias "débiles" defensibles (sin tareas, decididas por título inequívoco). |

**Lectura:** la cosecha tiene precisión alta (~89-93% según cómo se cuente la dudosa) y
sus 2 fallas son diagnósticas: (1) revisar la entrada `técnico oficial` del diccionario
(candidata a remoción o condición de contexto — NO tocada en este frente); (2) las otras
2 son la clase de error que el diccionario plano no puede resolver y el traductor sí.

## P2 — Tasa de resolución labels→código (gate de compilación del traductor)

**Método:** el output del barrido original (473 ramas) no está materializado en repo ni
sandbox (probablemente el reporte perdido que motivó la regla nueva). Se REPRODUJO el
parse desde `exports/cyn_backlog/taxonomia_contexto_cyn.md` (37 líneas `*Regla:*` con
`⇒` + 61 bloques citados «…corresponde a X; si…, a Y»). Resolución: match **exacto
normalizado** (lowercase, sin acentos, expansión de género `/a` incluso múltiple
«ingeniero/a técnico/a») contra labels preferidos (metadata 3.046) + alternativos
(tabla `esco_occupation_alternative_labels`). Jamás LIKE.

**Ramas parseadas: 462** (referencia: 473 — delta de parse propio, ±2%).

| Clase | n | % |
|---|---|---|
| **Resuelve única** | 316 | **68,4%** |
| Multi-URI (ambiguo) | 56 | 12,1% |
| Destino-abierto (disyunción) | 52 | 11,3% |
| No resuelve | 38 | 8,2% |

**Por familia (extracto; tabla completa en el output del script):** operario 89/103
única (86%), técnico 41/55 (75%), electricista 11/14, pintor 12/13; las peores en
no-resuelve: técnico (13), ingeniero (10, +5 multi-URI). Los no-resuelve son de dos
sub-clases: labels con variantes no exactas del catálogo («electricista de obras y
afines» es label ISCO, no ESCO; «técnico/a HVAC-R») y prosa no atómica (destino con
comentario pegado) — ambas necesitan resolución humana, que es exactamente lo que el
gate mide.

**⚠ Las familias del piloto:**
- **técnico: 74,5% única** — arranca con pre-trabajo acotado (14 ramas a resolver).
- **vendedor: NO TIENE ÁRBOL.** No aparece en la taxonomía (1 mención tangencial) ni en
  REGLAS-v2.xlsx. **El piloto vendedor no puede compilar hasta que Cyn entregue su árbol**
  — es la familia de mayor volumen de reglas planas (984 ofertas con raíz en el lote).
  Decisión para el spec: reemplazar vendedor en el piloto o priorizar su sesión con Cyn.

## P3 — Preguntas destino-abierto (artefacto listo, NO enviado)

`exports/cyn_backlog/preguntas_destino_abierto_2026-08-03.md`: **52 preguntas** (46
generales + 6 de chofer/conductor), cada una con familia, prosa textual de Cyn,
candidatos con código resuelto donde aplica, y la pregunta del sub-criterio. La
referencia contaba 26 "puras"; se incluyeron también las semi-abiertas
(destino + excepción condicional) — mejor preguntar de más. **Chofer/conductor va
aparte con la nota: 6 de sus 9 ramas parseadas son destino-abierto → la familia entera
espera su sesión antes del traductor v1.**

## P4 — Fixes

**4.a SY-02 (commit `fix(sy02)`):** las 10 URIs del drift resultaron ser **conceptos
ESCO OBSOLETOS** (iso-thes:status=obsolete en el RDF v1.2.0, sin label español —
"mobile agriculture", "telehealth", "six sigma", "be a role model"…). El catálogo las
excluyó con razón; el índice de embeddings las retuvo y las sigue atrayendo
(la dominante: 12.943 filas históricas + 10.230 del lote). Parche aplicado: insertadas
con `status='obsolete'` y label EN → **+29.745 filas de skills ahora resuelven su JOIN**.
Quedan 51 URIs fabricadas históricas fuera de catálogo (pileta, reproceso hacia atrás).
**El fix real es sacar las 10 del índice de embeddings** (toca matcher → deuda SY-02).

**4.b Mapeo M1 (commit `feat(traductor)`):** `config/mapeo_reglas_familias.json` — 357
reglas clasificadas (CUBIERTA 109 / CUBIERTA-pendiente 52 / AMBIGUA-a 127 / AMBIGUA-b 1
/ HUÉRFANA 68), con familia, criterios en `_meta` y `asignacion: dudosa` donde
corresponde. Validación contra la referencia: CUBIERTA pondera **28,1%** de las ofertas
decididas por reglas (vs 26,1% migrable-ya del M1 original — calibra). AMBIGUA-a quedó
amplia (31,3% ponderado; las raíces de conducción solapan) — todas marcadas dudosas,
para afinar cuando aparezca el M1 original.

**4.c Script tmpfs (commit `feat(ops)`):** `scripts/ops/run_con_tmpfs.sh` — la ceremonia
completa del incidente 9p con guardas (espacio, BD libre, sha256 en ida y vuelta,
quick_check, abort conservador). Smoke-test del ciclo completo: OK.

**4.d Drift de docs (commit `docs`):** CLAUDE.md corregido — NLP v11.3.1 y Matcher
v3.5.8 en los 11 sitios de estado-actual; anotaciones históricas conservadas.

## Tests

Suite Python completa post-4.a, con baseline riguroso: **en el mismo entorno limpio
(worktree sin configs locales no versionadas), main y este branch dan EXACTAMENTE lo
mismo: 42 failed + 81 errors** — cero fallas introducidas por el frente. El drift es
preexistente y de tres clases: (1) `test_nlp_validation_rules` pina el config v1.1.0
(35 reglas) mientras el config efectivo vía override Supabase tiene 51 con otro schema;
(2) 3 casos del gold set pinean `titulo_esco_code` que filas viejas
(`validado_claude_C1`) nunca tuvieron — verificado idéntico en snapshot pre-frente;
(3) tests con dependencias de red o fixtures locales no versionadas
(`test_aplicar_candidata`, `test_sugeridor_candidatas`: FileNotFoundError en checkout
limpio). La suite necesita su propio frente de saneamiento — queda como pendiente 6.

## Pendientes que deja este frente

1. Árbol de **vendedor** — bloqueante del piloto del traductor tal como está especificado.
2. Sesión **chofer/conductor** (mayoría destino-abierto) + envío de las 52 preguntas cuando Gerardo decida.
3. Entrada `técnico oficial` del diccionario — candidata a revisión (evidencia en P1).
4. SY-02 estructural: remover las 10 obsoletas del índice de embeddings + reconciliación continua.
5. Las 51 URIs fabricadas históricas — esperan el reproceso de la pileta.
6. Saneamiento de la suite de tests: 42F+81E preexistentes en main (tests pinean
   configs viejos vs override Supabase; fixtures no versionadas; granularidad SPEC J
   sobre filas pre-SPEC J).
