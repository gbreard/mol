# MOL - Monitor de Ofertas Laborales

## Descripcion
Sistema de monitoreo del mercado laboral argentino para OEDE. Scrapea ofertas de empleo, extrae informacion con NLP, clasifica segun taxonomia ESCO, y provee dashboards para analistas.

## Estado Actual (2026-01-03)
- 11,001 ofertas en BD
- NLP v10.0 (153 campos, ~90% precision)
- Matching v2.1.1 BGE-M3 (100% precision Gold Set, filtros ISCO contextuales)
- Documentacion reorganizada en docs/ (current/, guides/, planning/, reference/)
- Tests organizados en tests/ (nlp/, matching/, scraping/, database/, integration/)

---

## VERSIONES ACTUALES - USAR SIEMPRE ESTAS

### NLP Pipeline

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline NLP | `database/process_nlp_from_db_v10.py` | v7, v8, v9 |
| Prompt | `02.5_nlp_extraction/prompts/extraction_prompt_v10.py` | v8, v9 |
| Schema | 153 columnas (NLP Schema v5) | schemas anteriores |
| Normalizador | `database/normalize_nlp_values.py` | - |

### Matching Pipeline v2.1.1 BGE-M3

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline Matching | `database/match_ofertas_v2.py` | match_ofertas_multicriteria.py, v8.x |
| Version | **v2.1.1** | v2.0, v8.x |
| Precision Gold Set | **100% (49/49)** | - |
| Modelo Embeddings | **BAAI/bge-m3** | - |
| Estrategia v2 | `docs/MATCHING_STRATEGY_V2.md` | - |
| Config principal | `config/matching_config.json` | valores hardcodeados |
| Config area | `config/area_funcional_esco_map.json` | - |
| Config seniority | `config/nivel_seniority_esco_map.json` | - |
| Config sector | `config/sector_isco_compatibilidad.json` | - |

### Tests

| Componente | Ubicacion |
|------------|-----------|
| Tests NLP | `tests/nlp/test_extraction.py` |
| Tests Matching | `tests/matching/test_precision.py` |
| Tests Scraping | `tests/scraping/` |
| Tests Database | `tests/database/` |
| Tests Integracion | `tests/integration/test_pipeline_completo.py` |
| Gold Set NLP | `tests/nlp/gold_set.json` (49 casos) |
| Gold Set Matching | `database/gold_set_manual_v2.json` (49 casos) |

**Ejecutar tests:**
```bash
python -m pytest tests/ -v
```

### Configuracion

| Archivo | Proposito |
|---------|-----------|
| `config/matching_config.json` | Config principal matching v2 (pesos, umbrales, penalizaciones) |
| `config/area_funcional_esco_map.json` | Mapeo area_funcional → codigos ISCO |
| `config/nivel_seniority_esco_map.json` | Mapeo seniority → ISCO + matriz penalizacion |
| `config/sector_isco_compatibilidad.json` | Compatibilidad sector empresa ↔ ISCO |

### Diccionarios de Extraccion

| Archivo | Proposito | Items |
|---------|-----------|-------|
| `config/skills_database.json` | Skills tecnicas, LATAM, logistica, contables | ~320 |
| `config/oficios_arg.json` | Oficios y ocupaciones argentinas | ~170 |
| `config/nlp_preprocessing.json` | Preprocesamiento ubicacion | - |
| `config/nlp_validation.json` | Validacion tipos (rechazo booleanos) | - |
| `config/nlp_extraction_patterns.json` | Patterns regex experiencia | - |
| `config/nlp_inference_rules.json` | Inferencia modalidad/seniority/area | - |
| `config/nlp_defaults.json` | Valores default campos | - |
| `config/nlp_normalization.json` | Normalizacion provincias (CABA) | - |

**Agregar nuevas skills:**
```python
# Editar config/skills_database.json, categoria correspondiente
# NO hardcodear en codigo Python
# Categorias disponibles: lenguajes_programacion, frameworks_web, bases_datos,
# cloud_devops, plataformas_latam, skills_logistica, skills_contables,
# skills_operativas_retail, skills_gastronomia, certificaciones_arg
```

