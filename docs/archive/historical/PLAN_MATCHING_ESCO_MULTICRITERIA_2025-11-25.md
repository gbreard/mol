# Plan: Reingeniería del Pipeline de Transformación Semántica

---

# ANÁLISIS COMPARATIVO: SISTEMA ACTUAL vs PROPUESTO

## RESUMEN EJECUTIVO

| Aspecto | Sistema Actual | Sistema Propuesto | Diferencia |
|---------|---------------|-------------------|------------|
| **Accuracy estimada** | ~50-60% | >85% objetivo | +25-35% |
| **Tablas de datos** | 3 fragmentadas | 1 unificada | -2 tablas |
| **Uso de NLP** | NO se usa en matching | SI, multicriteria | Habilitado |
| **Diccionario argentino** | 46 términos | 200+ términos | +150 |
| **Alt labels ESCO** | NO se usan (13,796) | SI | Habilitado |
| **Skills en matching** | NO | SI (30% peso) | Nuevo |
| **Gap analysis** | NO existe | SI | Nuevo |
| **Esfuerzo estimado** | - | 5-6 fases | ~80 horas |

---

## 1. ESTADO ACTUAL DEL SISTEMA

### 1.1 Datos Existentes

```
TABLAS PRINCIPALES:
- ofertas:              6,521 registros (scraping completo)
- ofertas_nlp:          5,479 registros (84% procesado)
- ofertas_esco_matching: 6,521 registros (100% matcheado)

RECURSOS ESCO:
- esco_occupations:     3,045 ocupaciones
  - CON codigo ISCO:    1,791 (58.8%) ← PROBLEMA
  - SIN codigo ISCO:    1,254 (41.2%) ← DATOS INCOMPLETOS
- esco_associations:    134,805 relaciones skill-ocupacion
- esco_occupation_alternative_labels: 13,796 ← NO SE USAN
- diccionario_arg_esco: 46 terminos ← MUY POCOS
```

### 1.2 Calidad del Matching Actual

```
DISTRIBUCION DE SCORES (occupation_match_score):
- BAJO (<0.50):       158 ofertas (2.4%)
- MEDIO-BAJO (0.50-0.60): 4,380 ofertas (67.2%) ← MAYORIA AQUI
- MEDIO-ALTO (0.60-0.70): 1,762 ofertas (27.0%)
- ALTO (>0.70):       221 ofertas (3.4%) ← MUY POCOS

ESTADISTICAS:
- Score promedio: 0.5832 (bajo)
- Score minimo:   0.4241
- Score maximo:   0.9785

CONCENTRACION (Top 5 ocupaciones):
1. asistente administrativo...: 291 (4.5%)
2. director comercializacion...: 270 (4.1%)
3. director de ventas...:      158 (2.4%)
4. tecnico analista...:        105 (1.6%)
5. vendedor repuestos...:       97 (1.5%)

HHI < 100 = Alta diversidad (POSITIVO, no hay concentracion extrema)
```

### 1.3 Problemas Detectados

| Problema | Evidencia | Impacto |
|----------|-----------|---------|
| **NLP no se usa en matching** | Score similar con/sin NLP (0.57 vs 0.64) | Skills extraidos desperdiciados |
| **Solo usa titulo** | `match_ofertas_to_esco.py` solo usa titulo | Ignora 80% de la informacion |
| **Alt labels ignorados** | 13,796 labels disponibles, 0 usados | Sinonimos argentinos perdidos |
| **Diccionario muy pequeno** | Solo 46 terminos argentinos | "Jefe de Obra" no se normaliza |
| **41% ISCO faltantes** | 1,254 ocupaciones sin ISCO | Jerarquia incompleta |
| **Tablas fragmentadas** | ofertas, ofertas_nlp, ofertas_esco_matching | JOINs complejos, no hay vista unificada |

---

## 2. LO QUE FUNCIONA (NO CAMBIAR)

### 2.1 Scraping ✓
- 6,521 ofertas completas
- 43 campos extraidos correctamente
- Normalizacion territorial INDEC funcionando

### 2.2 NLP Extraction ✓
- 84% de ofertas procesadas
- Campos extraidos: experiencia, educacion, skills, idiomas
- Hermes 3:8b funcionando

### 2.3 Embeddings BGE-M3 ✓
- Embeddings multilingues de calidad
- 3,045 ocupaciones ESCO indexadas
- Busqueda por similitud funcionando

### 2.4 Reranker ESCO-XLM ✓
- Modelo especializado en ESCO
- Mejora el ranking inicial

---

## 3. LO QUE HAY QUE MEJORAR

### 3.1 PRIORIDAD ALTA

| Mejora | Costo | Beneficio | ROI |
|--------|-------|-----------|-----|
| **Usar NLP en matching** | 8h | +15% accuracy | ALTO |
| **Expandir diccionario argentino** | 16h | +10% accuracy | ALTO |
| **Completar ISCO faltantes** | 4h | 100% jerarquia | ALTO |
| **Usar alt_labels ESCO** | 8h | +5% accuracy | MEDIO |

### 3.2 PRIORIDAD MEDIA

| Mejora | Costo | Beneficio | ROI |
|--------|-------|-----------|-----|
| **Matching multicriteria** | 24h | +15% accuracy | MEDIO |
| **Validacion por area Bumeran** | 8h | -10% errores | MEDIO |
| **Gap analysis skills** | 16h | Nuevo insight | MEDIO |

### 3.3 PRIORIDAD BAJA

| Mejora | Costo | Beneficio | ROI |
|--------|-------|-----------|-----|
| **Tabla unificada** | 8h | Mantenibilidad | BAJO |
| **Ocupaciones relacionadas** | 8h | Movilidad laboral | BAJO |

---

## 4. ANALISIS COSTO-BENEFICIO

### 4.1 Costos de Implementacion

```
FASE 0: Preparacion (prerrequisitos)
  - Completar ISCO faltantes:    4 horas
  - Verificar integridad:        2 horas
  SUBTOTAL:                      6 horas

FASE 1: Diccionarios (paralelo)
  - Expandir diccionario arg:   16 horas
  - Modelo datos unificado:      8 horas
  SUBTOTAL:                     24 horas

FASE 2: Integrar NLP en matching
  - Modificar matcher:           8 horas
  - Tests:                       4 horas
  SUBTOTAL:                     12 horas

FASE 3: Matching multicriteria
  - Implementar combinador:     16 horas
  - Integrar alt_labels:         8 horas
  - Tests y validacion:          8 horas
  SUBTOTAL:                     32 horas

FASE 4: Enriquecimiento ESCO
  - Gap analysis:                8 horas
  - Ocupaciones relacionadas:    8 horas
  SUBTOTAL:                     16 horas

FASE 5: Migracion y validacion
  - Migrar datos:                4 horas
  - Validacion manual:           8 horas
  SUBTOTAL:                     12 horas

=========================================
TOTAL ESTIMADO:                ~80-100 horas
```

### 4.2 Beneficios Esperados

```
CUANTITATIVOS:
- Accuracy matching ESCO: 50-60% → >85% (+25-35%)
- Ofertas con skills gap: 0% → 100%
- Cobertura diccionario: 46 → 200+ terminos
- ISCO completos: 59% → 100%

CUALITATIVOS:
- Trazabilidad completa del matching
- Explicabilidad (por que se asigno X ocupacion)
- Nuevo insight: skills gap analysis
- Mantenibilidad: 1 tabla vs 3
- Validacion por multiples criterios

PARA EL DASHBOARD:
- Filtros por skills especificos
- Indicador de calidad de oferta (cobertura skills)
- Analisis de tendencias en skills demandados
- Recomendaciones a empresas (skills faltantes)
```

### 4.3 Riesgos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| Diccionario insuficiente | Media | Alto | Expansion iterativa |
| Matching mas lento | Baja | Medio | Cache embeddings |
| Regresion accuracy | Baja | Alto | Test A/B con muestra |
| ISCO incorrectos | Baja | Medio | Validacion manual |

---

## 5. ALTERNATIVAS DE IMPLEMENTACION

### OPCION A: Mejora Incremental (RECOMENDADA)
**Solo las mejoras de alto ROI**

```
1. Completar ISCO faltantes (4h)
2. Expandir diccionario argentino (16h)
3. Integrar NLP en matching actual (12h)
4. Usar alt_labels (8h)

TOTAL: ~40 horas
BENEFICIO: +20-25% accuracy
RIESGO: Bajo (cambios pequenos)
```

