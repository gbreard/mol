-- Migration 024 — SPEC W Etapa 1
-- Schema base para captura de auditorías estructuradas de validadores
--
-- Refs:
--   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.1
--   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (D1, D3, D5)

-- 1) Tabla audit_actions (append-only)
CREATE TABLE audit_actions (
  id BIGSERIAL PRIMARY KEY,
  id_oferta TEXT NOT NULL,
  validador TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  action_type TEXT NOT NULL CHECK (action_type IN (
    'mark_task_incorrect',
    'mark_skill_incorrect',
    'add_suggested_task',
    'add_suggested_skill',
    'mark_revised',
    'mark_total_failure',
    'unmark_revised',
    'unmark_total_failure'
  )),
  target_type TEXT CHECK (target_type IN ('task', 'skill', 'occupation', 'oferta_global')),
  target_id TEXT,
  target_value TEXT,
  note TEXT,
  run_id TEXT,
  matching_version TEXT,
  source TEXT NOT NULL DEFAULT 'human'
    CHECK (source IN ('human', 'auto_corrector', 'rule_engine', 'import'))
);

CREATE INDEX idx_audit_actions_oferta ON audit_actions(id_oferta);
CREATE INDEX idx_audit_actions_validador ON audit_actions(validador);
CREATE INDEX idx_audit_actions_type ON audit_actions(action_type);
CREATE INDEX idx_audit_actions_timestamp ON audit_actions(timestamp DESC);
CREATE INDEX idx_audit_actions_source ON audit_actions(source);

-- 2) Trigger para prevenir UPDATE/DELETE (inmutabilidad append-only)
CREATE OR REPLACE FUNCTION prevent_audit_actions_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_actions is append-only. Use inverse actions instead.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_actions_no_update
  BEFORE UPDATE ON audit_actions
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_actions_modification();

CREATE TRIGGER trg_audit_actions_no_delete
  BEFORE DELETE ON audit_actions
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_actions_modification();

-- 3) Columnas nuevas en ofertas_dashboard
ALTER TABLE ofertas_dashboard
  ADD COLUMN estado_revision TEXT
  CHECK (estado_revision IS NULL OR estado_revision IN ('revisada', 'mal_extraida_total'));

ALTER TABLE ofertas_dashboard ADD COLUMN denominacion_arg TEXT;
ALTER TABLE ofertas_dashboard ADD COLUMN denominacion_esp TEXT;

CREATE INDEX idx_ofertas_dashboard_estado_revision
  ON ofertas_dashboard(estado_revision)
  WHERE estado_revision IS NOT NULL;

-- 4) Comentarios documentales
COMMENT ON TABLE audit_actions IS
  'SPEC W Etapa 1 — Captura granular de auditorías. Append-only: no UPDATE ni DELETE permitidos.';
COMMENT ON COLUMN audit_actions.source IS
  'Origen de la acción: human (validador), auto_corrector, rule_engine, import (histórico).';
COMMENT ON COLUMN ofertas_dashboard.estado_revision IS
  'SPEC W — Estado de revisión humana. NULL=pendiente, revisada=OK, mal_extraida_total=todo mal.';