---

## Regla de Versionado de Componentes

**OBLIGATORIO:** Cuando se crea una nueva version de cualquier componente:

### Paso 1: Crear nueva version
```bash
# Ejemplo: match_ofertas_v2.py, process_nlp_v11.py
```

### Paso 2: INMEDIATAMENTE archivar la version anterior

| Tipo de componente | Mover a |
|--------------------|---------|
| Matching (match_*.py) | database/archive_old_versions/matching/ |
| NLP processors (process_nlp_*.py) | database/archive_old_versions/nlp_processors/ |
| Regex patterns (regex_patterns_*.py) | archive/patterns_old/ |
| Prompts (extraction_prompt_*.py) | archive/prompts_old/ |
| Extractors | archive/extractors_old/ |
| Scripts one-time (fix_*, debug_*) | archive/scripts_historical/ |

### Paso 3: Verificar que nada importe el archivo archivado
```bash
grep -rn "from archivo_viejo import" --include="*.py" .
grep -rn "import archivo_viejo" --include="*.py" .
```

### Paso 4: Actualizar CLAUDE.md
- Cambiar version en tabla de componentes
- Agregar al CHANGELOG si es cambio significativo

### REGLA ESTRICTA
NUNCA dejar dos versiones del mismo componente activas en el mismo directorio.
Si existe `component_v8.py` y creas `component_v9.py`, el v8 debe archivarse en el mismo commit.

### Ejemplo de commit correcto
```
feat: NLP v11 con nuevo campo X

- Crear database/process_nlp_from_db_v11.py
- Archivar database/process_nlp_from_db_v10.py -> archive_old_versions/nlp_processors/
- Actualizar CLAUDE.md
```

---

## ARCHIVOS DEPRECADOS - NO USAR

Los siguientes archivos estan en `database/archive_old_versions/` y NO deben usarse:

**NLP:**
- `process_nlp_from_db_v*.py` (v1-v9) → usar v10
- `extraction_prompt_v*.py` (v1-v9) → usar v10

**Matching:**
- `matching_rules_v*.py` (v81-v84) → archivados, usar match_ofertas_v2.py
- `match_ofertas_multicriteria.py` → archivado, usar match_ofertas_v2.py
- Scripts de matching antiguos

**Tests sueltos:**
- Cualquier `check_*.py`, `debug_*.py`, `test_*.py` fuera de `tests/`

Ver `database/archive_old_versions/DEPRECATED.md` para lista completa.

---

## Documentacion

La documentacion esta organizada en `docs/`:

| Carpeta | Contenido |
|---------|-----------|
| `docs/current/` | Documentos activos y actualizados |
| `docs/guides/` | Guias de uso (quickstart, flujos) |
| `docs/planning/` | Planificacion, issues Linear |
| `docs/reference/` | Referencia tecnica, APIs |
| `docs/archive/` | Documentos historicos |

**Documentos clave:**
| Documento | Descripcion |
|-----------|-------------|
| `docs/current/MOL_CONTEXT_MASTER.md` | Contexto completo del sistema |
| `docs/current/NLP_SCHEMA_V5.md` | Schema de 153 campos NLP |
| `docs/current/MATCHING_STRATEGY_V2.md` | Estrategia Matching v2.1.1 |
| `docs/current/CHANGELOG.md` | Historial de cambios |
| `docs/planning/MOL_LINEAR_ISSUES_V3.md` | Issues con specs detalladas |
| `docs/guides/QUICKSTART_BUMERAN.md` | Inicio rapido scraping |

## Comandos Clave

```bash
# Scraping (SIEMPRE usar este, NUNCA bumeran_scraper.py directo)
python run_scheduler.py --test

# Test Matching
python database/test_gold_set_manual.py

# Dashboard Admin (cuando este creado)
streamlit run dashboards/admin/app.py

# Linear - Sincronizar cache
python scripts/linear_sync.py

# Linear - Actualizar issue (no bloqueante)
python scripts/linear_update_async.py MOL-XX --status=done --comment="..."
```

## Modelos LLM/ML Activos

