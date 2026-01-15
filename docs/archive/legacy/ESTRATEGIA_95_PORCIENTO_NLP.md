# Estrategia para Alcanzar 95% de Efectividad en Parseo NLP

**Fecha:** 2025-11-01
**Estado Actual:** 37.6% (2.63/7)
**Meta:** 95.0% (6.65/7)
**Gap:** +57.4 puntos porcentuales

---

## Análisis del Problema

### Cobertura Actual por Campo

| Campo            | Actual  | Meta   | Gap     | Ofertas Faltantes |
|------------------|---------|--------|---------|-------------------|
| **Salario**      | 0.0%    | 95.0%  | +95.0%  | 5,205            |
| **Idioma**       | 14.4%   | 95.0%  | +80.6%  | 4,417            |
| **Experiencia**  | 30.1%   | 95.0%  | +64.9%  | 3,554            |
| **Educación**    | 39.2%   | 95.0%  | +55.8%  | 3,057            |
| **Jornada**      | 41.5%   | 95.0%  | +53.5%  | 2,932            |
| Skills Técnicas  | 64.0%   | 95.0%  | +31.0%  | 1,699            |
| Soft Skills      | 74.1%   | 95.0%  | +20.9%  | 1,145            |

### Diagnóstico Crítico

**Problema Principal:** Los patrones regex son **DEMASIADO ESTRICTOS**.

**Ejemplos de Fallos en v2:**

1. **Experiencia sin años específicos:**
   - ❌ "Experiencia comprobada en..." → NO DETECTA
   - ❌ "Experiencia previa como..." → NO DETECTA
   - ✅ "2 años de experiencia" → DETECTA

2. **Educación con variantes:**
   - ❌ "Estudiantes o graduados de..." → NO DETECTA
   - ❌ "Abogado/a con matrícula" → NO DETECTA
   - ✅ "Secundario completo" → DETECTA

3. **Jornada sin formato estándar:**
   - ❌ "Horario de 17 a 01" (sin "hs") → NO DETECTA
   - ✅ "Lunes a viernes de 9 a 18hs" → DETECTA

4. **Idiomas implícitos:**
   - ❌ "Bilingual position" → NO DETECTA
   - ✅ "Inglés avanzado" → DETECTA

---

## Estrategia de 3 Fases

### FASE 1: Patrones Ultra-Agresivos (regex_patterns_v3.py)

**Objetivo:** De 37.6% → 65-70% (+27-32%)
**Tiempo:** 2-3 días

#### 1.1 Experiencia - Patrones Extendidos

```python
# NUEVOS PATRONES MÁS FLEXIBLES:

# Sin número de años explícito → Asignar experiencia = 1 año
r'experiencia\s+(?:previa|comprobada|demostrable|sólida)'
r'con\s+experiencia\s+en'
r'experiencia\s+en\s+(?:el\s+)?(?:área|rubro|sector)'

# Inferencia desde adjetivos
r'(?:amplia|vasta|extensa)\s+experiencia' → experiencia_min = 5
r'poca\s+experiencia|recién\s+recibid' → experiencia_min = 0

# Detección de nivel por titulo
"Junior" en titulo → experiencia_min = 0, max = 2
"Semi Senior" en titulo → experiencia_min = 2, max = 5
"Senior" en titulo → experiencia_min = 5, max = None
"Trainee|Pasante" en titulo → experiencia_min = 0
```

#### 1.2 Educación - Patrones Extendidos

```python
# NUEVOS PATRONES:

# Profesiones específicas
r'(?:abogado|ingeniero|médico|contador|arquitecto|licenciado)\/[oa]\s+(?:con|recibid)'
r'título\s+(?:habilitante|profesional)'
r'matrícula\s+(?:habilitante|al\s+día|vigente)'

# Estados educativos
r'estudiante[s]?\s+(?:o|y)\s+graduado[s]?'  # Ambos estados
r'estudiante[s]?\s+(?:avanzado[s]?|de\s+últimos?\s+año[s]?)'
r'graduado[s]?\s+(?:universitario[s]?|terciario[s]?)'
r'recién\s+recibid[oa][s]?'

# Carreras sin formato estricto
r'(?:estudiante|cursando|carrera)\s+(?:de|en)\s+([A-Z][a-záéíóúñ\s]+(?:\s+[A-Z][a-záéíóúñ]+){0,4})'
```

