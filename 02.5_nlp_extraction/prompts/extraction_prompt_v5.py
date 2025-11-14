#!/usr/bin/env python3
"""
Extraction Prompt Template - NLP v5.0
======================================

Template de prompt para extracción híbrida con RAG.
Combina contexto ESCO + ejemplos + instrucciones detalladas.
"""

from typing import Dict, Any, Optional


def build_extraction_prompt(
    job_description: str,
    rag_context: str,
    regex_baseline: Optional[Dict[str, Any]] = None
) -> str:
    """
    Construye prompt completo para extracción NLP con RAG

    Args:
        job_description: Descripción completa de la oferta laboral
        rag_context: Contexto RAG generado (skills, ejemplos, etc.)
        regex_baseline: Extracción baseline de regex v3.7 (opcional)

    Returns:
        Prompt completo formateado para el LLM
    """

    # Sección de baseline (si existe)
    baseline_section = ""
    if regex_baseline:
        baseline_section = f"""
### EXTRACCIÓN BASELINE (Regex v3.7)
A continuación se muestra una extracción inicial realizada con expresiones regulares.
Usa esta información como PUNTO DE PARTIDA, pero valídala y mejórala según el contexto.

```json
{regex_baseline}
```

IMPORTANTE: La extracción baseline puede contener errores. Tu tarea es:
1. Validar cada campo contra la descripción original
2. Corregir errores evidentes (ej: skills que no son skills, salarios irreales)
3. Completar campos faltantes que encuentres en el texto
4. Eliminar información errónea o irrelevante

"""

    prompt = f"""Eres un experto extractor de información de ofertas laborales para el mercado argentino.

Tu tarea es analizar la siguiente descripción de oferta laboral y extraer información estructurada.

{baseline_section}

### CONTEXTO PARA VALIDACIÓN
{rag_context}

### DESCRIPCIÓN DE LA OFERTA LABORAL
```
{job_description}
```

### INSTRUCCIONES DE EXTRACCIÓN

Extrae la información en formato JSON con los siguientes campos:

**1. EXPERIENCIA:**
- `experiencia_min_anios` (número o null): Años mínimos de experiencia requeridos
- `experiencia_max_anios` (número o null): Años máximos de experiencia

**2. EDUCACIÓN:**
- `nivel_educativo` (string): Uno de: "primario", "secundario", "terciario", "universitario", "posgrado", null
- `estado_educativo` (string): Uno de: "en_curso", "completo", "incompleto", null
- `carrera_especifica` (string o null): Nombre específico de la carrera (ej: "Ingeniería Industrial")

**3. IDIOMAS:**
- `idioma_principal` (string o null): Idioma principal requerido (ej: "inglés", "español")
- `nivel_idioma_principal` (string): "basico", "intermedio", "avanzado", "nativo", null

**4. SKILLS Y COMPETENCIAS:**
- `skills_tecnicas_list` (string JSON array): Lista de habilidades técnicas como JSON string
  - VALIDAR contra el diccionario ESCO provisto
  - Incluir solo skills reales y relevantes
  - NO incluir: responsabilidades del puesto, requisitos genéricos, o descripciones largas
  - Ejemplos CORRECTOS: ["Python", "SQL", "Excel", "AutoCAD"]
  - Ejemplos INCORRECTOS: ["Responsable", "Gestión de proyectos completos", "toda la descripción"]

- `soft_skills_list` (string JSON array): Habilidades blandas como JSON string
  - Ejemplos: ["comunicación", "trabajo en equipo", "liderazgo"]

- `certificaciones_list` (string JSON array o null): Certificaciones específicas

**5. COMPENSACIÓN:**
- `salario_min` (número o null): Salario mínimo mensual bruto
- `salario_max` (número o null): Salario máximo mensual bruto
- `moneda` (string): "ARS", "USD", "EUR", null
  - VALIDACIÓN: Si no hay mención explícita de salario, todos estos campos deben ser null

**6. BENEFICIOS:**
- `beneficios_list` (string JSON array o null): Lista de beneficios como JSON string

**7. REQUISITOS:**
- `requisitos_excluyentes_list` (string JSON array o null): Requisitos obligatorios
- `requisitos_deseables_list` (string JSON array o null): Requisitos deseables/preferidos

**8. MODALIDAD:**
- `jornada_laboral` (string): "full_time", "part_time", "por_proyecto", "temporal", null
- `horario_flexible` (0 o 1 o null): 1 si menciona flexibilidad horaria

### REGLAS CRÍTICAS DE VALIDACIÓN

1. **Skills Técnicas:**
   - OBLIGATORIO: Validar contra diccionario ESCO del contexto
   - Incluir SOLO habilidades técnicas concretas y herramientas
   - NO incluir: descripciones largas, responsabilidades, requisitos genéricos
   - Máximo 10 skills por oferta

2. **Salarios:**
   - Solo extraer si hay MENCIÓN EXPLÍCITA en el texto
   - Validar que estén dentro de rangos razonables (usar estadísticas del contexto)
   - Si dice "competitivo", "a convenir", "según experiencia" → null

3. **Experiencia:**
   - Extraer números exactos cuando aparezcan
   - "Junior" → 0-2 años
   - "Semi-senior" → 2-4 años
   - "Senior" → 4+ años

4. **Educación:**
   - Usar nomenclatura argentina estándar del contexto
   - Si menciona "universitario en curso" → nivel_educativo: "universitario", estado: "en_curso"

5. **Arrays JSON:**
   - TODOS los arrays deben ser strings JSON válidos
   - Ejemplo correcto: '["Python", "SQL", "Excel"]'
   - NO usar listas Python directamente

6. **Valores null:**
   - Usar null (no "null" string) cuando no haya información EXPLÍCITA
   - EXCEPCIÓN: Aplicar REGLAS DE INFERENCIA CONTEXTUAL (ver sección 7) antes de usar null
   - Skills ESCO: validación estricta, NO inferir

7. **REGLAS DE INFERENCIA CONTEXTUAL** (para COMPLETITUD de datos):

   **Nivel Educativo** (si NO se menciona explícitamente):
   - Puestos operativos/manuales (chofer, repositor, limpieza, seguridad, etc.) → "secundario"
   - Puestos de ventas/atención al cliente (vendedor, cajero, telemarketing, etc.) → "secundario"
   - Puestos administrativos junior (auxiliar, asistente, etc.) → "secundario" o "terciario"
   - Puestos técnicos (técnico, especialista, instructor) → "terciario"
   - Puestos profesionales (analista, ingeniero, desarrollador) → "universitario"
   - Puestos gerenciales/directivos (gerente, jefe, coordinador, director) → "universitario"

   **Idioma Principal** (si NO se menciona explícitamente):
   - En Argentina: asumir "español" como idioma nativo
   - Solo usar null si el contexto indica que NO se requiere español

   **Experiencia** (interpretación de términos implícitos):
   - "Junior" o "trainee" → experiencia_min_anios: 0, experiencia_max_anios: 2
   - "Semi-senior" o "con experiencia" → experiencia_min_anios: 2, experiencia_max_anios: 4
   - "Senior" o "experimentado" → experiencia_min_anios: 4
   - "Excluyente X años" → usar el número mencionado

   **IMPORTANTE**:
   - Estas inferencias priorizan COMPLETITUD sobre precisión absoluta
   - NUNCA inferir skills_tecnicas_list: SIEMPRE validar contra ESCO
   - Si hay duda entre dos opciones, elegir la más conservadora

### FORMATO DE SALIDA

Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones adicionales.

Ejemplo de salida:
```json
{{
  "experiencia_min_anios": 2,
  "experiencia_max_anios": 4,
  "nivel_educativo": "universitario",
  "estado_educativo": "completo",
  "carrera_especifica": "Ingeniería en Sistemas",
  "idioma_principal": "ingles",
  "nivel_idioma_principal": "intermedio",
  "skills_tecnicas_list": "[\"Python\", \"Django\", \"PostgreSQL\", \"Docker\"]",
  "soft_skills_list": "[\"trabajo en equipo\", \"comunicación\", \"proactivo\"]",
  "certificaciones_list": null,
  "salario_min": 800000,
  "salario_max": 1200000,
  "moneda": "ARS",
  "beneficios_list": "[\"prepaga\", \"dia de cumpleaños\", \"home office\"]",
  "requisitos_excluyentes_list": "[\"titulo universitario\", \"ingles intermedio\"]",
  "requisitos_deseables_list": "[\"experiencia en startups\", \"conocimiento de AWS\"]",
  "jornada_laboral": "full_time",
  "horario_flexible": 1
}}
```

Ahora procede con la extracción:
"""

    return prompt


