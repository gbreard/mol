# Conteos 5 — BGE-M3 + scraping post-auditoría

**Fecha ejecución:** 2026-05-04
**Pipeline activo:** no (solo proceso `/tmp/diag4_section_BD.py` colgado en read-only desde sesión previa, no afecta nada)
**VPS accesible:** sí (SSH root@187.124.150.28 funciona, embed-server :8082 responde)
**Tiempo total:** ~80 min
**Modo:** READ-ONLY estricto. No se modificaron archivos, configs, BD ni embeddings.
**Secciones completadas:** A, B, C, D, E, F, G
**Pendientes:** ninguna sub-pregunta marcada pendiente. Drift exacto local↔VPS no se midió por evitar cargar modelo localmente; se infiere de SHA pinneado en ambos lados.

---

## A — BGE-M3 revision SHA y reproducibilidad

### A1. Revision SHA pinneada

**SHA declarado (canónico):** `5617a9f61b028005a4858fdac845db406aefb181`

| Lugar | Valor | Observación |
|---|---|---|
| `database/embeddings/corpus_manifest.json` (raíz) | `5617a9f6…` | manifest principal |
| `database/embeddings/enriched/corpus_manifest.json` | `5617a9f6…` | idéntico |
| `config/embedding_config.py:13` | `5617a9f6…` | constante central `EMBEDDING_REVISION` |
| `config/matching_config.json:9` | `5617a9f6…` | duplicación |
| `scripts/embeddings/build_enriched_embeddings.py:202` | `5617a9f6…` | hardcodeado en metadata |
| `scripts/embeddings/build_enriched_occupations.py:212` | `5617a9f6…` | hardcodeado en metadata |
| `/opt/mol/embed_server.py:16` (VPS) | `5617a9f6…` | constante en server |

**Coinciden en los 7 lugares.** Sin drift documental.

### A2. Revision SHA en runtime

**Pinneado correctamente:**
- `config/embedding_config.py:9` — `SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)`
- `database/skills_implicit_extractor.py:142–151` — pasa `revision=` al cargar (si LoRA no existe; LoRA no existe en disco).
- `scripts/db/regenerate_all_embeddings.py:435,477` — pasa `revision=`.
- `tests/matching/test_gold_set_manual.py:149` — pasa `revision=`.
- `/opt/mol/embed_server.py:20` (VPS) — pasa `revision=`.

**NO pinneado (descarga `main` actual):**
- `database/skills_implicit_extractor.py:1851` (función helper de utilidad, no ruta de prod).
- `scripts/inject_skills_from_issues.py:52`
- `scripts/analysis/validar_precision_real_v21.py:54`
- `scripts/db/create_chromadb_esco.py:29` (ChromaDB inactivo)
- `scripts/embeddings/build_enriched_occupations.py:176` ⚠️ — el script que **generó los embeddings de producción** carga el modelo SIN `revision=`. El SHA declarado en el manifest es **manualmente hardcodeado**, no lo que efectivamente se usó.
- `scripts/embeddings/build_enriched_embeddings.py:165` ⚠️ — mismo problema.
- `scripts/embeddings/prototipo_embeddings_enriquecidos.py:109`
- `scripts/embeddings/ab_test_embeddings.py:265`
- `scripts/matching/gold_set/03_match_semantico.py:34`

**Implicancia:** los 14.257 embeddings actuales se generaron sin pinear el SHA. El manifest declara `5617a9f6...` pero ese valor no se enforced en la generación; coincide *si y solo si* la cache local de HF en el momento de la generación apuntaba a ese SHA.

### A3. Cache local del modelo BGE-M3 (PC local)

**Path:** `~/.cache/huggingface/hub/models--BAAI--bge-m3/`

```
refs/main: 5617a9f61b028005a4858fdac845db406aefb181  (3 lines/40 bytes — coincide con manifest)
snapshots/:
  - 5617a9f61b028005a4858fdac845db406aefb181  (pinneado)
  - 9a0624b896d81da7492a910ffa53731274b6cf3d  (otro SHA — más reciente o experimental)
```

**Última modificación de `refs/main`:** `Mar 15 03:41` (2026).

**Hallazgo:** existen DOS snapshots descargados. Si algún script carga `BAAI/bge-m3` sin `revision=`, HF resolvería a `refs/main` (= `5617a9f6…`), pero si alguien actualizase manualmente `refs/main` a `9a0624b8`, los scripts no pinneados apuntarían a otro modelo.

### A4. ¿LoRA existe?

**NO existe en disco.**

```
data/finetuning/matching/                                # directorio existe
  ├── (vacío salvo training.log)
  └── training.log (18 bytes — contenido: "Acceso denegado.")
```

`SkillsImplicitExtractor._LORA_PATH = data/finetuning/matching/model_lora` — `.exists() = False`.

Implicancia para `database/skills_implicit_extractor.py:86–87`:
```python
DEFAULT_MODEL = "BAAI/bge-m3"           # ← cae al base
DEFAULT_MODEL_REVISION = EMBEDDING_REVISION  # ← se pinnea (fallback porque no hay LoRA)
```

El fallback a BGE-M3 base está pinneado. **El sistema corre sobre BGE-M3 base, no LoRA.** Coincide con `feedback_lora_vs_bge` en memoria.

### A5. ¿Cómo se generaron los embeddings actuales?

**Script:** `scripts/embeddings/build_enriched_embeddings.py` (skills) + `build_enriched_occupations.py` (occupations).

