-- ============================================
-- Tablas de Logs y Auditoría para /admin/logs
-- ============================================

-- 1. Tabla audit_log (registro de acciones de usuarios)
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  usuario_id UUID REFERENCES auth.users(id),
  organizacion_id UUID,  -- Para multi-tenancy futuro
  accion TEXT NOT NULL,  -- login, logout, create, update, delete, view, export
  recurso TEXT NOT NULL, -- ofertas, issues, usuarios, etc.
  recurso_id TEXT,       -- ID del recurso afectado
  detalle JSONB,         -- Datos adicionales
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_audit_log_usuario ON audit_log(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_accion ON audit_log(accion);

-- 2. Tabla eventos_uso (analytics de navegación)
CREATE TABLE IF NOT EXISTS eventos_uso (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  usuario_id UUID REFERENCES auth.users(id),
  evento TEXT NOT NULL,     -- page_view, filter_change, export_click, etc.
  categoria TEXT NOT NULL,  -- navigation, filter, export, search
  metadata JSONB,           -- Datos del evento (página, filtros, etc.)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_eventos_uso_usuario ON eventos_uso(usuario_id);
CREATE INDEX IF NOT EXISTS idx_eventos_uso_created ON eventos_uso(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eventos_uso_categoria ON eventos_uso(categoria);

-- 3. RLS (Row Level Security) - Admins pueden ver todo
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_uso ENABLE ROW LEVEL SECURITY;

-- Política: Admins pueden leer
CREATE POLICY admin_read_audit_log ON audit_log
  FOR SELECT
  TO authenticated
  USING (
    (SELECT role FROM auth.users WHERE id = auth.uid()) IN ('admin', 'super_admin')
    OR
    EXISTS (SELECT 1 FROM auth.users u WHERE u.id = auth.uid() AND u.raw_user_meta_data->>'role' IN ('admin', 'super_admin'))
  );

CREATE POLICY admin_read_eventos ON eventos_uso
  FOR SELECT
  TO authenticated
  USING (
    (SELECT role FROM auth.users WHERE id = auth.uid()) IN ('admin', 'super_admin')
    OR
    EXISTS (SELECT 1 FROM auth.users u WHERE u.id = auth.uid() AND u.raw_user_meta_data->>'role' IN ('admin', 'super_admin'))
  );

-- Política: El sistema puede insertar (desde Edge Functions o Service Role)
CREATE POLICY system_insert_audit_log ON audit_log
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY system_insert_eventos ON eventos_uso
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- 4. Función para registrar acciones (usar desde código)
CREATE OR REPLACE FUNCTION log_action(
  p_accion TEXT,
  p_recurso TEXT,
  p_recurso_id TEXT DEFAULT NULL,
  p_detalle JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
  INSERT INTO audit_log (usuario_id, accion, recurso, recurso_id, detalle)
  VALUES (auth.uid(), p_accion, p_recurso, p_recurso_id, p_detalle);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Ejemplo de inserción (para testing)
-- INSERT INTO audit_log (usuario_id, accion, recurso, detalle)
-- VALUES (auth.uid(), 'login', 'auth', '{"method": "email"}');

-- 6. Verificar
SELECT 'audit_log' as tabla, COUNT(*) FROM audit_log
UNION ALL
SELECT 'eventos_uso' as tabla, COUNT(*) FROM eventos_uso;
