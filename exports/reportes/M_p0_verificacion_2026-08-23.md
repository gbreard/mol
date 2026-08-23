# M — P0: verificación previa. **PARADA ANTES DE P1**

**Fecha:** 2026-08-23 · **Branch:** `feat/export-colegas-postL` · **Todo read-only.**

**Veredicto:** P0.1 (corpus) y P0.3 (artefactos) cierran. **P0.2 no**: el `05b` actual no puede
producir el export post-L, y la razón no se arregla extendiendo el script. P1 queda bloqueado a la
espera de una decisión de alcance que no corresponde tomar acá.

---

## P0.1 — El corpus está post-L y completo ✅ (con deriva menor, explicada)

| Métrica | Spec espera | Real | Estado |
|---|---:|---:|---|
| Ofertas con NLP | 98.770 | **98.770** | ✅ exacto |
| Matching 3.6.0 | 90.826 | **90.846** | +20 |
| Candado validadas-humanas | 6.326 | **6.326** | ✅ exacto e intacto |

**El candado cierra exacto** con la definición del propio frente L (`L_cierre_2026-08-22.md:11`):
6.275 `validado` + 38 `en_revision` + 13 `rule_manual_fix` = 6.326. Verificado estructuralmente,
que es lo que importa: **ninguna de esas filas está en 3.6.0** (las 6.275 siguen en 3.5.2, las 38 en
`spec_h_rematch`) y **cero filas con estado de validación humana aparecen en 3.6.0** — el rematch no
las tocó. No hubo fuga.

Fuera de 3.6.0 hay 6.339 filas: el candado de 6.326 más 13 `validado_claude` que tampoco se
re-matchearon — es el "remanente 13" ya documentado en `L_p3_medicion_2026-08-22.md:62`.

**El +20 es deriva del pipeline, no un faltante.** El 90.826 del spec viene de
`BACKLOG_NLP_cierre_2026-08-23.md:19`, donde mide *"filas con `isco_code` y `esco_occupation_uri`
poblados"* **en la ventana de esa operación**, no el universo 3.6.0 completo. El pipeline siguió
corriendo hasta el 2026-08-23 02:26. El corpus está más completo de lo que el spec asumía, no menos.

**Hallazgo lateral:** 50 filas en 3.6.0 sin `isco_code` (0,055%), todas `semantic_fallback_v3`,
matcheadas entre el 20 y el 22/08. **Sí tienen `esco_occupation_uri`** — resolvieron ocupación pero
no código ISCO. No contradice el "cero nulos" del informe de cierre (ese medía el subconjunto del
backlog), pero conviene saberlo: en el export saldrían con ISCO vacío.

## P0.2 — El script `05b` ❌ **BLOQUEO**

**No corre sobre el corpus actual, y no por un problema de esquema: por la fuente.**

`05b_export_definitivo.py` no lee del pipeline. Lee de `escenarios.duckdb` — la foto del sandbox,
**del 10 de junio**. Corrido hoy sin cambios, regeneraría el archivo de junio idéntico: cero datos
post-lote, cero post-L, cero traductor.

Cuán vieja es la foto: `ofertas_dashboard` tiene **68.241** ofertas contra **97.185** con matching
en la BD viva — faltan 28.944 (30% del corpus). Su `matching_version` máxima es `spec_h_rematch`:
**no hay una sola fila 3.6.0** adentro.

Y no alcanza con reapuntar el `05b` a la BD viva, porque **dos de sus tres tablas fuente no existen
ahí** — son artefactos que produce el propio sandbox:

| Tabla que usa `05b` | ¿Está en `bumeran_scraping.db`? | Quién la produce |
|---|---|---|
| `ofertas_dashboard` | **No** | `01_descargar_snapshot.py` (JOIN materializado, decisión D-007) |
| `ofertas_skills` | **No** | `01_descargar_snapshot.py` |
| `ofertas_skills_clasificadas` | **No** | `02_clasificar_escenarios.py` (capa de escenarios) |

Esa última es la que alimenta `escenario`, `confianza_skill`, `es_comodin_skill`,
`es_transversal_empirica` y `flag_uri_fantasma` en `oferta_skills` — columnas documentadas en la
guía de colegas y que ellos usan.

**La cadena real para un export post-L es: `01` (re-snapshot desde la BD viva) → `02`
(re-clasificar escenarios sobre el corpus nuevo) → `05b` extendido.** Eso es bastante más que
"extender el 05b", y el paso `02` es una decisión sustantiva: re-clasificar escenarios sobre un
corpus donde el 44% de los destinos se re-decidió no es un refresh mecánico.

**Nota estructural:** el `05b` vive en `D:\Trabajos en PY\MOL_escenarios\scripts\`, no en este repo.
El frente pide branch en `Webscrapping`, pero el script a extender está en el sandbox. Hay que
decidir dónde queda el `05b` extendido.

**Lo que sí está listo:** las columnas de trazabilidad del traductor existen y tienen datos —
`arbol_hub_id`, `arbol_regla_id`, `arbol_camino`, `arbol_traza_json`, y `decision_metodo` con
3.710 ofertas en `arbol_contexto`. P1.a es viable en cuanto la fuente esté resuelta.

## P0.3 — Artefactos rescatados ✅

`config/uri2esco.json` (271.601 bytes, 3.046 entradas) y `config/mr_seguimiento_INET.csv` (9.632
bytes, 51 filas) están donde los dejó el PR #66, junto con sus LEEME.

---

## Las tres salidas posibles para P1

**A — Correr la cadena completa (`01` → `02` → `05b` extendido).** Fiel al diseño actual; conserva
la capa de escenarios que los colegas usan. Costo: re-descarga completa (necesita credenciales de
Supabase) y re-clasificación sobre ~1,5M de filas de skills. Requiere decidir **con qué versión del
clasificador** se re-clasifica post-L.

**B — Reescribir el export contra la BD viva.** Más rápido y elimina la dependencia del duckdb —
que es, además, la causa de que la ceremonia de junio fuera artesanal. Costo: se pierden las cinco
columnas de la capa de escenarios, salvo que se re-deriven. Degrada un entregable documentado.

**C — Híbrido.** Base desde la BD viva, capa de escenarios desde el duckdb donde los `id` casen.
Deja 30% del corpus sin escenario y mezcla dos épocas dentro del mismo archivo. **No recomendado**:
es exactamente el tipo de costura silenciosa que este frente vino a eliminar.

**Recomendación: A**, porque `confianza_skill` es una columna que la guía de colegas documenta y
que ellos consultan; salir con B sería publicar una versión más pobre que la de junio justo en la
entrega que quiere mostrar el salto de calidad. Pero A necesita dos cosas que no están en el spec:
acceso a Supabase para el `01`, y una definición sobre el `02`.

**No avanzo a P1 hasta que eso esté laudado.** Nada se generó, nada se subió, el VPS no se tocó.