| Modelo | Tipo | Uso |
|--------|------|-----|
| **Qwen2.5:14b** | LLM | NLP: extraccion semantica (30% campos) |
| **BGE-M3** | Embeddings | Matching: titulo (50%) + descripcion (10%) |
| **ESCO-XLM-RoBERTa-Large** | Re-ranker | Re-ranking candidatos ESCO |
| **ChromaDB** | Vector DB | Skills lookup (40%) |

**Requisitos:**
- Ollama en `localhost:11434` con `qwen2.5:14b`
- ChromaDB con vectores en `database/esco_vectors/`
- `sentence-transformers` para BGE-M3
- `transformers` para ESCO-XLM-RoBERTa

**Pipeline NLP:** Regex (70%) -> Qwen2.5 (30%) -> Anti-alucinacion
**Pipeline Matching:** Titulo (50%) -> Skills (40%) -> Descripcion (10%) -> Validacion

## Linear (Sistema No Bloqueante)

### Configuracion inicial (1x)
1. Crear `config/linear_config.json` con tu API key
2. Ejecutar: `python scripts/linear_sync.py`

### Flujo de trabajo

**INICIO DE SESION:**
```bash
python scripts/linear_sync.py
# Sincroniza issues de Linear a .linear/issues.json
```

**LEER CONTEXTO DE UN ISSUE:**
- Leer specs de `docs/MOL_LINEAR_ISSUES_V3.md`
- Leer estado de `.linear/issues.json`
- NUNCA usar MCP de Linear (bloquea)

**ACTUALIZAR ISSUE (no bloqueante):**
```bash
python scripts/linear_update_async.py MOL-XX --status=done --comment="Completado"
# Retorna inmediato, Linear se actualiza en background
```

**MULTIPLES UPDATES:**
```bash
python scripts/linear_queue.py add MOL-31 --status=done
python scripts/linear_queue.py add MOL-32 --status=done
python scripts/linear_queue.py process  # Al final de la sesion
```

## Reglas de Desarrollo

1. **Scraping:** SIEMPRE usar `run_scheduler.py`, NUNCA `bumeran_scraper.py` directo
2. **Tests:** Todo cambio en NLP/Matching debe pasar gold set
3. **Umbrales:** NLP >= 90%, Matching >= 95%
4. **S3:** Experimentos van a `/experiment/`, produccion a `/production/`
5. **UI:** Dashboard produccion SIN siglas tecnicas (CIUO, ESCO)
6. **Linear:** Usar sistema de cache, NUNCA MCP directo

## Convenciones del Proyecto

### Estructura de Codigo

| Tipo de archivo | Ubicacion | Ejemplo |
|-----------------|-----------|---------|
| Tests pytest | `tests/` | `tests/nlp/test_extraction.py` |
| Migraciones BD | `database/migrations/` | `001_initial.sql` |
| Prompts LLM | `02.5_nlp_extraction/prompts/` | `extraction_prompt_v9.py` |
| Configuracion | `config/` | `matching_config.json` |
| Scripts one-time | `scripts/` | `fix_descripcion_nulls.py` |
| Archivos obsoletos | `database/archive_old_versions/` | Versiones antiguas |

### Tests

- **SIEMPRE** crear tests en `tests/`, nunca en `database/` u otras carpetas
- Estructura: `tests/{modulo}/test_{funcionalidad}.py`
- Gold sets van en `tests/{modulo}/gold_set.json` o `database/gold_set_*.json`
- Usar pytest: `python -m pytest tests/ -v`
- Fixtures compartidos: `tests/conftest.py`

### Versionado de Archivos

| Componente | Patron | Version ACTIVA |
|------------|--------|----------------|
| Prompts | `extraction_prompt_v{N}.py` | **v10** |
| Procesos NLP | `process_nlp_from_db_v{N}.py` | **v10** |
| Matching Rules | `matching_rules_v{NN}.py` | **v84** |
| Configs | Campo `"version"` interno | matching_config v2.0 |

### Scripts Temporales

- Si es debugging/one-time -> crear en `scripts/` con fecha: `2025-12-09_fix_xyz.py`
- Si es test -> crear en `tests/`
- **NUNCA** crear `check_*.py`, `debug_*.py` o `test_*.py` sueltos en `database/`
- Scripts obsoletos -> mover a `database/archive_old_versions/`

