#!/usr/bin/env python3
"""
Extraction Prompt Template - NLP v6.0
======================================

Template de prompt para extracción híbrida con RAG.
NOVEDAD v6.0: Agrega 6 campos nuevos (24 campos totales)

Campos nuevos:
- experiencia_cargo_previo
- tecnologias_stack_list
- sector_industria
- nivel_seniority
- modalidad_contratacion
- disponibilidad_viajes
"""

from typing import Dict, Any, Optional


def build_extraction_prompt_v6(
    job_description: str,
    rag_context: str,
    regex_baseline: Optional[Dict[str, Any]] = None
) -> str:
    """
    Construye prompt completo para extracción NLP v6.0 con RAG

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

### INSTRUCCIONES DE EXTRACCIÓN (NLP v6.0 - 24 campos)

Extrae la información en formato JSON con los siguientes campos:

**1. EXPERIENCIA:**
- `experiencia_min_anios` (número o null): Años mínimos de experiencia requeridos
- `experiencia_max_anios` (número o null): Años máximos de experiencia
- `experiencia_cargo_previo` (string o null): **NUEVO v6.0** - Cargo/título previo específico requerido
  - Ejemplos: "Gerente de Ventas", "Desarrollador Backend", "Analista de Datos"
  - Solo incluir si se menciona un cargo específico previo
  - NO incluir si solo dice "experiencia en el área"

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

- `tecnologias_stack_list` (string JSON array o null): **NUEVO v6.0** - Stack tecnológico completo
  - Incluir lenguajes, frameworks, herramientas, plataformas
  - Ejemplos: ["Python", "Django", "PostgreSQL", "Docker", "AWS", "React"]
  - Diferencia con skills_tecnicas_list: Este es más específico a tecnologías IT
  - Si no es un puesto IT/tecnológico, puede ser null

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

**8. MODALIDAD Y JORNADA:**
- `jornada_laboral` (string): "full_time", "part_time", "por_proyecto", "temporal", null
- `horario_flexible` (0 o 1 o null): 1 si menciona flexibilidad horaria

- `modalidad_contratacion` (string): **NUEVO v6.0** - Uno de:
  - "remoto" - 100% remoto/home office
  - "presencial" - 100% presencial en oficina
  - "hibrido" - Combinación de remoto y presencial
  - null - No se especifica

- `disponibilidad_viajes` (0 o 1 o null): **NUEVO v6.0**
  - 1 si requiere disponibilidad para viajar (nacional o internacional)
  - 0 si explícitamente NO requiere viajes
  - null si no se menciona

**9. CONTEXTO DEL PUESTO:**
- `sector_industria` (string o null): **NUEVO v6.0** - Sector/industria del puesto
  - Ejemplos: "IT/Tecnología", "Finanzas", "Retail", "Salud", "Educación", "Manufactura",
    "Construcción", "Logística", "Marketing", "Recursos Humanos", "Legal", "Consultoría"
  - Inferir del contexto de la empresa y naturaleza del puesto

- `nivel_seniority` (string o null): **NUEVO v6.0** - Nivel de senioridad
  - Uno de: "trainee", "junior", "semi-senior", "senior", "lead", "manager", "director"
  - Inferir de:
    * Términos explícitos en título/descripción
    * Años de experiencia requeridos (0-1: trainee, 1-2: junior, 2-4: semi-senior, 4+: senior)
    * Responsabilidades (gestión de equipo → manager/director)

### REGLAS CRÍTICAS DE VALIDACIÓN

1. **Skills Técnicas:**
   - OBLIGATORIO: Validar contra diccionario ESCO del contexto
   - Incluir SOLO habilidades técnicas concretas y herramientas
   - NO incluir: descripciones largas, responsabilidades, requisitos genéricos
   - Máximo 10 skills por oferta

2. **Tecnologías Stack (NUEVO v6.0):**
   - Solo para puestos IT/tecnológicos
   - Ser exhaustivo: incluir TODO el stack mencionado
   - Incluir: lenguajes, frameworks, bases de datos, cloud, DevOps, frontend, backend
   - Si no es puesto IT → null

3. **Salarios:**
   - Solo extraer si hay MENCIÓN EXPLÍCITA en el texto
   - Validar que estén dentro de rangos razonables (usar estadísticas del contexto)
   - Si dice "competitivo", "a convenir", "según experiencia" → null

4. **Experiencia:**
   - Extraer números exactos cuando aparezcan
   - "Junior" → 0-2 años
   - "Semi-senior" → 2-4 años
   - "Senior" → 4+ años

5. **Cargo Previo (NUEVO v6.0):**
   - Solo si menciona cargo/título específico previo
   - Ejemplos: "buscamos ex Gerente de...", "experiencia previa como..."
   - NO incluir descripciones genéricas de experiencia

6. **Sector Industria (NUEVO v6.0):**
   - Inferir del contexto general de la oferta
   - Usar categorías amplias y estándar
   - Si no es claro, inferir de: nombre empresa, tipo de puesto, skills requeridas

7. **Nivel Seniority (NUEVO v6.0):**
   - SIEMPRE inferir basado en:
     * Términos explícitos (Junior, Senior, etc.)
     * Años de experiencia
     * Responsabilidades (¿gestiona equipo? → manager)
     * Tipo de puesto (Gerente → manager, Director → director)

8. **Modalidad Contratación (NUEVO v6.0):**
   - Buscar términos: "remoto", "home office", "presencial", "oficina", "híbrido", "mixto"
   - Si no se menciona → null
   - Asumir presencial SOLO si hay mención de ubicación física sin remoto

9. **Arrays JSON:**
   - TODOS los arrays deben ser strings JSON válidos
   - Ejemplo correcto: '["Python", "SQL", "Excel"]'
   - NO usar listas Python directamente

10. **Valores null:**
    - Usar null (no "null" string) cuando no haya información EXPLÍCITA
    - EXCEPCIÓN: Aplicar REGLAS DE INFERENCIA CONTEXTUAL (ver sección 11)

11. **REGLAS DE INFERENCIA CONTEXTUAL** (para COMPLETITUD de datos):

   **Nivel Educativo** (si NO se menciona explícitamente):
   - Puestos operativos/manuales (chofer, repositor, limpieza, seguridad) → "secundario"
   - Puestos de ventas/atención (vendedor, cajero, telemarketing) → "secundario"
   - Puestos administrativos junior (auxiliar, asistente) → "secundario" o "terciario"
   - Puestos técnicos (técnico, especialista) → "terciario"
   - Puestos profesionales (analista, ingeniero, desarrollador) → "universitario"
   - Puestos gerenciales/directivos → "universitario"

   **Idioma Principal** (si NO se menciona):
   - En Argentina: asumir "español" como idioma nativo
   - Solo null si contexto indica que NO se requiere español

   **Nivel Seniority** (SIEMPRE inferir):
   - Trainee/Pasante/Becario → "trainee"
   - Junior/Sin experiencia/0-2 años → "junior"
   - Semi-senior/Con experiencia/2-4 años → "semi-senior"
   - Senior/Experimentado/4+ años → "senior"
   - Team Lead/Líder técnico → "lead"
   - Manager/Gerente/Jefe → "manager"
   - Director/Ejecutivo → "director"

   **Sector Industria** (inferir del contexto):
   - Desarrollador/Programador/Data/DevOps → "IT/Tecnología"
   - Contador/Finanzas/Auditor → "Finanzas"
   - Médico/Enfermero/Farmacéutico → "Salud"
   - Vendedor/Cajero/Repositor → "Retail"
   - Docente/Profesor/Capacitador → "Educación"
   - Operario/Técnico mantenimiento → "Manufactura"

   **Modalidad Contratación** (inferir si hay pistas):
   - Menciona ubicación física sin remoto → "presencial"
   - Menciona "desde cualquier lugar" → "remoto"
   - Si no hay info → null (no inferir)

   **IMPORTANTE**:
   - Estas inferencias priorizan COMPLETITUD sobre precisión absoluta
   - NUNCA inferir skills_tecnicas_list o tecnologias_stack_list: VALIDAR contra ESCO
   - nivel_seniority: SIEMPRE inferir (es crítico para analytics)
   - sector_industria: SIEMPRE inferir si es posible

### FORMATO DE SALIDA

Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones adicionales.

Ejemplo de salida (NLP v6.0 - 24 campos):
```json
{{
  "experiencia_min_anios": 2,
  "experiencia_max_anios": 4,
  "experiencia_cargo_previo": "Desarrollador Backend",
  "nivel_educativo": "universitario",
  "estado_educativo": "completo",
  "carrera_especifica": "Ingeniería en Sistemas",
  "idioma_principal": "ingles",
  "nivel_idioma_principal": "intermedio",
  "skills_tecnicas_list": "[\"Python\", \"Django\", \"PostgreSQL\", \"Docker\"]",
  "tecnologias_stack_list": "[\"Python\", \"Django\", \"PostgreSQL\", \"Docker\", \"Redis\", \"Celery\", \"AWS\", \"Kubernetes\"]",
  "soft_skills_list": "[\"trabajo en equipo\", \"comunicación\", \"proactivo\"]",
  "certificaciones_list": null,
  "salario_min": 800000,
  "salario_max": 1200000,
  "moneda": "ARS",
  "beneficios_list": "[\"prepaga\", \"dia de cumpleaños\", \"home office\"]",
  "requisitos_excluyentes_list": "[\"titulo universitario\", \"ingles intermedio\"]",
  "requisitos_deseables_list": "[\"experiencia en startups\", \"conocimiento de AWS\"]",
  "jornada_laboral": "full_time",
  "horario_flexible": 1,
  "modalidad_contratacion": "hibrido",
  "disponibilidad_viajes": 0,
  "sector_industria": "IT/Tecnología",
  "nivel_seniority": "semi-senior"
}}
```

Ahora procede con la extracción:
"""

    return prompt