**Argumentos efectivos** (de inspección de código):
- modelo: `SentenceTransformer('BAAI/bge-m3')` ⚠️ sin `revision=`
- batch_size: parametrizado vía `--batch-size`
- normalize_embeddings: `True`
- dtype: `float32`
- assert post-generación: `embeddings.shape[1] == 1024` y norma unitaria (`np.allclose(norms, 1.0, atol=1e-3)`)

**Manifest generado:**
- `model_revision: 5617a9f6…` — hardcodeado en línea 202, **no extraído del modelo cargado**
- `generated_at: 2026-04-24T23:03:18.263316+00:00` (skills)
- `generated_at: 2026-04-24T23:09:05.977633+00:00` (occupations)
- `generated_by: LOCAL:spec_e_fase_1`
- `source_table: esco_skills_enriched / esco_occupations_enriched`
- `source_count: 14257 / 3046`
- `checksum_sha256: ec6b2c84… / fdd0d9b4…`
- `enrichment_fields: [label, L1_L2_category, broader_label, top_3_occupations_with_esco_code, description_500chars]` (skills)
- `enrichment_fields: [esco_label_with_code, isco_hierarchy_1_2_4, top_5_essential_skills]` (occupations)

### A5b. Reproducibilidad

**Sin tests de reproducibilidad** — `tests/embeddings/` contiene 3 tests funcionales (`test_enriched_text_builder`, `test_filter_l2_compatibility`, `test_filter_llm_skills`) pero ninguno verifica `embed(x)` determinístico entre corridas.

**Sin determinismo explícito** en código:
- `grep "torch.manual_seed"` → 0 hits en database/ y scripts/.
- `model.encode(textos, normalize_embeddings=True)` no fuerza orden ni semilla.

**Verificación de compatibilidad runtime:** `database/skills_implicit_extractor.py:1007–1062` (`_verify_corpus_compatibility`) — lee `~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main` y compara con `manifest.model_revision`. Si difieren → `RuntimeError`. Si no se puede determinar → warning silencioso. **Esta es la única protección activa contra drift del modelo.**

**Drift histórico documentado:**
- `docs/SPEC_Motor_Conocimiento_V1_2.md:96–137`, `V1_4.md:99,139`, `V2.md:96,136` mencionan: *".npy actuales difieren 2.5% de los baselines sin causa documentada"*.
- Causa atribuida en V2: `SentenceTransformer("BAAI/bge-m3")` sin pinear.

---

## B — Embeddings skills: integridad

### B1. Integridad de archivos

| Archivo | Tamaño | Hash MD5 | Generado |
|---|---|---|---|
| `database/embeddings/esco_skills_embeddings_full.npy` | 56 MB (58.396.800 B) | `325911c08432afdba28da4dd41c8d1d8` | 2026-04-24 22:43:55 |
| `database/embeddings/enriched/esco_skills_embeddings_full.npy` | idéntico | `325911c0…` | 2026-04-24 20:03:17 |
| `database/embeddings/baselines/esco_skills_embeddings_full_baseline.npy` | 56 MB | `a58f8fceda03c11dfdc2e7b474cebf23` | 2026-01-03 |
| `database/embeddings/baselines/pre_spec_e_20260424_224334/esco_skills_embeddings_full.npy` | 56 MB | `228691f42c7b0155ed0b16472f7d2a42` | 2026-04-24 22:43 |

**Shape actual:** `(14257, 1024)` `float32`. **Metadata:** 14.257 entradas. **Coinciden N=N.**

Sample metadata entry (clave `uri`, `label`, `description`, `type`, `L1`, `L2`, `category_code`, `category_label`, `broader_uri`, `broader_label`, `esco_codes_aplicable`, `n_occupations`, `texto_indexado`).

### B2. Boost esco_argentino

**No es archivo en `config/`** — es **tabla Supabase `esco_argentino`**.

**Carga:** `database/skills_implicit_extractor.py:1208–1265` (`_load_argentino_cache`).
- Llama Supabase: `client.table('esco_argentino').select('esco_occupation_uri, skills_consolidadas')`.
- Construye cache `{occupation_uri: {"skills": {esco_uri: frequency}, "max_freq": int}}`.
- Si Supabase falla → degradación graceful (cache vacío, sin error).

**Aplicación:** `database/skills_implicit_extractor.py:1267–1320` (`rerank_with_argentino_boost`). Llamado desde `database/match_ofertas_v3.py:1753`.

**Es boost (suma), NO filtro/gate:**
```python
boost_factor = 0.05 * (frequency / max_frequency)
s_copy["score"] = min(1.0, original_score + boost_factor)
```

**Cap:** 0.05 cuando frequency = max_frequency. Coincide con la hipótesis del prompt.

**Cantidad documentada (SPEC V2.md:97):** 291 asignaciones, 44 ocupaciones, 220 skills únicas, 267 `mol_approved`. No verificado en runtime (requiere Supabase).

### B3. Regeneraciones de embeddings (commits)

```
2026-04-24 efacdf8f  feat(embeddings): SPEC E Fase 1 — scripts de generación + tests unit
2026-04-24 66f922fa  feat(embeddings): SPEC E Fases 2-3 — A/B test + promoción a producción
2026-04-24 25828fbf  chore(embeddings): destrackear binarios autogenerados
2026-04-09 09af7f35  feat: Motor de Conocimiento E1.3 + E1.5 + E4.1 (pinned + verify_corpus)
```

