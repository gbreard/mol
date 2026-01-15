# -*- coding: utf-8 -*-
"""
Prompt de Extraccion NLP LITE v1.2 - Campos para NLP + Matching
===============================================================

VERSION: 1.2
FECHA: 2026-01-12
CAMBIO: Regla 3 agregada - tareas_explicitas debe separar cada tarea con punto y coma
MODELO: Qwen2.5:14b (optimizado para velocidad)

OBJETIVO: Reducir tiempo de 4 min a <30 seg por oferta
ESTRATEGIA: 20 campos normalizables (15 NLP + 5 Matching)

CAMPOS (20):
  GRUPO 1 - NLP Base (15):
  - titulo_ocupacion (ESCO)
  - provincia, localidad (INDEC)
  - sector_empresa (CIIU)
  - tareas_explicitas (ESCO skills)
  - skills_tecnicas_list, soft_skills_list, tecnologias_list, herramientas_list (ESCO)
  - experiencia_min_anios, experiencia_max_anios (int)
  - nivel_educativo, titulo_requerido (CINE)
  - requerimiento_edad (cat 0-5), requerimiento_sexo (cat 0-2)

  GRUPO 2 - Matching ESCO (5):
  - area_funcional (cat: IT, Ventas, etc.)
  - nivel_seniority (cat: trainee-director)
  - tiene_gente_cargo (bool)
  - mision_rol (string)
  - tipo_oferta (cat: demanda_real, pasantia, etc.)

NOTA: Salarios, jornada, modalidad se extraen con regex en CAPA 0.
"""


EXTRACTION_PROMPT_LITE_V1 = """Extrae informacion de esta oferta laboral argentina.

Devuelve SOLO un JSON con estos 20 campos. Si no encuentras info, usa null o [].

## FORMATO JSON

```json
{{
  "titulo_ocupacion": "string - titulo limpio del puesto (sin empresa ni ubicacion)",
  "provincia": "string - provincia argentina",
  "localidad": "string - ciudad o localidad",
  "sector_empresa": "string - sector economico (tecnologia, salud, comercio, etc)",
  "tareas_explicitas": "string - lista de tareas separadas por punto y coma",
  "skills_tecnicas_list": ["skill1", "skill2"],
  "soft_skills_list": ["skill1", "skill2"],
  "tecnologias_list": ["tech1", "tech2"],
  "herramientas_list": ["herramienta1", "herramienta2"],
  "experiencia_min_anios": 0,
  "experiencia_max_anios": null,
  "nivel_educativo": "primario|secundario|terciario|universitario|posgrado",
  "titulo_requerido": "string - carrera o titulo especifico si se menciona",
  "requerimiento_edad": 0,
  "requerimiento_sexo": 0,
  "area_funcional": "IT|Ventas|Operaciones|RRHH|Administracion|Salud|Produccion|Logistica|Marketing|Legal|Finanzas|Otro",
  "nivel_seniority": "trainee|junior|semisenior|senior|lead|manager|director",
  "tiene_gente_cargo": false,
  "mision_rol": "string - objetivo principal del puesto en una oracion",
  "tipo_oferta": "demanda_real|pasantia|becario|freelance"
}}
```

## REGLAS IMPORTANTES

1. **titulo_ocupacion**: Solo el nombre del puesto, sin empresa ni ubicacion.
   - OK: "Desarrollador Python Senior"
   - MAL: "Desarrollador Python Senior - Empresa XYZ - CABA"

2. **Skills**: Distinguir entre:
   - skills_tecnicas_list: conocimientos especificos del area (contabilidad, soldadura, atencion al cliente)
   - soft_skills_list: habilidades blandas (comunicacion, trabajo en equipo, liderazgo)
   - tecnologias_list: lenguajes, frameworks, plataformas (Python, React, AWS, SAP)
   - herramientas_list: software/equipos especificos (Excel, AutoCAD, montacargas)

3. **tareas_explicitas**: Extraer CADA responsabilidad/tarea como item separado, usando punto y coma (;) como separador.
   - Buscar bullets (-), numeracion (1., 2.), o "Responsabilidades:" en la descripcion
   - Extraer cada tarea de forma INDIVIDUAL, no resumir ni condensar
   - OK: "Auditar prestaciones domiciliarias; Elaborar informes de gestion; Cumplir normativas ISO"
   - MAL: "auditar, revisar documentacion, cumplimiento de protocolos" (todo junto, sin separar)
   - Si hay 5 responsabilidades listadas, deben aparecer 5 items separados por punto y coma

4. **experiencia**: Solo numeros. Si dice "2-3 anios", min=2, max=3. Si dice "3+", min=3, max=null.

5. **requerimiento_edad** (categorias):
   - 0 = sin requisito de edad
   - 1 = 18-25 anios
   - 2 = 25-35 anios
   - 3 = 35-45 anios
   - 4 = 45+ anios
   - 5 = ambiguo/no claro

6. **requerimiento_sexo** (categorias):
   - 0 = sin requisito de sexo
   - 1 = masculino
   - 2 = femenino

7. **area_funcional**: Area principal del puesto:
   - IT = sistemas, desarrollo, soporte tecnico
   - Ventas = comercial, ventas, atencion al cliente
   - Operaciones = produccion, manufactura, calidad
   - RRHH = recursos humanos, seleccion, capacitacion
   - Administracion = administracion, secretaria, recepcion
   - Salud = medicina, enfermeria, salud
   - Produccion = fabrica, manufactura, operarios
   - Logistica = deposito, distribucion, transporte
   - Marketing = marketing, publicidad, comunicacion
   - Legal = legal, abogados, compliance
   - Finanzas = contabilidad, finanzas, auditoria
   - Otro = si no encaja en ninguna categoria

8. **nivel_seniority**: Nivel de experiencia requerido:
   - trainee = sin experiencia, primer empleo
   - junior = hasta 2 anios de experiencia
   - semisenior = 2-5 anios de experiencia
   - senior = 5+ anios de experiencia
   - lead = lider tecnico, referente
   - manager = gerente, jefe de area
   - director = director, C-level

9. **tiene_gente_cargo**: true si supervisa personal, coordina equipos, o tiene reportes directos.

10. **mision_rol**: Objetivo principal del puesto en UNA oracion corta. Ejemplo: "Liderar el equipo de desarrollo backend y garantizar la calidad del codigo".

11. **tipo_oferta**: Tipo de contratacion:
    - demanda_real = empleo formal tradicional
    - pasantia = pasantia universitaria
    - becario = programa de becarios/trainees
    - freelance = trabajo independiente, por proyecto

## OFERTA A PROCESAR

TITULO: {titulo}
EMPRESA: {empresa}
UBICACION: {ubicacion}

DESCRIPCION:
{descripcion}

Responde SOLO con el JSON, sin explicaciones."""


