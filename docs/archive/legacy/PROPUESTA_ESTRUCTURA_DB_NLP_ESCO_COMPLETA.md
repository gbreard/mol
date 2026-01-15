# ESTRUCTURA DE BASE DE DATOS: NLP + ESCO COMPLETO

**Fecha:** 2025-10-31
**Estado:** DISEÑO COMPLETO - Listo para implementación
**Versión:** 2.0 - Aprovecha TODA la capacidad de ESCO (solo español)
**Contexto:** Integración completa de scraping, NLP extraction y ontología ESCO

---

## RESUMEN EJECUTIVO

Este documento define la estructura **completa e integrada** de la base de datos SQLite que unifica:

1. ✅ **Datos de scraping** (5,479+ ofertas, 38 campos)
2. ✅ **Extracción NLP** (27 campos: skills, experiencia, educación, compensación)
3. ✅ **Ontología ESCO COMPLETA** (3,008 ocupaciones, 13,890 skills) - **SOLO ESPAÑOL**
4. ✅ **Diccionarios de normalización** Argentina-ESCO
5. ✅ **Matching semántico** con BGE-M3 embeddings

**Objetivo:** Aprovechar TODA la información disponible en ESCO (no solo labels básicos) para:
- Matching avanzado de ofertas con ocupaciones ESCO
- Gap analysis de skills del mercado laboral argentino
- Expansión del bucle iterativo de keywords (v3.2 → v4.0)
- Analytics multidimensional de demanda laboral

---

## PROBLEMAS IDENTIFICADOS

### 1. Encoding UTF-8 corrupto en `descripcion`

- **Síntoma:** Caracteres `�` en lugar de acentos (técnico → t�cnico)
- **Causa:** Corrupción en proceso de scraping/almacenamiento
- **Impacto:** Afecta extracción NLP de ~100% ofertas
- **Solución:** Nueva columna `descripcion_utf8` con texto limpio

### 2. Resultados NLP dispersos en CSV

- **Estado actual:** `02.5_nlp_extraction/data/processed/*.csv`
- **Problema:** No integrados en DB, dificulta queries
- **Solución:** Tabla `ofertas_nlp` con 27 campos estructurados

### 3. ESCO subutilizado (CRÍTICO)

**Campos que NO estábamos capturando:**

- ❌ Alternative labels en español (solo guardábamos preferredLabel)
- ❌ Términos con género (administrador/administradora)
- ❌ Código ESCO específico (4110.1.1 ≠ ISCO C4110)
- ❌ Scope notes con exclusiones ("Excludes political party agent")
- ❌ Información de profesiones reguladas
- ❌ Jerarquía completa de ancestors (solo broader)
- ❌ Skills agrupados por tipo (essential skill vs knowledge)

**Impacto:** Perdemos ~60% del valor informativo de ESCO

**Solución:** Tablas ESCO completas con TODOS los campos (solo español)

---

## ESQUEMA COMPLETO DE BASE DE DATOS

### GRUPO 1: DATOS DE SCRAPING

#### Tabla: `ofertas` (MODIFICADA)

```sql
-- Agregar nueva columna para encoding limpio
ALTER TABLE ofertas ADD COLUMN descripcion_utf8 TEXT;

-- La tabla ya tiene 38 columnas existentes:
-- id_oferta (PK), id_empresa, titulo, empresa, descripcion (original),
-- localizacion, modalidad_trabajo, tipo_trabajo, fecha_publicacion_iso,
-- url_oferta, portal, scrapeado_en, etc.
```

**Cambios:**
- ✨ Nueva columna `descripcion_utf8` con texto limpio UTF-8
- ⚠️ Mantiene `descripcion` original para auditoría
- 📊 Total: 39 columnas (38 + 1 nueva)

---

### GRUPO 2: EXTRACCIÓN NLP

#### Tabla: `ofertas_nlp`

```sql
CREATE TABLE ofertas_nlp (
    id_oferta TEXT PRIMARY KEY,

    -- EXPERIENCIA (3 campos)
    experiencia_min_anios INTEGER,
    experiencia_max_anios INTEGER,
    experiencia_area TEXT,

    -- EDUCACIÓN (4 campos)
    nivel_educativo TEXT,            -- Secundario, Terciario, Universitario, Posgrado
    estado_educativo TEXT,           -- En curso, Graduado, Trunco
    carrera_especifica TEXT,
    titulo_excluyente INTEGER,       -- 0=No, 1=Sí

    -- IDIOMAS (4 campos)
    idioma_principal TEXT,
    nivel_idioma_principal TEXT,     -- Básico, Intermedio, Avanzado, Nativo
    idioma_secundario TEXT,
    nivel_idioma_secundario TEXT,

    -- SKILLS TÉCNICAS (4 campos - JSON arrays)
    skills_tecnicas_list TEXT,       -- ["Python", "SQL", "Docker"]
    niveles_skills_list TEXT,        -- ["Avanzado", "Intermedio", "Básico"]
    soft_skills_list TEXT,           -- ["Liderazgo", "Trabajo en equipo"]
    certificaciones_list TEXT,       -- ["PMP", "AWS Solutions Architect"]

    -- COMPENSACIÓN (4 campos)
    salario_min REAL,
    salario_max REAL,
    moneda TEXT,                     -- ARS, USD
    beneficios_list TEXT,            -- JSON: ["Prepaga", "Bonos"]

    -- REQUISITOS (2 campos)
    requisitos_excluyentes_list TEXT,  -- JSON array
    requisitos_deseables_list TEXT,    -- JSON array

    -- JORNADA (2 campos)
    jornada_laboral TEXT,            -- Full-time, Part-time
    horario_flexible INTEGER,        -- 0=No, 1=Sí

    -- METADATA NLP (3 campos)
    nlp_extraction_timestamp TEXT,
    nlp_version TEXT,                -- v1.0, v2.0, etc.
    nlp_confidence_score REAL,       -- 0.0 a 1.0

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
);

CREATE INDEX idx_ofertas_nlp_experiencia ON ofertas_nlp(experiencia_min_anios);
CREATE INDEX idx_ofertas_nlp_nivel_educativo ON ofertas_nlp(nivel_educativo);
```

