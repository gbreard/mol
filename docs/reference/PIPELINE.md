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

**Gate:** Ofertas con errores critico/alto quedan BLOQUEADAS (no entran a matching)

**Reglas cross-field (NQ01-NQ05):**
- NQ01: Título senior pero seniority trainee → reinferir
- NQ02: Título junior pero seniority senior → reinferir
- NQ03: Área incoherente con título → reinferir
- NQ04: Experiencia >= 5 años pero seniority trainee → warning
- NQ05: Modalidad scraping difiere de NLP → corregir

**Auto-corrección NLP:** Si el gate bloquea, auto_corrector intenta corregir.
Si corrige → re-valida → puede desbloquear. Si no puede → escala a Claude.

## ETAPA 5: MULTI-POSITION DETECTION

- **Archivo:** `database/limpiar_titulos.py` → `expandir_ofertas_multi_perfil()`

**Detección híbrida:**
1. Regex en título ("Vendedor / Cajero")
2. Regex en descripción
3. LLM confirma si son puestos distintos vs polivalente

**Resultado:** Crea sub-ofertas (`id_oferta_2`, `id_oferta_3`) con `parent_id_oferta`.

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

## ETAPA 7: VALIDACIÓN + AUTO-CORRECCIÓN

- **Validación:** `database/auto_validator.py` (V01-V31)
- **Corrección:** `database/auto_corrector.py` (con valor_corregido tracking)

**Tracking fine-tuning:**
- `valor_actual`: Qué tenía el campo cuando se detectó el error
- `valor_corregido`: A qué se cambió

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
