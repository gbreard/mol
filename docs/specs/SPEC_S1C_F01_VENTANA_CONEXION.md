# SPEC S1C-F0.1 — Ventana de conexión viva

> Versión 0.2 · 2026-06-12 · Fase 0 del master S1.C — Reparación
> Primer spec de la fase de reparación. Agrupa en una sesión las verificaciones pendientes que requieren conexión viva o datos frescos. Es verificación read-only: produce los datos con los que la Fase 0 decide. No repara nada.
> *v0.2 (pre-ejecución)*: incorpora la revisión cruzada del 2026-06-12 — V7 (censo de residencia de datos, principio nº7 del master, PR en curso), V4 fijado GET-only con endpoints exactos, V2 con segunda pata discriminante, V6 con corte por portal, y premisas del índice del harness en el entregable.

## 1. Propósito

Cerrar las verificaciones que los specs de relevamiento dejaron marcadas como "no verificable en esta pasada", más el censo del principio de residencia de datos, para que las decisiones de la Fase 0 (cimientos del Eje 1, harness, backlog, bajada automática) se tomen con datos y no con supuestos.

## 2. Reutilización

- Credenciales Supabase: `config/supabase_config.json` (service_role, ya usada por los scripts de sync).
- Scripts existentes como referencia de conexión: `scripts/exports/sync_to_supabase.py`, `scripts/sync_gold_set.py`, `scripts/spec_u1/export_validaciones_humanas.py`.
- BD local: `database/bumeran_scraping.db`.
- Grep de lecturas runtime ya verificado (arranque de V7-b): `config_loader.py:316-339`, `match_ofertas_v3.py:2094-2101`, `skills_implicit_extractor.py:1102, 1119-1131, 1223-1231`.
- Evidencia previa: adendas harness en S1.B.3/S1.B.4; reportes del sandbox en `MOL_escenarios/data_out/` (referencia externa).

## 3. Entregables

1. Esta misma spec actualizada con la sección 8 (Resultados) completa.
2. Lista de premisas actualizadas en dos registros: (a) los specs S1.B afectados (S1.B.3 A-1, S1.B.4 D-06, etc.); (b) **las premisas del índice de investigaciones del harness afectadas** (ficha del Gold Set, R6/A-2, P-13 y las que los veredictos toquen) — para que el hilo del harness arme su adenda con los resultados.

## 4. Implementación — las siete verificaciones

### V1 — El Gold Set ampliado (Supabase, read-only)
Confirmar la ubicación y composición del Gold Set ampliado (adenda A-1 de S1.B.3).
- Query: conteo total de la tabla `gold_set` + búsqueda de trazadores (`titulo ILIKE '%sommelier%' OR titulo ILIKE '%carnicer%'`).
- **Criterio binario**: trazadores presentes Y conteo en rango 110-115 → CONFIRMADO. Cualquier otro resultado → reportar lo encontrado.

### V2 — Embeddings vs catálogo de runtime (BD local, read-only, dos patas)
Resolver la hipótesis de la adenda A-2 de S1.B.4 (8.381 URIs huérfanas) de forma discriminante, no solo confirmatoria.
- **Pata (a)**: conteo de URIs presentes en `esco_skills_enriched` ausentes de `esco_skills` (ajustar nombres de columna con PRAGMA antes).
- **Pata (b)**: de las URIs huérfanas reales (las de `ofertas_esco_skills_detalle` con `skill_tipo_fuente='semantico'` cuya `esco_skill_uri` no está en `esco_skills`), ¿cuántas SÍ están en `esco_skills_enriched`?
- **Criterio binario**: si (b) ≈ 8.381 → hipótesis CONFIRMADA limpia (el .npy se generó de enriched y los corpus divergieron). Si (a) ≈ 0 y las huérfanas tampoco están en enriched → tercera posibilidad: el .npy es de una época anterior de enriched — comparar contra `database/embeddings/corpus_manifest.json` y reportar.

### V3 — Estado real de las emergentes (Supabase, read-only)
Actualizar el dato de mayo (431 pendientes / 0 aprobadas).
- Query: distribución por estado de la tabla de emergentes (localizar el nombre real en el código que la consume — `PerfilArgentinoAdmin.tsx` — antes de consultar).
- **Criterio binario**: dato actualizado obtenido. Comparar contra 431/0 y reportar el delta.

### V4 — Seguridad del deploy vivo (curl GET-only, sin descargar datos)
La verificación que Gerardo difirió: ¿los endpoints OE-11 responden sin auth en producción?
- Probar **EXACTAMENTE estos tres endpoints, método GET exclusivamente**: `GET /api/personas`, `GET /api/casos`, `GET /api/perfiles` contra `https://mol-nextjs.vercel.app`, sin sesión, con `curl -s -o /dev/null -w "%{http_code}" -X GET`.
- **PROHIBIDO**: POST/PATCH/PUT/DELETE bajo cualquier circunstancia — estos endpoints exportan POST y un request de mutación crearía PII en producción. Solo status code; no descargar ni persistir contenido.
- **Criterio binario**: 200 sin auth en alguno → exposición CONFIRMADA en vivo (dato para que S1.C decida cuándo sube). 401/403 en todos → la exposición es solo de código local; reportar.

