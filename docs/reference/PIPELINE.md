# Arquitectura del Pipeline MOL

## Pipeline COMPLETO - 8 Pasos (v3.3)

```
SCRAPING → NLP v11.4 → NLP GATE → MULTI-POS → MATCHING v3.5.4 → VALIDACIÓN → AUTO-CORR → EXPORT
              │            │           │              │               │             │
              │            │           │              │               │             └── valor_corregido
              │            │           │              │               └── validation_errors
              │            │           └── sub-ofertas │
              │            └── bloquea critico/alto    └── ofertas_esco_matching
              └── ofertas_nlp + llm_raw_json                + ofertas_esco_skills_detalle
```

**Entry point:** `python scripts/run_validated_pipeline.py --limit 500`

## ETAPA 1: SCRAPING + DETECCIÓN DE BAJAS

- **Archivo:** `run_scheduler.py` → `01_sources/bumeran/`
- **VPS:** `scripts/scraping/run_scraping_vps.sh` (6 portales)
- **Salida:** Datos crudos en `database/bumeran_scraping.db`

**Portales:** Bumeran, ZonaJobs, ComputRabajo, CABA, Portal Empleo Nacional, Indeed

**Estados de una oferta:**

| Estado | URL | ¿Postulable? | Detectado |
|--------|-----|--------------|-----------|
| `activa` | Funciona | Sí | Sí |
| `cerrada` | Funciona | No | **NO** |
| `baja` | 404 | No | Sí |

## ETAPA 2: LIMPIEZA DE TÍTULO (v2.8.1)

- **Archivo:** `database/limpiar_titulos.py`
- **Config:** `config/nlp_titulo_limpieza.json`

**Ejemplo:**
```
ANTES:  "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10..."
DESPUÉS: "Operarios industria ALIMENTICIA"
```

**Patrones que elimina:** Códigos internos, fechas/horarios, sucursales, prefijos, ubicaciones.
**v2.8.1:** Second pass cleanup + acronym preservation (DBA, SAP, QA, SQL, etc.)

## ETAPA 3: EXTRACCIÓN NLP v11.4 (Source-Aware)

- **Archivo:** `database/process_nlp_from_db_v11.py`
- **Modelo:** Qwen2.5:7b via Ollama

**Arquitectura v11.4:**
```
CAPA 0: Regex (salarios, jornada) + Scraping directo (modalidad, portal)
CAPA 1: LLM Qwen2.5:7b (20 campos)
CAPA 1b: Source-aware pre-fill (metadata embebida de CABA/Portal Empleo/Indeed)
CAPA 2: Postprocessor (config/nlp_*.json) + diff tracking
CAPA 3: Skills implícitas (LoRA fine-tuned + ESCO embeddings)
```

**Campos principales:**
- Ubicación: provincia, localidad, modalidad
- Requisitos: experiencia, educación, idiomas
- Persona: sexo requerido, edad
- Trabajo: jornada, turnos, gente a cargo
- Salario: min/max, moneda
- Skills: técnicas, soft skills
- Tareas: lista de responsabilidades

**Fine-tuning data (v11.4):**
- `llm_raw_json`: Output original del LLM (antes del postprocessor)
- `postprocessor_diff_json`: Campos que el postprocessor cambió (before/after)

## ETAPA 3b: POSTPROCESSING v1.3 (Source-Aware)

- **Archivo:** `database/nlp_postprocessor.py`
- **Configs:** `config/nlp_*.json`

**Correcciones:**
1. **Source-aware pre-fill:** Metadata embebida de CABA/Portal Empleo/Indeed
2. **Ubicación:** Prioriza dato scraping sobre inferido
3. **Sector:** Corrige clasificaciones erróneas + catálogo empresas
4. **Merge skills:** Combina regex + LLM
5. **Modalidad:** Scraping SIEMPRE gana sobre LLM

## ETAPA 4: NLP VALIDATION GATE v1.1

- **Archivo:** `database/nlp_validator.py`
- **Config:** `config/nlp_validation_rules.json` (35+ reglas)

