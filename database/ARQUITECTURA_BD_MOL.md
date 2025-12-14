# Arquitectura Base de Datos MOL

> **Base de datos:** `bumeran_scraping.db`
> **Motor:** SQLite 3
> **Generado:** 2025-12-09
> **Total tablas:** 38
> **Total registros:** ~212,000

---

## 1. Modelo de Datos

### 1.1 Dominios Principales

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARQUITECTURA MOL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   SCRAPING   │───▶│   OFERTAS    │───▶│     NLP      │                  │
│   │   (fuentes)  │    │   (core)     │    │  (extracción)│                  │
│   └──────────────┘    └──────┬───────┘    └──────────────┘                  │
│                              │                                               │
│                              ▼                                               │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │    ESCO      │◀───│   MATCHING   │───▶│  VALIDACIÓN  │                  │
│   │  (taxonomía) │    │  (ocupación) │    │   (calidad)  │                  │
│   └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tablas por Dominio

### 2.1 DOMINIO: Ofertas Laborales (Core)

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `ofertas` | 9,564 | Ofertas laborales scrapeadas (tabla principal) |
| `ofertas_raw` | 1,078 | Ofertas en formato JSON crudo |
| `ofertas_historial` | 0 | Historial de cambios en ofertas |

**Tabla `ofertas` - Esquema Principal:**
```sql
ofertas (49 columnas)
├── id_oferta           INTEGER PK    -- ID único de la oferta
├── titulo              TEXT NOT NULL -- Título del puesto
├── empresa             TEXT          -- Nombre de la empresa
├── descripcion         TEXT          -- Descripción completa
├── localizacion        TEXT          -- Ubicación geográfica
├── modalidad_trabajo   TEXT          -- Presencial/remoto/híbrido
├── fecha_publicacion_iso TEXT        -- Fecha ISO normalizada
├── portal              TEXT          -- Portal fuente (bumeran, zonajobs, etc.)
├── provincia_normalizada TEXT        -- Provincia INDEC normalizada
├── codigo_provincia_indec TEXT       -- Código INDEC de provincia
├── estado_oferta       TEXT          -- activa/baja/pausada
├── fecha_baja          TEXT          -- Fecha de baja detectada
├── dias_publicada      INTEGER       -- Días de permanencia
└── ...
```

### 2.2 DOMINIO: Procesamiento NLP

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `ofertas_nlp` | 5,479 | Datos extraídos por NLP (versión activa) |
| `ofertas_nlp_v2` | 0 | Nueva versión de extracción NLP |
| `ofertas_nlp_history` | 0 | Historial de extracciones |
| `nlp_versions` | 4 | Versiones del modelo NLP |

**Tabla `ofertas_nlp` - Extracción Estructurada:**
```sql
ofertas_nlp (28 columnas)
├── id_oferta             TEXT PK      -- FK a ofertas
├── experiencia_min_anios INTEGER      -- Años mínimos requeridos
├── experiencia_max_anios INTEGER      -- Años máximos
├── nivel_educativo       TEXT         -- Secundario/universitario/etc.
├── idioma_principal      TEXT         -- Idioma requerido
├── skills_tecnicas_list  TEXT (JSON)  -- Lista de skills técnicas
├── soft_skills_list      TEXT (JSON)  -- Habilidades blandas
├── salario_min           REAL         -- Salario mínimo
├── salario_max           REAL         -- Salario máximo
├── nlp_version           TEXT         -- Versión del modelo usado
├── confianza_extraccion  REAL         -- Score de confianza
└── ...
```

### 2.3 DOMINIO: Taxonomía ESCO

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `esco_occupations` | 3,045 | Ocupaciones ESCO v1.2 en español |
| `esco_skills` | 14,247 | Skills/competencias ESCO |
| `esco_associations` | 134,805 | Relaciones ocupación-skill |
| `esco_occupation_alternative_labels` | 13,796 | Labels alternativos de ocupaciones |
| `esco_skill_alternative_labels` | 20,422 | Labels alternativos de skills |
| `esco_isco_hierarchy` | 619 | Jerarquía ISCO-08 |
| `esco_occupation_ancestors` | 0 | Ancestros jerárquicos |
| `esco_occupation_gendered_terms` | 0 | Términos con género |