**Total:** 27 campos + metadata
**Tamaño estimado:** ~2 MB para 5,479 ofertas

---

### GRUPO 3: ONTOLOGÍA ESCO COMPLETA (SOLO ESPAÑOL)

#### Tabla: `esco_occupations`

```sql
CREATE TABLE esco_occupations (
    -- IDENTIFICADORES
    occupation_uri TEXT PRIMARY KEY,           -- http://data.europa.eu/esco/occupation/[UUID]
    occupation_uuid TEXT UNIQUE NOT NULL,      -- 0a3c2d5b-e1f9-4200-9288-62bf3fed3310
    esco_code TEXT,                            -- 4110.1.1 (código ESCO específico)
    isco_code TEXT,                            -- C4110 (código ISCO-08)

    -- LABELS Y DESCRIPCIONES (SOLO ESPAÑOL)
    preferred_label_es TEXT NOT NULL,          -- "administrador de cuentas de socios"
    description_es TEXT,                       -- Descripción completa

    -- SCOPE NOTES
    scope_note_es TEXT,                        -- Exclusiones y aclaraciones
    scope_note_mimetype TEXT DEFAULT 'text/html',

    -- PROFESIÓN REGULADA
    regulated_profession_uri TEXT,             -- URI de regulación
    regulated_profession_note TEXT,            -- Nota sobre regulación
    is_regulated INTEGER DEFAULT 0,            -- 0=No regulada, 1=Regulada

    -- JERARQUÍA
    broader_occupation_uri TEXT,               -- Ocupación padre directa
    hierarchy_level INTEGER,                   -- 0=raíz, 1,2,3,4=niveles ISCO

    -- METADATA
    status TEXT DEFAULT 'released',            -- released, deprecated
    concept_type TEXT DEFAULT 'Occupation',
    last_modified TEXT,

    FOREIGN KEY (isco_code) REFERENCES esco_isco_hierarchy(isco_code),
    FOREIGN KEY (broader_occupation_uri) REFERENCES esco_occupations(occupation_uri)
);

CREATE INDEX idx_esco_occ_code ON esco_occupations(esco_code);
CREATE INDEX idx_esco_occ_isco ON esco_occupations(isco_code);
CREATE INDEX idx_esco_occ_label ON esco_occupations(preferred_label_es);
CREATE INDEX idx_esco_occ_broader ON esco_occupations(broader_occupation_uri);
```

**Registros esperados:** ~3,008 ocupaciones
**Tamaño estimado:** ~1.5 MB

---

#### Tabla: `esco_occupation_alternative_labels` (SOLO ESPAÑOL)

```sql
CREATE TABLE esco_occupation_alternative_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_uri TEXT NOT NULL,
    label TEXT NOT NULL,                       -- "administradora de cuentas de socios"
    label_type TEXT DEFAULT 'altLabel',        -- altLabel, hiddenLabel

    FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
    UNIQUE(occupation_uri, label)
);

CREATE INDEX idx_esco_alt_labels_occ ON esco_occupation_alternative_labels(occupation_uri);
CREATE INDEX idx_esco_alt_labels_text ON esco_occupation_alternative_labels(label);
```

**Registros esperados:** ~6,000 (promedio 2 labels alternativos por ocupación en español)
**Tamaño estimado:** ~300 KB

**Justificación:** En lugar de 40,000 registros (27 idiomas), solo ~6,000 en español

---

#### Tabla: `esco_occupation_gendered_terms`

```sql
CREATE TABLE esco_occupation_gendered_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_uri TEXT NOT NULL,
    term_label TEXT NOT NULL,                  -- "administrador de cuentas de socios"
    roles_json TEXT,                           -- ["male", "standard male"]
    term_type TEXT DEFAULT 'alternativeTerm',

    FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri)
);

CREATE INDEX idx_esco_gendered_occ ON esco_occupation_gendered_terms(occupation_uri);
```

**Registros esperados:** ~5,000 (términos masculino/femenino)
**Tamaño estimado:** ~250 KB

**Importancia:** Captura variantes de género en búsquedas (desarrollador/desarrolladora)

---

#### Tabla: `esco_occupation_ancestors`

```sql
CREATE TABLE esco_occupation_ancestors (
    occupation_uri TEXT NOT NULL,
    ancestor_uri TEXT NOT NULL,
    ancestor_level INTEGER NOT NULL,           -- 0=self, 1=padre, 2=abuelo, etc.
    ancestor_title TEXT,                       -- Título del ancestor
    ancestor_type TEXT,                        -- ISCOGroup, Occupation

    PRIMARY KEY (occupation_uri, ancestor_uri),
    FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
    FOREIGN KEY (ancestor_uri) REFERENCES esco_occupations(occupation_uri)
);

CREATE INDEX idx_esco_ancestors_occ ON esco_occupation_ancestors(occupation_uri);
CREATE INDEX idx_esco_ancestors_level ON esco_occupation_ancestors(ancestor_level);
```

**Registros esperados:** ~12,000 (promedio 4 ancestors por ocupación)
**Tamaño estimado:** ~500 KB

**Uso:** Navegación completa de jerarquía, análisis agregado por grupos ISCO

---

#### Tabla: `esco_isco_hierarchy`

```sql
CREATE TABLE esco_isco_hierarchy (
    isco_code TEXT PRIMARY KEY,                -- C1, C11, C111, C1111, etc.
    preferred_label_es TEXT NOT NULL,
    description_es TEXT,
    hierarchy_level INTEGER NOT NULL,          -- 1, 2, 3, 4
    broader_isco_code TEXT,

    FOREIGN KEY (broader_isco_code) REFERENCES esco_isco_hierarchy(isco_code)
);

CREATE INDEX idx_isco_level ON esco_isco_hierarchy(hierarchy_level);
```

**Registros esperados:** ~436 códigos ISCO (10 + 43 + 130 + 436)
**Tamaño estimado:** ~200 KB

