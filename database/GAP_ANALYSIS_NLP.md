# Gap Analysis: NLP Schema v5 vs Implementación Actual

**Fecha:** 2025-12-09 20:41
**Total registros en ofertas_nlp:** 5,479
**Columnas en BD:** 28

---

## Resumen por Bloque

| # | Bloque | Campos Diseñados | Implementados | % | Con Datos |
|---|--------|------------------|---------------|---|-----------|
| 1 | Metadata del Portal | 9 | 0 | 0% | 0 |
| 2 | Empresa | 10 | 0 | 0% | 0 |
| 3 | Ubicación y Movilidad | 12 | 0 | 0% | 0 |
| 4 | Experiencia | 9 | 2 | 22% | 2 |
| 5 | Educación | 8 | 2 | 25% | 2 |
| 6 | Skills y Conocimientos | 10 | 2 | 20% | 2 |
| 7 | Idiomas | 4 | 1 | 25% | 1 |
| 8 | Rol y Tareas | 8 | 0 | 0% | 0 |
| 9 | Condiciones Laborales | 8 | 1 | 12% | 1 |
| 10 | Compensación | 12 | 2 | 17% | 0 |
| 11 | Beneficios | 12 | 1 | 8% | 0 |
| 12 | Metadatos NLP | 9 | 1 | 11% | 1 |
| 13 | Licencias y Permisos | 7 | 0 | 0% | 0 |
| 14 | Calidad y Flags | 13 | 0 | 0% | 0 |
| 15 | Certificaciones | 4 | 0 | 0% | 0 |
| 16 | Condiciones Especiales de Trabajo | 12 | 0 | 0% | 0 |

**TOTAL:** 12/147 campos implementados (8.2%)

---

## Detalle por Bloque

### Bloque 1: Metadata del Portal

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| id | ✗ | - | - | string | scraping |
| titulo | ✗ | - | - | string | scraping |
| descripcion | ✗ | - | - | string | scraping |
| url_fuente | ✗ | - | - | string | scraping |
| portal | ✗ | - | - | string | scraping |
| fecha_publicacion | ✗ | - | - | date | scraping |
| fecha_actualizacion | ✗ | - | - | date | scraping |
| tipo_postulacion | ✗ | - | - | string | scraping |
| cantidad_vacantes | ✗ | - | - | string | scraping |

### Bloque 2: Empresa

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| empresa_nombre | ✗ | - | - | string | scraping |
| empresa_confidencial | ✗ | - | - | boolean | scraping |
| empresa_rating | ✗ | - | - | float | scraping |
| empresa_tamaño | ✗ | - | - | string | NLP |
| empresa_antiguedad | ✗ | - | - | string | NLP |
| sector_empresa | ✗ | - | - | string | NLP |
| rubro_empresa | ✗ | - | - | string | NLP |
| certificaciones | ✗ | - | - | [string] | NLP |
| es_tercerizado | ✗ | - | - | boolean | NLP |
| cliente_final | ✗ | - | - | string | NLP |

### Bloque 3: Ubicación y Movilidad

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| ubicacion_principal | ✗ | - | - | string | scraping |
| provincia | ✗ | - | - | string | NLP |
| localidad | ✗ | - | - | string | NLP |
| tipo_lugar | ✗ | - | - | string | NLP |
| zonas_cobertura | ✗ | - | - | [string] | NLP |
| modalidad | ✗ | - | - | string | scraping/NLP |
| requiere_viajar | ✗ | - | - | boolean | NLP |
| frecuencia_viaje | ✗ | - | - | string | NLP |
| radio_viaje_km | ✗ | - | - | int | NLP |
| requiere_movilidad_propia | ✗ | - | - | boolean | NLP |
| zona_residencia_req | ✗ | - | - | string | NLP |
| acepta_relocacion | ✗ | - | - | boolean | NLP |

### Bloque 4: Experiencia

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| experiencia_min_anios | ✓ | experiencia_min_anios | 83.2% | int | NLP |
| experiencia_max_anios | ✓ | experiencia_max_anios | 7.7% | int | NLP |
| experiencia_texto | ✗ | - | - | string | NLP (original) |
| experiencia_descripcion | ✗ | - | - | string | NLP |
| experiencia_nivel_previo | ✗ | - | - | string | NLP |
| experiencia_sector | ✗ | - | - | string | NLP |
| experiencia_areas | ✗ | - | - | [string] | NLP |
| experiencia_excluyente | ✗ | - | - | boolean | NLP |
| experiencia_valorada | ✗ | - | - | boolean | NLP |

