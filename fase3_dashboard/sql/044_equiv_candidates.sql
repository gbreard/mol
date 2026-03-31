-- Migration 044: Tabla equiv_candidates + RPCs
-- M-08b Parte 2: Candidatos a nuevos grupos desde co-matcheo

CREATE TABLE IF NOT EXISTS equiv_candidates (
    id                BIGSERIAL PRIMARY KEY,
    uri_esco          TEXT NOT NULL,
    skill_label_esco  TEXT NOT NULL,
    termino_a         TEXT NOT NULL,
    termino_b         TEXT NOT NULL,
    fuente_a          TEXT NOT NULL,
    fuente_b          TEXT NOT NULL,
    co_apariciones    INT NOT NULL,
    score_promedio_a  REAL,
    score_promedio_b  REAL,
    estado            TEXT DEFAULT 'pendiente',
    revisado_por      TEXT,
    revisado_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidates_uri    ON equiv_candidates(uri_esco);
CREATE INDEX IF NOT EXISTS idx_candidates_estado ON equiv_candidates(estado);

ALTER TABLE equiv_candidates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "platform_admin_only" ON equiv_candidates;
CREATE POLICY "platform_admin_only" ON equiv_candidates
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');

-- RPC: Listar candidatos
CREATE OR REPLACE FUNCTION get_equiv_candidates(
    p_estado TEXT DEFAULT 'pendiente',
    limit_n INT DEFAULT 50
)
RETURNS SETOF equiv_candidates
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT * FROM equiv_candidates
    WHERE estado = p_estado
    ORDER BY co_apariciones DESC
    LIMIT limit_n;
$$;

-- RPC: Aprobar candidato
CREATE OR REPLACE FUNCTION aprobar_candidato(p_candidate_id BIGINT, p_action TEXT)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    UPDATE equiv_candidates
    SET estado = 'aprobado',
        revisado_at = NOW()
    WHERE id = p_candidate_id;
END;
$$;

-- RPC: Rechazar candidato
CREATE OR REPLACE FUNCTION rechazar_candidato(p_candidate_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    UPDATE equiv_candidates
    SET estado = 'rechazado',
        revisado_at = NOW()
    WHERE id = p_candidate_id;
END;
$$;