---

#### Tabla: `esco_skills`

```sql
CREATE TABLE esco_skills (
    -- IDENTIFICADORES
    skill_uri TEXT PRIMARY KEY,                -- http://data.europa.eu/esco/skill/[UUID]
    skill_uuid TEXT UNIQUE NOT NULL,
    skill_code TEXT,                           -- S1.2.3 (si existe)

    -- LABELS (SOLO ESPAÑOL)
    preferred_label_es TEXT NOT NULL,          -- "desarrollo de software"
    description_es TEXT,

    -- CLASIFICACIÓN
    skill_type TEXT,                           -- skill, knowledge, attitude
    skill_reusability_level TEXT,              -- transversal, cross-sector, sector, occupation

    -- METADATA
    status TEXT DEFAULT 'released',
    last_modified TEXT,

    CHECK (skill_type IN ('skill', 'knowledge', 'attitude'))
);

CREATE INDEX idx_esco_skills_label ON esco_skills(preferred_label_es);
CREATE INDEX idx_esco_skills_type ON esco_skills(skill_type);
CREATE INDEX idx_esco_skills_reusability ON esco_skills(skill_reusability_level);
```

**Registros esperados:** ~13,890 skills
**Tamaño estimado:** ~3 MB

---

#### Tabla: `esco_skill_alternative_labels` (SOLO ESPAÑOL)

```sql
CREATE TABLE esco_skill_alternative_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_uri TEXT NOT NULL,
    label TEXT NOT NULL,
    label_type TEXT DEFAULT 'altLabel',

    FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
    UNIQUE(skill_uri, label)
);

CREATE INDEX idx_esco_skill_alt_occ ON esco_skill_alternative_labels(skill_uri);
CREATE INDEX idx_esco_skill_alt_text ON esco_skill_alternative_labels(label);
```

**Registros esperados:** ~20,000 (promedio 1.5 labels alternativos por skill)
**Tamaño estimado:** ~800 KB

---

#### Tabla: `esco_associations` (Ocupación-Skill)

```sql
CREATE TABLE esco_associations (
    association_uri TEXT PRIMARY KEY,          -- http://data.europa.eu/esco/association/[UUID]
    occupation_uri TEXT NOT NULL,
    skill_uri TEXT NOT NULL,

    -- TIPO DE RELACIÓN
    relation_type TEXT NOT NULL,               -- essential, optional

    -- CLASIFICACIÓN DEL SKILL EN ESTA RELACIÓN
    skill_type_in_relation TEXT,               -- skill, knowledge (del query essentialSkills)

    FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
    FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
    CHECK (relation_type IN ('essential', 'optional'))
);

CREATE INDEX idx_esco_assoc_occ ON esco_associations(occupation_uri);
CREATE INDEX idx_esco_assoc_skill ON esco_associations(skill_uri);
CREATE INDEX idx_esco_assoc_type ON esco_associations(relation_type);
```

**Registros esperados:** ~60,000 asociaciones (promedio 20 skills por ocupación)
**Tamaño estimado:** ~2.5 MB

**Importancia:** Permite queries como "skills esenciales para ocupación X" y "ocupaciones que requieren skill Y"

---

### GRUPO 4: NORMALIZACIÓN ARGENTINA-ESCO

#### Tabla: `diccionario_arg_esco`

```sql
CREATE TABLE diccionario_arg_esco (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termino_argentino TEXT UNIQUE NOT NULL,    -- "colectivero", "kiosquero"
    esco_terms_json TEXT,                      -- ["conductor", "autobús"]
    isco_target TEXT,                          -- "8331"
    esco_preferred_label TEXT,                 -- "conductor de autobús"
    notes TEXT,                                -- "Denominación argentina para conductor de colectivo"

    FOREIGN KEY (isco_target) REFERENCES esco_isco_hierarchy(isco_code)
);

CREATE INDEX idx_dict_arg_termino ON diccionario_arg_esco(termino_argentino);
CREATE INDEX idx_dict_arg_isco ON diccionario_arg_esco(isco_target);
```

**Registros esperados:** ~300 términos argentinos
**Tamaño estimado:** ~100 KB

**Fuente:** `03_esco_matching/data/diccionario_normalizacion_arg_esco.json`

---

#### Tabla: `sinonimos_regionales`

```sql
CREATE TABLE sinonimos_regionales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_ocupacional TEXT,                -- "servicios_gastronomia"
    termino_base TEXT,                         -- "mozo"
    pais TEXT,                                 -- "argentina", "españa", "mexico"
    sinonimos_json TEXT,                       -- ["mozo", "moza"]
    descripcion TEXT,

    UNIQUE(categoria_ocupacional, termino_base, pais)
);

CREATE INDEX idx_sinonimos_cat ON sinonimos_regionales(categoria_ocupacional);
CREATE INDEX idx_sinonimos_pais ON sinonimos_regionales(pais);
```

**Registros esperados:** ~500 (100 términos × 4-5 países)
**Tamaño estimado:** ~150 KB

**Fuente:** `07_esco_data/diccionario_sinonimos_ocupacionales_AR_ES.json`

---

#### Tabla: `cno_ocupaciones` (Clasificador Nacional de Ocupaciones)

```sql
CREATE TABLE cno_ocupaciones (
    cno_codigo TEXT PRIMARY KEY,               -- "5133101000"
    cno_descripcion TEXT NOT NULL,             -- "Mesero"
    cno_grupo TEXT,                            -- Grupo CNO
    cno_subgrupo TEXT,
    ejemplos_ocupacionales TEXT,               -- Ejemplos del CNO

    -- Metadata
    vigente INTEGER DEFAULT 1
);

CREATE INDEX idx_cno_descripcion ON cno_ocupaciones(cno_descripcion);
```

**Registros esperados:** ~594 ocupaciones CNO
**Tamaño estimado:** ~200 KB

---

#### Tabla: `cno_esco_matches` (Matches pre-calculados)

