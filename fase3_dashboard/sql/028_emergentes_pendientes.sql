-- ============================================================
-- Bloque 9° — Workflow curación automática del perfil
-- PCA-3a: Tabla emergentes_pendientes
-- PCA-3b: RPC recalcular_emergentes()
-- PCA-6b: API support (list + approve/reject)
-- ============================================================

-- Tabla de skills emergentes detectadas automáticamente
CREATE TABLE IF NOT EXISTS emergentes_pendientes (
  id SERIAL PRIMARY KEY,
  skill_label TEXT NOT NULL,
  skill_uri TEXT,                       -- URI ESCO si matchea, null si es nueva
  isco_code TEXT NOT NULL,
  ocupacion_label TEXT,
  frecuencia_pct REAL NOT NULL,         -- % de ofertas de ese ISCO que mencionan esta skill
  ofertas_count INT NOT NULL DEFAULT 0, -- ofertas que la mencionan
  total_ofertas_isco INT NOT NULL DEFAULT 0, -- total ofertas de ese ISCO
  estado TEXT NOT NULL DEFAULT 'pendiente', -- pendiente, aprobada, rechazada
  fecha_deteccion TIMESTAMPTZ DEFAULT NOW(),
  fecha_resolucion TIMESTAMPTZ,
  resuelto_por TEXT,
  notas TEXT,
  UNIQUE(skill_label, isco_code)
);

CREATE INDEX IF NOT EXISTS idx_emergentes_estado ON emergentes_pendientes(estado);
CREATE INDEX IF NOT EXISTS idx_emergentes_isco ON emergentes_pendientes(isco_code);

-- RLS
ALTER TABLE emergentes_pendientes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica emergentes" ON emergentes_pendientes FOR SELECT USING (true);
CREATE POLICY "Service role modifica emergentes" ON emergentes_pendientes FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- RPC: recalcular_emergentes()
-- Cruza ofertas_skills × esco_argentino por ISCO
-- Detecta skills con frecuencia ≥30% que NO están en el perfil
-- ============================================================

CREATE OR REPLACE FUNCTION recalcular_emergentes()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '30s'
AS $$
DECLARE
  v_nuevas int := 0;
  v_actualizadas int := 0;
  v_result json;
BEGIN
  -- Calcular frecuencia de cada skill por ISCO
  -- Solo para ISCOs que tienen perfil en esco_argentino
  WITH skill_freq AS (
    SELECT
      os.preferred_label as skill_label,
      os.skill_uri,
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
      HAVING COUNT(*) >= 10  -- solo ISCOs con suficientes ofertas
    ) total ON od.isco_code = total.isco_code
    WHERE od.isco_code IS NOT NULL
      AND os.preferred_label IS NOT NULL
    GROUP BY os.preferred_label, os.skill_uri, od.isco_code, od.isco_label, total.total_ofertas
    HAVING ROUND(COUNT(DISTINCT os.id_oferta)::numeric / GREATEST(total.total_ofertas, 1) * 100, 1) >= 30
  ),
  -- Skills que ya están en el perfil consolidado
  perfil_skills AS (
    SELECT isco_code, jsonb_array_elements_text(skills_consolidadas) as skill
    FROM esco_argentino
    WHERE skills_consolidadas IS NOT NULL
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
  FROM skill_freq sf
  WHERE NOT EXISTS (
    SELECT 1 FROM perfil_skills ps
    WHERE ps.isco_code = sf.isco_code
      AND LOWER(ps.skill) = LOWER(sf.skill_label)
  )
  AND NOT EXISTS (
    SELECT 1 FROM emergentes_pendientes ep
    WHERE ep.skill_label = sf.skill_label
      AND ep.isco_code = sf.isco_code
      AND ep.estado IN ('aprobada', 'rechazada')  -- no re-detectar las ya procesadas
  )
  ON CONFLICT (skill_label, isco_code)
  DO UPDATE SET
    frecuencia_pct = EXCLUDED.frecuencia_pct,
    ofertas_count = EXCLUDED.ofertas_count,
    total_ofertas_isco = EXCLUDED.total_ofertas_isco,
    fecha_deteccion = NOW()
  WHERE emergentes_pendientes.estado = 'pendiente';  -- solo actualizar pendientes

  GET DIAGNOSTICS v_nuevas = ROW_COUNT;

  -- Contar actualizadas vs nuevas
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

-- ============================================================
-- RPC: get_emergentes(estado, isco_code)
-- Lista emergentes con filtros
-- ============================================================

CREATE OR REPLACE FUNCTION get_emergentes(
  p_estado text DEFAULT 'pendiente',
  p_isco text DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
BEGIN
  SELECT COALESCE(json_agg(row_to_json(e) ORDER BY e.frecuencia_pct DESC), '[]'::json)
  INTO v_result
  FROM (
    SELECT id, skill_label, skill_uri, isco_code, ocupacion_label,
           frecuencia_pct, ofertas_count, total_ofertas_isco,
           estado, fecha_deteccion, fecha_resolucion, resuelto_por, notas
    FROM emergentes_pendientes
    WHERE (p_estado IS NULL OR estado = p_estado)
      AND (p_isco IS NULL OR isco_code = p_isco)
    LIMIT 200
  ) e;

  RETURN v_result;
END;
$$;
