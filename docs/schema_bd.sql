-- SCHEMA DE BASE DE DATOS: bumeran_scraping.db
-- Total de tablas: 32
-- Generado: 2025-11-14

-- ========================================
-- TABLA: alertas
-- ========================================
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Timestamp
    timestamp TEXT NOT NULL,  -- ISO 8601

    -- Tipo y severidad
    level TEXT NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
    type TEXT NOT NULL,   -- scraping, validation, circuit_breaker, rate_limiter, etc.
    message TEXT NOT NULL,

    -- Contexto adicional (JSON string)
    context TEXT,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Registros: 5

-- ========================================
-- TABLA: circuit_breaker_stats
-- ========================================
CREATE TABLE circuit_breaker_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Estadísticas
    state TEXT NOT NULL,  -- closed, open, half_open
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    consecutive_successes INTEGER NOT NULL DEFAULT 0,
    total_calls INTEGER NOT NULL DEFAULT 0,
    total_successes INTEGER NOT NULL DEFAULT 0,
    total_failures INTEGER NOT NULL DEFAULT 0,
    total_rejected INTEGER NOT NULL DEFAULT 0,
    success_rate REAL,
    times_opened INTEGER NOT NULL DEFAULT 0,
    time_in_state_seconds REAL,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Registros: 0

-- ========================================
-- TABLA: cno_esco_matches
-- ========================================
CREATE TABLE cno_esco_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cno_codigo TEXT NOT NULL,
            esco_occupation_uri TEXT NOT NULL,

            similarity_score REAL,
            matching_method TEXT,

            match_date TEXT,
            validated INTEGER DEFAULT 0,

            FOREIGN KEY (cno_codigo) REFERENCES cno_ocupaciones(cno_codigo),
            FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        );

-- Registros: 0

-- ========================================
-- TABLA: cno_ocupaciones
-- ========================================
CREATE TABLE cno_ocupaciones (
            cno_codigo TEXT PRIMARY KEY,
            cno_descripcion TEXT NOT NULL,
            cno_grupo TEXT,
            cno_subgrupo TEXT,
            ejemplos_ocupacionales TEXT,
            vigente INTEGER DEFAULT 1
        );

-- Registros: 0

-- ========================================
-- TABLA: diccionario_arg_esco
-- ========================================
CREATE TABLE diccionario_arg_esco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termino_argentino TEXT UNIQUE NOT NULL,
            esco_terms_json TEXT,
            isco_target TEXT,
            esco_preferred_label TEXT,
            notes TEXT
        );

-- Registros: 46

-- ========================================
-- TABLA: esco_associations
-- ========================================
CREATE TABLE esco_associations (
            association_uri TEXT PRIMARY KEY,
            occupation_uri TEXT NOT NULL,
            skill_uri TEXT NOT NULL,

            -- TIPO DE RELACIÓN
            relation_type TEXT NOT NULL,
            skill_type_in_relation TEXT,

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
            CHECK (relation_type IN ('essential', 'optional'))
        );

-- Registros: 0

-- ========================================
-- TABLA: esco_isco_hierarchy
-- ========================================
CREATE TABLE esco_isco_hierarchy (
            isco_code TEXT PRIMARY KEY,
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,
            hierarchy_level INTEGER NOT NULL,
            broader_isco_code TEXT,

            FOREIGN KEY (broader_isco_code) REFERENCES esco_isco_hierarchy(isco_code)
        );

-- Registros: 619

-- ========================================
-- TABLA: esco_occupation_alternative_labels
-- ========================================
CREATE TABLE esco_occupation_alternative_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occupation_uri TEXT NOT NULL,
            label TEXT NOT NULL,
            label_type TEXT DEFAULT 'altLabel',

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            UNIQUE(occupation_uri, label)
        );

-- Registros: 13796

