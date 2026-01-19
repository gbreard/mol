# Arquitectura del Pipeline MOL

## Pipeline COMPLETO - 5 Etapas

```
SCRAPING → LIMPIEZA → NLP → POSTPROC → SKILLS → MATCHING (v3.2) → DASH
                                          │          │
                                          │          └── ofertas_esco_matching
                                          │
                                          └── ofertas_esco_skills_detalle
```

**Orden conceptual:** Skills se extraen PRIMERO, luego Matching USA esas skills como input.

## ETAPA 1: SCRAPING + DETECCIÓN DE BAJAS

- **Archivo:** `run_scheduler.py` → `01_sources/bumeran/`
- **Salida:** Datos crudos en `database/bumeran_scraping.db`

**Pasos del scheduler:**
1. Scraping con `BumeranMultiSearch`
2. Guardar CSV backup
3. Guardar en SQLite
4. Backup de BD
5. **Detectar bajas** (`database/detectar_bajas_integrado.py`)

**Estados de una oferta:**

| Estado | URL | ¿Postulable? | Detectado |
|--------|-----|--------------|-----------|
| `activa` | Funciona | Sí | Sí |
| `cerrada` | Funciona | No | **NO** |
| `baja` | 404 | No | Sí |

## ETAPA 2: LIMPIEZA DE TÍTULO

- **Archivo:** `database/limpiar_titulos.py`
- **Config:** `config/nlp_titulo_limpieza.json`

**Ejemplo:**
```
ANTES:  "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10..."
DESPUÉS: "Operarios industria ALIMENTICIA"
```

**Patrones que elimina:** Códigos internos, fechas/horarios, sucursales, prefijos, ubicaciones.

## ETAPA 3: EXTRACCIÓN NLP (IA)

- **Archivo:** `database/process_nlp_from_db_v11.py`
- **Modelo:** Qwen2.5:7b

**Campos principales:**
- Ubicación: provincia, localidad, modalidad
- Requisitos: experiencia, educación, idiomas
- Persona: sexo requerido, edad
- Trabajo: jornada, turnos, gente a cargo
- Salario: min/max, moneda
- Skills: técnicas, soft skills
- Tareas: lista de responsabilidades

## ETAPA 4: POSTPROCESSING (Correcciones)

- **Archivo:** `database/nlp_postprocessor.py`
- **Configs:** `config/nlp_*.json`

**Correcciones:**
1. **Ubicación:** Prioriza dato scraping sobre inferido
2. **Sector:** Corrige clasificaciones erróneas
3. **Merge skills:** Combina regex + LLM

## ETAPA 5: SKILLS → MATCHING (v3.2 unificado)

- **Archivo:** `database/match_ofertas_v3.py` → `match_and_persist()`

**Orden interno:**
1. `skills_implicit_extractor.py` - Extrae skills desde título + tareas
2. `match_by_skills.py` - Usa esas skills como INPUT para matching
3. `skill_categorizer.py` - Categoriza L1/L2

**Proceso:**
```
titulo_limpio + tareas
        │
        ▼
1. EXTRAER SKILLS (BGE-M3, 14,247 skills ESCO)
   └── Persiste en: ofertas_esco_skills_detalle
        │
        ▼
2. MATCHING USA SKILLS COMO INPUT
   ├── Score = 60% skills + 40% semántico título
   └── Persiste en: ofertas_esco_matching
        │
        ▼
3. Aplicar Reglas de Negocio (ver conteos en .ai/learnings.yaml)
        │
        ▼
4. Categorizar Skills (L1/L2 + es_digital)
```

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
run_scheduler.py
    │
    ▼
01_sources/bumeran/ (scraping)
    │
    ▼
database/bumeran_scraping.db ──► tabla: ofertas
    │
    ▼
database/limpiar_titulos.py
    │
    ▼
database/process_nlp_from_db_v11.py ──► tabla: ofertas_nlp
    │
    ▼
database/nlp_postprocessor.py
    │
    ▼
match_ofertas_v3.py → match_and_persist()
    │
    │   1. skills_implicit_extractor ──► ofertas_esco_skills_detalle
    │   2. match_by_skills ──► ofertas_esco_matching
    │
    ▼
Visual--/ (Dashboard R Shiny)
```

## Uso en Producción

```python
from match_ofertas_v3 import run_matching_pipeline

# Procesar todas las ofertas pendientes
run_matching_pipeline(only_pending=True, verbose=True)

# O individualmente
matcher = MatcherV3(db_conn=conn)
result = matcher.match_and_persist(id_oferta, oferta_nlp)
```

```bash
# Comando bash
python -c "from match_ofertas_v3 import run_matching_pipeline; run_matching_pipeline(only_pending=True, verbose=True)"
```
