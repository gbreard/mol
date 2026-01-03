#!/usr/bin/env python3
"""
Extraction Prompt Template - NLP v6.2.1
=======================================

Template de prompt para extracción híbrida con RAG.
NOVEDAD v6.0: Agrega 6 campos nuevos (24 campos totales)
MEJORAS v6.1: Prompts refinados para mejorar coverage de campos críticos
MEJORAS v6.2: 10 campos nuevos (34 campos totales) basados en validación iterativa
CORRECCIÓN v6.2.1 (2025-11-27): Anti-hallucination - evitar que el LLM copie datos del ejemplo

Campos v6.0:
- experiencia_cargo_previo
- tecnologias_stack_list
- sector_industria
- nivel_seniority
- modalidad_contratacion
- disponibilidad_viajes

Mejoras v6.1 (coverage optimization):
- experiencia_max_anios: Instrucciones más agresivas para buscar rangos
- experiencia_min_anios: Inferencia reforzada desde nivel_seniority
- experiencia_cargo_previo: Ejemplos más claros y menos restricciones
- disponibilidad_viajes: Más patrones de búsqueda

Campos NUEVOS v6.2 (basados en análisis de ofertas reales):
- responsabilidades_list: Lista de tareas discretas del puesto
- empresa_publicadora: Consultora/portal que publica (si difiere)
- empresa_contratante: Empresa real que contrata
- empresa_descripcion: Descripción breve del negocio de la empresa
- licencia_conducir_requerida: Boolean si requiere registro
- licencia_conducir_categoria: Categoría mínima (B1, C, D, etc.)
- indexacion_salarial: Objeto {tiene: bool, indice: str, frecuencia: str}
- contratacion_inmediata: Boolean si es incorporación inmediata
- edad_min: Edad mínima requerida (tolerar espacios: "1 8" → 18)
- edad_max: Edad máxima requerida
"""

from typing import Dict, Any, Optional