-- ========================================
-- TABLA: esco_occupation_ancestors
-- ========================================
CREATE TABLE esco_occupation_ancestors (
            occupation_uri TEXT NOT NULL,
            ancestor_uri TEXT NOT NULL,
            ancestor_level INTEGER NOT NULL,
            ancestor_title TEXT,
            ancestor_type TEXT,

            PRIMARY KEY (occupation_uri, ancestor_uri),
            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            FOREIGN KEY (ancestor_uri) REFERENCES esco_occupations(occupation_uri)
        );

-- Registros: 0

-- ========================================
-- TABLA: esco_occupation_gendered_terms
-- ========================================
CREATE TABLE esco_occupation_gendered_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occupation_uri TEXT NOT NULL,
            term_label TEXT NOT NULL,
            roles_json TEXT,
            term_type TEXT DEFAULT 'alternativeTerm',

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri)
        );

-- Registros: 0

-- ========================================
-- TABLA: esco_occupations
-- ========================================
CREATE TABLE esco_occupations (
            -- IDENTIFICADORES
            occupation_uri TEXT PRIMARY KEY,
            occupation_uuid TEXT UNIQUE NOT NULL,
            esco_code TEXT,
            isco_code TEXT,

            -- LABELS Y DESCRIPCIONES (SOLO ESPAÑOL)
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,

            -- SCOPE NOTES
            scope_note_es TEXT,
            scope_note_mimetype TEXT DEFAULT 'text/html',

            -- PROFESIÓN REGULADA
            regulated_profession_uri TEXT,
            regulated_profession_note TEXT,
            is_regulated INTEGER DEFAULT 0,

            -- JERARQUÍA
            broader_occupation_uri TEXT,
            hierarchy_level INTEGER,

            -- METADATA
            status TEXT DEFAULT 'released',
            concept_type TEXT DEFAULT 'Occupation',
            last_modified TEXT,

            FOREIGN KEY (broader_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        );

-- Registros: 3045

-- ========================================
-- TABLA: esco_skill_alternative_labels
-- ========================================
CREATE TABLE esco_skill_alternative_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_uri TEXT NOT NULL,
            label TEXT NOT NULL,
            label_type TEXT DEFAULT 'altLabel',

            FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
            UNIQUE(skill_uri, label)
        );

-- Registros: 20422

-- ========================================
-- TABLA: esco_skills
-- ========================================
CREATE TABLE esco_skills (
            -- IDENTIFICADORES
            skill_uri TEXT PRIMARY KEY,
            skill_uuid TEXT UNIQUE NOT NULL,
            skill_code TEXT,

            -- LABELS (SOLO ESPAÑOL)
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,

            -- CLASIFICACIÓN
            skill_type TEXT,
            skill_reusability_level TEXT,

            -- METADATA
            status TEXT DEFAULT 'released',
            last_modified TEXT,

            CHECK (skill_type IN ('skill', 'knowledge', 'attitude'))
        );

-- Registros: 14247

-- ========================================
-- TABLA: keywords_performance
-- ========================================
CREATE TABLE keywords_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    estrategia TEXT,
    ofertas_encontradas INTEGER DEFAULT 0,
    ofertas_nuevas INTEGER DEFAULT 0,
    ofertas_duplicadas INTEGER DEFAULT 0,
    tiempo_ejecucion REAL,
    exito BOOLEAN DEFAULT 1,
    scraping_date TEXT,
    fuente TEXT DEFAULT 'bumeran',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
, esco_occupation_uri TEXT, esco_skill_uri TEXT, keyword_source TEXT, keyword_version TEXT);

-- Registros: 2296

