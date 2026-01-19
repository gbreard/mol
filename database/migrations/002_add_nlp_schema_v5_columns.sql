-- Migration: 002_add_nlp_schema_v5_columns.sql
-- Fecha: 2025-12-09
-- Descripción: Agrega campos críticos de NLP Schema v5 para mejorar matching
-- Issue: MOL-62

-- ============================================================================
-- BLOQUE 8: Rol y Tareas
-- ============================================================================

-- Tareas explícitas extraídas de la descripción (JSON array)
ALTER TABLE ofertas_nlp ADD COLUMN tareas_explicitas TEXT;

-- Tareas inferidas del contexto (JSON array)
ALTER TABLE ofertas_nlp ADD COLUMN tareas_inferidas TEXT;

-- ¿Tiene gente a cargo? (0=No, 1=Sí, NULL=No detectado)
ALTER TABLE ofertas_nlp ADD COLUMN tiene_gente_cargo INTEGER;

-- Tipo de equipo que supervisa
ALTER TABLE ofertas_nlp ADD COLUMN tipo_equipo TEXT;

-- Producto o servicio que vende/produce
ALTER TABLE ofertas_nlp ADD COLUMN producto_servicio TEXT;

-- ============================================================================
-- BLOQUE 9: Condiciones Laborales
-- ============================================================================

-- Área funcional: 'Ventas', 'RRHH', 'IT', 'Administración', etc.
ALTER TABLE ofertas_nlp ADD COLUMN area_funcional TEXT;

-- Nivel de seniority: 'trainee', 'junior', 'semi-senior', 'senior', 'lead', 'manager'
ALTER TABLE ofertas_nlp ADD COLUMN nivel_seniority TEXT;

-- Tipo de contrato: 'indeterminado', 'temporal', 'eventual', 'pasantia'
ALTER TABLE ofertas_nlp ADD COLUMN tipo_contrato TEXT;

-- ============================================================================
-- BLOQUE 2: Empresa
-- ============================================================================

-- Sector de la empresa: 'retail', 'tecnología', 'salud', 'manufactura', etc.
ALTER TABLE ofertas_nlp ADD COLUMN sector_empresa TEXT;

-- ¿Es tercerizado? (consultora que contrata para cliente final)
ALTER TABLE ofertas_nlp ADD COLUMN es_tercerizado INTEGER;

-- ============================================================================
-- BLOQUE 6: Skills Expandido
-- ============================================================================

-- Tecnologías específicas (más granular que skills_tecnicas)
ALTER TABLE ofertas_nlp ADD COLUMN tecnologias_list TEXT;

-- Marcas específicas mencionadas
ALTER TABLE ofertas_nlp ADD COLUMN marcas_especificas_list TEXT;

-- ============================================================================
-- BLOQUE 12: Metadatos NLP
-- ============================================================================

-- Tipo de oferta: 'demanda_real', 'motivacional', 'titulo_only', 'republica'
ALTER TABLE ofertas_nlp ADD COLUMN tipo_oferta TEXT;

-- Calidad del texto: 'alta', 'media', 'baja'
ALTER TABLE ofertas_nlp ADD COLUMN calidad_texto TEXT;

-- ¿Pasa a matching? (basado en calidad)
ALTER TABLE ofertas_nlp ADD COLUMN pasa_a_matching INTEGER;

-- ============================================================================
-- BLOQUE 13: Licencias y Permisos
-- ============================================================================

-- ¿Requiere licencia de conducir?
ALTER TABLE ofertas_nlp ADD COLUMN licencia_conducir INTEGER;

-- Tipo de licencia requerida
ALTER TABLE ofertas_nlp ADD COLUMN tipo_licencia TEXT;

-- ============================================================================
-- BLOQUE 14: Calidad y Flags
-- ============================================================================

-- ¿Tiene requisitos discriminatorios? (edad, sexo)
ALTER TABLE ofertas_nlp ADD COLUMN tiene_requisitos_discriminatorios INTEGER;

-- Edad mínima requerida (si se menciona)
ALTER TABLE ofertas_nlp ADD COLUMN requisito_edad_min INTEGER;

-- Edad máxima requerida (si se menciona)
ALTER TABLE ofertas_nlp ADD COLUMN requisito_edad_max INTEGER;

-- ============================================================================
-- ÍNDICES para consultas frecuentes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_area_funcional ON ofertas_nlp(area_funcional);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_nivel_seniority ON ofertas_nlp(nivel_seniority);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_tipo_oferta ON ofertas_nlp(tipo_oferta);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_sector_empresa ON ofertas_nlp(sector_empresa);

-- ============================================================================
-- Registro de migración
-- ============================================================================

INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('002', 'Add NLP Schema v5 columns', datetime('now'));
