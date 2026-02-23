-- ============================================================
-- Índices para acelerar get_skills_resumen
-- ofertas_skills tiene ~296K filas, el GROUP BY es el cuello
-- ============================================================

-- Índice compuesto para el GROUP BY del path sin filtros
-- Cubre: GROUP BY preferred_label, l1, l1_nombre, es_digital
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_agg
ON ofertas_skills (preferred_label, l1, l1_nombre, es_digital);

-- Índice para el JOIN del path con filtros
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_oferta
ON ofertas_skills (id_oferta);

-- Índice para ofertas_dashboard.id_oferta (para el JOIN inverso)
CREATE INDEX IF NOT EXISTS idx_ofertas_dashboard_id_oferta
ON ofertas_dashboard (id_oferta);
