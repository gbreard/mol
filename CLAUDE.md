# MOL - Monitor de Ofertas Laborales

## LEER PRIMERO: Estado Actual

**ANTES DE HACER CUALQUIER COSA, leer `.ai/learnings.yaml` para el estado actual del trabajo.**

El archivo `learnings.yaml` contiene:
- `current_state`: Qué estamos haciendo AHORA (ofertas, versiones, próximo paso)
- `ultimo_trabajo`: Qué se hizo en la última sesión
- `problemas_conocidos`: Issues actuales

**Comando del usuario: "Guardá estado"** → Actualizar learnings.yaml con el estado actual.

**REGLA: Actualizar `.ai/learnings.yaml` AUTOMATICAMENTE después de cada cambio significativo** (editar archivo, arreglar bug, procesar ofertas, agregar regla). No esperar a que el usuario lo pida.

---

## Descripcion
Sistema de monitoreo del mercado laboral argentino para OEDE. Scrapea ofertas de empleo, extrae informacion con NLP, clasifica segun taxonomia ESCO, y provee dashboards para analistas.

## Estado Actual (2026-01-14)
- 11,001 ofertas en BD
- **100 ofertas con matching procesado**, estado `pendiente` (en validación)
- NLP v11.3 (20 campos + postprocessor + qwen2.5:7b)
- **Matching v3.3.2** con prioridad: Reglas negocio → Diccionario argentino → Semántico
- Skills implicitas: 14,247 embeddings ESCO skills pre-calculados
- **Diccionario argentino**: `config/sinonimos_argentinos_esco.json` (12 ocupaciones)
- **Auto-validación**: `config/validation_rules.json` (15 reglas)

### Trabajo en Curso
- Validando 100 ofertas para dashboard (próximo paso: revisión manual)
- Gold Set de referencia: 49 casos (archivo histórico, la validación real es sobre los 100)

---

## Modelo de 3 Fases

El proyecto se organiza en 3 macro-fases independientes:

| Fase | Descripcion | Ubicacion Principal | Salida |
|------|-------------|---------------------|--------|
| 1. Adquisicion | Scraping, deteccion bajas | `01_sources/`, `run_scheduler.py` | BD cruda |
| 2. Procesamiento | NLP, Skills, Matching, **Validacion** | `database/`, `config/`, `export_validation_excel.py` | Excel validacion + datos validados |
| 3. Presentacion | Dashboard (solo validados) | `Visual--/`, `sync_to_supabase.py` | Dashboard usuarios finales |

**Para trabajar en una fase especifica**, indicar en `learnings.yaml`:
```yaml
fase_actual: "procesamiento"  # adquisicion | procesamiento | presentacion
```

**REGLA:** Si modificas el pipeline de una fase, actualizar `docs/reference/ARQUITECTURA_3_FASES.md`.

> Arquitectura completa: `docs/reference/ARQUITECTURA_3_FASES.md`

---

## Documentación Extendida

| Tema | Documento | Cuándo leer |
|------|-----------|-------------|
| **Arquitectura 3 Fases** | `docs/reference/ARQUITECTURA_3_FASES.md` | Entender macro-estructura |
| **Colaboracion (multi-dev)** | `docs/guides/COLABORACION.md` | Trabajo en equipo, sync git |
| Pipeline completo (5 etapas) | `docs/reference/PIPELINE.md` | Entender flujo de datos |
| Run Tracking y Versionado | `docs/guides/RUN_TRACKING.md` | Comparar corridas |
| Sistema de Validación | `docs/guides/VALIDACION.md` | Estados, protección datos |
| Flujos de Optimización | `docs/guides/OPTIMIZACION.md` | Corregir errores NLP/Matching |
| Sincronización Supabase | `docs/guides/SUPABASE_SYNC.md` | Subir datos al dashboard |

**IMPORTANTE:** Antes de optimizar el pipeline, LEER `docs/guides/OPTIMIZACION.md`.

---

## REGLAS CRÍTICAS - LEER PRIMERO

**ANTES de escribir código o crear archivos:**

1. **LEER este CLAUDE.md COMPLETO** - todo está documentado aquí
2. **NUNCA crear scripts nuevos** - buscar si ya existe uno para la tarea
3. **Cambios van en `config/*.json`** - no en código Python
4. **Si hay que modificar un `.py`**:
   - Versionar (ej: `v3.py` → `v4.py`)
   - Archivar versión anterior en `archive_old_versions/`
   - Actualizar CLAUDE.md

### Entry Points del Sistema (NO crear alternativas)