### Bloque 5: Educación

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| nivel_educativo | ✓ | nivel_educativo | 99.9% | string | NLP |
| nivel_educativo_excluyente | ✗ | - | - | boolean | NLP |
| titulo_requerido | ✗ | - | - | string | NLP |
| carrera_especifica | ✓ | carrera_especifica | 8.2% | string | NLP |
| orientacion_estudios | ✗ | - | - | string | NLP |
| estado_titulo | ✗ | - | - | string | NLP |
| acepta_estudiantes_avanzados | ✗ | - | - | boolean | NLP |
| estudios_valorados | ✗ | - | - | [string] | NLP |

### Bloque 6: Skills y Conocimientos

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| tech_skills | ✓ | skills_tecnicas_list | 95.4% | [string] | NLP |
| soft_skills | ✓ | soft_skills_list | 100.0% | [string] | NLP |
| perfil_actitudinal | ✗ | - | - | [string] | NLP |
| conocimientos_especificos | ✗ | - | - | [string] | NLP |
| herramientas | ✗ | - | - | [string] | NLP |
| sistemas | ✗ | - | - | [string] | NLP |
| tecnologias | ✗ | - | - | [string] | NLP |
| marcas_especificas | ✗ | - | - | [string] | NLP |
| nivel_herramienta | ✗ | - | - | object | NLP |
| conocimiento_excluyente | ✗ | - | - | [string] | NLP |

### Bloque 7: Idiomas

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| idioma_principal | ✓ | idioma_principal | 100.0% | string | NLP |
| idioma_nivel | ✗ | - | - | string | NLP |
| idioma_excluyente | ✗ | - | - | boolean | NLP |
| idiomas_adicionales | ✗ | - | - | [object] | NLP |

### Bloque 8: Rol y Tareas

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| mision_rol | ✗ | - | - | string | NLP |
| tareas_explicitas | ✗ | - | - | [string] | NLP |
| tareas_inferidas | ✗ | - | - | [string] | NLP |
| tareas | ✗ | - | - | [string] | calculado |
| producto_servicio | ✗ | - | - | string | NLP |
| tiene_gente_cargo | ✗ | - | - | boolean | NLP |
| tipo_equipo | ✗ | - | - | string | NLP |
| interactua_con_externos | ✗ | - | - | [string] | NLP |

### Bloque 9: Condiciones Laborales

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| jornada_laboral | ✓ | jornada_laboral | 100.0% | string | scraping/NLP |
| tipo_contrato | ✗ | - | - | string | scraping/NLP |
| area_funcional | ✗ | - | - | string | scraping |
| nivel_seniority | ✗ | - | - | string | scraping/NLP |
| horario_especifico | ✗ | - | - | string | NLP |
| dias_trabajo | ✗ | - | - | [string] | NLP |
| hora_entrada | ✗ | - | - | string | NLP |
| hora_salida | ✗ | - | - | string | NLP |

### Bloque 10: Compensación

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| salario_min | ✓ | salario_min | 0.0% | int | NLP |
| salario_max | ✓ | salario_max | 0.0% | int | NLP |
| salario_moneda | ✗ | - | - | string | NLP |
| salario_periodo | ✗ | - | - | string | NLP |
| salario_neto | ✗ | - | - | boolean | NLP |
| tiene_salario_base | ✗ | - | - | boolean | NLP |
| tiene_comisiones | ✗ | - | - | boolean | NLP |
| tiene_bonos | ✗ | - | - | boolean | NLP |
| estructura_salarial | ✗ | - | - | string | NLP |
| bonos | ✗ | - | - | [object] | NLP |
| pide_pretension_salarial | ✗ | - | - | boolean | NLP |
| pretension_formato | ✗ | - | - | string | NLP |

