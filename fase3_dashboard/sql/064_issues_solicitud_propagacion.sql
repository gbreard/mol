-- Migration 064: Solicitudes de propagación por analistas
-- SPEC T Fase 4 — agrega 3 columnas a issues para que analistas (Cyn/Diego)
-- puedan SOLICITAR propagación. Solo el admin (Gerardo) APLICA.
--
-- Fecha: 2026-04-28
-- Spec: docs/specs/2026-04-27_T_flujo_propagacion_correcciones.md
-- Wireframe: docs/plan/03_WIREFRAMES/spec-t-propagacion-issues.md
--
-- Modelo de roles:
--   Analistas (Cyn/Diego): VEN propagación + SOLICITAN, NO aplican.
--   Admin (Gerardo): VE + SOLICITA + APLICA.
--
-- Razón del modelo: una propagación mal calibrada puede dañar miles
-- de ofertas. El admin hace controles previos (dry-run, sample,
-- validar target) antes de aplicar.

ALTER TABLE issues
  ADD COLUMN IF NOT EXISTS propagacion_solicitada boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS propagacion_solicitada_por text,
  ADD COLUMN IF NOT EXISTS propagacion_solicitada_at timestamptz;

COMMENT ON COLUMN issues.propagacion_solicitada IS
  'Boolean. Analista (Cyn/Diego) o admin marcó que la corrección debería aplicarse a otras ofertas similares. Genera orden pendiente para que admin aplique.';

COMMENT ON COLUMN issues.propagacion_solicitada_por IS
  'Email del usuario que solicitó la propagación. Para auditoría.';

COMMENT ON COLUMN issues.propagacion_solicitada_at IS
  'Cuándo se solicitó la propagación. Permite ordenar la cola admin por antigüedad.';

-- Índice parcial para query de cola admin (solo solicitudes activas)
CREATE INDEX IF NOT EXISTS idx_issues_propagacion_solicitada
  ON issues(propagacion_solicitada, propagacion_solicitada_at)
  WHERE propagacion_solicitada = true;
