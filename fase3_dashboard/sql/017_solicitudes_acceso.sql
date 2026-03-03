-- 017: Tabla solicitudes_acceso + RPCs
-- Ejecutar en Supabase SQL Editor

-- ============================================================
-- TABLA: solicitudes_acceso
-- ============================================================
CREATE TABLE IF NOT EXISTS solicitudes_acceso (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  nombre text NOT NULL,
  organizacion text,
  motivo text NOT NULL,
  estado text NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente', 'aprobada', 'rechazada')),
  revisado_por text,           -- email del admin que revisó
  revisado_at timestamptz,
  notas_admin text,
  created_at timestamptz DEFAULT now()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes_acceso(estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_user_id ON solicitudes_acceso(user_id);

-- ============================================================
-- RLS: Row Level Security
-- ============================================================
ALTER TABLE solicitudes_acceso ENABLE ROW LEVEL SECURITY;

-- Usuarios leen sus propias solicitudes
CREATE POLICY "Users read own solicitudes"
  ON solicitudes_acceso FOR SELECT
  USING (auth.uid() = user_id);

-- Usuarios crean sus propias solicitudes
CREATE POLICY "Users insert own solicitudes"
  ON solicitudes_acceso FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Admins leen todas las solicitudes
CREATE POLICY "Admins read all solicitudes"
  ON solicitudes_acceso FOR SELECT
  USING (
    (auth.jwt() -> 'user_metadata' ->> 'role') IN ('admin', 'super_admin')
  );

-- Admins actualizan cualquier solicitud
CREATE POLICY "Admins update solicitudes"
  ON solicitudes_acceso FOR UPDATE
  USING (
    (auth.jwt() -> 'user_metadata' ->> 'role') IN ('admin', 'super_admin')
  );

-- ============================================================
-- RPC: crear_solicitud_acceso
-- ============================================================
CREATE OR REPLACE FUNCTION crear_solicitud_acceso(
  p_nombre text,
  p_organizacion text DEFAULT NULL,
  p_motivo text DEFAULT ''
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid;
  v_email text;
  v_existing_id uuid;
  v_new_id uuid;
BEGIN
  -- Obtener datos del usuario autenticado
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'No autenticado';
  END IF;

  v_email := (auth.jwt() ->> 'email');

  -- Verificar que no haya solicitud pendiente
  SELECT id INTO v_existing_id
  FROM solicitudes_acceso
  WHERE user_id = v_user_id AND estado = 'pendiente'
  LIMIT 1;

  IF v_existing_id IS NOT NULL THEN
    RAISE EXCEPTION 'Ya existe una solicitud pendiente (id: %)', v_existing_id;
  END IF;

  -- Crear la solicitud
  INSERT INTO solicitudes_acceso (user_id, email, nombre, organizacion, motivo)
  VALUES (v_user_id, v_email, p_nombre, p_organizacion, p_motivo)
  RETURNING id INTO v_new_id;

  RETURN v_new_id;
END;
$$;

-- ============================================================
-- RPC: aprobar_solicitud (solo admins)
-- ============================================================
CREATE OR REPLACE FUNCTION aprobar_solicitud(
  p_solicitud_id uuid,
  p_notas text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_role text;
  v_admin_email text;
BEGIN
  -- Verificar que el caller es admin
  v_role := (auth.jwt() -> 'user_metadata' ->> 'role');
  IF v_role NOT IN ('admin', 'super_admin') THEN
    RAISE EXCEPTION 'Solo admins pueden aprobar solicitudes';
  END IF;

  v_admin_email := (auth.jwt() ->> 'email');

  UPDATE solicitudes_acceso
  SET estado = 'aprobada',
      revisado_por = v_admin_email,
      revisado_at = now(),
      notas_admin = p_notas
  WHERE id = p_solicitud_id
    AND estado = 'pendiente';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Solicitud no encontrada o ya procesada';
  END IF;
END;
$$;

-- ============================================================
-- RPC: rechazar_solicitud (solo admins)
-- ============================================================
CREATE OR REPLACE FUNCTION rechazar_solicitud(
  p_solicitud_id uuid,
  p_notas text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_role text;
  v_admin_email text;
BEGIN
  -- Verificar que el caller es admin
  v_role := (auth.jwt() -> 'user_metadata' ->> 'role');
  IF v_role NOT IN ('admin', 'super_admin') THEN
    RAISE EXCEPTION 'Solo admins pueden rechazar solicitudes';
  END IF;

  v_admin_email := (auth.jwt() ->> 'email');

  UPDATE solicitudes_acceso
  SET estado = 'rechazada',
      revisado_por = v_admin_email,
      revisado_at = now(),
      notas_admin = p_notas
  WHERE id = p_solicitud_id
    AND estado = 'pendiente';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Solicitud no encontrada o ya procesada';
  END IF;
END;
$$;
