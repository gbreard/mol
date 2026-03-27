-- Migration 036: Skill Equivalences — grupos de skills ESCO equivalentes
-- Resuelve: variaciones lingüísticas del mismo concepto (singular/plural/verbal)
-- "trabajar en equipo" = "trabajar en equipos" = "principios del trabajo en equipo"

CREATE TABLE IF NOT EXISTS skill_equivalences (
  id TEXT PRIMARY KEY,                       -- EQ-00001
  label_representante TEXT NOT NULL,         -- El label que ve el usuario
  label_argentino TEXT,                      -- Label argentino (si el analista lo puso)
  miembros JSONB NOT NULL DEFAULT '[]',      -- [{uri, label, score_promedio, frecuencia}]
  cantidad_miembros INTEGER DEFAULT 0,
  frecuencia_total INTEGER DEFAULT 0,        -- Cuántas ofertas tienen algún miembro del grupo
  estado TEXT DEFAULT 'auto' CHECK (estado IN ('auto', 'revisado', 'aprobado')),
  revisado_por TEXT,
  notas TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skill_equiv_estado ON skill_equivalences(estado);
CREATE INDEX IF NOT EXISTS idx_skill_equiv_frecuencia ON skill_equivalences(frecuencia_total DESC);

-- Lookup inverso: dado un URI, encontrar su grupo
CREATE TABLE IF NOT EXISTS skill_equivalence_lookup (
  skill_uri TEXT PRIMARY KEY,
  equivalence_id TEXT REFERENCES skill_equivalences(id),
  skill_label TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_equiv_lookup_group ON skill_equivalence_lookup(equivalence_id);

-- RLS
ALTER TABLE skill_equivalences ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_equivalence_lookup ENABLE ROW LEVEL SECURITY;

CREATE POLICY "skill_equiv_read" ON skill_equivalences FOR SELECT USING (true);
CREATE POLICY "skill_equiv_write" ON skill_equivalences FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "skill_equiv_lookup_read" ON skill_equivalence_lookup FOR SELECT USING (true);
CREATE POLICY "skill_equiv_lookup_write" ON skill_equivalence_lookup FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- Trigger updated_at
DROP TRIGGER IF EXISTS skill_equiv_updated_at ON skill_equivalences;
CREATE TRIGGER skill_equiv_updated_at BEFORE UPDATE ON skill_equivalences
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