| Tarea | Comando | NO hacer |
|-------|---------|----------|
| **Matching lote** | `run_matching_pipeline(offer_ids=[...])` en `match_ofertas_v3.py` | ⚠️ NUNCA `match_and_persist()` directo |
| **Export Excel** | `python scripts/exports/export_validation_excel.py --etapa completo --ids X` | Crear export custom |
| **NLP lote** | `python database/process_nlp_from_db_v11.py --ids X` | Crear script nuevo |
| **Scraping** | `python run_scheduler.py` | Llamar scrapers directo |
| **Comparar runs** | `python scripts/compare_runs.py --latest` | Crear comparador custom |
| **Validar ofertas** | `python scripts/validar_ofertas.py --ids X --estado validado` | UPDATE manual en BD |
| **Auto-validar** | `python database/auto_validator.py --limit 100` | Queries manuales |
| **Revisar cadena** | `python scripts/review_offer_chain.py --errores` | Revisar solo matching |
| **Sync Supabase** | `python scripts/exports/sync_to_supabase.py` | Queries directas a Supabase |

**⚠️ REGLA CRÍTICA - Run Tracking (v3.3.2):**
- SIEMPRE usar `run_matching_pipeline()` para matching, NUNCA `match_and_persist()` directo
- `match_and_persist()` sin `run_id` genera WARNING y ofertas quedan sin tracking
- Si ves ofertas con `run_id = NULL` en BD, es porque alguien llamó `match_and_persist()` directo
- El código ahora emite un WARNING visible cuando esto pasa

---

## Pipeline de Validación con Aprendizaje (v1.0)

**Principio:** Claude REVISA casos individuales para APRENDER y crear REGLAS en JSONs.
El sistema luego aplica las reglas automáticamente. Claude NO reemplaza al LLM.

### Cadena de Dependencias

```
SCRAPING → NLP → SKILLS → MATCHING
              ↓       ↓         ↓
           tareas  extraídas  ESCO code
           ubicación  de tareas+título
           seniority
           área

Si NLP extrae mal las tareas → Skills quedan mal → Matching falla
```

### Flujo de Trabajo Claude

```
PASO 1: PROCESAR
────────────────
python -c "
from database.match_ofertas_v3 import run_matching_pipeline
stats = run_matching_pipeline(limit=100, source='optimizacion_v1')
print(f'Run ID: {stats[\"run_id\"]}')
"

PASO 2: DETECTAR ERRORES
────────────────────────
python database/auto_validator.py --limit 100 --reporte

PASO 3: CLAUDE REVISA UNO POR UNO (cadena completa)
───────────────────────────────────────────────────
python scripts/review_offer_chain.py --errores --limit 5

Claude ve TODA la cadena:
1. SCRAPING: ¿Datos completos?
2. NLP: ¿Tareas, ubicación, seniority, área correctos?
3. SKILLS: ¿Coherentes con título y tareas?
4. MATCHING: ¿ISCO correcto?

Claude identifica DÓNDE falló y crea regla en el JSON correspondiente.

PASO 4: CREAR REGLA
───────────────────
Según dónde falló:
| Falla en | Config a modificar |
|----------|-------------------|
| NLP - tareas | prompt o nlp_extraction_patterns.json |
| NLP - ubicación | config/nlp_preprocessing.json |
| NLP - seniority | config/nlp_inference_rules.json |
| NLP - área | config/nlp_inference_rules.json |
| Skills - faltan | config/skills_database.json |
| Matching | config/matching_rules_business.json |

PASO 5: REPROCESAR
──────────────────
python -c "
from database.match_ofertas_v3 import run_matching_pipeline
stats = run_matching_pipeline(offer_ids=['id1','id2'], source='fix_v1')
"

PASO 6: COMPARAR
────────────────
python scripts/compare_runs.py --latest

REPETIR hasta sin errores.
```

### Archivos del Sistema de Validación

| Archivo | Función |
|---------|---------|
| `config/validation_rules.json` | 15 reglas de auto-detección de errores |
| `config/diagnostic_patterns.json` | Patrones para identificar punto de falla |
| `config/auto_correction_map.json` | Mapeo diagnóstico → config a modificar |
| `database/auto_validator.py` | Validador automático |
| `database/auto_corrector.py` | Corrector automático |
| `scripts/review_offer_chain.py` | **Revisión UNO POR UNO** (cadena completa) |

### Ejemplo de Revisión Claude

```
Caso: "Gerente de Ventas" → ISCO 2433 (incorrecto, debería ser 1221)

Claude revisa cadena:
1. SCRAPING: OK
2. NLP: nivel_seniority = NULL ❌ (debería ser "manager")
3. SKILLS: OK
4. MATCHING: Sin seniority, no priorizó nivel directivo

Diagnóstico: Falla RAÍZ en NLP (seniority no inferido de "Gerente")

Claude crea reglas:
1. nlp_inference_rules.json: {"keyword": "gerente", "nivel_seniority": "manager"}
2. matching_rules_business.json: R_GERENTE_VENTAS → forzar_isco 1221

Reprocesar → ISCO correcto
Próxima vez: Sistema aplica regla automáticamente
```

