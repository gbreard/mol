# Diagrama Entidad-Relación - MOL

## Arquitectura Dual

El proyecto MOL usa dos bases de datos con propósitos distintos:

| BD | Motor | Propósito | Datos |
|----|-------|-----------|-------|
| **Local** | SQLite | Procesamiento (scraping, NLP, matching) | 13K+ ofertas, todo el historial |
| **Cloud** | Supabase (PostgreSQL) | Presentación (dashboard multi-tenant) | ~1K ofertas validadas |

---

## SQLite Local - Schema Actual

### Diagrama Principal (Tablas Core)

```mermaid
erDiagram
    ofertas ||--o| ofertas_nlp : "1:1"
    ofertas ||--o| ofertas_esco_matching : "1:1"
    ofertas ||--o{ ofertas_esco_skills_detalle : "1:N"
    ofertas ||--o{ ofertas_nlp_history : "1:N"
    ofertas ||--o| ofertas_prioridad : "1:1"

    ofertas {
        int id_oferta PK
        int id_empresa
        string titulo
        string empresa
        string descripcion
        string localizacion
        string modalidad_trabajo
        date fecha_publicacion_iso
        int cantidad_vacantes
        string portal
        string url_oferta
        timestamp scrapeado_en
        string estado_oferta
        date fecha_ultimo_visto
        date fecha_baja
        int dias_publicada
        string categoria_permanencia
    }

    ofertas_nlp {
        int id_oferta PK,FK
        string titulo_limpio
        string provincia
        string localidad
        string modalidad
        int experiencia_min_anios
        int experiencia_max_anios
        string nivel_educativo
        string area_funcional
        string nivel_seniority
        string sector_empresa
        int salario_min
        int salario_max
        json skills_tecnicas_list
        json soft_skills_list
        json tareas_explicitas
        json tareas_inferidas
        string clae_code
        string clae_grupo
    }

    ofertas_esco_matching {
        int id_oferta PK,FK
        string run_id FK
        string esco_occupation_uri
        string esco_occupation_label
        string isco_code
        string isco_label
        float occupation_match_score
        string isco_regla
        string isco_semantico
        float score_semantico
        string regla_aplicada
        int dual_coinciden
        string decision_metodo
        json skills_oferta_json
        json skills_regla_json
        json skills_semantico_json
        string estado_validacion
        timestamp validado_timestamp
        string validado_por
    }

    ofertas_esco_skills_detalle {
        int id PK
        int id_oferta FK
        string skill_esco
        string skill_uri
        string preferred_label_es
        string L1
        string L1_nombre
        string L2
        string L2_nombre
        int es_digital
        float score
        string origen_tipo
    }

    ofertas_nlp_history {
        int id PK
        int id_oferta FK
        string nlp_version
        timestamp processed_at
        json extracted_data
        float quality_score
        int is_active
    }

    ofertas_prioridad {
        int id_oferta PK,FK
        float score_total
        float score_fecha
        float score_vacantes
        float score_permanencia
        string estado
        string lote_asignado
    }
```

### Diagrama Tracking y Validación

```mermaid
erDiagram
    pipeline_runs ||--o{ ofertas_esco_matching : "1:N"
    pipeline_runs ||--o{ validation_errors : "1:N"
    pipeline_runs ||--o{ learning_history : "1:N"

    pipeline_runs {
        string run_id PK
        timestamp timestamp
        string source
        string description
        string git_branch
        string git_commit
        string nlp_version
        string matching_version
        json config_snapshot
        int ofertas_count
        json ofertas_ids
        float metricas_precision
        int errores_detectados
        int errores_corregidos
        int delta_reglas
    }

    validation_errors {
        int id PK
        int id_oferta FK
        string run_id FK
        string error_id
        string error_tipo
        string severidad
        string mensaje
        string campo_afectado
        string valor_actual
        int corregido
        int escalado_claude
        int resuelto
    }

    learning_history {
        int id PK
        timestamp timestamp
        string run_id FK
        string evento_tipo
        string config_modificado
        string descripcion
        int conteo_antes
        int conteo_despues
        int delta
    }
```