-- ========================================
-- TABLA: keywords_performance_v2
-- ========================================
CREATE TABLE keywords_performance_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relaciones
    scraping_session_id INTEGER NOT NULL,     -- FK a scraping_sessions(id)
    keyword TEXT NOT NULL,                    -- Keyword usada en la búsqueda

    -- Resultados
    ofertas_encontradas INTEGER NOT NULL DEFAULT 0,
    ofertas_nuevas INTEGER NOT NULL DEFAULT 0,
    ofertas_duplicadas INTEGER NOT NULL DEFAULT 0,

    -- Enriquecimiento ESCO
    esco_occupation_uri TEXT,                 -- FK a esco_occupations(occupation_uri)
    esco_skill_uri TEXT,                      -- FK a esco_skills(skill_uri)
    keyword_source TEXT,                      -- 'manual', 'esco_occupation', 'esco_skill', 'trending', 'ai_generated'
    keyword_version TEXT,                     -- Versión del diccionario de keywords

    -- Performance
    execution_date TEXT NOT NULL DEFAULT (datetime('now')),
    execution_time_seconds REAL,              -- Tiempo que tomó scrapear este keyword
    pages_scraped INTEGER,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(scraping_session_id, keyword),

    FOREIGN KEY (scraping_session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri) ON DELETE SET NULL,
    FOREIGN KEY (esco_skill_uri) REFERENCES esco_skills(skill_uri) ON DELETE SET NULL,

    CHECK (keyword_source IN ('manual', 'esco_occupation', 'esco_skill', 'trending', 'ai_generated', 'user_input'))
);

-- Registros: 0

-- ========================================
-- TABLA: metricas_scraping
-- ========================================
CREATE TABLE metricas_scraping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Tiempos
    start_time TEXT NOT NULL,  -- ISO 8601
    end_time TEXT NOT NULL,
    total_time_seconds REAL NOT NULL,

    -- Páginas
    pages_scraped INTEGER NOT NULL DEFAULT 0,
    pages_failed INTEGER NOT NULL DEFAULT 0,
    pages_total INTEGER NOT NULL DEFAULT 0,
    success_rate REAL,  -- Porcentaje (0-100)
    avg_time_per_page REAL,  -- Segundos

    -- Ofertas
    offers_total INTEGER NOT NULL DEFAULT 0,
    offers_new INTEGER NOT NULL DEFAULT 0,
    offers_duplicates INTEGER NOT NULL DEFAULT 0,
    offers_per_second REAL,

    -- Validación
    validation_rate_avg REAL,  -- Porcentaje (0-100)
    validation_rate_min REAL,
    validation_rate_max REAL,

    -- Errores
    errors_count INTEGER NOT NULL DEFAULT 0,
    warnings_count INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    incremental_mode INTEGER NOT NULL DEFAULT 1,  -- 0=False, 1=True
    query TEXT,  -- Query de búsqueda si se usó

    -- Timestamp de inserción
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Registros: 2

-- ========================================
-- TABLA: nlp_versions
-- ========================================
CREATE TABLE nlp_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación
    version_name TEXT UNIQUE NOT NULL,        -- 'v1.0-regex', 'v2.0-llm', 'v3.7-hybrid'
    version_code TEXT UNIQUE NOT NULL,        -- 'regex_v1', 'llm_v2', 'hybrid_v3.7'

    -- Metadata
    description TEXT,                         -- Descripción de la versión
    model_type TEXT NOT NULL,                 -- 'regex', 'llm', 'hybrid', 'ner', 'transformer'
    model_name TEXT,                          -- 'llama3:latest', 'spacy_es_core_news_lg', etc.
    model_config TEXT,                        -- JSON con configuración del modelo

    -- Versionamiento
    major_version INTEGER NOT NULL,           -- 3
    minor_version INTEGER NOT NULL,           -- 7
    patch_version INTEGER NOT NULL,           -- 0

    -- Fechas
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT,                          -- Usuario/script que creó la versión
    deprecated_at TEXT,                       -- Fecha de deprecación (si aplica)

    -- Estado
    is_active INTEGER DEFAULT 0,              -- Solo una versión activa (1=activa, 0=inactiva)
    is_deprecated INTEGER DEFAULT 0,          -- Si está deprecada
    is_experimental INTEGER DEFAULT 0,        -- Si es experimental (no usar en prod)

    -- Performance agregada
    avg_confidence_score REAL,                -- Promedio de confidence score
    total_ofertas_procesadas INTEGER DEFAULT 0,
    avg_processing_time_ms REAL,              -- Tiempo promedio de procesamiento

    CHECK (is_active IN (0, 1)),
    CHECK (is_deprecated IN (0, 1)),
    CHECK (is_experimental IN (0, 1)),
    CHECK (model_type IN ('regex', 'llm', 'hybrid', 'ner', 'transformer', 'rule_based')),
    CHECK (major_version >= 0),
    CHECK (minor_version >= 0),
    CHECK (patch_version >= 0)
);