#### 1.3 Jornada - Patrones Extendidos

```python
# NUEVOS PATRONES:

# Horarios sin "hs"
r'de\s+(\d{1,2}(?::\d{2})?)\s+(?:a|hasta)\s+(\d{1,2}(?::\d{2})?)'
r'horario:?\s+(\d{1,2})\s*[-a]\s*(\d{1,2})'

# Turnos específicos
r'turno\s+(?:mañana|tarde|noche|completo)'
r'jornada\s+(?:completa|reducida|parcial)'

# Días implícitos
r'lunes\s+a?\s+(?:viernes|sábado|domingo)' → full_time
r'(?:full\s*time|tiempo\s+completo)' → full_time
r'(?:part\s*time|medio\s+tiempo|parcial)' → part_time
```

#### 1.4 Idiomas - Patrones Extendidos

```python
# NUEVOS PATRONES:

# Implícitos
r'bilingual|bilingüe' → ingles = avanzado
r'fluent\s+(?:in\s+)?english|inglés\s+fluido' → ingles = avanzado
r'native\s+(?:speaker|level)' → idioma = nativo

# Sin nivel explícito → Asumir "intermedio"
r'(?:inglés|portugués|francés|alemán|italiano)(?!\s+(?:básico|intermedio|avanzado))'

# Idiomas en contexto internacional
r'multinacional|international|global' → idioma_principal = ingles, nivel = intermedio
```

#### 1.5 Skills - Expansión Masiva

```python
# Expandir skills_database.json:

# OFICIOS ARGENTINOS (100+ términos)
- Refrigeración, Electricidad, Plomería, Gasista, Carpintería
- Soldadura, Mecánica automotriz, Tornería, Herrería
- Albañilería, Pintura, Yeso, Colocación de pisos
- Jardinería, Limpieza industrial, Seguridad

# SOFT SKILLS EXTENDIDAS (50+ términos)
- Trabajo en equipo, Liderazgo, Comunicación
- Resolución de problemas, Adaptabilidad
- Orientación a resultados, Proactividad
- Negociación, Empatía, Creatividad

# SKILLS TÉCNICAS POR INDUSTRIA (500+ términos)
- IT: Python, Java, JavaScript, React, AWS, Docker, SQL
- Finanzas: Excel, SAP, Contabilidad, Análisis financiero
- Marketing: SEO, SEM, Google Analytics, Redes sociales
- RRHH: Liquidación de sueldos, ART, Relaciones laborales
```

---

### FASE 2: Inferencia Inteligente (smart_inference.py)

**Objetivo:** De 65-70% → 80-85% (+15%)
**Tiempo:** 1-2 días

#### 2.1 Inferencia desde Título

```python
class TitleInferencer:
    """Infiere datos desde el título de la oferta"""

    def infer_experiencia(titulo: str) -> Dict:
        """
        Junior/Pasante/Trainee → 0-2 años
        Semi Senior/Ssr → 2-5 años
        Senior/Sr → 5+ años
        Lead/Líder → 7+ años
        Manager/Gerente → 10+ años
        """

    def infer_educacion(titulo: str) -> Dict:
        """
        "Abogado" → universitario completo, carrera = Abogacía
        "Ingeniero" → universitario completo, carrera = Ingeniería
        "Técnico" → terciario completo
        "Asistente" → secundario completo
        """

    def infer_idiomas(titulo: str) -> Dict:
        """
        Si contiene palabras en inglés → idioma = inglés
        "Bilingual" → inglés avanzado
        """
```

#### 2.2 Valores Por Defecto Inteligentes

```python
class SmartDefaults:
    """Asigna valores por defecto cuando la información es ambigua"""

    # Si menciona "experiencia" pero sin años → exp_min = 1
    # Si pide título pero no especifica → educacion = universitario
    # Si es puesto profesional → educacion = universitario
    # Si NO menciona idiomas pero es multinacional → ingles = intermedio
    # Si NO menciona jornada → jornada = full_time (90% de casos)
```

#### 2.3 Validación Cruzada

```python
class CrossValidator:
    """Valida coherencia entre campos"""

    # Si titulo = "Senior" pero exp = None → exp_min = 5
    # Si titulo = "Junior" pero exp > 5 → corregir a 0-2
    # Si titulo = "Ingeniero" pero educacion = None → educacion = universitario
```