### Diagrama Catálogos ESCO

```mermaid
erDiagram
    esco_occupations ||--o{ esco_associations : "1:N"
    esco_skills ||--o{ esco_associations : "1:N"
    esco_occupations ||--o{ esco_occupation_alternative_labels : "1:N"
    esco_skills ||--o{ esco_skill_alternative_labels : "1:N"

    esco_occupations {
        string occupation_uri PK
        string preferred_label_es
        string isco_code
        string description
        string esco_classification_code
    }

    esco_skills {
        string skill_uri PK
        string preferred_label_es
        string L1
        string L1_nombre
        string L2
        string L2_nombre
        int es_digital
    }

    esco_associations {
        int id PK
        string occupation_uri FK
        string skill_uri FK
        string relation_type
    }

    esco_occupation_alternative_labels {
        int id PK
        string occupation_uri FK
        string alternative_label
        string language
    }

    esco_skill_alternative_labels {
        int id PK
        string skill_uri FK
        string alternative_label
        string language
    }
```

### Diagrama Scraping y Métricas

```mermaid
erDiagram
    metricas_scraping ||--o{ alertas : "1:N"
    metricas_scraping ||--o| circuit_breaker_stats : "1:1"
    metricas_scraping ||--o| rate_limiter_stats : "1:1"

    metricas_scraping {
        int id PK
        timestamp start_time
        timestamp end_time
        float total_time_seconds
        int pages_scraped
        int pages_failed
        float success_rate
        int offers_total
        int offers_new
        int offers_duplicates
        int errors_count
        int warnings_count
        string query
    }

    alertas {
        int id PK
        int metrica_id FK
        timestamp timestamp
        string level
        string type
        string message
        json context
    }

    circuit_breaker_stats {
        int id PK
        int metrica_id FK
        string state
        int consecutive_failures
        int total_calls
        float success_rate
    }

    rate_limiter_stats {
        int id PK
        int metrica_id FK
        float current_delay
        int total_requests
        float success_rate
    }
```

---

## Supabase Cloud - Schema Propuesto (Multi-Tenant)

### Diagrama Multi-Tenant

```mermaid
erDiagram
    tenants ||--o{ tenant_users : "1:N"
    tenants ||--o{ ofertas : "1:N"
    auth_users ||--o{ tenant_users : "1:N"
    ofertas ||--o{ ofertas_skills : "1:N"
    skills ||--o{ ofertas_skills : "1:N"
    empresas ||--o{ ofertas : "1:N"
    ocupaciones_esco ||--o{ ofertas : "1:N"

    tenants {
        uuid id PK
        string nombre
        string tipo
        jsonb config
        timestamp created_at
    }

    tenant_users {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        enum role
        timestamp created_at
    }

    auth_users {
        uuid id PK
        string email
        timestamp created_at
    }

    ofertas {
        serial id PK
        int id_oferta UK
        string titulo
        string titulo_limpio
        int empresa_id FK
        string provincia
        string localidad
        string modalidad
        string isco_code
        string isco_label
        string esco_uri FK
        decimal match_score
        int salario_min
        int salario_max
        string nivel_seniority
        uuid tenant_id FK
        string visibilidad
        timestamp fecha_publicacion
        timestamp fecha_sync
    }

    ofertas_skills {
        serial id PK
        int id_oferta FK
        string skill_uri FK
        decimal score
        string origen
    }

    skills {
        string skill_uri PK
        string preferred_label_es
        string L1
        string L1_nombre
        string L2
        string L2_nombre
        bool es_digital
    }

    empresas {
        serial id PK
        string nombre
        string sector
        string tamanio
        int ofertas_count
    }

    ocupaciones_esco {
        string esco_uri PK
        string isco_code
        string preferred_label_es
        string description
    }
```