### OPCION B: Reingenieria Completa
**Todo el plan de 4 capas**

```
Implementar las 5 fases completas

TOTAL: ~80-100 horas
BENEFICIO: +30-35% accuracy + gap analysis
RIESGO: Medio (mas cambios)
```

### OPCION C: Solo Correccion de Datos
**Minimo esfuerzo**

```
1. Completar ISCO faltantes (4h)
2. Agregar 50 terminos al diccionario (8h)

TOTAL: ~12 horas
BENEFICIO: +5-10% accuracy
RIESGO: Muy bajo
```

---

## 7. ALINEAMIENTO CON DOCUMENTACIÓN OFICIAL

### PLAN_TECNICO_MOL_v2.0 (Sección 5.6) define este algoritmo:

```
ALGORITMO DE MATCHING DOCUMENTADO (4 PASOS):

PASO 1: Matching por TÍTULO (50% del score)
  - Similitud entre título oferta y títulos ESCO
  - Levenshtein + TF-IDF + coseno
  - Seleccionar top 3 candidatos con similitud >70%

PASO 2: Matching por SKILLS (40% del score)  ← CRÍTICO
  - Comparar skills NLP vs skills ESCO (essential + optional)
  - Score = (match_optional × 1.0) + (match_essential × 0.5)

PASO 3: Matching por DESCRIPCIÓN (10% del score)
  - Keywords descripción oferta vs descripción ESCO

PASO 4: Calcular SCORE FINAL ponderado
  - Score = (título×0.5) + (skills×0.4) + (descripción×0.1)
  - Si >75%: MATCH CONFIRMADO
  - Si 50-75%: REVISIÓN MANUAL
  - Si <50%: NO MATCH
```

### Lo que el sistema actual implementa:

```
ALGORITMO ACTUAL (solo 1 paso efectivo):

PASO 1: Embedding BGE-M3 del TÍTULO
  - Genera embedding del título
  - Busca top-10 ocupaciones por similitud coseno

PASO 2: Re-ranking ESCO-XLM (opcional)
  - Re-rankea candidatos con modelo especializado

PASO 3: Guardar mejor match
  - SIN usar skills de NLP
  - SIN usar descripción
  - SIN calcular score ponderado

RESULTADO: Solo usa ~50% de lo documentado
```

### COMPARATIVA DIRECTA:

| Componente | Documentación | Sistema Actual | Gap |
|------------|---------------|----------------|-----|
| Título (50%) | SI | SI | 0% |
| Skills (40%) | SI | **NO** | **40%** |
| Descripción (10%) | SI | **NO** | **10%** |
| Score ponderado | SI | **NO** | Falta |
| Threshold 75% | SI | NO (usa 0.424 min) | Diferente |
| Revisión manual | SI | **NO** | Falta |

### CONCLUSIÓN:

**El plan propuesto NO es una reingeniería nueva**, sino **implementar lo que la documentación ya define**.

El sistema actual solo implementa ~50% del algoritmo documentado:
- Falta el PASO 2 (skills) que representa **40% del score**
- Falta el PASO 3 (descripción) que representa **10% del score**
- Falta el umbral de calidad 75% para confirmación automática

---

## 8. MAPEO TECNOLOGÍA → PIPELINE

### Tecnologías disponibles y su rol óptimo:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STACK TECNOLÓGICO DISPONIBLE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. HERMES 3:8b (Ollama)                                                   │
│     ├─ ROL: Extracción de entidades de texto libre                         │
│     ├─ FORTALEZA: Comprensión semántica profunda                           │
│     ├─ DEBILIDAD: Lento (~10s por oferta)                                  │
│     └─ USO ACTUAL: ofertas_nlp (skills, experiencia, educación)            │
│                                                                             │
│  2. BGE-M3 (Sentence-Transformers)                                         │
│     ├─ ROL: Embeddings multilingües de alta calidad                        │
│     ├─ FORTALEZA: Rápido, buena similitud semántica                        │
│     ├─ DEBILIDAD: No especializado en ESCO                                 │
│     └─ USO ACTUAL: Similitud título-ocupación                              │
│                                                                             │
│  3. ESCO-XLM-RoBERTa-Large (HuggingFace)                                   │
│     ├─ ROL: Re-ranking especializado en ontología ESCO                     │
│     ├─ FORTALEZA: Entrenado específicamente con datos ESCO                 │
│     ├─ DEBILIDAD: Solo para re-ranking, no extracción                      │
│     └─ USO ACTUAL: Re-rankea top-10 candidatos de BGE-M3                   │
│                                                                             │
│  4. spaCy (es_core_news_lg) - DISPONIBLE PERO NO USADO                     │
│     ├─ ROL: NER tradicional (entidades nombradas)                          │
│     ├─ FORTALEZA: Muy rápido, reglas determinísticas                       │
│     ├─ DEBILIDAD: Menos flexible que LLM                                   │
│     └─ USO ACTUAL: NO SE USA (todo va a Hermes)                            │
│                                                                             │
│  5. REGEX + Diccionarios                                                   │
│     ├─ ROL: Extracción de patrones conocidos                               │
│     ├─ FORTALEZA: 100% preciso para patrones definidos, instantáneo        │
│     ├─ DEBILIDAD: No generaliza                                            │
│     └─ USO ACTUAL: PARCIAL (solo algunos campos)                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Asignación óptima tecnología → paso del pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         PIPELINE DOCUMENTADO + TECNOLOGÍA ÓPTIMA                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PASO 1: MATCHING POR TÍTULO (50% score)                                    │
│  ────────────────────────────────────────                                   │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │ Título oferta    │───▶│ BGE-M3 embedding │───▶│ Top-10 candidatos│       │
│  │ "Dev Python Sr"  │    │ (384 dims)       │    │ por similitud    │       │
│  └──────────────────┘    └──────────────────┘    └────────┬─────────┘       │
│                                                           │                 │
│                                                           ▼                 │
│                                            ┌──────────────────────────┐     │
│                                            │ ESCO-XLM re-rank top-3   │     │
│                                            │ (modelo especializado)   │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                 │
│  SCORE TÍTULO = similitud_bge_m3 × 0.7 + score_esco_xlm × 0.3              │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  PASO 2: MATCHING POR SKILLS (40% score)  ← CRÍTICO, HOY NO SE HACE         │
│  ────────────────────────────────────────                                   │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │ Skills de NLP    │───▶│ Normalizar skills│───▶│ Buscar en        │       │
│  │ ofertas_nlp      │    │ (diccionario)    │    │ esco_associations│       │
│  │ ["Excel","SQL"]  │    │ ["Excel","SQL"]  │    │                  │       │
│  └──────────────────┘    └──────────────────┘    └────────┬─────────┘       │
│                                                           │                 │
│                                                           ▼                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Para cada candidato ESCO del Paso 1:                                  │  │
│  │   - Obtener skills_essential de esco_associations                     │  │
│  │   - Obtener skills_optional de esco_associations                      │  │
│  │   - Calcular intersección con skills_oferta                           │  │
│  │   - SCORE = (match_optional/total_optional) + (match_essential×1.5)  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TECNOLOGÍA: SQL queries + diccionario de sinónimos (NO necesita modelo)    │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  PASO 3: MATCHING POR DESCRIPCIÓN (10% score)                               │
│  ────────────────────────────────────────────                               │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │ Descripción      │───▶│ BGE-M3 embedding │───▶│ Similitud vs     │       │
│  │ oferta (truncada │    │ (384 dims)       │    │ descripción ESCO │       │
│  │ a 512 tokens)    │    │                  │    │ del candidato    │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│                                                                             │
│  NOTA: Las descripciones ESCO ya están en esco_occupations.description_es   │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  PASO 4: SCORE FINAL PONDERADO                                              │
│  ─────────────────────────────                                              │
│                                                                             │
│  SCORE_FINAL = (score_titulo × 0.50) +                                      │
│                (score_skills × 0.40) +                                      │
│                (score_descripcion × 0.10)                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ SI score_final > 0.75:  MATCH_CONFIRMADO = True                       │  │
│  │ SI 0.50 < score_final ≤ 0.75:  REQUIERE_REVISION = True               │  │
│  │ SI score_final ≤ 0.50:  MATCH_RECHAZADO = True                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resumen de uso de cada tecnología:

| Tecnología | Paso 1 (Título) | Paso 2 (Skills) | Paso 3 (Desc) | Paso 4 (Score) |
|------------|-----------------|-----------------|---------------|----------------|
| **BGE-M3** | SI (embedding) | NO | SI (embedding) | NO |
| **ESCO-XLM** | SI (re-rank) | NO | NO | NO |
| **Hermes** | NO | NO (ya extrajo) | NO | NO |
| **SQL/Dict** | NO | **SI** (lookup) | NO | NO |
| **Cálculo** | NO | NO | NO | **SI** (ponderación) |

### ¿Qué cambia vs implementación actual?

```
ACTUAL:
  BGE-M3 → ESCO-XLM → Guardar mejor match
  (Solo Paso 1, ignora Pasos 2-4)

PROPUESTO:
  BGE-M3 → ESCO-XLM → SQL skills lookup → BGE-M3 desc → Score ponderado
  (Pasos 1-4 completos)

TECNOLOGÍA NUEVA REQUERIDA: NINGUNA
  - BGE-M3: ya cargado ✓
  - ESCO-XLM: ya cargado ✓
  - SQL: ya disponible ✓
  - ofertas_nlp: ya tiene skills ✓
  - esco_associations: ya tiene relaciones ✓
```

---

## 8b. EJEMPLO END-TO-END COMPLETO

### INPUT: Una oferta real de la base de datos

```
OFERTA ID: 1117985034

TABLA ofertas:
├─ titulo: "Analista de auditoría Ssr"
├─ descripcion: "Barbieri S.A busca profesional para desarrollarse en Auditoría.
│               Requisitos: Experiencia 2-5 años. Excel avanzado, Power BI, TOTVS.
│               Estudiantes de Ing. Industrial o Contador. OSDE, bono anual..."
├─ empresa: "VOCARE"
├─ id_area: 1 (Administración)
├─ id_subarea: 83 (Auditoría)
└─ provincia_normalizada: "Buenos Aires"

TABLA ofertas_nlp (ya extraído por Hermes):
├─ experiencia_min_anios: 2
├─ experiencia_max_anios: 5
├─ nivel_educativo: "universitario"
├─ estado_educativo: "en_curso"
├─ skills_tecnicas: ["Excel", "Power BI", "TOTVS"]
├─ skills_blandas: ["trabajo en equipo"]
└─ beneficios: ["OSDE", "bono anual"]
```

---

### PASO 1: MATCHING POR TÍTULO (50%)

```python
# 1.1 Normalizar título
titulo = "Analista de auditoría Ssr"
titulo_normalizado = normalizar(titulo)  # → "analista auditoria"

# 1.2 Generar embedding con BGE-M3
embedding_titulo = bge_m3.encode(titulo_normalizado)  # Vector 384 dims

# 1.3 Buscar top-10 ocupaciones similares
candidatos_titulo = buscar_similares(
    query_embedding=embedding_titulo,
    corpus_embeddings=embeddings_esco_ocupaciones,  # 3,045 ocupaciones
    top_k=10
)

# RESULTADO:
# ┌─────────────────────────────────────────────────────────────────┐
# │ Candidatos por similitud de título:                             │
# │                                                                 │
# │ 1. "auditor/auditora" (C4312)           → sim: 0.847           │
# │ 2. "analista de riesgos aseguradoras"   → sim: 0.723           │
# │ 3. "auditor financiero/a"               → sim: 0.715           │
# │ 4. "analista financiero/a"              → sim: 0.698           │
# │ 5. "analista de sistemas"               → sim: 0.621           │
# │ ... 5 más                                                      │
# └─────────────────────────────────────────────────────────────────┘

# 1.4 Re-ranking con ESCO-XLM (top-3)
candidatos_reranked = esco_xlm.rerank(
    query=titulo_normalizado,
    candidates=candidatos_titulo[:3]
)

# RESULTADO DESPUÉS DE RERANK:
# 1. "auditor/auditora" (C4312)      → score_xlm: 0.912
# 2. "auditor financiero/a"          → score_xlm: 0.834
# 3. "analista de riesgos"           → score_xlm: 0.756

# 1.5 Calcular SCORE_TITULO (para cada candidato)
# score_titulo = sim_bge × 0.7 + score_xlm × 0.3
candidato_1_score_titulo = 0.847 × 0.7 + 0.912 × 0.3 = 0.866
candidato_2_score_titulo = 0.715 × 0.7 + 0.834 × 0.3 = 0.751
candidato_3_score_titulo = 0.723 × 0.7 + 0.756 × 0.3 = 0.733
```

---

### PASO 2: MATCHING POR SKILLS (40%)

```python
# 2.1 Obtener skills de la oferta (de ofertas_nlp)
skills_oferta = ["Excel", "Power BI", "TOTVS"]

# 2.2 Normalizar skills (diccionario de sinónimos)
skills_normalizados = [
    normalizar_skill("Excel"),    # → "Microsoft Excel"
    normalizar_skill("Power BI"), # → "Microsoft Power BI"
    normalizar_skill("TOTVS")     # → "TOTVS" (sin match, queda igual)
]

# 2.3 Para CADA candidato, obtener sus skills ESCO
# SQL Query para candidato 1 "auditor/auditora" (C4312):

"""
SELECT s.preferred_label_es, a.relation_type
FROM esco_associations a
JOIN esco_skills s ON a.skill_uri = s.skill_uri
WHERE a.occupation_uri = 'http://data.europa.eu/esco/occupation/...'
"""

# RESULTADO para "auditor/auditora":
skills_esco_auditor = {
    "essential": [
        "analizar información financiera",
        "elaborar informes de auditoría",
        "evaluar controles internos",
        "Microsoft Excel",           # ← MATCH con oferta
        "normas de auditoría IIA",
        "aplicar procedimientos de auditoría"
    ],
    "optional": [
        "Microsoft Power BI",        # ← MATCH con oferta
        "SAP",
        "gestión de riesgos",
        "comunicar hallazgos"
    ]
}

# 2.4 Calcular intersección
match_essential = {"Microsoft Excel"}        # 1 de 6
match_optional = {"Microsoft Power BI"}      # 1 de 4

# 2.5 Calcular SCORE_SKILLS
# Formula: (match_optional/total_optional) + (match_essential × 1.5 / total_essential)
candidato_1_score_skills = (1/4) + (1 × 1.5 / 6) = 0.25 + 0.25 = 0.50

# Repetir para otros candidatos...
# candidato_2_score_skills = 0.35 (menos matches)
# candidato_3_score_skills = 0.20 (pocos matches)
```

---

### PASO 3: MATCHING POR DESCRIPCIÓN (10%)

```python
# 3.1 Obtener descripción de la oferta (truncada a 512 tokens)
desc_oferta = "Barbieri S.A busca profesional para desarrollarse en Auditoría..."[:512]

# 3.2 Obtener descripción ESCO del candidato
desc_esco_auditor = """
Los auditores examinan y analizan registros financieros de empresas
para verificar su exactitud y conformidad con las normas establecidas.
Realizan evaluaciones de riesgo y controles internos.
"""

# 3.3 Generar embeddings con BGE-M3
emb_oferta = bge_m3.encode(desc_oferta)
emb_esco = bge_m3.encode(desc_esco_auditor)

# 3.4 Calcular similitud coseno
candidato_1_score_desc = cosine_similarity(emb_oferta, emb_esco)  # → 0.723

# Repetir para otros candidatos...
# candidato_2_score_desc = 0.689
# candidato_3_score_desc = 0.612
```

---

### PASO 4: CALCULAR SCORE FINAL PONDERADO

```python
# Formula: score_final = titulo×0.50 + skills×0.40 + descripcion×0.10

# CANDIDATO 1: "auditor/auditora" (C4312)
score_final_1 = (0.866 × 0.50) + (0.50 × 0.40) + (0.723 × 0.10)
              = 0.433 + 0.200 + 0.072
              = 0.705  # ← MEJOR

# CANDIDATO 2: "auditor financiero/a"
score_final_2 = (0.751 × 0.50) + (0.35 × 0.40) + (0.689 × 0.10)
              = 0.376 + 0.140 + 0.069
              = 0.585

# CANDIDATO 3: "analista de riesgos"
score_final_3 = (0.733 × 0.50) + (0.20 × 0.40) + (0.612 × 0.10)
              = 0.367 + 0.080 + 0.061
              = 0.508
```

