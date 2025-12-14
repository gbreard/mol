-- =====================================================================
-- Migración 003: NLP Schema v5 Completo
-- =====================================================================
-- Fecha: 2025-12-10
-- Descripción: Agrega ~100 columnas faltantes para implementar el schema v5
-- Referencia: docs/NLP_SCHEMA_V5.md (16 bloques, ~130 campos totales)
--
-- IMPORTANTE: Ejecutar con backup previo de bumeran_scraping.db
-- =====================================================================

-- =====================================================================
-- BLOQUE 2: EMPRESA (4 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN empresa_tamanio TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN empresa_antiguedad TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN rubro_empresa TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN cliente_final TEXT;

-- =====================================================================
-- BLOQUE 3: UBICACIÓN Y MOVILIDAD (11 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN provincia TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN localidad TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN tipo_lugar TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN zonas_cobertura_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN modalidad TEXT;  -- presencial/remoto/hibrido
ALTER TABLE ofertas_nlp ADD COLUMN requiere_viajar INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN frecuencia_viaje TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN radio_viaje_km INTEGER;
ALTER TABLE ofertas_nlp ADD COLUMN requiere_movilidad_propia INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN zona_residencia_req TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN acepta_relocacion INTEGER;  -- boolean

-- =====================================================================
-- BLOQUE 4: EXPERIENCIA (7 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_texto TEXT;  -- texto original
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_descripcion TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_nivel_previo TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_sector TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_areas_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_excluyente INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN experiencia_valorada INTEGER;  -- boolean

-- =====================================================================
-- BLOQUE 5: EDUCACIÓN (5 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN nivel_educativo_excluyente INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN titulo_requerido TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN orientacion_estudios TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN acepta_estudiantes_avanzados INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN estudios_valorados_list TEXT;  -- JSON array

-- =====================================================================
-- BLOQUE 6: SKILLS Y CONOCIMIENTOS (6 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN perfil_actitudinal_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN conocimientos_especificos_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN herramientas_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN sistemas_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN nivel_herramienta_json TEXT;  -- JSON object
ALTER TABLE ofertas_nlp ADD COLUMN conocimiento_excluyente_list TEXT;  -- JSON array

-- =====================================================================
-- BLOQUE 7: IDIOMAS (2 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN idioma_excluyente INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN idiomas_adicionales_json TEXT;  -- JSON array of objects

-- =====================================================================
-- BLOQUE 8: ROL Y TAREAS (2 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN mision_rol TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN interactua_con_externos_list TEXT;  -- JSON array

-- =====================================================================
-- BLOQUE 9: CONDICIONES LABORALES (4 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN horario_especifico TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN dias_trabajo_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN hora_entrada TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN hora_salida TEXT;

-- =====================================================================
-- BLOQUE 10: COMPENSACIÓN (9 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN salario_periodo TEXT;  -- mensual/anual
ALTER TABLE ofertas_nlp ADD COLUMN salario_neto INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_salario_base INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_comisiones INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_bonos INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN estructura_salarial TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN bonos_json TEXT;  -- JSON array of objects
ALTER TABLE ofertas_nlp ADD COLUMN pide_pretension_salarial INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN pretension_formato TEXT;

-- =====================================================================
-- BLOQUE 11: BENEFICIOS (11 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN tiene_cobertura_salud INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN cobertura_salud_familia INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_comedor INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_capacitacion INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_crecimiento INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_programa_asistencia INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tiene_descuentos INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN descuentos_educacion_json TEXT;  -- JSON
ALTER TABLE ofertas_nlp ADD COLUMN descuentos_gimnasio_json TEXT;  -- JSON
ALTER TABLE ofertas_nlp ADD COLUMN vehiculo_provisto INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN otros_beneficios_list TEXT;  -- JSON array

-- =====================================================================
-- BLOQUE 12: METADATOS NLP (3 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN nlp_score_max INTEGER;
ALTER TABLE ofertas_nlp ADD COLUMN largo_descripcion INTEGER;
ALTER TABLE ofertas_nlp ADD COLUMN campos_con_fuente_json TEXT;  -- JSON trazabilidad

-- =====================================================================
-- BLOQUE 13: LICENCIAS Y PERMISOS (5 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN licencia_conducir_excluyente INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN licencia_autoelevador INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN otras_licencias_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN matricula_profesional INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN matricula_tipo TEXT;

-- =====================================================================
-- BLOQUE 14: CALIDAD Y FLAGS (10 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN tiene_errores_tipeo INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN errores_detectados_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN calidad_redaccion TEXT;  -- alta/media/baja
ALTER TABLE ofertas_nlp ADD COLUMN titulo_repetido_en_descripcion INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN tipo_discriminacion_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN requisito_sexo TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN titulo_genero_especifico INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN titulo_normalizado TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN es_republica INTEGER;  -- boolean (reposteo)
ALTER TABLE ofertas_nlp ADD COLUMN tiene_clausula_diversidad INTEGER;  -- boolean

-- =====================================================================
-- BLOQUE 15: CERTIFICACIONES (4 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN certificaciones_requeridas_json TEXT;  -- JSON array objects
ALTER TABLE ofertas_nlp ADD COLUMN certificaciones_deseables_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN certificaciones_tecnicas_list TEXT;  -- JSON array
ALTER TABLE ofertas_nlp ADD COLUMN certificaciones_seguridad_list TEXT;  -- JSON array

-- =====================================================================
-- BLOQUE 16: CONDICIONES ESPECIALES DE TRABAJO (12 nuevas)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_en_altura INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN altura_metros INTEGER;
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_espacios_confinados INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_exterior INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_nocturno INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_turnos_rotativos INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_fines_semana INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_feriados INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN trabajo_riesgo INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN requiere_esfuerzo_fisico INTEGER;  -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN carga_peso_kg INTEGER;
ALTER TABLE ofertas_nlp ADD COLUMN ambiente_trabajo TEXT;

-- =====================================================================
-- RESUMEN: 95 columnas nuevas agregadas
-- Total columnas ofertas_nlp: 48 + 95 = 143
-- =====================================================================