def build_extraction_prompt_v6(
    job_description: str,
    rag_context: str,
    regex_baseline: Optional[Dict[str, Any]] = None
) -> str:
    """
    Construye prompt completo para extracción NLP v6.2 con RAG

    v6.2 incluye 34 campos (10 nuevos sobre v6.1):
    - empresa_publicadora, empresa_contratante, empresa_descripcion
    - responsabilidades_list
    - edad_min, edad_max
    - licencia_conducir_requerida, licencia_conducir_categoria
    - contratacion_inmediata
    - indexacion_salarial

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

### REGLA CRÍTICA: NO INVENTAR DATOS

**IMPORTANTE:** Extraer ÚNICAMENTE información que aparece EXPLÍCITAMENTE en la descripción.
- Si un campo no tiene información en el texto → devolver null
- NUNCA copiar valores del ejemplo de formato (es solo para mostrar la ESTRUCTURA)
- NUNCA inferir skills técnicas que no estén mencionadas explícitamente
- Si la oferta es de Contador/Administrativo → NO devolver Python/Django/tecnologías IT
- Si la oferta es de Ventas/Marketing → NO devolver stacks de programación
- Cada oferta tiene sus PROPIOS datos - extraer del texto, NO del ejemplo

**CONSECUENCIA:** Si inventas datos que no están en el texto, el sistema falla completamente.

{baseline_section}

### CONTEXTO PARA VALIDACIÓN
{rag_context}

### DESCRIPCIÓN DE LA OFERTA LABORAL
```
{job_description}
```

### INSTRUCCIONES DE EXTRACCIÓN (NLP v6.2 - 34 campos)

Extrae la información en formato JSON con los siguientes campos:

**1. EXPERIENCIA:**
- `experiencia_min_anios` (número o null): Años mínimos de experiencia requeridos
  - BUSCAR ACTIVAMENTE: "X años", "mínimo X", "al menos X", "desde X", etc.
  - INFERIR de nivel seniority si no se menciona explícitamente (ver REGLA 4 más abajo)
  - Ejemplos: "3 años mínimo" → 3, "Junior" → 0, "Senior" → 4

- `experiencia_max_anios` (número o null): Años máximos de experiencia
  - CRÍTICO: Buscar RANGOS en el texto ("X a Y años", "entre X y Y", "X-Y años")
  - Si hay mínimo, BUSCAR máximo activamente
  - Patrones: "3 a 5 años" → max:5, "hasta 10 años" → max:10
  - Si solo dice "Junior" o "Trainee" → inferir max:2
  - Si solo dice "Semi-senior" → inferir max:4
  - **OBJETIVO: NUNCA dejar null si hay evidencia de rango o nivel**

- `experiencia_cargo_previo` (string o null): **NUEVO v6.0** - Cargo/título previo específico requerido
  - BUSCAR: "experiencia como...", "haber trabajado de...", "ex ...", "proveniente de..."
  - Incluir ROLES mencionados explícitamente (no genéricos)
  - Ejemplos VÁLIDOS:
    * "experiencia como Gerente de Ventas" → "Gerente de Ventas"
    * "buscamos Desarrollador con exp. en Backend" → "Desarrollador Backend"
    * "haber trabajado de Analista" → "Analista de Datos"
  - Ejemplos INVÁLIDOS:
    * "experiencia en el área" → null (muy genérico)
    * "conocimiento del rubro" → null (no es cargo específico)

**2. EDUCACIÓN:**
- `nivel_educativo` (string): Uno de: "primario", "secundario", "terciario", "universitario", "posgrado", null
  - **NORMALIZACIÓN OBLIGATORIA - Ejemplos:**
    * "Estudiante avanzado de Licenciatura" → "universitario"
    * "Graduado/Licenciado/Ingeniero" → "universitario"
    * "Estudiante o graduado universitario" → "universitario"
    * "Técnico Superior en..." → "terciario"
    * "Tecnicatura en..." → "terciario"
    * "Secundario completo excluyente" → "secundario"
  - USAR el nivel más alto mencionado

- `estado_educativo` (string): Uno de: "en_curso", "completo", "incompleto", null
  - **SOLO el estado, NO la carrera:**
    * "Estudiante avanzado" → "en_curso"
    * "Graduado/Licenciado/Recibido" → "completo"
    * "Con o sin título" → "incompleto" (aceptan sin completar)
  - NO poner nombre de carrera aquí (va en carrera_especifica)

- `carrera_especifica` (string o null): Nombre específico de la carrera
  - Ejemplos: "Administración de Empresas", "Ingeniería Industrial", "Lic. en Comercialización"
  - Si dice "carreras afines a comercio" → "Comercio/afines"
  - **SIEMPRE extraer si se menciona carrera**

**3. IDIOMAS:**
- `idioma_principal` (string o null): Idioma principal requerido (ej: "inglés", "español")
- `nivel_idioma_principal` (string): "basico", "intermedio", "avanzado", "nativo", null

**4. SKILLS Y COMPETENCIAS:**
- `skills_tecnicas_list` (string JSON array): Lista de habilidades técnicas como JSON string
  - VALIDAR contra el diccionario ESCO provisto
  - Incluir solo skills reales y relevantes
  - **CRÍTICO: DIFERENCIAR de responsabilidades_list:**
    * Skills = herramientas, tecnologías, conocimientos (sustantivos)
    * Responsabilidades = tareas, funciones, actividades (verbos)
  - NO incluir: responsabilidades del puesto, requisitos genéricos, o descripciones largas
  - Ejemplos CORRECTOS: ["Excel", "KPIs", "análisis de ventas", "liquidación de comisiones"]
  - Ejemplos INCORRECTOS: ["Diseñar plan comercial", "Definir objetivos", "Gestionar equipo"]
  - Si dice "diseñar y gestionar KPIs" → skill es "KPIs", NO "diseñar y gestionar KPIs"

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
  - BUSCAR PATRONES: "disponibilidad para viajar", "viajes frecuentes", "viajes al interior",
    "viajes internacionales", "movilidad", "traslados", "desplazamientos"
  - También positivo: "zona de cobertura", "visitas a clientes", "recorrer territorio"

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

**10. INFORMACIÓN DE LA EMPRESA (NUEVO v6.2):**
- `empresa_publicadora` (string o null): Consultora o portal que publica la oferta
  - Si la oferta es de una consultora de RRHH buscando para otra empresa
  - **LISTA DE CONSULTORAS CONOCIDAS (detectar automáticamente):**
    * Zivot, Randstad, Manpower, Adecco, Grupo Gestión, Be Part, MCV, GI GROUP
    * Job Solutions, Ghidini Rodil, PageGroup, Michael Page, Hays, Robert Half
    * Experis, Kelly Services, Tempo, Bayton, Mia RRHH, Nexo RRHH
    * Términos clave: "Consultora", "RRHH", "Recursos Humanos", "Selección de Personal"
  - Si el nombre contiene alguna de estas → ES empresa_publicadora
  - Ejemplos: "Zivot Consultora en RH" → empresa_publicadora = "Zivot"
  - Si la empresa publica directamente (sin consultora) → null

- `empresa_contratante` (string o null): Empresa real que contrata al empleado
  - La empresa final donde trabajará el candidato
  - Si la consultora menciona el cliente → extraer el nombre
  - Ejemplos: "Toyota", "Banco Macro", "importante empresa del rubro automotriz"
  - Si publica directamente (sin consultora) → null (ya está en otro campo)

- `empresa_descripcion` (string o null): Descripción breve del negocio de la empresa
  - Rubro o actividad principal de la empresa contratante
  - Ejemplos: "Fábrica de productos plásticos", "Empresa de logística", "Fintech de pagos"
  - Extraer de menciones como "somos una empresa de...", "dedicada a...", etc.

**11. RESPONSABILIDADES DEL PUESTO (NUEVO v6.2):**
- `responsabilidades_list` (string JSON array o null): Lista de tareas discretas del puesto
  - Extraer como tareas individuales y específicas
  - NO incluir requisitos ni skills (eso va en otros campos)
  - Formato: verbos en infinitivo cuando sea posible
  - Ejemplo: '["Realizar mantenimiento preventivo", "Operar maquinaria CNC", "Reportar a supervisor"]'
  - Máximo 10 responsabilidades más relevantes

**12. REQUISITOS DEMOGRÁFICOS (NUEVO v6.2):**
- `edad_min` (número o null): Edad mínima requerida
  - Buscar: "mayor de X", "desde X años", "mínimo X años de edad"
  - IMPORTANTE: Tolerar espacios en OCR defectuoso: "1 8" → 18, "2 5" → 25
  - En Argentina no es legal discriminar por edad, pero algunas ofertas lo incluyen

- `edad_max` (número o null): Edad máxima requerida
  - Buscar: "hasta X años", "máximo X años", "menor de X"
  - Tolerar espacios: "4 5" → 45, "5 5" → 55

**13. LICENCIA DE CONDUCIR (NUEVO v6.2):**
- `licencia_conducir_requerida` (0 o 1 o null): Si requiere registro de conducir
  - 1 si menciona "registro de conducir", "carnet de conducir", "licencia", etc.
  - 0 si explícitamente dice "no requiere"
  - null si no se menciona

- `licencia_conducir_categoria` (string o null): Categoría mínima requerida
  - En Argentina: A (motos), B1/B2 (autos), C (camiones), D (transporte pasajeros), E (articulados)
  - Buscar: "registro B", "carnet tipo C", "licencia profesional"
  - Si solo dice "registro" sin especificar → "B1" (asumir particular)

**14. CONDICIONES CONTRACTUALES ADICIONALES (NUEVO v6.2):**
- `contratacion_inmediata` (0 o 1 o null): Si es incorporación inmediata
  - 1 si menciona: "incorporación inmediata", "urgente", "disponibilidad inmediata"
  - 0 si menciona fecha futura específica
  - null si no se menciona

- `indexacion_salarial` (string JSON object o null): Información de ajuste salarial
  - **CRÍTICO: SOLO extraer si hay mención EXPLÍCITA de indexación/ajuste**
  - Objeto JSON con estructura: {{"tiene": true/false, "indice": "IPC"/"UVA"/otro, "frecuencia": "mensual"/"trimestral"/etc.}}
  - Palabras clave OBLIGATORIAS: "indexado", "ajuste", "IPC", "UVA", "actualización salarial", "paritarias"
  - **NO INFERIR** - Si no menciona explícitamente → null
  - Ejemplo CORRECTO: "salario con ajuste trimestral por IPC" → '{{"tiene": true, "indice": "IPC", "frecuencia": "trimestral"}}'
  - Ejemplo INCORRECTO: No dice nada de ajuste → null (NO inventar {{"tiene": true}})

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

4. **Experiencia (CRÍTICO - MEJORADO v6.1):**
   - PRIORIDAD 1: Buscar rangos explícitos ("3 a 5 años", "entre 2 y 4")
   - PRIORIDAD 2: Buscar mínimos/máximos por separado ("mínimo 3 años", "hasta 10 años")
   - PRIORIDAD 3: Inferir de nivel seniority:
     * "Trainee/Pasante" → min:0, max:1
     * "Junior" → min:0, max:2
     * "Semi-senior" → min:2, max:4
     * "Senior" → min:4, max:null (no hay máximo claro)
   - **REGLA DE ORO**: Si tienes experiencia_min, BUSCA experiencia_max activamente
   - **NUNCA** dejes experiencia_max_anios en null si el puesto es Trainee/Junior/Semi-senior

5. **Cargo Previo (NUEVO v6.0 - MEJORADO v6.1):**
   - INCLUIR si menciona un ROL/CARGO específico previo
   - Patrones a buscar:
     * "experiencia como [CARGO]"
     * "haber trabajado de [CARGO]"
     * "proveniente de [CARGO]"
     * "[CARGO] con X años de experiencia"
   - Ejemplos VÁLIDOS (más permisivo que v6.0):
     * "Desarrollador con experiencia en Backend" → "Desarrollador Backend"
     * "Vendedor con experiencia en retail" → "Vendedor Retail"
     * "Analista de datos" → "Analista de Datos"
   - Ejemplos INVÁLIDOS:
     * "experiencia en el área" → null
     * "conocimiento del rubro" → null

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

12. **Empresa Publicadora vs Contratante (NUEVO v6.2):**
    - Si una consultora (Randstad, Manpower, etc.) publica para una empresa cliente:
      * empresa_publicadora = nombre de la consultora
      * empresa_contratante = nombre de la empresa cliente (si se menciona)
    - Si la empresa publica directamente:
      * empresa_publicadora = null
      * empresa_contratante = null (el nombre ya está en el título/datos de la oferta)
    - CLAVE: Identificar frases como "para importante cliente", "empresa del rubro...", "seleccionamos para..."

13. **Responsabilidades (NUEVO v6.2):**
    - Extraer SOLO tareas del puesto, NO requisitos
    - Formato preferido: verbos en infinitivo
    - Si el texto mezcla responsabilidades con requisitos, separar cuidadosamente
    - Máximo 10 ítems

14. **Licencia de Conducir (NUEVO v6.2):**
    - Si solo dice "registro de conducir" sin categoría → asumir "B1"
    - Si dice "registro profesional" → buscar contexto (C para camiones, D para pasajeros)
    - licencia_conducir_requerida y licencia_conducir_categoria deben ser consistentes

15. **Edad (NUEVO v6.2):**
    - CRÍTICO: Tolerar espacios en números (OCR defectuoso): "1 8" → 18, "2 5" → 25
    - Unir dígitos separados por espacio si tienen sentido como edad (18-65)
    - Si dice "mayor de edad" sin número → edad_min = 18

16. **Indexación Salarial (NUEVO v6.2):**
    - Solo extraer si hay mención EXPLÍCITA de indexación/ajuste
    - Índices comunes en Argentina: IPC, UVA, paritarias
    - Frecuencias comunes: mensual, trimestral, semestral, anual
    - Si no hay mención → null (NO inferir)

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

**ADVERTENCIA CRÍTICA sobre el ejemplo:**
El siguiente ejemplo muestra SOLO la ESTRUCTURA del JSON esperado.
Los valores son PLACEHOLDERS - NO los copies. Extrae los valores REALES del texto de la oferta.
Si un campo no tiene información en la oferta → usa null.

Ejemplo de ESTRUCTURA (NO copiar estos valores):
```json
{{
  "experiencia_min_anios": null,
  "experiencia_max_anios": null,
  "experiencia_cargo_previo": null,
  "nivel_educativo": null,
  "estado_educativo": null,
  "carrera_especifica": null,
  "idioma_principal": null,
  "nivel_idioma_principal": null,
  "skills_tecnicas_list": null,
  "tecnologias_stack_list": null,
  "soft_skills_list": null,
  "certificaciones_list": null,
  "salario_min": null,
  "salario_max": null,
  "moneda": null,
  "beneficios_list": null,
  "requisitos_excluyentes_list": null,
  "requisitos_deseables_list": null,
  "jornada_laboral": null,
  "horario_flexible": null,
  "modalidad_contratacion": null,
  "disponibilidad_viajes": null,
  "sector_industria": null,
  "nivel_seniority": null,
  "empresa_publicadora": null,
  "empresa_contratante": null,
  "empresa_descripcion": null,
  "responsabilidades_list": null,
  "edad_min": null,
  "edad_max": null,
  "licencia_conducir_requerida": null,
  "licencia_conducir_categoria": null,
  "contratacion_inmediata": null,
  "indexacion_salarial": null
}}
```

RECUERDA: Cada campo debe extraerse DEL TEXTO de la oferta. Si no está mencionado → null.

Ahora procede con la extracción:
"""

    return prompt