---

### OUTPUT: Resultado guardado en ofertas_esco_matching

```sql
INSERT INTO ofertas_esco_matching (
    id_oferta,
    esco_occupation_uri,
    esco_occupation_label,
    occupation_match_score,      -- Score final
    occupation_match_method,

    -- Trazabilidad (NUEVO)
    score_titulo,
    score_skills,
    score_descripcion,
    skills_matched_essential,
    skills_matched_optional,
    match_confirmado,
    requiere_revision
) VALUES (
    '1117985034',
    'http://data.europa.eu/esco/occupation/auditor',
    'auditor/auditora',
    0.705,                       -- Score final ponderado
    'multicriteria_v2',

    -- Trazabilidad
    0.866,
    0.500,
    0.723,
    '["Microsoft Excel"]',
    '["Microsoft Power BI"]',
    FALSE,                       -- 0.705 < 0.75, no confirmado automático
    TRUE                         -- 0.50 < 0.705 < 0.75, necesita revisión
);
```

---

### COMPARATIVA: Output actual vs propuesto

```
SISTEMA ACTUAL (solo título):
├─ esco_occupation_label: "analista de riesgos en aseguradoras"  ← INCORRECTO
├─ occupation_match_score: 0.583                                  ← Bajo
├─ match_method: "bge_m3_embedding"
└─ Sin trazabilidad de por qué se eligió

SISTEMA PROPUESTO (multicriteria):
├─ esco_occupation_label: "auditor/auditora"                      ← CORRECTO
├─ occupation_match_score: 0.705                                  ← Mejor
├─ match_method: "multicriteria_v2"
├─ score_titulo: 0.866
├─ score_skills: 0.500 (Excel y Power BI matchearon)
├─ score_descripcion: 0.723
├─ skills_matched: ["Excel", "Power BI"]
└─ requiere_revision: TRUE (para verificación humana)
```

---

### DIAGRAMA DE FLUJO COMPLETO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FLUJO END-TO-END                                    │
└─────────────────────────────────────────────────────────────────────────────┘

TABLA ofertas          TABLA ofertas_nlp         TABLA esco_occupations
┌──────────────┐      ┌──────────────┐          ┌──────────────┐
│ titulo       │      │ skills_tecnicas│         │ 3,045 ocupaciones│
│ descripcion  │      │ experiencia   │          │ c/embeddings  │
│ id_area      │      │ educacion     │          └──────┬───────┘
└──────┬───────┘      └──────┬───────┘                  │
       │                     │                          │
       │     ┌───────────────┘                          │
       │     │                                          │
       ▼     ▼                                          │
┌─────────────────────────────────────────────────────────────────────────┐
│                        MATCHING ENGINE (nuevo)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐     ┌─────────────┐                                    │
│  │  PASO 1     │────▶│   BGE-M3    │────▶ Top-10 candidatos            │
│  │  Título     │     │  embedding  │      por similitud                │
│  │  (50%)      │     └─────────────┘                                    │
│  └─────────────┘            │                                           │
│                             ▼                                           │
│                      ┌─────────────┐                                    │
│                      │  ESCO-XLM   │────▶ Re-rank top-3                │
│                      │  reranker   │                                    │
│                      └─────────────┘                                    │
│                             │                                           │
│  ┌─────────────┐           │                                           │
│  │  PASO 2     │◀──────────┘                                           │
│  │  Skills     │                                                        │
│  │  (40%)      │────▶ SQL lookup en esco_associations                  │
│  └─────────────┘      Comparar skills_oferta vs skills_esco            │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐     ┌─────────────┐                                    │
│  │  PASO 3     │────▶│   BGE-M3    │────▶ Similitud descripción        │
│  │  Descripción│     │  embedding  │                                    │
│  │  (10%)      │     └─────────────┘                                    │
│  └─────────────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PASO 4: Score Final = T×0.5 + S×0.4 + D×0.1                    │   │
│  │                                                                  │   │
│  │  SI score > 0.75 → CONFIRMADO                                   │   │
│  │  SI 0.50 < score ≤ 0.75 → REVISION                              │   │
│  │  SI score ≤ 0.50 → RECHAZADO                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────────┐
                          │ ofertas_esco_matching │
                          │ (con trazabilidad)   │
                          └──────────────────────┘
```

---

## 9. RECOMENDACION FINAL

### La tarea es: IMPLEMENTAR LO DOCUMENTADO

No se trata de "reingeniería" sino de **completar la implementación** del algoritmo definido en PLAN_TECNICO_MOL_v2.0 Sección 5.6.

### Pasos concretos para alinear con documentación:

```
FASE 1: Corregir datos base (~6h)
  1.1 Completar ISCO faltantes (1,254 ocupaciones sin código)
  1.2 Expandir diccionario argentino (46 → 150+ términos)

FASE 2: Implementar matching por skills (~12h)
  2.1 Modificar match_ofertas_to_esco.py
  2.2 Agregar consulta a ofertas_nlp para skills extraídos
  2.3 Comparar skills oferta vs skills ESCO (essential + optional)
  2.4 Calcular score parcial de skills (40% del total)

FASE 3: Implementar matching por descripción (~8h)
  3.1 Agregar análisis de descripción vs descripción ESCO
  3.2 Calcular score parcial de descripción (10% del total)

FASE 4: Calcular score ponderado (~4h)
  4.1 Combinar: título(50%) + skills(40%) + descripción(10%)
  4.2 Implementar thresholds: >75% confirmado, 50-75% revisar
  4.3 Agregar flag "requiere_revision_manual"

FASE 5: Validación (~8h)
  5.1 Re-procesar las 6,521 ofertas
  5.2 Comparar accuracy antes/después con muestra de 100
  5.3 Documentar mejoras
```

### TOTAL: ~38 horas

### Por qué esta es la opción correcta:

1. **Alineado con documentación**: Implementa exactamente lo que el PLAN_TECNICO define
2. **No inventa nada nuevo**: Todo está especificado en Sección 5.6
3. **Corrige gap crítico**: El 40% del score (skills) no se está usando
4. **Medible**: Se puede comparar accuracy antes/después
5. **Bajo riesgo**: Usa datos que ya existen (ofertas_nlp tiene skills)

---

## PROBLEMA ACTUAL

El pipeline actual tiene pasos **DESCONECTADOS**:
```
SCRAPING → ofertas (43 campos)
    ↓ (sin conexión)
NLP → ofertas_nlp (27 campos) ← NO SE USA DESPUÉS
    ↓ (sin conexión)
ESCO → ofertas_esco_matching ← SOLO USA TÍTULO, ignora NLP
```

**Resultado**: Información fragmentada, sin enriquecimiento progresivo.

## NUEVA ARQUITECTURA: ENRIQUECIMIENTO SEMÁNTICO PROGRESIVO

Cada paso INCREMENTA el valor de la oferta, no la segmenta:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OFERTA ENRIQUECIDA (tabla única)                         │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   CAPA 1    │ →  │   CAPA 2    │ →  │   CAPA 3    │ →  │   CAPA 4    │  │
│  │  Scraping   │    │ Extracción  │    │Normalización│    │Enriquecim.  │  │
│  │   (raw)     │    │  NER/NLP    │    │  ESCO       │    │  Semántico  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
│  Cada capa AGREGA campos a la misma oferta                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CAPA 1: DATOS CRUDOS (Scraping + Normalización Territorial)

### 1.1 Fuente de Datos
```
API: https://avisos.bumeran.com.ar/api/...
Método: REST GET con paginación
Frecuencia: Diaria
```

### 1.2 Campos Extraídos (43 campos)

| Campo | Tipo | Ejemplo | Uso posterior |
|-------|------|---------|---------------|
| id_oferta | INT | 1117985034 | PK |
| titulo | TEXT | "Analista de auditoría Ssr" | INPUT Capa 2 NER |
| descripcion | TEXT | "Barbieri S.A busca..." | INPUT Capa 2 NLP |
| empresa | TEXT | "VOCARE" | Contexto |
| id_area | INT | 1 | INPUT Capa 3 (validación) |
| id_subarea | INT | 83 | INPUT Capa 3 (validación) |
| localizacion | TEXT | "Burzaco, Buenos Aires" | INPUT normalización |
| modalidad_trabajo | TEXT | "Presencial" | Filtro dashboard |
| tipo_trabajo | TEXT | "Full-time" | Filtro dashboard |
| fecha_publicacion | DATE | 2025-09-28 | Análisis temporal |

### 1.3 Normalización Territorial (INDEC)

```python
# Input: localizacion = "Burzaco, Buenos Aires"
# Proceso: Fuzzy matching contra catálogo INDEC

