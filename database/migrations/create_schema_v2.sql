-- =====================================================================
-- ESQUEMA DE BASE DE DATOS V2.0 - Bumeran Scraping
-- =====================================================================
--
-- Migración de diseño actual a diseño relacional normalizado
-- con versionado, tracking histórico y normalización de skills
--
-- Fecha:       2025-11-02
-- Versión:     2.0.0
-- Fase:        FASE 1 - Preparación
--
-- Mejoras principales:
--   1. Versionado de extracción NLP (rollback, A/B testing)
--   2. Tracking de cambios históricos
--   3. Normalización de skills/certificaciones
--   4. Eliminación de redundancia de fechas
--   5. Foreign keys formalizadas
--   6. Índices optimizados para queries analíticos
--
-- =====================================================================

-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- =====================================================================
-- TABLA 1: scraping_sessions
-- =====================================================================
-- Contexto de cada ejecución de scraping
-- Permite agrupar ofertas por sesión y hacer análisis temporal
-- =====================================================================

CREATE TABLE IF NOT EXISTS scraping_sessions (
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

-- Índices para scraping_sessions
CREATE INDEX idx_sessions_source_status ON scraping_sessions(source, status);
CREATE INDEX idx_sessions_start_time ON scraping_sessions(start_time DESC);
CREATE INDEX idx_sessions_uuid ON scraping_sessions(session_uuid);
CREATE INDEX idx_sessions_created ON scraping_sessions(created_at DESC);


-- =====================================================================
-- TABLA 2: ofertas_raw
-- =====================================================================
-- Almacena TODAS las versiones scrapeadas de cada oferta (inmutable)
-- Permite auditoría completa y re-procesamiento sin pérdida de datos
-- =====================================================================

CREATE TABLE IF NOT EXISTS ofertas_raw (
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

-- Índices para ofertas_raw
CREATE INDEX idx_ofertas_raw_id_oferta ON ofertas_raw(id_oferta);
CREATE INDEX idx_ofertas_raw_session ON ofertas_raw(scraping_session_id);
CREATE INDEX idx_ofertas_raw_scrapeado ON ofertas_raw(scrapeado_en DESC);
CREATE INDEX idx_ofertas_raw_source ON ofertas_raw(source);
CREATE INDEX idx_ofertas_raw_hash ON ofertas_raw(content_hash);


-- =====================================================================
-- TABLA 3: nlp_versions
-- =====================================================================
-- Catálogo de versiones de extracción NLP
-- Permite rollback, A/B testing y comparación de versiones
-- =====================================================================

CREATE TABLE IF NOT EXISTS nlp_versions (
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

-- Índices para nlp_versions
CREATE INDEX idx_nlp_versions_active ON nlp_versions(is_active);
CREATE INDEX idx_nlp_versions_code ON nlp_versions(version_code);
CREATE INDEX idx_nlp_versions_model_type ON nlp_versions(model_type);
CREATE INDEX idx_nlp_versions_created ON nlp_versions(created_at DESC);

-- Trigger: Solo una versión puede estar activa
CREATE TRIGGER trg_nlp_versions_single_active
BEFORE UPDATE OF is_active ON nlp_versions
WHEN NEW.is_active = 1
BEGIN
    UPDATE nlp_versions SET is_active = 0 WHERE id != NEW.id AND is_active = 1;
END;


-- =====================================================================
-- TABLA 4: ofertas_nlp_v2
-- =====================================================================
-- Resultados de extracción NLP con versionado
-- NO sobrescribe versiones anteriores (permite comparación)
-- =====================================================================

CREATE TABLE IF NOT EXISTS ofertas_nlp_v2 (
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

-- Índices para ofertas_nlp_v2
CREATE INDEX idx_ofertas_nlp_v2_oferta ON ofertas_nlp_v2(id_oferta);
CREATE INDEX idx_ofertas_nlp_v2_version ON ofertas_nlp_v2(version_id);
CREATE INDEX idx_ofertas_nlp_v2_exp ON ofertas_nlp_v2(experiencia_min_anios);
CREATE INDEX idx_ofertas_nlp_v2_edu ON ofertas_nlp_v2(nivel_educativo);
CREATE INDEX idx_ofertas_nlp_v2_jornada ON ofertas_nlp_v2(jornada_laboral);
CREATE INDEX idx_ofertas_nlp_v2_timestamp ON ofertas_nlp_v2(extraction_timestamp DESC);
CREATE INDEX idx_ofertas_nlp_v2_confidence ON ofertas_nlp_v2(confidence_score DESC);

-- Índice compuesto para la query más frecuente: obtener NLP de versión activa
CREATE INDEX idx_ofertas_nlp_v2_oferta_version ON ofertas_nlp_v2(id_oferta, version_id);


-- =====================================================================
-- TABLA 5: skills
-- =====================================================================
-- Catálogo normalizado de skills (técnicas, soft, certificaciones, idiomas)
-- Elimina duplicación y permite análisis de tendencias
-- =====================================================================

CREATE TABLE IF NOT EXISTS skills (
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

-- Índices para skills
CREATE INDEX idx_skills_nombre ON skills(nombre_normalizado);
CREATE INDEX idx_skills_tipo ON skills(tipo);
CREATE INDEX idx_skills_categoria ON skills(categoria);
CREATE INDEX idx_skills_esco ON skills(esco_skill_uri);
CREATE INDEX idx_skills_frecuencia_total ON skills(frecuencia_total DESC);
CREATE INDEX idx_skills_frecuencia_actual ON skills(frecuencia_actual DESC);

-- Índice compuesto para búsqueda por tipo y frecuencia
CREATE INDEX idx_skills_tipo_frecuencia ON skills(tipo, frecuencia_total DESC);


-- =====================================================================
-- TABLA 6: ofertas_skills
-- =====================================================================
-- Relación N:M entre ofertas y skills
-- Permite queries tipo "ofertas que requieren Python Y SQL"
-- =====================================================================

CREATE TABLE IF NOT EXISTS ofertas_skills (
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

-- Índices para ofertas_skills
CREATE INDEX idx_ofertas_skills_oferta ON ofertas_skills(oferta_id);
CREATE INDEX idx_ofertas_skills_skill ON ofertas_skills(skill_id);
CREATE INDEX idx_ofertas_skills_version ON ofertas_skills(version_id);
CREATE INDEX idx_ofertas_skills_nivel ON ofertas_skills(nivel);
CREATE INDEX idx_ofertas_skills_tipo ON ofertas_skills(tipo_requisito);
CREATE INDEX idx_ofertas_skills_confidence ON ofertas_skills(confidence_score DESC);

-- Índice compuesto para la query más frecuente: skills de una oferta en versión específica
CREATE INDEX idx_ofertas_skills_lookup ON ofertas_skills(oferta_id, version_id, skill_id);


-- =====================================================================
-- TABLA 7: keywords_performance_v2
-- =====================================================================
-- Performance de keywords en scraping (formalización de tabla actual)
-- Incluye enriquecimiento con ESCO
-- =====================================================================

CREATE TABLE IF NOT EXISTS keywords_performance_v2 (
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

-- Índices para keywords_performance_v2
CREATE INDEX idx_kw_perf_v2_session ON keywords_performance_v2(scraping_session_id);
CREATE INDEX idx_kw_perf_v2_keyword ON keywords_performance_v2(keyword);
CREATE INDEX idx_kw_perf_v2_esco_occ ON keywords_performance_v2(esco_occupation_uri);
CREATE INDEX idx_kw_perf_v2_esco_skill ON keywords_performance_v2(esco_skill_uri);
CREATE INDEX idx_kw_perf_v2_date ON keywords_performance_v2(execution_date DESC);
CREATE INDEX idx_kw_perf_v2_ofertas ON keywords_performance_v2(ofertas_encontradas DESC);


-- =====================================================================
-- TABLA 8: ofertas_historial
-- =====================================================================
-- Tracking de cambios en ofertas (auditoría completa)
-- Permite análisis temporal: "¿cuándo cambió el salario de esta oferta?"
-- =====================================================================

CREATE TABLE IF NOT EXISTS ofertas_historial (
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

-- Índices para ofertas_historial
CREATE INDEX idx_historial_oferta ON ofertas_historial(oferta_id);
CREATE INDEX idx_historial_fecha ON ofertas_historial(fecha_modificacion DESC);
CREATE INDEX idx_historial_campo ON ofertas_historial(campo_modificado);
CREATE INDEX idx_historial_session ON ofertas_historial(scraping_session_id);
CREATE INDEX idx_historial_change_type ON ofertas_historial(change_type);

-- Índice compuesto para la query más frecuente: historial de una oferta ordenado por fecha
CREATE INDEX idx_historial_oferta_fecha ON ofertas_historial(oferta_id, fecha_modificacion DESC);


-- =====================================================================
-- VISTAS ÚTILES
-- =====================================================================
-- Vistas para facilitar queries comunes
-- =====================================================================

-- Vista: Ofertas con NLP de la versión activa
CREATE VIEW IF NOT EXISTS v_ofertas_nlp_active AS
SELECT
    o.id_oferta,
    o.titulo,
    o.empresa,
    o.localizacion,
    n.experiencia_min_anios,
    n.nivel_educativo,
    n.jornada_laboral,
    n.confidence_score,
    nv.version_name,
    n.extraction_timestamp
FROM ofertas o
INNER JOIN ofertas_nlp_v2 n ON o.id_oferta = n.id_oferta
INNER JOIN nlp_versions nv ON n.version_id = nv.id
WHERE nv.is_active = 1;

-- Vista: Top skills más demandados (últimos 30 días)
CREATE VIEW IF NOT EXISTS v_top_skills_30d AS
SELECT
    s.nombre,
    s.tipo,
    s.categoria,
    COUNT(DISTINCT os.oferta_id) as num_ofertas,
    COUNT(CASE WHEN os.tipo_requisito = 'excluyente' THEN 1 END) as veces_excluyente,
    AVG(os.confidence_score) as avg_confidence
FROM skills s
INNER JOIN ofertas_skills os ON s.id = os.skill_id
INNER JOIN ofertas o ON os.oferta_id = o.id_oferta
WHERE o.scrapeado_en >= DATE('now', '-30 days')
  AND os.version_id = (SELECT id FROM nlp_versions WHERE is_active = 1)
GROUP BY s.id, s.nombre, s.tipo, s.categoria
ORDER BY num_ofertas DESC;

-- Vista: Sesiones de scraping recientes con stats
CREATE VIEW IF NOT EXISTS v_scraping_sessions_recent AS
SELECT
    s.session_uuid,
    s.start_time,
    s.end_time,
    s.source,
    s.mode,
    s.ofertas_total,
    s.ofertas_nuevas,
    s.status,
    s.total_time_seconds,
    ROUND(s.ofertas_total * 1.0 / NULLIF(s.total_time_seconds, 0), 2) as ofertas_por_segundo
FROM scraping_sessions s
WHERE s.start_time >= DATE('now', '-7 days')
ORDER BY s.start_time DESC;


-- =====================================================================
-- TRIGGERS
-- =====================================================================

-- Trigger: Actualizar frecuencia de skills cuando se inserta en ofertas_skills
CREATE TRIGGER IF NOT EXISTS trg_ofertas_skills_insert_freq
AFTER INSERT ON ofertas_skills
BEGIN
    UPDATE skills
    SET frecuencia_total = frecuencia_total + 1,
        ultima_aparicion = datetime('now'),
        updated_at = datetime('now')
    WHERE id = NEW.skill_id;

    -- Si no tiene primera_aparicion, establecerla
    UPDATE skills
    SET primera_aparicion = datetime('now')
    WHERE id = NEW.skill_id AND primera_aparicion IS NULL;
END;

-- Trigger: Actualizar stats de nlp_versions cuando se inserta en ofertas_nlp_v2
CREATE TRIGGER IF NOT EXISTS trg_ofertas_nlp_v2_insert_stats
AFTER INSERT ON ofertas_nlp_v2
BEGIN
    UPDATE nlp_versions
    SET total_ofertas_procesadas = total_ofertas_procesadas + 1,
        avg_confidence_score = (
            SELECT AVG(confidence_score)
            FROM ofertas_nlp_v2
            WHERE version_id = NEW.version_id
        )
    WHERE id = NEW.version_id;
END;

-- Trigger: Registrar cambios en ofertas_historial cuando se actualiza ofertas
-- Nota: Este trigger se creará después de migrar la tabla ofertas


-- =====================================================================
-- METADATA DE LA MIGRACIÓN
-- =====================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    applied_by TEXT,
    execution_time_seconds REAL
);

-- Registrar esta migración
INSERT INTO schema_migrations (version, description, applied_by)
VALUES ('2.0.0', 'Esquema v2: Versionado NLP, normalización de skills, tracking histórico', 'create_schema_v2.sql');


-- =====================================================================
-- FINALIZACIÓN
-- =====================================================================

-- Verificar integridad
PRAGMA integrity_check;

-- Estadísticas finales
SELECT
    '✓ Esquema v2.0 creado exitosamente' as status,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%') as num_tables,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%') as num_indexes,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='trigger') as num_triggers,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='view') as num_views;