→ **Plan completo:** `/home/gerardo/.claude/plans/elegant-crunching-hippo.md`
→ **Guía optimización:** `docs/guides/OPTIMIZACION.md`

---

### Flujo de Optimización LEGACY (sin revisión Claude)

```
1. PROCESAR    → run_matching_pipeline(ids, source="gold_set")
2. EXPORTAR   → export_validation_excel.py --ids X
3. CORREGIR   → Modificar config/*.json (NO código Python)
4. COMPARAR   → compare_runs.py --latest
5. REPETIR    → Pasos 2-4 hasta que esté OK
6. VALIDAR    → validar_ofertas.py --ids X --estado validado
```

→ **Detalles:** `docs/guides/VALIDACION.md`

### Protección de Datos Validados

**CRÍTICO:** Una vez que una oferta tiene `estado_validacion = 'validado'`:
- El pipeline **RECHAZA** reprocesarla (error automático)
- Para forzar: usar `force=True` (NO recomendado)

---

## VERSIONES ACTUALES - USAR SIEMPRE ESTAS

### NLP Pipeline

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline NLP | `database/process_nlp_from_db_v11.py` | v7, v8, v9, v10 |
| Prompt | `database/prompts/extraction_prompt_lite_v1.py` | v8, v9, v10 |
| Regex Patterns | `database/patterns/regex_patterns_v4.py` | v1, v2, v3 |
| Normalizador | `database/normalize_nlp_values.py` | - |

**Arquitectura v11.3:**
```
CAPA 0: Regex (salarios, jornada) + Scraping directo (modalidad)
CAPA 1: LLM Qwen2.5:7b (20 campos)
CAPA 2: Postprocessor (config/nlp_*.json)
CAPA 3: Skills implícitas (BGE-M3 + ESCO embeddings)
```

### Matching Pipeline v3.3.2

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline Matching | `database/match_ofertas_v3.py` v3.3.2 | v2.py, v8.x |
| Matcher por Skills | `database/match_by_skills.py` v1.2.0 | - |
| Skills Extractor | `database/skills_implicit_extractor.py` v2.0 | - |
| Diccionario Argentino | `config/sinonimos_argentinos_esco.json` (12 ocup) | - |
| Config reglas negocio | `config/matching_rules_business.json` (52 reglas) | hardcodeados |
| Config principal | `config/matching_config.json` | - |

**Arquitectura v3.3.2 (orden de prioridad):**
```
1. REGLAS DE NEGOCIO (bypass) ← Prioridad máxima, casos específicos
        ↓ (si no matchea)
2. DICCIONARIO ARGENTINO ← Vocabulario local → ISCO
        ↓ (si no matchea)
3. SEMÁNTICO (BGE-M3) ← Skills 60% + Titulo 40%
        ↓
4. PENALIZACIONES (sector, seniority)
        ↓
5. PERSISTIR EN BD
```

→ **Detalles:** `docs/reference/PIPELINE.md`

### Tests y Gold Sets

| Conjunto | Ubicación | Casos | Uso |
|----------|-----------|-------|-----|
| **Ofertas en validación** | BD `ofertas_esco_matching` | **100** | Validar para dashboard |
| Gold Set referencia | `database/gold_set_manual_v2.json` | 49 | Test de regresión |
| NLP Extraction | `tests/nlp/gold_set.json` | 20+ | Test NLP |

**IMPORTANTE:** El trabajo actual es sobre las **100 ofertas en validación**, no el Gold Set de 49.

```bash
# Ejecutar tests
python -m pytest tests/ -v

# Test Gold Set Matching (referencia)
pytest tests/matching/test_gold_set_manual.py -v

# Ver estado de las 100 ofertas en validación
python scripts/validar_ofertas.py --status
```

---

## Configuración

### Configs NLP (Postprocessor)

| Archivo | Propósito |
|---------|-----------|
| `config/nlp_preprocessing.json` | Parsing ubicación |
| `config/nlp_inference_rules.json` | Inferencia área/seniority/modalidad |
| `config/nlp_validation.json` | Validación tipos |
| `config/nlp_extraction_patterns.json` | Regex experiencia |
| `config/nlp_normalization.json` | CABA → Capital Federal |

### Configs Matching

| Archivo | Propósito |
|---------|-----------|
| `config/matching_config.json` | Pesos, umbrales, penalizaciones |
| `config/matching_rules_business.json` | 52 reglas de negocio |
| `config/area_funcional_esco_map.json` | Mapeo área → ISCO |
| `config/sector_isco_compatibilidad.json` | Compatibilidad sector-ISCO |

### Diccionarios