### V5 — Facturación de Supabase (GERARDO, manual)
Confirmar cuantitativamente el candidato de costo (N+1 vs RPCs pgvector vs pollers — S1.B.1).
- Gerardo exporta del dashboard de Supabase el desglose de uso/billing del último mes (compute, egress, storage; por día si está disponible).
- **Criterio binario**: el desglose atribuye el costo dominante a uno de los tres candidatos → CONFIRMADO. No bloquea el resto del spec.

### V6 — Diagnóstico CLAE previo al backlog (BD local, read-only)
La condición de la sección 4.1 del master: estado de la caída de cobertura CLAE (18-20pp, mayo, detectada originalmente por portal).
- Query: cobertura CLAE agrupada por **mes × portal × estado de procesamiento** (el corte por portal hace el resultado comparable con la medición de mayo que disparó la alarma), para discriminar las tres hipótesis: (a) backlog pre-clasificador, (b) regresión, (c) distribución de las 13K excluidas.
- **Criterio binario**: una hipótesis dominante con números → backlog HABILITADO para soltarse con ese dato en mano. Si es ambiguo, reportar distribución e hipótesis sobrevivientes.

### V7 — Censo de residencia de datos (mixto, read-only)
El principio nº7 del master (PR en curso) se viola en ambas direcciones; esta verificación lo censa completo.
- **Pata (a) — dato humano varado arriba**: para cada dato humano de Supabase — `gold_set`, `issues`, `validacion_humana*`, emergentes, `approved_training_pairs` — conteo en Supabase vs equivalente local (si existe) y evidencia de última bajada. Aprovechar la conexión ya abierta de V1/V3.
- **Pata (b) — el pipeline estira la mano**: completar el censo de lecturas Supabase en runtime del núcleo. Arranque ya verificado: `config_loader.py:316-339` (config_overrides), `match_ofertas_v3.py:2094-2101` (RPC equivalencias), `skills_implicit_extractor.py:1102+` (equivalencias + boost). Buscar otras (grep de supabase/SUPABASE en `database/` y `scripts/` del núcleo). Para cada punto: qué trae, si afecta decisión, y qué pasa si Supabase no responde (¿fallback local? ¿crash? ¿silencio?).
- **Criterio binario**: lista completa de violaciones en ambas direcciones con conteos y comportamiento ante fallo. Alimenta el diseño de la bajada automática (Eje 2) y el corte de lecturas runtime (Ejes 4/5).

## 5. Dependencias

- Conexión a Supabase con la service_role local (V1, V3, V7-a).
- Acceso de Gerardo al dashboard de billing (V5).
- Salida a internet para los curl GET (V4).

## 6. Validación

Cada verificación tiene su criterio binario en la sección 4. El spec valida cuando V1-V4, V6 y V7 tienen veredicto documentado (V5 puede quedar con casilla abierta sin bloquear).

## 7. Riesgos

- **Read-only estricto**: solo SELECT en Supabase y SQLite; ningún INSERT/UPDATE/DELETE; ningún RPC que escriba.
- **V4 es GET-only por regla dura**: los endpoints exportan POST; una mutación accidental crearía PII en producción.
- **PII**: V4 no descarga contenido; V1/V3/V7 consultan tablas sin PII — si una query trajera columnas personales por accidente, no copiarlas al spec.
- **Producción intacta**: queries de lectura puntuales, sin repetición pesada.
- Si una tabla no existe con el nombre esperado: buscar el nombre real en el código que la consume antes de declarar ausencia.

## 8. Resultados

> Ejecutado 2026-06-12, read-only. Orden: V2/V6 (local) → V1/V3/V7-a (Supabase) → V7-b (grep) → V4 (GET). Punto de control reportado tras V1-V3. V5 pendiente de Gerardo (no bloquea).