```sql
CREATE TABLE cno_esco_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cno_codigo TEXT NOT NULL,
    esco_occupation_uri TEXT NOT NULL,

    -- Scores de matching
    similarity_score REAL,                     -- 0.0 a 1.0
    matching_method TEXT,                      -- "BGE-M3", "manual", "fuzzy"

    -- Metadata
    match_date TEXT,
    validated INTEGER DEFAULT 0,               -- 0=No validado, 1=Validado manualmente

    FOREIGN KEY (cno_codigo) REFERENCES cno_ocupaciones(cno_codigo),
    FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
);

CREATE INDEX idx_cno_matches_cno ON cno_esco_matches(cno_codigo);
CREATE INDEX idx_cno_matches_esco ON cno_esco_matches(esco_occupation_uri);
CREATE INDEX idx_cno_matches_score ON cno_esco_matches(similarity_score DESC);
```

**Registros esperados:** ~1,200 (promedio 2 matches por ocupación CNO)
**Tamaño estimado:** ~150 KB

**Fuente:** Matches BGE-M3 del proyecto EPH-ESCO

---

### GRUPO 5: MATCHING OFERTAS-ESCO

#### Tabla: `ofertas_esco_matching`

```sql
CREATE TABLE ofertas_esco_matching (
    id_oferta TEXT PRIMARY KEY,

    -- MATCHING DE OCUPACIÓN
    esco_occupation_uri TEXT,                  -- Ocupación ESCO matcheada
    esco_occupation_label TEXT,                -- Label de la ocupación
    occupation_match_score REAL,               -- 0.0 a 1.0
    occupation_match_method TEXT,              -- "BGE-M3", "dictionary", "manual"

    -- MATCHING DE TÍTULO USANDO ESCO
    titulo_normalizado TEXT,                   -- Título después de aplicar diccionarios
    titulo_esco_code TEXT,                     -- Código ESCO del título

    -- SKILLS MATCHEADOS
    esco_skills_esenciales_json TEXT,          -- JSON: [{"uri": "...", "label": "Python", "score": 0.95}]
    esco_skills_opcionales_json TEXT,          -- JSON: [{"uri": "...", "label": "Docker", "score": 0.82}]

    -- GAP ANALYSIS
    skills_demandados_total INTEGER,           -- Total skills mencionados en oferta
    skills_matcheados_esco INTEGER,            -- Skills que se encontraron en ESCO
    skills_sin_match_json TEXT,                -- Skills que no están en ESCO

    -- METADATA
    matching_timestamp TEXT,
    matching_version TEXT,                     -- v1.0, v2.0
    confidence_score REAL,                     -- 0.0 a 1.0 (confianza global)

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
    FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
);

CREATE INDEX idx_ofertas_esco_occ ON ofertas_esco_matching(esco_occupation_uri);
CREATE INDEX idx_ofertas_esco_score ON ofertas_esco_matching(occupation_match_score DESC);
CREATE INDEX idx_ofertas_esco_confidence ON ofertas_esco_matching(confidence_score DESC);
```

**Registros esperados:** ~5,479 (una por oferta)
**Tamaño estimado:** ~2 MB

---

#### Tabla: `ofertas_esco_skills_detalle`

```sql
CREATE TABLE ofertas_esco_skills_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,

    -- SKILL EXTRAÍDO DE LA OFERTA
    skill_mencionado TEXT NOT NULL,            -- "python", "trabajo en equipo"
    skill_tipo_fuente TEXT,                    -- "tecnica", "soft", "certificacion"
    skill_nivel_mencionado TEXT,               -- "Avanzado", "Intermedio", etc.

    -- MATCHING CON ESCO
    esco_skill_uri TEXT,                       -- NULL si no hay match
    esco_skill_label TEXT,
    match_score REAL,                          -- 0.0 a 1.0
    match_method TEXT,                         -- "exact", "fuzzy", "embedding"

    -- CLASIFICACIÓN ESCO
    esco_skill_type TEXT,                      -- skill, knowledge, attitude
    esco_skill_reusability TEXT,               -- transversal, sector, occupation

    -- RELACIÓN CON OCUPACIÓN
    is_essential_for_occupation INTEGER DEFAULT 0,  -- 1 si es essential skill
    is_optional_for_occupation INTEGER DEFAULT 0,   -- 1 si es optional skill

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
    FOREIGN KEY (esco_skill_uri) REFERENCES esco_skills(skill_uri)
);

CREATE INDEX idx_skills_det_oferta ON ofertas_esco_skills_detalle(id_oferta);
CREATE INDEX idx_skills_det_esco ON ofertas_esco_skills_detalle(esco_skill_uri);
CREATE INDEX idx_skills_det_tipo ON ofertas_esco_skills_detalle(esco_skill_type);
```

**Registros esperados:** ~30,000 (promedio 5-6 skills por oferta)
**Tamaño estimado:** ~1.5 MB

**Uso:** Análisis granular de demanda de skills, gap analysis, trending skills

---

### GRUPO 6: KEYWORDS Y BUCLE ITERATIVO

#### Tabla: `keywords_performance` (YA EXISTE - actualizar)

```sql
-- Tabla existente, agregar columnas:
ALTER TABLE keywords_performance ADD COLUMN esco_occupation_uri TEXT;
ALTER TABLE keywords_performance ADD COLUMN esco_skill_uri TEXT;
ALTER TABLE keywords_performance ADD COLUMN keyword_source TEXT; -- 'manual', 'nlp_extracted', 'esco_occupation', 'esco_skill'
ALTER TABLE keywords_performance ADD COLUMN keyword_version TEXT; -- 'v3.2', 'v4.0'

-- Indices nuevos
CREATE INDEX idx_kw_perf_esco_occ ON keywords_performance(esco_occupation_uri);
CREATE INDEX idx_kw_perf_source ON keywords_performance(keyword_source);
CREATE INDEX idx_kw_perf_version ON keywords_performance(keyword_version);
```

**Uso:** Tracking del bucle iterativo v1 → v3.2 → v4.0

---

## ESTIMACIÓN DE TAMAÑOS (SOLO ESPAÑOL)