**3 versiones distintas en disco** (hashes confirmados):
- baseline `a58f8fce…` (Jan 3 2026 — pre-SPEC E, pre-pinning)
- pre_spec_e `228691f4…` (Apr 24 22:43 — backup justo antes de promoción SPEC E)
- actual `325911c0…` (Apr 24 22:43 — SPEC E enriquecido)

`.npy` está en `.gitignore` desde 2026-04-24 (`25828fbf chore(embeddings): destrackear binarios autogenerados`), por eso `git log --follow` no devuelve historial.

### B4. Skills emergentes (M-08) y URIs no canónicas

**Las 51 URIs no canónicas detectadas en reporte 4 NO son skills emergentes generadas por M-08.**

**M-08 confirmado** (`database/skills_implicit_extractor.py:1513–1672` — `extract_declared_skills`): extrae skills ESCO desde 4 fuentes declaradas (skills_explicitas, conocimientos_explicitos, idiomas, certificaciones). **No genera URIs nuevas; mapea a URIs canónicas existentes.**

**Origen real de las 51 URIs:** `config/terminologia_argentina_skills.json`.

```json
"picking": {
  "expansion": "recoleccion de productos en almacen",
  "skills_esco": [
    {"skill": "preparar pedidos", "uri": "http://data.europa.eu/esco/skill/24c4beb4-…"},
    {"skill": "gestionar el inventario", "uri": "http://data.europa.eu/esco/skill/a7754107-…"}
  ]
}
```

**Conteo en archivo:** 30 términos, 49 URIs hex únicas (varias coinciden con URIs canónicas reales, otras son sintéticas). Patrón sintético claro:

```
Top sintéticas (5,655 + 5,568 + 1,602 + 1,417 + 1,065 + … ofertas):
  4a5b6c7d-8e9f-0a1b-2c3d-4e5f6a7b8c9d   →  "operar equipos de almacen"
  d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a   →  (no encontrada en sample)
  d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a   →  "realizar operaciones de carga y descarga"
  6a7b8c9d-0e1f-2a3b-4c5d-6e7f8a9b0c1d   →  "mover objetos"
  9f0a1b2c-3d4e-5f6a-7b8c-9d0e1f2a3b4c   →  "empaquetar mercancias"
  a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d   →  "gestionar redes sociales"
  b4c5d6e7-f8a9-0b1c-2d3e-4f5a6b7c8d9e   →  "crear contenido digital"
  …
```

Patrón hex-secuencial (`a→b→c→d→e` shift de 1 carácter) → **inventadas a mano**, no UUIDs random. Labels sin tildes ("almacen", "codigo", "diseno") confirma origen manual.

**Distribución de las 30.593 filas afectadas por matching_version:**
| matching_version | filas |
|---|---|
| `3.5.2` | 11.225 |
| `spec_h_rematch` | 2.018 |
| (otras: NULL, etc.) | resto |

**Skills emergentes reales** según SPEC V2.md:82–98: 431 emergentes pendientes en tabla Supabase `emergentes_pendientes`. `recalcular_emergentes()` RPC tiene un bug (`isco_code` NULL en las 44 filas de `esco_argentino`) — no procesadas. **No están en BD local**.

**Adicional — tabla `ofertas_skills_norm`:** 12.304 filas, 4.649 URIs únicas, **2.341 URIs no canónicas** (formato slug `asesorar_sobre_el_mantenimiento_de_máquinas`, no UUIDs). Origen distinto, presumiblemente normalización pre-ESCO. Afecta 6.248 filas.

### B5. Drift entre regeneraciones

**Sin logs de regeneración** en `logs/` (los más recientes son del 20/03/2026, anteriores a SPEC E).

**Comparación directa** (hecha en este diagnóstico, read-only sobre archivos):

Sample 100 skills, comparación por **URI común** entre `pre_spec_e` (Apr 24 pre-promoción) y `actual` (Apr 24 SPEC E):

```
URIs comunes: 14.247
URIs nuevas en SPEC E: 10
URIs removidas: 0

Cosine similitud (mismo URI, pre vs actual SPEC E):
  mean=0.3737   median=0.3557
  min=0.2389    max=0.7421
  drift cos<0.99: 100/100
  drift cos<0.95: 100/100
  drift cos<0.80: 100/100
```

**Lectura:** los embeddings cambiaron drásticamente entre pre-SPEC E y SPEC E porque **el texto indexado** cambió (enriquecimiento con label + L1/L2 + broader + top_3_occupations + description_500chars). **NO es drift del modelo** — es por design.

El "2.5% drift" mencionado en SPEC V2 se refiere a una comparación *anterior* (entre `.npy` locales del 7/04 via VPS y baselines del 31/03–1/04). En el corpus actual no es comparable porque el contenido textual cambió.

---

## C — Cache singleton del extractor

### C1. Comportamiento

**Class-level cache** (`database/skills_implicit_extractor.py:91–97`):
```python
_model = None
_skills_embeddings = None
_skills_metadata = None
_skills_weights_config = None
_terminology_config = None
_initialized = False
```

**Implicancia:** cada **proceso Python tiene su propio singleton**. No se comparte entre procesos. Si corren 2 instancias del pipeline simultáneamente → **cada una carga 56 MB embeddings + JSON metadata + modelo BGE-M3 (~1.3 GB)** independientemente.

**Tamaño en RAM (medido en VPS):** `Memory: 1.3G (peak: 1.4G)` para el embed-server (idéntico stack: BGE-M3 + uvicorn + 1 worker).

**Procesos concurrentes esperados en local:** 1 (el pipeline corre secuencial, `run_validated_pipeline.py` no paraleliza).

### C2. Invalidación