-- Registros: 4

-- ========================================
-- TABLA: ofertas
-- ========================================
CREATE TABLE ofertas (
    -- IDs
    id_oferta INTEGER PRIMARY KEY,
    id_empresa INTEGER,

    -- Información básica
    titulo TEXT NOT NULL,
    empresa TEXT,
    descripcion TEXT,
    confidencial INTEGER,  -- 0=False, 1=True

    -- Ubicación y modalidad
    localizacion TEXT,
    modalidad_trabajo TEXT,
    tipo_trabajo TEXT,

    -- Fechas (formato original DD-MM-YYYY)
    fecha_publicacion_original TEXT,
    fecha_hora_publicacion_original TEXT,
    fecha_modificado_original TEXT,

    -- Fechas ISO 8601 (para ordenamiento y filtrado)
    fecha_publicacion_iso TEXT,  -- YYYY-MM-DD
    fecha_hora_publicacion_iso TEXT,  -- YYYY-MM-DD HH:MM:SS
    fecha_modificado_iso TEXT,  -- YYYY-MM-DD

    -- Fechas datetime con timezone Argentina (UTC-3)
    fecha_publicacion_datetime TEXT,  -- ISO 8601 with timezone
    fecha_hora_publicacion_datetime TEXT,
    fecha_modificado_datetime TEXT,

    -- Detalles
    cantidad_vacantes INTEGER,
    apto_discapacitado INTEGER,  -- 0=False, 1=True

    -- Categorización
    id_area INTEGER,
    id_subarea INTEGER,
    id_pais INTEGER,

    -- Empresa
    logo_url TEXT,
    empresa_validada INTEGER,  -- 0=False, 1=True
    empresa_pro INTEGER,  -- 0=False, 1=True
    promedio_empresa REAL,

    -- Plan de publicación
    plan_publicacion_id INTEGER,
    plan_publicacion_nombre TEXT,

    -- Otros
    portal TEXT,
    tipo_aviso TEXT,
    tiene_preguntas INTEGER,  -- 0=False, 1=True
    salario_obligatorio INTEGER,  -- 0=False, 1=True
    alta_revision_perfiles INTEGER,  -- 0=False, 1=True
    guardado INTEGER,  -- 0=False, 1=True
    gptw_url TEXT,

    -- Metadata
    url_oferta TEXT,
    scrapeado_en TEXT NOT NULL DEFAULT (datetime('now'))  -- ISO 8601
, descripcion_utf8 TEXT);

-- Registros: 6521

-- ========================================
-- TABLA: ofertas_esco_matching
-- ========================================
CREATE TABLE ofertas_esco_matching (
            id_oferta TEXT PRIMARY KEY,

            -- MATCHING DE OCUPACI[U+00D3]N
            esco_occupation_uri TEXT,
            esco_occupation_label TEXT,
            occupation_match_score REAL,
            occupation_match_method TEXT,

            -- MATCHING DE T[U+00CD]TULO
            titulo_normalizado TEXT,
            titulo_esco_code TEXT,

            -- SKILLS MATCHEADOS
            esco_skills_esenciales_json TEXT,
            esco_skills_opcionales_json TEXT,

            -- GAP ANALYSIS
            skills_demandados_total INTEGER,
            skills_matcheados_esco INTEGER,
            skills_sin_match_json TEXT,

            -- METADATA
            matching_timestamp TEXT,
            matching_version TEXT,
            confidence_score REAL,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
            FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        );

-- Registros: 6521