**Tabla `esco_occupations` - Ocupaciones:**
```sql
esco_occupations (16 columnas)
├── occupation_uri        TEXT PK      -- URI única ESCO
├── occupation_uuid       TEXT UNIQUE  -- UUID interno
├── esco_code            TEXT          -- Código ESCO (ej: "C1221")
├── isco_code            TEXT          -- Código ISCO-08 (ej: "1221")
├── preferred_label_es   TEXT NOT NULL -- Nombre preferido en español
├── description_es       TEXT          -- Descripción en español
├── broader_occupation_uri TEXT        -- Ocupación padre (FK recursiva)
├── hierarchy_level      INTEGER       -- Nivel en jerarquía
└── ...

INDICES:
  - idx_esco_occ_isco: isco_code
  - idx_esco_occ_label: preferred_label_es
  - idx_esco_occ_broader: broader_occupation_uri
```

**Tabla `esco_skills` - Competencias:**
```sql
esco_skills (12 columnas)
├── skill_uri             TEXT PK      -- URI única ESCO
├── preferred_label_es    TEXT NOT NULL-- Nombre en español
├── skill_type           TEXT          -- skill/knowledge/attitude
├── skill_reusability_level TEXT       -- transversal/cross-sector/sector-specific
├── skill_category       TEXT          -- Categoría agregada
└── ...
```

### 2.4 DOMINIO: Matching Ocupacional

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `ofertas_esco_matching` | 6,621 | Matches oferta→ocupación ESCO |
| `ofertas_esco_skills_detalle` | 1,315 | Detalle de skills matcheados |
| `diccionario_arg_esco` | 267 | Diccionario argentino→ESCO |
| `sinonimos_regionales` | 0 | Sinónimos regionales |
| `cno_ocupaciones` | 0 | Clasificador Nacional de Ocupaciones |
| `cno_esco_matches` | 0 | Matches CNO→ESCO |

**Tabla `ofertas_esco_matching` - Core del Matching:**
```sql
ofertas_esco_matching (30 columnas)
├── id_oferta             TEXT PK      -- FK a ofertas
├── esco_occupation_uri   TEXT         -- FK a esco_occupations
├── esco_occupation_label TEXT         -- Label de la ocupación asignada
├── occupation_match_score REAL        -- Score del match (0-1)
├── occupation_match_method TEXT       -- Método: diccionario/embedding/hybrid
├── titulo_normalizado    TEXT         -- Título preprocesado
├── isco_code            TEXT          -- Código ISCO asignado
├── score_titulo         REAL          -- Score por título
├── score_skills         REAL          -- Score por skills
├── score_descripcion    REAL          -- Score por descripción
├── score_final_ponderado REAL         -- Score final combinado
├── confidence_score     REAL          -- Confianza del match
├── match_confirmado     INTEGER       -- Validado manualmente (0/1)
├── requiere_revision    INTEGER       -- Marcado para revisión
└── ...

INDICES:
  - idx_ofertas_esco_occ: esco_occupation_uri
  - idx_ofertas_esco_score: occupation_match_score
  - idx_ofertas_esco_confidence: confidence_score

FOREIGN KEYS:
  - id_oferta → ofertas.id_oferta
  - esco_occupation_uri → esco_occupations.occupation_uri
```

**Tabla `diccionario_arg_esco` - Bypass Diccionario:**
```sql
diccionario_arg_esco (6 columnas)
├── id                    INTEGER PK
├── termino_argentino     TEXT UNIQUE  -- Término local (ej: "repositor")
├── esco_preferred_label  TEXT         -- Label ESCO exacto
├── isco_target          TEXT          -- Código ISCO (ej: "C9334")
├── esco_terms_json      TEXT          -- Terms JSON para embedding
└── notes                TEXT          -- Notas

USO:
  - Bypass de búsqueda semántica para términos argentinos
  - Requiere coincidencia EXACTA con preferred_label_es en esco_occupations
```

### 2.5 DOMINIO: Validación y Calidad

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `validacion_pipeline` | 0 | Métricas del pipeline |
| `validacion_humana` | 0 | Validaciones manuales |
| `validacion_campos` | 0 | Validación de campos |
| `validacion_incremental` | 0 | Validación incremental |
| `validacion_v7` | 0 | Validación versión 7 |

