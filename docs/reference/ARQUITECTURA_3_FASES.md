# Arquitectura MOL - Modelo de 3 Fases

## Vision General

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FASE 1: ADQUISICION                                     │
│                                                                                      │
│   Portales ──> run_scheduler.py ──> Scrapers ──> SQLite: ofertas (13K+)             │
│   (Bumeran, ZonaJobs, Computrabajo)                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FASE 2: PROCESAMIENTO                                   │
│                                                                                      │
│   ofertas ──────────────────────────────────────────────────────────────────────    │
│       │                                                                              │
│       ▼                                                                              │
│   ┌─────────────────────────────────────┐                                           │
│   │ 2.1 NLP (Qwen2.5:7b)                │                                           │
│   │     process_nlp_from_db_v11.py      │                                           │
│   │     → ofertas_nlp (20 campos)       │                                           │
│   └─────────────────┬───────────────────┘                                           │
│                     ▼                                                                │
│   ┌─────────────────────────────────────┐                                           │
│   │ 2.2 Skills (BGE-M3 + reglas)        │                                           │
│   │     skills_implicit_extractor.py    │                                           │
│   │     → ofertas_esco_skills_detalle   │                                           │
│   └─────────────────┬───────────────────┘                                           │
│                     ▼                                                                │
│   ┌─────────────────────────────────────┐                                           │
│   │ 2.3 Matching ESCO v3.4.2            │                                           │
│   │     match_ofertas_v3.py             │                                           │
│   │     reglas + diccionario argentino  │                                           │
│   │     → ofertas_esco_matching         │                                           │
│   └─────────────────┬───────────────────┘                                           │
│                     ▼                                                                │
│   ┌─────────────────────────────────────┐                                           │
│   │ 2.4 Validación                      │                                           │
│   │     auto_validator.py (22 reglas)   │                                           │
│   │     + validación humana             │                                           │
│   │     → estado_validacion='validado'  │                                           │
│   └─────────────────────────────────────┘                                           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ Solo validadas (~1K)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FASE 3: PRESENTACION                                    │
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │ sync_to_supabase.py                                                          │   │
│   │                                                                              │   │
│   │  SQLite (3 tablas)              Supabase (2 tablas)                         │   │
│   │  ─────────────────              ───────────────────                         │   │
│   │  ofertas          ─┐                                                        │   │
│   │  ofertas_nlp      ─┼──JOIN──>  ofertas_dashboard (desnormalizada)          │   │
│   │  ofertas_esco_    ─┘             - id_oferta, titulo, empresa               │   │
│   │    matching                      - provincia, localidad, modalidad          │   │
│   │                                  - esco_occupation_uri, isco_code           │   │
│   │                                  - nivel_seniority, area_funcional          │   │
│   │                                  - experiencia_min_anios, nivel_educativo   │   │
│   │                                  - jornada_laboral, tiene_gente_cargo       │   │
│   │                                                                              │   │
│   │  ofertas_esco_    ──────────>  ofertas_skills (normalizada)                 │   │
│   │    skills_detalle                - id_oferta, skill_uri                     │   │
│   │                                  - preferred_label                           │   │
│   │                                  - l1, l1_nombre, l2, l2_nombre             │   │
│   │                                  - es_digital, score, origen                │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                            │
│                                         ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │ Dashboard Next.js  →  mol-nextjs.vercel.app                                 │   │
│   │                                                                              │   │
│   │  lib/supabase.ts (con paginación fetchAllPaginated)                         │   │
│   │    - getKPIs(), getOfertasPorProvincia(), getTopOcupaciones()              │   │
│   │    - getSkillsPorCategoriaL1(), getDistribucionRequerimientos()            │   │
│   │                                                                              │   │
│   │  Tabs: Panorama General | Requerimientos | Skills Intelligence | Admin      │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Principio:** Cada fase es independiente y tiene responsabilidades claras.
- **Fase 1** captura datos crudos
- **Fase 2** transforma, valida y produce datos listos para produccion
- **Fase 3** SOLO recibe datos ya validados para usuarios finales

---

## FASE 1: ADQUISICION

### Objetivo
Capturar ofertas laborales de multiples fuentes y mantener la BD actualizada.

### Ubicaciones

| Componente | Ubicacion |
|------------|-----------|
| Scrapers | `01_sources/bumeran/`, `01_sources/zonajobs/`, etc. |
| Entry point | `run_scheduler.py` |
| BD cruda | `database/bumeran_scraping.db` -> tabla `ofertas` |
| Config | `config/scraping.ini` |

### Pipeline Scraping

