-- Migration 063: Trazabilidad de propagación de correcciones humanas
-- SPEC T — agrega 3 columnas a issues para registrar el patrón corregido
-- y cuántas ofertas similares se propagaron.
--
-- Fecha: 2026-04-27
-- Spec: docs/specs/2026-04-27_T_flujo_propagacion_correcciones.md
--
-- Contexto: 542 issues humanos resueltos, 99.8% sin trazabilidad de
-- propagación. Esta migration habilita el modelo nuevo donde cada
-- corrección humana documenta cuántas ofertas similares afectó.

ALTER TABLE issues
  ADD COLUMN IF NOT EXISTS patron_corregido jsonb,
  ADD COLUMN IF NOT EXISTS propagacion_n int DEFAULT 0,
  ADD COLUMN IF NOT EXISTS propagacion_ids jsonb;

COMMENT ON COLUMN issues.patron_corregido IS
  'JSON estructurado: {campo, condicion: {tipo, keywords/valores}, valor_anterior, valor_nuevo}. Generado por Claude al resolver issue, describe el patrón aplicable a otras ofertas.';

COMMENT ON COLUMN issues.propagacion_n IS
  'Cantidad de ofertas similares afectadas por el fix (excluye la oferta del issue). 0 si excepción puntual sin patrón generalizable.';

COMMENT ON COLUMN issues.propagacion_ids IS
  'Array JSON con id_oferta tocados durante la propagación. Para auditoría posterior y rollback si necesario.';

-- Índice parcial para queries de auditoría (solo issues con propagación efectiva)
CREATE INDEX IF NOT EXISTS idx_issues_propagacion_n ON issues(propagacion_n)
  WHERE propagacion_n > 0;
