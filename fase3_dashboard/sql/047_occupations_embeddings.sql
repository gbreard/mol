-- Migration 047: Tabla occupations_embeddings + RPC match_occupations_by_skills
-- Embeddings BGE-M3 (1024 dims) de 3,045 ocupaciones ESCO
-- Permite match directo: skills persona → ocupaciones por cosine similarity

-- ============================================================
-- 1. TABLA
-- ============================================================

CREATE TABLE IF NOT EXISTS occupations_embeddings (
  occupation_uri   TEXT PRIMARY KEY,
  occupation_label TEXT NOT NULL,
  isco_code        TEXT NOT NULL,
  embedding        vector(1024) NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE occupations_embeddings IS 'Embeddings BGE-M3 de ocupaciones ESCO para match directo skills→ocupaciones';

-- ============================================================
-- 2. ÍNDICE HNSW
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_occ_emb_hnsw
  ON occupations_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 128);

CREATE INDEX IF NOT EXISTS idx_occ_emb_isco
  ON occupations_embeddings(isco_code);

-- ============================================================
-- 3. RPC match_occupations_by_skills
-- ============================================================
-- Skill-por-skill con score máximo (no promedio).
-- Para cada skill de la persona, busca ocupaciones cercanas por cosine.
-- Agrega por ocupación: MAX(similarity) + COUNT(skills distintas).

CREATE OR REPLACE FUNCTION match_occupations_by_skills(
  skill_uris           TEXT[],
  similarity_threshold FLOAT DEFAULT 0.55,
  max_results          INT DEFAULT 10
)
RETURNS TABLE (
  occupation_uri   TEXT,
  occupation_label TEXT,
  isco_code        TEXT,
  best_similarity  FLOAT,
  skills_matched   INT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    oe.occupation_uri,
    oe.occupation_label,
    oe.isco_code,
    MAX(1 - (oe.embedding <=> se.embedding))::FLOAT AS best_similarity,
    COUNT(DISTINCT se.skill_uri)::INT               AS skills_matched
  FROM occupations_embeddings oe
  JOIN skills_embeddings se ON se.skill_uri = ANY(skill_uris)
  WHERE (1 - (oe.embedding <=> se.embedding)) >= similarity_threshold
  GROUP BY oe.occupation_uri, oe.occupation_label, oe.isco_code
  ORDER BY best_similarity DESC
  LIMIT max_results;
$$;

COMMENT ON FUNCTION match_occupations_by_skills IS 'Match directo skills persona → ocupaciones ESCO por cosine similarity (skill-por-skill, MAX)';

-- ============================================================
-- 4. RLS
-- ============================================================

ALTER TABLE occupations_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "occupations_embeddings_read" ON occupations_embeddings
  FOR SELECT USING (true);

CREATE POLICY "occupations_embeddings_write" ON occupations_embeddings
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
