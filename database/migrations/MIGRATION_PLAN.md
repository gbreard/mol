# PLAN INTEGRADO DE MIGRACIÓN - Database v2.0
## Sistema de Inteligencia del Mercado Laboral Argentino

**Versión**: 2.0.0
**Fecha de creación**: 2025-11-02
**Estado**: En preparación
**Fuente primaria**: Bumeran (expandible a otras fuentes en futuro)

---

## TABLA DE CONTENIDOS

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Estado Actual y Problemas Identificados](#2-estado-actual-y-problemas-identificados)
3. [Database v2.0 - Arquitectura Completa](#3-database-v20---arquitectura-completa)
4. [Estrategia de Migración](#4-estrategia-de-migración)
5. [Pipeline End-to-End Bumeran](#5-pipeline-end-to-end-bumeran)
6. [Fixes Críticos](#6-fixes-críticos)
7. [Timeline de Implementación](#7-timeline-de-implementación)
8. [Dashboard Integration](#8-dashboard-integration)
9. [Criterios de Validación](#9-criterios-de-validación)
10. [Rollback Plan](#10-rollback-plan)

---

## 1. VISIÓN GENERAL DEL SISTEMA

El sistema es una **plataforma de aprendizaje multi-capa** para análisis del mercado laboral argentino:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA 1: SCRAPING                             │
│  Bumeran → Keywords → Incremental tracking → Raw offers         │
│  Scheduler: Lunes y Jueves 8:00 AM (PRODUCCIÓN - NO ROMPER)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA 2: NLP EXTRACTION                        │
│  Regex v3.7 (70-80%) + LLM v4.0 (95%+) → Structured data        │
│  Extrae: experiencia, educación, skills, salario, etc.          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA 3: ESCO MATCHING                         │
│  RDF Ontology (17 tablas) → Semantic enrichment                 │
│  Occupations + Skills + BGE-M3 embeddings                        │
│  BUG CRÍTICO: 6 skills en DB (esperado: 13,890)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA 4: VISUALIZACIÓN                         │
│  • Dashboard Operativo (Dash) - localhost - Monitoreo calidad   │
│  • Dashboard Público (Shiny) - shinyapps.io - Analytics         │
└─────────────────────────────────────────────────────────────────┘
```

### Objetivo de la Migración

Diseñar una base de datos relacional v2.0 que:
- **Soporte el pipeline completo** sin necesidad de parches constantes
- **Preserve la producción** (scheduler Monday/Thursday 8:00 AM sigue funcionando)
- **Habilite versioning** de NLP (comparar regex vs LLM)
- **Normalice datos** (skills en tablas relacionales, no JSON)
- **Integre ESCO** correctamente (fix bug de 6 → 13,890 skills)
- **Permita análisis temporal** (tracking de cambios en ofertas)
- **Sea visible** en dashboard operativo en tiempo real

---

## 2. ESTADO ACTUAL Y PROBLEMAS IDENTIFICADOS

### 2.1 Base de Datos Actual (v1.0)

**Archivo**: `D:/OEDE/Webscrapping/database/bumeran_scraping.db`
**Tamaño**: ~30 MB
**Total ofertas**: 5,479
**Total tablas**: 22

#### Tablas Core v1.0

```
ofertas (38 columnas)
├── id_oferta (PK, TEXT)
├── titulo, descripcion, empresa
├── fecha_publicacion (3 formatos distintos!)
├── provincia, localidad
├── area_trabajo
└── ... (35 campos más)

ofertas_nlp
├── id_oferta (TEXT, sin FK formal)
├── experiencia_min_anios, experiencia_max_anios
├── nivel_educativo, estado_educativo
├── skills_tecnicas_list (JSON string)  ← PROBLEMA
├── soft_skills_list (JSON string)      ← PROBLEMA
├── nlp_version (TEXT, sobrescribe)     ← PROBLEMA
└── nlp_confidence_score

ofertas_esco_matching
├── oferta_id (TEXT, sin FK formal)
├── matched_occupation_uri
├── occupation_confidence
├── matched_skills_uris (JSON)          ← PROBLEMA
└── skills_confidence
```

#### 17 Tablas ESCO (RDF Ontology)

```
# Occupations
esco_occupations                    (Conceptos de ocupaciones)
esco_occupation_labels_es           (Labels en español)
esco_occupation_descriptions        (Descripciones)

# Skills
esco_skills                         (BUG: solo 6 registros, debería tener ~13,890)
esco_skill_labels_es
esco_skill_descriptions

# Relaciones semánticas
esco_occupation_essential_skills    (N:M occupation ↔ essential skills)
esco_occupation_optional_skills     (N:M occupation ↔ optional skills)
esco_occupation_broader             (Jerarquía: broader concepts)
esco_occupation_narrower            (Jerarquía: narrower concepts)
esco_skill_broader
esco_skill_narrower

# Localización argentina
diccionario_arg_esco_occupations    (Títulos AR → ESCO)
diccionario_arg_esco_skills         (Skills AR → ESCO)

# Análisis
ofertas_esco_matching               (Ofertas → ESCO matches)
esco_gap_analysis                   (Skills en ofertas pero no en ESCO)
```

### 2.2 Problemas Críticos Identificados

#### ❌ PROBLEMA 1: Skills en JSON (No Queryable)

```sql
-- IMPOSIBLE hacer esta query:
SELECT COUNT(*) FROM ofertas_nlp WHERE skills_tecnicas_list LIKE '%Python%';

-- Razón: skills_tecnicas_list = '["Python", "Django", "PostgreSQL"]' (JSON string)
```

**Impacto**: No se puede analizar "¿Cuántas ofertas requieren Python?" sin parsear JSON en app.

#### ❌ PROBLEMA 2: NLP Version Sobrescribe Datos

```sql
-- Si re-ejecutamos NLP con nueva versión:
UPDATE ofertas_nlp SET nlp_version = 'v4.0', skills_tecnicas_list = '...' WHERE id_oferta = '123';

-- PERDEMOS la versión anterior (v3.7) y sus resultados
```

**Impacto**: No podemos comparar "¿LLM v4.0 extrajo más skills que Regex v3.7?"

#### ❌ PROBLEMA 3: Sin Tracking de Cambios

```sql
-- Si una oferta cambia de título o sueldo:
INSERT OR REPLACE INTO ofertas VALUES (...);

-- PERDEMOS el valor anterior, no hay historial
```

**Impacto**: No podemos analizar "¿Cuántas ofertas aumentaron el salario en los últimos 30 días?"

#### ❌ PROBLEMA 4: Redundancia de Fechas (9 columnas!)

```
fecha_publicacion      (TEXT ISO)
fecha_publicacion_ts   (INTEGER timestamp)
fecha_publicacion_dt   (TEXT datetime format)
fecha_scraping         (TEXT ISO)
fecha_scraping_ts      (INTEGER)
fecha_scraping_dt      (TEXT)
fecha_actualizacion    (TEXT)
fecha_actualizacion_ts (INTEGER)
fecha_actualizacion_dt (TEXT)
```

**Impacto**: Confusión, desperdicio de espacio, 3 formatos para el mismo dato.

#### ❌ PROBLEMA 5: ESCO Skills Bug CRÍTICO

```sql
SELECT COUNT(*) FROM esco_skills;
-- Resultado: 6 (debería ser ~13,890)
```

**Causa**: Bug en `populate_esco_from_rdf.py` líneas 200-300 (SPARQL query incompleto)
**Impacto**: ESCO matching completamente inútil (no hay skills para matchear)

#### ❌ PROBLEMA 6: Sin Foreign Keys Formales

```sql
-- No hay CASCADE, no hay validación referencial
id_oferta en ofertas_nlp puede referenciar oferta inexistente
```

**Impacto**: Posibles registros huérfanos, inconsistencias.

---

## 3. DATABASE v2.0 - ARQUITECTURA COMPLETA

### 3.1 Principios de Diseño

1. **Normalización**: Skills, keywords, empresas en tablas separadas con N:M
2. **Versionado**: Múltiples versiones NLP por oferta (comparación A/B)
3. **Auditoría**: Tracking completo de cambios con ofertas_historial
4. **Integridad**: Foreign keys con CASCADE explícitos
5. **Performance**: Índices en campos de búsqueda frecuente
6. **ESCO-first**: Integración nativa con ontología RDF
7. **Backward-compatible**: v1 schema se mantiene para scheduler

### 3.2 Esquema Completo v2.0

#### CAPA 1: SCRAPING (4 tablas nuevas)

```sql
-- =====================================================================
-- TABLA: scraping_sessions
-- Tracking de cada ejecución del scraper
-- =====================================================================
CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_uuid TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,              -- 'bumeran', 'indeed' (futuro)
    mode TEXT NOT NULL,                -- 'full', 'incremental'
    start_time TEXT NOT NULL,
    end_time TEXT,
    ofertas_total INTEGER DEFAULT 0,
    ofertas_nuevas INTEGER DEFAULT 0,
    ofertas_actualizadas INTEGER DEFAULT 0,
    keywords_used TEXT,                -- JSON array de keywords usadas
    status TEXT DEFAULT 'running',     -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sessions_source ON scraping_sessions(source);
CREATE INDEX idx_sessions_start ON scraping_sessions(start_time);

-- =====================================================================
-- TABLA: ofertas_raw
-- Inmutable audit log - NUNCA se modifica, solo INSERT
-- =====================================================================
CREATE TABLE ofertas_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,
    scraping_session_id INTEGER NOT NULL,
    raw_json TEXT NOT NULL,            -- JSON completo de la oferta
    content_hash TEXT,                 -- SHA256 para detectar cambios
    scraped_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (scraping_session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_raw_oferta ON ofertas_raw(id_oferta);
CREATE INDEX idx_raw_session ON ofertas_raw(scraping_session_id);
CREATE INDEX idx_raw_hash ON ofertas_raw(content_hash);

-- =====================================================================
-- TABLA: ofertas_v2 (normalized)
-- Tabla principal normalizada, reemplaza 38 columnas de ofertas v1
-- =====================================================================
CREATE TABLE ofertas_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT UNIQUE NOT NULL,    -- ID de Bumeran
    titulo TEXT NOT NULL,
    descripcion TEXT,
    empresa_id INTEGER,                -- FK a empresas (nueva tabla)
    url TEXT,
    provincia TEXT,
    localidad TEXT,
    area_trabajo TEXT,
    tipo_contrato TEXT,                -- 'full-time', 'part-time', etc.
    modalidad_trabajo TEXT,            -- 'presencial', 'remoto', 'híbrido'

    -- Fechas (solo 3, no 9!)
    fecha_publicacion TEXT,
    fecha_actualizacion TEXT,
    primera_vez_scrapeada TEXT,

    -- Estado
    is_active INTEGER DEFAULT 1,       -- 0 = oferta expiró

    -- Metadata
    source TEXT DEFAULT 'bumeran',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL
);

CREATE INDEX idx_ofertas_v2_id_oferta ON ofertas_v2(id_oferta);
CREATE INDEX idx_ofertas_v2_titulo ON ofertas_v2(titulo);
CREATE INDEX idx_ofertas_v2_empresa ON ofertas_v2(empresa_id);
CREATE INDEX idx_ofertas_v2_provincia ON ofertas_v2(provincia);
CREATE INDEX idx_ofertas_v2_fecha_pub ON ofertas_v2(fecha_publicacion);

-- =====================================================================
-- TABLA: empresas (nueva)
-- Normalización de empresas
-- =====================================================================
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    sector TEXT,                       -- 'Tecnología', 'Finanzas', etc.
    tamanio TEXT,                      -- 'startup', 'pyme', 'grande'
    ofertas_count INTEGER DEFAULT 0,   -- Denormalizado para performance
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_empresas_nombre ON empresas(nombre);
```

#### CAPA 2: NLP EXTRACTION (5 tablas nuevas)

```sql
-- =====================================================================
-- TABLA: nlp_versions
-- Catálogo de versiones NLP (permite comparación)
-- =====================================================================
CREATE TABLE nlp_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_name TEXT UNIQUE NOT NULL,  -- 'v3.7-regex-aggressive'
    model_type TEXT NOT NULL,           -- 'regex', 'llm', 'hybrid'
    model_details TEXT,                 -- JSON con config del modelo
    is_active INTEGER DEFAULT 0,        -- Solo 1 activa a la vez
    avg_confidence_score REAL,          -- Calculado periódicamente
    created_at TEXT DEFAULT (datetime('now'))
);

INSERT INTO nlp_versions (version_name, model_type, is_active) VALUES
    ('v2.0-regex-basic', 'regex', 0),
    ('v3.7-regex-aggressive', 'regex', 0),
    ('v4.0-llm-llama3', 'llm', 0),
    ('v4.0-hybrid-regex-llm', 'hybrid', 1);

-- =====================================================================
-- TABLA: ofertas_nlp_v2
-- Versionado de extracciones NLP (múltiples versiones por oferta)
-- =====================================================================
CREATE TABLE ofertas_nlp_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,
    version_id INTEGER NOT NULL,

    -- Experiencia
    experiencia_min_anios INTEGER,
    experiencia_max_anios INTEGER,
    experiencia_area TEXT,

    -- Educación
    nivel_educativo TEXT,              -- 'secundario', 'terciario', 'universitario', 'posgrado'
    estado_educativo TEXT,             -- 'completo', 'en_curso', 'incompleto'
    carrera_especifica TEXT,
    titulo_excluyente INTEGER,         -- Boolean: 1 = excluyente

    -- Idiomas
    idioma_principal TEXT,
    nivel_idioma_principal TEXT,
    idioma_secundario TEXT,
    nivel_idioma_secundario TEXT,

    -- Salario (extraído de descripción)
    salario_min REAL,
    salario_max REAL,
    moneda TEXT,

    -- Jornada
    jornada_laboral TEXT,              -- 'full-time', 'part-time', 'freelance'
    horario_flexible INTEGER,          -- Boolean

    -- Metadata
    confidence_score REAL,             -- Score global de esta extracción
    extracted_at TEXT DEFAULT (datetime('now')),
    extraction_time_ms INTEGER,        -- Tiempo que tomó el procesamiento

    UNIQUE(id_oferta, version_id),
    FOREIGN KEY (version_id) REFERENCES nlp_versions(id) ON DELETE CASCADE
);

CREATE INDEX idx_nlp_v2_oferta ON ofertas_nlp_v2(id_oferta);
CREATE INDEX idx_nlp_v2_version ON ofertas_nlp_v2(version_id);
CREATE INDEX idx_nlp_v2_confidence ON ofertas_nlp_v2(confidence_score);

-- =====================================================================
-- TABLA: skills (nueva - normalización)
-- Catálogo unificado de skills técnicas
-- =====================================================================
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,                -- 'tecnica', 'soft', 'certificacion'
    categoria TEXT,                    -- 'programación', 'base de datos', etc.
    esco_skill_uri TEXT,               -- Link a ESCO (si existe)
    frecuencia_total INTEGER DEFAULT 0,-- Cuántas ofertas la mencionan
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_skills_nombre ON skills(nombre);
CREATE INDEX idx_skills_tipo ON skills(tipo);
CREATE INDEX idx_skills_esco ON skills(esco_skill_uri);

-- =====================================================================
-- TABLA: ofertas_skills (N:M)
-- Relación ofertas ↔ skills (VERSIONADA por NLP)
-- =====================================================================
CREATE TABLE ofertas_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oferta_id TEXT NOT NULL,
    skill_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,       -- Versión NLP que extrajo esta skill
    nivel TEXT,                        -- 'basico', 'intermedio', 'avanzado', 'excluyente'
    es_excluyente INTEGER DEFAULT 0,   -- Boolean

    UNIQUE(oferta_id, skill_id, version_id),
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES nlp_versions(id) ON DELETE CASCADE
);

CREATE INDEX idx_ofertas_skills_oferta ON ofertas_skills(oferta_id);
CREATE INDEX idx_ofertas_skills_skill ON ofertas_skills(skill_id);
CREATE INDEX idx_ofertas_skills_version ON ofertas_skills(version_id);

-- =====================================================================
-- TABLA: soft_skills (nueva)
-- Catálogo de soft skills
-- =====================================================================
CREATE TABLE soft_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    categoria TEXT,                    -- 'liderazgo', 'comunicación', etc.
    frecuencia_total INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- N:M entre ofertas y soft_skills (similar a ofertas_skills)
CREATE TABLE ofertas_soft_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oferta_id TEXT NOT NULL,
    soft_skill_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,

    UNIQUE(oferta_id, soft_skill_id, version_id),
    FOREIGN KEY (soft_skill_id) REFERENCES soft_skills(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES nlp_versions(id) ON DELETE CASCADE
);
```

#### CAPA 3: ESCO INTEGRATION (mantiene 17 tablas existentes + mejoras)

```sql
-- =====================================================================
-- Las 17 tablas ESCO existentes se MANTIENEN:
-- =====================================================================
-- esco_occupations
-- esco_occupation_labels_es
-- esco_occupation_descriptions
-- esco_skills                           ← FIX: 6 → 13,890 registros
-- esco_skill_labels_es
-- esco_skill_descriptions
-- esco_occupation_essential_skills
-- esco_occupation_optional_skills
-- esco_occupation_broader
-- esco_occupation_narrower
-- esco_skill_broader
-- esco_skill_narrower
-- diccionario_arg_esco_occupations
-- diccionario_arg_esco_skills
-- ofertas_esco_matching
-- esco_gap_analysis

-- MEJORA: Agregar versioning a ofertas_esco_matching
ALTER TABLE ofertas_esco_matching ADD COLUMN matching_version TEXT DEFAULT 'v1.0';
ALTER TABLE ofertas_esco_matching ADD COLUMN matched_at TEXT DEFAULT (datetime('now'));

-- NUEVA TABLA: esco_matching_versions
CREATE TABLE esco_matching_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_name TEXT UNIQUE NOT NULL,  -- 'v1.0-bge-m3-base'
    embedding_model TEXT,               -- 'BGE-M3', 'mpnet', etc.
    matching_algorithm TEXT,            -- 'cosine-similarity', 'semantic-search'
    threshold REAL,                     -- Umbral de confianza mínimo
    is_active INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### CAPA 4: AUDITORÍA Y ANALYTICS (2 tablas nuevas)

```sql
-- =====================================================================
-- TABLA: ofertas_historial
-- Tracking de TODOS los cambios en ofertas
-- =====================================================================
CREATE TABLE ofertas_historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oferta_id TEXT NOT NULL,
    campo_modificado TEXT NOT NULL,    -- 'titulo', 'descripcion', 'salario_min', etc.
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha_modificacion TEXT DEFAULT (datetime('now')),
    changed_by TEXT DEFAULT 'system',  -- 'scraper', 'nlp', 'manual'

    FOREIGN KEY (oferta_id) REFERENCES ofertas_v2(id_oferta) ON DELETE CASCADE
);

CREATE INDEX idx_historial_oferta ON ofertas_historial(oferta_id);
CREATE INDEX idx_historial_campo ON ofertas_historial(campo_modificado);
CREATE INDEX idx_historial_fecha ON ofertas_historial(fecha_modificacion);

-- =====================================================================
-- TABLA: analytics_cache
-- Cache de queries pesadas para dashboards
-- =====================================================================
CREATE TABLE analytics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_key TEXT UNIQUE NOT NULL,    -- 'top_skills_last_30_days'
    query_result TEXT NOT NULL,        -- JSON con resultado
    last_updated TEXT DEFAULT (datetime('now')),
    expires_at TEXT,                   -- TTL para invalidación
    computation_time_ms INTEGER
);

CREATE INDEX idx_cache_key ON analytics_cache(query_key);
CREATE INDEX idx_cache_expires ON analytics_cache(expires_at);
```

### 3.3 Resumen de Tablas v2.0

**Total tablas v2.0**: 30 (22 v1 se mantienen + 8 nuevas)

| Categoría | Tablas | Estado |
|-----------|--------|--------|
| **v1 Core (mantener para scheduler)** | ofertas, ofertas_nlp (38 cols) | MANTENER sin modificar |
| **v2 Scraping** | scraping_sessions, ofertas_raw, ofertas_v2, empresas | NUEVAS |
| **v2 NLP** | nlp_versions, ofertas_nlp_v2, skills, ofertas_skills, soft_skills, ofertas_soft_skills | NUEVAS |
| **ESCO (existentes)** | 17 tablas ESCO | MANTENER + fix bug skills |
| **Auditoría** | ofertas_historial, analytics_cache | NUEVAS |

---

## 4. ESTRATEGIA DE MIGRACIÓN

### 4.1 Principio: DUAL-WRITE (No Romper Producción)

```
┌─────────────────────────────────────────────┐
│          Scheduler (Lun/Jue 8:00 AM)        │
│             run_scheduler.py                 │
└─────────────────┬───────────────────────────┘
                  ↓
         ┌────────────────┐
         │  db_manager.py │  ← MODIFICAR AQUÍ
         └────────┬───────┘
                  ↓
    ┌─────────────┴─────────────┐
    ↓                           ↓
┌─────────┐              ┌─────────────┐
│ WRITE V1│ (CRITICAL)   │  WRITE V2   │ (best effort)
│ ofertas │              │ ofertas_v2  │
│ 38 cols │              │ ofertas_raw │
└─────────┘              │scraping_sess│
    ↓                    └─────────────┘
    ↓                           ↓
[PRODUCCIÓN]              [MIGRACIÓN]
Scheduler sigue           Validación en
funcionando               paralelo
```

### 4.2 Modificación de db_manager.py

**Ubicación**: `D:/OEDE/Webscrapping/database/db_manager.py`

```python
class DatabaseManager:
    """
    DUAL-WRITE: Escribe a v1 (producción) Y v2 (nueva arquitectura)
    """

    def __init__(self, db_path='bumeran_scraping.db'):
        self.conn = sqlite3.connect(db_path)
        self.v2_enabled = True  # Flag para habilitar/deshabilitar v2

    def insert_ofertas(self, ofertas_df, session_info=None):
        """
        Inserta ofertas en AMBOS schemas: v1 y v2

        Args:
            ofertas_df: DataFrame con ofertas scrapeadas
            session_info: Dict con info de scraping_session (para v2)

        Returns:
            (v1_count, v2_count): Tupla con registros insertados
        """
        cursor = self.conn.cursor()
        v1_inserted = 0
        v2_inserted = 0

        try:
            # ========================================
            # FASE 1: WRITE TO V1 (PRODUCCIÓN)
            # SI ESTO FALLA → RAISE ERROR
            # ========================================
            for _, row in ofertas_df.iterrows():
                # Convertir a formato v1 (38 columnas)
                v1_data = self._to_v1_format(row)

                cursor.execute("""
                    INSERT OR REPLACE INTO ofertas (
                        id_oferta, titulo, descripcion, ...  -- 38 columnas
                    ) VALUES (?, ?, ?, ...)
                """, v1_data)

                v1_inserted += 1

            self.conn.commit()
            logger.info(f"[V1] {v1_inserted} ofertas insertadas (PRODUCCIÓN)")

            # ========================================
            # FASE 2: WRITE TO V2 (NUEVA ARQUITECTURA)
            # SI ESTO FALLA → LOG WARNING, NO ROMPER
            # ========================================
            if self.v2_enabled:
                try:
                    # 2.1 Crear scraping_session
                    session_id = self._create_scraping_session(session_info)

                    for _, row in ofertas_df.iterrows():
                        # 2.2 ofertas_raw (immutable audit log)
                        self._insert_ofertas_raw(row, session_id)

                        # 2.3 ofertas_v2 (normalized)
                        self._insert_ofertas_v2(row)

                        # 2.4 empresas (si no existe)
                        if row.get('empresa'):
                            self._upsert_empresa(row['empresa'])

                        v2_inserted += 1

                    self.conn.commit()
                    logger.info(f"[V2] {v2_inserted} ofertas insertadas (MIGRACIÓN)")

                except Exception as e:
                    logger.warning(f"[V2] Inserción falló: {e}")
                    logger.warning("[V2] Continuando solo con v1...")
                    # NO raise - v1 ya tiene los datos

            return (v1_inserted, v2_inserted)

        except Exception as e:
            self.conn.rollback()
            logger.critical(f"[V1] Inserción CRÍTICA falló: {e}")
            raise  # Esto rompe el scheduler → necesario para no perder datos

    def _create_scraping_session(self, session_info):
        """Crea registro en scraping_sessions"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO scraping_sessions (
                session_uuid, source, mode, start_time, keywords_used
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            session_info.get('uuid'),
            session_info.get('source', 'bumeran'),
            session_info.get('mode', 'incremental'),
            session_info.get('start_time'),
            json.dumps(session_info.get('keywords', []))
        ))

        return cursor.lastrowid

    def _insert_ofertas_raw(self, row, session_id):
        """Inserta en ofertas_raw (audit log inmutable)"""
        import hashlib

        cursor = self.conn.cursor()

        # Calcular hash del contenido
        raw_json = row.to_json()
        content_hash = hashlib.sha256(raw_json.encode()).hexdigest()

        cursor.execute("""
            INSERT INTO ofertas_raw (
                id_oferta, scraping_session_id, raw_json, content_hash
            ) VALUES (?, ?, ?, ?)
        """, (
            row['id_oferta'],
            session_id,
            raw_json,
            content_hash
        ))

    def _insert_ofertas_v2(self, row):
        """Inserta en ofertas_v2 (normalizado)"""
        cursor = self.conn.cursor()

        # Obtener empresa_id
        empresa_id = None
        if row.get('empresa'):
            empresa_id = self._get_or_create_empresa(row['empresa'])

        cursor.execute("""
            INSERT OR REPLACE INTO ofertas_v2 (
                id_oferta, titulo, descripcion, empresa_id,
                provincia, localidad, area_trabajo,
                fecha_publicacion, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['id_oferta'],
            row['titulo'],
            row['descripcion'],
            empresa_id,
            row.get('provincia'),
            row.get('localidad'),
            row.get('area_trabajo'),
            row.get('fecha_publicacion'),
            'bumeran'
        ))
```

### 4.3 Constraints de Producción (NO ROMPER)

**Archivos CRÍTICOS que NO se pueden modificar**:

1. `run_scheduler.py` - NO TOCAR (scheduler production)
2. `bumeran_scraped_ids.json` - NO CORROMPER (12,847 IDs trackeados)
3. Tabla `ofertas` (38 columnas) - NO RENOMBRAR
4. Tabla `ofertas_nlp` - NO ELIMINAR
5. Primary key `id_oferta` - NO MODIFICAR tipo

**Lo que SÍ se puede modificar**:
- `db_manager.py` - Agregar dual-write
- `create_schema_v2.sql` - Aplicar (nuevas tablas, no afecta v1)
- Dashboard operativo - Agregar tabs de migración

---

## 5. PIPELINE END-TO-END BUMERAN

### 5.1 Flujo Completo (Estado Objetivo)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 1: SCRAPING                                                    │
│─────────────────────────────────────────────────────────────────────│
│ Scheduler → Keywords → Bumeran.com.ar → Ofertas HTML               │
│   ↓                                                                 │
│ db_manager.py (DUAL-WRITE)                                          │
│   ├→ V1: ofertas (38 cols)         [PRODUCCIÓN - SCHEDULER]        │
│   └→ V2: ofertas_raw + ofertas_v2  [MIGRACIÓN - VALIDACIÓN]        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 2: NLP EXTRACTION                                              │
│─────────────────────────────────────────────────────────────────────│
│ process_nlp_from_db_v4.py --mode hybrid                             │
│   ├→ Regex v3.7 (fast, 70-80%)                                     │
│   └→ LLM v4.0 (solo campos vacíos, 95%+)                           │
│                                                                     │
│ Destino:                                                            │
│   ├→ V1: ofertas_nlp (sobrescribe)                                 │
│   └→ V2: ofertas_nlp_v2 (versioned)                                │
│         ├→ skills → Normalizadas en ofertas_skills                 │
│         └→ soft_skills → ofertas_soft_skills                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 3: ESCO MATCHING                                               │
│─────────────────────────────────────────────────────────────────────│
│ [PRIMERO: FIX BUG] populate_esco_from_rdf.py                        │
│   Fix SPARQL query → 6 skills a 13,890 skills ✓                    │
│                                                                     │
│ esco_hybrid_matcher.py                                              │
│   ├→ BGE-M3 embeddings                                             │
│   ├→ Cosine similarity                                             │
│   └→ Threshold 0.7                                                 │
│                                                                     │
│ Destino: ofertas_esco_matching                                      │
│   ├→ matched_occupation_uri                                        │
│   ├→ matched_skills_uris                                           │
│   └→ confidence scores                                             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 4: VISUALIZACIÓN                                               │
│─────────────────────────────────────────────────────────────────────│
│ A. Dashboard Operativo (Dash - localhost:8050)                      │
│    ├→ Tab: Calidad NLP (v1 vs v2 comparison)                       │
│    ├→ Tab: ESCO Matching Coverage                                  │
│    ├→ Tab: Migración Status (v1 vs v2 sync)                        │
│    └→ Tab: Scraping Sessions                                       │
│                                                                     │
│ B. Dashboard Público (Shiny - shinyapps.io)                         │
│    ├→ Análisis de mercado laboral                                  │
│    ├→ Skills más demandadas                                        │
│    ├→ Salarios por provincia                                       │
│    └→ Tendencias temporales                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Validación de Cada Fase

#### Checkpoint 1: Post-Scraping

```sql
-- ¿Se escribió en ambos schemas?
SELECT
    (SELECT COUNT(*) FROM ofertas) as v1_count,
    (SELECT COUNT(*) FROM ofertas_v2) as v2_count,
    (SELECT COUNT(*) FROM ofertas_raw) as raw_count;

-- Esperar: v1_count = v2_count = raw_count

-- ¿Scraping session creada?
SELECT * FROM scraping_sessions ORDER BY start_time DESC LIMIT 1;
```

#### Checkpoint 2: Post-NLP

```sql
-- ¿Versiones NLP creadas?
SELECT version_name, COUNT(*) as ofertas_procesadas
FROM ofertas_nlp_v2
JOIN nlp_versions ON ofertas_nlp_v2.version_id = nlp_versions.id
GROUP BY version_name;

-- Esperar:
-- v3.7-regex-aggressive  | 5479
-- v4.0-hybrid-regex-llm  | 5479

-- ¿Skills normalizadas?
SELECT COUNT(*) FROM skills;
SELECT COUNT(*) FROM ofertas_skills;

-- Esperar: skills > 200, ofertas_skills > 10000
```

#### Checkpoint 3: Post-ESCO

```sql
-- ¿ESCO skills corregidas?
SELECT COUNT(*) FROM esco_skills;
-- Esperar: ~13,890 (NO 6)

-- ¿Matching coverage?
SELECT
    COUNT(DISTINCT oferta_id) * 100.0 / (SELECT COUNT(*) FROM ofertas_v2) as coverage
FROM ofertas_esco_matching;

-- Esperar: > 85%
```

---

## 6. FIXES CRÍTICOS

### 6.1 ESCO Skills Bug (BLOCKING)

**Archivo**: `D:/OEDE/Webscrapping/database/populate_esco_from_rdf.py`
**Líneas**: ~200-300 (sección de skills extraction)

**Problema**:
```sql
SELECT COUNT(*) FROM esco_skills;
-- Actual: 6
-- Esperado: ~13,890
```

**Fix requerido**:

```python
# populate_esco_from_rdf.py - ANTES (Bug)

def extract_skills(self, graph):
    """BUG: Query SPARQL incompleto"""
    query = """
        PREFIX esco: <http://data.europa.eu/esco/model#>
        SELECT ?skill ?label
        WHERE {
            ?skill a esco:Skill .
            ?skill skos:prefLabel ?label .
            FILTER(lang(?label) = "en")
        }
        LIMIT 10  # ← BUG: Solo 10 registros
    """

    results = graph.query(query)
    # Solo procesa 10, pero luego algo más falla y solo quedan 6

# populate_esco_from_rdf.py - DESPUÉS (Fix)

def extract_skills(self, graph):
    """FIX: Query completa sin LIMIT"""
    query = """
        PREFIX esco: <http://data.europa.eu/esco/model#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT DISTINCT ?skill ?label_en ?label_es ?description
        WHERE {
            # Skill concept
            ?skill a esco:Skill .

            # English label (siempre presente)
            ?skill skos:prefLabel ?label_en .
            FILTER(lang(?label_en) = "en")

            # Spanish label (opcional)
            OPTIONAL {
                ?skill skos:prefLabel ?label_es .
                FILTER(lang(?label_es) = "es")
            }

            # Description (opcional)
            OPTIONAL {
                ?skill skos:definition ?description .
                FILTER(lang(?description) = "en")
            }
        }
        # NO LIMIT - queremos TODAS las skills
    """

    results = graph.query(query)
    skills_inserted = 0

    for row in results:
        skill_uri = str(row.skill)
        label_en = str(row.label_en)
        label_es = str(row.label_es) if row.label_es else label_en
        description = str(row.description) if row.description else None

        # INSERT into esco_skills
        cursor.execute("""
            INSERT OR IGNORE INTO esco_skills (
                skill_uri, preferred_label_en, preferred_label_es, description
            ) VALUES (?, ?, ?, ?)
        """, (skill_uri, label_en, label_es, description))

        skills_inserted += 1

    print(f"[OK] {skills_inserted} skills insertadas")
    return skills_inserted
```

**Validación**:
```bash
# Re-ejecutar población ESCO
cd D:/OEDE/Webscrapping/database
python populate_esco_from_rdf.py --force-reload

# Verificar
sqlite3 bumeran_scraping.db "SELECT COUNT(*) FROM esco_skills;"
# Esperar: ~13,890
```

### 6.2 Encoding Issues

**Problema**: Caracteres mal encodificados (Ã³, Ã±, â€)

**Fix**: Aplicar en scraping antes de DB insert

```python
# D:/OEDE/Webscrapping/01_sources/bumeran/scrapers/scrapear_con_diccionario.py

class BumeranMultiSearch:

    def _clean_text(self, text):
        """Fix encoding antes de guardar en DB"""
        if not text:
            return text

        # Fix common encoding issues
        replacements = {
            'Ã³': 'ó',
            'Ã¡': 'á',
            'Ã©': 'é',
            'Ã­': 'í',
            'Ã±': 'ñ',
            'Ãº': 'ú',
            'â€': '"',
            'â€™': "'",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        # Ensure UTF-8
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')

        return text
```

---

## 7. TIMELINE DE IMPLEMENTACIÓN

### AHORA (Preparación - 2-3 horas)

#### ✅ COMPLETADO
- [x] Crear directorio `database/migrations/`
- [x] Crear `backup_db.py`
- [x] Crear `create_schema_v2.sql`
- [x] Crear `test_data_integrity.py`
- [x] Crear `MIGRATION_PLAN.md` (este documento)

#### 🔄 EN PROCESO (Ejecutar AHORA)

**Hora 1: Backup y Tests** (30 min)
```bash
# 1.1 Backup de producción
cd D:/OEDE/Webscrapping/database/migrations
python backup_db.py --description "Pre-migración v2.0"

# 1.2 Tests de integridad
python test_data_integrity.py --report integrity_pre_migration.json

# 1.3 Revisar resultados
# Si FAIL > 0 → Resolver antes de continuar
```

**Hora 2: Aplicar Schema v2** (30 min)
```bash
# 2.1 Crear schema v2 (no afecta v1)
cd D:/OEDE/Webscrapping/database
sqlite3 bumeran_scraping.db < migrations/create_schema_v2.sql

# 2.2 Verificar tablas creadas
sqlite3 bumeran_scraping.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

# Esperar ver:
# - scraping_sessions
# - ofertas_raw
# - ofertas_v2
# - nlp_versions
# - ofertas_nlp_v2
# - skills
# - ofertas_skills
# - ...
```

**Hora 3: Fix ESCO Skills Bug** (60 min)
```bash
# 3.1 Backup de tabla esco_skills actual (solo 6 registros)
sqlite3 bumeran_scraping.db "CREATE TABLE esco_skills_backup AS SELECT * FROM esco_skills;"

# 3.2 Editar populate_esco_from_rdf.py (fix SPARQL query)
# Ver sección 6.1 de este plan

# 3.3 Re-ejecutar población ESCO
python populate_esco_from_rdf.py --force-reload

# 3.4 Verificar fix
sqlite3 bumeran_scraping.db "SELECT COUNT(*) FROM esco_skills;"
# Esperar: ~13,890
```

### HOY (Implementación Core - 4-6 horas)

**Hora 4-5: Modificar db_manager.py para Dual-Write** (90 min)
```bash
# 4.1 Backup de db_manager.py actual
cp database/db_manager.py database/db_manager_v1_backup.py

# 4.2 Implementar dual-write
# Ver sección 4.2 de este plan

# 4.3 Test con scraping manual (NO scheduler)
python -c "
from database.db_manager import DatabaseManager
import pandas as pd

# Test oferta
test_df = pd.DataFrame([{
    'id_oferta': 'TEST_001',
    'titulo': 'Test Dual Write',
    'descripcion': 'Testing...',
    'empresa': 'Test SA'
}])

db = DatabaseManager()
v1, v2 = db.insert_ofertas(test_df, {
    'uuid': 'test-session',
    'source': 'bumeran',
    'mode': 'manual',
    'start_time': '2025-11-02 00:00:00'
})

print(f'V1 insertados: {v1}')
print(f'V2 insertados: {v2}')
"

# 4.4 Verificar en DB
sqlite3 bumeran_scraping.db "
SELECT 'V1', COUNT(*) FROM ofertas WHERE id_oferta = 'TEST_001'
UNION ALL
SELECT 'V2', COUNT(*) FROM ofertas_v2 WHERE id_oferta = 'TEST_001';
"
```

**Hora 6-7: Migrar Datos Históricos a v2** (120 min)
```python
# migrations/migrate_historical_data.py

import sqlite3
from tqdm import tqdm
import json

def migrate_ofertas_to_v2():
    """Migra todas las ofertas existentes de v1 a v2"""
    conn = sqlite3.connect('database/bumeran_scraping.db')
    cursor = conn.cursor()

    # 1. Crear session para migración histórica
    cursor.execute("""
        INSERT INTO scraping_sessions (
            session_uuid, source, mode, start_time, status
        ) VALUES (?, ?, ?, ?, ?)
    """, ('migration-historical', 'bumeran', 'full',
          '2025-11-02 00:00:00', 'completed'))

    migration_session_id = cursor.lastrowid

    # 2. Obtener todas las ofertas v1
    cursor.execute("SELECT * FROM ofertas")
    ofertas_v1 = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    print(f"Migrando {len(ofertas_v1):,} ofertas a v2...")

    for row in tqdm(ofertas_v1):
        oferta = dict(zip(columns, row))

        # 2.1 ofertas_raw
        raw_json = json.dumps(oferta, ensure_ascii=False)
        content_hash = hashlib.sha256(raw_json.encode()).hexdigest()

        cursor.execute("""
            INSERT INTO ofertas_raw (
                id_oferta, scraping_session_id, raw_json, content_hash
            ) VALUES (?, ?, ?, ?)
        """, (oferta['id_oferta'], migration_session_id, raw_json, content_hash))

        # 2.2 ofertas_v2
        # Obtener/crear empresa
        empresa_id = None
        if oferta.get('empresa'):
            cursor.execute("SELECT id FROM empresas WHERE nombre = ?", (oferta['empresa'],))
            result = cursor.fetchone()
            if result:
                empresa_id = result[0]
            else:
                cursor.execute("INSERT INTO empresas (nombre) VALUES (?)", (oferta['empresa'],))
                empresa_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO ofertas_v2 (
                id_oferta, titulo, descripcion, empresa_id,
                provincia, localidad, area_trabajo,
                fecha_publicacion, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            oferta['id_oferta'],
            oferta['titulo'],
            oferta['descripcion'],
            empresa_id,
            oferta.get('provincia'),
            oferta.get('localidad'),
            oferta.get('area_trabajo'),
            oferta.get('fecha_publicacion'),
            'bumeran'
        ))

    conn.commit()
    print(f"[OK] {len(ofertas_v1):,} ofertas migradas a v2")

def migrate_nlp_to_v2():
    """Migra ofertas_nlp a ofertas_nlp_v2 con versionado"""
    conn = sqlite3.connect('database/bumeran_scraping.db')
    cursor = conn.cursor()

    # Obtener version_id actual
    cursor.execute("SELECT id FROM nlp_versions WHERE is_active = 1")
    active_version_id = cursor.fetchone()[0]

    # Migrar datos NLP
    cursor.execute("SELECT * FROM ofertas_nlp")
    ofertas_nlp = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    print(f"Migrando {len(ofertas_nlp):,} registros NLP a v2...")

    for row in tqdm(ofertas_nlp):
        nlp = dict(zip(columns, row))

        # Insertar en ofertas_nlp_v2
        cursor.execute("""
            INSERT INTO ofertas_nlp_v2 (
                id_oferta, version_id,
                experiencia_min_anios, experiencia_max_anios,
                nivel_educativo, estado_educativo, carrera_especifica,
                idioma_principal, nivel_idioma_principal,
                salario_min, salario_max, moneda,
                jornada_laboral, horario_flexible,
                confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nlp['id_oferta'], active_version_id,
            nlp.get('experiencia_min_anios'),
            nlp.get('experiencia_max_anios'),
            nlp.get('nivel_educativo'),
            nlp.get('estado_educativo'),
            nlp.get('carrera_especifica'),
            nlp.get('idioma_principal'),
            nlp.get('nivel_idioma_principal'),
            nlp.get('salario_min'),
            nlp.get('salario_max'),
            nlp.get('moneda'),
            nlp.get('jornada_laboral'),
            nlp.get('horario_flexible'),
            nlp.get('nlp_confidence_score', 0.0)
        ))

        # Normalizar skills
        if nlp.get('skills_tecnicas_list'):
            try:
                skills = json.loads(nlp['skills_tecnicas_list'])
                for skill_name in skills:
                    # Get or create skill
                    cursor.execute("SELECT id FROM skills WHERE nombre = ?", (skill_name,))
                    result = cursor.fetchone()
                    if result:
                        skill_id = result[0]
                    else:
                        cursor.execute(
                            "INSERT INTO skills (nombre, tipo) VALUES (?, ?)",
                            (skill_name, 'tecnica')
                        )
                        skill_id = cursor.lastrowid

                    # Link oferta ↔ skill
                    cursor.execute("""
                        INSERT OR IGNORE INTO ofertas_skills (
                            oferta_id, skill_id, version_id
                        ) VALUES (?, ?, ?)
                    """, (nlp['id_oferta'], skill_id, active_version_id))
            except:
                pass

    conn.commit()
    print(f"[OK] {len(ofertas_nlp):,} registros NLP migrados")

if __name__ == '__main__':
    import hashlib
    migrate_ofertas_to_v2()
    migrate_nlp_to_v2()
```

**Ejecutar migración**:
```bash
python migrations/migrate_historical_data.py
```

### MAÑANA (Validación - 2-4 horas)

**Validar Dual-Write con Scheduler** (Test completo)
```bash
# 1. Ejecutar scheduler en modo test
python run_scheduler.py --test

# 2. Verificar escritura en ambos schemas
sqlite3 database/bumeran_scraping.db "
SELECT
    'V1 ofertas' as tabla, COUNT(*) as count FROM ofertas
UNION ALL
SELECT 'V2 ofertas_v2', COUNT(*) FROM ofertas_v2
UNION ALL
SELECT 'V2 ofertas_raw', COUNT(*) FROM ofertas_raw;
"

# 3. Verificar última session
sqlite3 database/bumeran_scraping.db "
SELECT * FROM scraping_sessions
ORDER BY start_time DESC LIMIT 1;
"
```

**Actualizar Dashboard Operativo**
```python
# Agregar en dashboard_scraping_v4.py

# Tab: Migración Status
@app.callback(...)
def update_migration_status():
    """Compara v1 vs v2 en tiempo real"""

    # Query ambos schemas
    v1_count = pd.read_sql("SELECT COUNT(*) as c FROM ofertas", conn)
    v2_count = pd.read_sql("SELECT COUNT(*) as c FROM ofertas_v2", conn)

    sync_percentage = (v2_count['c'][0] / v1_count['c'][0]) * 100

    return html.Div([
        html.H3("Estado de Migración v1 → v2"),
        dcc.Graph(figure={
            'data': [{
                'x': ['V1 (Producción)', 'V2 (Nueva)'],
                'y': [v1_count['c'][0], v2_count['c'][0]],
                'type': 'bar'
            }],
            'layout': {
                'title': f'Sincronización: {sync_percentage:.1f}%'
            }
        })
    ])
```

### PRÓXIMA SEMANA (Cutover - Planificado)

**Lunes**: Continuar validación dual-write
**Martes**: Re-ejecutar NLP v4.0 con nueva arquitectura
**Miércoles**: Re-ejecutar ESCO matching con skills corregidas
**Jueves**: Validar scheduler production con v2 activo
**Viernes**: Actualizar Shiny dashboard con datos enriquecidos

---

## 8. DASHBOARD INTEGRATION

### 8.1 Dashboard Operativo (localhost:8050)

**Archivo**: `D:/OEDE/Webscrapping/dashboard_scraping_v4.py`

**Nuevos Tabs a Agregar**:

#### Tab: Migración v1 → v2

```python
# Métricas de sincronización
- Total ofertas v1 vs v2
- Última session de migración
- Ofertas pendientes de migrar
- Tiempo de sync promedio
```

#### Tab: NLP Versions Comparison

```python
# Comparar versiones NLP
- v3.7 (regex) vs v4.0 (hybrid)
- Confidence score por versión
- Campos extraídos por versión
- Tabla comparativa lado a lado
```

#### Tab: ESCO Integration Health

```python
# Métricas ESCO
- Total skills en ESCO: 13,890 ✓ (antes: 6 ❌)
- Cobertura de matching: 85%+
- Top 20 occupations detectadas
- Skills gap analysis
```

### 8.2 Dashboard Público (shinyapps.io)

**Archivo**: `D:/OEDE/Webscrapping/Visual--/app.R`

**Datos a actualizar**:
- Usar datos de `ofertas_v2` (normalizado)
- Usar `ofertas_esco_matching` (con fix de skills)
- Agregar filtro por "Skills ESCO" (ahora tenemos 13K+)

---

## 9. CRITERIOS DE VALIDACIÓN

### 9.1 Validación de Migración Exitosa

#### ✅ Criterio 1: Integridad de Datos

```sql
-- Test 1: Sin pérdida de datos
SELECT
    (SELECT COUNT(*) FROM ofertas) as v1,
    (SELECT COUNT(*) FROM ofertas_v2) as v2,
    CASE
        WHEN v1 = v2 THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status;

-- Test 2: Skills normalizadas
SELECT COUNT(*) FROM skills WHERE tipo = 'tecnica';
-- Esperar: > 200

SELECT COUNT(*) FROM ofertas_skills;
-- Esperar: > 10,000

-- Test 3: ESCO skills corregidas
SELECT COUNT(*) FROM esco_skills;
-- Esperar: >= 13,000
```

#### ✅ Criterio 2: Performance

```sql
-- Query v1 (lento - JSON)
-- No se puede hacer eficientemente

-- Query v2 (rápido - normalizado)
SELECT s.nombre, COUNT(*) as ofertas_count
FROM skills s
JOIN ofertas_skills os ON s.id = os.skill_id
WHERE s.tipo = 'tecnica'
GROUP BY s.nombre
ORDER BY ofertas_count DESC
LIMIT 20;

-- Debe ejecutar en < 100ms
```

#### ✅ Criterio 3: Scheduler NO Roto

```bash
# Ejecutar scheduler
python run_scheduler.py --test

# Verificar:
# 1. Scraping exitoso (ofertas nuevas > 0)
# 2. DB v1 actualizada (scheduler sigue funcionando)
# 3. DB v2 sincronizada (dual-write funciona)
# 4. Sin errores CRITICAL en logs
```

### 9.2 Métricas de Éxito

| Métrica | Objetivo | Actual | Status |
|---------|----------|--------|--------|
| **ESCO Skills** | 13,890 | 6 | ❌ → Arreglar |
| **NLP Coverage** | > 95% | ? | Medir post-fix |
| **Matching Coverage** | > 85% | ? | Medir post-fix |
| **Dual-Write Success** | 100% | - | Implementar |
| **Migration Sync** | 100% | - | Validar |
| **Dashboard Updated** | Sí | No | Agregar tabs |
| **Scheduler Working** | Sí | Sí | ✅ Mantener |

---

## 10. ROLLBACK PLAN

### En Caso de Fallo Crítico

#### Scenario A: Scheduler Roto

```bash
# 1. Revertir db_manager.py
cp database/db_manager_v1_backup.py database/db_manager.py

# 2. Restart scheduler
# El scheduler volverá a funcionar con v1 (sin dual-write)

# 3. Investigar error en logs
tail -f logs/scheduler_*.log
```

#### Scenario B: Corrupción de Datos

```bash
# 1. Restaurar desde backup
cd database/migrations
python -c "
import shutil
from pathlib import Path

# Encontrar último backup
backups = sorted(Path('backups').glob('*_backup_*.db'), reverse=True)
latest = backups[0]

# Restaurar
shutil.copy(latest, '../bumeran_scraping.db')
print(f'Restaurado desde: {latest}')
"

# 2. Verificar integridad
python test_data_integrity.py
```

#### Scenario C: ESCO Population Falla

```sql
-- Restaurar tabla ESCO skills desde backup
DROP TABLE esco_skills;
ALTER TABLE esco_skills_backup RENAME TO esco_skills;

-- Volver a intentar con query corregida
```

---

## RESUMEN EJECUTIVO

### ¿Qué estamos haciendo?

Diseñando e implementando **Database v2.0** para soportar el sistema completo de inteligencia laboral sin parches constantes.

### ¿Por qué?

- Skills en JSON → No queryable
- NLP sin versioning → Perdemos historial
- ESCO con 6 skills → Matching inútil (debería tener 13,890)
- Sin tracking de cambios → No análisis temporal

### ¿Cómo?

1. **DUAL-WRITE**: Escribir a v1 (producción) Y v2 (nueva) simultáneamente
2. **NO ROMPER SCHEDULER**: Lunes/Jueves 8:00 AM sigue funcionando
3. **FIX ESCO BUG**: 6 → 13,890 skills
4. **BUMERAN-FIRST**: Completar pipeline end-to-end con una fuente antes de agregar más
5. **DASHBOARD-VISIBLE**: Todo monitoreado en localhost en tiempo real

### ¿Cuándo?

- **AHORA**: Backup, tests, crear schema v2, fix ESCO bug
- **HOY**: Implementar dual-write, migrar datos históricos
- **MAÑANA**: Validar con scheduler, actualizar dashboard
- **PRÓXIMA SEMANA**: Cutover completo a v2

### Estado Actual de Archivos

```
✅ COMPLETADOS:
- database/migrations/backup_db.py
- database/migrations/create_schema_v2.sql
- database/migrations/test_data_integrity.py
- database/migrations/MIGRATION_PLAN.md (este documento)

🔄 PENDIENTES:
- database/migrations/migrate_historical_data.py (crear)
- database/db_manager.py (modificar para dual-write)
- database/populate_esco_from_rdf.py (fix SPARQL query)
- dashboard_scraping_v4.py (agregar tabs de migración)

⚠️ CRÍTICOS (NO TOCAR):
- run_scheduler.py
- data/tracking/bumeran_scraped_ids.json
- tabla ofertas (38 columnas)
```

---

**Documento de Referencia**: Cuando olvides algo, vuelve a este plan.
**Próxima Acción**: Ejecutar backups y tests de integridad (sección 7, Hora 1)

---

*Generado: 2025-11-02*
*Versión: 2.0.0*
*Autor: Sistema de Migración Database v2*