**Gate:** Ofertas con errores critico/alto quedan BLOQUEADAS (no entran a matching).
Solo ofertas con `nlp_gate_status = 'aprobado'` pasan a las etapas siguientes.

**Familias de reglas (35+):**

| Familia | Rango | Qué validan |
|---------|-------|-------------|
| V (Validación) | V01-V26 | Campos individuales: formato, rango, valores permitidos |
| NV (NLP Validation) | NV02-NV11 | Coherencia NLP: ubicación, sector, experiencia, educación |
| NQ (NLP Quality) | NQ01-NQ05 | Cross-field: título vs seniority, área vs título, modalidad scraping vs NLP |

**Severidades y acción:**

| Severidad | Acción | Ejemplo |
|-----------|--------|---------|
| `critico` | BLOQUEA matching | Provincia inválida, tareas vacías |
| `alto` | BLOQUEA matching | Seniority contradice título, área incoherente |
| `medio` | WARNING (no bloquea) | Experiencia alta pero seniority trainee |
| `bajo` | INFO (no bloquea) | Tareas muy cortas (< 50 chars) |

**Reglas cross-field (NQ01-NQ05):**
- NQ01: Título contiene "senior/gerente/jefe" pero seniority es trainee → reinferir
- NQ02: Título contiene "junior/pasante/trainee" pero seniority es senior → reinferir
- NQ03: Área funcional incoherente con título (ej: "Contador" con área "IT") → reinferir
- NQ04: Experiencia >= 5 años pero seniority trainee → warning
- NQ05: Modalidad scraping difiere de NLP → corregir (scraping gana)

**Auto-corrección NLP:** Si el gate bloquea, `auto_corrector.py` intenta corregir.
Si corrige → re-valida → puede desbloquear. Si no puede → escala a Claude
(marcado `escalado_claude=1` en `validation_errors`, genera `metrics/cola_claude_*.json`).

### ETAPA 4b: CANONIZACIÓN DE TAREAS (2026-03-26 — planificado)

Nueva etapa entre Gate NLP y Skills. Cada oferta recibe una tarea canónica como metadata adicional.

```
Tareas originales (del NLP)
    ↓
Buscador de tarea canónica (embedding similarity > 0.80)
    ↓
Si matchea → asigna tarea_canonica existente
Si no matchea → queda como "nueva tarea sin canónico" → cola analista
    ↓
Tarea original SE MANTIENE (preserva varianza)
Tarea canónica SE AGREGA (metadata para análisis)
```

**Tabla:** `tareas_canonical`
**Config:** `config/tareas_canonical.json` (cuando exista)
**Admin:** `/admin/procesamiento/fabrica/tareas`

## ETAPA 5: MULTI-POSITION DETECTION

- **Archivo:** `database/limpiar_titulos.py` → `expandir_ofertas_multi_perfil()`

**Detección híbrida (regex + LLM):**
1. **Regex en título:** Detecta separadores (`/`, `–`, `y/o`) entre sustantivos distintos
2. **Regex en descripción:** Busca listas de puestos o secciones separadas por perfil
3. **LLM confirma:** Qwen2.5:7b decide si son puestos genuinamente distintos vs polivalente
   (ej: "Vendedor / Cajero" = 2 puestos, "Analista Contable / Impositivo" = 1 puesto polivalente)

**Resultado:** Crea sub-ofertas (`id_oferta_2`, `id_oferta_3`) con `parent_id_oferta`.
Cada sub-oferta recibe su propio título limpio y pasa por el pipeline completo de forma independiente.

**Ejemplo concreto:**
```
Oferta original: "Vendedor / Cajero para sucursal centro"
  → Sub-oferta 1: "Vendedor"  → ISCO 5223 (Vendedores de tiendas)
  → Sub-oferta 2: "Cajero"    → ISCO 4220 (Cajeros de banco y afines)
  → Ambas con parent_id_oferta = id original
```

## ETAPA 6: SKILLS → MATCHING v3.5.4