### 2.6 DOMINIO: Scraping y Monitoreo

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `scraping_sessions` | 0 | Sesiones de scraping |
| `metricas_scraping` | 2 | Métricas agregadas |
| `keywords_performance` | 2,296 | Performance de keywords |
| `keywords_performance_v2` | 0 | Nueva versión de métricas |
| `alertas` | 5 | Alertas del sistema |
| `circuit_breaker_stats` | 0 | Stats del circuit breaker |
| `rate_limiter_stats` | 0 | Stats del rate limiter |

### 2.7 DOMINIO: Auxiliares

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `indec_provincias` | 24 | Provincias argentinas (INDEC) |
| `skills` | 0 | Skills genéricas (deprecated?) |
| `ofertas_skills` | 0 | Relación oferta-skill (deprecated?) |
| `schema_migrations` | 0 | Migraciones de schema |
| `sqlite_sequence` | 20 | Secuencias SQLite (interno) |

---

## 3. Diagrama Entidad-Relación

```
                                    ┌─────────────────────┐
                                    │   esco_occupations  │
                                    │   (3,045 registros) │
                                    └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
    ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
    │ esco_occupation_      │   │   esco_associations   │   │ diccionario_arg_esco  │
    │ alternative_labels    │   │  (134,805 registros)  │   │   (267 registros)     │
    │  (13,796 registros)   │   └───────────┬───────────┘   └───────────────────────┘
    └───────────────────────┘               │
                                            ▼
                                ┌───────────────────────┐
                                │     esco_skills       │
                                │  (14,247 registros)   │
                                └───────────┬───────────┘
                                            │
                                            ▼
                                ┌───────────────────────┐
                                │ esco_skill_           │
                                │ alternative_labels    │
                                │  (20,422 registros)   │
                                └───────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE DATOS                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

 Portal Web                   Base de Datos               Taxonomía ESCO
     │                             │                            │
     │   scraping                  │                            │
     ▼                             ▼                            │
┌─────────┐   insert   ┌─────────────────┐                     │
│ Bumeran │ ─────────▶ │    ofertas      │                     │
│ ZonaJobs│            │  (9,564 reg)    │                     │
│ Indeed  │            └────────┬────────┘                     │
└─────────┘                     │                              │
                                │ NLP extraction               │
                                ▼                              │
                    ┌─────────────────┐                        │
                    │   ofertas_nlp   │                        │
                    │  (5,479 reg)    │                        │
                    └────────┬────────┘                        │
                             │                                 │
                             │ matching                        │
                             ▼                                 ▼
                    ┌─────────────────────────────────────────────┐
                    │           ofertas_esco_matching             │
                    │              (6,621 reg)                    │
                    │   ┌─────────────────────────────────────┐   │
                    │   │ • score_titulo (embedding BGE-M3)   │   │
                    │   │ • score_skills (coverage)           │   │
                    │   │ • score_descripcion (contextual)    │   │
                    │   │ • diccionario_arg_esco (bypass)     │   │
                    │   └─────────────────────────────────────┘   │
                    └─────────────────────────────────────────────┘
```

---

## 4. Relaciones Clave (Foreign Keys)

### 4.1 Foreign Keys Definidas

| Tabla Origen | Columna | Tabla Destino | Columna |
|--------------|---------|---------------|---------|
| `alertas` | metrica_id | `metricas_scraping` | id |
| `circuit_breaker_stats` | metrica_id | `metricas_scraping` | id |
| `cno_esco_matches` | cno_codigo | `cno_ocupaciones` | cno_codigo |
| `cno_esco_matches` | esco_occupation_uri | `esco_occupations` | occupation_uri |
| `esco_associations` | occupation_uri | `esco_occupations` | occupation_uri |
| `esco_associations` | skill_uri | `esco_skills` | skill_uri |
| `esco_isco_hierarchy` | broader_isco_code | `esco_isco_hierarchy` | isco_code |
| `esco_occupation_alternative_labels` | occupation_uri | `esco_occupations` | occupation_uri |
| `esco_occupation_ancestors` | occupation_uri | `esco_occupations` | occupation_uri |
| `esco_occupation_gendered_terms` | occupation_uri | `esco_occupations` | occupation_uri |
| `esco_skill_alternative_labels` | skill_uri | `esco_skills` | skill_uri |
| `keywords_performance_v2` | scraping_session_id | `scraping_sessions` | id |
| `keywords_performance_v2` | esco_occupation_uri | `esco_occupations` | occupation_uri |
| `keywords_performance_v2` | esco_skill_uri | `esco_skills` | skill_uri |
| `ofertas_esco_matching` | id_oferta | `ofertas` | id_oferta |
| `ofertas_esco_matching` | esco_occupation_uri | `esco_occupations` | occupation_uri |
| `ofertas_esco_skills_detalle` | id_oferta | `ofertas` | id_oferta |
| `ofertas_esco_skills_detalle` | esco_skill_uri | `esco_skills` | skill_uri |
| `ofertas_historial` | oferta_id | `ofertas` | id_oferta |
| `ofertas_historial` | scraping_session_id | `scraping_sessions` | id |