---

## Flujo de Datos: SQLite → Supabase

```mermaid
flowchart LR
    subgraph LOCAL["SQLite Local"]
        O[ofertas]
        N[ofertas_nlp]
        M[ofertas_esco_matching]
        S[ofertas_esco_skills_detalle]
    end

    subgraph SYNC["sync_to_supabase.py"]
        F1[Filtrar validadas]
        F2[Desnormalizar]
        F3[Extraer skills]
        F4[Asignar tenant]
    end

    subgraph CLOUD["Supabase Cloud"]
        OS[ofertas]
        SK[ofertas_skills]
        T[tenants]
    end

    O --> F1
    N --> F1
    M --> F1
    S --> F3

    F1 --> F2
    F2 --> F4
    F3 --> SK

    F4 --> OS
    T -.-> OS
```

---

## Resumen de Tablas

### SQLite Local (32 tablas)

| Capa | Tablas | Propósito |
|------|--------|-----------|
| **Scraping** | ofertas, metricas_scraping, alertas, circuit_breaker_stats, rate_limiter_stats | Datos crudos y métricas |
| **NLP** | ofertas_nlp, ofertas_nlp_history | Extracción semántica |
| **Matching** | ofertas_esco_matching, ofertas_esco_skills_detalle | Clasificación ESCO |
| **ESCO** | esco_occupations, esco_skills, esco_associations, *_alternative_labels | Catálogos de referencia |
| **Tracking** | pipeline_runs, validation_errors, learning_history, validacion_historial | Auditoría y aprendizaje |
| **Priorización** | ofertas_prioridad | Cola de procesamiento |
| **A/B Testing** | ab_snapshot_*, ab_experiments | Experimentación |

### Supabase Cloud (8 tablas propuestas)

| Capa | Tablas | Propósito |
|------|--------|-----------|
| **Core** | ofertas, empresas, ocupaciones_esco | Datos desnormalizados para dashboard |
| **Skills** | skills, ofertas_skills | Skills normalizados y queryables |
| **Multi-tenant** | tenants, tenant_users | Aislamiento por organización |
| **Issues** | issues | Feedback de usuarios |

---

## Índices Principales

### SQLite

| Tabla | Índice | Columnas |
|-------|--------|----------|
| ofertas | idx_ofertas_fecha_pub_iso | fecha_publicacion_iso |
| ofertas | idx_ofertas_estado | estado_oferta |
| ofertas_nlp | idx_ofertas_nlp_area | area_funcional |
| ofertas_nlp | idx_ofertas_nlp_seniority | nivel_seniority |
| ofertas_esco_matching | idx_matching_estado | estado_validacion |
| ofertas_esco_matching | idx_dual_coinciden | dual_coinciden |
| ofertas_prioridad | idx_prioridad_estado_score | estado, score_total |
| validation_errors | idx_errors_no_resuelto | resuelto, severidad |

### Supabase

| Tabla | Índice | Columnas |
|-------|--------|----------|
| ofertas | idx_ofertas_tenant | tenant_id |
| ofertas | idx_ofertas_visibilidad | visibilidad |
| ofertas | idx_ofertas_isco | isco_code |
| ofertas_skills | idx_skills_oferta | id_oferta |
| ofertas_skills | idx_skills_uri | skill_uri |

---

## Row Level Security (Supabase)

```sql
-- Política principal: cada tenant ve solo sus datos + públicos
CREATE POLICY "tenant_isolation" ON ofertas
    FOR SELECT USING (
        tenant_id = auth.uid()
        OR visibilidad = 'publico'
        OR EXISTS (
            SELECT 1 FROM tenants t
            WHERE t.id = auth.uid() AND t.tipo = 'oede'
        )
    );
```

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-03 | Versión inicial con arquitectura dual |
