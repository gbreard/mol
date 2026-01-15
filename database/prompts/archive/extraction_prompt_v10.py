# -*- coding: utf-8 -*-
"""
Prompt de Extraccion NLP v10.0 - NLP SCHEMA v5 COMPLETO (16 Bloques)
====================================================================

VERSION: 10.0
FECHA: 2025-12-10
MODELO: Qwen2.5:14b
ISSUE: MOL-62

CAMBIOS v10.0:
  - Schema v5 COMPLETO con 16 bloques y ~95 campos nuevos (143 total en BD)
  - Organizado en bloques tematicos para mejor precision
  - Campos criticos para matching ESCO priorizados
  - Trazabilidad de fuentes con texto_original

BLOQUES (16):
  1. Metadata Portal (del scraping)
  2. Empresa (6 campos)
  3. Ubicacion y Movilidad (11 campos)
  4. Experiencia (9 campos)
  5. Educacion (8 campos)
  6. Skills y Conocimientos (10 campos)
  7. Idiomas (4 campos)
  8. Rol y Tareas (8 campos)
  9. Condiciones Laborales (8 campos)
  10. Compensacion (12 campos)
  11. Beneficios (12 campos)
  12. Metadatos NLP (5 campos)
  13. Licencias y Permisos (7 campos)
  14. Calidad y Flags (12 campos)
  15. Certificaciones (4 campos)
  16. Condiciones Especiales (12 campos)

ANTI-ALUCINACION: texto_original obligatorio para campos lista.
"""