### 4.2 Relaciones Implícitas (sin FK formal)

| Tabla Origen | Columna | Tabla Destino | Nota |
|--------------|---------|---------------|------|
| `ofertas_nlp` | id_oferta | `ofertas` | Usa TEXT, no INTEGER FK |
| `ofertas_nlp_v2` | id_oferta | `ofertas` | Similar |
| `ofertas` | codigo_provincia_indec | `indec_provincias` | Sin FK formal |

---

## 5. Problemas de Diseño Detectados

### 5.1 Tablas Vacías (posible deprecated)

| Tabla | Estado | Recomendación |
|-------|--------|---------------|
| `scraping_sessions` | 0 registros | Implementar o eliminar |
| `circuit_breaker_stats` | 0 registros | Implementar o eliminar |
| `rate_limiter_stats` | 0 registros | Implementar o eliminar |
| `cno_ocupaciones` | 0 registros | No implementado - archivar |
| `cno_esco_matches` | 0 registros | No implementado - archivar |
| `ofertas_historial` | 0 registros | Implementar tracking |
| `esco_occupation_ancestors` | 0 registros | Poblar datos faltantes |
| `esco_occupation_gendered_terms` | 0 registros | Poblar datos faltantes |
| `skills` | 0 registros | Deprecated - eliminar |
| `ofertas_skills` | 0 registros | Deprecated - usar ofertas_esco_skills_detalle |
| `validacion_*` (5 tablas) | 0 registros | Implementar validación |

### 5.2 Inconsistencias de Tipos

| Problema | Tablas Afectadas | Impacto |
|----------|-----------------|---------|
| `id_oferta` como TEXT vs INTEGER | ofertas_nlp, ofertas_esco_matching | Sin FK integrity |
| FKs sin restricción NOT NULL | Múltiples | Posibles orphans |
| Fechas como TEXT | Todas | No validación de formato |

### 5.3 Indices Faltantes Recomendados

```sql
-- ofertas: índice compuesto para queries frecuentes
CREATE INDEX idx_ofertas_portal_fecha ON ofertas(portal, fecha_publicacion_iso);

-- ofertas_nlp: necesita índice para joins
CREATE INDEX idx_ofertas_nlp_id ON ofertas_nlp(id_oferta);

-- ofertas_esco_matching: índice para ISCO queries
CREATE INDEX idx_ofertas_esco_isco ON ofertas_esco_matching(isco_code);
```

### 5.4 Tablas Duplicadas/Versiones

| Grupo | Tablas | Recomendación |
|-------|--------|---------------|
| NLP | ofertas_nlp, ofertas_nlp_v2 | Migrar a v2, archivar v1 |
| Keywords | keywords_performance, keywords_performance_v2 | Migrar a v2, archivar v1 |
| Validación | 5 tablas separadas | Consolidar en una |

---

## 6. Estadísticas de Uso

### 6.1 Distribución de Registros

```
ofertas                          9,564  ████████████████████████████████████
ofertas_esco_matching            6,621  █████████████████████████
ofertas_nlp                      5,479  ████████████████████
keywords_performance             2,296  ████████
ofertas_esco_skills_detalle      1,315  ████
ofertas_raw                      1,078  ███
esco_isco_hierarchy                619  ██
diccionario_arg_esco               267  █
indec_provincias                    24
nlp_versions                         4
alertas                              5
metricas_scraping                    2
```

