# Esquema NLP v5 - Especificación Completa

**Fecha:** 2025-12-06
**Versión:** 5.0
**Estado:** En diseño

---

## Resumen

Este documento define los ~130 campos que el pipeline NLP debe extraer de las ofertas laborales, organizados en 16 bloques temáticos.

---

## Bloque 1: Metadata del Portal

Campos que vienen del scraping, no requieren NLP.

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| id | string | "1118027662" | scraping |
| titulo | string | "Vendedor Senior B2B" | scraping |
| descripcion | string | "Buscamos vendedor..." | scraping |
| url_fuente | string | "https://bumeran.com/..." | scraping |
| portal | string | "bumeran" | scraping |
| fecha_publicacion | date | "2025-12-05" | scraping |
| fecha_actualizacion | date | "2025-12-06" | scraping |
| tipo_postulacion | string | "rápida" / "normal" | scraping |
| cantidad_vacantes | string | "1" / "Múltiples" | scraping |

---

## Bloque 2: Empresa

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| empresa_nombre | string | "La Anónima" | scraping |
| empresa_confidencial | boolean | false | scraping |
| empresa_rating | float | 4.7 | scraping |
| empresa_tamaño | string | "9000 personas" | NLP |
| empresa_antiguedad | string | "117 años" | NLP |
| sector_empresa | string | "retail", "automotriz" | NLP |
| rubro_empresa | string | "supermercados" | NLP |
| certificaciones | [string] | ["Empresa B", "ISO 9001"] | NLP |
| es_tercerizado | boolean | true | NLP |
| cliente_final | string | "compañía telecomunicaciones" | NLP |

**Notas:**
- `es_tercerizado`: Detectar cuando empresa contratante ≠ donde trabaja
- Ejemplo: "Experis" contrata, pero trabaja en "Telco"

---

## Bloque 3: Ubicación y Movilidad

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| ubicacion_principal | string | "CABA, Buenos Aires" | scraping |
| provincia | string | "Buenos Aires" | NLP |
| localidad | string | "Villa Lynch" | NLP |
| tipo_lugar | string | "Depósito", "Oficina" | NLP |
| zonas_cobertura | [string] | ["San Isidro", "Acasusso"] | NLP |
| modalidad | string | "presencial" / "remoto" / "híbrido" | scraping/NLP |
| requiere_viajar | boolean | true | NLP |
| frecuencia_viaje | string | "frecuente", "ocasional" | NLP |
| radio_viaje_km | int | 400 | NLP |
| requiere_movilidad_propia | boolean | true | NLP |
| zona_residencia_req | string | "cerca de Esteban Echeverría" | NLP |
| acepta_relocacion | boolean | true | NLP |

---

## Bloque 4: Experiencia

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| experiencia_min_anios | int | 3 | NLP |
| experiencia_max_anios | int | 5 | NLP |
| experiencia_texto | string | "amplia experiencia" | NLP (original) |
| experiencia_descripcion | string | "en venta de planes de ahorro" | NLP |
| experiencia_nivel_previo | string | "Analista Sr", "Coordinador" | NLP |
| experiencia_sector | string | "industrial", "servicios" | NLP |
| experiencia_areas | [string] | ["CCTV", "alarmas"] | NLP |
| experiencia_excluyente | boolean | true | NLP |
| experiencia_valorada | boolean | false | NLP |

**Conversión cualitativo → cuantitativo:**

| Texto | Años | Confianza |
|-------|------|-----------|
| "sin experiencia" | 0 | alta |
| "poca experiencia" | 0-1 | media |
| "experiencia" | 1-2 | baja |
| "experiencia previa" | 1-2 | baja |
| "experiencia comprobable" | 2+ | media |
| "amplia experiencia" | 3+ | media |
| "sólida experiencia" | 3-5 | media |
| "vasta experiencia" | 5+ | media |
| "extensa trayectoria" | 7+ | media |

---