-- ========================================
-- TABLA: ofertas_esco_skills_detalle
-- ========================================
CREATE TABLE ofertas_esco_skills_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta TEXT NOT NULL,

            -- SKILL EXTRA[U+00CD]DO
            skill_mencionado TEXT NOT NULL,
            skill_tipo_fuente TEXT,
            skill_nivel_mencionado TEXT,

            -- MATCHING CON ESCO
            esco_skill_uri TEXT,
            esco_skill_label TEXT,
            match_score REAL,
            match_method TEXT,

            -- CLASIFICACI[U+00D3]N ESCO
            esco_skill_type TEXT,
            esco_skill_reusability TEXT,

            -- RELACI[U+00D3]N CON OCUPACI[U+00D3]N
            is_essential_for_occupation INTEGER DEFAULT 0,
            is_optional_for_occupation INTEGER DEFAULT 0,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
            FOREIGN KEY (esco_skill_uri) REFERENCES esco_skills(skill_uri)
        );

-- Registros: 0

-- ========================================
-- TABLA: ofertas_historial
-- ========================================
CREATE TABLE ofertas_historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación
    oferta_id TEXT NOT NULL,                  -- FK a ofertas(id_oferta)
    campo_modificado TEXT NOT NULL,           -- 'salario_min', 'descripcion', 'titulo', etc.

    -- Valores (serializados como TEXT para soportar cualquier tipo)
    valor_anterior TEXT,                      -- Valor antes del cambio
    valor_nuevo TEXT,                         -- Valor después del cambio

    -- Tipo de dato (para deserializar correctamente)
    tipo_dato TEXT NOT NULL,                  -- 'TEXT', 'INTEGER', 'REAL', 'JSON', 'BOOLEAN'

    -- Contexto del cambio
    fecha_modificacion TEXT NOT NULL DEFAULT (datetime('now')),
    scraping_session_id INTEGER,              -- FK a scraping_sessions(id) - NULL si cambio manual
    change_type TEXT NOT NULL,                -- 'insert', 'update', 'delete', 'manual'
    change_source TEXT,                       -- 'scraping', 'manual_edit', 'migration', 'api'

    -- Metadata
    user_id TEXT,                             -- Usuario que hizo el cambio (si aplica)
    notes TEXT,                               -- Notas adicionales sobre el cambio

    FOREIGN KEY (oferta_id) REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    FOREIGN KEY (scraping_session_id) REFERENCES scraping_sessions(id) ON DELETE SET NULL,

    CHECK (change_type IN ('insert', 'update', 'delete', 'manual')),
    CHECK (change_source IN ('scraping', 'manual_edit', 'migration', 'api', 'system')),
    CHECK (tipo_dato IN ('TEXT', 'INTEGER', 'REAL', 'JSON', 'BOOLEAN', 'NULL'))
);

-- Registros: 0

-- ========================================
-- TABLA: ofertas_nlp
-- ========================================
CREATE TABLE ofertas_nlp (
            id_oferta TEXT PRIMARY KEY,

            -- EXPERIENCIA (3 campos)
            experiencia_min_anios INTEGER,
            experiencia_max_anios INTEGER,
            experiencia_area TEXT,

            -- EDUCACIÓN (4 campos)
            nivel_educativo TEXT,
            estado_educativo TEXT,
            carrera_especifica TEXT,
            titulo_excluyente INTEGER,

            -- IDIOMAS (4 campos)
            idioma_principal TEXT,
            nivel_idioma_principal TEXT,
            idioma_secundario TEXT,
            nivel_idioma_secundario TEXT,

            -- SKILLS TÉCNICAS (4 campos - JSON arrays)
            skills_tecnicas_list TEXT,
            niveles_skills_list TEXT,
            soft_skills_list TEXT,
            certificaciones_list TEXT,

            -- COMPENSACIÓN (4 campos)
            salario_min REAL,
            salario_max REAL,
            moneda TEXT,
            beneficios_list TEXT,

            -- REQUISITOS (2 campos)
            requisitos_excluyentes_list TEXT,
            requisitos_deseables_list TEXT,

            -- JORNADA (2 campos)
            jornada_laboral TEXT,
            horario_flexible INTEGER,

            -- METADATA NLP (3 campos)
            nlp_extraction_timestamp TEXT,
            nlp_version TEXT,
            nlp_confidence_score REAL,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
        );