### 6.2 Taxonomía ESCO Cargada

| Componente | Registros |
|------------|-----------|
| Ocupaciones | 3,045 |
| Skills | 14,247 |
| Asociaciones Ocupación-Skill | 134,805 |
| Labels alternativos ocupaciones | 13,796 |
| Labels alternativos skills | 20,422 |
| Jerarquía ISCO | 619 |
| **Total ESCO** | **186,934** |

### 6.3 Cobertura de Datos

| Métrica | Valor | Porcentaje |
|---------|-------|------------|
| Ofertas con NLP procesado | 5,479 / 9,564 | 57.3% |
| Ofertas con matching ESCO | 6,621 / 9,564 | 69.2% |
| Ofertas con ambos | ~5,000 | ~52% |
| Skills detallados | 1,315 ofertas | 13.7% |

---

## 7. Queries de Referencia

### 7.1 Ofertas por Ocupación ESCO

```sql
SELECT
    m.esco_occupation_label,
    m.isco_code,
    COUNT(*) as total_ofertas,
    AVG(m.score_final_ponderado) as avg_score
FROM ofertas_esco_matching m
GROUP BY m.esco_occupation_uri
ORDER BY total_ofertas DESC
LIMIT 20;
```

### 7.2 Skills más Demandados

```sql
SELECT
    d.esco_skill_label,
    d.esco_skill_type,
    COUNT(*) as frecuencia
FROM ofertas_esco_skills_detalle d
WHERE d.esco_skill_uri IS NOT NULL
GROUP BY d.esco_skill_uri
ORDER BY frecuencia DESC
LIMIT 20;
```

### 7.3 Ofertas sin Match de Alta Calidad

```sql
SELECT
    o.id_oferta,
    o.titulo,
    m.esco_occupation_label,
    m.score_final_ponderado
FROM ofertas o
JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE m.score_final_ponderado < 0.5
  AND m.requiere_revision = 1
ORDER BY m.score_final_ponderado ASC;
```

### 7.4 Uso del Diccionario Bypass

```sql
SELECT
    d.termino_argentino,
    d.esco_preferred_label,
    d.isco_target,
    COUNT(m.id_oferta) as ofertas_matcheadas
FROM diccionario_arg_esco d
LEFT JOIN ofertas_esco_matching m
    ON m.esco_occupation_label = d.esco_preferred_label
GROUP BY d.id
ORDER BY ofertas_matcheadas DESC;
```

---

## 8. Recomendaciones

### 8.1 Corto Plazo (inmediato)

1. **Eliminar tablas deprecated:**
   - `skills`, `ofertas_skills` (reemplazadas por ofertas_esco_skills_detalle)
   - `cno_ocupaciones`, `cno_esco_matches` (nunca implementadas)

2. **Crear índices faltantes** (ver sección 5.3)

3. **Normalizar tipos de id_oferta** a INTEGER con FK formal

### 8.2 Mediano Plazo

1. **Implementar tracking:**
   - Poblar `ofertas_historial` con cambios detectados
   - Activar `scraping_sessions` para trazabilidad

2. **Consolidar validación:**
   - Unificar las 5 tablas de validación en una sola
   - Implementar workflow de validación humana

3. **Completar datos ESCO:**
   - Poblar `esco_occupation_ancestors`
   - Poblar `esco_occupation_gendered_terms`

### 8.3 Largo Plazo

1. **Migrar a PostgreSQL** si el volumen crece significativamente

2. **Implementar particionamiento** por fecha para ofertas históricas

3. **Crear vistas materializadas** para dashboards de alta frecuencia

---

## 9. Anexo: Tablas con id_oferta

Las siguientes tablas tienen referencia a ofertas:

| Tabla | Tipo columna | FK formal |
|-------|--------------|-----------|
| ofertas | INTEGER PK | - |
| ofertas_esco_matching | TEXT | Sí |
| ofertas_esco_skills_detalle | TEXT | Sí |
| ofertas_nlp | TEXT | No |
| ofertas_nlp_v2 | TEXT | No |
| ofertas_historial | TEXT | Sí |
| ofertas_raw | INTEGER | No |

---

*Documento generado automáticamente por analyze_db_architecture.py*
