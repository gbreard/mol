-- ============================================================
-- RPC: preview_rule_impact(p_condicion jsonb)
-- Preview de impacto de una regla ANTES de guardarla
--
-- Recibe la condición de la regla y el ISCO propuesto.
-- Retorna: ofertas afectadas, ejemplos antes/después, conflictos.
-- ============================================================

CREATE OR REPLACE FUNCTION preview_rule_impact(
  p_titulo_contiene text DEFAULT NULL,
  p_titulo_contiene_alguno text[] DEFAULT NULL,
  p_forzar_isco text DEFAULT NULL,
  p_area text DEFAULT NULL,
  p_limit int DEFAULT 10
)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_count bigint;
  v_ejemplos json;
  v_conflictos json;
  v_isco_actual json;
BEGIN
  -- Contar ofertas que matchean la condición
  SELECT COUNT(*)
  INTO v_count
  FROM ofertas_dashboard
  WHERE
    CASE
      WHEN p_titulo_contiene IS NOT NULL THEN
        LOWER(titulo_limpio) LIKE '%' || LOWER(p_titulo_contiene) || '%'
        OR LOWER(titulo) LIKE '%' || LOWER(p_titulo_contiene) || '%'
      WHEN p_titulo_contiene_alguno IS NOT NULL THEN
        EXISTS (
          SELECT 1 FROM unnest(p_titulo_contiene_alguno) kw
          WHERE LOWER(titulo_limpio) LIKE '%' || LOWER(kw) || '%'
             OR LOWER(titulo) LIKE '%' || LOWER(kw) || '%'
        )
      ELSE FALSE
    END;

  -- Ejemplos de ofertas afectadas (antes/después)
  SELECT COALESCE(json_agg(row_to_json(e)), '[]'::json)
  INTO v_ejemplos
  FROM (
    SELECT
      id_oferta,
      titulo,
      titulo_limpio,
      isco_code as isco_actual,
      isco_label as label_actual,
      p_forzar_isco as isco_nuevo,
      CASE WHEN isco_code = p_forzar_isco THEN 'SIN CAMBIO' ELSE 'CAMBIA' END as estado,
      decision_metodo as metodo_actual,
      provincia
    FROM ofertas_dashboard
    WHERE
      CASE
        WHEN p_titulo_contiene IS NOT NULL THEN
          LOWER(titulo_limpio) LIKE '%' || LOWER(p_titulo_contiene) || '%'
          OR LOWER(titulo) LIKE '%' || LOWER(p_titulo_contiene) || '%'
        WHEN p_titulo_contiene_alguno IS NOT NULL THEN
          EXISTS (
            SELECT 1 FROM unnest(p_titulo_contiene_alguno) kw
            WHERE LOWER(titulo_limpio) LIKE '%' || LOWER(kw) || '%'
               OR LOWER(titulo) LIKE '%' || LOWER(kw) || '%'
          )
        ELSE FALSE
      END
    ORDER BY fecha_publicacion DESC NULLS LAST
    LIMIT p_limit
  ) e;

  -- Distribución de ISCO actual de las ofertas afectadas
  SELECT COALESCE(json_agg(row_to_json(d)), '[]'::json)
  INTO v_isco_actual
  FROM (
    SELECT isco_code, isco_label, COUNT(*) as cantidad
    FROM ofertas_dashboard
    WHERE
      CASE
        WHEN p_titulo_contiene IS NOT NULL THEN
          LOWER(titulo_limpio) LIKE '%' || LOWER(p_titulo_contiene) || '%'
          OR LOWER(titulo) LIKE '%' || LOWER(p_titulo_contiene) || '%'
        WHEN p_titulo_contiene_alguno IS NOT NULL THEN
          EXISTS (
            SELECT 1 FROM unnest(p_titulo_contiene_alguno) kw
            WHERE LOWER(titulo_limpio) LIKE '%' || LOWER(kw) || '%'
               OR LOWER(titulo) LIKE '%' || LOWER(kw) || '%'
          )
        ELSE FALSE
      END
    GROUP BY isco_code, isco_label
    ORDER BY cantidad DESC
    LIMIT 10
  ) d;

  -- Ofertas que ya tienen el ISCO correcto (no cambian)
  -- y ofertas que cambiarían
  v_result := json_build_object(
    'total_afectadas', v_count,
    'cambiarian', (
      SELECT COUNT(*) FROM ofertas_dashboard
      WHERE (
        CASE
          WHEN p_titulo_contiene IS NOT NULL THEN
            LOWER(titulo_limpio) LIKE '%' || LOWER(p_titulo_contiene) || '%'
            OR LOWER(titulo) LIKE '%' || LOWER(p_titulo_contiene) || '%'
          WHEN p_titulo_contiene_alguno IS NOT NULL THEN
            EXISTS (
              SELECT 1 FROM unnest(p_titulo_contiene_alguno) kw
              WHERE LOWER(titulo_limpio) LIKE '%' || LOWER(kw) || '%'
                 OR LOWER(titulo) LIKE '%' || LOWER(kw) || '%'
            )
          ELSE FALSE
        END
      ) AND (isco_code IS NULL OR isco_code != p_forzar_isco)
    ),
    'ya_correctas', (
      SELECT COUNT(*) FROM ofertas_dashboard
      WHERE (
        CASE
          WHEN p_titulo_contiene IS NOT NULL THEN
            LOWER(titulo_limpio) LIKE '%' || LOWER(p_titulo_contiene) || '%'
            OR LOWER(titulo) LIKE '%' || LOWER(p_titulo_contiene) || '%'
          WHEN p_titulo_contiene_alguno IS NOT NULL THEN
            EXISTS (
              SELECT 1 FROM unnest(p_titulo_contiene_alguno) kw
              WHERE LOWER(titulo_limpio) LIKE '%' || LOWER(kw) || '%'
                 OR LOWER(titulo) LIKE '%' || LOWER(kw) || '%'
            )
          ELSE FALSE
        END
      ) AND isco_code = p_forzar_isco
    ),
    'distribucion_isco_actual', v_isco_actual,
    'ejemplos', v_ejemplos
  );

  RETURN v_result;
