# -*- coding: utf-8 -*-
"""
Prompt de Extraccion NLP v8.0 - QWEN 14B ULTRA-CONSERVADOR
==========================================================

VERSION: 8.0
FECHA: 2025-11-27
MODELO: Qwen2.5:14b

CAMBIOS v8.0:
  - Prompt rediseñado para Qwen2.5:14b con ejemplos negativos explicitos
  - Enfasis en COPIA LITERAL y NO INVENTAR
  - Ejemplos negativos: Excel/Excelentes, relacionesinterpersonales
  - Formato {valor, texto_original} reforzado
  - Instrucciones claras sobre cuando NO agregar items

CAMPOS (7 campos):
1. skills_tecnicas_list
2. soft_skills_list
3. requisitos_list          (Python clasifica excluyente/deseable despues)
4. beneficios_list
5. responsabilidades_list
6. tecnologias_stack_list
7. certificaciones_list

ANTI-ALUCINACION: Cada item DEBE incluir "texto_original" LITERAL.
"""


EXTRACTION_PROMPT_V8 = """Eres un extractor de informacion para ofertas laborales argentinas.

Tu tarea es LEER la oferta de trabajo y devolver SOLO un objeto JSON con 7 campos.

## REGLA FUNDAMENTAL: COPIA LITERAL

Para cada elemento que extraigas, DEBES devolver un objeto con:
- "texto_original": fragmento EXACTO copiado de la oferta (sin inventarlo)
- "valor": el mismo texto o una version recortada, SIN CAMBIAR PALABRAS

Si no puedes citar texto LITERAL del aviso, NO agregues el item.
Es mejor una lista vacia [] que inventar datos.

## CAMPOS A EXTRAER

```json
{{
  "skills_tecnicas_list": [],
  "soft_skills_list": [],
  "requisitos_list": [],
  "beneficios_list": [],
  "responsabilidades_list": [],
  "tecnologias_stack_list": [],
  "certificaciones_list": []
}}
```

## REGLAS POR CAMPO

### skills_tecnicas_list
Lenguajes, herramientas, tecnologias que aparezcan EXPLICITAMENTE.
- Solo si el nombre aparece textual: "Python", "Excel", "SAP", "SQL Server"
- NO conviertas adjetivos en tecnologias

### soft_skills_list
Habilidades blandas: "trabajo en equipo", "liderazgo", "proactivo"
- Copia LITERAL del texto, no parafrasees

### requisitos_list
Requisitos del puesto: educacion, experiencia, idiomas, licencias
- Frases completas copiadas del aviso
- NO agregues "(excluyente)" si no esta escrito

### beneficios_list
Beneficios: "prepaga", "home office", "dia de cumpleanos libre"
- Copia literal del texto

### responsabilidades_list
Tareas del puesto: "Realizar auditorias", "Control de stock"
- Frases cortas pero LITERALES

### tecnologias_stack_list
Stack tecnologico (solo puestos IT): "Docker", "AWS", "React"
- Si NO es puesto IT, dejar vacio []

### certificaciones_list
Certificaciones especificas: "PMP", "AWS Certified", "Contador Publico"
- Solo si aparece textual

## EJEMPLOS NEGATIVOS - MUY IMPORTANTE

### Ejemplo 1: Excel vs Excelentes
Texto: "Excelentes habilidades analiticas y de resolucion de problemas."

INCORRECTO:
"skills_tecnicas_list": [{{"valor": "Excel", "texto_original": "Excelentes"}}]

CORRECTO:
"skills_tecnicas_list": []

Explicacion: La palabra "Excel" NO aparece. "Excelentes" es un adjetivo, NO una tecnologia.

### Ejemplo 2: No parafrasear soft skills
Texto: "Ser proactivo, organizado, con gran capacidad negociadora y excelente manejo de relacionesinterpersonales."

INCORRECTO:
"soft_skills_list": [
  {{"valor": "proactividad", "texto_original": "Ser proactivo"}},
  {{"valor": "organizacion", "texto_original": "organizado"}},
  {{"valor": "capacidad de negociacion", "texto_original": "gran capacidad negociadora"}}
]

CORRECTO:
"soft_skills_list": [
  {{"valor": "proactivo", "texto_original": "Ser proactivo"}},
  {{"valor": "organizado", "texto_original": "organizado"}},
  {{"valor": "gran capacidad negociadora", "texto_original": "gran capacidad negociadora"}},
  {{"valor": "relacionesinterpersonales", "texto_original": "relacionesinterpersonales"}}
]

Explicacion: Copia LITERAL. Si dice "proactivo", no escribas "proactividad". Si esta mal escrito ("relacionesinterpersonales"), copialo igual.

### Ejemplo 3: No inventar requisitos
Texto: "Buscamos contador para estudio contable."

INCORRECTO:
"requisitos_list": [{{"valor": "Titulo de Contador Publico", "texto_original": "contador"}}]

CORRECTO:
"requisitos_list": []

Explicacion: El texto NO dice "Titulo de Contador Publico". Solo menciona "contador" como descripcion del puesto.

### Ejemplo 4: Skills tecnicas correctas
Texto: "Python y/o Node.js (al menos uno a nivel productivo)."

CORRECTO:
"skills_tecnicas_list": [
  {{"valor": "Python", "texto_original": "Python y/o Node.js (al menos uno a nivel productivo)."}},
  {{"valor": "Node.js", "texto_original": "Python y/o Node.js (al menos uno a nivel productivo)."}}
]

## FORMATO DE SALIDA

Devuelve SOLO un JSON valido con los 7 campos.
NO incluyas explicaciones, comentarios ni texto fuera del JSON.

---

## OFERTA A ANALIZAR:

{descripcion}

---

Responde SOLO con el JSON:"""


def build_prompt(descripcion: str) -> str:
    """
    Construye el prompt con la descripcion de la oferta.

    Args:
        descripcion: Texto de la descripcion de la oferta

    Returns:
        Prompt completo listo para enviar al LLM
    """
    return EXTRACTION_PROMPT_V8.format(descripcion=descripcion)


# Schema JSON para validacion
JSON_SCHEMA_V8 = {
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


# Campos que extrae este prompt (para referencia) - v8.0: 7 campos
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
    - Titulo de Contador Publico
    - 5 anos de experiencia en auditoria
    - Manejo avanzado de Excel y sistemas contables

    Requisitos deseables:
    - Conocimiento en SAP
    - Ingles intermedio

    Funciones:
    - Realizar auditorias contables
    - Preparar estados financieros
    - Supervisar equipo de 3 personas

    Beneficios:
    - Prepaga OSDE
    - Horario flexible
    - Home office 2 dias
    """

    prompt = build_prompt(descripcion_test)
    print("=== PROMPT v8 ===")
    print(prompt[:1000] + "...")