EXTRACTION_PROMPT_V10 = """Eres un extractor de informacion para ofertas laborales argentinas.

Tu tarea es LEER la oferta de trabajo y devolver SOLO un objeto JSON organizado en 16 bloques.

## REGLA FUNDAMENTAL: COPIA LITERAL

Para cada elemento de LISTA que extraigas, DEBES devolver un objeto con:
- "texto_original": fragmento EXACTO copiado de la oferta (sin inventarlo)
- "valor": el mismo texto o una version normalizada

Para campos SIMPLES (string, boolean, int), devuelve el valor directamente.

Si no puedes citar texto LITERAL del aviso, NO agregues el item.
Es mejor null o [] que inventar datos.

## ESTRUCTURA JSON (16 BLOQUES)

```json
{{
  "empresa": {{
    "sector_empresa": null,
    "rubro_empresa": null,
    "empresa_tamanio": null,
    "es_tercerizado": null,
    "cliente_final": null
  }},
  "ubicacion": {{
    "provincia": null,
    "localidad": null,
    "modalidad": null,
    "requiere_viajar": null,
    "frecuencia_viaje": null,
    "requiere_movilidad_propia": null,
    "zona_residencia_req": null
  }},
  "experiencia": {{
    "experiencia_min_anios": null,
    "experiencia_max_anios": null,
    "experiencia_texto": null,
    "experiencia_nivel_previo": null,
    "experiencia_sector": null,
    "experiencia_areas_list": [],
    "experiencia_excluyente": null
  }},
  "educacion": {{
    "nivel_educativo": null,
    "nivel_educativo_excluyente": null,
    "titulo_requerido": null,
    "carrera_especifica": null,
    "orientacion_estudios": null,
    "acepta_estudiantes_avanzados": null,
    "estudios_valorados_list": []
  }},
  "skills": {{
    "skills_tecnicas_list": [],
    "soft_skills_list": [],
    "perfil_actitudinal_list": [],
    "conocimientos_especificos_list": [],
    "herramientas_list": [],
    "tecnologias_list": [],
    "marcas_especificas_list": [],
    "conocimiento_excluyente_list": []
  }},
  "idiomas": {{
    "idioma_principal": null,
    "idioma_nivel": null,
    "idioma_excluyente": null,
    "idiomas_adicionales_list": []
  }},
  "rol": {{
    "mision_rol": null,
    "tareas_explicitas_list": [],
    "tareas_inferidas_list": [],
    "producto_servicio": null,
    "tiene_gente_cargo": null,
    "tipo_equipo": null,
    "interactua_con_externos_list": []
  }},
  "condiciones": {{
    "area_funcional": null,
    "nivel_seniority": null,
    "jornada_laboral": null,
    "tipo_contrato": null,
    "horario_especifico": null,
    "dias_trabajo_list": [],
    "hora_entrada": null,
    "hora_salida": null
  }},
  "compensacion": {{
    "salario_min": null,
    "salario_max": null,
    "moneda": null,
    "salario_periodo": null,
    "salario_neto": null,
    "tiene_comisiones": null,
    "tiene_bonos": null,
    "estructura_salarial": null,
    "pide_pretension_salarial": null
  }},
  "beneficios": {{
    "beneficios_list": [],
    "tiene_cobertura_salud": null,
    "cobertura_salud_familia": null,
    "tiene_comedor": null,
    "tiene_capacitacion": null,
    "tiene_crecimiento": null,
    "vehiculo_provisto": null
  }},
  "licencias": {{
    "licencia_conducir": null,
    "licencia_conducir_excluyente": null,
    "tipo_licencia": null,
    "licencia_autoelevador": null,
    "matricula_profesional": null,
    "matricula_tipo": null
  }},
  "calidad": {{
    "tipo_oferta": null,
    "calidad_texto": null,
    "tiene_requisitos_discriminatorios": null,
    "tipo_discriminacion_list": [],
    "requisito_sexo": null,
    "requisito_edad_min": null,
    "requisito_edad_max": null,
    "titulo_normalizado": null,
    "tiene_clausula_diversidad": null
  }},
  "certificaciones": {{
    "certificaciones_list": [],
    "certificaciones_tecnicas_list": [],
    "certificaciones_seguridad_list": []
  }},
  "condiciones_especiales": {{
    "trabajo_en_altura": null,
    "trabajo_exterior": null,
    "trabajo_nocturno": null,
    "trabajo_turnos_rotativos": null,
    "trabajo_fines_semana": null,
    "requiere_esfuerzo_fisico": null,
    "ambiente_trabajo": null
  }}
}}
```

## REGLAS POR BLOQUE

### BLOQUE 2: EMPRESA

- **sector_empresa**: Sector de la empresa. Valores: "Retail/Comercio", "Tecnologia/Software", "Salud/Farmaceutica", "Manufactura/Industria", "Servicios Financieros", "Construccion", "Educacion", "Alimentacion", "Transporte/Logistica", "Consultoria", "Telecomunicaciones"
- **rubro_empresa**: Rubro especifico dentro del sector. Ej: "supermercados", "laboratorio", "fintech"
- **empresa_tamanio**: Tamano si se menciona. Ej: "500 empleados", "multinacional", "PyME"
- **es_tercerizado** (boolean): true si es consultora buscando para cliente ("para importante empresa", "cliente final")
- **cliente_final**: Si es_tercerizado=true, quien es el cliente. Ej: "importante banco", "compania de telecomunicaciones"

### BLOQUE 3: UBICACION Y MOVILIDAD

- **provincia**: Provincia argentina. Ej: "Buenos Aires", "CABA", "Cordoba"
- **localidad**: Localidad especifica. Ej: "Villa Lynch", "Pacheco", "Pilar"
- **modalidad**: "presencial", "remoto", "hibrido"
- **requiere_viajar** (boolean): true si requiere viajes
- **frecuencia_viaje**: "frecuente", "ocasional", "esporadico"
- **requiere_movilidad_propia** (boolean): true si pide auto/moto propia
- **zona_residencia_req**: Zona donde debe residir. Ej: "cerca de Esteban Echeverria"

### BLOQUE 4: EXPERIENCIA

- **experiencia_min_anios** (int): Minimo de anos. 0 si dice "sin experiencia"
- **experiencia_max_anios** (int): Maximo de anos si especifica rango
- **experiencia_texto**: Texto LITERAL. Ej: "amplia experiencia", "3 a 5 anos"
- **experiencia_nivel_previo**: Nivel anterior requerido. Ej: "Analista Sr", "Supervisor"
- **experiencia_sector**: Sector de experiencia. Ej: "retail", "automotriz"
- **experiencia_areas_list**: Areas de experiencia (lista con texto_original)
- **experiencia_excluyente** (boolean): true si es excluyente

Conversion experiencia:
- "sin experiencia", "1er empleo" -> 0 anos
- "experiencia", "experiencia previa" -> 1-2 anos
- "amplia experiencia" -> 3+ anos
- "solida experiencia" -> 3-5 anos
- "extensa trayectoria" -> 7+ anos

### BLOQUE 5: EDUCACION

- **nivel_educativo**: "primario", "secundario", "terciario", "universitario", "posgrado"
- **nivel_educativo_excluyente** (boolean): true si es excluyente
- **titulo_requerido**: Titulo especifico. Ej: "Contador Publico", "Ing. Industrial"
- **carrera_especifica**: Carrera requerida. Ej: "Administracion de Empresas"
- **orientacion_estudios**: "tecnica", "comercial", "humanistica"
- **acepta_estudiantes_avanzados** (boolean): true si acepta estudiantes avanzados
- **estudios_valorados_list**: Estudios valorados (lista con texto_original)

### BLOQUE 6: SKILLS Y CONOCIMIENTOS

Todos los campos lista llevan objetos {{"valor": "...", "texto_original": "..."}}

- **skills_tecnicas_list**: Skills tecnicas EXPLICITAS. Ej: "Excel", "SAP", "Python"
- **soft_skills_list**: Habilidades blandas. Ej: "trabajo en equipo", "comunicacion"
- **perfil_actitudinal_list**: Rasgos de personalidad. Ej: "proactivo", "dinamico"
- **conocimientos_especificos_list**: Conocimientos de dominio. Ej: "normas IRAM", "legislacion laboral"
- **herramientas_list**: Herramientas/software. Ej: "Word", "Tango", "AutoCAD"
- **tecnologias_list**: Tecnologias (IT). Ej: "Docker", "AWS", "React"
- **marcas_especificas_list**: Marcas. Ej: "Hikvision", "Cisco", "Oracle"
- **conocimiento_excluyente_list**: Conocimientos excluyentes (lista con texto_original)

### BLOQUE 7: IDIOMAS

- **idioma_principal**: Idioma principal. Ej: "ingles", "portugues"
- **idioma_nivel**: "basico", "intermedio", "avanzado", "nativo"
- **idioma_excluyente** (boolean): true si es excluyente
- **idiomas_adicionales_list**: Lista con {{"idioma": "...", "nivel": "..."}}

### BLOQUE 8: ROL Y TAREAS

- **mision_rol**: Descripcion breve del rol
- **tareas_explicitas_list**: Tareas LITERALES del aviso (lista con texto_original)
- **tareas_inferidas_list**: Tareas que se pueden inferir del contexto
- **producto_servicio**: Que vende/produce. Ej: "Plan de Ahorro", "seguros"
- **tiene_gente_cargo** (boolean): true si supervisa equipo
- **tipo_equipo**: Tipo de equipo. Ej: "vendedores", "tecnicos", "cuadrilla"
- **interactua_con_externos_list**: Con quienes interactua externamente

### BLOQUE 9: CONDICIONES LABORALES

- **area_funcional**: "Ventas/Comercial", "RRHH", "IT/Sistemas", "Administracion/Finanzas", "Operaciones/Logistica", "Marketing", "Legal", "Salud", "Produccion", "Atencion al Cliente", "Compras"
- **nivel_seniority**: "trainee", "junior", "semi-senior", "senior", "lead", "manager"
- **jornada_laboral**: "full-time", "part-time"
- **tipo_contrato**: "indeterminado", "temporal", "eventual", "pasantia"
- **horario_especifico**: Horario textual. Ej: "Lunes a Viernes 9 a 18"
- **dias_trabajo_list**: Dias (lista)
- **hora_entrada**: "09:00"
- **hora_salida**: "18:00"

Pistas seniority:
- "Sin experiencia", "1er empleo" -> "junior"
- "Jr", "Junior" en titulo -> "junior"
- "Ssr", "Semi Senior" -> "semi-senior"
- "Sr", "Senior" en titulo -> "senior"
- "Jefe", "Coord", "Supervisor" -> "lead"
- "Gerente", "Director" -> "manager"

### BLOQUE 10: COMPENSACION

- **salario_min** (int): Salario minimo
- **salario_max** (int): Salario maximo
- **moneda**: "ARS", "USD"
- **salario_periodo**: "mensual", "anual", "por hora"
- **salario_neto** (boolean): true si dice "en mano", "neto"
- **tiene_comisiones** (boolean): true si tiene comisiones
- **tiene_bonos** (boolean): true si tiene bonos
- **estructura_salarial**: "base + comisiones", "fijo + variable"
- **pide_pretension_salarial** (boolean): true si pide pretension salarial

### BLOQUE 11: BENEFICIOS

- **beneficios_list**: Lista de beneficios (con texto_original)
- **tiene_cobertura_salud** (boolean): prepaga, obra social
- **cobertura_salud_familia** (boolean): si incluye familia
- **tiene_comedor** (boolean): comedor, almuerzo, viandas
- **tiene_capacitacion** (boolean): capacitacion, formacion
- **tiene_crecimiento** (boolean): desarrollo profesional, carrera
- **vehiculo_provisto** (boolean): auto, moto de la empresa

### BLOQUE 13: LICENCIAS Y PERMISOS

- **licencia_conducir** (boolean): true si requiere licencia
- **licencia_conducir_excluyente** (boolean): true si es excluyente
- **tipo_licencia**: "A", "B", "C", "D", "E", "profesional"
- **licencia_autoelevador** (boolean): autoelevador, montacargas
- **matricula_profesional** (boolean): requiere matricula
- **matricula_tipo**: "Contador", "Ingeniero", "Abogado"

### BLOQUE 14: CALIDAD Y FLAGS

- **tipo_oferta**: "demanda_real" (completa), "motivacional" (generica), "titulo_only" (solo titulo)
- **calidad_texto**: "alta", "media", "baja"
- **tiene_requisitos_discriminatorios** (boolean): discrimina por edad, sexo
- **tipo_discriminacion_list**: ["edad", "sexo", "nacionalidad"]
- **requisito_sexo**: "Masculino", "Femenino" si discrimina
- **requisito_edad_min** (int): edad minima si discrimina
- **requisito_edad_max** (int): edad maxima si discrimina
- **titulo_normalizado**: Titulo sin genero. Ej: "Contador/a"
- **tiene_clausula_diversidad** (boolean): mencion de diversidad/inclusion

### BLOQUE 15: CERTIFICACIONES

- **certificaciones_list**: Certificaciones generales (con texto_original)
- **certificaciones_tecnicas_list**: Certs IT. Ej: "AWS Certified", "PMP"
- **certificaciones_seguridad_list**: Certs seguridad. Ej: "Trabajo en Alturas"

### BLOQUE 16: CONDICIONES ESPECIALES

- **trabajo_en_altura** (boolean): trabajo en altura
- **trabajo_exterior** (boolean): trabajo al aire libre
- **trabajo_nocturno** (boolean): horario nocturno
- **trabajo_turnos_rotativos** (boolean): turnos rotativos
- **trabajo_fines_semana** (boolean): sabados, domingos
- **requiere_esfuerzo_fisico** (boolean): carga fisica
- **ambiente_trabajo**: "oficina", "deposito", "campo", "obra"

## EJEMPLO COMPLETO

Texto: "Importante empresa de retail busca Jefe de Ventas Senior para sucursal Pilar.
Requisitos: 5 anos experiencia en ventas retail, secundario completo, licencia B excluyente.
Funciones: Supervisar equipo de 10 vendedores, control de stock, reportar a gerencia.
Beneficios: Prepaga familiar, auto empresa, bonus trimestral.
Horario: Lunes a Viernes 9 a 18hs, sabados rotativos."

Respuesta:
```json
{{
  "empresa": {{
    "sector_empresa": "Retail/Comercio",
    "rubro_empresa": null,
    "empresa_tamanio": null,
    "es_tercerizado": false,
    "cliente_final": null
  }},
  "ubicacion": {{
    "provincia": "Buenos Aires",
    "localidad": "Pilar",
    "modalidad": "presencial",
    "requiere_viajar": null,
    "frecuencia_viaje": null,
    "requiere_movilidad_propia": null,
    "zona_residencia_req": null
  }},
  "experiencia": {{
    "experiencia_min_anios": 5,
    "experiencia_max_anios": null,
    "experiencia_texto": "5 anos experiencia en ventas retail",
    "experiencia_nivel_previo": null,
    "experiencia_sector": "retail",
    "experiencia_areas_list": [{{"valor": "ventas retail", "texto_original": "experiencia en ventas retail"}}],
    "experiencia_excluyente": null
  }},
  "educacion": {{
    "nivel_educativo": "secundario",
    "nivel_educativo_excluyente": true,
    "titulo_requerido": null,
    "carrera_especifica": null,
    "orientacion_estudios": null,
    "acepta_estudiantes_avanzados": null,
    "estudios_valorados_list": []
  }},
  "skills": {{
    "skills_tecnicas_list": [],
    "soft_skills_list": [],
    "perfil_actitudinal_list": [],
    "conocimientos_especificos_list": [],
    "herramientas_list": [],
    "tecnologias_list": [],
    "marcas_especificas_list": [],
    "conocimiento_excluyente_list": []
  }},
  "idiomas": {{
    "idioma_principal": null,
    "idioma_nivel": null,
    "idioma_excluyente": null,
    "idiomas_adicionales_list": []
  }},
  "rol": {{
    "mision_rol": "Supervisar equipo de vendedores en sucursal",
    "tareas_explicitas_list": [
      {{"valor": "control de stock", "texto_original": "control de stock"}},
      {{"valor": "reportar a gerencia", "texto_original": "reportar a gerencia"}}
    ],
    "tareas_inferidas_list": [],
    "producto_servicio": null,
    "tiene_gente_cargo": true,
    "tipo_equipo": "vendedores",
    "interactua_con_externos_list": []
  }},
  "condiciones": {{
    "area_funcional": "Ventas/Comercial",
    "nivel_seniority": "lead",
    "jornada_laboral": "full-time",
    "tipo_contrato": null,
    "horario_especifico": "Lunes a Viernes 9 a 18hs, sabados rotativos",
    "dias_trabajo_list": ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado"],
    "hora_entrada": "09:00",
    "hora_salida": "18:00"
  }},
  "compensacion": {{
    "salario_min": null,
    "salario_max": null,
    "moneda": null,
    "salario_periodo": null,
    "salario_neto": null,
    "tiene_comisiones": null,
    "tiene_bonos": true,
    "estructura_salarial": null,
    "pide_pretension_salarial": null
  }},
  "beneficios": {{
    "beneficios_list": [
      {{"valor": "Prepaga familiar", "texto_original": "Prepaga familiar"}},
      {{"valor": "auto empresa", "texto_original": "auto empresa"}},
      {{"valor": "bonus trimestral", "texto_original": "bonus trimestral"}}
    ],
    "tiene_cobertura_salud": true,
    "cobertura_salud_familia": true,
    "tiene_comedor": null,
    "tiene_capacitacion": null,
    "tiene_crecimiento": null,
    "vehiculo_provisto": true
  }},
  "licencias": {{
    "licencia_conducir": true,
    "licencia_conducir_excluyente": true,
    "tipo_licencia": "B",
    "licencia_autoelevador": null,
    "matricula_profesional": null,
    "matricula_tipo": null
  }},
  "calidad": {{
    "tipo_oferta": "demanda_real",
    "calidad_texto": "alta",
    "tiene_requisitos_discriminatorios": false,
    "tipo_discriminacion_list": [],
    "requisito_sexo": null,
    "requisito_edad_min": null,
    "requisito_edad_max": null,
    "titulo_normalizado": "Jefe/a de Ventas",
    "tiene_clausula_diversidad": null
  }},
  "certificaciones": {{
    "certificaciones_list": [],
    "certificaciones_tecnicas_list": [],
    "certificaciones_seguridad_list": []
  }},
  "condiciones_especiales": {{
    "trabajo_en_altura": null,
    "trabajo_exterior": null,
    "trabajo_nocturno": null,
    "trabajo_turnos_rotativos": true,
    "trabajo_fines_semana": true,
    "requiere_esfuerzo_fisico": null,
    "ambiente_trabajo": null
  }}
}}
```

## FORMATO DE SALIDA

Devuelve SOLO un JSON valido con los 14 bloques.
NO incluyas explicaciones, comentarios ni texto fuera del JSON.

---

## OFERTA A ANALIZAR:

{descripcion}

---

Responde SOLO con el JSON:"""