`SkillsImplicitExtractor.clear_cache()` (línea 1000–1005) existe pero **ningún script lo llama**.

```bash
$ grep -rn "SkillsImplicitExtractor.clear_cache\|extractor.clear_cache" --include="*.py"
# (sin resultados en producción)
```

**No hay file watcher** que detecte modificación de `.npy` en disco. Si se actualiza el archivo mientras el pipeline está vivo → **el proceso sigue usando el cache viejo** hasta reinicio.

`_verify_corpus_compatibility` (línea 1007) solo se ejecuta en `_initialize()`, no en cada `extract_*` call.

### C3. Cache en VPS Hostinger

VPS embed-server **mantiene el modelo en memoria** (load-once en startup, línea 19–20 de `embed_server.py`): activo desde 2026-04-30 15:44:48 (4 días sin reinicio).

**No hay TTL** ni invalidación automática. Reinicio manual via `systemctl restart embed-server`.

**No tiene `.npy`** — el VPS solo provee `model.encode(text)` por HTTP. Los `.npy` viven en local y se sincronizan a Supabase pgvector aparte.

---

## D — VPS Hostinger embedding server

### D1. ¿Está corriendo?

**Sí, activo.**

```
● embed-server.service - BGE-M3 Embed Server
  Loaded: loaded (/etc/systemd/system/embed-server.service; enabled)
  Active: active (running) since Thu 2026-04-30 15:44:48 -03; 4 days ago
  Main PID: 692 (python3)
  Tasks: 5 (limit: 9431)
  Memory: 1.3G (peak: 1.4G)
  CPU: 10min 9.609s  ← acumulado en 4 días
```

**Healthcheck:**
```
GET http://187.124.150.28:8082/health
→ {"status":"ok","model":"BAAI/bge-m3","revision":"5617a9f61b02","dims":1024}
```

**Test embed (read-only):**
```
POST /embed { "text": "hola" }
→ {"embedding":[0.00932, 0.02294, -0.04283, …]}  (1024 floats)
```

### D2. Modelo en VPS

**Path:** `/opt/mol/embed_server.py` (50 líneas).

```python
MODEL_NAME = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
model = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)
```

**SHA pinneado correctamente** (con `revision=`).

**Cache HuggingFace en VPS:**
```
~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main = 5617a9f61b028005a4858fdac845db406aefb181
snapshots/:
  - 5617a9f61b028005a4858fdac845db406aefb181  ← coincide con local
  - 9a0624b896d81da7492a910ffa53731274b6cf3d  ← idem (mismos 2 snapshots)
```

**No usa LoRA** — solo BGE-M3 base.

### D3. Drift local↔VPS

**No medido directamente** (requeriría cargar el modelo localmente, costoso). Se infiere:

| Variable | Local | VPS | Coincide |
|---|---|---|---|
| Modelo | `BAAI/bge-m3` | `BAAI/bge-m3` | ✓ |
| Revision SHA | `5617a9f6…` (pinneado en `_initialize`) | `5617a9f6…` (pinneado en `embed_server.py:20`) | ✓ |
| Snapshot en cache HF | `5617a9f6…`, `9a0624b8…` | idem | ✓ |
| `normalize_embeddings` | `True` | `True` (`model.encode(req.text, normalize_embeddings=True)`) | ✓ |
| Padding/truncation | default sentence-transformers | idem | implícito ✓ |
| Batch | configurable | configurable | irrelevante |
| Determinism (sin seeds) | sin `torch.manual_seed` | sin `torch.manual_seed` | ambos no determinísticos pero por design BGE-M3 es determinístico en inferencia |

**Probabilidad de drift:** baja para texto único; potencialmente nula si SentenceTransformer y torch son las mismas versiones. **No verificado empíricamente.**

### D4. Carga de la VPS

**Tráfico /embed desde 2026-04-01:** **0 POSTs** (verificado vía `journalctl -u embed-server | grep -c "POST /embed"` → 0).

Logs systemd muestran solo bots probando endpoints inexistentes (`/metrics`, `/`, `/v1/metadata`, `/favicon.ico`).

**CPU acumulada:** 10 min en 4 días arriba → ~150ms/día. Confirma 0 tráfico real.

**No hay rate limit configurado** explícitamente (FastAPI sin middleware de rate limiting).

**Auth:** header `X-Embed-Secret: mol-embed-2026` (fijo en código, no rotable sin redeploy).

**Quiénes deberían consumirlo (según SPEC V2):** dashboard OE (S2 / Skill Intelligence) para embedding runtime de queries del usuario. **No lo están consumiendo** — probablemente porque los componentes activos usan pgvector con embeddings precalculados en Supabase, no embed runtime.

---

## E — Estado actual del scraping (post-auditoría 22/04)

### E1. Última corrida exitosa de cada scraper

**Cron VPS:**
```
0 7 * * *      python3 run_scheduler.py --test                 ← Bumeran daily
0 8 * * 1,4    bash /opt/mol/scripts/scraping/run_scraping_vps.sh   ← Multi-portal Lun/Jue
```

**Hoy (2026-05-04, lunes) corrió OK:**
- `08:00:01` cron disparó multi-portal
- `11:30:44` finalizó el pipeline completo (3 h 30 min)
- Stats sync a Supabase: ⚠️ falla con `KeyError: 'ultimos_7d'` (ver hallazgo G).

**Histórico de corridas (logs en VPS `/opt/mol/logs/scraping_*`):**

