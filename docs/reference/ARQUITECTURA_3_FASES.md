# Arquitectura MOL - Modelo de 3 Fases

## Vision General

```
┌─────────────────┐         ┌─────────────────────────┐         ┌─────────────────┐
│   ADQUISICION   │         │     PROCESAMIENTO       │         │  PRESENTACION   │
│                 │         │                         │         │                 │
│  Scraping       │────────>│  NLP -> Skills -> Match │────────>│  Dashboard      │
│  Dedup, Bajas   │         │  + Excel validacion     │         │  (solo validados)│
│                 │         │  + Validacion humana    │         │                 │
└─────────────────┘         └─────────────────────────┘         └─────────────────┘
     Fase 1                        Fase 2                           Fase 3
   BD cruda                Excel + datos validados              Usuarios finales
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

### Componentes del Pipeline

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

### Documentacion Relacionada
- `docs/guides/FLUJO_BUMERAN.md` - Flujo especifico Bumeran
- `01_sources/bumeran/README.md` - Documentacion del scraper
- `docs/reference/ZONAJOBS_API_DOCUMENTATION.md` - API ZonaJobs

### Complejidades Tipicas
- Rate limiting / anti-bot de portales
- Encoding (acentos, ñ) - algunas provincias vienen corruptas
- Cambios en estructura HTML de portales
- Deduplicacion cross-source
- Deteccion de ofertas cerradas vs eliminadas (404)

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
| Processors | `database/` |
| Configs | `config/nlp_*.json`, `config/matching_*.json` |
| Export validacion | `scripts/exports/export_validation_excel.py` |
| Validar ofertas | `scripts/validar_ofertas.py` |

### Pipeline Completo

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
│     -> ofertas_esco_skills_detalle                  │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.5 MATCHING ESCO (v3.3.2)                          │
│     match_ofertas_v3.py                             │
│     104 reglas negocio + diccionario arg + semantico│
│     -> ofertas_esco_matching                        │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 2.6 VALIDACION AUTOMATICA                           │
│     auto_validator.py                               │
│     15 reglas de deteccion de errores               │
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
│     -> estado_validacion = 'validado'               │
└─────────────────────────────────────────────────────┘
```

### Salidas de esta Fase

| Salida | Destino | Uso |
|--------|---------|-----|
| Datos procesados | BD SQLite | Interno |
| Excel validacion | Archivo local | Revision humana |
| Ofertas validadas | BD con estado `validado` | Input para Fase 3 |

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
| `config/matching_rules_business.json` | 104 reglas de negocio |
| `config/sinonimos_argentinos_esco.json` | Diccionario argentino |
| `config/area_funcional_esco_map.json` | Mapeo area -> ISCO |

### Documentacion Relacionada
- `docs/reference/PIPELINE.md` - Pipeline tecnico detallado
- `docs/guides/OPTIMIZACION.md` - Flujo de correccion de errores
- `docs/guides/VALIDACION.md` - Sistema de validacion
- `docs/guides/RUN_TRACKING.md` - Comparacion de corridas

### Complejidades Tipicas
- Cadena de dependencias: NLP -> Skills -> Matching
- Reglas de negocio para casos argentinos especificos
- Umbrales de matching (precision vs recall)
- Ciclo de validacion humana hasta calidad aceptable

---

## FASE 3: PRESENTACION

### Objetivo
Presentar datos **YA VALIDADOS** a usuarios finales via dashboard.

### CRITICO
Esta fase SOLO recibe datos con `estado_validacion = 'validado'`.
Los Excel de validacion son parte de Fase 2, NO de Fase 3.

### Entrada
- Ofertas con estado `validado` (pasaron validacion humana en Fase 2)

### Ubicaciones

| Componente | Ubicacion |
|------------|-----------|
| Sync Supabase | `scripts/exports/sync_to_supabase.py` |
| Dashboard | `Visual--/` (Next.js) |
| BD Produccion | Supabase (cloud) |
| Config | `config/supabase_config.json` |

### Pipeline

```
ofertas_esco_matching (validadas)
       │
       v
┌─────────────────────────────────────────────────────┐
│ 3.1 SYNC A SUPABASE                                 │
│     sync_to_supabase.py                             │
│     Solo ofertas con estado = 'validado'            │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 3.2 AGREGACIONES / CALCULOS                         │
│     - Distribucion por provincia                    │
│     - Top skills demandadas                         │
│     - Tendencias temporales                         │
│     - Indices de digitalizacion                     │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 3.3 VISTAS POR TIPO DE USUARIO                      │
│                                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐         │
│  │ Analista  │ │ Director  │ │  Publico  │         │
│  │   OEDE    │ │   OEDE    │ │  General  │         │
│  ├───────────┤ ├───────────┤ ├───────────┤         │
│  │ Detalle   │ │ KPIs      │ │ Resumenes │         │
│  │ Filtros   │ │ Tendencias│ │ Mapas     │         │
│  │ Export    │ │ Alertas   │ │ Rankings  │         │
│  └───────────┘ └───────────┘ └───────────┘         │
└──────────────────────┬──────────────────────────────┘
                       v
┌─────────────────────────────────────────────────────┐
│ 3.4 DASHBOARD NEXT.JS                               │
│     Visual--/                                       │
│     https://mol-nextjs.vercel.app/                  │
└─────────────────────────────────────────────────────┘
```

### Documentacion Relacionada
- `docs/guides/SUPABASE_SYNC.md` - Sincronizacion con Supabase
- `docs/guides/COMPARTIR_DASHBOARD_NGROK.md` - Deployment

### Complejidades Tipicas
- Sync incremental vs full
- Vistas diferenciadas por rol de usuario
- Performance con volumen creciente
- Calculos de agregacion en tiempo real vs pre-calculados

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
| Modificar dashboard | `Visual--/` | 3 |

---

## Dependencias entre Fases

```
FASE 1              FASE 2                    FASE 3
───────             ──────                    ──────
Scraping    ──>     NLP           ──>         Sync Supabase
                      │
                      v
                    Skills        ──>         (Solo validados)
                      │
                      v
                    Matching
                      │
                      v
                    Validacion
                      │
                      v
                    Excel (interno)
                      │
                      v
                    Validacion Humana
                      │
                      v
                    estado='validado' ──────> Dashboard
```

**Regla:** Fase 3 NUNCA recibe datos sin validar.

---

## Regla de Mantenimiento

**CRITICO:** Cada vez que se modifique el pipeline de cualquier fase, actualizar este documento.

Ejemplos:
- Se agrega nuevo scraper -> Actualizar Fase 1
- Se cambia version de NLP -> Actualizar Fase 2
- Se agrega nuevo export -> Actualizar Fase 2 o 3 segun corresponda
- Se modifica sync Supabase -> Actualizar Fase 3

---

*Ultima actualizacion: 2026-01-15*