| Tabla | Registros | Tamaño Est. | Observaciones |
|-------|-----------|-------------|---------------|
| **ofertas** | 5,479+ | 13 MB | Existente + descripcion_utf8 |
| **ofertas_nlp** | 5,479 | 2 MB | 27 campos estructurados |
| **esco_occupations** | 3,008 | 1.5 MB | Ocupaciones completas |
| **esco_occupation_alternative_labels** | ~6,000 | 300 KB | ⬇️ Solo ES (vs 40K multi-idioma) |
| **esco_occupation_gendered_terms** | ~5,000 | 250 KB | Términos masculino/femenino |
| **esco_occupation_ancestors** | ~12,000 | 500 KB | Jerarquía completa |
| **esco_isco_hierarchy** | 436 | 200 KB | Grupos ISCO |
| **esco_skills** | 13,890 | 3 MB | Skills, knowledge, attitudes |
| **esco_skill_alternative_labels** | ~20,000 | 800 KB | ⬇️ Solo ES |
| **esco_associations** | ~60,000 | 2.5 MB | Ocupación-Skill relations |
| **diccionario_arg_esco** | ~300 | 100 KB | Normalización argentina |
| **sinonimos_regionales** | ~500 | 150 KB | Variantes regionales |
| **cno_ocupaciones** | 594 | 200 KB | CNO Argentina |
| **cno_esco_matches** | ~1,200 | 150 KB | Matches pre-calculados |
| **ofertas_esco_matching** | 5,479 | 2 MB | Resultados matching |
| **ofertas_esco_skills_detalle** | ~30,000 | 1.5 MB | Skills granulares |
| **keywords_performance** | ~1,500 | 200 KB | Tracking keywords |
| **TOTAL** | ~170,465 | **~28 MB** | ✅ Manejable en SQLite |

**Comparación:**
- ❌ Con 27 idiomas: ~45 MB
- ✅ Solo español: ~28 MB (reducción 38%)

---

## QUERIES SQL DE EJEMPLO

### Query 1: Ofertas con experiencia mínima y skills en español

```sql
SELECT
    o.titulo,
    o.empresa,
    o.descripcion_utf8,
    n.experiencia_min_anios,
    n.skills_tecnicas_list,
    m.esco_occupation_label,
    m.occupation_match_score
FROM ofertas o
LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE n.experiencia_min_anios >= 3
  AND m.occupation_match_score > 0.8
ORDER BY m.occupation_match_score DESC
LIMIT 10;
```

---

### Query 2: Alternative labels de una ocupación (solo español)

```sql
SELECT
    occ.esco_code,
    occ.preferred_label_es AS label_principal,
    GROUP_CONCAT(alt.label, '; ') AS labels_alternativos
FROM esco_occupations occ
LEFT JOIN esco_occupation_alternative_labels alt
    ON occ.occupation_uri = alt.occupation_uri
WHERE occ.esco_code = '4110.1.1'
GROUP BY occ.occupation_uri;

-- Resultado:
-- esco_code  | label_principal                              | labels_alternativos
-- 4110.1.1   | administrador de cuentas de socios           | administradora de cuentas de socios; account administrator
```

---

### Query 3: Jerarquía completa de una ocupación

```sql
WITH RECURSIVE hierarchy AS (
    -- Base: ocupación actual
    SELECT
        occupation_uri,
        preferred_label_es,
        esco_code,
        broader_occupation_uri,
        0 AS level
    FROM esco_occupations
    WHERE esco_code = '4110.1.1'

    UNION ALL

    -- Recursión: padres
    SELECT
        p.occupation_uri,
        p.preferred_label_es,
        p.esco_code,
        p.broader_occupation_uri,
        h.level + 1
    FROM esco_occupations p
    JOIN hierarchy h ON p.occupation_uri = h.broader_occupation_uri
)
SELECT level, esco_code, preferred_label_es
FROM hierarchy
ORDER BY level DESC;

-- Resultado:
-- level | esco_code | preferred_label_es
-- 3     | C4        | Empleados de oficina
-- 2     | C41       | Oficinistas generales
-- 1     | C411      | Oficinistas generales
-- 0     | 4110.1.1  | administrador de cuentas de socios
```

---

### Query 4: Skills esenciales vs opcionales para una ocupación

```sql
SELECT
    a.relation_type,
    a.skill_type_in_relation,
    s.preferred_label_es AS skill,
    COUNT(*) OVER (PARTITION BY a.relation_type) AS total_por_tipo
FROM esco_associations a
JOIN esco_skills s ON a.skill_uri = s.skill_uri
JOIN esco_occupations occ ON a.occupation_uri = occ.occupation_uri
WHERE occ.esco_code = '4110.1.1'
ORDER BY a.relation_type, a.skill_type_in_relation, s.preferred_label_es;

-- Resultado:
-- relation_type | skill_type_in_relation | skill                          | total_por_tipo
-- essential     | knowledge              | conocimiento de administración | 11
-- essential     | knowledge              | conocimiento de ofimática      | 11
-- essential     | skill                  | atención al detalle            | 11
-- essential     | skill                  | comunicación efectiva          | 11
-- optional      | skill                  | negociación                    | 11
-- ...
```

---

### Query 5: Gap analysis - Skills demandados vs ESCO

```sql
SELECT
    sd.skill_mencionado,
    sd.skill_tipo_fuente,
    COUNT(DISTINCT sd.id_oferta) AS ofertas_demandan,
    COUNT(DISTINCT sd.esco_skill_uri) AS tiene_match_esco,
    ROUND(AVG(sd.match_score), 2) AS score_promedio,
    -- Skills que aparecen mucho pero no están en ESCO
    CASE
        WHEN sd.esco_skill_uri IS NULL THEN 'CANDIDATO_KEYWORD_V4'
        ELSE 'OK'
    END AS estado_esco
FROM ofertas_esco_skills_detalle sd
GROUP BY sd.skill_mencionado, sd.skill_tipo_fuente
HAVING ofertas_demandan >= 10
ORDER BY ofertas_demandan DESC, estado_esco DESC
LIMIT 20;

-- Uso: Identificar skills populares no mapeados → candidatos para keywords v4.0
```