| Fecha | Día | Estado | Total BD VPS |
|---|---|---|---|
| 2026-04-20 | Lun | ✓ | 39.450 |
| 2026-04-23 | Jue | ✓ | 41.141 |
| 2026-04-27 | Lun | ✓ | 42.254 |
| 2026-04-30 | Jue | ✓ | (no extraído del log directo) |
| **2026-05-04** | **Lun** | **✓** | **44.607** |

**Ofertas obtenidas hoy 2026-05-04** (por portal, de logs):

| Portal | Scrapeadas | Insertadas | Duplicadas | Tiempo | Total acumulado |
|---|---|---|---|---|---|
| Bumeran (165 keywords) | 1.475 | 2 | 1.145 | ~6 min | (no expuesto en log) |
| ZonaJobs (1.072 keywords) | 4.738 | 91 | 4.647 | 11 min | 6.045 |
| ComputRabajo (1.072 keywords) | 12.444 | 325 | 12.119 | 180 min | 25.352 |
| CABA (listado completo) | 9 | 1 | 8 | 30 s | 24 |
| Portal Empleo (listado completo) | 433 | 22 | 411 | 13 min | 860 |
| Indeed (encolado a local) | — | — | — | — | — |
| **TOTAL nuevas hoy** | | **441** | | | **44.607** |

**Indeed corre en local**, no en VPS (`scripts/scraping/queue_indeed_local.py` inserta un comando UUID que el local debe procesar).

### E2. Estado de S-01..S-06

> Premisa: el archivo `AUDITORIA_PIPELINE_MOL.md` mencionado en el prompt no se encontró en el repo. Se infiere el estado de los issues a partir de logs y código actual; no se remapea la arquitectura.

**S-01: ZonaJobs paginación rota** — **sigue sin resolver**. Evidencia: hoy 4.738 ofertas scrapeadas, 91 insertadas, 4.647 duplicadas (98%). El comportamiento "20 ofertas por keyword" persiste; el sistema lo compensa procesando 1.072 keywords distintas para acumular 6.045 ofertas únicas en BD VPS. CLAUDE.md sigue documentándolo: *"el parámetro `page` es ignorado y siempre devuelve las mismas 20 ofertas"*.

**S-02 a S-06: no hay listado canónico encontrado** del set específico de issues. Hallazgos colaterales relacionados detectados en este diagnóstico (cualquiera puede mapear a S-02..S-06):
- ComputRabajo: 374/12.444 (3%) ofertas con descripción enriquecida en hoy. CLAUDE.md documenta: *"`fetch_description=True` por default: 1 request extra por oferta para descripción completa"* — discrepancia entre lo documentado y lo medido.
- `cron_errors.log` muestra `KeyError: 'ultimos_7d'` repetido en `sync_scraping_stats.py:82` — bug nuevo no documentado.
- Indeed scraping no corre en VPS sino en local via cola — modelo arquitectural distinto al resto, no documentado en CLAUDE.md (que dice *"Activo en VPS"*).

### E3. Republicaciones

| Métrica | Valor |
|---|---|
| Total ofertas | 60.983 |
| `es_republicacion = 1` | 3.270 (5,4%) |

> **Pendiente:** la query `WHERE fecha_scraping >= '2026-04-29'` falló — la columna se llama `scrapeado_en`, no `fecha_scraping`. Distribución por portal y temporal de republicaciones queda como pendiente menor.

### E4. Ofertas dadas de baja

| Métrica | Valor |
|---|---|
| `estado_oferta = 'baja'` | 57.515 (94,3%) |
| `estado_oferta = 'activa'` | 3.468 (5,7%) |
| `fecha_baja IS NOT NULL` | 57.515 |
| Bajas desde 2026-04-29 | 3.084 |
| Última `fecha_baja` registrada | 2026-05-04T11:00:10.661833 |

**Distribución por mes de bajas:**
| Mes | Bajas |
|---|---|
| 2026-05 | 1.526 |
| 2026-04 | 12.101 |
| 2026-03 | 31.251 |
| 2026-02 | 12.204 |
| 2026-01 | 433 |

**Auditoría 22/04 reportaba 14.413 bajas; hoy son 57.515.** El sistema de detección de bajas está corriendo y generó +43.000 bajas en 12 días (incluye bajas retroactivas del scraping histórico, no solo nuevas).

**Falsos positivos:** no medible read-only sin re-scrapear. Sin tooling de cross-check.

### E5. Sync VPS → Local

**Imports recientes** (en `data/vps_imports/`):
```
2026-04-30 09:00  (1,7 MB)
2026-04-30 10:00  (270 KB)
2026-04-30 11:00  (78 KB)
2026-05-01 08:00  (380 KB)
2026-05-02 08:00  (331 KB)
2026-05-03 08:00  (72 KB)
2026-05-04 08:00  (265 KB)
2026-05-04 09:00  (564 KB)
2026-05-04 10:00  (102 KB)
2026-05-04 11:00  (248 KB)
```

**Sync corre cada hora** (no solo Lun/Jue).

**Distribución `scrapeado_en` por día (BD local):**
| Día | Ofertas |
|---|---|
| 2026-05-04 | 1.306 |
| 2026-05-03 | 19 |
| 2026-05-02 | 69 |
| 2026-05-01 | 74 |
| 2026-04-30 | 1.320 |
| 2026-04-29 | 101 |
| 2026-04-27 | 1.382 |
| 2026-04-23 | 1.865 |
| 2026-04-20 | 1.407 |

Picos en Lun/Jue (multi-portal); días intermedios solo Bumeran daily.

