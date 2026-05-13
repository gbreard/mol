-- Migration 065: índice parcial para issues humanos
--
-- Fecha: 2026-05-13
-- Contexto:
--   La tabla `issues` tiene ~397K filas, de las cuales ~396K son del
--   auto-validator y solo ~738 son humanas. La query del panel
--   /admin/issues filtra `autor_email != 'auto-validator@mol.gob.ar'`
--   y ordena por `created_at DESC LIMIT 500`. Sin índice que soporte
--   ese filtro, Postgres escanea las 397K filas y se aborta por
--   statement timeout (código 57014).
--
-- Solución: índice parcial sobre el subset humano, ordenado por
--   created_at DESC para que el ORDER BY use directamente el índice.
--
-- IMPORTANTE: el predicado usa `<>` (no `IS DISTINCT FROM`) porque
--   PostgREST `.neq()` genera `autor_email <> 'X'`. El planner de
--   Postgres descarta el índice parcial si los predicados no son
--   sintácticamente iguales (no chequea equivalencia semántica).
--   Filas con autor_email IS NULL quedan fuera del índice — igual
--   que las descarta el filtro `<>` (PostgREST nunca las devuelve
--   con .neq), así que la cobertura es exacta.

DROP INDEX IF EXISTS idx_issues_humanos_created_at;

CREATE INDEX idx_issues_humanos_created_at
  ON issues (created_at DESC)
  WHERE autor_email <> 'auto-validator@mol.gob.ar';

COMMENT ON INDEX idx_issues_humanos_created_at IS
  'Acelera /admin/issues. Subset ~738 humanos vs 397K totales. Sin este índice la query timeout-ea.';