## Bloque 5: Educación

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| nivel_educativo | string | "secundario" / "universitario" | NLP |
| nivel_educativo_excluyente | boolean | true | NLP |
| titulo_requerido | string | "Lic. en SHyMA" | NLP |
| carrera_especifica | string | "Contador Público" | NLP |
| orientacion_estudios | string | "técnica / Industrial" | NLP |
| estado_titulo | string | "recibido" / "en curso" / "próximo" | NLP |
| acepta_estudiantes_avanzados | boolean | true | NLP |
| estudios_valorados | [string] | ["MBA", "posgrado"] | NLP |

---

## Bloque 6: Skills y Conocimientos

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| tech_skills | [string] | ["SAP", "Excel avanzado"] | NLP |
| soft_skills | [string] | ["comunicación", "negociación"] | NLP |
| perfil_actitudinal | [string] | ["proactivo", "autónomo"] | NLP |
| conocimientos_especificos | [string] | ["procedimientos seguridad"] | NLP |
| herramientas | [string] | ["Excel", "SAP", "AutoCAD"] | NLP |
| sistemas | [string] | ["sistema gestión interno"] | NLP |
| tecnologias | [string] | ["3G", "4G", "5G", "CCTV IP"] | NLP |
| marcas_especificas | [string] | ["Hikvision", "Dahua"] | NLP |
| nivel_herramienta | object | {"Excel": "intermedio"} | NLP |
| conocimiento_excluyente | [string] | ["Bejerman"] | NLP |

**Nota:** Diferenciar soft_skills (habilidades medibles) de perfil_actitudinal (rasgos de personalidad).

---

## Bloque 7: Idiomas

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| idioma_principal | string | "inglés" | NLP |
| idioma_nivel | string | "intermedio" / "avanzado" | NLP |
| idioma_excluyente | boolean | true | NLP |
| idiomas_adicionales | [object] | [{"idioma": "portugués", "nivel": "básico"}] | NLP |

---

## Bloque 8: Rol y Tareas

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| mision_rol | string | "liderar la gestión de SHyMA..." | NLP |
| tareas_explicitas | [string] | ["liquidación impuestos"] | NLP |
| tareas_inferidas | [string] | ["contabilidad general"] | NLP |
| tareas | [string] | (unión de explícitas + inferidas) | calculado |
| producto_servicio | string | "Plan de Ahorro" | NLP |
| tiene_gente_cargo | boolean | true | NLP |
| tipo_equipo | string | "cuadrillas" | NLP |
| interactua_con_externos | [string] | ["Municipio", "organismos"] | NLP |

---

## Bloque 9: Condiciones Laborales

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| jornada_laboral | string | "full-time" / "part-time" | scraping/NLP |
| tipo_contrato | string | "indeterminado" / "temporal" | scraping/NLP |
| area_funcional | string | "Ventas", "Contabilidad" | scraping |
| nivel_seniority | string | "junior" / "senior" / "jefe" | scraping/NLP |
| horario_especifico | string | "Lunes a Viernes 9am - 6pm" | NLP |
| dias_trabajo | [string] | ["lunes", "martes", ..., "viernes"] | NLP |
| hora_entrada | string | "09:00" | NLP |
| hora_salida | string | "18:00" | NLP |

**Conversión seniority (si no viene en metadata):**

| Señales | Seniority | Confianza |
|---------|-----------|-----------|
| "sin experiencia", "1er empleo" | trainee/junior | alta |
| "Jr", "junior" en título | junior | alta |
| "experiencia" sin calificar | semi-senior | baja |
| "amplia experiencia" | semi-senior | media |
| "sólida experiencia" | senior | media |
| "Sr", "senior" en título | senior | alta |
| "Jefe", "Coord" en título | supervisor | alta |
| "Gerente", "Director" | gerente | alta |

---

