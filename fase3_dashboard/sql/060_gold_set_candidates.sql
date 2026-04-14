-- Migration 060: M-10 — RPC para candidatas al Gold Set
--
-- Retorna ofertas priorizadas para agregar al Gold Set,
-- excluyendo las que ya están en él.

CREATE OR REPLACE FUNCTION get_gold_set_candidates(
  p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
  id_oferta       TEXT,
  titulo          TEXT,
  isco_code       TEXT,
  isco_label      TEXT,
  prioridad       INTEGER,
  razon           TEXT,
  regla_aplicada  TEXT,
  tiene_correccion_cynthia BOOLEAN
)
LANGUAGE sql STABLE
SECURITY DEFINER
SET statement_timeout = '10s'
AS $$
  WITH existing_gs AS (
    SELECT id_oferta FROM gold_set WHERE activo = TRUE
  ),

  -- P1: Correcciones de Cynthia (tienen ocupacion_corregida)
  p1 AS (
    SELECT
      d.id_oferta, d.titulo, d.isco_code, d.isco_label,
      1 AS prioridad,
      'Corrección validador' AS razon,
      d.regla_aplicada,
      TRUE AS tiene_correccion_cynthia
    FROM ofertas_dashboard d
    WHERE d.validacion_correcciones->>'ocupacion_corregida' IS NOT NULL
      AND d.id_oferta NOT IN (SELECT id_oferta FROM existing_gs)
  ),

  -- P2: Reglas nuevas R301-R323
  p2 AS (
    SELECT
      d.id_oferta, d.titulo, d.isco_code, d.isco_label,
      2 AS prioridad,
      'Regla nueva ' || d.regla_aplicada AS razon,
      d.regla_aplicada,
      (d.validacion_correcciones->>'ocupacion_corregida' IS NOT NULL) AS tiene_correccion_cynthia
    FROM ofertas_dashboard d
    WHERE d.regla_aplicada IN (
      'R301_ascensores','R302_supervisor_obra','R303_gerente_admin',
      'R304_torrista','R305_electromecanico','R306_mantenimiento_electrico',
      'R307_ingeniero_electronico','R308_lonas_toldos','R309_responsable_deposito',
      'R310_atencion_publico','R311_programador_produccion','R312_consultor_nomina',
      'R313_encargado_logistica','R315_metalurgico','R316_ventas_industrial',
      'R317_viajante','R318_operador_produccion','R319_corte_costura',
      'R320_ventas_telemarketing','R321_tecnico_instalador','R322_mecanico_industrial',
      'R323_atencion_publico'
    )
    AND d.id_oferta NOT IN (SELECT id_oferta FROM existing_gs)
    AND d.id_oferta NOT IN (SELECT id_oferta FROM p1)
  ),

  -- P3: Divergencia semántica (V27 activo)
  p3 AS (
    SELECT
      d.id_oferta, d.titulo, d.isco_code, d.isco_label,
      3 AS prioridad,
      'Divergencia semántica' AS razon,
      d.regla_aplicada,
      (d.validacion_correcciones->>'ocupacion_corregida' IS NOT NULL) AS tiene_correccion_cynthia
    FROM ofertas_dashboard d
    WHERE d.decision_metodo = 'regla_prioridad'
      AND d.id_oferta NOT IN (SELECT id_oferta FROM existing_gs)
      AND d.id_oferta NOT IN (SELECT id_oferta FROM p1)
      AND d.id_oferta NOT IN (SELECT id_oferta FROM p2)
    LIMIT 50
  ),

  -- P4: Perfil Argentino (ISCO con esco_argentino)
  p4 AS (
    SELECT
      d.id_oferta, d.titulo, d.isco_code, d.isco_label,
      4 AS prioridad,
      'Perfil Argentino' AS razon,
      d.regla_aplicada,
      (d.validacion_correcciones->>'ocupacion_corregida' IS NOT NULL) AS tiene_correccion_cynthia
    FROM ofertas_dashboard d
    WHERE d.isco_code IN (
      SELECT DISTINCT isco_code FROM esco_argentino WHERE isco_code IS NOT NULL
    )
    AND d.id_oferta NOT IN (SELECT id_oferta FROM existing_gs)
    AND d.id_oferta NOT IN (SELECT id_oferta FROM p1)
    AND d.id_oferta NOT IN (SELECT id_oferta FROM p2)
    AND d.id_oferta NOT IN (SELECT id_oferta FROM p3)
    LIMIT 50
  )

  SELECT * FROM p1
  UNION ALL SELECT * FROM p2
  UNION ALL SELECT * FROM p3
  UNION ALL SELECT * FROM p4
  ORDER BY prioridad, id_oferta
  LIMIT p_limit;
$$;

COMMENT ON FUNCTION get_gold_set_candidates IS 'M-10: Candidatas priorizadas para Gold Set (excluye existentes)';