```
Portales de empleo
       │
       v
┌──────────────────┐
│  run_scheduler   │  <- Orquestador
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Scraper fuente  │  <- BumeranMultiSearch, etc.
└────────┬─────────┘
         │
    ┌────┴────┬────────────┐
    v         v            v
┌───────┐ ┌───────┐ ┌──────────┐
│Dedup  │ │Backup │ │Detectar  │
│       │ │CSV    │ │Bajas     │
└───────┘ └───────┘ └──────────┘
         │
         v
   tabla: ofertas
```

### Estados de una Oferta (Scraping)

| Estado | URL | Postulable | Detectado |
|--------|-----|------------|-----------|
| `activa` | Funciona | Si | Si |
| `cerrada` | Funciona | No | NO |
| `baja` | 404 | No | Si |

---

## FASE 2: PROCESAMIENTO

### Objetivo
Transformar texto crudo en datos estructurados clasificados ESCO + validacion humana.

### IMPORTANTE
Esta fase incluye TODO el ciclo hasta que los datos esten **validados**:
- Extraccion automatica (NLP, Skills, Matching)
- Export Excel para revision humana
- Validacion humana
- Marcado como `validado`

### Ubicaciones

| Componente | Ubicacion |
|------------|-----------|
| NLP Processor | `database/process_nlp_from_db_v11.py` |
| Skills Extractor | `database/skills_implicit_extractor.py` |
| Matching | `database/match_ofertas_v3.py` |
| Validador | `database/auto_validator.py` |
| Configs NLP | `config/nlp_*.json` |
| Configs Matching | `config/matching_*.json` |
| Export validacion | `scripts/exports/export_validation_excel.py` |
| Validar ofertas | `scripts/validar_ofertas.py` |

### Pipeline Detallado

```
ofertas (crudo)
       │
       v
┌─────────────────────────────────────────────────────┐
│ 2.1 LIMPIEZA                                        │
│     limpiar_titulos.py                              │
│     Config: config/nlp_titulo_limpieza.json         │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.2 EXTRACCION NLP (Qwen2.5:7b)                     │
│     process_nlp_from_db_v11.py                      │
│     20 campos: ubicacion, requisitos, salario, etc. │
│     → ofertas_nlp                                   │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.3 POSTPROCESSING                                  │
│     nlp_postprocessor.py                            │
│     Configs: config/nlp_*.json                      │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.4 SKILLS EXTRACTION (BGE-M3)                      │
│     skills_implicit_extractor.py                    │
│     14,247 skills ESCO vectorizadas                 │
│     → ofertas_esco_skills_detalle                   │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.5 MATCHING ESCO (v3.4.2)                          │
│     match_ofertas_v3.py                             │
│     ~195 reglas negocio + diccionario arg + semant. │
│     → ofertas_esco_matching                         │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.6 VALIDACION AUTOMATICA                           │
│     auto_validator.py (22 reglas)                   │
│     → validation_errors                             │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.7 EXPORT VALIDACION (salida interna)              │
│     export_validation_excel.py                      │
│     Excel para revision humana                      │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.8 VALIDACION HUMANA                               │
│     Revision Excel + validar_ofertas.py             │
│     → estado_validacion = 'validado'                │
└─────────────────────────────────────────────────────┘
```

### Configuracion

**NLP:**
| Archivo | Proposito |
|---------|-----------|
| `config/nlp_preprocessing.json` | Parsing ubicacion |
| `config/nlp_inference_rules.json` | Inferencia area/seniority/modalidad |
| `config/nlp_extraction_patterns.json` | Regex experiencia |
| `config/nlp_normalization.json` | CABA -> Capital Federal |
| `config/nlp_validation.json` | Validacion tipos |

**Matching:**
| Archivo | Proposito |
|---------|-----------|
| `config/matching_config.json` | Pesos y umbrales |
| `config/matching_rules_business.json` | ~195 reglas de negocio |
| `config/sinonimos_argentinos_esco.json` | Diccionario argentino (13 ocupaciones) |
| `config/skills_rules.json` | 25 reglas de skills |

**Tracking:**
| Tabla | Proposito |
|-------|-----------|
| `pipeline_runs` | Historial de corridas |
| `ofertas_matching_history` | Historial de cada matching |
| `ofertas_nlp_history` | Versiones NLP por oferta |
| `validation_errors` | Errores detectados por oferta |

---

## FASE 3: PRESENTACION

### Objetivo
Presentar datos **YA VALIDADOS** a usuarios finales via dashboard.

### CRITICO
Esta fase SOLO recibe datos con `estado_validacion IN ('validado_claude', 'validado_humano')`.
Los Excel de validacion son parte de Fase 2, NO de Fase 3.