normalizar_ubicacion(localizacion) → {
    provincia_indec: "Buenos Aires",
    codigo_provincia: "06",
    localidad_indec: "Burzaco",
    codigo_localidad: "060098"  # Si existe en catálogo
}
```

**Recursos usados:**
- `indec_provincias` (24 provincias)
- Catálogo INDEC de localidades (archivo externo)

### 1.4 Script Actual
```
Archivo: 01_sources/bumeran/scrapers/bumeran_scraper.py
Output: tabla 'ofertas'
```

---

## CAPA 2: EXTRACCIÓN DE ENTIDADES (NER + NLP)

### 2.1 Objetivo
Extraer entidades estructuradas del texto libre. Esto es lo que **PIDE LA EMPRESA**.

### 2.2 Inputs
```
De Capa 1:
- titulo: "Analista de auditoría Ssr"
- descripcion: "Barbieri S.A busca profesional para desarrollarse en Auditoría.
               Requisitos: Experiencia 2-5 años. Excel avanzado, Power BI.
               Estudiantes de Ing. Industrial o Contador. OSDE, bono anual..."
```

### 2.3 Entidades a Extraer

#### A) Del TÍTULO (NER simple)
```python
extraer_titulo("Analista de auditoría Ssr") → {
    ocupacion_raw: "Analista de auditoría",  # Sin nivel
    nivel_seniority: "Ssr",                   # Jr/Ssr/Sr/Lead/Manager
    es_pasantia: False,
    es_temporal: False
}
```

**Técnica:** Regex + lista de patrones de seniority
```python
SENIORITY_PATTERNS = [
    r'\b(Jr|Junior|Trainee|Pasante)\b',
    r'\b(Ssr|Semi\s?Senior)\b',
    r'\b(Sr|Senior)\b',
    r'\b(Lead|Líder|Jefe|Gerente|Manager)\b'
]
```

#### B) De la DESCRIPCIÓN (NER + NLP híbrido)

| Entidad | Técnica | Ejemplo Input | Output |
|---------|---------|---------------|--------|
| **Experiencia** | Regex | "2-5 años de experiencia" | `{min: 2, max: 5}` |
| **Educación** | NER + Clasificación | "Estudiantes de Ing. Industrial" | `{nivel: "universitario", estado: "en_curso", carreras: ["Ing. Industrial"]}` |
| **Skills técnicas** | NER + Diccionario | "Excel avanzado, Power BI" | `["Excel", "Power BI"]` |
| **Skills blandas** | NER + Diccionario | "trabajo en equipo" | `["trabajo en equipo"]` |
| **Certificaciones** | NER | "Normas IIA, COSO" | `["IIA", "COSO"]` |
| **Idiomas** | NER + Regex | "Inglés intermedio" | `[{idioma: "inglés", nivel: "intermedio"}]` |
| **Beneficios** | NER + Diccionario | "OSDE, bono anual" | `["OSDE", "bono anual"]` |
| **Salario** | Regex | "$150.000 - $200.000" | `{min: 150000, max: 200000, moneda: "ARS"}` |

### 2.4 Arquitectura de Extracción

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTRACTOR NER/NLP                            │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   Regex     │    │   spaCy     │    │  Hermes 3   │             │
│  │  Patterns   │    │    NER      │    │   (LLM)     │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                  │                     │
│         v                  v                  v                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              COMBINATOR + VALIDADOR                      │       │
│  │  - Prioriza extracciones más confiables                 │       │
│  │  - Resuelve conflictos                                  │       │
│  │  - Normaliza valores                                    │       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                      │
│                              v                                      │
│                    Entidades Estructuradas                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.5 Detalle por Extractor

#### REGEX (Rápido, Alta Precisión)
```python
# Experiencia
r'(\d+)\s*[-a]\s*(\d+)\s*(años?|years?)\s*(de\s+experiencia)?'
r'(mínimo|al\s+menos)\s*(\d+)\s*(años?)'

# Salario
r'\$?\s*([\d.,]+)\s*[-a]\s*\$?\s*([\d.,]+)'
r'(USD|ARS|pesos)\s*([\d.,]+)'

# Edad (para filtrar - NO confundir con experiencia)
r'(\d+)\s*[-a]\s*(\d+)\s*años\s*(de\s+edad)?'
```

#### spaCy NER (Entidades nombradas)
```python
# Modelo: es_core_news_lg (español)
# Entidades: ORG, PER, LOC, MISC

doc = nlp(descripcion)
for ent in doc.ents:
    if ent.label_ == "ORG":  # Posible certificación o empresa
        ...
```

#### Diccionarios (Lookup)
```python
SKILLS_TECNICAS = {
    "excel": "Microsoft Excel",
    "power bi": "Microsoft Power BI",
    "python": "Python",
    "sql": "SQL",
    ...
}

BENEFICIOS = ["osde", "swiss medical", "bono", "comedor", "gimnasio", ...]

CERTIFICACIONES = ["pmp", "scrum", "itil", "coso", "iia", ...]
```

#### Hermes 3:8b (LLM para casos complejos)
```python
# Solo para campos difíciles de extraer con regex/NER
# Ejemplo: carreras específicas, descripciones ambiguas

prompt = """
Extrae las carreras universitarias mencionadas:
Texto: "Buscamos estudiantes de Ing. Industrial, Sistemas o carreras afines"
Output JSON: {"carreras": ["Ingeniería Industrial", "Ingeniería en Sistemas"]}
"""
```

### 2.6 Output Capa 2 (campos AGREGADOS)

```python
oferta += {
    # Del título
    "ocupacion_raw": "Analista de auditoría",
    "nivel_seniority": "Ssr",

    # De la descripción
    "req_experiencia_min": 2,
    "req_experiencia_max": 5,
    "req_experiencia_area": "auditoría",

    "req_educacion_nivel": "universitario",
    "req_educacion_estado": "en_curso",
    "req_carreras": ["Ingeniería Industrial", "Contador", "Administración"],
    "req_titulo_excluyente": False,

    "req_skills_tecnicas": ["Excel", "Power BI", "TOTVS", "VISMA"],
    "req_skills_blandas": ["trabajo en equipo", "proactividad"],
    "req_certificaciones": ["Normas IIA", "COSO"],
    "req_idiomas": [{"idioma": "español", "nivel": "nativo"}],

    "beneficios": ["OSDE", "bono anual", "comedor"],
    "salario_min": None,
    "salario_max": None,

    # Metadata extracción
    "nlp_confidence": 0.85,
    "nlp_version": "v2.0",
    "extraction_timestamp": "2025-11-25T..."
}
```

### 2.7 Script a Crear/Modificar
```
Archivo actual: database/process_nlp_from_db_v6.py
Archivo nuevo: database/extract_entities_v2.py (arquitectura híbrida)
```

---

## CAPA 3: NORMALIZACIÓN Y MATCHING ESCO

### 3.1 Objetivo
Asignar ocupación ESCO usando **TODAS** las señales de capas anteriores, no solo el título.

### 3.2 Inputs (de Capas 1 y 2)
```python
inputs = {
    # De Capa 1
    "titulo": "Analista de auditoría Ssr",
    "id_area": 1,        # Bumeran: Administración
    "id_subarea": 83,    # Bumeran: Auditoría

    # De Capa 2
    "ocupacion_raw": "Analista de auditoría",
    "nivel_seniority": "Ssr",
    "req_skills_tecnicas": ["Excel", "Power BI", "TOTVS"],
    "req_educacion_nivel": "universitario",
    "req_experiencia_min": 2
}
```

### 3.3 Sub-paso 3A: Normalización Terminológica Argentina

**Antes de cualquier matching, normalizar términos argentinos a estándar ESCO.**

```python
def normalizar_argentino(termino):
    """Usa diccionario_arg_esco + sinonimos_regionales"""

    # Búsqueda en diccionario argentino
    match = buscar_diccionario_arg(termino.lower())
    if match:
        return {
            "termino_normalizado": match["esco_preferred_label"],
            "isco_sugerido": match["isco_target"],
            "confianza": 1.0,
            "metodo": "diccionario_argentino"
        }

    # Búsqueda en labels alternativos ESCO
    match = buscar_alt_labels(termino.lower())
    if match:
        return {
            "termino_normalizado": match["preferred_label"],
            "occupation_uri": match["occupation_uri"],
            "confianza": 0.95,
            "metodo": "esco_alt_label"
        }

    return {"termino_normalizado": termino, "confianza": 0.5, "metodo": "sin_normalizar"}
