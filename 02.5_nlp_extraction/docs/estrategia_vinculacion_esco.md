# Estrategia de Vinculación con ESCO
## Ofertas Laborales → Taxonomía ESCO

---

## 1. ESTADO ACTUAL

### Datos de Ofertas Laborales
**Archivo**: `all_sources_fixed_20251027_170535.csv`
- **Total ofertas**: 8,472
- **Campos extraídos**:
  - `titulo`: Título del puesto
  - `descripcion`: Descripción completa
  - `soft_skills`: Lista separada por comas (70.1% cobertura, 5,943 ofertas)
  - `skills_tecnicas`: Lista separada por comas (40.3% cobertura, 3,414 ofertas)
  - `nivel_educativo`: secundario/terciario/universitario/posgrado (38.6%)
  - `experiencia_min_anios`: Años de experiencia (29.2%)
  - `localizacion`: Ubicación geográfica (29.1%)

### Datos ESCO Disponibles
**Ubicación**: `D:\Trabajos en PY\EPH-ESCO\07_esco_data\`

1. **`esco_consolidado_con_isco.json`**
   - 1,886 ocupaciones ESCO
   - Campos: `label_es`, `label_en`, `codigo_isco`, `alt_labels_es`

2. **`esco_ocupaciones_skills_relaciones.json`**
   - 2,865 ocupaciones con relaciones
   - Skills esenciales y opcionales por ocupación
   - Enlaces a IDs de skills

3. **`esco_skills_info.json`**
   - 6,818 skills con información completa
   - Labels en español e inglés

---

## 2. ESTRATEGIA DE VINCULACIÓN

### Enfoque Multi-nivel

```
NIVEL 1: Matching de Ocupaciones (Título → ESCO Occupation)
   ↓
NIVEL 2: Validación por Skills (Skills extraídas → ESCO Skills)
   ↓
NIVEL 3: Enriquecimiento (Agregar skills faltantes de ESCO)
```

---

## 3. NIVEL 1: MATCHING DE OCUPACIONES

### Objetivo
Mapear el **título de la oferta** a una **ocupación ESCO**.

### Técnicas Propuestas

#### 3.1. Matching Exacto (Fuzzy)
```python
from fuzzywuzzy import fuzz
import unidecode

def normalizar_texto(texto):
    """Normaliza para matching"""
    texto = unidecode.unidecode(texto.lower())
    texto = re.sub(r'[^\w\s]', ' ', texto)
    return ' '.join(texto.split())

def fuzzy_match_ocupacion(titulo_oferta, ocupaciones_esco):
    """
    Match fuzzy entre título y ocupaciones ESCO

    Retorna:
    - ocupacion_id
    - score (0-100)
    - label_es
    """
    titulo_norm = normalizar_texto(titulo_oferta)

    best_match = None
    best_score = 0

    for occ_id, occ_data in ocupaciones_esco.items():
        # Comparar con label principal
        score = fuzz.token_sort_ratio(
            titulo_norm,
            normalizar_texto(occ_data['label_es'])
        )

        # Comparar con labels alternativos
        for alt_label in occ_data.get('alt_labels_es', []):
            alt_score = fuzz.token_sort_ratio(
                titulo_norm,
                normalizar_texto(alt_label)
            )
            score = max(score, alt_score)

        if score > best_score:
            best_score = score
            best_match = (occ_id, occ_data['label_es'])

    return best_match[0], best_score, best_match[1]
```

**Umbrales propuestos**:
- Score >= 90: Match alta confianza
- Score 70-89: Match media confianza (revisar manualmente)
- Score < 70: No match (enviar a LLM)

#### 3.2. Matching Semántico (LLM)
Para títulos sin match fuzzy > 70, usar **Ollama** para clasificación:

```python
def llm_clasificar_ocupacion(titulo, descripcion, top_ocupaciones_esco):
    """
    Usa LLM para clasificar ocupación cuando fuzzy falla
    """
    prompt = f"""Eres un experto en clasificación ocupacional según ESCO.

OFERTA:
Título: {titulo}
Descripción: {descripcion[:500]}

OCUPACIONES ESCO CANDIDATAS:
{json.dumps(top_ocupaciones_esco, ensure_ascii=False, indent=2)}

TAREA:
Identifica cuál ocupación ESCO corresponde mejor a esta oferta.
Responde SOLO con JSON:
{{
    "esco_id": "UUID de la ocupación ESCO",
    "confianza": 0-100,
    "razon": "Breve explicación"
}}

JSON:"""

    response = ollama.run('llama3', prompt)
    return parse_json(response)