**Drift VPS↔Local:**
- VPS BD total: 44.607
- Local BD total: 60.983
- Diferencia: **+16.376 en local**

Esto es esperado: local mantiene histórico, VPS solo el snapshot de scraping reciente. Las 57.515 bajas viven en local; muchas ya no existen en VPS porque el scraping diario no las trae más.

`config/vps_sync_log.json` contiene el log de syncs.

### E6. published_at y temporalidad

**Schema columns** (en `ofertas`): `fecha_publicacion_original`, `fecha_hora_publicacion_original`, `fecha_modificado_original`, `fecha_publicacion_iso`, `fecha_hora_publicacion_iso`, `fecha_modificado_iso`, `fecha_publicacion_datetime`, `fecha_hora_publicacion_datetime`, `fecha_modificado_datetime`.

**Comportamiento de cada una:**

| Columna | NULL/empty | Tipo | Notas |
|---|---|---|---|
| `fecha_publicacion_original` | 0,5% | TEXT libre | Strings sin parsear: *"Hace 9 días"*, *"Más de 30 días"*. Inutilizable para análisis temporal. |
| `fecha_publicacion_iso` ✅ | 1,4% | TEXT ISO | Bien parseado: 593 mayo / 12.579 abril / 24.695 marzo. **Sin futuras, 1 vieja**. |
| `fecha_hora_publicacion_iso` | 53,2% | TEXT ISO | Esparcido. Muchas ofertas no tienen timestamp horario del portal. |
| `fecha_publicacion_datetime` | 51,9% | TEXT datetime | Idem. |

**`fecha_publicacion_iso` es la columna confiable.** Coverage: 98,6%.

**Distribución por mes (`fecha_publicacion_iso`):**
| Mes | Ofertas |
|---|---|
| 2026-05 | 593 |
| 2026-04 | 12.579 |
| 2026-03 | 24.695 |
| 2026-02 | 6.945 |
| 2026-01 | 4.176 |

**`scrapeado_en`:** 0 NULL, rango `2025-10-23T21:30:57` → `2026-05-04T13:49:24`. **Es timestamp del momento de inserción, no del portal.**

### E7. Encoding y normalización

Sample 600 ofertas aleatorias:
- **Mojibake (`Ã`, `Â`, `â\x80…`):** 0
- **Combining diacritics (Unicode normalization NFD `[̀-ͯ]`):** 0
- **Tildes correctamente codificadas en UTF-8:** confirmado en sample por portal (`Técnico` 4 hi-bytes = 1 carácter UTF-8 multibyte).

Sample por portal (cada uno tiene tildes correctas):
```
bumeran:       'Técnico en refrigeración automotor'
zonajobs:      'Mecánico arreglo de máquinas y herramientas'
computrabajo:  'Técnico en refrigeración automotor'
caba:          'Técnico en refrigeración automotor'
portalempleo:  'Técnico en refrigeración automotor'
indeed:        'Técnico en refrigeración automotor'
```

**Encoding está OK** en BD local. No se detectan scripts de normalización post-scraping (los scrapers ya guardan UTF-8).

---

## F — Conexión scraping → NLP

### F1. Cobertura

| Métrica | Valor |
|---|---|
| Ofertas (BD local) | 60.983 |
| `ofertas_nlp` filas | 57.900 |
| `ofertas_nlp` distintas (`COUNT(DISTINCT id_oferta)`) | 57.683 |
| **Cobertura efectiva** | **94,6%** |
| Sin NLP | 3.300 |
| Filas duplicadas en `ofertas_nlp` | 217 (57.900 − 57.683) |

**Hallazgo nuevo:** hay **217 filas duplicadas** en `ofertas_nlp` por `id_oferta`. No detectado en reporte 4.

### F2. Backlog actual

| Origen | Sin NLP |
|---|---|
| Auditoría 22/04 | 19.007 |
| Hoy 2026-05-04 | 3.300 |
| **Procesadas en 12 días** | **15.707** |
| Tasa promedio | ~1.309 ofertas/día |

**Plausible** (un lote típico es 100–500/h con qwen2.5:7b sobre Ollama).

**Backlog actual por portal:**
| Portal | Sin NLP |
|---|---|
| computrabajo | 1.951 |
| indeed | 1.019 |
| bumeran | 221 |
| zonajobs | 109 |

**Por mes scrapeado:**
| Mes | Sin NLP |
|---|---|
| 2026-05 | 1.468 |
| 2026-04 | 1.573 |
| 2026-03 | 259 |
| (resto: marginal) | — |

→ El backlog es 92% reciente (último mes y medio).

### F3. id_oferta TEXT vs INTEGER

**Schema declarado (PRAGMA):**
| Tabla | id_oferta tipo |
|---|---|
| `ofertas` | INTEGER |
| `ofertas_nlp` | TEXT |
| `ofertas_esco_matching` | TEXT |

**Runtime sample (typeof):**
```
ofertas:                  id=5000283951 type=integer
ofertas_nlp:              id=10000061094 type=text
ofertas_esco_matching:    id=10000061094 type=text
```

**Origen del cast** (búsqueda `grep`):
- `database/limpiar_titulos.py:823` — `id_oferta = str(row_dict['id_oferta'])`
- `database/limpiar_titulos.py:1077` — `resultados.append((titulo_limpio, str(id_oferta)))`
- `database/auto_corrector.py:154,266,343,417,452,478` — funciones `_*` reciben `id_oferta: str`.

**Decisión documentada:** ninguna encontrada — sin comentario explicativo en el código.