### Gold Sets

| Gold Set | Ubicacion | Casos |
|----------|-----------|-------|
| Matching ESCO | `database/gold_set_manual_v2.json` | 49 casos |
| NLP Extraction | `tests/nlp/gold_set.json` | 20+ casos |

### Commits

- Usar conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Incluir issue Linear si aplica: `feat(MOL-XX): descripcion`

---

## Metodología Git Colaborativa

### Estructura de Ramas

```
main (producción estable - PROTEGIDA)
  │
  ├── visualizacion (Sergio - Fase 3: Dashboard)
  │     ├── feat/fase3-setup-repo
  │     ├── feat/fase3-supabase
  │     └── ...
  │
  └── desarrollo (Otro dev - Fase 1-2: Scraping/NLP)
        ├── feat/fase1-zonajobs
        ├── fix/fase2-nlp-bug
        └── ...
```

### Roles y Áreas

| Dev | Rama Base | Área | Carpetas |
|-----|-----------|------|----------|
| Sergio | `visualizacion` | Fase 3: Dashboard | `dashboards/`, `fase3_dashboard/` |
| Otro dev | `desarrollo` | Fase 1-2: Scraping/NLP | `01_sources/`, `database/`, `02.5_nlp_extraction/` |

### Flujo de Trabajo Diario

```bash
# 1. Actualizar main
git checkout main && git pull origin main

# 2. Actualizar tu rama base desde main
git checkout visualizacion && git merge main

# 3. Crear rama para la tarea
git checkout -b feat/fase3-nombre-tarea

# 4. Trabajar y commitear
git add . && git commit -m "feat(fase3): descripción"

# 5. Push
git push -u origin feat/fase3-nombre-tarea

# 6. Crear PR hacia tu rama base
gh pr create --base visualizacion --title "feat(fase3): título" --body "Closes #XX"

# 7. Después de aprobar, merge
gh pr merge --squash
```

### Ciclo de Releases

```
Trabajo diario:
  visualizacion ←── feat/fase3-xxx (PRs frecuentes)
  desarrollo    ←── feat/fase1-xxx (PRs frecuentes)

Fin de Sprint (semanal):
  1. desarrollo → main (PR, review cruzado)
  2. visualizacion → main (PR, review cruzado)
```

### Reglas de Oro

| Regla | Motivo |
|-------|--------|
| Nunca push directo a `main` | main es producción estable |
| Nunca push a rama del otro | Evita conflictos y sorpresas |
| PRs para todo | Historial claro, code review |
| Sync con main antes de PR grande | Evita conflictos al mergear |
| Coordinar archivos compartidos | `CLAUDE.md`, `config/`, `requirements.txt` |

### Archivos Compartidos (Coordinar)

```
CLAUDE.md              → Cada uno edita su sección
config/*.json          → Avisar antes de modificar
requirements.txt       → Coordinar dependencias
.gitignore             → Coordinar
```

### Convención de Ramas

```
feat/fase{N}-xxx       → Nueva funcionalidad
fix/fase{N}-xxx        → Bug fix
chore/fase{N}-xxx      → Mantenimiento
docs/xxx               → Documentación
```

### Resolver Conflictos

```bash
# 1. Ver archivos en conflicto
git status

# 2. Editar archivo, buscar marcadores:
<<<<<<< HEAD
tu código
=======
código del otro
>>>>>>> main

# 3. Resolver, guardar, continuar
git add archivo.py
git commit -m "fix: resolver conflicto en archivo"
```

### Configuración Inicial GitHub

1. **Proteger main:**
   ```
   Settings → Branches → Add rule → main
   ✅ Require pull request before merging
   ✅ Require approvals: 1
   ```

2. **Agregar colaborador:**
   ```
   Settings → Collaborators → Add people
   ```

---

## Dashboard R Shiny (Produccion)

El dashboard R Shiny esta en `Visual--/` y **esta en produccion**.

