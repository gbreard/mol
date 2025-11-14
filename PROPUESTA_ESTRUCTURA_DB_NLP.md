# PROPUESTA: Estructura de Base de Datos para NLP + ESCO

**Fecha:** 2025-10-31
**Estado:** BORRADOR - En discusión
**Contexto:** Diseño de estructura de datos antes de completar Fase 02.5 y 03

---

## PROBLEMA IDENTIFICADO

### 1. Encoding corrupto en campo `descripcion`

- **Síntoma:** Caracteres `�` en lugar de acentos (técnico → t�cnico)
- **Causa:** Corrupción UTF-8/Latin-1 al guardar en DB
- **Impacto:** Afecta extracción NLP (~100% de ofertas con problema)

### 2. Resultados NLP actualmente en CSV

- **Estado actual:** `02.5_nlp_extraction/data/processed/*.csv`
- **Problema:** No están en DB, dificulta queries SQL
- **Necesidad:** Integrar con scraping + ESCO en DB única

---

## SOLUCIÓN PROPUESTA: Encoding

### Agregar columna `descripcion_utf8` limpia

```sql
ALTER TABLE ofertas ADD COLUMN descripcion_utf8 TEXT;

-- Luego poblar con EncodingFixer
UPDATE ofertas
SET descripcion_utf8 = fix_encoding(descripcion)
WHERE descripcion IS NOT NULL;
```

**Ventajas:**
- ✅ No pierde datos originales
- ✅ Rápido (10 min para 5,479 ofertas)
- ✅ Reversible
- ✅ Auditable (comparar antes/después)

**Script:** `fix_encoding_db.py` (pendiente crear)

---

## SOLUCIÓN PROPUESTA: Tabla NLP

### Crear tabla `ofertas_nlp` separada

```sql
CREATE TABLE ofertas_nlp (
    id_oferta INTEGER PRIMARY KEY,

    -- Experiencia (3 campos)
    experiencia_min_anios INTEGER,
    experiencia_max_anios INTEGER,
    experiencia_area TEXT,

    -- Educación (4 campos)
    nivel_educativo TEXT,            -- enum
    estado_educativo TEXT,           -- enum
    carrera_especifica TEXT,
    titulo_excluyente INTEGER,       -- boolean

    -- Idiomas (4 campos)
    idioma_principal TEXT,
    nivel_idioma_principal TEXT,
    idioma_secundario TEXT,
    nivel_idioma_secundario TEXT,

    -- Skills (4 campos) - Arrays en JSON
    skills_tecnicas_list TEXT,       -- JSON array
    niveles_skills_list TEXT,        -- JSON array
    soft_skills_list TEXT,           -- JSON array
    certificaciones_list TEXT,       -- JSON array

    -- Compensación (4 campos)
    salario_min REAL,
    salario_max REAL,
    moneda TEXT,
    beneficios_list TEXT,            -- JSON array

    -- Requisitos (2 campos)
    requisitos_excluyentes_list TEXT,  -- JSON array
    requisitos_deseables_list TEXT,    -- JSON array

    -- Jornada (2 campos)
    jornada_laboral TEXT,
    horario_flexible INTEGER,

    -- Metadata NLP (3 campos)
    nlp_extraction_timestamp TEXT,
    nlp_version TEXT,
    nlp_confidence_score REAL,

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
);
```

**Ventajas:**
- ✅ Separación clara (scraping vs procesamiento)
- ✅ Fácil de reprocesar (DROP + recrear)
- ✅ No contamina tabla original
- ✅ JOIN simple cuando se necesite

**Script:** `create_ofertas_nlp_table.py` (pendiente crear)

---

## ESTRUCTURA RESULTANTE (Parcial - solo NLP)

```
database/bumeran_scraping.db
│
├── ofertas (39 columnas)
│   ├── id_oferta PK
│   ├── descripcion (original corrupta) ⚠️
│   ├── descripcion_utf8 (nueva, limpia) ✨
│   └── ... 36 campos más de scraping
│
└── ofertas_nlp (27 columnas) ✨
    ├── id_oferta PK, FK
    ├── experiencia_min_anios
    ├── skills_tecnicas_list (JSON)
    ├── nlp_confidence_score
    └── ... 23 campos más
```

**Query ejemplo:**
```sql
SELECT
    o.titulo,
    o.empresa,
    o.descripcion_utf8,
    n.experiencia_min_anios,
    n.skills_tecnicas_list
FROM ofertas o
LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
WHERE n.experiencia_min_anios >= 3;
```

---

## PENDIENTE: Integración con ESCO

**IMPORTANTE:** Esta estructura es **parcial**. Falta diseñar:

- Tabla(s) para matching ESCO (Fase 03)
- Relación con taxonomía ESCO (ocupaciones, skills)
- Niveles de vinculación ESCO (exacto, similar, sugerido)
- Variables de confianza del matching

**Próximo paso:** Analizar Fase 03 y diseñar estructura completa NLP + ESCO integrada.

---

## SCRIPTS A CREAR

1. `fix_encoding_db.py` - Corrige encoding y crea columna `descripcion_utf8`
2. `create_ofertas_nlp_table.py` - Crea tabla `ofertas_nlp`
3. Modificar `run_nlp_extraction.py` - Guardar en DB además de CSV
4. **PENDIENTE:** Scripts para ESCO matching y sus tablas

---

**Fecha de propuesta:** 2025-10-31
**Estado:** BORRADOR - Esperando análisis ESCO para estructura final
**Próxima acción:** Explorar Fase 03 ESCO matching
