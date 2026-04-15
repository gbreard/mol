-- Migration 062: M-10 Parte 2 — Gold Set con skills esperadas
--
-- Skills anotadas para cada oferta del Gold Set.
-- Fuente inicial: Excel sheet 17_Skills_Completas_ESCO (587 skills, 48 ofertas).

CREATE TABLE IF NOT EXISTS gold_set_skills (
    id              BIGSERIAL PRIMARY KEY,
    id_oferta       TEXT NOT NULL,
    skill_label     TEXT NOT NULL,
    skill_uri       TEXT,
    origen          TEXT CHECK (origen IS NULL OR origen IN ('DECLARADA', 'IMPLÍCITA', 'IMPLICITA')),
    tipo_skill      TEXT,
    categoria       TEXT,
    es_digital      BOOLEAN DEFAULT FALSE,
    fuente          TEXT DEFAULT 'excel_dic2025',
    agregado_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(id_oferta, skill_label)
);

CREATE INDEX IF NOT EXISTS idx_gold_set_skills_oferta ON gold_set_skills(id_oferta);

COMMENT ON TABLE gold_set_skills IS 'M-10 P2: Skills esperadas por oferta del Gold Set para medir precision/recall de extracción';

ALTER TABLE gold_set_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "gold_set_skills_read" ON gold_set_skills FOR SELECT USING (true);
CREATE POLICY "gold_set_skills_write" ON gold_set_skills
  FOR ALL USING (auth.role() = 'service_role' OR auth.role() = 'authenticated')
  WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');