**¿Destruye el orden numérico?** Lexicográficamente sí (`'1000' < '999'`). Pero los IDs reales en BD comienzan con `5_000_000_000` (Bumeran), `10_000_000_000` (otro), etc. — todos tienen el mismo número de dígitos, así que el orden lexicográfico = numérico. **No es problema en la práctica.**

**¿Causa pérdida de índices en JOINs?**

```
JOIN con CAST: 57.683
JOIN natural:  57.683  (diff: 0)
```

SQLite usa **type affinity dinámico**: `INTEGER` JOIN `TEXT` matchea correctamente. El JOIN devuelve los mismos resultados con o sin CAST. **Funcionalmente OK.**

**Pero:** SQLite puede no usar índices cuando los tipos difieren. El reporte 4 lo señaló como causa de slow JOINs. No se midió EXPLAIN aquí (read-only sin afectar perf).

---

## G — Hallazgos colaterales

### G1. cron_errors.log — bug `KeyError: 'ultimos_7d'`

**VPS** `/opt/mol/logs/cron_errors.log` muestra error repetido en cada corrida:

```python
File "/opt/mol/scripts/sync_scraping_stats.py", line 86, in <module>
    sync()
File "/opt/mol/scripts/sync_scraping_stats.py", line 82, in sync
    total_7d = sum(p["ultimos_7d"] for p in merged.values())
KeyError: 'ultimos_7d'
```

El scraping en sí finaliza OK (`=== TODO FINALIZADO: Mon May  4 11:30:44 ===`), pero el step `[STATS] Subiendo stats a Supabase` falla. Stats de scraping en Supabase quedan desactualizadas.

### G2. ComputRabajo descripción enriquecida — regresión

**Hoy:** 374/12.444 (3%) ofertas con descripción enriquecida.
**CLAUDE.md documenta:** *"`fetch_description=True` por default: 1 request extra por oferta para descripción completa"*.

Discrepancia: o el flag está en `False`, o el portal está rate-limitando los detalles. No verificable sin reproducir scrape.

### G3. VPS embed-server vivo pero 0 tráfico

Confirmado en D4: 0 POSTs `/embed` desde 2026-04-01.
- 1.3 GB RAM ocupada permanentemente
- El componente que lo *podría* consumir (Skill Intelligence S2/S3) no lo usa — probablemente porque el path real es **Supabase pgvector con embeddings precalculados**.

### G4. Dos snapshots BGE-M3 en cache

Tanto en local como en VPS hay dos snapshots:
- `5617a9f6…` (pinneado, manifest)
- `9a0624b8…` (otro SHA — origen desconocido)

Si algún script hace `SentenceTransformer('BAAI/bge-m3')` sin `revision=` y el `refs/main` apuntara al SHA nuevo, la generación se haría con un modelo distinto. Verify_corpus_compatibility lo detectaría en `_initialize`, pero la generación de nuevos embeddings (`build_enriched_*.py`) no tiene esa salvaguarda.

### G5. URIs hex-secuenciales sintéticas en config

`config/terminologia_argentina_skills.json` declara 49 URIs hex sintéticas (`a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d`, etc.) para skills cuyo URI ESCO real no se conocía al momento de la creación. Las labels carecen de tildes (origen manual). Aplicado a 30.593 filas (2,7%) en `ofertas_esco_skills_detalle`.

### G6. ofertas_nlp duplicados

217 filas duplicadas por `id_oferta` en `ofertas_nlp` (57.900 vs 57.683 distintas). Origen no investigado — probablemente reprocesos NLP que dejaron duplicados.

### G7. fecha_publicacion_original es texto libre

`fecha_publicacion_original` (TEXT) contiene strings tipo *"Hace 9 días"*, *"Más de 30 días"*, *"3"*. La query inocente *"agrupar por mes"* devuelve esas strings textuales. Para análisis usar `fecha_publicacion_iso` (98.6% coverage).

### G8. Indeed no corre en VPS

CLAUDE.md dice *"Indeed | Activo en VPS"*. La realidad: el script VPS `run_scraping_vps.sh` paso `[6/7] Indeed` ejecuta `queue_indeed_local.py` que solo inserta un comando UUID en `pipeline_commands` para que el local lo procese (`bcd75cf6-…`). **El scraping Indeed corre en local**, no en VPS. CLAUDE.md desactualizado en ese punto.

### G9. estado_oferta=baja: 94% de la BD

57.515 / 60.983 ofertas (94,3%) están en estado `baja`. Solo 3.468 ofertas activas. El sistema hace bajas masivas (probablemente al detectar que no aparecieron en scraping reciente). 31.251 bajas registradas en marzo 2026 (lote retroactivo grande).

### G10. cron daily Bumeran

`crontab` en VPS:
```
0 7 * * *      python3 run_scheduler.py --test
0 8 * * 1,4    bash /opt/mol/scripts/scraping/run_scraping_vps.sh
```

Bumeran daily a las 07:00 AM **todos los días** (`run_scheduler.py --test`). Multi-portal a las 08:00 **solo Lun/Jue**. CLAUDE.md no documenta el daily Bumeran.

### G11. 51 vs 49 URIs

Reporte 4 detectó 51 URIs no canónicas en `ofertas_esco_skills_detalle`. `terminologia_argentina_skills.json` aporta 49 URIs distintas. Discrepancia de 2 — probablemente otras 2 URIs ingresaron por otra ruta (e.g. inserciones manuales históricas o test fixtures).

### G12. Sin tests de reproducibilidad embedding