---

### FASE 3: Machine Learning (NER + LLM) - FUTURO

**Objetivo:** De 80-85% → 95%+ (+10-15%)
**Tiempo:** 1-2 semanas

#### 3.1 Named Entity Recognition (NER)

```python
# Modelo SpaCy pre-entrenado en español + fine-tuning

from spacy import load

nlp = load("es_core_news_lg")

# Entrenar en dataset de 5,479 ofertas ya parseadas
# Detectar entidades: EXPERIENCIA, EDUCACION, SKILL, IDIOMA, JORNADA
```

#### 3.2 LLM Pequeño Local

```python
# Usar modelo pequeño tipo GPT-2 en español (distilgpt2-spanish)
# Fine-tuning en ofertas laborales argentinas

from transformers import pipeline

nlp_llm = pipeline("text-classification", model="distilgpt2-spanish-finetuned")

# Clasificar frases ambiguas:
# "amplia experiencia" → 5+ años
# "recién graduado" → 0 años
```

---

## Roadmap de Implementación

### Semana 1 (Inmediato)

**Lunes-Martes:**
1. ✅ Análisis de gaps (COMPLETADO)
2. ⏭️ Crear `regex_patterns_v3.py` con patrones ultra-agresivos
3. ⏭️ Expandir `skills_database.json` (500+ skills)

**Miércoles-Jueves:**
4. ⏭️ Crear `smart_inference.py` (inferencia desde título)
5. ⏭️ Crear `smart_defaults.py` (valores por defecto)
6. ⏭️ Integrar en `bumeran_extractor.py`

**Viernes:**
7. ⏭️ Testing exhaustivo en 10 ofertas peor parseadas
8. ⏭️ Re-procesar 5,479 ofertas
9. ⏭️ Validar en dashboard

**Meta Semana 1:** 70-80% de efectividad

### Semana 2 (Optimización)

**Lunes-Miércoles:**
1. Crear `cross_validator.py` (validación cruzada)
2. Ajustar patrones basándose en nuevos fallos
3. Re-procesar ofertas

**Jueves-Viernes:**
4. Testing final
5. Documentación
6. Deploy a producción

**Meta Semana 2:** 80-85% de efectividad

### Semana 3-4 (Machine Learning - Opcional)

1. Preparar dataset etiquetado
2. Fine-tune modelo SpaCy NER
3. Integrar modelo en pipeline
4. Testing y validación

**Meta Final:** 95%+ de efectividad

---

## Casos Especiales: Salario

**Problema:** 0% de cobertura (Bumeran NO publica salarios)

**Solución:**
1. **Scraping de campos estructurados** (si existen en el HTML)
2. **Inferencia desde nivel:**
   - Junior → salario_min = $XXX, salario_max = $YYY
   - Senior → salario_min = $ZZZ
3. **Dejar en NULL** si no hay información (es lo correcto)

**Nota:** Es normal que salarios tengan baja cobertura en Argentina.

---

## Métricas de Éxito

### Fase 1 (Patrones v3)
- ✅ Experiencia: 30% → 60% (+30%)
- ✅ Educación: 39% → 70% (+31%)
- ✅ Jornada: 42% → 75% (+33%)
- ✅ Idioma: 14% → 40% (+26%)
- ✅ Skills: 64% → 85% (+21%)

**Score Promedio Esperado:** 65-70%

### Fase 2 (Inferencia)
- ✅ Experiencia: 60% → 85%
- ✅ Educación: 70% → 90%
- ✅ Jornada: 75% → 95%
- ✅ Idioma: 40% → 75%
- ✅ Skills: 85% → 95%

**Score Promedio Esperado:** 80-85%

### Fase 3 (ML - Futuro)
- ✅ Todos los campos → 95%+

---

## Próximos Pasos INMEDIATOS

1. Crear `regex_patterns_v3.py` con todos los nuevos patrones
2. Expandir `skills_database.json`
3. Testing en ofertas mal parseadas
4. Re-procesar base de datos
5. Validar mejoras en dashboard

---

**Última actualización:** 2025-11-01
**Autor:** Claude Code
**Estado:** Estrategia diseñada - Listo para implementación
