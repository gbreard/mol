-- Migration 057: E2.4 — Downstream triggers para aprobación de emergentes
--
-- 1. Tabla approved_training_pairs: almacena pares contrastivos generados al aprobar
-- 2. RPC aprobar_emergente_con_triggers(): ejecuta los 4 triggers en una transacción

-- ============================================================
-- 1. TABLA approved_training_pairs
-- ============================================================

CREATE TABLE IF NOT EXISTS approved_training_pairs (
  id SERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  positive TEXT NOT NULL,
  negatives JSONB NOT NULL DEFAULT '[]',
  occupation_context TEXT,
  occupation_label TEXT,
  source TEXT NOT NULL DEFAULT 'emergente_aprobada',
  confianza TEXT NOT NULL DEFAULT 'alta',
  split TEXT NOT NULL DEFAULT 'train',
  emergente_id INTEGER REFERENCES emergentes_pendientes(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by TEXT
);

COMMENT ON TABLE approved_training_pairs IS 'Training pairs contrastivos generados al aprobar emergentes (E2.4)';

ALTER TABLE approved_training_pairs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "approved_training_pairs_read" ON approved_training_pairs
  FOR SELECT USING (true);
CREATE POLICY "approved_training_pairs_write" ON approved_training_pairs
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- ============================================================
-- 2. RPC aprobar_emergente_con_triggers
-- ============================================================
-- Ejecuta todos los triggers E2.4 en una sola transacción:
-- T1: Inserta skill en esco_argentino.skills_consolidadas
-- T2: Genera training pair (negatives via expand_skills_semantic)
-- T3: Invalida cache argentino (pipeline_commands)
-- T4: Alerta si >= 10 aprobaciones desde último corte

CREATE OR REPLACE FUNCTION aprobar_emergente_con_triggers(
  p_emergente_id INTEGER,
  p_admin_email TEXT DEFAULT 'admin',
  p_notas TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '15s'
AS $$
DECLARE
  v_emergente RECORD;
  v_occ_uri TEXT;
  v_skill_entry JSONB;
  v_current_skills JSONB;
  v_negatives JSONB;
  v_training_pair_id INTEGER;
  v_aprobadas_desde_corte INTEGER;
  v_ultimo_corte TIMESTAMPTZ;
  v_alerta_msg TEXT;
  v_result JSONB;
BEGIN
  -- Obtener datos de la emergente
  SELECT * INTO v_emergente
  FROM emergentes_pendientes
  WHERE id = p_emergente_id AND estado = 'pendiente';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Emergente % no encontrada o no está pendiente', p_emergente_id;
  END IF;

  -- Marcar como aprobada
  UPDATE emergentes_pendientes SET
    estado = 'aprobada',
    fecha_resolucion = NOW(),
    resuelto_por = p_admin_email,
    notas = p_notas
  WHERE id = p_emergente_id;

  -- ============================================================
  -- TRIGGER 1: Insertar skill en esco_argentino
  -- ============================================================

  -- Buscar la ocupación en esco_argentino por isco_code
  SELECT esco_occupation_uri INTO v_occ_uri
  FROM esco_argentino
  WHERE isco_code = v_emergente.isco_code
  LIMIT 1;

  IF v_occ_uri IS NOT NULL THEN
    -- Construir la entrada de skill
    v_skill_entry := jsonb_build_object(
      'esco_uri', v_emergente.skill_uri,
      'label_original', v_emergente.skill_label,
      'label_normalized', LOWER(v_emergente.skill_label),
      'source', 'mol_approved',
      'frequency', ROUND(v_emergente.frecuencia_pct)::INTEGER,
      'percentage', ROUND(v_emergente.frecuencia_pct),
      'approved_at', NOW()::TEXT,
      'approved_by', p_admin_email
    );

    -- Obtener skills actuales
    SELECT skills_consolidadas INTO v_current_skills
    FROM esco_argentino
    WHERE esco_occupation_uri = v_occ_uri;

    -- Append skill (no duplicar si ya existe por URI)
    IF NOT EXISTS (
      SELECT 1 FROM jsonb_array_elements(COALESCE(v_current_skills, '[]'::jsonb)) elem
      WHERE elem->>'esco_uri' = v_emergente.skill_uri
        OR elem->>'label_normalized' = LOWER(v_emergente.skill_label)
    ) THEN
      UPDATE esco_argentino SET
        skills_consolidadas = COALESCE(v_current_skills, '[]'::jsonb) || jsonb_build_array(v_skill_entry),
        total_skills = COALESCE(total_skills, 0) + 1,
        skills_from_argentina = COALESCE(skills_from_argentina, 0) + 1,
        updated_at = NOW(),
        updated_by = p_admin_email
      WHERE esco_occupation_uri = v_occ_uri;
    END IF;
  END IF;

  -- ============================================================
  -- TRIGGER 2: Generar training pair con hard negatives
  -- ============================================================

  -- Obtener negatives via expand_skills_semantic (solo si skill tiene URI)
  v_negatives := '[]'::JSONB;
  IF v_emergente.skill_uri IS NOT NULL THEN
    SELECT COALESCE(jsonb_agg(
      jsonb_build_object('uri', m.skill_uri, 'label', m.skill_label, 'similarity', m.similarity)
    ), '[]'::JSONB)
    INTO v_negatives
    FROM expand_skills_semantic(
      v_emergente.skill_uri, 0.40, 8, v_occ_uri
    ) m
    WHERE m.is_argentino = FALSE
    LIMIT 3;
  END IF;

  INSERT INTO approved_training_pairs (
    query, positive, negatives, occupation_context, occupation_label,
    source, emergente_id, created_by
  ) VALUES (
    v_emergente.skill_label,
    COALESCE(v_emergente.skill_uri, '') || ' ' || v_emergente.skill_label,
    v_negatives,
    v_occ_uri,
    v_emergente.ocupacion_label,
    'emergente_aprobada',
    p_emergente_id,
    p_admin_email
  ) RETURNING id INTO v_training_pair_id;

  -- ============================================================
  -- TRIGGER 3: Invalidar cache argentino
  -- ============================================================

  INSERT INTO pipeline_commands (comando, params, estado, creado_por)
  VALUES (
    'invalidar_cache_argentino',
    jsonb_build_object(
      'emergente_id', p_emergente_id,
      'skill_label', v_emergente.skill_label,
      'isco_code', v_emergente.isco_code
    ),
    'pendiente',
    p_admin_email
  );

  -- ============================================================
  -- TRIGGER 4: Alerta si >= 10 aprobaciones desde último corte
  -- ============================================================

  SELECT created_at INTO v_ultimo_corte
  FROM perfil_argentino_versiones
  WHERE activa = TRUE
  LIMIT 1;

  SELECT COUNT(*) INTO v_aprobadas_desde_corte
  FROM emergentes_pendientes
  WHERE estado = 'aprobada'
    AND fecha_resolucion > COALESCE(v_ultimo_corte, '1970-01-01'::TIMESTAMPTZ);

  v_alerta_msg := NULL;
  IF v_aprobadas_desde_corte >= 10 THEN
    v_alerta_msg := format(
      'Hay %s skills aprobadas desde el último corte. Considerá crear una nueva versión del Perfil Argentino.',
      v_aprobadas_desde_corte
    );
  END IF;

  -- ============================================================
  -- Resultado
  -- ============================================================

  v_result := jsonb_build_object(
    'emergente_id', p_emergente_id,
    'skill_label', v_emergente.skill_label,
    'estado', 'aprobada',
    'trigger_1_esco_argentino', v_occ_uri IS NOT NULL,
    'trigger_2_training_pair_id', v_training_pair_id,
    'trigger_3_cache_invalidated', TRUE,
    'trigger_4_alerta', v_alerta_msg,
    'aprobadas_desde_corte', v_aprobadas_desde_corte
  );

  RETURN v_result;
END;
$$;

COMMENT ON FUNCTION aprobar_emergente_con_triggers IS 'E2.4: Aprueba emergente y ejecuta 4 triggers downstream en una transacción';