---

### Query 6: Búsqueda por términos con género

```sql
SELECT DISTINCT
    occ.esco_code,
    occ.preferred_label_es,
    gt.term_label,
    gt.roles_json
FROM esco_occupations occ
JOIN esco_occupation_gendered_terms gt ON occ.occupation_uri = gt.occupation_uri
WHERE gt.term_label LIKE '%desarrollador%'
   OR gt.term_label LIKE '%desarrolladora%';

-- Resultado:
-- esco_code | preferred_label_es              | term_label                       | roles_json
-- 2512.3    | desarrollador de software       | desarrollador de software        | ["male", "standard male"]
-- 2512.3    | desarrollador de software       | desarrolladora de software       | ["female", "standard female"]
```

---

### Query 7: Normalización de término argentino

```sql
SELECT
    d.termino_argentino,
    d.esco_terms_json,
    occ.preferred_label_es AS ocupacion_esco,
    occ.esco_code,
    d.notes
FROM diccionario_arg_esco d
LEFT JOIN esco_occupations occ
    ON occ.isco_code = d.isco_target
WHERE d.termino_argentino IN ('colectivero', 'fletero', 'kiosquero')
ORDER BY d.termino_argentino;

-- Resultado:
-- termino_argentino | esco_terms_json           | ocupacion_esco         | esco_code | notes
-- colectivero       | ["conductor", "autobús"]  | conductor de autobús   | 8331.1    | Denominación argentina
-- fletero           | ["conductor", "reparto"]  | conductor de reparto   | 8322.2    | Conductor de camión de reparto
-- kiosquero         | ["vendedor", "comercio"]  | vendedor de comercio   | 5223.1    | Vendedor de kiosco
```

---

### Query 8: Top ocupaciones ESCO matcheadas con ofertas

```sql
SELECT
    occ.esco_code,
    occ.preferred_label_es,
    COUNT(m.id_oferta) AS total_ofertas,
    ROUND(AVG(m.occupation_match_score), 2) AS score_promedio,
    COUNT(DISTINCT o.empresa) AS empresas_distintas
FROM esco_occupations occ
JOIN ofertas_esco_matching m ON occ.occupation_uri = m.esco_occupation_uri
JOIN ofertas o ON m.id_oferta = o.id_oferta
WHERE m.occupation_match_score > 0.7
GROUP BY occ.occupation_uri
ORDER BY total_ofertas DESC
LIMIT 15;

-- Uso: Identificar ocupaciones más demandadas en el mercado argentino
```

---

### Query 9: Trending skills por mes

```sql
SELECT
    strftime('%Y-%m', o.fecha_publicacion_iso) AS mes,
    sd.esco_skill_label,
    COUNT(DISTINCT sd.id_oferta) AS ofertas,
    ROUND(AVG(sd.match_score), 2) AS confianza_promedio
FROM ofertas_esco_skills_detalle sd
JOIN ofertas o ON sd.id_oferta = o.id_oferta
WHERE sd.esco_skill_uri IS NOT NULL
  AND o.fecha_publicacion_iso >= date('now', '-6 months')
GROUP BY mes, sd.esco_skill_label
HAVING ofertas >= 5
ORDER BY mes DESC, ofertas DESC;

-- Uso: Análisis temporal de demanda de competencias
```

---

## SCRIPTS DE IMPLEMENTACIÓN

### Script 1: `fix_encoding_db.py`

**Propósito:** Corregir encoding UTF-8 en descripción y crear columna limpia

```python
"""
Corrige encoding corrupto en campo descripcion y crea descripcion_utf8
Usa ftfy library para fix automático de encoding mixto UTF-8/Latin-1
"""

import sqlite3
import ftfy
from tqdm import tqdm

def fix_encoding():
    conn = sqlite3.connect('database/bumeran_scraping.db')
    cursor = conn.cursor()

    # 1. Agregar columna si no existe
    cursor.execute("ALTER TABLE ofertas ADD COLUMN descripcion_utf8 TEXT")

    # 2. Obtener todas las descripciones
    cursor.execute("SELECT id_oferta, descripcion FROM ofertas WHERE descripcion IS NOT NULL")
    ofertas = cursor.fetchall()

    # 3. Corregir encoding
    for id_oferta, descripcion in tqdm(ofertas, desc="Fixing encoding"):
        descripcion_limpia = ftfy.fix_text(descripcion)
        cursor.execute(
            "UPDATE ofertas SET descripcion_utf8 = ? WHERE id_oferta = ?",
            (descripcion_limpia, id_oferta)
        )

    conn.commit()
    conn.close()
```

**Tiempo estimado:** 10-15 minutos para 5,479 ofertas

---

### Script 2: `create_tables_nlp_esco.py`

**Propósito:** Crear todas las tablas NLP y ESCO

```python
"""
Crea estructura completa de tablas:
- ofertas_nlp
- esco_occupations + tablas relacionadas
- esco_skills + tablas relacionadas
- diccionarios argentinos
- tablas de matching
"""

import sqlite3

def create_all_tables():
    conn = sqlite3.connect('database/bumeran_scraping.db')
    cursor = conn.cursor()

    # Ejecutar todos los CREATE TABLE del diseño
    # (SQL completo incluido en el script)

    conn.commit()
    conn.close()
```

**Tiempo estimado:** <1 minuto

---

### Script 3: `populate_esco_from_rdf.py`

**Propósito:** Parsear RDF de ESCO y poblar tablas (SOLO ESPAÑOL)