def build_simple_extraction_prompt(job_description: str) -> str:
    """
    Versión simplificada del prompt sin RAG (para testing)

    Args:
        job_description: Descripción de la oferta

    Returns:
        Prompt simplificado
    """
    return f"""Extrae información estructurada de esta oferta laboral en formato JSON.

Descripción:
{job_description}

Campos a extraer:
- experiencia_min_anios, experiencia_max_anios
- nivel_educativo, estado_educativo, carrera_especifica
- idioma_principal, nivel_idioma_principal
- skills_tecnicas_list (JSON string array)
- soft_skills_list (JSON string array)
- salario_min, salario_max, moneda
- beneficios_list, requisitos_excluyentes_list, requisitos_deseables_list (JSON string arrays)
- jornada_laboral, horario_flexible

Responde solo con JSON válido, sin explicaciones.
"""


# Función helper para generar prompt rápido
def generate_extraction_prompt(
    job_description: str,
    use_rag: bool = True,
    rag_context: str = "",
    regex_baseline: Optional[Dict[str, Any]] = None
) -> str:
    """
    Genera prompt de extracción con o sin RAG

    Args:
        job_description: Descripción de la oferta
        use_rag: Si usar contexto RAG
        rag_context: Contexto RAG (requerido si use_rag=True)
        regex_baseline: Baseline de regex v3.7

    Returns:
        Prompt completo
    """
    if use_rag:
        if not rag_context:
            raise ValueError("rag_context es requerido cuando use_rag=True")
        return build_extraction_prompt(job_description, rag_context, regex_baseline)
    else:
        return build_simple_extraction_prompt(job_description)


if __name__ == '__main__':
    # Test del prompt
    test_description = """
    Buscamos Desarrollador Python Senior con 3-5 años de experiencia.

    Requisitos:
    - Universitario completo en Ingeniería/Sistemas
    - Inglés intermedio
    - Python, Django, PostgreSQL, Docker
    - Git, CI/CD

    Ofrecemos:
    - Salario: $800.000 - $1.200.000
    - OSDE
    - Home office
    - Día de cumpleaños libre

    Full time, horario flexible.
    """

    # Prompt simple
    simple = build_simple_extraction_prompt(test_description)
    print("=== PROMPT SIMPLE ===")
    print(simple[:500])
    print(f"\n... (total: {len(simple)} caracteres)\n")

    # Prompt con RAG (simulado)
    mock_rag = "CONTEXTO RAG: 14,241 skills ESCO disponibles..."
    mock_baseline = {
        "experiencia_min_anios": 3,
        "skills_tecnicas_list": "[\"Python\", \"Django\"]"
    }

    full = build_extraction_prompt(test_description, mock_rag, mock_baseline)
    print("=== PROMPT COMPLETO CON RAG ===")
    print(full[:500])
    print(f"\n... (total: {len(full)} caracteres)")
