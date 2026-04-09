-- Migration 052: Ampliar CHECK constraint de ofertas_skills.origen
-- El pipeline local genera nuevos valores de skill_tipo_fuente que
-- no estaban en el constraint original.

-- Eliminar constraint viejo
ALTER TABLE ofertas_skills DROP CONSTRAINT IF EXISTS ofertas_skills_origen_check;

-- Crear constraint ampliado con todos los valores del pipeline
ALTER TABLE ofertas_skills ADD CONSTRAINT ofertas_skills_origen_check
  CHECK (origen IN (
    'regla', 'semantico', 'llm', 'merged', 'manual',
    'tarea', 'titulo', 'terminologia',
    'soft_skill_declarada', 'tecnologia_declarada',
    'herramienta_declarada', 'skills_nlp', 'skills_nlp_declarada'
  ));
