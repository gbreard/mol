-- Migration 037: Add equivalence columns to ofertas_skills
-- Allows grouping/aggregation by canonical skill (equivalence group)

ALTER TABLE ofertas_skills ADD COLUMN IF NOT EXISTS equivalence_id TEXT;
ALTER TABLE ofertas_skills ADD COLUMN IF NOT EXISTS canonical_label TEXT;

-- Index for GROUP BY equivalence_id (aggregation queries)
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_equiv
  ON ofertas_skills(equivalence_id) WHERE equivalence_id IS NOT NULL;

-- Index for canonical_label aggregation
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_canonical
  ON ofertas_skills(canonical_label) WHERE canonical_label IS NOT NULL;
