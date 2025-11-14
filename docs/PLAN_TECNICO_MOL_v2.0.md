# PLAN TÉCNICO: Monitor de Ofertas Laborales (MOL) v2.0

**Versión**: 2.0
**Fecha**: Noviembre 2025
**Autor**: Equipo OEDE
**Estado**: Planificación

---

## TABLA DE CONTENIDOS

1. [Arquitectura y Contexto](#1-arquitectura-y-contexto)
2. [Fase 1: Ontología ESCO](#2-fase-1-ontología-esco)
3. [Fase 2: Pipeline de Datos](#3-fase-2-pipeline-de-datos)
4. [Fase 3: Dashboard Shiny](#4-fase-3-dashboard-shiny)
5. [Fase 4: Dashboard Plotly v5](#5-fase-4-dashboard-plotly-v5)
6. [Fase 5: Testing y Validación](#6-fase-5-testing-y-validación)
7. [Apéndices](#7-apéndices)

---

## 1. ARQUITECTURA Y CONTEXTO

### 1.1 Estado Actual del Sistema

El MOL actual opera con una arquitectura de 5 etapas:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SCRAPING   │───>│CONSOLIDACIÓN │───>│  NLP v5.1    │───>│ESCO MATCHING │───>│  PRODUCTOS   │
│  (Bumeran)   │    │              │    │  (Ollama)    │    │ (RapidFuzz)  │    │(2 Dashboards)│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                    │                    │                    │                    │
   Ofertas              Dedupl.            Extracción           Clasificación        Visualización
   HTML/JSON            Limpieza           Structured           ESCO codes           + Análisis
```

**Componentes actuales:**

1. **Scraping**: `bumeran_scraper.py` (2,500-5,000 ofertas/día)
2. **Base de datos**: SQLite `bumeran_scraping.db` (~28 MB, 32 tablas, 5,479 ofertas)
3. **NLP**: `procesador_ofertas_nlp.py` con Ollama llama3.1:8b (v5.1)
4. **ESCO**: Matching básico con `esco_occupations` (3,045) y `esco_skills` (14,247)
5. **Dashboard Plotly v4**: Control operativo (puerto 8052, 5 tabs)
6. **Dashboard Shiny R v2.4**: Análisis público (6 tabs, 268 ofertas)

**Formato de datos actual (CSV v1):**
```csv
titulo,empresa,ubicacion,descripcion,salario,fecha_publicacion,fecha_scraping,url,
experiencia_min,nivel_educativo,skills_tecnicas,soft_skills,esco_occupation_code,
esco_occupation_label,esco_skills_matched,...
```

### 1.2 Brechas Identificadas

**1.2.1 Ontología ESCO**

| Problema | Impacto | Estado Actual |
|----------|---------|---------------|
| Tabla `esco_associations` VACÍA | No hay relaciones ocupación-skill | 0 registros de 240K esperados |
| Sin clasificación Conocimientos/Competencias | No se puede filtrar por tipo de skill | Campo inexistente |
| Sin relaciones jerárquicas ISCO | No se puede navegar árbol ocupacional | Solo códigos planos |
| RDF local (1.35 GB) sin procesar | Información completa no aprovechada | esco-v1.2.0.rdf disponible |

**1.2.2 Pipeline de Datos**

| Campo Requerido | Estado | Solución Propuesta |
|----------------|--------|-------------------|
| `edad_min`, `edad_max` | No existe | NLP v6.0 con Ollama |
| `ubicacion_provincia_norm` | Texto libre inconsistente | Normalización INDEC |
| `ubicacion_localidad_norm` | Texto libre inconsistente | Fuzzy matching ~4,000 localidades |
| `ubicacion_required` | No existe | NLP v6.0 extracción |
| `permanencia` | No existe | Cálculo heurístico (contrato/plazo/indefinido) |
| `jornada_laboral` | Extracción básica | Mejora con NLP v6.0 |

**1.2.3 Dashboard Shiny**

```
Estado actual (6 tabs):          Diseño requerido (3 paneles):
- Overview General               ├── PANORAMA GENERAL
- Análisis Territorial           │   └── 5 filtros globales + overview
- Habilidades                    ├── REQUERIMIENTOS
- Ocupaciones ESCO               │   └── Skills, educación, experiencia
- Tendencias                     └── OFERTAS LABORALES
- Datos Crudos                       └── Búsqueda + tabla detallada
```

**Filtros faltantes:**
- Territorial por provincia/localidad normalizada
- Período (mes/trimestre/año)
- Permanencia (indefinido/plazo fijo/temporal)
- Búsqueda por título de ocupación
- Navegación árbol ISCO-08

### 1.3 Decisiones Arquitectónicas

**DECISIÓN 1: ESCO como fuente de enriquecimiento offline**

```
ESTRATEGIA: Extracción única RDF → SQLite
- Procesar esco-v1.2.0.rdf UNA VEZ
- Poblar tablas SQLite (~50-100 MB)
- NUNCA consultar RDF en tiempo real
- No servidor triple-store
- No queries SPARQL

JUSTIFICACIÓN:
- No hay servidor disponible para triple-store
- 1.35 GB demasiado pesado para tiempo real
- Datos ESCO estables (actualizaciones anuales)
- SQLite suficiente para 3K ocupaciones + 14K skills
```

**DECISIÓN 2: Clasificación híbrida Conocimientos/Competencias**

```python
# Enfoque de 3 niveles
def clasificar_skill(skill_uri, skill_data):
    # NIVEL 1: skill_type del RDF
    if skill_data['skill_type'] == 'knowledge':
        return 'conocimiento'

    # NIVEL 2: reusability_level
    if skill_data['skill_type'] == 'skill':
        if skill_data['reusability'] in ['transversal', 'cross-sector']:
            return 'competencia'  # Soft skill
        else:
            return 'conocimiento'  # Skill técnico

    # NIVEL 3: Heurísticas + ML (si ambiguo)
    return clasificar_con_heuristicas(skill_data)

# Objetivo: 90% cobertura niveles 1+2, 10% nivel 3
```

**Ejemplo clasificación:**

| Skill Label ES | skill_type | reusability | Clasificación Final | Método |
|---------------|------------|-------------|-------------------|--------|
| SQL | knowledge | cross-sector | **conocimiento** | Nivel 1 (tipo) |
| liderazgo de equipos | skill | transversal | **competencia** | Nivel 2 (reusability) |
| programar en Python | skill | sector-specific | **conocimiento** | Nivel 2 (técnico) |
| comunicación efectiva | skill | transversal | **competencia** | Nivel 2 (soft) |
| normativa laboral argentina | knowledge | occupation-specific | **conocimiento** | Nivel 1 (tipo) |

**DECISIÓN 3: Normalización territorial con INDEC**

```
FUENTE: Códigos INDEC (Sistema Oficial Argentino)
- 24 provincias (código 2 dígitos)
- ~4,000 localidades (código 6 dígitos)
- Variantes de nombre (Buenos Aires/CABA/Bs.As./Capital Federal)

PROCESO:
1. Extraer ubicacion raw del scraping
2. Fuzzy matching con RapidFuzz (score >= 85)
3. Asignar codigo_indec + nombre_oficial
4. Fallback a provincia si localidad no match
```

**DECISIÓN 4: NLP v6.0 con campos adicionales**

```yaml
Prompt NLP v5.1 (actual):           Prompt NLP v6.0 (nuevo):
- experiencia_min/max               - experiencia_min/max
- nivel_educativo                   - nivel_educativo
- skills_tecnicas                   - skills_tecnicas
- soft_skills                       - soft_skills
- salario_min/max                   - salario_min/max
- jornada_laboral                   - jornada_laboral
                                    + edad_min/edad_max (NUEVO)
                                    + ubicacion_required (NUEVO)
                                    + permanencia_tipo (NUEVO)
```

**DECISIÓN 5: No implementar campo género**

```
RIESGO LEGAL: Artículo 81 Ley de Contrato de Trabajo
"Queda prohibido cualquier tipo de discriminación entre
los trabajadores por motivo de sexo..."

DECISIÓN: NO extraer ni almacenar información de género
- Alto riesgo de uso discriminatorio
- No aporta valor analítico justificable
- Incompatible con legislación laboral argentina
```

### 1.4 Stack Tecnológico

| Componente | Tecnología | Versión | Justificación |
|-----------|------------|---------|---------------|
| Base de datos | SQLite | 3.x | Portabilidad, sin servidor, <100 MB |
| NLP | Ollama + llama3.1 | 8b | Local, sin costos API, 8B parámetros suficiente |
| Fuzzy matching | RapidFuzz | 3.x | 10x más rápido que FuzzyWuzzy |
| Dashboard operativo | Plotly Dash | 2.x | Python nativo, interactivo, control tiempo real |
| Dashboard público | Shiny R | 1.8.x | Visualizaciones rápidas, comunidad ESCO |
| Parseo RDF | rdflib | 7.x | Estándar Python para RDF/OWL |
| Scraping | BeautifulSoup + Requests | 4.x | Estable, mantenido |

**Dependencias críticas:**
```txt
rdflib==7.0.0
rapidfuzz==3.5.0
ollama==0.1.0
dash==2.14.0
plotly==5.18.0
pandas==2.1.0
sqlite3 (stdlib)
```

---

## 2. FASE 1: ONTOLOGÍA ESCO

### 2.1 Extracción desde RDF

**Objetivo**: Procesar `esco-v1.2.0.rdf` (1.35 GB) una única vez y poblar tablas SQLite.

**Script**: `scripts/esco_rdf_extractor.py`

```python
# Pseudo-código (arquitectura)
from rdflib import Graph, Namespace

# Namespaces ESCO
ESCO = Namespace("http://data.europa.eu/esco/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ISCO = Namespace("http://data.europa.eu/esco/isco/")

def extract_esco_rdf(rdf_path, db_path):
    g = Graph()
    g.parse(rdf_path, format="xml")

    # 1. Extraer ocupaciones (3,137)
    occupations = extract_occupations(g)
    bulk_insert(db_path, "esco_occupations", occupations)

    # 2. Extraer skills (14,279)
    skills = extract_skills(g)
    bulk_insert(db_path, "esco_skills", skills)

    # 3. Extraer asociaciones (240,000)
    associations = extract_associations(g)
    bulk_insert(db_path, "esco_occupation_skill_associations", associations)

    # 4. Extraer jerarquías ISCO
    hierarchies = extract_isco_hierarchies(g)
    bulk_insert(db_path, "esco_isco_hierarchy", hierarchies)
```

**2.1.1 Ocupaciones**

Query SPARQL conceptual:
```sparql
SELECT ?uri ?preferredLabel_es ?isco_code ?description_es
WHERE {
  ?uri a esco:Occupation .
  ?uri skos:prefLabel ?preferredLabel_es FILTER(lang(?preferredLabel_es) = "es") .
  ?uri esco:iscoGroup ?isco_code .
  OPTIONAL { ?uri dc:description ?description_es FILTER(lang(?description_es) = "es") }
}
```

Resultado esperado:
```
esco_occupations (3,137 registros)
┌────────────────────────────────────────┬─────────────────────┬───────────┬──────────────────┐
│ occupation_uri                         │ label_es            │ isco_code │ description_es   │
├────────────────────────────────────────┼─────────────────────┼───────────┼──────────────────┤
│ http://.../occupation/114e1eff-...     │ desarrollador web   │ 2513      │ Los desarrolla...│
│ http://.../occupation/3ac7fbb4-...     │ gerente de ventas   │ 1221      │ Los gerentes ... │
│ http://.../occupation/9e81adde-...     │ analista contable   │ 2411      │ Los analistas... │
└────────────────────────────────────────┴─────────────────────┴───────────┴──────────────────┘
```

**2.1.2 Skills**

Query SPARQL conceptual:
```sparql
SELECT ?uri ?preferredLabel_es ?skill_type ?reusability_level ?description_es
WHERE {
  ?uri a esco:Skill .
  ?uri skos:prefLabel ?preferredLabel_es FILTER(lang(?preferredLabel_es) = "es") .
  ?uri esco:skillType ?skill_type .
  ?uri esco:skillReuseLevel ?reusability_level .
  OPTIONAL { ?uri dc:description ?description_es FILTER(lang(?description_es) = "es") }
}
```

Resultado esperado:
```
esco_skills (14,279 registros)
┌────────────────────────────────────────┬─────────────────────┬────────────┬─────────────────┐
│ skill_uri                              │ label_es            │ skill_type │ reusability     │
├────────────────────────────────────────┼─────────────────────┼────────────┼─────────────────┤
│ http://.../skill/S1.2.3                │ SQL                 │ knowledge  │ cross-sector    │
│ http://.../skill/S4.5.6                │ liderazgo           │ skill      │ transversal     │
│ http://.../skill/S7.8.9                │ Python programming  │ skill      │ sector-specific │
└────────────────────────────────────────┴─────────────────────┴────────────┴─────────────────┘
```

**2.1.3 Asociaciones Ocupación-Skill**

Query SPARQL conceptual:
```sparql
SELECT ?occupation_uri ?skill_uri ?relation_type
WHERE {
  ?occupation_uri esco:hasEssentialSkill ?skill_uri .
  BIND("essential" AS ?relation_type)
}
UNION
{
  ?occupation_uri esco:hasOptionalSkill ?skill_uri .
  BIND("optional" AS ?relation_type)
}
```

Resultado esperado:
```
esco_occupation_skill_associations (240,000 registros)
┌────────────────────────────────────────┬────────────────────────────────┬──────────────┐
│ occupation_uri                         │ skill_uri                      │ relation_type│
├────────────────────────────────────────┼────────────────────────────────┼──────────────┤
│ http://.../occupation/114e1eff-...     │ http://.../skill/S1.2.3 (SQL)  │ essential    │
│ http://.../occupation/114e1eff-...     │ http://.../skill/S7.8.9 (Py)   │ essential    │
│ http://.../occupation/114e1eff-...     │ http://.../skill/S4.5.6 (lid)  │ optional     │
│ http://.../occupation/3ac7fbb4-...     │ http://.../skill/S4.5.6 (lid)  │ essential    │
└────────────────────────────────────────┴────────────────────────────────┴──────────────┘
```

**2.1.4 Jerarquías ISCO-08**

```
Estructura ISCO-08 (4 niveles):
1 → Gran Grupo (1 dígito)      Ej: 2 = "Profesionales científicos e intelectuales"
25 → Subgrupo (2 dígitos)       Ej: 25 = "Profesionales TIC"
251 → Grupo primario (3 dígitos) Ej: 251 = "Desarrolladores software y analistas"
2513 → Ocupación (4 dígitos)     Ej: 2513 = "Desarrolladores web y multimedia"
```

Resultado esperado:
```
esco_isco_hierarchy
┌───────────┬──────────┬───────────────────────────────────┬────────────────────────────┐
│ isco_code │ level    │ label_es                          │ parent_isco_code           │
├───────────┼──────────┼───────────────────────────────────┼────────────────────────────┤
│ 2         │ 1        │ Profesionales científicos         │ NULL                       │
│ 25        │ 2        │ Profesionales TIC                 │ 2                          │
│ 251       │ 3        │ Desarrolladores software          │ 25                         │
│ 2513      │ 4        │ Desarrolladores web y multimedia  │ 251                        │
└───────────┴──────────┴───────────────────────────────────┴────────────────────────────┘
```

### 2.2 Clasificación Conocimientos vs Competencias

**Algoritmo de 3 niveles:**

```python
def clasificar_skill_categoria(skill_uri, skill_data):
    """
    Retorna: ('conocimiento'|'competencia', método, confidence)
    """

    # NIVEL 1: skill_type directo (75% de casos)
    if skill_data['skill_type'] == 'knowledge':
        return ('conocimiento', 'nivel_1_tipo', 1.0)

    # NIVEL 2: reusability_level (20% de casos)
    if skill_data['skill_type'] == 'skill':
        if skill_data['reusability_level'] in ['transversal', 'cross-sector']:
            return ('competencia', 'nivel_2_reusability', 0.95)
        elif skill_data['reusability_level'] in ['sector-specific', 'occupation-specific']:
            return ('conocimiento', 'nivel_2_reusability', 0.90)

    # NIVEL 3: Heurísticas + keywords (5% de casos ambiguos)
    soft_keywords = ['comunicación', 'liderazgo', 'trabajo en equipo',
                     'adaptabilidad', 'creatividad', 'resolución de problemas']
    tech_keywords = ['programar', 'base de datos', 'lenguaje', 'software',
                     'hardware', 'metodología', 'normativa']

    label_lower = skill_data['label_es'].lower()

    if any(kw in label_lower for kw in soft_keywords):
        return ('competencia', 'nivel_3_heuristica', 0.75)
    elif any(kw in label_lower for kw in tech_keywords):
        return ('conocimiento', 'nivel_3_heuristica', 0.75)
    else:
        # Fallback: clasificar como conocimiento por defecto
        return ('conocimiento', 'nivel_3_fallback', 0.50)
```

**Resultado esperado en tabla actualizada:**

```sql
-- Añadir columnas a esco_skills
ALTER TABLE esco_skills
  ADD COLUMN skill_category TEXT,              -- 'conocimiento' | 'competencia'
  ADD COLUMN classification_method TEXT,       -- 'nivel_1_tipo' | 'nivel_2_reusability' | ...
  ADD COLUMN classification_confidence REAL;   -- 0.0 a 1.0
```

Ejemplo de datos resultantes:
```
esco_skills (actualizado)
┌─────────────────────┬────────────┬─────────────────┬────────────────┬─────────────────────────┬────────────┐
│ label_es            │ skill_type │ reusability     │ skill_category │ classification_method   │ confidence │
├─────────────────────┼────────────┼─────────────────┼────────────────┼─────────────────────────┼────────────┤
│ SQL                 │ knowledge  │ cross-sector    │ conocimiento   │ nivel_1_tipo            │ 1.00       │
│ liderazgo           │ skill      │ transversal     │ competencia    │ nivel_2_reusability     │ 0.95       │
│ Python programming  │ skill      │ sector-specific │ conocimiento   │ nivel_2_reusability     │ 0.90       │
│ comunicación oral   │ skill      │ transversal     │ competencia    │ nivel_2_reusability     │ 0.95       │
│ contabilidad        │ knowledge  │ cross-sector    │ conocimiento   │ nivel_1_tipo            │ 1.00       │
└─────────────────────┴────────────┴─────────────────┴────────────────┴─────────────────────────┴────────────┘
```

**Métricas de validación:**
- Cobertura Nivel 1+2: >= 90%
- Confidence promedio: >= 0.85
- Revisión manual muestra aleatoria: 100 skills

### 2.3 Re-matching con Asociaciones

**Problema**: Las 5,479 ofertas actuales fueron clasificadas SIN utilizar asociaciones ocupación-skill (tabla vacía).

**Solución**: Re-ejecutar matching aprovechando las 240K asociaciones.

**Algoritmo mejorado:**

```python
def match_occupation_with_associations(oferta_skills, esco_data):
    """
    Entrada:
      oferta_skills: ['Python', 'SQL', 'liderazgo', 'trabajo en equipo']
      esco_data: {occupations, skills, associations}

    Salida:
      (occupation_uri, isco_code, confidence_score)
    """

    # 1. Fuzzy match skills de la oferta → esco_skills
    matched_skills = []
    for skill_text in oferta_skills:
        best_match = fuzzy_match(skill_text, esco_data['skills'], threshold=85)
        if best_match:
            matched_skills.append(best_match['uri'])

    # 2. Encontrar ocupaciones que requieren esos skills
    occupation_scores = {}
    for occupation in esco_data['occupations']:
        # Obtener skills esenciales y opcionales de esta ocupación
        essential_skills = get_associated_skills(occupation['uri'], 'essential', esco_data)
        optional_skills = get_associated_skills(occupation['uri'], 'optional', esco_data)

        # Calcular score
        essential_matches = len(set(matched_skills) & set(essential_skills))
        optional_matches = len(set(matched_skills) & set(optional_skills))

        # Fórmula ponderada
        score = (essential_matches * 2.0) + (optional_matches * 1.0)

        # Penalizar si faltan skills esenciales
        if essential_skills:
            coverage = essential_matches / len(essential_skills)
            score *= coverage

        occupation_scores[occupation['uri']] = score

    # 3. Retornar ocupación con mayor score
    best_occupation = max(occupation_scores, key=occupation_scores.get)
    confidence = min(occupation_scores[best_occupation] / 10.0, 1.0)  # Normalizar

    return (best_occupation, get_isco_code(best_occupation), confidence)
```

**Ejemplo de mejora:**

```
OFERTA: "Desarrollador Full Stack"
Skills extraídos por NLP: ['Python', 'JavaScript', 'React', 'SQL', 'Git']

MATCHING ANTERIOR (sin asociaciones):
- Fuzzy match título "Desarrollador Full Stack" → ESCO occupation
- Resultado: ISCO 2513 (confidence: 0.65)

MATCHING NUEVO (con asociaciones):
- Match skills: Python→S7.8.9, JavaScript→S2.3.4, React→S5.6.7, SQL→S1.2.3, Git→S9.1.2
- Ocupaciones candidatas:
  * ISCO 2513 "Desarrolladores web" → 4 essential matches, 1 optional → score=9.0
  * ISCO 2512 "Desarrolladores software" → 3 essential, 2 optional → score=8.0
  * ISCO 2514 "Desarrolladores apps" → 2 essential, 2 optional → score=6.0
- Resultado: ISCO 2513 (confidence: 0.90) ← MEJORA +38%
```

**Proceso de re-matching:**

```bash
# Script: scripts/rematch_ofertas_con_associations.py
# 1. Leer ofertas existentes de tabla ofertas_nlp_history (v5.1)
# 2. Para cada oferta:
#    - Obtener skills_tecnicas + soft_skills
#    - Ejecutar nuevo algoritmo con associations
#    - Actualizar ofertas_esco_matching con nuevos códigos
# 3. Generar reporte de mejoras (coverage, confidence delta)
```

**Métricas esperadas:**
- Ofertas con match ESCO: 95% → 98% (+3%)
- Confidence promedio: 0.65 → 0.85 (+31%)
- Tiempo de procesamiento: ~10 min para 5,479 ofertas

---

## 3. FASE 2: PIPELINE DE DATOS

### 3.1 NLP v6.0 - Nuevos Campos

**Campos adicionales a extraer:**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `edad_min` | INTEGER | Edad mínima requerida | 25 |
| `edad_max` | INTEGER | Edad máxima requerida | 45 |
| `ubicacion_required` | BOOLEAN | ¿Requiere presencialidad en ubicación? | true |
| `permanencia_tipo` | TEXT | Tipo de contrato | 'indefinido' / 'plazo_fijo' / 'temporal' |

**Prompt NLP v6.0 (Ollama llama3.1:8b):**

```json
{
  "system": "Eres un experto en análisis de ofertas laborales argentinas. Extrae información estructurada del texto.",
  "prompt": "Analiza esta oferta laboral y extrae los siguientes campos en formato JSON:\n\nOFERTA:\n{descripcion_completa}\n\nEXTRAER:\n1. experiencia_min_anios: años mínimos de experiencia (null si no especifica)\n2. experiencia_max_anios: años máximos (null si no especifica)\n3. nivel_educativo: 'secundario'|'terciario'|'universitario'|'posgrado'|null\n4. estado_educativo: 'en_curso'|'completo'|'indistinto'|null\n5. carrera_especifica: nombre de carrera si especifica (null si no)\n6. skills_tecnicas: lista de habilidades técnicas/conocimientos\n7. soft_skills: lista de habilidades blandas/competencias\n8. edad_min: edad mínima requerida (null si no especifica)\n9. edad_max: edad máxima requerida (null si no especifica)\n10. ubicacion_required: true si requiere trabajar EN la ubicación publicada, false si remoto/híbrido\n11. permanencia_tipo: 'indefinido'|'plazo_fijo'|'temporal'|'pasantia'|null\n12. jornada_laboral: 'completa'|'parcial'|'por_horas'|null\n13. salario_min: salario mínimo en ARS (null si no especifica)\n14. salario_max: salario máximo en ARS (null si no especifica)\n\nResponde SOLO con JSON válido, sin explicaciones adicionales.",
  "response_format": "json"
}
```

**Ejemplos de extracción:**

**Ejemplo 1: Oferta con edad y permanencia**
```
INPUT (descripcion):
"Buscamos Desarrollador Full Stack para incorporación inmediata.
Requisitos: 3-5 años de experiencia en Python/Django.
Edad: 25 a 40 años. Relación de dependencia. Jornada completa.
Modalidad: 100% remoto."

OUTPUT (NLP v6.0):
{
  "experiencia_min_anios": 3,
  "experiencia_max_anios": 5,
  "nivel_educativo": null,
  "estado_educativo": null,
  "carrera_especifica": null,
  "skills_tecnicas": ["Python", "Django", "Full Stack"],
  "soft_skills": [],
  "edad_min": 25,
  "edad_max": 40,
  "ubicacion_required": false,
  "permanencia_tipo": "indefinido",
  "jornada_laboral": "completa",
  "salario_min": null,
  "salario_max": null
}
```

**Ejemplo 2: Oferta con ubicación requerida**
```
INPUT (descripcion):
"Analista Contable - CABA (Belgrano).
EXCLUYENTE: vivir en CABA o GBA Norte. Presentismo en oficina.
Experiencia mínima 2 años. Contador Público recibido o próximo a recibirse."

OUTPUT (NLP v6.0):
{
  "experiencia_min_anios": 2,
  "experiencia_max_anios": null,
  "nivel_educativo": "universitario",
  "estado_educativo": "completo",
  "carrera_especifica": "Contador Público",
  "skills_tecnicas": ["contabilidad", "análisis contable"],
  "soft_skills": [],
  "edad_min": null,
  "edad_max": null,
  "ubicacion_required": true,
  "permanencia_tipo": null,
  "jornada_laboral": null,
  "salario_min": null,
  "salario_max": null
}
```

**Integración en pipeline:**

```python
# scripts/procesador_ofertas_nlp_v6.py
import ollama

def procesar_oferta_v6(oferta_id, descripcion):
    # Construir prompt v6.0
    prompt = build_prompt_v6(descripcion)

    # Llamar Ollama
    response = ollama.generate(
        model='llama3.1:8b',
        prompt=prompt,
        format='json'
    )

    # Parsear respuesta
    nlp_result = json.loads(response['response'])

    # Guardar en ofertas_nlp_history con version='v6.0'
    save_nlp_result(oferta_id, nlp_result, version='v6.0')

    return nlp_result
```

### 3.2 Normalización Territorial INDEC

**Objetivo**: Convertir ubicaciones de texto libre a códigos INDEC oficiales.

**Datos INDEC:**
- **Fuente**: Códigos geográficos del INDEC (Instituto Nacional de Estadísticas)
- **Estructura**:
  - Provincias: 24 (código 2 dígitos)
  - Localidades: ~4,000 (código 6 dígitos, primeros 2 = provincia)

**Tabla de referencia:**

```sql
CREATE TABLE provincias_argentina (
    codigo_indec TEXT PRIMARY KEY,  -- '06' (Buenos Aires)
    nombre_oficial TEXT,             -- 'Buenos Aires'
    variantes TEXT                   -- JSON: ["Bs.As.", "Bs As", "Buenos Aires", "BA", "Prov. Buenos Aires"]
);

CREATE TABLE localidades_argentina (
    codigo_indec TEXT PRIMARY KEY,  -- '060007' (Bahía Blanca)
    nombre_oficial TEXT,             -- 'Bahía Blanca'
    codigo_provincia TEXT,           -- '06'
    variantes TEXT,                  -- JSON: ["Bahia Blanca", "B. Blanca", ...]
    FOREIGN KEY (codigo_provincia) REFERENCES provincias_argentina(codigo_indec)
);
```

**Ejemplo de datos:**

```
provincias_argentina
┌──────────────┬───────────────────┬─────────────────────────────────────────┐
│ codigo_indec │ nombre_oficial    │ variantes                               │
├──────────────┼───────────────────┼─────────────────────────────────────────┤
│ 02           │ Ciudad de Bs. As. │ ["CABA","Capital Federal","Buenos Ai...│
│ 06           │ Buenos Aires      │ ["Bs.As.","Bs As","BA","Prov. Bs.As."...│
│ 14           │ Córdoba           │ ["Cordoba","Cba","Prov. Córdoba"]       │
└──────────────┴───────────────────┴─────────────────────────────────────────┘

localidades_argentina (ejemplo parcial)
┌──────────────┬───────────────────┬──────────────────┬────────────────────────┐
│ codigo_indec │ nombre_oficial    │ codigo_provincia │ variantes              │
├──────────────┼───────────────────┼──────────────────┼────────────────────────┤
│ 020007       │ Comuna 1          │ 02               │ ["C1","Retiro","..."]  │
│ 060007       │ Bahía Blanca      │ 06               │ ["Bahia Blanca",...]   │
│ 140007       │ Córdoba           │ 14               │ ["Cordoba Capital",...] │
└──────────────┴───────────────────┴──────────────────┴────────────────────────┘
```

**Algoritmo de normalización:**

```python
from rapidfuzz import fuzz, process

def normalizar_ubicacion(ubicacion_raw):
    """
    Entrada: "Caba - Belgrano" / "Bahia Blanca, Bs As" / "Cordoba Capital"
    Salida: {
        'provincia_codigo': '02',
        'provincia_nombre': 'Ciudad de Bs. As.',
        'localidad_codigo': '020007',
        'localidad_nombre': 'Comuna 1',
        'confidence': 0.92
    }
    """

    # 1. Limpiar texto
    ubicacion_clean = ubicacion_raw.strip().lower()

    # 2. Intentar match con LOCALIDADES (más específico)
    localidades = get_all_localidades_con_variantes()  # [(codigo, nombre, variantes)]

    best_localidad = None
    best_score = 0

    for codigo, nombre, variantes in localidades:
        # Probar nombre oficial
        score = fuzz.ratio(ubicacion_clean, nombre.lower())
        if score > best_score:
            best_score = score
            best_localidad = codigo

        # Probar variantes
        for variante in json.loads(variantes):
            score = fuzz.ratio(ubicacion_clean, variante.lower())
            if score > best_score:
                best_score = score
                best_localidad = codigo

    # 3. Si score >= 85, aceptar localidad
    if best_score >= 85:
        localidad_data = get_localidad(best_localidad)
        provincia_data = get_provincia(localidad_data['codigo_provincia'])
        return {
            'provincia_codigo': provincia_data['codigo_indec'],
            'provincia_nombre': provincia_data['nombre_oficial'],
            'localidad_codigo': localidad_data['codigo_indec'],
            'localidad_nombre': localidad_data['nombre_oficial'],
            'confidence': best_score / 100.0
        }

    # 4. Fallback a PROVINCIA (menos específico)
    provincias = get_all_provincias_con_variantes()
    best_provincia = None
    best_score_prov = 0

    for codigo, nombre, variantes in provincias:
        score = fuzz.ratio(ubicacion_clean, nombre.lower())
        if score > best_score_prov:
            best_score_prov = score
            best_provincia = codigo

        for variante in json.loads(variantes):
            score = fuzz.ratio(ubicacion_clean, variante.lower())
            if score > best_score_prov:
                best_score_prov = score
                best_provincia = codigo

    if best_score_prov >= 80:
        provincia_data = get_provincia(best_provincia)
        return {
            'provincia_codigo': provincia_data['codigo_indec'],
            'provincia_nombre': provincia_data['nombre_oficial'],
            'localidad_codigo': None,
            'localidad_nombre': None,
            'confidence': best_score_prov / 100.0
        }

    # 5. Sin match
    return None
```

**Ejemplos de normalización:**

| ubicacion_raw (scraping) | provincia_codigo | provincia_nombre | localidad_codigo | localidad_nombre | confidence |
|-------------------------|------------------|------------------|------------------|------------------|------------|
| "CABA - Belgrano" | 02 | Ciudad de Bs. As. | 020007 | Comuna 1 | 0.88 |
| "Bahia Blanca, Bs As" | 06 | Buenos Aires | 060007 | Bahía Blanca | 0.93 |
| "Cordoba Capital" | 14 | Córdoba | 140007 | Córdoba | 0.95 |
| "Rosario, Santa Fe" | 82 | Santa Fe | 820007 | Rosario | 0.97 |
| "Buenos Aires" | 06 | Buenos Aires | NULL | NULL | 0.85 |

**Actualización de esquema:**

```sql
ALTER TABLE ofertas
  ADD COLUMN provincia_codigo_indec TEXT,
  ADD COLUMN provincia_nombre_norm TEXT,
  ADD COLUMN localidad_codigo_indec TEXT,
  ADD COLUMN localidad_nombre_norm TEXT,
  ADD COLUMN ubicacion_norm_confidence REAL;
```

### 3.3 Cálculo de Permanencia

**Objetivo**: Clasificar tipo de contrato en 4 categorías.

**Categorías:**
1. **indefinido**: Relación de dependencia sin plazo
2. **plazo_fijo**: Contrato por tiempo determinado
3. **temporal**: Proyecto específico, reemplazo, eventual
4. **pasantia**: Becas, prácticas profesionales

**Heurísticas + NLP:**

```python
def calcular_permanencia(descripcion, nlp_result):
    """
    Combina extracción NLP + keywords heurísticos
    """

    # 1. Si NLP v6.0 extrajo permanencia_tipo, usar eso
    if nlp_result.get('permanencia_tipo'):
        return nlp_result['permanencia_tipo']

    # 2. Keywords heurísticos
    desc_lower = descripcion.lower()

    keywords_indefinido = [
        'relación de dependencia', 'contrato indefinido', 'efectivo',
        'planilla permanente', 'estabilidad laboral'
    ]
    keywords_plazo_fijo = [
        'plazo fijo', 'contrato determinado', '6 meses', '1 año',
        'renovable', 'por tiempo determinado'
    ]
    keywords_temporal = [
        'proyecto', 'reemplazo', 'temporal', 'eventual', 'por campaña',
        'freelance', 'por contrato'
    ]
    keywords_pasantia = [
        'pasantía', 'pasante', 'beca', 'práctica profesional',
        'trainee', 'jóvenes profesionales'
    ]

    # Contadores
    scores = {
        'indefinido': sum(1 for kw in keywords_indefinido if kw in desc_lower),
        'plazo_fijo': sum(1 for kw in keywords_plazo_fijo if kw in desc_lower),
        'temporal': sum(1 for kw in keywords_temporal if kw in desc_lower),
        'pasantia': sum(1 for kw in keywords_pasantia if kw in desc_lower)
    }

    # 3. Retornar categoría con mayor score (o null si todos 0)
    max_score = max(scores.values())
    if max_score == 0:
        return None

    return max(scores, key=scores.get)
```

**Ejemplos:**

| Fragmento de descripción | permanencia_tipo |
|-------------------------|------------------|
| "Incorporación efectiva, relación de dependencia indeterminada" | indefinido |
| "Contrato por 6 meses renovable" | plazo_fijo |
| "Proyecto de 3 meses para migración de sistemas" | temporal |
| "Buscamos pasante de Sistemas para sumarse al equipo" | pasantia |

### 3.4 Generación CSV v2.0

**Objetivo**: Crear nuevo formato CSV enriquecido para Shiny dashboard.

**Estructura CSV v1.0 (actual):**
```
48 columnas:
titulo, empresa, ubicacion, descripcion, salario, fecha_publicacion,
experiencia_min, nivel_educativo, skills_tecnicas, soft_skills,
esco_occupation_code, esco_occupation_label, ...
```

**Estructura CSV v2.0 (nueva):**
```
65 columnas (agregamos 17):

# Campos originales (48)
[mantener todos los existentes]

# Campos ESCO enriquecidos (5)
+ esco_isco_hierarchy_level1        # Gran Grupo ISCO
+ esco_isco_hierarchy_level2        # Subgrupo ISCO
+ esco_essential_skills_count       # Cantidad skills esenciales
+ esco_optional_skills_count        # Cantidad skills opcionales
+ esco_matching_confidence          # Score de confianza matching

# Campos NLP v6.0 (4)
+ edad_min
+ edad_max
+ ubicacion_required
+ permanencia_tipo

# Campos territorial INDEC (5)
+ provincia_codigo_indec
+ provincia_nombre_norm
+ localidad_codigo_indec
+ localidad_nombre_norm
+ ubicacion_norm_confidence

# Campos clasificación skills (3)
+ conocimientos_count               # Cantidad de conocimientos
+ competencias_count                # Cantidad de competencias
+ skills_tecnicas_clasificadas      # JSON con categorías
```

**Script de generación:**

```python
# scripts/generate_csv_v2.py

import sqlite3
import pandas as pd
import json

def generate_csv_v2(db_path, output_csv):
    conn = sqlite3.connect(db_path)

    # Query complejo uniendo todas las tablas
    query = """
    SELECT
        o.id,
        o.titulo,
        o.empresa,
        o.ubicacion,
        o.descripcion,
        o.salario,
        o.fecha_publicacion,
        o.fecha_scraping,
        o.url,

        -- NLP v5.1 (existentes)
        nlp.experiencia_min_anios,
        nlp.experiencia_max_anios,
        nlp.nivel_educativo,
        nlp.estado_educativo,
        nlp.carrera_especifica,
        nlp.skills_tecnicas,
        nlp.soft_skills,
        nlp.jornada_laboral,
        nlp.salario_min,
        nlp.salario_max,

        -- NLP v6.0 (nuevos)
        nlp.edad_min,
        nlp.edad_max,
        nlp.ubicacion_required,
        nlp.permanencia_tipo,

        -- ESCO matching
        em.esco_occupation_uri,
        em.esco_occupation_label,
        em.esco_isco_code,
        em.matching_confidence,

        -- Territorial INDEC
        o.provincia_codigo_indec,
        o.provincia_nombre_norm,
        o.localidad_codigo_indec,
        o.localidad_nombre_norm,
        o.ubicacion_norm_confidence

    FROM ofertas o
    LEFT JOIN ofertas_nlp_history nlp ON o.id = nlp.oferta_id
        AND nlp.version = 'v6.0'
    LEFT JOIN ofertas_esco_matching em ON o.id = em.oferta_id
    WHERE o.activa = 1
    """

    df = pd.read_sql_query(query, conn)

    # Enriquecer con jerarquías ISCO
    df['esco_isco_hierarchy_level1'] = df['esco_isco_code'].apply(get_isco_level1)
    df['esco_isco_hierarchy_level2'] = df['esco_isco_code'].apply(get_isco_level2)

    # Enriquecer con conteos de associations
    df['esco_essential_skills_count'] = df['esco_occupation_uri'].apply(
        lambda uri: count_skills(uri, 'essential') if uri else 0
    )
    df['esco_optional_skills_count'] = df['esco_occupation_uri'].apply(
        lambda uri: count_skills(uri, 'optional') if uri else 0
    )

    # Clasificar skills en conocimientos/competencias
    df['conocimientos_count'] = df.apply(count_conocimientos, axis=1)
    df['competencias_count'] = df.apply(count_competencias, axis=1)
    df['skills_tecnicas_clasificadas'] = df.apply(clasificar_skills_json, axis=1)

    # Guardar CSV
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')

    conn.close()

    print(f"✓ CSV v2.0 generado: {len(df)} ofertas, {len(df.columns)} columnas")
    return output_csv
```

**Ejemplo de fila CSV v2.0:**

```csv
id,titulo,empresa,ubicacion,...,edad_min,edad_max,ubicacion_required,permanencia_tipo,provincia_codigo_indec,provincia_nombre_norm,...
2162282,"Desarrollador Full Stack",TechCorp SA,"CABA - Belgrano",...,25,40,false,indefinido,02,"Ciudad de Bs. As.",...
```

**Validaciones:**
- Ofertas activas: >= 5,000
- Columnas totales: 65
- Campos nulos en ubicacion_norm: < 10%
- Campos nulos en permanencia_tipo: < 20%
- Encoding: UTF-8 con BOM para Excel

---

## 4. FASE 3: DASHBOARD SHINY

### 4.1 Arquitectura UI

**Diseño requerido (3 paneles):**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ MONITOR DE OFERTAS LABORALES - ESCO                                     │
│                                                                          │
│ [FILTROS GLOBALES - Sidebar]                                            │
│  □ Territorial (Provincia → Localidad)                                  │
│  □ Período (Mes/Trimestre/Año)                                          │
│  □ Permanencia (Indefinido/Plazo/Temporal/Pasantía)                     │
│  □ Ocupación (Búsqueda texto + árbol ISCO)                              │
│  □ Edad requerida (Rango slider)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ [TAB 1: PANORAMA GENERAL]                                               │
│   Row 1: InfoBoxes (Total ofertas, Provincias activas, Ocupaciones)    │
│   Row 2: Serie temporal (ofertas/mes) + Mapa territorial               │
│   Row 3: Top 10 ocupaciones ESCO + Top 10 empresas                      │
├─────────────────────────────────────────────────────────────────────────┤
│ [TAB 2: REQUERIMIENTOS]                                                 │
│   Row 1: Distribución nivel educativo + Distribución experiencia       │
│   Row 2: Top 20 Conocimientos + Top 20 Competencias (separados)        │
│   Row 3: Distribución jornada + Distribución permanencia               │
├─────────────────────────────────────────────────────────────────────────┤
│ [TAB 3: OFERTAS LABORALES]                                              │
│   Row 1: Búsqueda avanzada (texto libre, filtros específicos)          │
│   Row 2: DataTable interactiva (todas las columnas, exportable)        │
│   Row 3: Detalle de oferta seleccionada (descripción completa)         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Filtros Globales

**Implementación en Shiny (pseudo-código R):**

```r
# ui.R - Sidebar con filtros
sidebarPanel(
  width = 3,

  # FILTRO 1: Territorial (cascada)
  selectInput(
    "filtro_provincia",
    "Provincia:",
    choices = c("Todas", unique(datos$provincia_nombre_norm)),
    selected = "Todas"
  ),

  conditionalPanel(
    condition = "input.filtro_provincia != 'Todas'",
    selectInput(
      "filtro_localidad",
      "Localidad:",
      choices = NULL,  # Reactivo según provincia
      selected = "Todas"
    )
  ),

  # FILTRO 2: Período
  selectInput(
    "filtro_periodo_tipo",
    "Agrupar por:",
    choices = c("Mes", "Trimestre", "Año"),
    selected = "Mes"
  ),

  dateRangeInput(
    "filtro_fecha_rango",
    "Rango de fechas:",
    start = min(datos$fecha_publicacion),
    end = max(datos$fecha_publicacion),
    language = "es"
  ),

  # FILTRO 3: Permanencia
  checkboxGroupInput(
    "filtro_permanencia",
    "Tipo de contrato:",
    choices = c("Indefinido" = "indefinido",
                "Plazo fijo" = "plazo_fijo",
                "Temporal" = "temporal",
                "Pasantía" = "pasantia"),
    selected = c("indefinido", "plazo_fijo", "temporal", "pasantia")
  ),

  # FILTRO 4: Ocupación ESCO (búsqueda + árbol)
  textInput(
    "filtro_ocupacion_buscar",
    "Buscar ocupación:",
    placeholder = "Ej: desarrollador, contador..."
  ),

  # Árbol ISCO (usando shinyTree)
  shinyTree::shinyTree(
    "filtro_isco_tree",
    checkbox = TRUE,
    search = TRUE,
    theme = "proton"
  ),

  # FILTRO 5: Edad requerida
  sliderInput(
    "filtro_edad_rango",
    "Rango de edad:",
    min = 18,
    max = 65,
    value = c(18, 65),
    step = 1
  ),

  # Botón aplicar
  actionButton("aplicar_filtros", "Aplicar Filtros", class = "btn-primary")
)
```

**Lógica reactiva de filtros (server.R):**

```r
# server.R - Reactividad de filtros

# Actualizar localidades según provincia seleccionada
observe({
  if (input$filtro_provincia != "Todas") {
    localidades <- datos %>%
      filter(provincia_nombre_norm == input$filtro_provincia) %>%
      pull(localidad_nombre_norm) %>%
      unique() %>%
      sort()

    updateSelectInput(session, "filtro_localidad",
                      choices = c("Todas", localidades))
  }
})

# Dataset filtrado (reactivo)
datos_filtrados <- eventReactive(input$aplicar_filtros, {
  df <- datos

  # Aplicar filtro territorial
  if (input$filtro_provincia != "Todas") {
    df <- df %>% filter(provincia_nombre_norm == input$filtro_provincia)

    if (!is.null(input$filtro_localidad) && input$filtro_localidad != "Todas") {
      df <- df %>% filter(localidad_nombre_norm == input$filtro_localidad)
    }
  }

  # Aplicar filtro período
  df <- df %>% filter(
    fecha_publicacion >= input$filtro_fecha_rango[1],
    fecha_publicacion <= input$filtro_fecha_rango[2]
  )

  # Aplicar filtro permanencia
  df <- df %>% filter(permanencia_tipo %in% input$filtro_permanencia)

  # Aplicar filtro ocupación (si hay búsqueda)
  if (nchar(input$filtro_ocupacion_buscar) > 0) {
    df <- df %>% filter(
      grepl(input$filtro_ocupacion_buscar, esco_occupation_label, ignore.case = TRUE)
    )
  }

  # Aplicar filtro árbol ISCO (nodos seleccionados)
  nodos_isco <- get_tree(input$filtro_isco_tree)
  if (length(nodos_isco) > 0) {
    df <- df %>% filter(esco_isco_code %in% nodos_isco)
  }

  # Aplicar filtro edad
  df <- df %>% filter(
    (is.na(edad_min) | edad_min >= input$filtro_edad_rango[1]),
    (is.na(edad_max) | edad_max <= input$filtro_edad_rango[2])
  )

  return(df)
})
```

**Árbol ISCO-08 (shinyTree):**

```r
# Generar estructura jerárquica para shinyTree
isco_tree <- list(
  "1 - Directores y Gerentes" = list(
    "11 - Directores Ejecutivos" = list(
      "111 - Legisladores y altos funcionarios" = list(),
      "112 - Directores generales y ejecutivos" = list()
    ),
    "12 - Directores Administración y Servicios" = list(...)
  ),
  "2 - Profesionales Científicos e Intelectuales" = list(
    "21 - Profesionales Ciencias y Ingeniería" = list(...),
    "25 - Profesionales TIC" = list(
      "251 - Desarrolladores Software y Analistas" = list(
        "2511 - Analistas de sistemas",
        "2512 - Desarrolladores de software",
        "2513 - Desarrolladores web y multimedia",
        "2514 - Programadores de aplicaciones"
      ),
      "252 - Especialistas Bases de Datos y Redes" = list(...)
    )
  ),
  "3 - Técnicos y Profesionales de Nivel Medio" = list(...),
  ...
)

# Renderizar árbol
output$filtro_isco_tree <- shinyTree::renderTree({
  isco_tree
})
```

### 4.3 Panel 1: Panorama General

**Componentes:**

```r
# ui.R - Tab Panorama General
tabPanel(
  "Panorama General",

  # Row 1: InfoBoxes
  fluidRow(
    infoBoxOutput("info_total_ofertas", width = 3),
    infoBoxOutput("info_provincias_activas", width = 3),
    infoBoxOutput("info_ocupaciones_unicas", width = 3),
    infoBoxOutput("info_empresas_activas", width = 3)
  ),

  # Row 2: Gráficos principales
  fluidRow(
    box(
      title = "Evolución Temporal de Ofertas",
      width = 8,
      plotlyOutput("plot_serie_temporal", height = 350)
    ),
    box(
      title = "Distribución Territorial",
      width = 4,
      plotlyOutput("plot_mapa_argentina", height = 350)
    )
  ),

  # Row 3: Rankings
  fluidRow(
    box(
      title = "Top 10 Ocupaciones ESCO",
      width = 6,
      plotlyOutput("plot_top_ocupaciones", height = 400)
    ),
    box(
      title = "Top 10 Empresas",
      width = 6,
      plotlyOutput("plot_top_empresas", height = 400)
    )
  )
)
```

**InfoBoxes (server.R):**

```r
# InfoBox 1: Total ofertas
output$info_total_ofertas <- renderInfoBox({
  df <- datos_filtrados()

  infoBox(
    title = "Total Ofertas",
    value = format(nrow(df), big.mark = ".", decimal.mark = ","),
    icon = icon("briefcase"),
    color = "blue",
    fill = TRUE
  )
})

# InfoBox 2: Provincias activas
output$info_provincias_activas <- renderInfoBox({
  df <- datos_filtrados()
  n_provincias <- df %>% pull(provincia_nombre_norm) %>% n_distinct()

  infoBox(
    title = "Provincias",
    value = n_provincias,
    subtitle = "con ofertas activas",
    icon = icon("map-marked-alt"),
    color = "green",
    fill = TRUE
  )
})

# InfoBox 3: Ocupaciones únicas
output$info_ocupaciones_unicas <- renderInfoBox({
  df <- datos_filtrados()
  n_ocupaciones <- df %>% pull(esco_occupation_label) %>% n_distinct()

  infoBox(
    title = "Ocupaciones ESCO",
    value = n_ocupaciones,
    subtitle = "distintas",
    icon = icon("users-cog"),
    color = "purple",
    fill = TRUE
  )
})

# InfoBox 4: Empresas activas
output$info_empresas_activas <- renderInfoBox({
  df <- datos_filtrados()
  n_empresas <- df %>% pull(empresa) %>% n_distinct()

  infoBox(
    title = "Empresas",
    value = n_empresas,
    subtitle = "publicando ofertas",
    icon = icon("building"),
    color = "orange",
    fill = TRUE
  )
})
```

**Serie Temporal (Plotly):**

```r
output$plot_serie_temporal <- renderPlotly({
  df <- datos_filtrados()

  # Agrupar según filtro de período
  df_agregado <- df %>%
    mutate(
      periodo = case_when(
        input$filtro_periodo_tipo == "Mes" ~ floor_date(fecha_publicacion, "month"),
        input$filtro_periodo_tipo == "Trimestre" ~ floor_date(fecha_publicacion, "quarter"),
        input$filtro_periodo_tipo == "Año" ~ floor_date(fecha_publicacion, "year")
      )
    ) %>%
    group_by(periodo) %>%
    summarise(n_ofertas = n(), .groups = "drop")

  # Gráfico Plotly
  plot_ly(df_agregado, x = ~periodo, y = ~n_ofertas, type = "scatter", mode = "lines+markers") %>%
    layout(
      xaxis = list(title = "Período"),
      yaxis = list(title = "Cantidad de Ofertas"),
      hovermode = "x unified"
    )
})
```

**Mapa Argentina (Choropleth):**

```r
output$plot_mapa_argentina <- renderPlotly({
  df <- datos_filtrados()

  # Contar ofertas por provincia
  df_mapa <- df %>%
    group_by(provincia_codigo_indec, provincia_nombre_norm) %>%
    summarise(n_ofertas = n(), .groups = "drop")

  # Crear mapa coroplético
  plot_ly(
    df_mapa,
    type = "choropleth",
    locations = ~provincia_codigo_indec,
    z = ~n_ofertas,
    text = ~paste(provincia_nombre_norm, ":", n_ofertas, "ofertas"),
    colorscale = "Blues",
    marker = list(line = list(color = "white", width = 1))
  ) %>%
    layout(
      geo = list(
        scope = "south america",
        center = list(lon = -63, lat = -38),
        projection = list(type = "mercator")
      )
    )
})
```

**Top 10 Ocupaciones:**

```r
output$plot_top_ocupaciones <- renderPlotly({
  df <- datos_filtrados()

  df_top <- df %>%
    count(esco_occupation_label, esco_isco_code, sort = TRUE) %>%
    head(10) %>%
    mutate(
      label_completo = paste0(esco_occupation_label, " (", esco_isco_code, ")")
    )

  plot_ly(
    df_top,
    x = ~n,
    y = ~reorder(label_completo, n),
    type = "bar",
    orientation = "h",
    marker = list(color = "steelblue")
  ) %>%
    layout(
      xaxis = list(title = "Cantidad de Ofertas"),
      yaxis = list(title = ""),
      margin = list(l = 200)
    )
})
```

### 4.4 Panel 2: Requerimientos

**Componentes:**

```r
# ui.R - Tab Requerimientos
tabPanel(
  "Requerimientos",

  # Row 1: Educación y Experiencia
  fluidRow(
    box(
      title = "Distribución Nivel Educativo",
      width = 6,
      plotlyOutput("plot_nivel_educativo", height = 300)
    ),
    box(
      title = "Distribución Experiencia Requerida",
      width = 6,
      plotlyOutput("plot_experiencia", height = 300)
    )
  ),

  # Row 2: Conocimientos y Competencias (separados)
  fluidRow(
    box(
      title = "Top 20 Conocimientos (Skills Técnicos)",
      width = 6,
      plotlyOutput("plot_top_conocimientos", height = 450)
    ),
    box(
      title = "Top 20 Competencias (Soft Skills)",
      width = 6,
      plotlyOutput("plot_top_competencias", height = 450)
    )
  ),

  # Row 3: Jornada y Permanencia
  fluidRow(
    box(
      title = "Distribución Jornada Laboral",
      width = 6,
      plotlyOutput("plot_jornada", height = 300)
    ),
    box(
      title = "Distribución Tipo de Permanencia",
      width = 6,
      plotlyOutput("plot_permanencia", height = 300)
    )
  )
)
```

**Nivel Educativo (Pie Chart):**

```r
output$plot_nivel_educativo <- renderPlotly({
  df <- datos_filtrados()

  df_edu <- df %>%
    filter(!is.na(nivel_educativo)) %>%
    count(nivel_educativo, sort = TRUE) %>%
    mutate(
      nivel_educativo = factor(nivel_educativo,
        levels = c("secundario", "terciario", "universitario", "posgrado"))
    )

  plot_ly(
    df_edu,
    labels = ~nivel_educativo,
    values = ~n,
    type = "pie",
    textinfo = "label+percent",
    marker = list(colors = c("#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"))
  )
})
```

**Top 20 Conocimientos (separado de Competencias):**

```r
output$plot_top_conocimientos <- renderPlotly({
  df <- datos_filtrados()

  # Extraer skills técnicos clasificados como "conocimiento"
  df_skills <- df %>%
    select(skills_tecnicas_clasificadas) %>%
    filter(!is.na(skills_tecnicas_clasificadas)) %>%
    rowwise() %>%
    mutate(skills_list = list(fromJSON(skills_tecnicas_clasificadas))) %>%
    unnest(skills_list) %>%
    filter(skills_list$categoria == "conocimiento") %>%
    pull(skills_list$label)

  # Contar frecuencias
  df_top <- table(df_skills) %>%
    as.data.frame() %>%
    arrange(desc(Freq)) %>%
    head(20)

  colnames(df_top) <- c("skill", "frecuencia")

  plot_ly(
    df_top,
    x = ~frecuencia,
    y = ~reorder(skill, frecuencia),
    type = "bar",
    orientation = "h",
    marker = list(color = "#3498db")
  ) %>%
    layout(
      xaxis = list(title = "Frecuencia"),
      yaxis = list(title = ""),
      margin = list(l = 150)
    )
})
```

**Top 20 Competencias:**

```r
output$plot_top_competencias <- renderPlotly({
  df <- datos_filtrados()

  # Similar a conocimientos pero filtrar categoria == "competencia"
  df_skills <- df %>%
    select(soft_skills, skills_tecnicas_clasificadas) %>%
    filter(!is.na(skills_tecnicas_clasificadas)) %>%
    rowwise() %>%
    mutate(skills_list = list(fromJSON(skills_tecnicas_clasificadas))) %>%
    unnest(skills_list) %>%
    filter(skills_list$categoria == "competencia") %>%
    pull(skills_list$label)

  df_top <- table(df_skills) %>%
    as.data.frame() %>%
    arrange(desc(Freq)) %>%
    head(20)

  colnames(df_top) <- c("skill", "frecuencia")

  plot_ly(
    df_top,
    x = ~frecuencia,
    y = ~reorder(skill, frecuencia),
    type = "bar",
    orientation = "h",
    marker = list(color = "#e74c3c")
  ) %>%
    layout(
      xaxis = list(title = "Frecuencia"),
      yaxis = list(title = ""),
      margin = list(l = 150)
    )
})
```

### 4.5 Panel 3: Ofertas Laborales

**Componentes:**

```r
# ui.R - Tab Ofertas Laborales
tabPanel(
  "Ofertas Laborales",

  # Row 1: Búsqueda avanzada
  fluidRow(
    box(
      title = "Búsqueda Avanzada",
      width = 12,
      collapsible = TRUE,

      fluidRow(
        column(4, textInput("buscar_titulo", "Título:", placeholder = "Ej: desarrollador")),
        column(4, textInput("buscar_empresa", "Empresa:", placeholder = "Ej: Mercado Libre")),
        column(4, selectInput("buscar_provincia", "Provincia:", choices = NULL))
      ),

      fluidRow(
        column(4, selectInput("buscar_ocupacion_esco", "Ocupación ESCO:", choices = NULL)),
        column(4, sliderInput("buscar_salario_min", "Salario mínimo (ARS):",
                              min = 0, max = 1000000, value = 0, step = 10000)),
        column(4, actionButton("ejecutar_busqueda", "Buscar", class = "btn-success"))
      )
    )
  ),

  # Row 2: Tabla de resultados
  fluidRow(
    box(
      title = "Resultados",
      width = 12,
      DT::dataTableOutput("tabla_ofertas", height = "500px"),
      downloadButton("descargar_ofertas", "Descargar CSV")
    )
  ),

  # Row 3: Detalle de oferta seleccionada
  fluidRow(
    box(
      title = "Detalle de Oferta",
      width = 12,
      collapsible = TRUE,
      collapsed = TRUE,
      uiOutput("detalle_oferta")
    )
  )
)
```

**DataTable interactiva (DT):**

```r
output$tabla_ofertas <- DT::renderDataTable({
  df <- datos_filtrados()

  # Aplicar filtros de búsqueda avanzada
  if (nchar(input$buscar_titulo) > 0) {
    df <- df %>% filter(grepl(input$buscar_titulo, titulo, ignore.case = TRUE))
  }
  if (nchar(input$buscar_empresa) > 0) {
    df <- df %>% filter(grepl(input$buscar_empresa, empresa, ignore.case = TRUE))
  }
  if (!is.null(input$buscar_provincia) && input$buscar_provincia != "Todas") {
    df <- df %>% filter(provincia_nombre_norm == input$buscar_provincia)
  }

  # Seleccionar columnas relevantes para mostrar
  df_tabla <- df %>%
    select(
      id,
      titulo,
      empresa,
      provincia_nombre_norm,
      localidad_nombre_norm,
      esco_occupation_label,
      esco_isco_code,
      nivel_educativo,
      experiencia_min_anios,
      permanencia_tipo,
      jornada_laboral,
      salario_min,
      fecha_publicacion,
      url
    )

  # Renderizar DataTable
  DT::datatable(
    df_tabla,
    options = list(
      pageLength = 25,
      scrollX = TRUE,
      order = list(list(12, "desc")),  # Ordenar por fecha_publicacion desc
      columnDefs = list(
        list(targets = 0, visible = FALSE)  # Ocultar columna id
      )
    ),
    selection = "single",
    rownames = FALSE,
    filter = "top"
  )
})
```

**Detalle de oferta seleccionada:**

```r
output$detalle_oferta <- renderUI({
  df <- datos_filtrados()
  row_selected <- input$tabla_ofertas_rows_selected

  if (length(row_selected) == 0) {
    return(p("Seleccione una oferta de la tabla para ver detalles."))
  }

  oferta <- df[row_selected, ]

  tagList(
    h3(oferta$titulo),
    hr(),

    fluidRow(
      column(6,
        h4("Información General"),
        p(strong("Empresa:"), oferta$empresa),
        p(strong("Ubicación:"), paste(oferta$provincia_nombre_norm, "-", oferta$localidad_nombre_norm)),
        p(strong("Fecha publicación:"), format(oferta$fecha_publicacion, "%d/%m/%Y")),
        p(strong("URL:"), a(href = oferta$url, "Ver oferta original", target = "_blank"))
      ),
      column(6,
        h4("Clasificación ESCO"),
        p(strong("Ocupación:"), oferta$esco_occupation_label),
        p(strong("Código ISCO:"), oferta$esco_isco_code),
        p(strong("Confianza matching:"), sprintf("%.0f%%", oferta$esco_matching_confidence * 100))
      )
    ),

    hr(),

    fluidRow(
      column(12,
        h4("Requerimientos"),
        p(strong("Educación:"), oferta$nivel_educativo, "-", oferta$estado_educativo),
        p(strong("Experiencia:"), paste(oferta$experiencia_min_anios, "-", oferta$experiencia_max_anios, "años")),
        p(strong("Edad:"), if (!is.na(oferta$edad_min)) paste(oferta$edad_min, "-", oferta$edad_max, "años") else "No especifica"),
        p(strong("Permanencia:"), oferta$permanencia_tipo),
        p(strong("Jornada:"), oferta$jornada_laboral)
      )
    ),

    hr(),

    fluidRow(
      column(6,
        h4("Conocimientos"),
        renderUI({
          skills <- fromJSON(oferta$skills_tecnicas_clasificadas)
          conocimientos <- skills %>% filter(categoria == "conocimiento")
          tags$ul(lapply(conocimientos$label, tags$li))
        })
      ),
      column(6,
        h4("Competencias"),
        renderUI({
          skills <- fromJSON(oferta$skills_tecnicas_clasificadas)
          competencias <- skills %>% filter(categoria == "competencia")
          tags$ul(lapply(competencias$label, tags$li))
        })
      )
    ),

    hr(),

    h4("Descripción Completa"),
    p(oferta$descripcion, style = "white-space: pre-wrap; background-color: #f5f5f5; padding: 15px; border-radius: 5px;")
  )
})
```

---

## 5. FASE 4: DASHBOARD PLOTLY v5

### 5.1 Nuevo Tab: Pipeline Monitor

**Objetivo**: Añadir visibilidad sobre el estado del pipeline completo (scraping → NLP → ESCO → productos).

**Diseño del tab:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [TAB 6: PIPELINE MONITOR]                                               │
│                                                                          │
│ Row 1: KPIs del Pipeline                                                │
│   [InfoBox: Ofertas Scraped Hoy] [InfoBox: Procesadas NLP v6.0]        │
│   [InfoBox: Matched ESCO] [InfoBox: Publicadas en Shiny]               │
│                                                                          │
│ Row 2: Flujo del Pipeline (Sankey Diagram)                             │
│   Scraping → Consolidación → NLP → ESCO → Productos                    │
│                                                                          │
│ Row 3: Calidad por Etapa                                                │
│   [Gráfico: Quality Score NLP v6.0 vs v5.1]                            │
│   [Gráfico: Confidence Score ESCO matching con/sin associations]       │
│                                                                          │
│ Row 4: Alertas y Errores                                                │
│   [Tabla: Últimos errores del pipeline con timestamps]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Implementación (pseudo-código Python/Dash):**

```python
# dashboard_scraping_v5.py - Nuevo tab

import dash
from dash import dcc, html
import plotly.graph_objs as go
import plotly.express as px

# Callback para KPIs
@app.callback(
    [Output("kpi_scraped_hoy", "children"),
     Output("kpi_nlp_procesadas", "children"),
     Output("kpi_esco_matched", "children"),
     Output("kpi_publicadas_shiny", "children")],
    [Input("interval-component", "n_intervals")]
)
def update_kpis_pipeline(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    # KPI 1: Ofertas scraped hoy
    hoy = datetime.now().date()
    scraped_hoy = pd.read_sql_query(
        f"SELECT COUNT(*) as n FROM ofertas WHERE DATE(fecha_scraping) = '{hoy}'",
        conn
    )['n'][0]

    # KPI 2: Procesadas NLP v6.0
    nlp_v6 = pd.read_sql_query(
        "SELECT COUNT(DISTINCT oferta_id) as n FROM ofertas_nlp_history WHERE version = 'v6.0'",
        conn
    )['n'][0]

    # KPI 3: Matched ESCO
    esco_matched = pd.read_sql_query(
        "SELECT COUNT(*) as n FROM ofertas_esco_matching WHERE matching_confidence >= 0.7",
        conn
    )['n'][0]

    # KPI 4: Publicadas en Shiny (CSV generado hoy)
    csv_path = "Visual--/ofertas_esco_shiny.csv"
    if os.path.exists(csv_path):
        csv_fecha = datetime.fromtimestamp(os.path.getmtime(csv_path)).date()
        if csv_fecha == hoy:
            publicadas = pd.read_csv(csv_path).shape[0]
        else:
            publicadas = 0
    else:
        publicadas = 0

    conn.close()

    return (
        f"{scraped_hoy:,}",
        f"{nlp_v6:,}",
        f"{esco_matched:,}",
        f"{publicadas:,}"
    )

# Callback para Sankey Diagram
@app.callback(
    Output("sankey_pipeline", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_sankey_pipeline(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    # Obtener métricas de cada etapa
    total_scraped = pd.read_sql_query("SELECT COUNT(*) as n FROM ofertas", conn)['n'][0]
    total_consolidado = pd.read_sql_query("SELECT COUNT(*) as n FROM ofertas WHERE duplicada = 0", conn)['n'][0]
    total_nlp = pd.read_sql_query("SELECT COUNT(DISTINCT oferta_id) as n FROM ofertas_nlp_history WHERE version = 'v6.0'", conn)['n'][0]
    total_esco = pd.read_sql_query("SELECT COUNT(*) as n FROM ofertas_esco_matching WHERE matching_confidence >= 0.7", conn)['n'][0]
    total_productos = 268  # Hardcoded por ahora (leer de CSV)

    conn.close()

    # Construir Sankey
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = [
              "Scraping",
              "Consolidación",
              "NLP v6.0",
              "ESCO Matching",
              "Productos",
              "Descartadas (duplicados)",
              "Sin NLP",
              "Sin ESCO match"
          ],
          color = ["blue", "green", "purple", "orange", "red", "gray", "gray", "gray"]
        ),
        link = dict(
          source = [0, 1, 1, 2, 2, 3, 3],  # índices de nodos origen
          target = [1, 2, 5, 3, 6, 4, 7],  # índices de nodos destino
          value = [
              total_consolidado,                    # Scraping → Consolidación
              total_nlp,                            # Consolidación → NLP
              total_scraped - total_consolidado,    # Consolidación → Descartadas
              total_esco,                           # NLP → ESCO
              total_nlp - total_esco,               # NLP → Sin ESCO
              total_productos,                      # ESCO → Productos
              total_esco - total_productos          # ESCO → Sin productos
          ]
      )
    )])

    fig.update_layout(title_text="Flujo del Pipeline MOL", font_size=10)

    return fig

# Callback para comparación Quality Score
@app.callback(
    Output("plot_quality_score_comparison", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_quality_comparison(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    # Leer A/B test report
    with open("database/ab_test_report.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parsear Quality Scores (hardcoded por ahora, idealmente desde DB)
    scores = {
        'v4.0': 7.89,
        'v5.0': 7.52,
        'v5.1': 8.81
    }

    df = pd.DataFrame(list(scores.items()), columns=['Version', 'Quality Score'])

    fig = px.bar(df, x='Version', y='Quality Score',
                 title="Quality Score por Versión NLP",
                 color='Version',
                 text='Quality Score')

    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_range=[0, 10])

    conn.close()

    return fig
```

**Tabla de errores recientes:**

```python
@app.callback(
    Output("tabla_errores_pipeline", "children"),
    [Input("interval-component", "n_intervals")]
)
def update_tabla_errores(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    # Leer últimos 20 errores del log
    df_errores = pd.read_sql_query("""
        SELECT
            timestamp,
            etapa,
            error_type,
            error_message,
            oferta_id
        FROM pipeline_errors
        ORDER BY timestamp DESC
        LIMIT 20
    """, conn)

    conn.close()

    if df_errores.empty:
        return html.P("✓ No hay errores recientes en el pipeline", style={'color': 'green'})

    # Renderizar tabla con Dash Bootstrap
    return dbc.Table.from_dataframe(df_errores, striped=True, bordered=True, hover=True)
```

### 5.2 Mejoras en Tab Calidad de Parseo NLP

**Objetivo**: Incorporar métricas de NLP v6.0 vs v5.1.

**Gráficos adicionales:**

1. **Cobertura de nuevos campos:**
```python
@app.callback(
    Output("plot_cobertura_campos_v6", "figure"),
    [Input("interval-component", "n_intervals")]
)
def plot_cobertura_v6(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    df = pd.read_sql_query("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN edad_min IS NOT NULL THEN 1 ELSE 0 END) as con_edad_min,
            SUM(CASE WHEN edad_max IS NOT NULL THEN 1 ELSE 0 END) as con_edad_max,
            SUM(CASE WHEN ubicacion_required IS NOT NULL THEN 1 ELSE 0 END) as con_ubicacion_required,
            SUM(CASE WHEN permanencia_tipo IS NOT NULL THEN 1 ELSE 0 END) as con_permanencia
        FROM ofertas_nlp_history
        WHERE version = 'v6.0'
    """, conn)

    conn.close()

    # Calcular porcentajes
    total = df['total'][0]
    porcentajes = {
        'edad_min': df['con_edad_min'][0] / total * 100,
        'edad_max': df['con_edad_max'][0] / total * 100,
        'ubicacion_required': df['con_ubicacion_required'][0] / total * 100,
        'permanencia_tipo': df['con_permanencia'][0] / total * 100
    }

    df_plot = pd.DataFrame(list(porcentajes.items()), columns=['Campo', 'Cobertura (%)'])

    fig = px.bar(df_plot, x='Campo', y='Cobertura (%)',
                 title="Cobertura de Nuevos Campos NLP v6.0",
                 color='Cobertura (%)',
                 color_continuous_scale='Greens')

    fig.update_layout(yaxis_range=[0, 100])

    return fig
```

2. **Distribución de confidence score ESCO (con vs sin associations):**
```python
@app.callback(
    Output("plot_confidence_esco_comparison", "figure"),
    [Input("interval-component", "n_intervals")]
)
def plot_confidence_esco(n):
    conn = sqlite3.connect("database/bumeran_scraping.db")

    # Leer scores de matching
    df = pd.read_sql_query("""
        SELECT
            matching_confidence,
            CASE WHEN used_associations = 1 THEN 'Con Associations' ELSE 'Sin Associations' END as metodo
        FROM ofertas_esco_matching
        WHERE matching_confidence IS NOT NULL
    """, conn)

    conn.close()

    fig = px.histogram(df, x='matching_confidence', color='metodo',
                       barmode='overlay',
                       title="Distribución Confidence Score ESCO Matching",
                       labels={'matching_confidence': 'Confidence Score'},
                       nbins=20)

    return fig
```

---

## 6. FASE 5: TESTING Y VALIDACIÓN

### 6.1 Test Suite ESCO

**Objetivo**: Validar extracción completa de RDF y clasificación de skills.

**Script**: `tests/test_esco_extraction.py`

```python
import unittest
import sqlite3

class TestESCOExtraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect("database/bumeran_scraping.db")

    def test_ocupaciones_count(self):
        """Verificar que se extrajeron ~3,137 ocupaciones"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM esco_occupations")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 3000, "Debe haber al menos 3,000 ocupaciones")
        self.assertLess(count, 3200, "No debe exceder 3,200 ocupaciones")

    def test_skills_count(self):
        """Verificar que se extrajeron ~14,279 skills"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM esco_skills")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 14000, "Debe haber al menos 14,000 skills")
        self.assertLess(count, 15000, "No debe exceder 15,000 skills")

    def test_associations_count(self):
        """Verificar que se extrajeron ~240,000 asociaciones"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM esco_occupation_skill_associations")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 200000, "Debe haber al menos 200,000 asociaciones")
        self.assertLess(count, 260000, "No debe exceder 260,000 asociaciones")

    def test_clasificacion_cobertura(self):
        """Verificar que al menos 90% de skills tienen clasificación"""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN skill_category IS NOT NULL THEN 1 ELSE 0 END) as clasificados
            FROM esco_skills
        """)
        row = cursor.fetchone()
        total, clasificados = row[0], row[1]
        cobertura = clasificados / total
        self.assertGreaterEqual(cobertura, 0.90, "Cobertura de clasificación debe ser >= 90%")

    def test_clasificacion_confidence_promedio(self):
        """Verificar que confidence promedio es >= 0.85"""
        cursor = self.conn.execute("""
            SELECT AVG(classification_confidence) as avg_conf
            FROM esco_skills
            WHERE skill_category IS NOT NULL
        """)
        avg_conf = cursor.fetchone()[0]
        self.assertGreaterEqual(avg_conf, 0.85, "Confidence promedio debe ser >= 0.85")

    def test_jerarquias_isco(self):
        """Verificar que hay 4 niveles ISCO"""
        cursor = self.conn.execute("SELECT DISTINCT level FROM esco_isco_hierarchy ORDER BY level")
        levels = [row[0] for row in cursor.fetchall()]
        self.assertEqual(levels, [1, 2, 3, 4], "Debe haber 4 niveles ISCO")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

if __name__ == "__main__":
    unittest.main()
```

### 6.2 Test Suite NLP v6.0

**Script**: `tests/test_nlp_v6.py`

```python
import unittest
from scripts.procesador_ofertas_nlp_v6 import procesar_oferta_v6

class TestNLPv6(unittest.TestCase):

    def test_extraccion_edad(self):
        """Verificar extracción de edad_min y edad_max"""
        descripcion = "Buscamos desarrollador de 25 a 40 años"
        result = procesar_oferta_v6(oferta_id=999, descripcion=descripcion)

        self.assertEqual(result['edad_min'], 25)
        self.assertEqual(result['edad_max'], 40)

    def test_ubicacion_required_remoto(self):
        """Verificar que detecta modalidad remota"""
        descripcion = "Desarrollador Full Stack - 100% remoto"
        result = procesar_oferta_v6(oferta_id=999, descripcion=descripcion)

        self.assertFalse(result['ubicacion_required'])

    def test_ubicacion_required_presencial(self):
        """Verificar que detecta requerimiento presencial"""
        descripcion = "Analista Contable - EXCLUYENTE vivir en CABA"
        result = procesar_oferta_v6(oferta_id=999, descripcion=descripcion)

        self.assertTrue(result['ubicacion_required'])

    def test_permanencia_indefinido(self):
        """Verificar detección de contrato indefinido"""
        descripcion = "Relación de dependencia, contrato indefinido"
        result = procesar_oferta_v6(oferta_id=999, descripcion=descripcion)

        self.assertEqual(result['permanencia_tipo'], 'indefinido')

    def test_permanencia_plazo_fijo(self):
        """Verificar detección de plazo fijo"""
        descripcion = "Contrato por 6 meses renovable"
        result = procesar_oferta_v6(oferta_id=999, descripcion=descripcion)

        self.assertEqual(result['permanencia_tipo'], 'plazo_fijo')

if __name__ == "__main__":
    unittest.main()
```

### 6.3 Test Suite Normalización Territorial

**Script**: `tests/test_normalizacion_territorial.py`

```python
import unittest
from scripts.normalizador_territorial import normalizar_ubicacion

class TestNormalizacionTerritorial(unittest.TestCase):

    def test_caba_variantes(self):
        """Verificar normalización de variantes de CABA"""
        casos = [
            "CABA",
            "Capital Federal",
            "Buenos Aires (Capital)",
            "Ciudad de Buenos Aires"
        ]

        for caso in casos:
            result = normalizar_ubicacion(caso)
            self.assertEqual(result['provincia_codigo'], '02')
            self.assertEqual(result['provincia_nombre'], 'Ciudad de Bs. As.')

    def test_bahia_blanca(self):
        """Verificar normalización de localidad con tildes"""
        result = normalizar_ubicacion("Bahia Blanca, Bs As")

        self.assertEqual(result['provincia_codigo'], '06')
        self.assertEqual(result['localidad_codigo'], '060007')
        self.assertEqual(result['localidad_nombre'], 'Bahía Blanca')
        self.assertGreaterEqual(result['confidence'], 0.85)

    def test_cordoba_capital(self):
        """Verificar normalización de Córdoba capital"""
        result = normalizar_ubicacion("Cordoba Capital")

        self.assertEqual(result['provincia_codigo'], '14')
        self.assertEqual(result['localidad_codigo'], '140007')
        self.assertGreaterEqual(result['confidence'], 0.90)

    def test_fallback_provincia(self):
        """Verificar fallback a provincia si localidad no matchea"""
        result = normalizar_ubicacion("Buenos Aires")  # Sin especificar localidad

        self.assertEqual(result['provincia_codigo'], '06')
        self.assertEqual(result['provincia_nombre'], 'Buenos Aires')
        self.assertIsNone(result['localidad_codigo'])
        self.assertGreaterEqual(result['confidence'], 0.80)

    def test_no_match(self):
        """Verificar retorno None si no hay match"""
        result = normalizar_ubicacion("XYZ123")  # Texto inválido

        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
```

### 6.4 Validaciones de Calidad

**Script**: `tests/validate_quality.py`

```python
import sqlite3
import pandas as pd

def validate_csv_v2(csv_path):
    """Validar calidad del CSV v2.0"""
    df = pd.read_csv(csv_path)

    print("=== VALIDACIÓN CSV v2.0 ===\n")

    # 1. Validar cantidad de ofertas
    print(f"✓ Total ofertas: {len(df):,}")
    assert len(df) >= 5000, "ERROR: Debe haber al menos 5,000 ofertas"

    # 2. Validar columnas esperadas
    expected_cols = 65
    print(f"✓ Columnas: {len(df.columns)} (esperado: {expected_cols})")
    assert len(df.columns) == expected_cols, f"ERROR: Esperado {expected_cols} columnas"

    # 3. Validar campos clave no nulos
    campos_criticos = ['titulo', 'empresa', 'fecha_publicacion', 'esco_occupation_code']
    for campo in campos_criticos:
        nulos = df[campo].isna().sum()
        pct_nulos = nulos / len(df) * 100
        print(f"✓ {campo}: {pct_nulos:.1f}% nulos")
        assert pct_nulos < 5, f"ERROR: {campo} tiene más de 5% nulos"

    # 4. Validar normalización territorial
    ubicacion_norm_nulos = df['provincia_codigo_indec'].isna().sum() / len(df) * 100
    print(f"✓ Normalización territorial: {100 - ubicacion_norm_nulos:.1f}% cobertura")
    assert ubicacion_norm_nulos < 10, "ERROR: Normalización territorial < 90%"

    # 5. Validar permanencia_tipo
    permanencia_nulos = df['permanencia_tipo'].isna().sum() / len(df) * 100
    print(f"✓ Permanencia tipo: {100 - permanencia_nulos:.1f}% cobertura")
    assert permanencia_nulos < 20, "ERROR: Permanencia tipo < 80%"

    # 6. Validar encoding
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            f.read()
        print("✓ Encoding: UTF-8 con BOM ✓")
    except UnicodeDecodeError:
        raise AssertionError("ERROR: CSV no es UTF-8 con BOM")

    print("\n=== VALIDACIÓN EXITOSA ===")

if __name__ == "__main__":
    validate_csv_v2("Visual--/ofertas_esco_shiny_v2.csv")
```

---

## 7. APÉNDICES

### Apéndice A: Esquemas SQL Completos

**A.1 Tabla esco_occupations**
```sql
CREATE TABLE esco_occupations (
    occupation_uri TEXT PRIMARY KEY,
    label_es TEXT NOT NULL,
    label_en TEXT,
    isco_code TEXT NOT NULL,
    description_es TEXT,
    description_en TEXT,
    alternative_labels_es TEXT,  -- JSON array
    FOREIGN KEY (isco_code) REFERENCES esco_isco_hierarchy(isco_code)
);

CREATE INDEX idx_esco_occupations_isco ON esco_occupations(isco_code);
CREATE INDEX idx_esco_occupations_label_es ON esco_occupations(label_es);
```

**A.2 Tabla esco_skills**
```sql
CREATE TABLE esco_skills (
    skill_uri TEXT PRIMARY KEY,
    label_es TEXT NOT NULL,
    label_en TEXT,
    skill_type TEXT NOT NULL,  -- 'knowledge' | 'skill'
    reusability_level TEXT NOT NULL,  -- 'transversal' | 'cross-sector' | 'sector-specific' | 'occupation-specific'
    description_es TEXT,
    description_en TEXT,
    alternative_labels_es TEXT,  -- JSON array

    -- Clasificación Conocimientos/Competencias (v2.0)
    skill_category TEXT,  -- 'conocimiento' | 'competencia'
    classification_method TEXT,  -- 'nivel_1_tipo' | 'nivel_2_reusability' | 'nivel_3_heuristica' | 'nivel_3_fallback'
    classification_confidence REAL  -- 0.0 a 1.0
);

CREATE INDEX idx_esco_skills_label_es ON esco_skills(label_es);
CREATE INDEX idx_esco_skills_category ON esco_skills(skill_category);
CREATE INDEX idx_esco_skills_type ON esco_skills(skill_type);
```

**A.3 Tabla esco_occupation_skill_associations**
```sql
CREATE TABLE esco_occupation_skill_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occupation_uri TEXT NOT NULL,
    skill_uri TEXT NOT NULL,
    relation_type TEXT NOT NULL,  -- 'essential' | 'optional'
    FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
    FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
    UNIQUE(occupation_uri, skill_uri, relation_type)
);

CREATE INDEX idx_associations_occupation ON esco_occupation_skill_associations(occupation_uri);
CREATE INDEX idx_associations_skill ON esco_occupation_skill_associations(skill_uri);
CREATE INDEX idx_associations_type ON esco_occupation_skill_associations(relation_type);
```

**A.4 Tabla esco_isco_hierarchy**
```sql
CREATE TABLE esco_isco_hierarchy (
    isco_code TEXT PRIMARY KEY,
    level INTEGER NOT NULL,  -- 1, 2, 3, 4
    label_es TEXT NOT NULL,
    label_en TEXT,
    parent_isco_code TEXT,
    FOREIGN KEY (parent_isco_code) REFERENCES esco_isco_hierarchy(isco_code)
);

CREATE INDEX idx_isco_hierarchy_level ON esco_isco_hierarchy(level);
CREATE INDEX idx_isco_hierarchy_parent ON esco_isco_hierarchy(parent_isco_code);
```

**A.5 Tabla provincias_argentina**
```sql
CREATE TABLE provincias_argentina (
    codigo_indec TEXT PRIMARY KEY,
    nombre_oficial TEXT NOT NULL,
    variantes TEXT NOT NULL  -- JSON array: ["Bs.As.", "BA", ...]
);
```

**A.6 Tabla localidades_argentina**
```sql
CREATE TABLE localidades_argentina (
    codigo_indec TEXT PRIMARY KEY,
    nombre_oficial TEXT NOT NULL,
    codigo_provincia TEXT NOT NULL,
    variantes TEXT NOT NULL,  -- JSON array
    FOREIGN KEY (codigo_provincia) REFERENCES provincias_argentina(codigo_indec)
);

CREATE INDEX idx_localidades_provincia ON localidades_argentina(codigo_provincia);
```

**A.7 Tabla ofertas (actualizada)**
```sql
-- Añadir columnas a tabla ofertas existente
ALTER TABLE ofertas ADD COLUMN provincia_codigo_indec TEXT;
ALTER TABLE ofertas ADD COLUMN provincia_nombre_norm TEXT;
ALTER TABLE ofertas ADD COLUMN localidad_codigo_indec TEXT;
ALTER TABLE ofertas ADD COLUMN localidad_nombre_norm TEXT;
ALTER TABLE ofertas ADD COLUMN ubicacion_norm_confidence REAL;

CREATE INDEX idx_ofertas_provincia_norm ON ofertas(provincia_codigo_indec);
CREATE INDEX idx_ofertas_localidad_norm ON ofertas(localidad_codigo_indec);
```

**A.8 Tabla ofertas_nlp_history (actualizada)**
```sql
-- Añadir columnas v6.0 a tabla existente
ALTER TABLE ofertas_nlp_history ADD COLUMN edad_min INTEGER;
ALTER TABLE ofertas_nlp_history ADD COLUMN edad_max INTEGER;
ALTER TABLE ofertas_nlp_history ADD COLUMN ubicacion_required BOOLEAN;
ALTER TABLE ofertas_nlp_history ADD COLUMN permanencia_tipo TEXT;

CREATE INDEX idx_nlp_history_permanencia ON ofertas_nlp_history(permanencia_tipo);
```

**A.9 Tabla ofertas_esco_matching (actualizada)**
```sql
-- Añadir columna para tracking de método
ALTER TABLE ofertas_esco_matching ADD COLUMN used_associations BOOLEAN DEFAULT 0;
ALTER TABLE ofertas_esco_matching ADD COLUMN matching_method TEXT;  -- 'fuzzy_title' | 'skills_associations' | 'hybrid'

CREATE INDEX idx_esco_matching_method ON ofertas_esco_matching(matching_method);
```

**A.10 Tabla pipeline_errors (nueva)**
```sql
CREATE TABLE pipeline_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    etapa TEXT NOT NULL,  -- 'scraping' | 'consolidacion' | 'nlp' | 'esco' | 'productos'
    error_type TEXT NOT NULL,
    error_message TEXT,
    oferta_id INTEGER,
    stack_trace TEXT,
    FOREIGN KEY (oferta_id) REFERENCES ofertas(id)
);

CREATE INDEX idx_pipeline_errors_timestamp ON pipeline_errors(timestamp DESC);
CREATE INDEX idx_pipeline_errors_etapa ON pipeline_errors(etapa);
```

### Apéndice B: Ejemplos de Datos

**B.1 Ejemplo oferta completa (CSV v2.0)**
```csv
id,titulo,empresa,ubicacion,provincia_codigo_indec,provincia_nombre_norm,localidad_codigo_indec,localidad_nombre_norm,
descripcion,fecha_publicacion,fecha_scraping,url,
experiencia_min_anios,experiencia_max_anios,nivel_educativo,estado_educativo,carrera_especifica,
edad_min,edad_max,ubicacion_required,permanencia_tipo,jornada_laboral,
skills_tecnicas,soft_skills,conocimientos_count,competencias_count,
esco_occupation_uri,esco_occupation_label,esco_isco_code,esco_isco_hierarchy_level1,esco_isco_hierarchy_level2,
esco_matching_confidence,esco_essential_skills_count,esco_optional_skills_count,
salario_min,salario_max,...

2162282,"Desarrollador Full Stack Senior","TechCorp SA","CABA - Belgrano","02","Ciudad de Bs. As.","020007","Comuna 1",
"Buscamos Desarrollador Full Stack con experiencia en Python/Django y React...",2025-11-10,2025-11-10,https://bumeran.com/...,
3,5,"universitario","completo","Ingeniería en Sistemas",
25,40,0,"indefinido","completa",
"[""Python"",""Django"",""React"",""PostgreSQL"",""Docker"",""Git""]","[""liderazgo"",""trabajo en equipo"",""comunicación""]",6,3,
"http://data.europa.eu/esco/occupation/114e1eff-...","desarrollador web","2513","2 - Profesionales Científicos","25 - Profesionales TIC",
0.92,15,8,
NULL,NULL,...
```

**B.2 Ejemplo skills_tecnicas_clasificadas (JSON)**
```json
[
  {
    "label": "Python",
    "esco_uri": "http://data.europa.eu/esco/skill/S7.8.9",
    "categoria": "conocimiento",
    "clasificacion_metodo": "nivel_2_reusability",
    "confidence": 0.90
  },
  {
    "label": "Django",
    "esco_uri": "http://data.europa.eu/esco/skill/S7.8.10",
    "categoria": "conocimiento",
    "clasificacion_metodo": "nivel_2_reusability",
    "confidence": 0.90
  },
  {
    "label": "liderazgo",
    "esco_uri": "http://data.europa.eu/esco/skill/S4.5.6",
    "categoria": "competencia",
    "clasificacion_metodo": "nivel_2_reusability",
    "confidence": 0.95
  }
]
```

### Apéndice C: Configuración

**C.1 Archivo .env (variables de entorno)**
```bash
# Base de datos
DB_PATH=database/bumeran_scraping.db

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=120

# RapidFuzz
FUZZY_THRESHOLD_SKILLS=85
FUZZY_THRESHOLD_TERRITORIAL=85
FUZZY_THRESHOLD_PROVINCIA=80

# ESCO
RDF_PATH=D:/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf

# Dashboards
PLOTLY_PORT=8052
SHINY_PORT=3840

# CSV Export
CSV_OUTPUT_PATH=Visual--/ofertas_esco_shiny_v2.csv
CSV_ENCODING=utf-8-sig

# Testing
AB_TEST_SAMPLE_SIZE=50
```

**C.2 Configuración Shiny (config.R)**
```r
# config.R - Configuración global Shiny Dashboard

# Paths
DATA_CSV_PATH <- "ofertas_esco_shiny_v2.csv"
ESCO_TREE_PATH <- "data/esco_isco_tree.rds"

# UI Settings
SIDEBAR_WIDTH <- 3
TABLE_PAGE_LENGTH <- 25
PLOT_HEIGHT <- 350

# Filtros defaults
DEFAULT_DATE_RANGE_DAYS <- 90
DEFAULT_PROVINCIA <- "Todas"
DEFAULT_PERMANENCIA <- c("indefinido", "plazo_fijo", "temporal", "pasantia")
DEFAULT_EDAD_RANGE <- c(18, 65)

# Colores
COLOR_SCHEME <- list(
  primary = "#3498db",
  success = "#2ecc71",
  warning = "#f39c12",
  danger = "#e74c3c",
  info = "#1abc9c"
)
```

### Apéndice D: Troubleshooting

**D.1 Problemas comunes ESCO**

| Error | Causa | Solución |
|-------|-------|----------|
| `MemoryError` al parsear RDF | Archivo 1.35 GB carga en RAM | Usar `rdflib` con chunking o `pyoxigraph` |
| Tabla `esco_associations` sigue vacía | Query SPARQL incorrecto | Revisar predicados `esco:hasEssentialSkill` y `esco:hasOptionalSkill` |
| Clasificación nivel 3 > 10% | Heurísticas insuficientes | Añadir más keywords o entrenar modelo ML |
| URIs duplicadas en associations | Sin constraint UNIQUE | Añadir `UNIQUE(occupation_uri, skill_uri, relation_type)` |

**D.2 Problemas comunes NLP v6.0**

| Error | Causa | Solución |
|-------|-------|----------|
| Ollama timeout | Prompt demasiado largo | Reducir `max_tokens` o usar modelo más pequeño |
| JSON inválido en respuesta | Formato no respetado | Añadir `format='json'` y validar con `json.loads()` |
| Edad extraída incorrecta (ej: 18-65) | Heurística genérica | Mejorar prompt con ejemplos negativos |
| `ubicacion_required` siempre NULL | Palabras clave no detectadas | Ampliar lista de keywords remoto/presencial |

**D.3 Problemas comunes normalización territorial**

| Error | Causa | Solución |
|-------|-------|----------|
| Confidence muy bajo (< 0.5) | Variantes incompletas | Añadir más variantes a tabla INDEC |
| Localidad en CABA no matchea | CABA usa "Comunas" no localidades | Mapear barrios → comunas |
| Provincia ambigua (Buenos Aires vs CABA) | Texto "Buenos Aires" sin contexto | Priorizar CABA si menciona "capital" |
| RapidFuzz lento (>1 seg/oferta) | 4,000 localidades sin índice | Pre-computar embeddings o usar BK-tree |

### Apéndice E: Comandos Útiles

**E.1 Extracción ESCO**
```bash
# Ejecutar extracción completa desde RDF
python scripts/esco_rdf_extractor.py \
  --rdf-path "D:/Trabajos en PY/EPH-ESCO/.../esco-v1.2.0.rdf" \
  --db-path "database/bumeran_scraping.db" \
  --verbose

# Verificar conteos
sqlite3 database/bumeran_scraping.db <<EOF
SELECT 'Occupations' as tabla, COUNT(*) as registros FROM esco_occupations
UNION ALL
SELECT 'Skills', COUNT(*) FROM esco_skills
UNION ALL
SELECT 'Associations', COUNT(*) FROM esco_occupation_skill_associations
UNION ALL
SELECT 'ISCO Hierarchy', COUNT(*) FROM esco_isco_hierarchy;
EOF

# Clasificar skills en conocimientos/competencias
python scripts/clasificar_skills_esco.py --db-path "database/bumeran_scraping.db"
```

**E.2 NLP v6.0**
```bash
# Procesar ofertas con NLP v6.0
python scripts/procesador_ofertas_nlp_v6.py \
  --db-path "database/bumeran_scraping.db" \
  --version "v6.0" \
  --batch-size 50

# Comparar v5.1 vs v6.0 (A/B test)
python scripts/ab_test_nlp_versions.py \
  --ids-file "database/ids_for_ab_test.txt" \
  --output "database/ab_test_v5_vs_v6.txt"
```

**E.3 Normalización territorial**
```bash
# Poblar tablas INDEC
python scripts/populate_indec_tables.py \
  --provincias "data/indec/provincias.csv" \
  --localidades "data/indec/localidades.csv" \
  --db-path "database/bumeran_scraping.db"

# Normalizar ubicaciones de ofertas
python scripts/normalizar_ubicaciones.py \
  --db-path "database/bumeran_scraping.db" \
  --threshold 85
```

**E.4 Re-matching ESCO con associations**
```bash
# Re-ejecutar matching con associations
python scripts/rematch_ofertas_con_associations.py \
  --db-path "database/bumeran_scraping.db" \
  --output-report "database/rematch_report.txt"
```

**E.5 Generación CSV v2.0**
```bash
# Generar CSV enriquecido
python scripts/generate_csv_v2.py \
  --db-path "database/bumeran_scraping.db" \
  --output "Visual--/ofertas_esco_shiny_v2.csv" \
  --encoding "utf-8-sig"

# Validar calidad del CSV
python tests/validate_quality.py \
  --csv-path "Visual--/ofertas_esco_shiny_v2.csv"
```

**E.6 Dashboards**
```bash
# Iniciar Dashboard Plotly v5
python dashboard_scraping_v5.py --port 8052

# Iniciar Dashboard Shiny
Rscript -e "shiny::runApp('Visual--/app.R', port=3840, host='0.0.0.0')"
```

**E.7 Testing**
```bash
# Ejecutar todos los tests
python -m unittest discover tests/

# Ejecutar test específico
python tests/test_esco_extraction.py
python tests/test_nlp_v6.py
python tests/test_normalizacion_territorial.py
```

---

## FIN DEL DOCUMENTO

**Próximos pasos:**
1. Revisar y aprobar este plan técnico
2. Crear documento ejecutivo para colegas
3. Iniciar implementación según fases definidas

**Versión**: 2.0
**Última actualización**: Noviembre 2025
**Estado**: Pendiente aprobación
