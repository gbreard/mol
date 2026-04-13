-- Migration 056: Actualizar match_occupations_by_skills con prioritize_argentino (E2.3)
--
-- Agrega parámetro prioritize_argentino BOOLEAN.
-- Si TRUE: ocupaciones con más skills argentinas matcheadas reciben bonus de 0.05.
--
-- Compatible con llamadas existentes (nuevo param tiene DEFAULT FALSE).

CREATE OR REPLACE FUNCTION match_occupations_by_skills(
  skill_uris              TEXT[],
  similarity_threshold    FLOAT DEFAULT 0.55,
  max_results             INT DEFAULT 10,
  prioritize_argentino    BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
  occupation_uri   TEXT,
  occupation_label TEXT,
  isco_code        TEXT,
  best_similarity  FLOAT,
  skills_matched   INT,
  argentino_skills INT
)
LANGUAGE sql STABLE
AS $$
  WITH base_matches AS (
    SELECT
      oe.occupation_uri,
      oe.occupation_label,
      oe.isco_code,
      MAX(1 - (oe.embedding <=> se.embedding))::FLOAT AS best_similarity,
      COUNT(DISTINCT se.skill_uri)::INT                AS skills_matched
    FROM occupations_embeddings oe
    JOIN skills_embeddings se ON se.skill_uri = ANY(skill_uris)
    WHERE (1 - (oe.embedding <=> se.embedding)) >= similarity_threshold
    GROUP BY oe.occupation_uri, oe.occupation_label, oe.isco_code
  ),
  argentino_count AS (
    -- Contar cuántas de las skills input están en el perfil argentino de cada ocupación
    SELECT
      ea.esco_occupation_uri AS occupation_uri,
      COUNT(DISTINCT elem->>'esco_uri')::INT AS argentino_count
    FROM esco_argentino ea,
         jsonb_array_elements(ea.skills_consolidadas) AS elem
    WHERE elem->>'esco_uri' = ANY(skill_uris)
    GROUP BY ea.esco_occupation_uri
  )
  SELECT
    bm.occupation_uri,
    bm.occupation_label,
    bm.isco_code,
    CASE
      WHEN prioritize_argentino AND COALESCE(ac.argentino_count, 0) > 0
      THEN LEAST(bm.best_similarity + 0.05, 1.0)
      ELSE bm.best_similarity
    END AS best_similarity,
    bm.skills_matched,
    COALESCE(ac.argentino_count, 0)::INT AS argentino_skills
  FROM base_matches bm
  LEFT JOIN argentino_count ac ON ac.occupation_uri = bm.occupation_uri
  ORDER BY
    CASE
      WHEN prioritize_argentino AND COALESCE(ac.argentino_count, 0) > 0
      THEN LEAST(bm.best_similarity + 0.05, 1.0)
      ELSE bm.best_similarity
    END DESC
  LIMIT max_results;
$$;

COMMENT ON FUNCTION match_occupations_by_skills IS 'Match skills → ocupaciones por cosine. Con prioritize_argentino=TRUE, bonus 0.05 a ocupaciones con skills del perfil argentino.';