## Bloque 10: Compensación

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| salario_min | int | 150000 | NLP |
| salario_max | int | 180000 | NLP |
| salario_moneda | string | "ARS" / "USD" | NLP |
| salario_periodo | string | "mensual" / "anual" | NLP |
| salario_neto | boolean | true (si dice "en mano") | NLP |
| tiene_salario_base | boolean | true | NLP |
| tiene_comisiones | boolean | true | NLP |
| tiene_bonos | boolean | true | NLP |
| estructura_salarial | string | "base + comisiones + bonos" | NLP |
| bonos | [object] | [{"tipo": "productividad", "detalle": "por sitio"}] | NLP |
| pide_pretension_salarial | boolean | true | NLP |
| pretension_formato | string | "en mano" | NLP |

---

## Bloque 11: Beneficios

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| beneficios | [string] | ["prepaga", "comedor"] | NLP |
| tiene_cobertura_salud | boolean | true | NLP |
| cobertura_salud_familia | boolean | true | NLP |
| tiene_comedor | boolean | true | NLP |
| tiene_capacitacion | boolean | true | NLP |
| tiene_crecimiento | boolean | true | NLP |
| tiene_programa_asistencia | boolean | true | NLP |
| tiene_descuentos | boolean | true | NLP |
| descuentos_educacion | [object] | [{"institucion": "Open English", "porcentaje": 75}] | NLP |
| descuentos_gimnasio | [object] | [{"institucion": "Megatlon", "porcentaje": 50}] | NLP |
| vehiculo_provisto | boolean | false | NLP |
| otros_beneficios | [string] | ["Cuponstar", "supermercados"] | NLP |

---

## Bloque 12: Metadatos NLP

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| nlp_version | string | "v8.0" | sistema |
| nlp_timestamp | datetime | "2025-12-05T08:15:00Z" | sistema |
| nlp_score | int | 12 | calculado |
| nlp_score_max | int | 18 | calculado |
| tipo_oferta | string | "demanda_real" / "motivacional" / "titulo_only" | NLP |
| calidad_texto | string | "alta" / "media" / "baja" | NLP |
| largo_descripcion | int | 1500 | calculado |
| pasa_a_matching | boolean | true | calculado |
| campos_con_fuente | object | (ver sección trazabilidad) | sistema |

---

## Bloque 13: Licencias y Permisos

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| licencia_conducir | boolean | true | NLP |
| licencia_conducir_excluyente | boolean | true | NLP |
| tipo_licencia | string | "B" / "profesional" | NLP |
| licencia_autoelevador | boolean | false | NLP |
| otras_licencias | [string] | ["montacargas"] | NLP |
| matricula_profesional | boolean | true | NLP |
| matricula_tipo | string | "Contador", "Arquitecto" | NLP |

---

## Bloque 14: Calidad y Flags

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| tiene_errores_tipeo | boolean | true | NLP |
| errores_detectados | [string] | ["EMPRE ADE"] | NLP |
| calidad_redaccion | string | "alta" / "media" / "baja" | NLP |
| titulo_repetido_en_descripcion | boolean | true | NLP |
| tiene_requisitos_discriminatorios | boolean | true | NLP |
| tipo_discriminacion | [string] | ["edad", "sexo"] | NLP |
| requisito_sexo | string | "Masculino" | NLP |
| requisito_edad_min | int | 30 | NLP |
| requisito_edad_max | int | 45 | NLP |
| titulo_genero_especifico | boolean | true | NLP |
| titulo_normalizado | string | "Contador/a" | NLP |
| es_republica | boolean | false | NLP |
| tiene_clausula_diversidad | boolean | true | NLP |

---

## Bloque 15: Certificaciones

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| certificaciones_requeridas | [object] | [{"nombre": "Trabajo en Alturas", "vigencia_max_meses": 6, "excluyente": true}] | NLP |
| certificaciones_deseables | [string] | ["ISDP Huawei"] | NLP |
| certificaciones_tecnicas | [string] | ["Cisco", "AWS"] | NLP |
| certificaciones_seguridad | [string] | ["Alturas", "Espacios Confinados"] | NLP |

---

