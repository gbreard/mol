-- Migration 042: Score de confianza + RPCs para equivalencias
-- SPEC_EQUIV_UI_MEJORAS: Componentes 1, 2, 3

-- Columnas de similitud (score de confianza del clustering)
ALTER TABLE skill_equivalences
ADD COLUMN IF NOT EXISTS similitud_promedio REAL;

ALTER TABLE skill_equivalences
ADD COLUMN IF NOT EXISTS similitud_minima REAL;

-- RPC: timestamp del último cambio en equivalencias
-- Usado por run_matching_pipeline() para detectar staleness
CREATE OR REPLACE FUNCTION get_latest_equiv_update()
RETURNS TIMESTAMPTZ
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT MAX(updated_at) FROM skill_equivalences;
$$;

-- RPC: impacto de un grupo de equivalencia en ocupaciones
-- Usado por UI al expandir grupo (lazy load)
CREATE OR REPLACE FUNCTION get_equivalencia_impacto(p_equivalence_id TEXT)
RETURNS TABLE (
    isco_code TEXT,
    ocupacion_label TEXT,
    ofertas_count BIGINT,
    pct_de_ocupacion REAL
)
LANGUAGE sql SECURITY DEFINER
SET statement_timeout = '10s'
AS $$
    WITH ofertas_del_grupo AS (
        SELECT DISTINCT os.id_oferta
        FROM ofertas_skills os
        WHERE os.equivalence_id = p_equivalence_id
    ),
    totales_por_isco AS (
        SELECT d.isco_code, COUNT(DISTINCT d.id_oferta) as total_ocupacion
        FROM ofertas_dashboard d
        GROUP BY d.isco_code
    )
    SELECT
        d.isco_code,
        d.isco_label as ocupacion_label,
        COUNT(DISTINCT og.id_oferta) as ofertas_count,
        ROUND(
            (COUNT(DISTINCT og.id_oferta)::NUMERIC /
            NULLIF(t.total_ocupacion, 0) * 100)::NUMERIC, 1
        )::REAL as pct_de_ocupacion
    FROM ofertas_del_grupo og
    JOIN ofertas_dashboard d ON og.id_oferta = d.id_oferta
    LEFT JOIN totales_por_isco t ON d.isco_code = t.isco_code
    GROUP BY d.isco_code, d.isco_label, t.total_ocupacion
    ORDER BY ofertas_count DESC
    LIMIT 5;
$$;