### Bloque 11: Beneficios

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| beneficios | ✓ | beneficios_list | 0.0% | [string] | NLP |
| tiene_cobertura_salud | ✗ | - | - | boolean | NLP |
| cobertura_salud_familia | ✗ | - | - | boolean | NLP |
| tiene_comedor | ✗ | - | - | boolean | NLP |
| tiene_capacitacion | ✗ | - | - | boolean | NLP |
| tiene_crecimiento | ✗ | - | - | boolean | NLP |
| tiene_programa_asistencia | ✗ | - | - | boolean | NLP |
| tiene_descuentos | ✗ | - | - | boolean | NLP |
| descuentos_educacion | ✗ | - | - | [object] | NLP |
| descuentos_gimnasio | ✗ | - | - | [object] | NLP |
| vehiculo_provisto | ✗ | - | - | boolean | NLP |
| otros_beneficios | ✗ | - | - | [string] | NLP |

### Bloque 12: Metadatos NLP

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| nlp_version | ✓ | nlp_version | 100.0% | string | sistema |
| nlp_timestamp | ✗ | - | - | datetime | sistema |
| nlp_score | ✗ | - | - | int | calculado |
| nlp_score_max | ✗ | - | - | int | calculado |
| tipo_oferta | ✗ | - | - | string | NLP |
| calidad_texto | ✗ | - | - | string | NLP |
| largo_descripcion | ✗ | - | - | int | calculado |
| pasa_a_matching | ✗ | - | - | boolean | calculado |
| campos_con_fuente | ✗ | - | - | object | sistema |

### Bloque 13: Licencias y Permisos

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| licencia_conducir | ✗ | - | - | boolean | NLP |
| licencia_conducir_excluyente | ✗ | - | - | boolean | NLP |
| tipo_licencia | ✗ | - | - | string | NLP |
| licencia_autoelevador | ✗ | - | - | boolean | NLP |
| otras_licencias | ✗ | - | - | [string] | NLP |
| matricula_profesional | ✗ | - | - | boolean | NLP |
| matricula_tipo | ✗ | - | - | string | NLP |

### Bloque 14: Calidad y Flags

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| tiene_errores_tipeo | ✗ | - | - | boolean | NLP |
| errores_detectados | ✗ | - | - | [string] | NLP |
| calidad_redaccion | ✗ | - | - | string | NLP |
| titulo_repetido_en_descripcion | ✗ | - | - | boolean | NLP |
| tiene_requisitos_discriminatorios | ✗ | - | - | boolean | NLP |
| tipo_discriminacion | ✗ | - | - | [string] | NLP |
| requisito_sexo | ✗ | - | - | string | NLP |
| requisito_edad_min | ✗ | - | - | int | NLP |
| requisito_edad_max | ✗ | - | - | int | NLP |
| titulo_genero_especifico | ✗ | - | - | boolean | NLP |
| titulo_normalizado | ✗ | - | - | string | NLP |
| es_republica | ✗ | - | - | boolean | NLP |
| tiene_clausula_diversidad | ✗ | - | - | boolean | NLP |

### Bloque 15: Certificaciones

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| certificaciones_requeridas | ✗ | - | - | [object] | NLP |
| certificaciones_deseables | ✗ | - | - | [string] | NLP |
| certificaciones_tecnicas | ✗ | - | - | [string] | NLP |
| certificaciones_seguridad | ✗ | - | - | [string] | NLP |

### Bloque 16: Condiciones Especiales de Trabajo

| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |
|--------------|-------|---------|-----------|------|--------|
| trabajo_en_altura | ✗ | - | - | boolean | NLP |
| altura_metros | ✗ | - | - | int | NLP |
| trabajo_espacios_confinados | ✗ | - | - | boolean | NLP |
| trabajo_exterior | ✗ | - | - | boolean | NLP |
| trabajo_nocturno | ✗ | - | - | boolean | NLP |
| trabajo_turnos_rotativos | ✗ | - | - | boolean | NLP |
| trabajo_fines_semana | ✗ | - | - | boolean | NLP |
| trabajo_feriados | ✗ | - | - | boolean | NLP |
| trabajo_riesgo | ✗ | - | - | boolean | NLP |
| requiere_esfuerzo_fisico | ✗ | - | - | boolean | NLP |
| carga_peso_kg | ✗ | - | - | int | NLP |
| ambiente_trabajo | ✗ | - | - | string | NLP |

---

## Campos Críticos para Matching