## Bloque 16: Condiciones Especiales de Trabajo

| Campo | Tipo | Ejemplo | Fuente |
|-------|------|---------|--------|
| trabajo_en_altura | boolean | true | NLP |
| altura_metros | int | 60 | NLP |
| trabajo_espacios_confinados | boolean | false | NLP |
| trabajo_exterior | boolean | true | NLP |
| trabajo_nocturno | boolean | false | NLP |
| trabajo_turnos_rotativos | boolean | false | NLP |
| trabajo_fines_semana | boolean | false | NLP |
| trabajo_feriados | boolean | false | NLP |
| trabajo_riesgo | boolean | true | NLP |
| requiere_esfuerzo_fisico | boolean | true | NLP |
| carga_peso_kg | int | 25 | NLP |
| ambiente_trabajo | string | "depósito", "oficina", "campo" | NLP |

---

## Trazabilidad de Fuentes

Para cada campo que puede ser inferido, guardar metadata:

```python
{
    "nivel_educativo": {
        "valor": "universitario",
        "fuente": "inferido",  # "explicito" | "inferido" | "metadata"
        "confianza": "alta",   # "alta" | "media" | "baja"
        "texto_original": null,
        "razon": "Título profesional regulado (Contador)"
    },
    
    "experiencia_min_anios": {
        "valor": 3,
        "fuente": "inferido",
        "confianza": "media",
        "texto_original": "amplia experiencia",
        "razon": "'amplia' interpretado como 3+ años"
    },
    
    "tareas": {
        "valor": ["liquidación impuestos", "armado Balances", "contabilidad general"],
        "explicitas": ["liquidación impuestos", "armado Balances"],
        "inferidas": ["contabilidad general"]
    }
}
```

---

## Campos Críticos para Matching

Ordenados por impacto en la clasificación ESCO:

| Prioridad | Campo | Impacto |
|-----------|-------|---------|
| ★★★★★ | titulo | Determina ocupación |
| ★★★★★ | tareas[] | Confirma ocupación |
| ★★★★★ | area_funcional | Contexto sector |
| ★★★★★ | nivel_seniority | Nivel jerárquico |
| ★★★★☆ | tiene_gente_cargo | Jefe vs Individual |
| ★★★★☆ | titulo_requerido | Ocupación específica |
| ★★★★☆ | producto_servicio | Qué vende/produce |
| ★★★☆☆ | tech_skills[] | Skills técnicas |
| ★★★☆☆ | tecnologias[] | Stack técnico |
| ★★★☆☆ | marcas_especificas[] | Conocimiento específico |
| ★★★☆☆ | sector_empresa | Industria |
| ★★★☆☆ | experiencia_nivel_previo | Nivel anterior |
| ★★☆☆☆ | conocimientos_especificos[] | Dominio técnico |
| ★★☆☆☆ | orientacion_estudios | Formación |
| ★☆☆☆☆ | perfil_actitudinal[] | Contexto |

---

## Priorización de Implementación

### Fase 1: Críticos (impactan matching)

- [ ] tareas[] (explicitas + inferidas)
- [ ] area_funcional
- [ ] nivel_seniority
- [ ] titulo_requerido
- [ ] tecnologias[] / marcas_especificas[]
- [ ] tiene_gente_cargo

### Fase 2: Importantes

- [ ] experiencia_nivel_previo
- [ ] experiencia_areas[]
- [ ] conocimientos_especificos[]
- [ ] producto_servicio
- [ ] licencia_conducir

### Fase 3: Calidad y Flags

- [ ] tiene_requisitos_discriminatorios
- [ ] calidad_redaccion
- [ ] tipo_oferta
- [ ] certificaciones_requeridas[]

### Fase 4: Contexto/Info

- [ ] beneficios detallados
- [ ] estructura_salarial
- [ ] empresa_tamaño
- [ ] es_tercerizado
- [ ] condiciones especiales trabajo

---

*Documento generado: 2025-12-06*