def build_prompt(descripcion: str) -> str:
    """
    Construye el prompt con la descripcion de la oferta.
    """
    return EXTRACTION_PROMPT_V10.format(descripcion=descripcion)


# Mapeo de bloques LLM a columnas de BD (flatten)
CAMPOS_DB_MAPPING = {
    # Empresa
    "empresa.sector_empresa": "sector_empresa",
    "empresa.rubro_empresa": "rubro_empresa",
    "empresa.empresa_tamanio": "empresa_tamanio",
    "empresa.es_tercerizado": "es_tercerizado",
    "empresa.cliente_final": "cliente_final",
    # Ubicacion
    "ubicacion.provincia": "provincia",
    "ubicacion.localidad": "localidad",
    "ubicacion.modalidad": "modalidad",
    "ubicacion.requiere_viajar": "requiere_viajar",
    "ubicacion.frecuencia_viaje": "frecuencia_viaje",
    "ubicacion.requiere_movilidad_propia": "requiere_movilidad_propia",
    "ubicacion.zona_residencia_req": "zona_residencia_req",
    # Experiencia
    "experiencia.experiencia_min_anios": "experiencia_min_anios",
    "experiencia.experiencia_max_anios": "experiencia_max_anios",
    "experiencia.experiencia_texto": "experiencia_texto",
    "experiencia.experiencia_nivel_previo": "experiencia_nivel_previo",
    "experiencia.experiencia_sector": "experiencia_sector",
    "experiencia.experiencia_areas_list": "experiencia_areas_list",
    "experiencia.experiencia_excluyente": "experiencia_excluyente",
    # Educacion
    "educacion.nivel_educativo": "nivel_educativo",
    "educacion.nivel_educativo_excluyente": "nivel_educativo_excluyente",
    "educacion.titulo_requerido": "titulo_requerido",
    "educacion.carrera_especifica": "carrera_especifica",
    "educacion.orientacion_estudios": "orientacion_estudios",
    "educacion.acepta_estudiantes_avanzados": "acepta_estudiantes_avanzados",
    "educacion.estudios_valorados_list": "estudios_valorados_list",
    # Skills
    "skills.skills_tecnicas_list": "skills_tecnicas_list",
    "skills.soft_skills_list": "soft_skills_list",
    "skills.perfil_actitudinal_list": "perfil_actitudinal_list",
    "skills.conocimientos_especificos_list": "conocimientos_especificos_list",
    "skills.herramientas_list": "herramientas_list",
    "skills.tecnologias_list": "tecnologias_list",
    "skills.marcas_especificas_list": "marcas_especificas_list",
    "skills.conocimiento_excluyente_list": "conocimiento_excluyente_list",
    # Idiomas
    "idiomas.idioma_principal": "idioma_principal",
    "idiomas.idioma_nivel": "nivel_idioma_principal",
    "idiomas.idioma_excluyente": "idioma_excluyente",
    "idiomas.idiomas_adicionales_list": "idiomas_adicionales_json",
    # Rol
    "rol.mision_rol": "mision_rol",
    "rol.tareas_explicitas_list": "tareas_explicitas",
    "rol.tareas_inferidas_list": "tareas_inferidas",
    "rol.producto_servicio": "producto_servicio",
    "rol.tiene_gente_cargo": "tiene_gente_cargo",
    "rol.tipo_equipo": "tipo_equipo",
    "rol.interactua_con_externos_list": "interactua_con_externos_list",
    # Condiciones
    "condiciones.area_funcional": "area_funcional",
    "condiciones.nivel_seniority": "nivel_seniority",
    "condiciones.jornada_laboral": "jornada_laboral",
    "condiciones.tipo_contrato": "tipo_contrato",
    "condiciones.horario_especifico": "horario_especifico",
    "condiciones.dias_trabajo_list": "dias_trabajo_list",
    "condiciones.hora_entrada": "hora_entrada",
    "condiciones.hora_salida": "hora_salida",
    # Compensacion
    "compensacion.salario_min": "salario_min",
    "compensacion.salario_max": "salario_max",
    "compensacion.moneda": "moneda",
    "compensacion.salario_periodo": "salario_periodo",
    "compensacion.salario_neto": "salario_neto",
    "compensacion.tiene_comisiones": "tiene_comisiones",
    "compensacion.tiene_bonos": "tiene_bonos",
    "compensacion.estructura_salarial": "estructura_salarial",
    "compensacion.pide_pretension_salarial": "pide_pretension_salarial",
    # Beneficios
    "beneficios.beneficios_list": "beneficios_list",
    "beneficios.tiene_cobertura_salud": "tiene_cobertura_salud",
    "beneficios.cobertura_salud_familia": "cobertura_salud_familia",
    "beneficios.tiene_comedor": "tiene_comedor",
    "beneficios.tiene_capacitacion": "tiene_capacitacion",
    "beneficios.tiene_crecimiento": "tiene_crecimiento",
    "beneficios.vehiculo_provisto": "vehiculo_provisto",
    # Licencias
    "licencias.licencia_conducir": "licencia_conducir",
    "licencias.licencia_conducir_excluyente": "licencia_conducir_excluyente",
    "licencias.tipo_licencia": "tipo_licencia",
    "licencias.licencia_autoelevador": "licencia_autoelevador",
    "licencias.matricula_profesional": "matricula_profesional",
    "licencias.matricula_tipo": "matricula_tipo",
    # Calidad
    "calidad.tipo_oferta": "tipo_oferta",
    "calidad.calidad_texto": "calidad_texto",
    "calidad.tiene_requisitos_discriminatorios": "tiene_requisitos_discriminatorios",
    "calidad.tipo_discriminacion_list": "tipo_discriminacion_list",
    "calidad.requisito_sexo": "requisito_sexo",
    "calidad.requisito_edad_min": "requisito_edad_min",
    "calidad.requisito_edad_max": "requisito_edad_max",
    "calidad.titulo_normalizado": "titulo_normalizado",
    "calidad.tiene_clausula_diversidad": "tiene_clausula_diversidad",
    # Certificaciones
    "certificaciones.certificaciones_list": "certificaciones_list",
    "certificaciones.certificaciones_tecnicas_list": "certificaciones_tecnicas_list",
    "certificaciones.certificaciones_seguridad_list": "certificaciones_seguridad_list",
    # Condiciones especiales
    "condiciones_especiales.trabajo_en_altura": "trabajo_en_altura",
    "condiciones_especiales.trabajo_exterior": "trabajo_exterior",
    "condiciones_especiales.trabajo_nocturno": "trabajo_nocturno",
    "condiciones_especiales.trabajo_turnos_rotativos": "trabajo_turnos_rotativos",
    "condiciones_especiales.trabajo_fines_semana": "trabajo_fines_semana",
    "condiciones_especiales.requiere_esfuerzo_fisico": "requiere_esfuerzo_fisico",
    "condiciones_especiales.ambiente_trabajo": "ambiente_trabajo",
}


