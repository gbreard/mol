-- Migration 048: OE-C3 — nivel + certificado en perfil_skills + search_occupations_by_text

CREATE INDEX IF NOT EXISTS idx_occ_label_trgm
  ON occupations_embeddings USING gin (occupation_label gin_trgm_ops);

CREATE OR REPLACE FUNCTION search_occupations_by_text(
  query_text TEXT,
  similarity_min FLOAT DEFAULT 0.2,
  max_results INT DEFAULT 10
)
RETURNS TABLE (
  occupation_uri TEXT,
  occupation_label TEXT,
  isco_code TEXT,
  text_similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    o.occupation_uri,
    o.occupation_label,
    o.isco_code,
    similarity(lower(o.occupation_label), lower(query_text))::FLOAT AS text_similarity
  FROM occupations_embeddings o
  WHERE similarity(lower(o.occupation_label), lower(query_text)) >= similarity_min
  ORDER BY similarity(lower(o.occupation_label), lower(query_text)) DESC
  LIMIT max_results;
$$;

ALTER TABLE perfil_skills
  ADD COLUMN IF NOT EXISTS nivel TEXT
    CHECK (nivel IN ('basico', 'intermedio', 'avanzado'))
    DEFAULT 'intermedio';

ALTER TABLE perfil_skills
  ADD COLUMN IF NOT EXISTS certificado BOOLEAN DEFAULT FALSE;
