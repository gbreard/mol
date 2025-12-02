# -*- coding: utf-8 -*-
"""
Prompt de Extracción NLP v7.3 - REQUISITOS UNIFICADOS
=====================================================

VERSION: 7.3
FECHA: 2025-11-27
MODELO: Hermes3:8b

CAMBIO v7.3: Unificación de requisitos + detección tech por diccionario.
  - requisitos_list único (Python clasifica excluyente/deseable después)
  - tecnologias_stack ahora se complementa con detección por diccionario
  - Normalización robusta con unicodedata.normalize("NFKC")

CAMBIO v7.2: Prompt optimizado para balance precisión/recall.
  - Instrucciones claras de NO INVENTAR
  - texto_original debe ser copia LITERAL
  - Post-procesamiento de prefijos en código Python

CAMBIO v7.1: Fix para problema de contaminación de spans.

CAMPOS PARA LLM (7 campos):
1. skills_tecnicas_list
2. soft_skills_list
3. requisitos_list          (NUEVO: unificado, Python clasifica después)
4. beneficios_list
5. responsabilidades_list
6. tecnologias_stack_list
7. certificaciones_list

ANTI-ALUCINACIÓN: Cada item debe incluir "texto_original" LITERAL para verificación.
"""


EXTRACTION_PROMPT_V7 = """
Eres un extractor de datos de ofertas de empleo argentinas.

## TU ÚNICA TAREA

Extraer 7 campos específicos de la descripción de la oferta.
Para cada item que extraigas, DEBES incluir el texto exacto donde lo encontraste.

## REGLA CRÍTICA: NO INVENTAR

- Extrae ÚNICAMENTE información que aparece EXPLÍCITAMENTE en el texto
- Si un campo no tiene información → devolver lista vacía []
- NUNCA inventes datos que no están en el texto
- Cada item DEBE incluir "texto_original" con la cita exacta del texto

EJEMPLOS DE ERRORES COMUNES (NO HACER):
- Si el texto dice "estudio contable" → NO extraer "Excel" (no lo menciona)
- Si el texto dice "experiencia en contabilidad" → NO extraer "SAP" (no lo menciona)
- Si NO menciona herramientas específicas → skills_tecnicas_list: []

## REGLA: texto_original = COPIA LITERAL

El campo "texto_original" DEBE ser una COPIA EXACTA del texto.
NO agregues prefijos como "Requisito", "Beneficio", "Responsabilidad".

Si el texto dice: "Requisitos: Título universitario"
- CORRECTO: "Título universitario"
- INCORRECTO: "Requisito Título universitario"

## CAMPOS A EXTRAER (7 total)

### 1. skills_tecnicas_list
Skills técnicas/herramientas mencionadas (Excel, SAP, Python, etc.)
- Solo extraer si el nombre de la herramienta aparece explícitamente
- NO inferir tecnologías por el sector

### 2. soft_skills_list
Habilidades blandas (trabajo en equipo, comunicación, liderazgo, etc.)

### 3. requisitos_list
TODOS los requisitos mencionados (excluyentes Y deseables)
- Incluir experiencia, educación, idiomas, licencias, etc.
- NO separar por tipo - extrae todos en una sola lista
- El sistema Python clasificará después cuáles son excluyentes/deseables

### 4. beneficios_list
Beneficios ofrecidos (prepaga, gimnasio, home office, etc.)

### 5. responsabilidades_list
Tareas y funciones del puesto
- Separar en items discretos
- NO mezclar con requisitos

### 6. tecnologias_stack_list
Stack tecnológico específico (solo para puestos IT)
- Si la oferta NO es de IT, devolver lista vacía []

### 7. certificaciones_list
Certificaciones específicas requeridas
- Ejemplos: PMP, AWS, ISO, IATF, CPA, CFA

## FORMATO DE SALIDA

Devuelve UN JSON con este formato EXACTO:

```json
{{
  "skills_tecnicas_list": [
    {{"valor": "Excel", "texto_original": "manejo avanzado de Excel"}},
    {{"valor": "SAP", "texto_original": "conocimiento en SAP"}}
  ],
  "soft_skills_list": [
    {{"valor": "trabajo en equipo", "texto_original": "capacidad de trabajo en equipo"}}
  ],
  "requisitos_list": [
    {{"valor": "3 años de experiencia", "texto_original": "3 años de experiencia en auditoría"}},
    {{"valor": "Título universitario", "texto_original": "Título de Contador Público"}},
    {{"valor": "Inglés intermedio", "texto_original": "Inglés intermedio (deseable)"}}
  ],
  "beneficios_list": [
    {{"valor": "prepaga", "texto_original": "prepaga OSDE"}}
  ],
  "responsabilidades_list": [
    {{"valor": "gestionar proveedores", "texto_original": "gestionar proveedores nacionales"}}
  ],
  "tecnologias_stack_list": [],
  "certificaciones_list": []
}}
```

## IMPORTANTE - VERIFICACIÓN AUTOMÁTICA

Tu respuesta será verificada automáticamente:
- El sistema buscará si "texto_original" existe LITERALMENTE en el texto original
- Si agregaste palabras que no están en el texto → el item será DESCARTADO
- Si "texto_original" no es una copia exacta → el item será DESCARTADO

Reglas finales:
- "texto_original" = copia LITERAL de una porción del texto (sin agregar nada)
- Si no encontrás información para un campo → lista vacía []
- NO inventes items
- NO copies los valores del ejemplo de formato
- NO agregues prefijos como "Requisito", "Beneficio", "Responsabilidad" al texto_original

---

## DESCRIPCIÓN DE LA OFERTA A ANALIZAR:

{descripcion}

---

Responde SOLO con el JSON, sin explicaciones adicionales.
"""