### V1 — Gold Set ampliado → ✅ CONFIRMADO
- **Comando**: `gold_set` en Supabase, `count(*)` + resolución de títulos por join local (`gold_set.id_oferta` → `ofertas.titulo`).
- **Resultado**: `gold_set` = **113** filas (∈ [110,115]). Columnas reales: `id, id_oferta, esco_ok, isco_esperado, esco_esperado, tipo_error, comentario, agregado_por, agregado_at, version_reglas, activo`. La tabla **no guarda título** → el trazador `sommelier/carnicer` no aplica a este schema. Por join local se resolvieron **110 de 113** títulos (reales y variados: Gerente Operaciones, Capataz, Odontólogo, Mozo, Electricista); **3 ids del gold set no existen en la BD local**.
- **Veredicto**: conteo CONFIRMA (113 en rango). **Corrección de supuesto del spec**: el trazador asumía una columna `titulo` inexistente; la composición se verifica por join, no por texto en la tabla. Los 3 ids ausentes en local son síntoma de residencia (el dato humano vive arriba, el local está incompleto).
- **Premisas**: S1.B.3 A-1 → confirmada (Gold Set ampliado = 113 en Supabase, regresión local mide contra 49). Índice harness → ficha del Gold Set: actualizar tamaño 113 y nota "3 ids sin contraparte local".

### V2 — Embeddings vs catálogo de runtime → número CONFIRMADO, causa simple REFUTADA
- **Comando**: SQLite local. Pata (a) implícita por conteos de catálogo; pata (b) discriminante: URIs huérfanas (`ofertas_esco_skills_detalle` `skill_tipo_fuente='semantico'` no en `esco_skills`) cruzadas contra el catálogo enriched real (`database/embeddings/enriched/esco_skills_metadata_full.json`, fuente del `.npy` según `corpus_manifest.json`).
- **Resultado**: **8.381 filas huérfanas** / **54 URIs distintas**. `esco_skills` local = 14.247; `.npy` `esco_skills_embeddings_full.npy` generado de `esco_skills_enriched` = **14.257** (manifest `generated_at` 2026-04-24). De las 54 huérfanas, **solo 10 están en el enriched actual; 44 no están ni en runtime ni en enriched actual**.
- **Veredicto**: el número 8.381 calza exacto con A-2, pero la hipótesis "el `.npy` se generó de enriched y los corpus divergieron" **solo explica 10/54**. Las 44 restantes son **acumulación multi-época**: filas escritas por embeddings de épocas anteriores que ya no existen en ningún catálogo vigente. No es una divergencia limpia de un solo `.npy`.
- **Premisas**: S1.B.4 A-2 → refinada (divergencia real + componente multi-época). Engancha con S1.B.4 D-08 (embeddings multi-época sin release estampada). Índice harness → R6/A-2: marcar "causa = multi-época, no divergencia de catálogo único".

### V3 — Estado real de las emergentes → ✅ CONFIRMADO
- **Comando**: Supabase `emergentes_pendientes`, distribución por `estado`.
- **Resultado**: **508 filas, todas `pendiente`**, 0 en cualquier otro estado.
- **Veredicto**: delta vs mayo (431/0) = **+77 pendientes, sigue 0 aprobadas**. El buffer se llena y no drena. C4 confirmado en vivo.
- **Premisas**: C4 del master → dato actualizado (508 pendientes / 0 aprobadas). Índice harness → P-13 (emergentes): actualizar conteo.

### V4 — Seguridad del deploy vivo → ⛔ EXPOSICIÓN CONFIRMADA EN VIVO
- **Comando**: `curl -s -o /dev/null -w "%{http_code}" -X GET` contra `https://mol-nextjs.vercel.app`, sin sesión, exactamente 3 endpoints, **solo GET, solo status code**.
- **Resultado**: `GET /api/personas → 200` · `GET /api/casos → 200` · `GET /api/perfiles → 200`.
- **Veredicto**: los tres endpoints de OE responden **200 sin autenticación en producción**. La exposición no es solo de código local (OE-11): está **viva**. Dato para que S1.C decida cuándo sube la deuda de seguridad (D-08), hoy diferida por decisión de Gerardo. No se descargó ni inspeccionó contenido (solo status).
- **Premisas**: S1.B.7 D-08 (seguridad) → confirmada en vivo, no solo en código. Severidad: PII accesible sin auth en producción.

### V5 — Facturación de Supabase → ⏳ ABIERTA (Gerardo)
- Pendiente del desglose de billing del último mes (compute/egress/storage). No bloquea el cierre del spec.