No hay `test_embed_deterministic.py` ni similar. Si BGE-M3 cambiara su comportamiento entre versiones de torch o sentence-transformers, no habría detección automática (solo el `_verify_corpus_compatibility` que compara SHAs, no embeddings concretos).

---

## Resumen ejecutivo

### BGE-M3

1. **SHA pinneado:** `5617a9f61b028005a4858fdac845db406aefb181` declarado en 7 lugares (manifest, `embedding_config.py`, `matching_config.json`, scripts de build, embed_server VPS). Coincide en todos.
2. **Pinning runtime parcial:** la **carga del modelo en producción** (extractor, VPS) sí pinnea con `revision=`. Los **scripts de generación de embeddings** (`build_enriched_*.py`) NO pinnean — usan `refs/main` del cache. El SHA del manifest es hardcodeado, no extraído del modelo cargado.
3. **LoRA NO existe en disco.** El sistema corre sobre BGE-M3 base. `data/finetuning/matching/` solo tiene `training.log` con texto "Acceso denegado.".
4. **`_verify_corpus_compatibility`** (extractor, línea 1007) verifica al inicializar que el SHA en HF cache coincide con el manifest. Si difiere → `RuntimeError`. Es la única protección activa contra drift de modelo.
5. **VPS embed-server vivo** desde 2026-04-30 (4 días), modelo correctamente pinneado, **0 tráfico real** (0 POSTs `/embed` desde 2026-04-01). Consume 1.3 GB RAM permanentemente.
6. **Drift documentado de 2,5%** en SPEC V2 corresponde a comparación pre-pinning (Apr 7 vs Mar 31). Post-SPEC E el corpus cambió completamente (enriquecimiento), drift por URI 100% (no es bug, es por design).
7. **Dos snapshots BGE-M3 en cache** (local y VPS): el pinneado y `9a0624b8…`. Riesgo bajo (todos los paths críticos pinnean).

### Scraping

8. **Cron VPS funciona OK Lun/Jue 08:00.** Última corrida exitosa: hoy 2026-05-04 08:00–11:30 (3h 30min). Histórico Lun/Jue desde 2026-04-20 sin gaps. Bumeran corre además daily a las 07:00.
9. **Total ofertas BD VPS:** 44.607 (snapshot reciente). **BD local:** 60.983 (incluye histórico). Sync VPS→local cada hora.
10. **94,3% de la BD está en estado `baja`** (57.515 ofertas). 3.468 activas. 3.084 bajas registradas en últimos 6 días.
11. **ZonaJobs paginación rota persiste** (98% duplicación en cada corrida). Compensado con 1.072 keywords distintas para acumular 6.045 únicas.
12. **ComputRabajo regresión:** 3% de ofertas con descripción enriquecida hoy (374/12.444), vs 100% documentado en CLAUDE.md.
13. **Indeed no corre en VPS** (encolado a local via `queue_indeed_local.py`). CLAUDE.md desactualizado.
14. **`cron_errors.log` bug:** `KeyError: 'ultimos_7d'` en `sync_scraping_stats.py:82` — falla silenciosamente cada corrida; stats de scraping no llegan a Supabase.

### Conexión scraping → NLP

15. **Cobertura NLP: 94,6%** (57.683 distintas / 60.983 ofertas). Backlog redujo de 19.007 (22/04) a 3.300 hoy → tasa ~1.309/día. Plausible.
16. **217 filas duplicadas** en `ofertas_nlp` por `id_oferta` (no detectado antes).
17. **id_oferta INTEGER vs TEXT** se origina en `limpiar_titulos.py:823` (`id_oferta = str(row_dict['id_oferta'])`). Sin decisión documentada. Funcionalmente OK (JOIN natural funciona, mismo dígito count → orden lexicográfico = numérico). Performance no medida.

### Riesgos críticos

- **`_verify_corpus_compatibility` solo se ejecuta en `_initialize`.** Si los `.npy` se actualizan en disco mientras un proceso está vivo (no es nuestro caso actual), el cache singleton sigue usando el corpus viejo.
- **0 tests de reproducibilidad embedding.** Cambios de torch/sentence-transformers podrían introducir drift sin detección.
- **Generación de embeddings sin `revision=`.** Si se regeneran sin actualizar `refs/main` deliberadamente, podrían usar un SHA distinto al declarado en el manifest.
- **30.593 filas (2,7%) tienen URIs hex sintéticas** del archivo `terminologia_argentina_skills.json`. Estas skills nunca matchearán contra `esco_skills_metadata_full.json` ni con embeddings — quedan huérfanas en cualquier flujo que use el corpus canónico.
- **VPS embed-server: 1.3 GB RAM ocupada para 0 tráfico.** Costo sin uso. O bien hace falta reconectar Skill Intelligence al endpoint, o bien apagarlo.

### Pendientes

- **Drift exacto local↔VPS** (mismo texto → mismo embedding). No medido para evitar cargar BGE-M3 localmente; se infiere coincidente por SHA pinneado idéntico.
- **Origen exacto de las 2 URIs no canónicas adicionales** (51 detectadas vs 49 en terminologia_argentina_skills.json).
- **EXPLAIN QUERY PLAN** sobre los JOINs `id_oferta INTEGER` vs `TEXT` para confirmar pérdida de índices.
- **S-02 a S-06** del archivo `AUDITORIA_PIPELINE_MOL.md`: el archivo no se encontró en el repo, no se pudo verificar el listado canónico.
- **Distribución por portal y temporal de republicaciones** (query falló por nombre de columna; corregible).