### Arquitectura Dual de Datos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           sync_to_supabase.py                                │
│                                                                              │
│  SQLite LOCAL (normalizado)          Supabase CLOUD (desnormalizado)        │
│  ─────────────────────────          ────────────────────────────────        │
│                                                                              │
│  ofertas                 ─┐                                                  │
│  ofertas_nlp             ─┼─ JOIN ──>  ofertas_dashboard                    │
│  ofertas_esco_matching   ─┘              (1 tabla plana con todos           │
│                                           los campos para queries           │
│                                           rapidas del dashboard)            │
│                                                                              │
│  ofertas_esco_skills_detalle ────────>  ofertas_skills                      │
│                                           (N:M normalizado con              │
│                                            L1, L2, es_digital)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ubicaciones

| Componente | Ubicacion |
|------------|-----------|
| Sync Supabase | `scripts/exports/sync_to_supabase.py` |
| Dashboard | `fase3_dashboard/mol-dashboard/` |
| BD Produccion | Supabase (PostgreSQL cloud) |
| Config | `config/supabase_config.json` |
| Schema docs | `docs/database/SCHEMA_SUPABASE.md` |
| Sync docs | `docs/database/SYNC.md` |

### Tablas Supabase

**ofertas_dashboard** (desnormalizada para queries rapidas):
| Campo | Origen |
|-------|--------|
| id_oferta, titulo, empresa, url, portal | ofertas |
| titulo_limpio, provincia, localidad, modalidad | ofertas_nlp |
| nivel_seniority, area_funcional, sector_empresa | ofertas_nlp |
| experiencia_min_anios, nivel_educativo | ofertas_nlp |
| tiene_gente_cargo, jornada_laboral | ofertas_nlp |
| esco_occupation_uri, isco_code, isco_label | ofertas_esco_matching |
| occupation_match_score, occupation_match_method | ofertas_esco_matching |

**ofertas_skills** (normalizada para queries de skills):
| Campo | Descripcion |
|-------|-------------|
| id_oferta | FK a ofertas_dashboard |
| skill_uri | URI ESCO del skill |
| preferred_label | Nombre del skill |
| l1, l1_nombre | Categoria nivel 1 |
| l2, l2_nombre | Categoria nivel 2 |
| es_digital | Boolean |
| score, origen | Metadata del matching |

### Dashboard Next.js

**URL:** https://mol-nextjs.vercel.app

**Funciones principales** (`lib/supabase.ts`):
- `fetchAllPaginated()` - Helper para superar limite 1000 filas
- `getKPIs()` - Metricas generales
- `getOfertasPorProvincia()` - Distribucion geografica
- `getTopOcupaciones()` - Ocupaciones mas demandadas
- `getSkillsPorCategoriaL1()` - Skills agrupados
- `getDistribucionRequerimientos()` - Educacion, experiencia, jornada

**Tabs:**
- Panorama General
- Requerimientos
- Skills Intelligence (+ Perfil Argentina)
- Admin (Scraping, Issues)

---

## Mapeo Rapido

| Si necesitas... | Ve a... | Fase |
|-----------------|---------|------|
| Agregar fuente de scraping | `01_sources/` | 1 |
| Corregir extraccion NLP | `config/nlp_*.json` | 2 |
| Agregar regla de matching | `config/matching_rules_business.json` | 2 |
| Exportar Excel validacion | `scripts/exports/export_validation_excel.py` | 2 |
| Validar ofertas | `scripts/validar_ofertas.py` | 2 |
| Sync datos validados | `scripts/exports/sync_to_supabase.py` | 3 |
| Modificar dashboard | `fase3_dashboard/mol-dashboard/` | 3 |

---

## Dependencias entre Fases

```
FASE 1              FASE 2                    FASE 3
───────             ──────                    ──────
Scraping    ──>     NLP
                      │
                      v
                    Skills
                      │
                      v
                    Matching
                      │
                      v
                    Validacion Auto
                      │
                      v
                    Excel (interno)
                      │
                      v
                    Validacion Humana
                      │
                      v
                    estado='validado' ──────> Sync Supabase
                                                    │
                                                    v
                                              Dashboard
```

**Regla:** Fase 3 NUNCA recibe datos sin validar.

---

## Conteos Actuales (ver learnings.yaml)

| Dato | Cantidad |
|------|----------|
| Ofertas SQLite | ~13,824 |
| Ofertas validadas | ~1,026 |
| Skills en Supabase | ~15,309 |
| Reglas de negocio | ~195 |
| Reglas validacion | 22 |
| Reglas skills | 25 |

---

## Regla de Mantenimiento

**CRITICO:** Cada vez que se modifique el pipeline de cualquier fase, actualizar este documento.

Ejemplos:
- Se agrega nuevo scraper -> Actualizar Fase 1
- Se cambia version de NLP -> Actualizar Fase 2
- Se agrega nuevo export -> Actualizar Fase 2 o 3 segun corresponda
- Se modifica sync Supabase -> Actualizar Fase 3
- Se agregan columnas a Supabase -> Actualizar tablas en Fase 3

---

*Ultima actualizacion: 2026-02-04*