def build_prompt(descripcion: str) -> str:
    """
    Construye el prompt con la descripción de la oferta.

    Args:
        descripcion: Texto de la descripción de la oferta

    Returns:
        Prompt completo listo para enviar al LLM
    """
    return EXTRACTION_PROMPT_V7.format(descripcion=descripcion)


# Schema JSON para validación
JSON_SCHEMA_V7 = {
    "type": "object",
    "properties": {
        "skills_tecnicas_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "soft_skills_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "requisitos_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "beneficios_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "responsabilidades_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "tecnologias_stack_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        },
        "certificaciones_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "texto_original": {"type": "string"}
                },
                "required": ["valor", "texto_original"]
            }
        }
    },
    "required": [
        "skills_tecnicas_list",
        "soft_skills_list",
        "requisitos_list",
        "beneficios_list",
        "responsabilidades_list",
        "tecnologias_stack_list",
        "certificaciones_list"
    ]
}


# Campos que extrae este prompt (para referencia) - v7.3: 7 campos
CAMPOS_LLM = [
    "skills_tecnicas_list",
    "soft_skills_list",
    "requisitos_list",
    "beneficios_list",
    "responsabilidades_list",
    "tecnologias_stack_list",
    "certificaciones_list"
]


if __name__ == "__main__":
    # Test
    descripcion_test = """
    Buscamos Contador Senior para importante estudio contable.

    Requisitos excluyentes:
    - Título de Contador Público
    - 5 años de experiencia en auditoría
    - Manejo avanzado de Excel y sistemas contables

    Requisitos deseables:
    - Conocimiento en SAP
    - Inglés intermedio

    Funciones:
    - Realizar auditorías contables
    - Preparar estados financieros
    - Supervisar equipo de 3 personas

    Beneficios:
    - Prepaga OSDE
    - Horario flexible
    - Home office 2 días
    """

    prompt = build_prompt(descripcion_test)
    print("=== PROMPT v7 ===")
    print(prompt[:500] + "...")