- **Archivo:** `database/match_ofertas_v3.py` → `match_and_persist()`

**Orden interno:**
1. `skills_implicit_extractor.py` v2.4 - Extrae skills (LoRA fine-tuned)
2. `match_by_skills.py` - Usa skills como INPUT para matching
3. `skill_categorizer.py` - Categoriza L1/L2

**Proceso:**
```
titulo_limpio + tareas
        │
        ▼
1. EXTRAER SKILLS (LoRA fine-tuned, 14,257 skills ESCO)
   └── Persiste en: ofertas_esco_skills_detalle
        │
        ▼
2. REGLAS DE NEGOCIO (297 reglas, GANAN SIEMPRE)
   └── titulo_original_contiene_alguno (v3.5.4)
        │
        ▼
3. DICCIONARIO ARGENTINO (17 ocupaciones)
        │
        ▼
4. MATCHING SEMÁNTICO
   ├── Score = 60% skills + 40% semántico título
   └── Persiste en: ofertas_esco_matching
        │
        ▼
5. Categorizar Skills (L1/L2 + es_digital)
```

### Cambio Skills Extractor (2026-03-26)

- Modelo: BAAI/bge-m3 base (LoRA fine-tuned no disponible — model_lora no existe)
- Umbral: 0.40 (bajado de 0.60 para BGE-M3 base)
- Planificado: Reducir 14,247 skills ESCO a ~3,000 canónicas por clustering
- Tabla: `skills_canonical`
- Admin: `/admin/procesamiento/fabrica/skills`, `/admin/procesamiento/fabrica/canonizacion`

> Plan completo: `docs/plan/14_CANONIZACION_SKILLS_TAREAS.md`

## ETAPA 7: VALIDACIÓN + AUTO-CORRECCIÓN

- **Validación:** `database/auto_validator.py` (V01-V31)
- **Corrección:** `database/auto_corrector.py` (con valor_corregido tracking)

**Tracking fine-tuning:**
- `valor_actual`: Qué tenía el campo cuando se detectó el error
- `valor_corregido`: A qué se cambió

## ETAPA 8: TRAINING DATA GENERATION

El pipeline genera datos de entrenamiento en múltiples puntos para futuro fine-tuning del modelo de clasificación ESCO.

### Datos capturados durante el pipeline

| Campo | Tabla | Qué contiene | Cuándo se genera |
|-------|-------|--------------|------------------|
| `llm_raw_json` | `ofertas_nlp` | Output original del LLM (antes del postprocessor) | Paso 1 (NLP) |
| `postprocessor_diff_json` | `ofertas_nlp` | Campos que cambió el postprocessor (before/after/razón) | Paso 1 (Postprocessor) |
| `valor_actual` | `validation_errors` | Valor del campo cuando se detectó el error | Paso 3 (Validación) |
| `valor_corregido` | `validation_errors` | Valor al que se cambió tras corrección | Paso 4 (Auto-corrección) |

### Pipeline de training pairs

```
validation_errors (BD local)
    → issues (Supabase, reportados por usuarios)
        → issue resuelto (con solucion_aplicada)
            → sync_learnings.py (auto-trigger)
                → generate_training_pairs.py
                    → config/training_pairs.json (dataset acumulado, 583+ pares)
```

- **Archivo generador:** `scripts/exports/generate_training_pairs.py`
- **Auto-trigger:** Se ejecuta automáticamente al final de `scripts/sync_learnings.py`
- **Deduplicación:** Issues de múltiples aspectos de la misma oferta se mergean
- **3 formatos soportados:** Supervised, DPO/RLHF, Chain-of-Thought

### Estructura de un training pair

```json
{
  "input": {"titulo": "...", "descripcion": "...", "tareas": "...", "sector": "..."},
  "clasificacion_incorrecta": {"isco": "0110", "label": "Oficial de las fuerzas armadas"},
  "clasificacion_correcta": {"isco": "6111", "label": "Agricultor"},
  "justificacion_humana": "Descripción del usuario sobre por qué es incorrecto"
}
```