def build_simple_extraction_prompt_v6(job_description: str) -> str:
    """
    Versión simplificada del prompt v6.2 sin RAG (para testing)

    Args:
        job_description: Descripción de la oferta

    Returns:
        Prompt simplificado
    """
    return f"""Extrae información estructurada de esta oferta laboral en formato JSON (NLP v6.2 - 34 campos).

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
- empresa_publicadora (consultora que publica), empresa_contratante (empresa real), empresa_descripcion
- responsabilidades_list (tareas discretas como JSON array)
- edad_min, edad_max (tolerar espacios en OCR: "1 8" → 18)
- licencia_conducir_requerida (0/1), licencia_conducir_categoria (B1/C/D/etc)
- contratacion_inmediata (0/1)
- indexacion_salarial (JSON object: {{"tiene": bool, "indice": str, "frecuencia": str}})

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
    # Test del prompt v6.2
    test_description = """
    Randstad selecciona para importante empresa del rubro automotriz:

    Buscamos Desarrollador Python Senior con 3-5 años de experiencia para trabajo híbrido.
    Incorporación inmediata.

    Requisitos:
    - Universitario completo en Ingeniería/Sistemas
    - Inglés intermedio
    - Experiencia previa como Desarrollador Backend
    - Stack: Python, Django, PostgreSQL, Docker, AWS, Redis
    - Git, CI/CD, Kubernetes
    - Edad: 25-45 años
    - Registro de conducir tipo B

    Responsabilidades:
    - Desarrollar y mantener APIs REST
    - Diseñar arquitectura de microservicios
    - Realizar code reviews
    - Mentorear desarrolladores junior

    Ofrecemos:
    - Salario: $800.000 - $1.200.000 (con ajuste trimestral por IPC)
    - OSDE
    - 2 días home office, 3 presencial
    - Día de cumpleaños libre

    Full time, horario flexible. Sin viajes requeridos.
    """

    # Prompt simple
    simple = build_simple_extraction_prompt_v6(test_description)
    print("=== PROMPT SIMPLE v6.2 ===")
    print(simple[:500])
    print(f"\n... (total: {len(simple)} caracteres)\n")

    # Prompt con RAG (simulado)
    mock_rag = "CONTEXTO RAG: 14,247 skills ESCO disponibles..."
    mock_baseline = {
        "experiencia_min_anios": 3,
        "skills_tecnicas_list": "[\"Python\", \"Django\"]"
    }

    full = build_extraction_prompt_v6(test_description, mock_rag, mock_baseline)
    print("=== PROMPT COMPLETO v6.2 CON RAG ===")
    print(full[:500])
    print(f"\n... (total: {len(full)} caracteres)")