-- Registros: 5479

-- ========================================
-- TABLA: ofertas_nlp_history
-- ========================================
CREATE TABLE ofertas_nlp_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,
    nlp_version TEXT NOT NULL,  -- Ej: "3.7.0", "4.0.0", "5.0.0"
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Datos extraídos (JSON completo con todos los campos)
    extracted_data TEXT,  -- JSON con estructura completa

    -- Métricas de calidad
    quality_score REAL,           -- Score 0-7 (número de campos poblados)
    confidence_score REAL,        -- Score 0-1 (confianza del extractor)
    processing_time_ms INTEGER,   -- Tiempo de procesamiento en ms

    -- Control de activación
    is_active BOOLEAN DEFAULT 0,  -- Solo una versión activa por oferta
    replaced_by_version TEXT,      -- Si fue reemplazada, ¿por cuál?

    -- Metadata adicional
    extraction_method TEXT,        -- "regex", "llm", "hybrid"
    error_message TEXT,            -- NULL si OK, mensaje si error

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta) ON DELETE CASCADE
);

-- Registros: 6053

-- ========================================
-- TABLA: ofertas_nlp_v2
-- ========================================
CREATE TABLE ofertas_nlp_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relaciones
    id_oferta TEXT NOT NULL,                  -- FK a ofertas(id_oferta)
    version_id INTEGER NOT NULL,              -- FK a nlp_versions(id)

    -- EXPERIENCIA (3 campos)
    experiencia_min_anios INTEGER,
    experiencia_max_anios INTEGER,
    experiencia_area TEXT,                    -- 'desarrollo', 'ventas', 'administracion'

    -- EDUCACIÓN (4 campos)
    nivel_educativo TEXT,                     -- 'secundario', 'terciario', 'universitario', 'posgrado'
    estado_educativo TEXT,                    -- 'completo', 'en_curso', 'incompleto'
    carrera_especifica TEXT,
    titulo_excluyente INTEGER DEFAULT 0,

    -- IDIOMAS (4 campos - se mantienen por ahora, se normalizarán en FASE 2)
    idioma_principal TEXT,                    -- 'español', 'inglés', 'portugués'
    nivel_idioma_principal TEXT,              -- 'basico', 'intermedio', 'avanzado', 'nativo'
    idioma_secundario TEXT,
    nivel_idioma_secundario TEXT,

    -- SKILLS: Ahora en tablas normalizadas (skills + ofertas_skills)
    -- Los campos JSON se mantienen temporalmente durante migración
    skills_tecnicas_list_legacy TEXT,         -- JSON array (deprecado, usar ofertas_skills)
    soft_skills_list_legacy TEXT,             -- JSON array (deprecado, usar ofertas_skills)
    certificaciones_list_legacy TEXT,         -- JSON array (deprecado, usar ofertas_skills)

    -- COMPENSACIÓN (4 campos)
    salario_min REAL,
    salario_max REAL,
    moneda TEXT DEFAULT 'ARS',
    beneficios_list TEXT,                     -- JSON array: ['obra social', 'vacaciones']

    -- REQUISITOS (2 campos - pendiente normalizar)
    requisitos_excluyentes_list TEXT,         -- JSON array
    requisitos_deseables_list TEXT,           -- JSON array

    -- JORNADA (2 campos)
    jornada_laboral TEXT,                     -- 'tiempo_completo', 'medio_tiempo', 'por_proyecto'
    horario_flexible INTEGER DEFAULT 0,

    -- METADATA
    extraction_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    confidence_score REAL,                    -- Score 0-7 (7 campos principales)
    processing_time_ms REAL,                  -- Tiempo que tomó el procesamiento

    -- Índice único: una oferta solo tiene una extracción por versión
    UNIQUE(id_oferta, version_id),

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES nlp_versions(id) ON DELETE RESTRICT,

    CHECK (nivel_educativo IN ('secundario', 'terciario', 'universitario', 'posgrado', NULL)),
    CHECK (estado_educativo IN ('completo', 'en_curso', 'incompleto', NULL)),
    CHECK (moneda IN ('ARS', 'USD', 'EUR', NULL)),
    CHECK (jornada_laboral IN ('tiempo_completo', 'medio_tiempo', 'por_proyecto', 'pasantia', NULL)),
    CHECK (titulo_excluyente IN (0, 1)),
    CHECK (horario_flexible IN (0, 1)),
    CHECK (confidence_score >= 0 AND confidence_score <= 7)
);