def build_simple_extraction_prompt_v6(job_description: str) -> str:
    """
    Versión simplificada del prompt v6.0 sin RAG (para testing)

    Args:
        job_description: Descripción de la oferta

    Returns:
        Prompt simplificado
    """
    return f"""Extrae información estructurada de esta oferta laboral en formato JSON (NLP v6.0 - 24 campos).

Descripción:
{job_description}

Campos a extraer:
- experiencia_min_anios, experiencia_max_anios, experiencia_cargo_previo
- nivel_educativo, estado_educativo, carrera_especifica
- idioma_principal, nivel_idioma_principal
- skills_tecnicas_list, tecnologias_stack_list (JSON string arrays)
- soft_skills_list, certificaciones_list (JSON string arrays)
- salario_min, salario_max, moneda
- beneficios_list, requisitos_excluyentes_list, requisitos_deseables_list (JSON string arrays)
- jornada_laboral, horario_flexible
- modalidad_contratacion (remoto/presencial/hibrido), disponibilidad_viajes (0/1)
- sector_industria, nivel_seniority

Responde solo con JSON válido, sin explicaciones.
"""


# Función helper para generar prompt rápido
def generate_extraction_prompt_v6(
    job_description: str,
    use_rag: bool = True,
    rag_context: str = "",
    regex_baseline: Optional[Dict[str, Any]] = None
) -> str:
    """
    Genera prompt de extracción v6.0 con o sin RAG

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
        return build_extraction_prompt_v6(job_description, rag_context, regex_baseline)
    else:
        return build_simple_extraction_prompt_v6(job_description)


if __name__ == '__main__':
    # Test del prompt v6.0
    test_description = """
    Buscamos Desarrollador Python Senior con 3-5 años de experiencia para trabajo híbrido.

    Requisitos:
    - Universitario completo en Ingeniería/Sistemas
    - Inglés intermedio
    - Experiencia previa como Desarrollador Backend
    - Stack: Python, Django, PostgreSQL, Docker, AWS, Redis
    - Git, CI/CD, Kubernetes

    Ofrecemos:
    - Salario: $800.000 - $1.200.000
    - OSDE
    - 2 días home office, 3 presencial
    - Día de cumpleaños libre

    Full time, horario flexible. Sin viajes requeridos.
    """

    # Prompt simple
    simple = build_simple_extraction_prompt_v6(test_description)
    print("=== PROMPT SIMPLE v6.0 ===")
    print(simple[:500])
    print(f"\n... (total: {len(simple)} caracteres)\n")

    # Prompt con RAG (simulado)
    mock_rag = "CONTEXTO RAG: 14,247 skills ESCO disponibles..."
    mock_baseline = {
        "experiencia_min_anios": 3,
        "skills_tecnicas_list": "[\"Python\", \"Django\"]"
    }

    full = build_extraction_prompt_v6(test_description, mock_rag, mock_baseline)
    print("=== PROMPT COMPLETO v6.0 CON RAG ===")
    print(full[:500])
    print(f"\n... (total: {len(full)} caracteres)")