```

**Ejemplos de normalización:**
| Input (Argentino) | Output (ESCO) | Método |
|-------------------|---------------|--------|
| "Jefe de Obra" | "director de obra" | diccionario_arg |
| "Playero" | "empleado de estación de servicio" | diccionario_arg |
| "Analista de auditoría" | "auditor/auditora" | esco_alt_label |
| "Developer Python" | "programador de aplicaciones" | esco_alt_label |

**Recursos usados:**
- `diccionario_arg_esco` (46 → expandir a 200+)
- `esco_occupation_alternative_labels` (13,796 labels)
- `sinonimos_regionales` (por crear)

### 3.4 Sub-paso 3B: Matching Multicriteria

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MATCHING MULTICRITERIA                                   │
│                                                                             │
│  SEÑAL 1: Ocupación normalizada (peso 0.4)                                  │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ "Analista de auditoría" → búsqueda en ESCO          │                    │
│  │ Candidatos: auditor, analista financiero, etc.      │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                                                             │
│  SEÑAL 2: Skills técnicas (peso 0.3)                                        │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ ["Excel", "Power BI"] → ¿qué ocupaciones ESCO       │                    │
│  │ tienen estos skills como esenciales?                │                    │
│  │ Match: auditor (Excel), analista datos (Power BI)   │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                                                             │
│  SEÑAL 3: Área Bumeran (peso 0.2)                                           │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ id_area=1 (Administración) → ISCO nivel 1: 2,3,4    │                    │
│  │ Filtrar ocupaciones que NO sean de estos grupos     │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                                                             │
│  SEÑAL 4: Nivel educativo (peso 0.1)                                        │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ "universitario" → ISCO nivel 1: 2 (profesionales)   │                    │
│  │ o 3 (técnicos) - no 9 (elementales)                 │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                                                             │
│                              ↓                                               │
│                    COMBINADOR DE SCORES                                      │
│                              ↓                                               │
│                    Mejor match + confianza                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Algoritmo de Matching Detallado

```python
def match_esco_multicriteria(oferta):
    """
    Matching que usa TODAS las señales disponibles
    """
    candidatos = {}

    # SEÑAL 1: Por ocupación normalizada (embedding o lookup)
    ocupacion_norm = normalizar_argentino(oferta.ocupacion_raw)
    if ocupacion_norm["metodo"] == "diccionario_argentino":
        # Match directo - alta confianza
        return crear_match_directo(ocupacion_norm)

    # Si no hay match directo, buscar por embedding
    candidatos_titulo = buscar_embedding_bge_m3(
        query=ocupacion_norm["termino_normalizado"],
        top_k=20
    )
    for c in candidatos_titulo:
        candidatos[c.uri] = {"score_titulo": c.score}

    # SEÑAL 2: Por skills técnicas
    for skill in oferta.req_skills_tecnicas:
        skill_norm = normalizar_skill(skill)
        ocupaciones_con_skill = buscar_ocupaciones_por_skill(skill_norm)
        for ocu in ocupaciones_con_skill:
            if ocu.uri in candidatos:
                candidatos[ocu.uri]["score_skills"] = candidatos[ocu.uri].get("score_skills", 0) + 0.1
            else:
                candidatos[ocu.uri] = {"score_skills": 0.1}

    # SEÑAL 3: Filtro por área Bumeran
    isco_permitidos = MAPEO_AREA_BUMERAN_ISCO.get(oferta.id_area, None)
    if isco_permitidos:
        for uri in list(candidatos.keys()):
            isco = obtener_isco(uri)
            if isco and isco[0] not in isco_permitidos:
                candidatos[uri]["penalizacion_area"] = -0.2

    # SEÑAL 4: Filtro por nivel educativo
    isco_educacion = MAPEO_EDUCACION_ISCO.get(oferta.req_educacion_nivel, None)
    # Similar al anterior...

    # COMBINAR SCORES
    for uri, scores in candidatos.items():
        score_final = (
            scores.get("score_titulo", 0) * 0.4 +
            scores.get("score_skills", 0) * 0.3 +
            scores.get("score_area", 0) * 0.2 +
            scores.get("score_educacion", 0) * 0.1 +
            scores.get("penalizacion_area", 0)
        )
        candidatos[uri]["score_final"] = score_final

    # Seleccionar mejor
    mejor = max(candidatos.items(), key=lambda x: x[1]["score_final"])
    return mejor
```

### 3.6 Mapeos de Validación

```python
# Mapeo Área Bumeran → ISCO nivel 1 permitidos
MAPEO_AREA_BUMERAN_ISCO = {
    1: ["2", "3", "4"],     # Administración → Profesionales, Técnicos, Administrativos
    2: ["2", "3"],         # Ingeniería → Profesionales, Técnicos
    3: ["2", "3"],         # IT → Profesionales, Técnicos
    4: ["5"],              # Comercial → Servicios/Vendedores
    5: ["7", "8", "9"],    # Producción → Operarios, Operadores, Elementales
    # ...
}

# Mapeo Educación → ISCO nivel 1
MAPEO_EDUCACION_ISCO = {
    "doctorado": ["2"],
    "maestria": ["2"],
    "universitario": ["2", "3"],
    "terciario": ["3", "4"],
    "secundario": ["4", "5", "7", "8", "9"],
    "primario": ["9"],
}
```

### 3.7 Output Capa 3 (campos AGREGADOS)

```python
oferta += {
    # OCUPACIÓN ESCO
    "esco_occupation_uri": "http://data.europa.eu/esco/occupation/...",
    "esco_occupation_label": "auditor/auditora",
    "esco_code": "4312.1",

    # JERARQUÍA ISCO-08
    "isco_code": "C4312",
    "isco_nivel1": "4",
    "isco_nivel1_label": "Personal de apoyo administrativo",
    "isco_nivel2": "43",
    "isco_nivel3": "431",
    "isco_nivel4": "4312",

    # TRAZABILIDAD DEL MATCHING
    "match_method": "multicriteria",
    "match_score_final": 0.87,
    "match_signals": {
        "titulo": {"score": 0.85, "termino_usado": "analista de auditoría"},
        "skills": {"score": 0.90, "skills_matched": ["Excel"]},
        "area_bumeran": {"compatible": True, "isco_esperado": ["2","3","4"]},
        "educacion": {"compatible": True}
    },

    # Ocupación normalizada (para trazabilidad)
    "ocupacion_normalizada": "auditor/auditora",
    "normalizacion_metodo": "esco_alt_label"
}
```

### 3.8 Scripts
```
Archivo actual: database/match_ofertas_to_esco.py (solo usa embedding)
Archivo nuevo: database/match_esco_multicriteria.py
```

---

## CAPA 4: ENRIQUECIMIENTO SEMÁNTICO ESCO

### 4.1 Objetivo
Una vez asignada la ocupación ESCO, **enriquecer** la oferta con conocimiento de la ontología:
- Skills que ESCO considera esenciales/opcionales para esa ocupación
- Análisis de brecha entre lo que pide la empresa y lo que ESCO sugiere
- Ocupaciones relacionadas (movilidad laboral)

### 4.2 Inputs (de Capa 3)
```python
inputs = {
    "esco_occupation_uri": "http://data.europa.eu/esco/occupation/abc123",
    "esco_occupation_label": "auditor/auditora",
    "isco_code": "C4312",

    # De Capa 2 (lo que pidió la empresa)
    "req_skills_tecnicas": ["Excel", "Power BI", "TOTVS"]
}
```

### 4.3 Sub-paso 4A: Obtener Skills de ESCO

```python
def obtener_skills_esco(occupation_uri):
    """
    Consulta esco_associations para obtener skills de esta ocupación
    """
    query = """
    SELECT s.skill_uri, s.preferred_label_es, s.skill_type, a.relation_type
    FROM esco_associations a
    JOIN esco_skills s ON a.skill_uri = s.skill_uri
    WHERE a.occupation_uri = ?
    """
    results = db.execute(query, [occupation_uri])

    return {
        "esenciales": [r for r in results if r.relation_type == "essential"],
        "opcionales": [r for r in results if r.relation_type == "optional"]
    }