-- Registros: 0

-- ========================================
-- TABLA: ofertas_raw
-- ========================================
CREATE TABLE ofertas_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación
    id_oferta TEXT NOT NULL,                  -- ID original de Bumeran/Indeed/etc
    scraping_session_id INTEGER NOT NULL,     -- FK a scraping_sessions(id)

    -- Datos crudos (payload completo de la API/HTML)
    raw_json TEXT NOT NULL,                   -- JSON completo del scraping

    -- Metadata
    scrapeado_en TEXT NOT NULL DEFAULT (datetime('now')),
    source TEXT NOT NULL,                     -- 'bumeran', 'indeed', etc
    url_oferta TEXT,                          -- URL de la oferta

    -- Hash para detectar cambios
    content_hash TEXT,                        -- SHA256 del raw_json

    FOREIGN KEY (scraping_session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE
);

-- Registros: 5479

-- ========================================
-- TABLA: ofertas_skills
-- ========================================
CREATE TABLE ofertas_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relaciones
    oferta_id TEXT NOT NULL,                  -- FK a ofertas(id_oferta)
    skill_id INTEGER NOT NULL,                -- FK a skills(id)
    version_id INTEGER NOT NULL,              -- FK a nlp_versions(id)

    -- Contexto del skill en la oferta
    nivel TEXT,                               -- 'basico', 'intermedio', 'avanzado', 'experto'
    tipo_requisito TEXT,                      -- 'excluyente', 'deseable', 'opcional', 'valorable'

    -- Origen de la detección
    fuente_deteccion TEXT,                    -- 'titulo', 'descripcion', 'requisitos', 'inferido'
    mencionado_en_titulo INTEGER DEFAULT 0,   -- Si aparece en el título de la oferta
    mencionado_en_descripcion INTEGER DEFAULT 0,

    -- Metadata
    confidence_score REAL,                    -- Confidence de que este skill aplica (0-1)
    extraction_method TEXT,                   -- 'regex', 'llm', 'ner', 'keyword'
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Índice único: un skill solo aparece una vez por oferta/versión
    UNIQUE(oferta_id, skill_id, version_id),

    FOREIGN KEY (oferta_id) REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES nlp_versions(id) ON DELETE RESTRICT,

    CHECK (nivel IN ('basico', 'intermedio', 'avanzado', 'experto', NULL)),
    CHECK (tipo_requisito IN ('excluyente', 'deseable', 'opcional', 'valorable', NULL)),
    CHECK (fuente_deteccion IN ('titulo', 'descripcion', 'requisitos', 'inferido', NULL)),
    CHECK (mencionado_en_titulo IN (0, 1)),
    CHECK (mencionado_en_descripcion IN (0, 1)),
    CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Registros: 0

-- ========================================
-- TABLA: rate_limiter_stats
-- ========================================
CREATE TABLE rate_limiter_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Estadísticas
    current_delay REAL NOT NULL,  -- Segundos
    min_delay REAL NOT NULL,
    max_delay REAL NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_success INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    total_rate_limits INTEGER NOT NULL DEFAULT 0,  -- 429s
    success_rate REAL,
    consecutive_success INTEGER NOT NULL DEFAULT 0,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,

    -- Historial de delays (JSON array como string)
    delay_history TEXT,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Registros: 0

-- ========================================
-- TABLA: schema_migrations
-- ========================================
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    applied_by TEXT,
    execution_time_seconds REAL
);

-- Registros: 1

