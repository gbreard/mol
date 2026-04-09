-- Migration 051: Agregar embedding_model_version a tablas vectoriales
-- E1.2 del SPEC Motor de Conocimiento v1.3
-- Cierra el linaje: cada embedding sabe qué modelo lo generó.

-- skills_embeddings
ALTER TABLE skills_embeddings
  ADD COLUMN IF NOT EXISTS embedding_model_version TEXT;

COMMENT ON COLUMN skills_embeddings.embedding_model_version
  IS 'SHA del commit de HuggingFace del modelo que generó este embedding';

-- occupations_embeddings
ALTER TABLE occupations_embeddings
  ADD COLUMN IF NOT EXISTS embedding_model_version TEXT;

COMMENT ON COLUMN occupations_embeddings.embedding_model_version
  IS 'SHA del commit de HuggingFace del modelo que generó este embedding';