| Prioridad | Campo | Estado | Cobertura | Impacto |
|-----------|-------|--------|-----------|---------|
| ★★★★★ | titulo | ✗ FALTA | - | Determina ocupación |
| ★★★★★ | tareas | ✗ FALTA | - | Confirma ocupación |
| ★★★★★ | area_funcional | ✗ FALTA | - | Contexto sector |
| ★★★★★ | nivel_seniority | ✗ FALTA | - | Nivel jerárquico |
| ★★★★☆ | tiene_gente_cargo | ✗ FALTA | - | Jefe vs Individual |
| ★★★★☆ | titulo_requerido | ✗ FALTA | - | Ocupación específica |
| ★★★★☆ | producto_servicio | ✗ FALTA | - | Qué vende/produce |
| ★★★☆☆ | tech_skills | ✓ Implementado | 95.4% | Skills técnicas |
| ★★★☆☆ | tecnologias | ✗ FALTA | - | Stack técnico |
| ★★★☆☆ | marcas_especificas | ✗ FALTA | - | Conocimiento específico |
| ★★★☆☆ | sector_empresa | ✗ FALTA | - | Industria |
| ★★★☆☆ | experiencia_nivel_previo | ✗ FALTA | - | Nivel anterior |
| ★★☆☆☆ | conocimientos_especificos | ✗ FALTA | - | Dominio técnico |
| ★★☆☆☆ | orientacion_estudios | ✗ FALTA | - | Formación |
| ★☆☆☆☆ | perfil_actitudinal | ✗ FALTA | - | Contexto |

---

## Cobertura de Datos (Campos Existentes)

| Campo | Registros | % del Total |
|-------|-----------|-------------|
| idioma_principal | 5,479 | 100.0% |
| nivel_idioma_principal | 5,479 | 100.0% |
| soft_skills_list | 5,479 | 100.0% |
| jornada_laboral | 5,479 | 100.0% |
| nlp_extraction_timestamp | 5,479 | 100.0% |
| nlp_version | 5,479 | 100.0% |
| nlp_confidence_score | 5,479 | 100.0% |
| nivel_educativo | 5,476 | 99.9% |
| skills_tecnicas_list | 5,228 | 95.4% |
| experiencia_min_anios | 4,558 | 83.2% |
| estado_educativo | 3,420 | 62.4% |
| requisitos_excluyentes_list | 2,041 | 37.3% |
| requisitos_deseables_list | 1,158 | 21.1% |
| carrera_especifica | 448 | 8.2% |
| experiencia_max_anios | 422 | 7.7% |
| horario_flexible | 121 | 2.2% |
| titulo_limpio | 44 | 0.8% |
| experiencia_area | 0 | 0.0% |
| titulo_excluyente | 0 | 0.0% |
| idioma_secundario | 0 | 0.0% |
| nivel_idioma_secundario | 0 | 0.0% |
| niveles_skills_list | 0 | 0.0% |
| certificaciones_list | 0 | 0.0% |
| salario_min | 0 | 0.0% |
| salario_max | 0 | 0.0% |
| moneda | 0 | 0.0% |
| beneficios_list | 0 | 0.0% |

---

## Campos Faltantes Priorizados

### Fase 1: Críticos (impactan matching)

- [ ] `tareas`
- [ ] `area_funcional`
- [ ] `nivel_seniority`
- [ ] `titulo_requerido`
- [ ] `tecnologias`
- [ ] `marcas_especificas`
- [ ] `tiene_gente_cargo`

### Fase 2: Importantes

- [ ] `experiencia_nivel_previo`
- [ ] `experiencia_areas`
- [ ] `conocimientos_especificos`
- [ ] `producto_servicio`
- [ ] `licencia_conducir`

### Fase 3: Calidad y Flags

- [ ] `tiene_requisitos_discriminatorios`
- [ ] `calidad_redaccion`
- [ ] `tipo_oferta`
- [ ] `certificaciones_requeridas`

---

## Recomendaciones

1. **Prioridad Alta:** Implementar extracción de `tareas[]` - impacto directo en matching ESCO
2. **Prioridad Alta:** Agregar `tiene_gente_cargo` para distinguir roles de liderazgo
3. **Prioridad Media:** Extraer `tecnologias[]` y `marcas_especificas[]` para skills técnicas
4. **Prioridad Media:** Mejorar detección de `nivel_seniority` desde título/descripción
5. **Calidad:** Implementar `tipo_oferta` para filtrar ofertas no-reales

---

*Generado automáticamente: 2025-12-09 20:41:37*