-- ========================================
-- TABLA: scraping_sessions
-- ========================================
CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación única
    session_uuid TEXT UNIQUE NOT NULL,        -- UUID único de la sesión

    -- Tiempos
    start_time TEXT NOT NULL,                 -- ISO 8601: '2025-11-02T14:30:00-03:00'
    end_time TEXT,                            -- NULL si aún está corriendo

    -- Configuración de scraping
    source TEXT NOT NULL,                     -- 'bumeran', 'indeed', 'zonajobs'
    mode TEXT NOT NULL,                       -- 'full', 'incremental', 'keyword_search'
    keywords_used TEXT,                       -- JSON array: ['python', 'sql', ...]
    max_pages INTEGER,                        -- Límite de páginas por keyword

    -- Resultados
    ofertas_total INTEGER DEFAULT 0,          -- Total de ofertas encontradas
    ofertas_nuevas INTEGER DEFAULT 0,         -- Ofertas nuevas (no duplicadas)
    ofertas_actualizadas INTEGER DEFAULT 0,   -- Ofertas que cambiaron desde último scraping

    -- Performance
    total_time_seconds REAL,                  -- Tiempo total de ejecución
    avg_time_per_oferta REAL,                 -- Promedio por oferta

    -- Estado
    status TEXT DEFAULT 'running',            -- 'running', 'completed', 'failed', 'cancelled'
    error_message TEXT,                       -- Mensaje de error si falló

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    CHECK (source IN ('bumeran', 'indeed', 'zonajobs', 'computrabajo', 'linkedin')),
    CHECK (mode IN ('full', 'incremental', 'keyword_search', 'url_list')),

    UNIQUE(source, start_time)
);

-- Registros: 1

-- ========================================
-- TABLA: sinonimos_regionales
-- ========================================
CREATE TABLE sinonimos_regionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_ocupacional TEXT,
            termino_base TEXT,
            pais TEXT,
            sinonimos_json TEXT,
            descripcion TEXT,

            UNIQUE(categoria_ocupacional, termino_base, pais)
        );

-- Registros: 0

-- ========================================
-- TABLA: skills
-- ========================================
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación
    nombre TEXT UNIQUE NOT NULL,              -- 'Python', 'SQL', 'Liderazgo'
    nombre_normalizado TEXT NOT NULL,         -- 'python', 'sql', 'liderazgo' (lowercase)

    -- Clasificación
    tipo TEXT NOT NULL,                       -- 'tecnica', 'soft', 'certificacion', 'idioma', 'herramienta'
    categoria TEXT,                           -- 'programacion', 'base_datos', 'gestion', 'ventas'
    subcategoria TEXT,                        -- 'backend', 'frontend', 'data_science'

    -- Enriquecimiento con ESCO
    esco_skill_uri TEXT,                      -- FK a esco_skills(skill_uri) si existe matching
    esco_reusability TEXT,                    -- 'transversal', 'sector_specific', 'occupation_specific'

    -- Sinónimos y variantes
    sinonimos TEXT,                           -- JSON array: ['Python 3', 'Python3', 'Py']
    tags TEXT,                                -- JSON array: ['lenguaje', 'backend', 'data']

    -- Estadísticas
    frecuencia_total INTEGER DEFAULT 0,       -- Cuántas veces aparece en ofertas (todas las versiones)
    frecuencia_actual INTEGER DEFAULT 0,      -- Cuántas veces en ofertas actuales (últimos 30 días)
    primera_aparicion TEXT,                   -- Primera vez que se vio este skill
    ultima_aparicion TEXT,                    -- Última vez que se vio

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,

    CHECK (tipo IN ('tecnica', 'soft', 'certificacion', 'idioma', 'herramienta', 'conocimiento')),
    CHECK (frecuencia_total >= 0),
    CHECK (frecuencia_actual >= 0)
);

-- Registros: 0

-- ========================================
-- TABLA: sqlite_sequence
-- ========================================
CREATE TABLE sqlite_sequence(name,seq);

-- Registros: 11