```

---

## 4. NIVEL 2: VALIDACIÓN POR SKILLS

### Objetivo
Validar el matching de ocupación comparando las **skills extraídas** de la oferta con las **skills esenciales** de la ocupación ESCO.

### Técnica: Overlap Score

```python
def calcular_skill_overlap(
    oferta_skills: List[str],
    esco_occupation_id: str,
    esco_skills_info: dict,
    esco_relaciones: dict
) -> float:
    """
    Calcula % de overlap entre skills de oferta y ESCO

    Returns:
        - overlap_score: 0-100
        - skills_matched: Lista de skills matcheadas
        - skills_missing: Skills ESCO no presentes en oferta
    """
    # Obtener skills esenciales de la ocupación ESCO
    esco_skill_ids = esco_relaciones[esco_occupation_id]['skills_esenciales']

    # Convertir IDs a labels en español
    esco_skills_labels = [
        normalizar_texto(esco_skills_info[sid]['label_es'])
        for sid in esco_skill_ids
    ]

    # Normalizar skills de oferta
    oferta_skills_norm = [normalizar_texto(s) for s in oferta_skills]

    # Calcular matches (fuzzy)
    matches = []
    for oferta_skill in oferta_skills_norm:
        for esco_skill in esco_skills_labels:
            if fuzz.token_sort_ratio(oferta_skill, esco_skill) >= 80:
                matches.append((oferta_skill, esco_skill))
                break

    # Score = % de skills ESCO esenciales presentes en oferta
    overlap_score = (len(matches) / len(esco_skills_labels)) * 100

    return {
        'overlap_score': overlap_score,
        'skills_matched': matches,
        'skills_esco_total': len(esco_skills_labels),
        'skills_oferta_total': len(oferta_skills_norm)
    }
```

**Interpretación**:
- Overlap >= 60%: Ocupación correcta
- Overlap 30-59%: Revisar (puede ser ocupación relacionada)
- Overlap < 30%: Probablemente ocupación incorrecta

---

## 5. NIVEL 3: ENRIQUECIMIENTO

### Objetivo
Agregar **skills faltantes** de ESCO que deberían estar presentes según la ocupación identificada.

```python
def enriquecer_oferta_con_esco(
    oferta: dict,
    esco_occupation_id: str,
    esco_skills_info: dict,
    esco_relaciones: dict
) -> dict:
    """
    Agrega skills ESCO a la oferta

    Returns:
        - oferta_enriquecida con nuevos campos:
          - esco_occupation_id
          - esco_occupation_label
          - esco_skills_recomendadas (skills esenciales no presentes)
          - esco_skills_opcionales
    """
    # Skills esenciales de ESCO
    skills_esenciales_ids = esco_relaciones[esco_occupation_id]['skills_esenciales']
    skills_opcionales_ids = esco_relaciones[esco_occupation_id].get('skills_opcionales', [])

    # Convertir a labels
    skills_esenciales = [
        esco_skills_info[sid]['label_es']
        for sid in skills_esenciales_ids
    ]

    skills_opcionales = [
        esco_skills_info[sid]['label_es']
        for sid in skills_opcionales_ids
    ]

    # Identificar skills faltantes
    oferta_skills = set(oferta['soft_skills'].split(', ') if oferta['soft_skills'] else [])
    oferta_skills.update(oferta['skills_tecnicas'].split(', ') if oferta['skills_tecnicas'] else [])

    skills_recomendadas = [
        skill for skill in skills_esenciales
        if not any(fuzz.token_sort_ratio(skill, os) >= 80 for os in oferta_skills)
    ]

    return {
        **oferta,
        'esco_occupation_id': esco_occupation_id,
        'esco_occupation_label': esco_consolidado[esco_occupation_id]['label_es'],
        'esco_codigo_isco': esco_consolidado[esco_occupation_id].get('codigo_isco'),
        'esco_skills_recomendadas': ', '.join(skills_recomendadas),
        'esco_skills_opcionales': ', '.join(skills_opcionales),
        'esco_match_score': calcular_skill_overlap(...)['overlap_score']
    }