def get_prompt_lite(titulo: str, empresa: str, ubicacion: str, descripcion: str) -> str:
    """Genera el prompt con los datos de la oferta."""
    return EXTRACTION_PROMPT_LITE_V1.format(
        titulo=titulo or "",
        empresa=empresa or "",
        ubicacion=ubicacion or "",
        descripcion=descripcion or ""
    )


# Schema para validacion (20 campos)
SCHEMA_LITE = {
    # Grupo 1: NLP Base (15)
    "titulo_ocupacion": str,
    "provincia": str,
    "localidad": str,
    "sector_empresa": str,
    "tareas_explicitas": str,
    "skills_tecnicas_list": list,
    "soft_skills_list": list,
    "tecnologias_list": list,
    "herramientas_list": list,
    "experiencia_min_anios": int,
    "experiencia_max_anios": int,
    "nivel_educativo": str,
    "titulo_requerido": str,
    "requerimiento_edad": int,
    "requerimiento_sexo": int,
    # Grupo 2: Matching ESCO (5)
    "area_funcional": str,
    "nivel_seniority": str,
    "tiene_gente_cargo": bool,
    "mision_rol": str,
    "tipo_oferta": str,
}

# Valores validos para campos categoricos
VALID_EDAD = {0, 1, 2, 3, 4, 5}
VALID_SEXO = {0, 1, 2}
VALID_EDUCACION = {"primario", "secundario", "terciario", "universitario", "posgrado"}
VALID_AREA_FUNCIONAL = {
    "IT", "Ventas", "Operaciones", "RRHH", "Administracion",
    "Salud", "Produccion", "Logistica", "Marketing", "Legal", "Finanzas", "Otro"
}
VALID_SENIORITY = {"trainee", "junior", "semisenior", "senior", "lead", "manager", "director"}
VALID_TIPO_OFERTA = {"demanda_real", "pasantia", "becario", "freelance"}