| Archivo | Propósito |
|---------|-----------|
| `config/skills_database.json` | ~320 skills técnicas |
| `config/oficios_arg.json` | ~170 oficios argentinos |

---

## Comandos Clave

```bash
# === SCRAPING ===
python run_scheduler.py --test

# === NLP ===
python database/process_nlp_from_db_v11.py --ids 123,456

# === MATCHING ===
pytest tests/matching/test_gold_set_manual.py -v

# === VALIDACIÓN ===
python scripts/validar_ofertas.py --status
python scripts/compare_runs.py --list
python scripts/compare_runs.py --latest
python scripts/validar_ofertas.py --ids 123,456 --estado validado

# === EXPORT ===
python scripts/exports/export_validation_excel.py --etapa completo --ids X
```

---

## Guía Rápida: Mapeo Error → Config

| Tipo de Error | Config a Editar |
|---------------|-----------------|
| Provincia/Localidad mal | `config/nlp_preprocessing.json` |
| Seniority incorrecto | `config/nlp_inference_rules.json` |
| Modalidad incorrecta | `config/nlp_inference_rules.json` |
| Área funcional incorrecta | `config/nlp_inference_rules.json` |
| ISCO incorrecto para título X | `config/matching_rules_business.json` |

→ **Tabla completa:** `docs/guides/OPTIMIZACION.md`

---

## Regla de Versionado

**OBLIGATORIO:** Cuando se crea una nueva versión:

1. Crear nueva versión (ej: `v11.py`)
2. Archivar anterior en `database/archive_old_versions/`
3. Verificar que nada importe el archivo archivado
4. Actualizar CLAUDE.md

**NUNCA** dejar dos versiones activas en el mismo directorio.

---

## Ubicación de Scripts

| Si el script es para... | Va en... |
|-------------------------|----------|
| Gold Set NLP | `scripts/nlp/gold_set/` |
| Gold Set Matching | `scripts/matching/gold_set/` |
| Backup/migrate BD | `scripts/db/` |
| Exportar (S3, Excel) | `scripts/exports/` |
| Linear | `scripts/` (raíz) |

**NUNCA** crear `test_*.py` fuera de `tests/`.

---

## Estructura del Proyecto (Resumen)

```
MOL/
├── 01_sources/          # Scraping (bumeran/, zonajobs/, etc.)
├── database/            # BD, NLP processors, matching
│   ├── prompts/         # Prompts LLM
│   ├── patterns/        # Regex patterns
│   └── archive_old_versions/
├── config/              # JSONs de configuración
├── tests/               # Tests pytest
├── scripts/             # Utilidades
│   ├── db/              # BD
│   ├── nlp/gold_set/    # Optimización NLP
│   ├── matching/        # Optimización Matching
│   └── exports/         # Exportaciones
├── docs/                # Documentación
│   ├── guides/          # RUN_TRACKING, VALIDACION, OPTIMIZACION
│   └── reference/       # PIPELINE
├── Visual--/            # Dashboard R Shiny (PRODUCCIÓN)
└── run_scheduler.py     # Entry point scraping
```

---

## Modelos LLM/ML

| Modelo | Uso |
|--------|-----|
| **Qwen2.5:7b** | NLP: extracción semántica |
| **BGE-M3** | Matching: embeddings |
| **ChromaDB** | Skills lookup |

**Requisitos:**
- Ollama en `localhost:11434` con `qwen2.5:7b`
- ChromaDB con vectores en `database/esco_vectors/`

---

## Reglas de Desarrollo

1. **Scraping:** SIEMPRE `run_scheduler.py`, NUNCA scrapers directo
2. **Tests:** Todo cambio NLP/Matching debe pasar Gold Set
3. **Umbrales:** NLP >= 90%, Matching >= 95%
4. **Linear:** Usar cache (`scripts/linear_*.py`), NUNCA MCP directo

---

## Flujo de Branches

```
main                    ← Producción (solo via PR)
  └── develop           ← Integración (pasó Gold Set)
        ├── feature/optimization-nlp
        └── feature/optimization-matching
```

**NUNCA** push directo a `main`. **SIEMPRE** Gold Set antes de merge.

---

## Colaboracion Multi-Desarrollador

Este proyecto es trabajado por **multiples personas en distintas fases**.

**LEER:** `docs/guides/COLABORACION.md` para reglas de sync, division de trabajo y referencias a documentacion oficial de Claude Code.

---

## AI Platform Local

Plataforma en `D:\AI_Platform`.

```python
import httpx
GATEWAY = "http://localhost:8080"
```

| Endpoint | Descripción |
|----------|-------------|
| `POST /v1/chat/completions` | LLM |
| `POST /v1/embeddings` | Embeddings |

Docs: http://localhost:8080/docs

---

> **Última actualización:** 2026-01-14