```

---

## 6. PIPELINE COMPLETO

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: all_sources_fixed_20251027_170535.csv              │
│  8,472 ofertas con soft_skills y skills_tecnicas           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 1: MATCHING DE OCUPACIONES                           │
│  - Fuzzy matching (título → ESCO occupation)               │
│  - LLM fallback si fuzzy < 70                              │
│  Output: esco_occupation_id + match_score                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 2: VALIDACIÓN POR SKILLS                             │
│  - Calcular overlap entre skills oferta y ESCO             │
│  - Flagear matches con overlap < 30% para revisión         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 3: ENRIQUECIMIENTO                                   │
│  - Agregar skills esenciales ESCO faltantes                │
│  - Agregar código ISCO                                      │
│  - Agregar metadata de ocupación                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: ofertas_esco_vinculadas_YYYYMMDD.csv              │
│  - Campos originales +                                      │
│  - esco_occupation_id, esco_occupation_label               │
│  - esco_codigo_isco                                         │
│  - esco_match_score                                         │
│  - esco_skills_recomendadas                                 │
│  - esco_skills_opcionales                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. CASOS ESPECIALES

### 7.1. Ofertas sin Skills Extraídas
**Problema**: 2,529 ofertas (29.9%) sin soft_skills
**Solución**: Usar solo título + descripción para matching de ocupación, luego enriquecer con todas las skills esenciales de ESCO.

### 7.2. Títulos Ambiguos
**Ejemplo**: "Analista" (puede ser de datos, financiero, RH, etc.)
**Solución**: Usar descripción + LLM para desambiguar.

### 7.3. Ocupaciones No ESCO
**Problema**: Títulos muy locales de Argentina no están en ESCO
**Solución**:
1. Intentar mapear a ocupación ESCO más cercana
2. Si no match, clasificar con LLM a nivel ISCO (4 dígitos)
3. Marcar para revisión manual

---

## 8. MÉTRICAS DE CALIDAD

### Durante Vinculación
- **Tasa de matching directo** (fuzzy >= 90)
- **Tasa de LLM fallback** (fuzzy < 70)
- **Overlap promedio de skills** (validación)

### Post-vinculación
- **Cobertura ESCO**: % ofertas con esco_occupation_id
- **Confianza promedio**: avg(esco_match_score)
- **Distribución por ISCO**: Top 10 ocupaciones más frecuentes

---

## 9. HERRAMIENTAS NECESARIAS

### Python Libraries
```bash
pip install fuzzywuzzy python-Levenshtein unidecode pandas tqdm
```

### LLM Local
- **Ollama** con `llama3` (ya disponible)

### Scripts a Crear
1. `esco_matcher.py` - Matching fuzzy + LLM
2. `esco_validator.py` - Validación por skills overlap
3. `esco_enricher.py` - Enriquecimiento con skills ESCO
4. `esco_pipeline.py` - Pipeline completo
5. `esco_quality_report.py` - Reporte de calidad

---

## 10. PRÓXIMOS PASOS

### Orden Sugerido

1. **Crear índice de búsqueda ESCO** (optimización)
   - Preprocesar labels de ocupaciones
   - Crear diccionario invertido para fuzzy search rápido

2. **Implementar Fase 1**: Matching de ocupaciones
   - Fuzzy matching
   - LLM fallback
   - Validar en muestra de 100 ofertas

3. **Implementar Fase 2**: Validación por skills
   - Calcular overlap
   - Ajustar umbrales

4. **Implementar Fase 3**: Enriquecimiento
   - Agregar skills ESCO
   - Generar campos finales

5. **Ejecutar pipeline completo** en 8,472 ofertas
   - Procesar por lotes
   - Guardar checkpoints

6. **Generar reporte de calidad**
   - Métricas de matching
   - Casos para revisión manual

---

## 11. TIEMPO ESTIMADO

### Con Fuzzy + LLM Híbrido
- Fuzzy matching: ~0.1s por oferta → 14 minutos (8,472 ofertas)
- LLM fallback (~30%): ~2.5s por oferta → 1.75 horas (2,542 ofertas)
- Validación + enriquecimiento: ~0.05s por oferta → 7 minutos

**TOTAL: ~2 horas** (con LLM local Ollama)

---

## 12. RESULTADO ESPERADO

### Archivo Final
```csv
fecha_publicacion,fuente,titulo,descripcion,...,
esco_occupation_id,esco_occupation_label,esco_codigo_isco,
esco_match_score,esco_match_method,
esco_skills_recomendadas,esco_skills_opcionales,
esco_overlap_score
```

### Ejemplo de Fila Enriquecida
```
titulo: "Vendedora/ Asistente Administrativo"
soft_skills: "comunicación, organización, proactividad, ..."
esco_occupation_id: "9e81adde-9983-44fa-b74b-c548d0dbfbdd"
esco_occupation_label: "asistente administrativo"
esco_codigo_isco: "4110"
esco_match_score: 85
esco_match_method: "fuzzy"
esco_skills_recomendadas: "gestión de documentos, archivo"
esco_overlap_score: 75.0
```

---

## 13. VENTAJAS DE ESTA ESTRATEGIA

1. **Multi-nivel**: Combina matching sintáctico, semántico y validación
2. **Escalable**: Fuzzy rápido para mayoría, LLM solo cuando necesario
3. **Validable**: Overlap score permite verificar calidad
4. **Enriquecedor**: No solo clasifica, también sugiere skills faltantes
5. **Compatible ISCO**: Vincula con clasificación internacional

---

**Autor**: Claude Code
**Fecha**: 2025-10-27
**Versión**: 1.0