def flatten_response(llm_response: dict) -> dict:
    """
    Aplana la respuesta del LLM a formato plano para la BD.

    Args:
        llm_response: Respuesta estructurada del LLM con bloques

    Returns:
        Dict plano con columnas de BD
    """
    flat = {}

    for llm_path, db_column in CAMPOS_DB_MAPPING.items():
        parts = llm_path.split(".")

        # Navegar al valor
        value = llm_response
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break

        flat[db_column] = value

    return flat


# Lista de todos los campos de BD que este prompt genera
CAMPOS_BD = list(set(CAMPOS_DB_MAPPING.values()))


if __name__ == "__main__":
    descripcion_test = """
    Importante empresa de retail busca Jefe de Ventas Senior para sucursal Pilar.

    Requisitos:
    - 5 anos experiencia en ventas retail
    - Secundario completo
    - Licencia de conducir B excluyente

    Funciones:
    - Supervisar equipo de 10 vendedores
    - Control de stock
    - Reportar a gerencia

    Beneficios:
    - Prepaga familiar
    - Auto de la empresa
    - Bonus trimestral

    Horario: Lunes a Viernes 9 a 18hs, sabados rotativos.
    """

    prompt = build_prompt(descripcion_test)
    print("=== PROMPT v10 (Schema v5 Completo) ===")
    print(f"Campos BD: {len(CAMPOS_BD)}")
    print(f"Prompt length: {len(prompt)} chars")
    print("\n--- Preview (primeros 2000 chars) ---")
    print(prompt[:2000] + "...")