## CONFIG OVERRIDES (Supabase → Local)

El pipeline soporta un mecanismo de override de configuración desde Supabase, permitiendo editar configs desde la UI del dashboard sin tocar archivos locales.

**Mecanismo:**
```
load_config("matching_rules_business")
    → 1. Buscar override en Supabase (tabla config_overrides)
    → 2. Si existe y es más reciente → usar override
    → 3. Si no existe → usar config/matching_rules_business.json local
```

**6 configs editables desde UI:**

| Config | Archivo local | Editable desde |
|--------|--------------|----------------|
| `matching_rules_business` | `config/matching_rules_business.json` | /admin/configuracion |
| `nlp_inference_rules` | `config/nlp_inference_rules.json` | /admin/configuracion |
| `sinonimos_argentinos_esco` | `config/sinonimos_argentinos_esco.json` | /admin/configuracion |
| `nlp_validation_rules` | `config/nlp_validation_rules.json` | /admin/configuracion |
| `skills_rules` | `config/skills_rules.json` | /admin/configuracion |
| `nlp_titulo_limpieza` | `config/nlp_titulo_limpieza.json` | /admin/configuracion |

**Preview de impacto:** Antes de aplicar un cambio, el UI muestra cuántas ofertas serían afectadas y un preview del resultado esperado.

**Flujo de aplicación:**
1. Usuario edita config en UI → guarda como override en Supabase
2. Próxima ejecución del pipeline usa el override automáticamente
3. Si se elimina el override → vuelve al JSON local

---

## Categorías L1 de Skills

| Código | Nombre | Ejemplos |
|--------|--------|----------|
| S1 | Comunicación | redacción, presentaciones |
| S3 | Asistencia/Ventas | atención cliente, negociación |
| S4 | Gestión | contabilidad, planificación |
| S5 | Digital/IT | Python, Excel, SAP |
| S6 | Técnicas | soldadura, electricidad |
| K | Conocimientos | normativa, inglés técnico |
| T | Transversales | liderazgo, trabajo en equipo |

## Pipeline Simplificado (vista rápida)

```
scripts/run_validated_pipeline.py (ENTRY POINT ÚNICO v3.3)
    │
    ├── PASO 1: NLP v11.4 (source-aware)
    │   └── process_nlp_from_db_v11.py ──► ofertas_nlp
    │       └── nlp_postprocessor.py (pre-fill metadata + diff tracking)
    │
    ├── PASO 1.5: NLP GATE v1.1
    │   └── nlp_validator.py (35+ reglas) ──► aprobado/bloqueado
    │       └── auto_corrector.py (si bloqueado → corregir → re-validar)
    │
    ├── PASO 1.6: MULTI-POSITION
    │   └── limpiar_titulos.py ──► sub-ofertas (regex + LLM)
    │
    ├── PASO 2: MATCHING v3.5.4
    │   └── match_ofertas_v3.py
    │       ├── skills_implicit_extractor v2.4 ──► ofertas_esco_skills_detalle
    │       └── match_by_skills ──► ofertas_esco_matching
    │
    ├── PASO 3-4: VALIDACIÓN + AUTO-CORRECCIÓN
    │   └── auto_validator.py + auto_corrector.py ──► validation_errors
    │
    ├── PASO 5: NLP RE-PROCESS (si errores NLP, max 2 iter)
    │
    ├── PASO 6: REPORTE CLAUDE (cola_claude.json)
    ├── PASO 7: EXPORT EXCEL
    └── PASO 8: SYNC LEARNINGS
```

## Uso en Producción

```bash
# Pipeline completo (8 pasos)
python scripts/run_validated_pipeline.py --limit 500

# NLP batch en background (skip matching)
python scripts/launch_nlp_batch.py

# IDs específicos
python scripts/run_validated_pipeline.py --ids 123,456,789

# Solo matching (skip NLP)
python scripts/run_validated_pipeline.py --ids 123 --skip-nlp
```
