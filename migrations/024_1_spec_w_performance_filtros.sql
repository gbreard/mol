-- Migration 024.1 — Performance optimization para filtros SPEC W
-- Sub-tarea C de Sprint 1: optimizar filtros solo_datos_incompletos y
-- estado_revision='pendiente' que sobre 68K ofertas tardaban 1.8-5s.
--
-- Refs:
--   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 2.1 (F7, F8)
--   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (D8 — cobertura 67%)
--   migrations/024_spec_w_audit_actions.sql (migration base)

-- 1) Generated column para datos incompletos
-- Cobertura: 67% del concepto original. Excluye chequeo "sin skills"
-- (queda como deuda D8 documentada).
ALTER TABLE ofertas_dashboard
  ADD COLUMN datos_incompletos BOOLEAN
  GENERATED ALWAYS AS (
    esco_occupation_uri IS NULL
    OR tareas_explicitas IS NULL
    OR tareas_explicitas = ''
    OR occupation_match_score < 0.5
  ) STORED;

-- 2) Índice parcial: solo indexamos las ofertas que SÍ son incompletas
-- (probable: ~6% del total = ~3500 ofertas)
CREATE INDEX idx_ofertas_datos_incompletos
  ON ofertas_dashboard(id_oferta)
  WHERE datos_incompletos = true;

-- 3) Índice parcial inverso para estado_revision IS NULL
-- (probable: 98% = ~68K ofertas; ayuda al planner a evitar Seq Scan
-- para queries con LIMIT + paginación)
CREATE INDEX idx_ofertas_dashboard_estado_pendiente
  ON ofertas_dashboard(id_oferta)
  WHERE estado_revision IS NULL;

-- 4) Comentarios documentales
COMMENT ON COLUMN ofertas_dashboard.datos_incompletos IS
  'SPEC W F7 — TRUE si la oferta tiene datos faltantes detectables: '
  'sin ESCO, sin tareas, o score < 0.5. LIMITACIÓN D8: NO incluye '
  'chequeo "sin skills" (~1.4K ofertas quedan fuera del filtro). Se '
  'agregará en iteración futura si Cyn lo necesita.';

COMMENT ON INDEX idx_ofertas_dashboard_estado_pendiente IS
  'SPEC W F7 — Acelera consultas estado_revision IS NULL (ofertas '
  'pendientes de revisión humana).';
