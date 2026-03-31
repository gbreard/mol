-- Migration 042: Tabla skills_embeddings con pgvector
-- Almacena embeddings BGE-M3 (1024 dims) de las 14,247 skills ESCO
-- Permite matching semántico: persona_skill <=> oferta_skill por cosine distance
--
-- Prerequisito: CREATE EXTENSION vector; (ya habilitado)

-- ============================================================
-- 1. TABLA skills_embeddings
-- ============================================================

CREATE TABLE IF NOT EXISTS skills_embeddings (
  skill_uri    TEXT PRIMARY KEY,
  skill_label  TEXT NOT NULL,
  embedding    vector(1024) NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE skills_embeddings IS 'Embeddings BGE-M3 de skills ESCO para matching semántico via pgvector';
COMMENT ON COLUMN skills_embeddings.embedding IS 'Vector BGE-M3 1024 dims, normalizado (cosine distance)';

-- ============================================================
-- 2. ÍNDICE HNSW para búsqueda por similitud coseno
-- ============================================================
-- HNSW es más rápido que IVFFlat para 14K rows y no requiere training
-- ef_construction=128 y m=16 son buenos defaults para este tamaño

CREATE INDEX IF NOT EXISTS idx_skills_embeddings_hnsw
  ON skills_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 128);

-- ============================================================
-- 3. RPC: match_skills_semantic
-- ============================================================
-- Recibe URIs de skills de una persona, encuentra las skills
-- más similares semánticamente en las ofertas.
--
-- Uso:
--   SELECT * FROM match_skills_semantic(
--     ARRAY['http://...skill/abc', 'http://...skill/def'],
--     0.60,  -- umbral mínimo de similitud
--     20     -- máximo resultados por skill
--   );

CREATE OR REPLACE FUNCTION match_skills_semantic(
  persona_skill_uris TEXT[],
  similarity_threshold FLOAT DEFAULT 0.60,
  max_results_per_skill INT DEFAULT 20
)
RETURNS TABLE (
  persona_skill_uri   TEXT,
  persona_skill_label TEXT,
  matched_skill_uri   TEXT,
  matched_skill_label TEXT,
  similarity          FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    p.skill_uri       AS persona_skill_uri,
    p.skill_label     AS persona_skill_label,
    m.skill_uri       AS matched_skill_uri,
    m.skill_label     AS matched_skill_label,
    1 - (p.embedding <=> m.embedding) AS similarity
  FROM skills_embeddings p
  CROSS JOIN LATERAL (
    SELECT s.skill_uri, s.skill_label, s.embedding
    FROM skills_embeddings s
    WHERE s.skill_uri != p.skill_uri
      AND 1 - (p.embedding <=> s.embedding) >= similarity_threshold
    ORDER BY p.embedding <=> s.embedding
    LIMIT max_results_per_skill
  ) m
  WHERE p.skill_uri = ANY(persona_skill_uris)
  ORDER BY persona_skill_uri, similarity DESC;
$$;

COMMENT ON FUNCTION match_skills_semantic IS 'Busca skills semánticamente similares a las de una persona usando cosine similarity';

-- ============================================================
-- 4. RPC: match_persona_ofertas_semantic
-- ============================================================
-- El query principal: dado un perfil de persona (skills URIs),
-- encuentra ofertas con mejor match semántico.
--
-- Para cada oferta, calcula cuántas de sus skills están cubiertas
-- por las skills de la persona (con similitud >= umbral).
--
-- Uso:
--   SELECT * FROM match_persona_ofertas_semantic(
--     ARRAY['http://...skill/abc', 'http://...skill/def'],
--     0.60,  -- umbral similitud
--     50     -- límite ofertas
--   );

CREATE OR REPLACE FUNCTION match_persona_ofertas_semantic(
  persona_skill_uris TEXT[],
  similarity_threshold FLOAT DEFAULT 0.60,
  max_ofertas INT DEFAULT 50
)
RETURNS TABLE (
  id_oferta           TEXT,
  titulo              TEXT,
  empresa             TEXT,
  provincia           TEXT,
  isco_code           TEXT,
  skills_oferta_total INT,
  skills_cubiertas    INT,
  match_score         FLOAT,
  skills_detalle      JSONB
)
LANGUAGE sql STABLE
AS $$
  WITH persona_embs AS (
    -- Obtener embeddings de las skills de la persona
    SELECT skill_uri, skill_label, embedding
    FROM skills_embeddings
    WHERE skill_uri = ANY(persona_skill_uris)
  ),
  oferta_skills_with_match AS (
    -- Para cada skill de cada oferta, buscar la mejor similitud
    -- con alguna skill de la persona
    SELECT
      os.id_oferta,
      os.skill_uri AS oferta_skill_uri,
      os.preferred_label AS oferta_skill_label,
      COALESCE(best.similarity, 0) AS best_similarity,
      best.persona_skill_label,
      CASE WHEN os.skill_uri = ANY(persona_skill_uris) THEN true ELSE false END AS exact_match
    FROM ofertas_skills os
    LEFT JOIN LATERAL (
      SELECT
        pe.skill_label AS persona_skill_label,
        1 - (se_oferta.embedding <=> pe.embedding) AS similarity
      FROM persona_embs pe
      JOIN skills_embeddings se_oferta ON se_oferta.skill_uri = os.skill_uri
      ORDER BY se_oferta.embedding <=> pe.embedding
      LIMIT 1
    ) best ON true
  ),
  oferta_scores AS (
    -- Agregar scores por oferta
    SELECT
      osm.id_oferta,
      COUNT(*) AS skills_total,
      COUNT(*) FILTER (WHERE osm.best_similarity >= similarity_threshold OR osm.exact_match) AS skills_cubiertas,
      AVG(osm.best_similarity) AS avg_similarity,
      jsonb_agg(
        jsonb_build_object(
          'skill', osm.oferta_skill_label,
          'similarity', ROUND(osm.best_similarity::numeric, 3),
          'matched_by', osm.persona_skill_label,
          'exact', osm.exact_match
        )
        ORDER BY osm.best_similarity DESC
      ) AS detalle
    FROM oferta_skills_with_match osm
    WHERE osm.best_similarity > 0
    GROUP BY osm.id_oferta
  )
  SELECT
    os.id_oferta,
    od.titulo,
    od.empresa,
    od.provincia,
    od.isco_code,
    os.skills_total::INT AS skills_oferta_total,
    os.skills_cubiertas::INT AS skills_cubiertas,
    ROUND((os.skills_cubiertas::FLOAT / NULLIF(os.skills_total, 0) * 100)::numeric, 1)::FLOAT AS match_score,
    os.detalle AS skills_detalle
  FROM oferta_scores os
  JOIN ofertas_dashboard od ON od.id_oferta::TEXT = os.id_oferta
  WHERE os.skills_cubiertas > 0
  ORDER BY match_score DESC, os.avg_similarity DESC
  LIMIT max_ofertas;
$$;

COMMENT ON FUNCTION match_persona_ofertas_semantic IS 'Matching semántico persona vs ofertas usando pgvector cosine similarity';

-- ============================================================
-- 5. RLS
-- ============================================================

ALTER TABLE skills_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "skills_embeddings_read" ON skills_embeddings
  FOR SELECT USING (true);

CREATE POLICY "skills_embeddings_write" ON skills_embeddings
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