```

**Ejemplo para "auditor/auditora":**
```python
skills_esco = {
    "esenciales": [
        "elaborar informes de auditoría",
        "analizar información financiera",
        "aplicar normas de auditoría",
        "evaluar controles internos",
        "Microsoft Excel",           # Skill técnico
        "gestionar documentación"
    ],
    "opcionales": [
        "utilizar software de auditoría",
        "comunicar resultados de auditoría",
        "gestión de riesgos"
    ]
}
```

### 4.4 Sub-paso 4B: Análisis de Cobertura (Gap Analysis)

```python
def analizar_cobertura_skills(skills_pedidos, skills_esco):
    """
    Compara lo que la empresa pide vs lo que ESCO sugiere
    """
    # Normalizar para comparación
    pedidos_norm = {normalizar_skill(s).lower() for s in skills_pedidos}
    esco_esenciales_norm = {s.lower() for s in skills_esco["esenciales"]}

    # Calcular intersección
    skills_cubiertos = pedidos_norm & esco_esenciales_norm
    skills_faltantes = esco_esenciales_norm - pedidos_norm
    skills_extra = pedidos_norm - esco_esenciales_norm  # La empresa pide algo extra

    cobertura = len(skills_cubiertos) / len(esco_esenciales_norm) if esco_esenciales_norm else 0

    return {
        "cobertura": cobertura,                    # 0.0 - 1.0
        "skills_cubiertos": list(skills_cubiertos),
        "skills_gap": list(skills_faltantes),      # Lo que falta según ESCO
        "skills_adicionales": list(skills_extra)   # Lo que la empresa agrega
    }
```

**Ejemplo:**
```
Skills pedidos por empresa: ["Excel", "Power BI", "TOTVS"]
Skills ESCO esenciales: ["Excel", "elaborar informes", "evaluar controles", ...]

Cobertura: 1/6 = 16.7%
Gap: ["elaborar informes de auditoría", "evaluar controles internos", ...]
Adicionales: ["Power BI", "TOTVS"] ← La empresa pide cosas que ESCO no considera esenciales
```

### 4.5 Sub-paso 4C: Ocupaciones Relacionadas

```python
def obtener_ocupaciones_relacionadas(occupation_uri):
    """
    Busca ocupaciones similares para análisis de movilidad laboral
    """
    # Opción 1: Por ISCO (misma familia)
    isco = obtener_isco(occupation_uri)
    isco_familia = isco[:3]  # Ej: C431 de C4312

    ocupaciones_misma_familia = buscar_por_isco_prefix(isco_familia)

    # Opción 2: Por skills compartidos
    skills_ocupacion = obtener_skills_esco(occupation_uri)
    ocupaciones_skills_similares = buscar_ocupaciones_con_skills_similares(skills_ocupacion)

    return {
        "misma_familia_isco": ocupaciones_misma_familia,
        "por_skills_similares": ocupaciones_skills_similares
    }
```

### 4.6 Output Capa 4 (campos AGREGADOS)

```python
oferta += {
    # SKILLS DE LA ONTOLOGÍA ESCO
    "esco_skills_esenciales": [
        {"uri": "...", "label": "elaborar informes de auditoría", "type": "skill"},
        {"uri": "...", "label": "analizar información financiera", "type": "skill"},
        {"uri": "...", "label": "Microsoft Excel", "type": "skill"},
        # ... total ~6-20 skills
    ],
    "esco_skills_opcionales": [
        {"uri": "...", "label": "utilizar software de auditoría", "type": "skill"},
        # ... total ~10-30 skills
    ],

    # ANÁLISIS DE COBERTURA
    "skills_cobertura": 0.167,     # 16.7% de skills ESCO cubiertos
    "skills_cubiertos": ["Microsoft Excel"],
    "skills_gap": [                # Lo que ESCO dice que debería pedir
        "elaborar informes de auditoría",
        "evaluar controles internos",
        "aplicar normas de auditoría"
    ],
    "skills_adicionales": [        # Lo que la empresa pide pero ESCO no considera esencial
        "Power BI",
        "TOTVS"
    ],

    # OCUPACIONES RELACIONADAS (movilidad laboral)
    "ocupaciones_relacionadas": [
        {"uri": "...", "label": "auditor financiero/auditora financiera", "isco": "C2411"},
        {"uri": "...", "label": "auditor de calidad/auditora de calidad", "isco": "C2141"},
        {"uri": "...", "label": "contable", "isco": "C4311"}
    ],

    # METADATA DE COMPLETITUD
    "enrichment_completeness": 0.92,  # Qué % del enriquecimiento se pudo hacer
    "enrichment_warnings": [],         # Alertas si algo falló
    "enrichment_timestamp": "2025-11-25T14:30:00"
}
```

### 4.7 Valor Agregado de Esta Capa

| Métrica | Descripción | Uso en Dashboard |
|---------|-------------|------------------|
| `skills_cobertura` | % de skills ESCO mencionados | Indicador de calidad de la oferta |
| `skills_gap` | Skills que faltan según ESCO | Recomendaciones a empresas |
| `skills_adicionales` | Skills extra que pide la empresa | Tendencias del mercado |
| `ocupaciones_relacionadas` | Ocupaciones similares | Análisis de movilidad laboral |

### 4.8 Scripts
```
Archivo nuevo: database/enrich_esco_knowledge.py
```

---

## ESTRUCTURA DE DATOS FINAL

### Una sola tabla: `ofertas_enriquecidas`

```sql
CREATE TABLE ofertas_enriquecidas (
    -- CAPA 1: Scraping
    id_oferta INTEGER PRIMARY KEY,
    titulo TEXT,
    descripcion TEXT,
    empresa TEXT,
    id_area INTEGER,
    id_subarea INTEGER,
    localizacion TEXT,

    -- CAPA 1b: Territorial INDEC
    provincia_indec TEXT,
    codigo_provincia TEXT,
    localidad_indec TEXT,

    -- CAPA 2: Extracción NER/NLP
    ocupacion_raw TEXT,
    ocupacion_nivel TEXT,
    req_experiencia_min INTEGER,
    req_experiencia_max INTEGER,
    req_educacion_nivel TEXT,
    req_skills_tecnicas JSON,    -- ["Excel", "Power BI"]
    req_skills_blandas JSON,
    req_idiomas JSON,
    beneficios JSON,

    -- CAPA 3: Matching ESCO
    esco_occupation_uri TEXT,
    esco_occupation_label TEXT,
    esco_isco_code TEXT,
    match_method TEXT,
    match_score REAL,
    match_signals JSON,

    -- CAPA 4: Enriquecimiento
    esco_skills_esenciales JSON,
    esco_skills_opcionales JSON,
    skills_cobertura REAL,
    skills_gap JSON,
    ocupaciones_relacionadas JSON,

    -- Metadata
    enrichment_completeness REAL,
    processing_timestamp TEXT
);
```

---

## EJEMPLO COMPLETO: UNA OFERTA TRANSFORMADA

```
ENTRADA (Scraping):
  titulo: "Analista de auditoría Ssr"
  descripcion: "Barbieri S.A busca profesional... Excel avanzado, Power BI..."
  id_area: 1, id_subarea: 83

CAPA 2 (NER/NLP):
  ocupacion_raw: "Analista de auditoría"
  ocupacion_nivel: "Ssr"
  req_experiencia: 2-5 años
  req_skills_tecnicas: ["Excel", "Power BI", "TOTVS"]
  req_educacion: "universitario en curso"

CAPA 3 (Matching ESCO):
  esco_occupation: "auditor/auditora" (C4312)
  match_score: 0.87
  match_signals: {titulo: 0.85, skills: 0.90, area: "match"}

CAPA 4 (Enriquecimiento):
  esco_skills_esenciales: ["elaborar informes de auditoría", "analizar información financiera", ...]
  skills_cobertura: 0.65
  skills_gap: ["gestión de riesgos", "control interno"]
  ocupaciones_relacionadas: ["auditor financiero", "auditor interno"]