END;
$$;

-- ============================================================
-- RPC: get_rule_suggestions()
-- Analiza errores de validación y correcciones humanas
-- para sugerir reglas nuevas
-- ============================================================

CREATE OR REPLACE FUNCTION get_rule_suggestions(p_limit int DEFAULT 10)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '10s'
AS $$
DECLARE
  v_result json;
BEGIN
  -- Buscar patrones en ofertas con issues de corrección de ISCO
  -- (issues tipo "Correccion" creados por humanos)
  SELECT COALESCE(json_agg(row_to_json(s) ORDER BY s.ofertas_afectadas DESC), '[]'::json)
  INTO v_result
  FROM (
    -- Patrón 1: Issues de corrección agrupados por título similar
    SELECT
      'correccion_titulo' as tipo_sugerencia,
      LOWER(COALESCE(od.titulo_limpio, od.titulo)) as patron_titulo,
      i.valor_esperado as isco_sugerido,
      od.isco_code as isco_actual,
      od.isco_label as label_actual,
      COUNT(DISTINCT i.id_oferta) as ofertas_afectadas,
      COUNT(DISTINCT i.id) as correcciones,
      json_agg(DISTINCT od.titulo) as titulos_ejemplo,
      MAX(i.created_at) as ultima_correccion,
      MAX(i.autor_nombre) as corregido_por
    FROM issues i
    JOIN ofertas_dashboard od ON od.id_oferta = i.id_oferta
    WHERE i.estado = 'pendiente'
      AND i.tipo = 'correccion'
      AND i.valor_esperado IS NOT NULL
      AND i.valor_esperado ~ '^\d{4}$'  -- es un ISCO code
      AND i.autor_email != 'auto-validator@mol.gob.ar'
    GROUP BY LOWER(COALESCE(od.titulo_limpio, od.titulo)), i.valor_esperado, od.isco_code, od.isco_label
    HAVING COUNT(DISTINCT i.id_oferta) >= 2  -- al menos 2 correcciones similares

    UNION ALL

    -- Patrón 2: Títulos frecuentes sin regla (matcheados solo por semántico con score bajo)
    SELECT
      'semantico_bajo' as tipo_sugerencia,
      LOWER(COALESCE(titulo_limpio, titulo)) as patron_titulo,
      isco_code as isco_sugerido,
      isco_code as isco_actual,
      isco_label as label_actual,
      COUNT(*) as ofertas_afectadas,
      0 as correcciones,
      json_agg(DISTINCT titulo) as titulos_ejemplo,
      MAX(fecha_publicacion::text) as ultima_correccion,
      NULL as corregido_por
    FROM ofertas_dashboard
    WHERE decision_metodo = 'semantico_default'
      AND occupation_match_score < 0.5
      AND isco_code IS NOT NULL
    GROUP BY LOWER(COALESCE(titulo_limpio, titulo)), isco_code, isco_label
    HAVING COUNT(*) >= 5  -- al menos 5 ofertas con el mismo patrón
    LIMIT p_limit
  ) s
  LIMIT p_limit;

  RETURN v_result;
END;
$$;
