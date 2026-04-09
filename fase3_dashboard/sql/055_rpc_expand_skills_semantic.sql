-- Migration 055: RPC expand_skills_semantic con soporte is_argentino (E2.3)
--
-- Expande una skill a skills semánticamente similares usando pgvector.
-- Si se provee occupation_uri, marca is_argentino=TRUE para skills
-- del perfil esco_argentino de esa ocupación.
--
-- Uso:
--   SELECT * FROM expand_skills_semantic(
--     'http://data.europa.eu/esco/skill/abc123',  -- skill URI a expandir
--     0.60,   -- umbral similitud
--     20,     -- máximo resultados
--     'http://data.europa.eu/esco/occupation/xyz'  -- ocupación (opcional)
--   );

CREATE OR REPLACE FUNCTION expand_skills_semantic(
  input_skill_uri      TEXT,
  match_threshold      FLOAT DEFAULT 0.60,
  match_count          INT DEFAULT 20,
  occupation_uri       TEXT DEFAULT NULL
)
RETURNS TABLE (
  skill_uri       TEXT,
  skill_label     TEXT,
  similarity      FLOAT,
  is_argentino    BOOLEAN
)
LANGUAGE sql STABLE
SET statement_timeout = '10s'
AS $$
  WITH argentino_skills AS (
    -- Extraer URIs de skills del perfil argentino para la ocupación dada
    SELECT elem->>'esco_uri' AS esco_uri
    FROM esco_argentino ea,
         jsonb_array_elements(ea.skills_consolidadas) AS elem
    WHERE occupation_uri IS NOT NULL
      AND ea.esco_occupation_uri = occupation_uri
  ),
  input_emb AS (
    SELECT embedding
    FROM skills_embeddings
    WHERE skills_embeddings.skill_uri = input_skill_uri
    LIMIT 1
  ),
  matches AS (
    -- LATERAL + ORDER BY usa el índice HNSW (mucho más rápido que CROSS JOIN + filter)
    SELECT
      se.skill_uri,
      se.skill_label,
      (1 - (se.embedding <=> ie.embedding))::FLOAT AS similarity
    FROM input_emb ie
    CROSS JOIN LATERAL (
      SELECT s.skill_uri, s.skill_label, s.embedding
      FROM skills_embeddings s
      WHERE s.skill_uri != input_skill_uri
      ORDER BY s.embedding <=> ie.embedding
      LIMIT match_count
    ) se
    WHERE (1 - (se.embedding <=> ie.embedding)) >= match_threshold
  )
  SELECT
    m.skill_uri,
    m.skill_label,
    m.similarity,
    CASE
      WHEN occupation_uri IS NOT NULL AND a.esco_uri IS NOT NULL THEN TRUE
      ELSE FALSE
    END AS is_argentino
  FROM matches m
  LEFT JOIN argentino_skills a ON a.esco_uri = m.skill_uri
  ORDER BY
    CASE WHEN occupation_uri IS NOT NULL AND a.esco_uri IS NOT NULL THEN 0 ELSE 1 END,
    m.similarity DESC;
$$;
