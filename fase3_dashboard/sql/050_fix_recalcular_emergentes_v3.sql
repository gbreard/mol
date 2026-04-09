-- Migration 050: Fix recalcular_emergentes() v3
-- E2.1 del SPEC Motor de Conocimiento v1.3
--
-- Bugs corregidos:
--   1. isco_code era NULL en esco_argentino → ahora poblado (vía script Python)
--   2. perfil_skills usaba jsonb_array_elements_text() sobre objetos JSONB
--      → convertía el objeto entero a texto, nunca matcheaba con skill_label
--   3. El campo URI en skills_consolidadas tiene dos nombres: 'uri' (esco_common)
--      y 'esco_uri' (mol_approved) → usar COALESCE para ambos
--
-- Cambios:
--   - perfil_skills ahora usa jsonb_array_elements() + ->> para extraer label y uri
--   - Comparación por URI (más confiable) además de label (fallback)
--   - Usa COALESCE(elem->>'esco_uri', elem->>'uri') para ambos nombres de campo

CREATE OR REPLACE FUNCTION recalcular_emergentes()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '30s'
AS $$
DECLARE
  v_nuevas int := 0;
  v_result json;
BEGIN
  -- Calcular frecuencia de cada skill por ISCO
  -- M-08b: COALESCE agrupa variantes por equivalencia (canonical_label)
  WITH skill_freq AS (
    SELECT
      COALESCE(os.canonical_label, os.preferred_label) as skill_label,
      COALESCE(os.equivalence_id, os.skill_uri) as skill_key,
      MIN(os.skill_uri) as skill_uri,
      od.isco_code,
      od.isco_label as ocupacion_label,
      COUNT(DISTINCT os.id_oferta) as ofertas_count,
      total.total_ofertas,
      ROUND(COUNT(DISTINCT os.id_oferta)::numeric / GREATEST(total.total_ofertas, 1) * 100, 1) as frecuencia_pct
    FROM ofertas_skills os
    JOIN ofertas_dashboard od ON os.id_oferta = od.id_oferta
    JOIN (
      SELECT isco_code, COUNT(*) as total_ofertas
      FROM ofertas_dashboard
      WHERE isco_code IS NOT NULL
      GROUP BY isco_code
      HAVING COUNT(*) >= 10
    ) total ON od.isco_code = total.isco_code
    WHERE od.isco_code IS NOT NULL
      AND os.preferred_label IS NOT NULL
    GROUP BY COALESCE(os.canonical_label, os.preferred_label),
             COALESCE(os.equivalence_id, os.skill_uri),
             od.isco_code, od.isco_label, total.total_ofertas
    HAVING ROUND(COUNT(DISTINCT os.id_oferta)::numeric / GREATEST(total.total_ofertas, 1) * 100, 1) >= 30
  ),
  -- FIX v3: Deduplicar por (skill_label, isco_code) para evitar
  -- "ON CONFLICT DO UPDATE cannot affect row a second time".
  -- Distintos skill_key pueden mapear al mismo label+isco.
  skill_freq_dedup AS (
    SELECT DISTINCT ON (skill_label, isco_code)
      skill_label, skill_uri, isco_code, ocupacion_label,
      frecuencia_pct, ofertas_count, total_ofertas
    FROM skill_freq
    ORDER BY skill_label, isco_code, frecuencia_pct DESC
  ),
  -- Skills que ya están en el perfil consolidado
  -- FIX v3: extraer label y uri correctamente del JSONB
  -- skills_consolidadas es JSONB array de objetos con campos:
  --   label (siempre), uri (esco_common) o esco_uri (mol_approved)
  perfil_skills AS (
    SELECT
      ea.isco_code,
      elem->>'label' as skill_label,
      COALESCE(elem->>'esco_uri', elem->>'uri') as skill_uri
    FROM esco_argentino ea,
    jsonb_array_elements(ea.skills_consolidadas) as elem
    WHERE ea.skills_consolidadas IS NOT NULL
      AND ea.isco_code IS NOT NULL
  )
  -- Insertar/actualizar emergentes que NO están en el perfil
  INSERT INTO emergentes_pendientes (skill_label, skill_uri, isco_code, ocupacion_label, frecuencia_pct, ofertas_count, total_ofertas_isco, estado, fecha_deteccion)
  SELECT
    sf.skill_label,
    sf.skill_uri,
    sf.isco_code,
    sf.ocupacion_label,
    sf.frecuencia_pct,
    sf.ofertas_count,
    sf.total_ofertas,
    'pendiente',
    NOW()
  FROM skill_freq_dedup sf
  WHERE NOT EXISTS (
    -- Comparar por URI (más confiable) O por label (fallback)
    SELECT 1 FROM perfil_skills ps
    WHERE ps.isco_code = sf.isco_code
      AND (
        ps.skill_uri = sf.skill_uri
        OR LOWER(ps.skill_label) = LOWER(sf.skill_label)
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM emergentes_pendientes ep
    WHERE ep.skill_label = sf.skill_label
      AND ep.isco_code = sf.isco_code
      AND ep.estado IN ('aprobada', 'rechazada')
  )
  ON CONFLICT (skill_label, isco_code)
  DO UPDATE SET
    frecuencia_pct = EXCLUDED.frecuencia_pct,
    ofertas_count = EXCLUDED.ofertas_count,
    total_ofertas_isco = EXCLUDED.total_ofertas_isco,
    fecha_deteccion = NOW()
  WHERE emergentes_pendientes.estado = 'pendiente';

  GET DIAGNOSTICS v_nuevas = ROW_COUNT;

  v_result := json_build_object(
    'nuevas_o_actualizadas', v_nuevas,
    'total_pendientes', (SELECT COUNT(*) FROM emergentes_pendientes WHERE estado = 'pendiente'),
    'total_aprobadas', (SELECT COUNT(*) FROM emergentes_pendientes WHERE estado = 'aprobada'),
    'total_rechazadas', (SELECT COUNT(*) FROM emergentes_pendientes WHERE estado = 'rechazada'),
    'timestamp', NOW()
  );

  RETURN v_result;
END;
$$;