| Componente | Ubicacion |
|------------|-----------|
| App principal | `Visual--/app.R` |
| Documentacion | `Visual--/docs/` |
| Deploy config | `Visual--/rsconnect/` |
| Datos CSV | `Visual--/ofertas_esco_*.csv` |

**NO modificar Visual--/** sin coordinacion con el equipo.

---

## Estructura del Proyecto

```
MOL/
├── 01_sources/bumeran/scrapers/    # Scrapers
├── 02.5_nlp_extraction/            # Pipeline NLP
├── database/                        # BD principal, matching, NLP processors
├── data/tracking/                  # IDs vistos
├── Visual--/                       # Dashboard R Shiny (PRODUCCION)
├── dashboards/                     # Dashboards nuevos
│   ├── admin/                      # Streamlit (por crear)
│   ├── optimization/               # Next.js Vercel (por crear)
│   └── production/                 # Next.js Vercel (por crear)
├── tests/                          # Tests pytest
│   ├── nlp/                        # Tests NLP
│   ├── matching/                   # Tests matching
│   ├── scraping/                   # Tests scraping
│   ├── database/                   # Tests BD
│   └── integration/                # Tests E2E
├── scripts/                        # Utilidades
│   ├── db/                         # Scripts BD (check_db, etc.)
│   ├── analysis/                   # Analisis de datos
│   ├── exploration/                # Investigacion APIs
│   ├── windows/                    # Scripts .ps1/.bat Windows
│   └── linear_*.py                 # Integracion Linear
├── config/                         # Configuracion JSON
├── docs/                           # Documentacion organizada
│   ├── current/                    # Docs activos
│   ├── guides/                     # Guias de uso
│   ├── planning/                   # Planificacion
│   ├── reference/                  # Referencia tecnica
│   └── archive/                    # Historico
├── archive/                        # Archivos historicos
│   ├── dashboards_old/             # Dashboard v1-v3 archivados
│   └── legacy_dashboard_oct2024/   # Dashboard R antiguo
├── backups/                        # Backups BD
├── logs/                           # Logs del sistema
├── exports/                        # Exportaciones
├── .linear/                        # Cache de Linear (no commitear)
├── run_scheduler.py                # PUNTO DE ENTRADA SCRAPING
├── dashboard_scraping_v4.py        # Dashboard Dash (en transicion)
└── CLAUDE.md                       # Este archivo
```

## Arquitectura del Pipeline

### Pipeline ACTUAL (1 portal - Bumeran)

```
run_scheduler.py
    |
    v
01_sources/bumeran/ (scraping)
    |
    v
database/bumeran_scraping.db
    |
    v
database/process_nlp_from_db_v10.py (NLP)
    |
    v
database/match_ofertas_v2.py (Matching)
    |
    v
Visual--/ (Dashboard R Shiny)
```

### Pipeline FUTURO (5 portales)

```
01_sources/* (Bumeran, ZonaJobs, Computrabajo, LinkedIn, Indeed)
    |
    v
02_consolidation/ (merge multi-fuente)
    |
    v
02.5_nlp_extraction/ (NLP modular)
    |
    v
03_esco_matching/ (matching modular)
    |
    v
04_analysis/ (analisis automatizado)
    |
    v
05_products/ (exports finales)
```

### Estado de Carpetas Numeradas

| Carpeta | Estado | Cuando se usa |
|---------|--------|---------------|
| `01_sources/` | ACTIVO | Ahora (Bumeran) |
| `02_consolidation/` | RESERVADO | Con 2+ portales |
| `02.5_nlp_extraction/` | PARCIAL | Solo prompts usados |
| `03_esco_matching/` | LEGACY | Codigo en database/ |
| `04_analysis/` | RESERVADO | Post-produccion |
| `05_products/` | PLACEHOLDER | Post-produccion |

> **Nota**: Ver STATUS.md en cada carpeta para detalles.

## Carpetas de Soporte

| Carpeta | Proposito | Documentacion |
|---------|-----------|---------------|
| `backups/` | Backups de BD y datos historicos | backups/README.md |
| `exports/` | Gold sets y exports Excel | exports/README.md |
| `logs/` | Logs del scheduler | logs/README.md |
| `metrics/` | Tracking de experimentos | metrics/README.md |

### Dashboards (aclaracion)

| Carpeta | Proposito | Estado |
|---------|-----------|--------|
| `dashboard/` | Modulo Python de utilidades (data_loaders, components) | ACTIVO |
| `dashboards/` | Ubicacion para nuevos dashboards (admin/, optimization/) | RESERVADO |
| `Visual--/` | Dashboard R Shiny produccion | PRODUCCION |

> **Nota**: `dashboard/` es un paquete Python usado por `dashboard_scraping_v4.py`, NO es un dashboard de usuario.

---

## FASE 3: Dashboard Next.js (EN DESARROLLO)

### Estado Actual (2026-01-21)

**Rama:** `visualizacion`

**Decisión:** Migrar desde `mol-nextjs` (repo externo) e integrar conexión Supabase.

### Repositorios

| Repo | Ubicación | Estado |
|------|-----------|--------|
| **mol-nextjs** | https://github.com/sergiandat/mol-nextjs.git | UI completa, datos mock |
| **fase3_dashboard** | `fase3_dashboard/mol-dashboard/` | Supabase conectado, UI básica |

### Arquitectura Objetivo

```
dashboards/production/          # <- Destino final
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx            # Panorama General
│   │   ├── requerimientos/     # Skills y competencias
│   │   └── ofertas/            # Tabla de ofertas
│   ├── components/
│   │   ├── ui/                 # 46 componentes Radix UI (de mol-nextjs)
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx         # Filtros verticales
│   │   └── charts/             # Gráficos Recharts
│   └── lib/
│       └── supabase.ts         # Cliente Supabase
├── .env.local                  # Credenciales Supabase
└── package.json
```

### Plan de Integración

#### Paso 1: Clonar mol-nextjs en MOL
```bash
cd C:\Users\Sergio\Documents\MOL
git clone https://github.com/sergiandat/mol-nextjs.git dashboards/production
```

#### Paso 2: Copiar integración Supabase
```bash
# Copiar cliente Supabase
cp fase3_dashboard/mol-dashboard/src/lib/supabase.ts dashboards/production/lib/

# Copiar SQL migrations
cp -r fase3_dashboard/sql/ dashboards/production/sql/
```

#### Paso 3: Configurar variables de entorno
Crear `dashboards/production/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
```

#### Paso 4: Reemplazar mock data con Supabase
- [x] `PanoramaGeneral.tsx` → usar `getKPIs()`, `getTopOcupaciones()`
- [x] `Requerimientos.tsx` → crear queries para skills
- [x] `OfertasLaborales.tsx` → usar `getOfertas()` con paginación
- [x] `Sidebar.tsx` → conectar filtros a queries

#### Paso 5: Archivar dashboard anterior (COMPLETADO)
```bash
mv fase3_dashboard/ archive/dashboards_old/fase3_dashboard_v1/
```

### Schema Supabase (Producción)

#### Tablas Principales

| Tabla | Propósito | Uso Dashboard |
|-------|-----------|---------------|
| `ofertas` | Datos completos NLP/Matching (153 campos) | Backend, sync |
| `ofertas_dashboard` | Vista simplificada para UI | **Principal** |
| `ofertas_skills` | Skills por oferta (normalizado) | Gráficos skills |
| `esco_occupations` | Catálogo ocupaciones ESCO | Filtros, labels |
| `esco_skills` | Catálogo skills ESCO | Filtros, categorías |
| `usuarios` | Usuarios del sistema | Auth |
| `organizaciones` | Orgs (OEDE, universidades, etc.) | Multi-tenant |
| `alertas` | Alertas configuradas por usuario | Feature futuro |
| `busquedas_guardadas` | Búsquedas guardadas | Feature futuro |
| `intereses` | Intereses de usuarios | Feature futuro |
| `metricas_plataforma` | KPIs diarios agregados | Dashboard admin |
| `sistema_estado` | Estado sync entre fases | Dashboard admin |
| `eventos_uso` | Tracking de uso | Analytics |
| `sesiones_usuario` | Sesiones de usuarios | Analytics |

#### Tabla: ofertas_dashboard (Principal UI)

```sql
CREATE TABLE ofertas_dashboard (
  id_oferta TEXT PRIMARY KEY,
  titulo TEXT NOT NULL,
  empresa TEXT,
  fecha_publicacion DATE,
  url TEXT,
  portal TEXT,
  provincia TEXT,
  localidad TEXT,
  isco_code TEXT,
  isco_label TEXT,
  occupation_match_score REAL,
  occupation_match_method TEXT,
  modalidad TEXT,                    -- remoto/hibrido/presencial
  nivel_seniority TEXT,              -- junior/semi-senior/senior/manager
  area_funcional TEXT,
  sector_empresa TEXT,
  salario_min INTEGER,
  salario_max INTEGER,
  moneda TEXT DEFAULT 'ARS',
  skills_tecnicas JSONB,             -- array de skills
  soft_skills JSONB,                 -- array de soft skills
  estado TEXT DEFAULT 'activa',      -- activa/cerrada
  fecha_sync TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla: ofertas_skills (Skills Normalizados)

```sql
CREATE TABLE ofertas_skills (
  id SERIAL PRIMARY KEY,
  id_oferta TEXT REFERENCES ofertas(id_oferta),
  skill_mencionado TEXT,             -- skill como aparece en oferta
  skill_tipo_fuente TEXT,            -- tecnica/soft/herramienta
  esco_skill_uri TEXT,               -- URI ESCO matcheado
  esco_skill_label TEXT,             -- label ESCO
  match_score NUMERIC,
  skill_type TEXT,                   -- skill/knowledge/competence
  l1 TEXT,                           -- categoría nivel 1
  l1_nombre TEXT,
  l2 TEXT,                           -- categoría nivel 2
  l2_nombre TEXT,
  es_digital BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla: esco_skills (Catálogo)

```sql
CREATE TABLE esco_skills (
  uri TEXT PRIMARY KEY,
  label TEXT,
  skill_type TEXT,                   -- skill/knowledge/competence
  l1 TEXT,                           -- categoría nivel 1
  l1_nombre TEXT,
  l2 TEXT,                           -- categoría nivel 2
  l2_nombre TEXT,
  es_digital BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla: metricas_plataforma (KPIs Diarios)

```sql
CREATE TABLE metricas_plataforma (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fecha DATE NOT NULL UNIQUE,
  ofertas_scrapeadas_total INTEGER,
  ofertas_scrapeadas_dia INTEGER,
  ofertas_activas INTEGER,
  ofertas_cerradas INTEGER,
  ofertas_con_nlp INTEGER,
  ofertas_con_matching INTEGER,
  ofertas_validadas INTEGER,
  usuarios_activos_dia INTEGER,
  usuarios_activos_semana INTEGER,
  usuarios_activos_mes INTEGER,
  busquedas_realizadas INTEGER,
  descargas_csv INTEGER,
  alertas_activas INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla: usuarios

```sql
CREATE TABLE usuarios (
  id UUID PRIMARY KEY,               -- viene de Supabase Auth
  organizacion_id UUID REFERENCES organizaciones(id),
  nombre TEXT NOT NULL,
  apellido TEXT NOT NULL,
  email TEXT NOT NULL,
  rol TEXT DEFAULT 'analista',       -- platform_admin/admin/analista/lector
  activo BOOLEAN DEFAULT TRUE,
  ultimo_acceso TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Queries para Dashboard

```typescript
// KPIs globales
const { data } = await supabase
  .from('ofertas_dashboard')
  .select('id_oferta, isco_code, empresa, provincia', { count: 'exact' })

// Top ocupaciones
const { data } = await supabase
  .from('ofertas_dashboard')
  .select('isco_code, isco_label')
  .not('isco_code', 'is', null)
  // agrupar en cliente o usar vista SQL

// Top skills (desde tabla normalizada)
const { data } = await supabase
  .from('ofertas_skills')
  .select('esco_skill_label, l1_nombre, es_digital')
  .not('esco_skill_uri', 'is', null)

// Evolución temporal (desde métricas)
const { data } = await supabase
  .from('metricas_plataforma')
  .select('fecha, ofertas_activas, ofertas_con_matching')
  .order('fecha', { ascending: true })
  .limit(30)

// Ofertas paginadas con filtros
const { data } = await supabase
  .from('ofertas_dashboard')
  .select('*')
  .eq('provincia', provincia)
  .eq('modalidad', modalidad)
  .range(offset, offset + limit - 1)
```

### Stack Tecnológico

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Next.js | 16.1.x | Framework React |
| React | 19.2.x | UI Library |
| Tailwind CSS | 4.x | Estilos |
| Radix UI | latest | Componentes accesibles |
| Recharts | 2.15.x | Gráficos |
| Supabase JS | 2.90.x | Backend PostgreSQL |
| TypeScript | 5.x | Tipado |

### Comandos Desarrollo

```bash
# Instalar dependencias
cd dashboards/production && npm install

# Desarrollo local
npm run dev  # http://localhost:3000

# Build producción
npm run build

# Deploy (cuando esté listo)
vercel deploy
```

### Checklist Fase 3

- [x] Análisis de mol-nextjs (UI components)
- [x] Análisis de fase3_dashboard (Supabase)
- [x] Clonar mol-nextjs a dashboards/production/
- [x] Integrar cliente Supabase
- [x] Configurar .env.local
- [x] Reemplazar mock data en PanoramaGeneral
- [x] Reemplazar mock data en Requerimientos
- [x] Reemplazar mock data en OfertasLaborales
- [x] Conectar filtros del Sidebar
- [x] Testing local completo (build exitoso)
- [x] Archivar fase3_dashboard anterior
- [ ] Deploy a Vercel (pendiente)

---

## Epicas Activas

| Epica | Prioridad | Descripcion |
|-------|-----------|-------------|
| 1. Scraping | Alta | Dashboard tab, ZonaJobs, deduplicacion |
| 2. NLP | Alta | Gold set 200+, tests, export S3 |
| 3. Matching | Alta | sector_funcion v8.4, gold set 200+ |
| 4. Validacion | Alta | Tests tab, S3 sync, sampling |
| 5. Dashboards | Media | Admin, Validacion, Produccion |
| 6. Infraestructura | Baja | Logs, alertas, CI/CD |

## Metricas Objetivo

| Metrica | Actual | Objetivo |
|---------|--------|----------|
| Precision NLP | ~90% | >= 90% |
| Precision Matching | **100%** | >= 95% |
| Gold Set NLP | 0 | 200+ |
| Gold Set Matching | **49** | 200+ |
| Portales | 1 | 5 |

---

> **Ultima actualizacion:** 2026-01-21

---

## AI Platform Local

Este proyecto usa la plataforma de IA local en `D:\AI_Platform`.

### Antes de cualquier tarea de IA

1. **Leer aprendizajes globales:** `D:\AI_Platform\learnings\global.yaml`
2. **Leer aprendizajes del proyecto:** `.ai/learnings.yaml`
3. **Aplicar lo aprendido** antes de decidir modelo o enfoque

### Conexión

```python
import httpx
GATEWAY = "http://localhost:8080"
```

### Endpoints disponibles

| Endpoint | Descripción |
|----------|-------------|
| `POST /v1/chat/completions` | LLM (modelos: fast, smart, reasoning, agent) |
| `POST /v1/embeddings` | Embeddings (e5-large, bge-m3) |
| `POST /v1/ocr` | OCR de imágenes/PDFs |
| `POST /v1/parse/legal` | Parser documentos legales |
| `POST /v1/parse/job` | Parser ofertas laborales |
| `POST /v1/rag/query` | RAG completo |
| `POST /v1/transcribe` | Audio a texto |
| `POST /v1/rerank` | Reordenar por relevancia |

### Verificar servicios

```python
response = httpx.get("http://localhost:8080/health")
```

### Documentación

- Swagger UI: http://localhost:8080/docs
- Monitor: http://localhost:8501
- Guía completa: `D:\AI_Platform\CLAUDE.md`

### Cuando descubras algo útil

- Aplica a ESTE proyecto → Agregar a `.ai/learnings.yaml`
- Aplica a TODOS → Agregar a `D:\AI_Platform\learnings\global.yaml`