SALIDA: Oferta completamente enriquecida lista para dashboard
```

---

## CRITERIOS DE ÉXITO

| Métrica | Objetivo |
|---------|----------|
| Ocupación ESCO correcta | >85% accuracy |
| Skills extraídos | >90% recall |
| Cobertura ESCO calculada | 100% ofertas |
| Tiempo procesamiento | <2s por oferta |

---

## CRONOGRAMA DE IMPLEMENTACIÓN

### Dependencias entre Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GRAFO DE DEPENDENCIAS                                │
│                                                                             │
│  ┌─────────────┐                                                            │
│  │   FASE 0    │  Preparación de datos base                                 │
│  │  Diccionarios│                                                           │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         v                                                                   │
│  ┌─────────────┐     ┌─────────────┐                                        │
│  │   FASE 1    │     │   FASE 1    │  (paralelo)                            │
│  │  Modelo DB  │     │  Diccionario│                                        │
│  │             │     │  Argentino  │                                        │
│  └──────┬──────┘     └──────┬──────┘                                        │
│         │                   │                                               │
│         v                   v                                               │
│  ┌─────────────────────────────────┐                                        │
│  │           FASE 2                │                                        │
│  │   Extractor NER/NLP (Capa 2)    │                                        │
│  └──────────────┬──────────────────┘                                        │
│                 │                                                           │
│                 v                                                           │
│  ┌─────────────────────────────────┐                                        │
│  │           FASE 3                │                                        │
│  │   Matching Multicriteria        │                                        │
│  │   (Capa 3)                      │                                        │
│  └──────────────┬──────────────────┘                                        │
│                 │                                                           │
│                 v                                                           │
│  ┌─────────────────────────────────┐                                        │
│  │           FASE 4                │                                        │
│  │   Enriquecimiento ESCO          │                                        │
│  │   (Capa 4)                      │                                        │
│  └──────────────┬──────────────────┘                                        │
│                 │                                                           │
│                 v                                                           │
│  ┌─────────────────────────────────┐                                        │
│  │           FASE 5                │                                        │
│  │   Migración + Validación        │                                        │
│  └─────────────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FASE 0: Preparación (Prerequisitos)

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 0.1 | Completar códigos ISCO faltantes en esco_occupations | `fix_isco_codes.py` |
| 0.2 | Verificar integridad de esco_associations | Query de validación |
| 0.3 | Documentar áreas/subareas de Bumeran | `mapeo_areas_bumeran.json` |

**Dependencias:** Ninguna
**Bloquea:** Fase 1, 2, 3

---

### FASE 1: Modelo de Datos + Diccionarios (PARALELO)

#### 1A: Crear Modelo de Datos Unificado

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 1A.1 | Crear tabla `ofertas_enriquecidas` | `create_ofertas_enriquecidas.sql` |
| 1A.2 | Crear índices para búsqueda | Índices en skills, ocupación |
| 1A.3 | Crear vistas para dashboard | `views_dashboard.sql` |

#### 1B: Expandir Diccionario Argentino

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 1B.1 | Analizar títulos más frecuentes | Query + análisis manual |
| 1B.2 | Mapear 100 términos argentinos | `diccionario_argentino_v2.json` |
| 1B.3 | Insertar en `diccionario_arg_esco` | `populate_diccionario.py` |
| 1B.4 | Crear `sinonimos_regionales` | Tabla nueva |

**Dependencias:** Fase 0
**Bloquea:** Fase 2, 3

---

### FASE 2: Extractor NER/NLP (Capa 2)

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 2.1 | Crear extractores regex | `extractors/regex_extractor.py` |
| 2.2 | Configurar spaCy para español | `extractors/spacy_extractor.py` |
| 2.3 | Crear diccionarios de lookup | `data/skills_dict.json`, `data/beneficios.json` |
| 2.4 | Integrar Hermes para casos complejos | `extractors/llm_extractor.py` |
| 2.5 | Crear combinador de extractores | `extractors/entity_combinator.py` |
| 2.6 | Tests unitarios | `tests/test_extractors.py` |
| 2.7 | Procesar batch de prueba (100 ofertas) | Validación manual |

**Dependencias:** Fase 1A (modelo de datos)
**Bloquea:** Fase 3

---

### FASE 3: Matching Multicriteria (Capa 3)

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 3.1 | Crear normalizador argentino | `matching/normalizer.py` |
| 3.2 | Crear buscador por alt_labels | `matching/alt_label_search.py` |
| 3.3 | Crear matcher por skills | `matching/skill_matcher.py` |
| 3.4 | Crear validador por área Bumeran | `matching/area_validator.py` |
| 3.5 | Crear combinador multicriteria | `matching/multicriteria_matcher.py` |
| 3.6 | Tests con casos conocidos | 50 ofertas anotadas manualmente |
| 3.7 | Evaluar accuracy vs pipeline actual | Comparación A/B |

**Dependencias:** Fase 1B (diccionario), Fase 2 (entidades extraídas)
**Bloquea:** Fase 4

---

### FASE 4: Enriquecimiento ESCO (Capa 4)

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 4.1 | Crear obtenedor de skills ESCO | `enrichment/esco_skills.py` |
| 4.2 | Crear analizador de cobertura | `enrichment/gap_analysis.py` |
| 4.3 | Crear buscador ocupaciones relacionadas | `enrichment/related_occupations.py` |
| 4.4 | Integrar en pipeline | `enrichment/enricher.py` |
| 4.5 | Tests de enriquecimiento | Validación campos generados |

**Dependencias:** Fase 3 (ocupación asignada)
**Bloquea:** Fase 5

---

### FASE 5: Migración y Validación

| Tarea | Descripción | Script/Archivo |
|-------|-------------|----------------|
| 5.1 | Migrar datos existentes | `migration/migrate_ofertas.py` |
| 5.2 | Procesar las 6,521 ofertas | Pipeline completo |
| 5.3 | Validación de calidad | Muestra de 100 ofertas |
| 5.4 | Comparar antes/después | Reporte de mejora |
| 5.5 | Actualizar exportación dashboard | Nuevos campos disponibles |

**Dependencias:** Fases 1-4 completas
**Bloquea:** Ninguno (fin del proyecto)

---

## ESTRUCTURA DE ARCHIVOS PROPUESTA

```
database/
├── create_ofertas_enriquecidas.sql
├── views_dashboard.sql
│
├── extractors/
│   ├── __init__.py
│   ├── regex_extractor.py
│   ├── spacy_extractor.py
│   ├── llm_extractor.py
│   └── entity_combinator.py
│
├── matching/
│   ├── __init__.py
│   ├── normalizer.py
│   ├── alt_label_search.py
│   ├── skill_matcher.py
│   ├── area_validator.py
│   └── multicriteria_matcher.py
│
├── enrichment/
│   ├── __init__.py
│   ├── esco_skills.py
│   ├── gap_analysis.py
│   ├── related_occupations.py
│   └── enricher.py
│
├── data/
│   ├── skills_dict.json
│   ├── beneficios.json
│   ├── certificaciones.json
│   ├── diccionario_argentino_v2.json
│   └── mapeo_areas_bumeran.json
│
├── migration/
│   └── migrate_ofertas.py
│
└── tests/
    ├── test_extractors.py
    ├── test_matching.py
    └── test_enrichment.py
```

---

## RESUMEN DE ARCHIVOS POR FASE

| Fase | Archivos Nuevos | Archivos Modificados |
|------|-----------------|---------------------|
| 0 | `fix_isco_codes.py` | `esco_occupations` (tabla) |
| 1A | `create_ofertas_enriquecidas.sql` | - |
| 1B | `diccionario_argentino_v2.json`, `populate_diccionario.py` | `diccionario_arg_esco` (tabla) |
| 2 | `extractors/*.py`, `data/*.json` | - |
| 3 | `matching/*.py` | - |
| 4 | `enrichment/*.py` | - |
| 5 | `migration/migrate_ofertas.py` | - |

---

## MÉTRICAS DE VALIDACIÓN POR FASE

| Fase | Métrica | Criterio de Éxito |
|------|---------|-------------------|
| 0 | % ocupaciones con ISCO | 100% (actual 59%) |
| 1B | Términos en diccionario | 200+ (actual 46) |
| 2 | Recall extracción skills | >90% |
| 3 | Accuracy matching | >85% (actual ~50%) |
| 4 | Ofertas con enrichment | 100% |
| 5 | Ofertas migradas | 6,521 |