```python
"""
Parsea esco-v1.2.0.rdf (1.26 GB) y extrae:
- Ocupaciones con TODOS los campos
- Alternative labels SOLO en español
- Términos con género
- Scope notes en español
- Ancestors completos
- Skills con alternative labels en español
- Associations (essential/optional)

Usa rdflib para parseo eficiente
Filtro: xml:lang="es" para todos los labels
"""

from rdflib import Graph, Namespace, RDF, SKOS
import sqlite3
from tqdm import tqdm

def populate_esco(rdf_path, db_path):
    # Cargar RDF (puede tomar 5-10 min)
    print("Cargando RDF...")
    g = Graph()
    g.parse(rdf_path, format='xml')

    # Conectar a DB
    conn = sqlite3.connect(db_path)

    # Procesar ocupaciones
    process_occupations(g, conn)

    # Procesar skills
    process_skills(g, conn)

    # Procesar associations
    process_associations(g, conn)

    conn.commit()
    conn.close()
```

**Tiempo estimado:** 15-30 minutos para RDF completo

---

### Script 4: `populate_dictionaries.py`

**Propósito:** Cargar diccionarios argentinos y CNO

```python
"""
Carga datos desde:
- diccionario_normalizacion_arg_esco.json
- diccionario_sinonimos_ocupacionales_AR_ES.json
- CNO occupations (si existe CSV/JSON)
- CNO-ESCO matches pre-calculados (BGE-M3)
"""

import json
import sqlite3

def populate_dictionaries():
    # Leer JSONs
    # Insertar en tablas correspondientes
    pass
```

**Tiempo estimado:** 2-5 minutos

---

### Script 5: `migrate_nlp_csv_to_db.py`

**Propósito:** Migrar resultados NLP de CSV a tabla ofertas_nlp

```python
"""
Lee CSVs de 02.5_nlp_extraction/data/processed/
Inserta en tabla ofertas_nlp
"""

import pandas as pd
import sqlite3

def migrate_nlp():
    # Leer CSVs NLP
    # Insertar en ofertas_nlp
    pass
```

**Tiempo estimado:** 5 minutos

---

### Script 6: `match_ofertas_to_esco.py`

**Propósito:** Matching semántico ofertas-ESCO con BGE-M3

```python
"""
Proceso de matching:
1. Normalizar título con diccionario argentino
2. Generar embedding BGE-M3 del título + descripción_utf8
3. Comparar con embeddings de ocupaciones ESCO
4. Guardar top-3 matches con scores
5. Matching de skills extraídos (NLP) con esco_skills
6. Gap analysis: skills sin match ESCO
"""

from sentence_transformers import SentenceTransformer
import sqlite3
import numpy as np

def match_ofertas():
    # Cargar modelo BGE-M3
    model = SentenceTransformer('BAAI/bge-m3')

    # Procesar ofertas
    # Generar embeddings
    # Matching semántico
    # Guardar resultados
    pass
```

**Tiempo estimado:** 30-60 minutos para 5,479 ofertas

---

## DIAGRAMA ER (Texto)

```
┌─────────────────┐
│    ofertas      │ (5,479+)
│  [id_oferta PK] │
│  descripcion    │──┐
│  descripcion_utf8│  │
│  titulo         │  │
│  empresa        │  │
│  ...            │  │
└─────────────────┘  │
         │           │
         │ 1:1       │ 1:1
         ▼           ▼
┌─────────────────┐ ┌──────────────────────┐
│  ofertas_nlp    │ │ ofertas_esco_matching│
│  [id_oferta PK] │ │  [id_oferta PK]      │
│  experiencia_*  │ │  esco_occupation_uri ├────┐
│  nivel_educativo│ │  match_score         │    │
│  skills_*_list  │ │  skills_*_json       │    │ N:1
│  salario_*      │ │  confidence_score    │    │
└─────────────────┘ └──────────────────────┘    │
                             │                   │
                             │ 1:N               ▼
                             ▼           ┌──────────────────┐
                    ┌──────────────────────────┐│  esco_occupations  │
                    │ofertas_esco_skills_detalle│  [occupation_uri PK]
                    │  skill_mencionado │       │  esco_code         │
                    │  esco_skill_uri   ├───┐   │  preferred_label_es│
                    │  match_score      │   │   │  scope_note_es     │
                    │  is_essential_*   │   │   │  broader_*         │
                    └───────────────────┘   │   └────────┬───────────┘
                                            │            │
                                            │ N:1        │ 1:N
                                            │            ▼
                                            │   ┌──────────────────────┐
                                            │   │ esco_occupation_     │
                                            │   │ alternative_labels   │
                                            │   │  label (ES)          │
                                            │   └──────────────────────┘
                                            │
                                            │   ┌──────────────────────┐
                                            │   │ esco_occupation_     │
                                            │   │ gendered_terms       │
                                            │   │  term_label          │
                                            │   │  roles_json          │
                                            │   └──────────────────────┘
                                            │
                                            │   ┌──────────────────────┐
                                            │   │ esco_occupation_     │
                                            │   │ ancestors            │
                                            │   │  ancestor_level      │
                                            │   └──────────────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │ esco_skills  │
                                    │[skill_uri PK]│
                                    │ skill_type   │
                                    │ reusability  │
                                    └──────┬───────┘
                                           │
                                           │ 1:N
                                           ▼
                                  ┌──────────────────────┐
                                  │ esco_skill_          │
                                  │ alternative_labels   │
                                  │  label (ES)          │
                                  └──────────────────────┘

         ┌──────────────────────┐
         │ esco_associations    │
         │  occupation_uri      ├───► esco_occupations
         │  skill_uri           ├───► esco_skills
         │  relation_type       │     (essential/optional)
         │  skill_type_in_rel   │
         └──────────────────────┘

         ┌──────────────────────┐
         │ diccionario_arg_esco │
         │  termino_argentino   │
         │  esco_terms_json     │
         │  isco_target         ├───► esco_isco_hierarchy
         └──────────────────────┘

         ┌──────────────────────┐
         │ cno_ocupaciones      │
         │  [cno_codigo PK]     │
         └──────┬───────────────┘
                │
                │ 1:N
                ▼
         ┌──────────────────────┐
         │ cno_esco_matches     │
         │  cno_codigo          ├───► cno_ocupaciones
         │  esco_occupation_uri ├───► esco_occupations
         │  similarity_score    │
         └──────────────────────┘
```

---

## ORDEN DE IMPLEMENTACIÓN