### V6 — Diagnóstico CLAE previo al backlog → REGRESIÓN ~2026-03 (no backlog pre-clasificador)
- **Comando**: SQLite local, cobertura CLAE (`ofertas_nlp.clae_code` no nulo entre ofertas con NLP) agrupada por **mes × portal**.
- **Resultado**: cobertura ~**100% en todos los portales hasta 2026-02**; cae desde **2026-03** de forma sostenida e independiente del portal — bumeran 100% → 95,9% (mar) → 69,7% (abr) → 69,1% (may); zonajobs 91,5% → 68%; computrabajo 80% → 66-68%; indeed con piso propio 42-60%. Cobertura agregada por portal: bumeran 94,2% · zonajobs 87,3% · portalempleo 82,9% · computrabajo 77,4% · indeed 52,1%.
- **Veredicto**: el patrón **descarta (a) backlog pre-clasificador** (los meses viejos tienen cobertura completa; la caída es de los meses recientes) y apunta a **(b) regresión introducida ~2026-03**, que degradó la clasificación CLAE en todos los portales establecidos. Indeed suma un factor de portal propio (metadata más pobre).
- ⚠️ **Nota que modifica la condición de la sección 4.1 del master**: "backlog HABILITADO" pasa a **"habilitado solo si primero se diagnostica o se acepta conscientemente la regresión CLAE de 2026-03"** — porque reprocesar el backlog con la versión vigente del pipeline **propagaría** la cobertura degradada. *El ajuste del texto del master se hace en un ciclo aparte tras el merge de este spec, no en este branch.*
- **Premisas**: master §4.1 → condición revisada (ver nota). Nuevo ítem candidato para Eje 5/NLP: regresión CLAE 2026-03. Índice harness → P-13 / cobertura: registrar la regresión con el corte por portal.

### V7 — Censo de residencia de datos → completo en ambas direcciones

**Pata (a) — dato humano varado arriba:**

| Dato humano | Supabase | Local | Estado de la bajada |
|---|---|---|---|
| `gold_set` | 113 | 49 (`database/gold_set_manual_v2.json`) | bajada rota; `scripts/sync_gold_set.py` existe pero no se corre; Δ64 |
| `emergentes_pendientes` | 508 | 0 | nunca bajó |
| `approved_training_pairs` | **0 (tabla vacía)** | `config/training_pairs.json` = 602 | el consumidor de aprobación **nunca escribió a la tabla**; el dato local proviene de otro flujo |
| `issues` | 431.314 (430.388 `auto-validator@mol.gob.ar` / **926 humanos**) | sin contraparte local | nativo Supabase; 99,8% automático |
| `validacion_humana*` | **no es tabla** | — | la validación humana vive como `estado_validacion` en `ofertas_dashboard` (lo confirma `scripts/spec_u1/export_validaciones_humanas.py`) — **corrección de supuesto del spec** |

**Pata (b) — el pipeline estira la mano (lecturas Supabase en runtime del núcleo):**

| Archivo del núcleo | Llamadas | Qué trae | Afecta decisión | Ante fallo |
|---|---|---|---|---|
| `config_loader.py:316-339` | 3 | tabla `config_overrides` (reglas de negocio, diccionario argentino) | **Sí** (reglas que "ganan siempre") | **fallback local** (try/except L340 → Warning → JSON local L363-365) |
| `match_ofertas_v3.py:2094-2101` | 3 | RPC `get_latest_equiv_update` + configs vía `load_config` | Sí (equivalencias) | degradado (depende del RPC) |
| `skills_implicit_extractor.py:1102,1119-1131,1223-1231` | 7 | equivalencias + boost (vía `service_role_key`) | Sí (skills) | boost deshabilitado / equivalencias off (graceful) |
| `process_nlp_from_db_v11.py` | 0 | — | — | núcleo NLP **limpio**, solo local |
| `match_by_skills.py`, `skills_rules_matcher.py` | 0 | — | — | limpios |

- **Veredicto**: **3 archivos del núcleo** leen Supabase en runtime para decidir; NLP y los matchers de reglas/skills están limpios. El fallo degrada con gracia (fallback local / boost off), **no crashea** — la dependencia es "blanda", pero igual viola la residencia: la decisión del pipeline **cambia** según si Supabase respondió (otras reglas/equivalencias/boost). La bajada se repara en el Eje 2; el corte de estas lecturas runtime en los Ejes 4/5.
- **Premisas**: principio nº7 del master (PR #30) → censo completo, ambas direcciones cuantificadas. S1.B.4 D-11 → confirmado (`approved_training_pairs` vacío = consumidor de aprobación nunca conectado, sabor D-15).

### Premisas actualizadas — resumen en ambos registros

**(a) Specs S1.B**: S1.B.3 A-1 (gold set 113 confirmado), S1.B.4 A-2 (causa multi-época), S1.B.4 D-08 (embeddings multi-época), S1.B.4 D-11 (`approved_training_pairs` vacío), S1.B.7 D-08 (exposición OE viva).

**(b) Índice de investigaciones del harness**: ficha del Gold Set (tamaño 113, 3 ids sin local), R6/A-2 (multi-época), P-13 / cobertura (emergentes 508/0; regresión CLAE 2026-03 con corte por portal), principio de residencia (censo bidireccional).

## 9. Criterio de aceptación

El spec está TERMINADO cuando: la sección 8 documenta veredicto de V1-V4, V6 y V7 (V5 con casilla abierta si falta el dato de Gerardo), las premisas afectadas están listadas en ambos registros (specs S1.B + índice del harness), y el PR está mergeado. Definición de terminado del Eje 6: este documento es su propio consumidor — la Fase 0 decide con él.
