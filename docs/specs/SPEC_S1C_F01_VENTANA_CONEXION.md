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

*(Se completa al ejecutar — cada verificación con: query/comando, resultado, veredicto contra el criterio binario, premisas que actualiza en ambos registros.)*

## 9. Criterio de aceptación

El spec está TERMINADO cuando: la sección 8 documenta veredicto de V1-V4, V6 y V7 (V5 con casilla abierta si falta el dato de Gerardo), las premisas afectadas están listadas en ambos registros (specs S1.B + índice del harness), y el PR está mergeado. Definición de terminado del Eje 6: este documento es su propio consumidor — la Fase 0 decide con él.