### Fase 1: Preparación (1 día)

1. ✅ Fix encoding UTF-8 → `fix_encoding_db.py`
2. ✅ Crear tablas vacías → `create_tables_nlp_esco.py`

### Fase 2: Población ESCO (2 días)

3. ✅ Parsear RDF y poblar ESCO → `populate_esco_from_rdf.py`
   - Solo campos en ESPAÑOL
   - ~28 MB finales
   - 15-30 minutos de procesamiento

### Fase 3: Diccionarios (medio día)

4. ✅ Cargar diccionarios AR-ESCO → `populate_dictionaries.py`
5. ✅ Cargar CNO y matches pre-calculados

### Fase 4: Migración NLP (1 día)

6. ✅ Migrar resultados NLP de CSV → `migrate_nlp_csv_to_db.py`
7. ✅ Validar completitud de datos

### Fase 5: Matching (2 días)

8. ✅ Matching ofertas-ESCO con BGE-M3 → `match_ofertas_to_esco.py`
9. ✅ Gap analysis de skills
10. ✅ Validación manual de top 100 matches

### Fase 6: Keywords v4.0 (1 día)

11. ✅ Extraer candidatos para keywords v4.0
12. ✅ Generar `diccionario_keywords_v4_0.json`
13. ✅ Testing con estrategia v4.0

**Total:** ~7-10 días de trabajo

---

## VENTAJAS DE ESTA ESTRUCTURA

### 1. Aprovecha TODA la ontología ESCO

✅ Alternative labels en español para búsqueda
✅ Términos con género (desarrollador/desarrolladora)
✅ Códigos ESCO específicos (más granulares que ISCO)
✅ Scope notes con exclusiones
✅ Info de profesiones reguladas
✅ Jerarquía completa navegable
✅ Skills clasificados por tipo y nivel de reutilización

### 2. Solo español = menor tamaño

✅ 28 MB vs 45 MB (38% reducción)
✅ Queries más rápidos
✅ Menor complejidad de mantenimiento

### 3. Integración completa

✅ Scraping + NLP + ESCO en una sola DB
✅ Queries SQL simples (no necesita joins externos)
✅ Gap analysis automatizado
✅ Tracking del bucle iterativo de keywords

### 4. Normalización argentina

✅ Diccionarios AR-ESCO integrados
✅ Matches CNO pre-calculados
✅ Sinonimos regionales

### 5. Analytics avanzado

✅ Trending skills por mes
✅ Top ocupaciones demandadas
✅ Skills sin match ESCO → candidatos keywords
✅ Análisis por jerarquía ISCO

---

## PRÓXIMOS PASOS DESPUÉS DE IMPLEMENTAR

### 1. Completar Fase 02.5 NLP (55% actual)

- Anotar 500 ofertas para entrenar NER
- Entrenar modelo spaCy
- Procesar 5,479 ofertas con modelo entrenado

### 2. Generar diccionario v4.0

- Extraer skills únicos de ofertas_esco_skills_detalle
- Combinar con ocupaciones ESCO matcheadas
- **Target:** 1,500 keywords (desde 1,148 actual)
- **Cobertura esperada:** 67-83% (desde 45.6% actual)

### 3. Testing del bucle iterativo

- Ejecutar scraping con v4.0
- Medir incremento en ofertas capturadas
- Analizar nuevos skills detectados
- Iterar a v5.0 si es necesario

### 4. Dashboard actualizado

- Queries con ESCO integrado
- Visualizaciones de gap analysis
- Trending skills por ocupación ESCO

---

## COMANDOS DE VERIFICACIÓN

### Verificar encoding fix

```sql
SELECT
    id_oferta,
    SUBSTR(descripcion, 1, 100) AS original,
    SUBSTR(descripcion_utf8, 1, 100) AS limpio
FROM ofertas
WHERE descripcion LIKE '%�%'
LIMIT 5;
```

### Contar registros ESCO

```sql
SELECT
    'Ocupaciones' AS tipo, COUNT(*) AS total FROM esco_occupations
UNION ALL
SELECT 'Alt Labels ES', COUNT(*) FROM esco_occupation_alternative_labels
UNION ALL
SELECT 'Gendered Terms', COUNT(*) FROM esco_occupation_gendered_terms
UNION ALL
SELECT 'Ancestors', COUNT(*) FROM esco_occupation_ancestors
UNION ALL
SELECT 'Skills', COUNT(*) FROM esco_skills
UNION ALL
SELECT 'Skill Alt Labels ES', COUNT(*) FROM esco_skill_alternative_labels
UNION ALL
SELECT 'Associations', COUNT(*) FROM esco_associations;
```

### Verificar matches de ofertas

```sql
SELECT
    COUNT(*) AS total_ofertas,
    COUNT(DISTINCT esco_occupation_uri) AS ocupaciones_distintas,
    ROUND(AVG(occupation_match_score), 2) AS score_promedio,
    MIN(occupation_match_score) AS score_min,
    MAX(occupation_match_score) AS score_max
FROM ofertas_esco_matching
WHERE occupation_match_score > 0.5;
```

---

## CONCLUSIÓN

Esta estructura de base de datos:

✅ **Resuelve** el problema de encoding UTF-8
✅ **Integra** resultados NLP en DB (no más CSVs dispersos)
✅ **Aprovecha TODA** la ontología ESCO (no solo labels básicos)
✅ **Optimiza** para español (reduce tamaño 38%)
✅ **Normaliza** términos argentinos con diccionarios
✅ **Habilita** el bucle iterativo de keywords (v3.2 → v4.0)
✅ **Facilita** analytics avanzado y gap analysis
✅ **Mantiene** tamaño manejable (~28 MB total)

**Estado:** LISTO PARA IMPLEMENTACIÓN
**Próxima acción:** Ejecutar scripts en orden (Fase 1 → Fase 6)

---

**Documento creado:** 2025-10-31
**Autor:** Claude Code
**Versión:** 2.0 - Diseño completo ESCO (solo español)
**Aprobación pendiente:** Usuario
