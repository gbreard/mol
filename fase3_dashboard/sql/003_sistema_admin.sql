-- ============================================================================
-- 003_sistema_admin.sql
-- Sistema de administracion: invitaciones, auditoria, exportaciones, alertas
-- ============================================================================

-- Tabla de invitaciones
CREATE TABLE IF NOT EXISTS invitaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    organizacion_id UUID REFERENCES organizaciones(id),
    rol TEXT NOT NULL DEFAULT 'lector',
    token TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    invitado_por UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',
    usado BOOLEAN DEFAULT FALSE,
    usado_at TIMESTAMPTZ,
    CONSTRAINT invitaciones_rol_valido CHECK (rol IN ('admin', 'analista', 'lector'))
);

-- RLS para invitaciones
ALTER TABLE invitaciones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins pueden crear invitaciones"
ON invitaciones FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1 FROM usuarios u
        WHERE u.auth_id = auth.uid()
        AND (u.rol = 'platform_admin' OR u.rol = 'admin')
    )
);

CREATE POLICY "Ver invitaciones de mi org"
ON invitaciones FOR SELECT
TO authenticated
USING (
    organizacion_id IN (
        SELECT organizacion_id FROM usuarios WHERE auth_id = auth.uid()
    )
    OR EXISTS (
        SELECT 1 FROM usuarios WHERE auth_id = auth.uid() AND rol = 'platform_admin'
    )
);

CREATE POLICY "Actualizar invitaciones de mi org"
ON invitaciones FOR UPDATE
TO authenticated
USING (
    organizacion_id IN (
        SELECT organizacion_id FROM usuarios WHERE auth_id = auth.uid()
    )
);

-- Permitir lectura publica de invitaciones por token (para registro)
CREATE POLICY "Ver invitacion por token"
ON invitaciones FOR SELECT
TO anon
USING (usado = FALSE AND expires_at > NOW());

-- ============================================================================
-- Log de auditoria
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id),
    organizacion_id UUID REFERENCES organizaciones(id),
    accion TEXT NOT NULL,  -- LOGIN, LOGOUT, EXPORT, SEARCH, INVITAR, CREATE_USER, etc.
    recurso TEXT,          -- Tipo de recurso afectado
    recurso_id TEXT,       -- ID del recurso afectado
    detalle JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_audit_log_usuario ON audit_log(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_organizacion ON audit_log(organizacion_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_accion ON audit_log(accion);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- RLS para audit_log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "SuperAdmin ve todo el audit log"
ON audit_log FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM usuarios WHERE auth_id = auth.uid() AND rol = 'platform_admin'
    )
);

CREATE POLICY "Admin ve audit log de su org"
ON audit_log FOR SELECT
TO authenticated
USING (
    organizacion_id IN (
        SELECT organizacion_id FROM usuarios
        WHERE auth_id = auth.uid() AND rol IN ('admin', 'platform_admin')
    )
);

CREATE POLICY "Insertar en audit log"
ON audit_log FOR INSERT
TO authenticated
WITH CHECK (true);

-- ============================================================================
-- Registro de exportaciones
-- ============================================================================
CREATE TABLE IF NOT EXISTS exportaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) NOT NULL,
    organizacion_id UUID REFERENCES organizaciones(id),
    tipo TEXT NOT NULL,  -- xlsx, csv, pdf
    nombre_archivo TEXT,
    filtros_aplicados JSONB,
    filas_exportadas INTEGER,
    tamano_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exportaciones_usuario ON exportaciones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_exportaciones_org ON exportaciones(organizacion_id);
CREATE INDEX IF NOT EXISTS idx_exportaciones_created_at ON exportaciones(created_at DESC);

-- RLS para exportaciones
ALTER TABLE exportaciones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver mis exportaciones"
ON exportaciones FOR SELECT
TO authenticated
USING (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
    OR organizacion_id IN (
        SELECT organizacion_id FROM usuarios
        WHERE auth_id = auth.uid() AND rol IN ('admin', 'platform_admin')
    )
);

CREATE POLICY "Crear mis exportaciones"
ON exportaciones FOR INSERT
TO authenticated
WITH CHECK (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

-- ============================================================================
-- Alertas configurables
-- ============================================================================
CREATE TABLE IF NOT EXISTS alertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) NOT NULL,
    organizacion_id UUID REFERENCES organizaciones(id),
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,  -- nuevas_ofertas, umbral_ocupacion, keyword_match, etc.
    configuracion JSONB NOT NULL,  -- Parametros especificos del tipo de alerta
    activa BOOLEAN DEFAULT TRUE,
    frecuencia TEXT DEFAULT 'diaria',  -- diaria, semanal, inmediata
    ultima_ejecucion TIMESTAMPTZ,
    ultimo_resultado JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alertas_usuario ON alertas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_alertas_activas ON alertas(activa) WHERE activa = TRUE;

-- RLS para alertas
ALTER TABLE alertas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ver mis alertas"
ON alertas FOR SELECT
TO authenticated
USING (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

CREATE POLICY "Crear mis alertas"
ON alertas FOR INSERT
TO authenticated
WITH CHECK (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

CREATE POLICY "Actualizar mis alertas"
ON alertas FOR UPDATE
TO authenticated
USING (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

CREATE POLICY "Eliminar mis alertas"
ON alertas FOR DELETE
TO authenticated
USING (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

-- ============================================================================
-- Busquedas para tracking de uso
-- ============================================================================
CREATE TABLE IF NOT EXISTS busquedas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) NOT NULL,
    organizacion_id UUID REFERENCES organizaciones(id),
    termino TEXT,
    filtros JSONB,
    resultados_count INTEGER,
    duracion_ms INTEGER,
    pagina TEXT,  -- Desde que pagina se hizo la busqueda
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_busquedas_usuario ON busquedas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_busquedas_org ON busquedas(organizacion_id);
CREATE INDEX IF NOT EXISTS idx_busquedas_created_at ON busquedas(created_at DESC);

-- RLS para busquedas
ALTER TABLE busquedas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admin ve busquedas de su org"
ON busquedas FOR SELECT
TO authenticated
USING (
    organizacion_id IN (
        SELECT organizacion_id FROM usuarios
        WHERE auth_id = auth.uid() AND rol IN ('admin', 'platform_admin')
    )
);

CREATE POLICY "Registrar mis busquedas"
ON busquedas FOR INSERT
TO authenticated
WITH CHECK (
    usuario_id = (SELECT id FROM usuarios WHERE auth_id = auth.uid())
);

-- ============================================================================
-- Vistas para metricas
-- ============================================================================

-- Vista: metricas generales del sistema (para superadmin)
CREATE OR REPLACE VIEW v_metricas_sistema AS
SELECT
    (SELECT COUNT(*) FROM ofertas_dashboard) as ofertas_totales,
    (SELECT COUNT(*) FROM usuarios) as usuarios_totales,
    (SELECT COUNT(*) FROM organizaciones) as organizaciones_totales,
    (SELECT COUNT(*) FROM busquedas WHERE created_at > NOW() - INTERVAL '30 days') as busquedas_mes,
    (SELECT COUNT(*) FROM exportaciones WHERE created_at > NOW() - INTERVAL '30 days') as exports_mes,
    (SELECT COUNT(*) FROM usuarios WHERE last_sign_in_at > NOW() - INTERVAL '7 days') as usuarios_activos_semana;

-- Vista: actividad por usuario (para admin)
CREATE OR REPLACE VIEW v_actividad_usuarios AS
SELECT
    u.id,
    u.nombre,
    u.email,
    u.rol,
    u.organizacion_id,
    u.last_sign_in_at,
    COALESCE(b.total_busquedas, 0) as total_busquedas,
    COALESCE(e.total_exports, 0) as total_exports,
    b.ultima_busqueda,
    e.ultimo_export
FROM usuarios u
LEFT JOIN (
    SELECT
        usuario_id,
        COUNT(*) as total_busquedas,
        MAX(created_at) as ultima_busqueda
    FROM busquedas
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY usuario_id
) b ON u.id = b.usuario_id
LEFT JOIN (
    SELECT
        usuario_id,
        COUNT(*) as total_exports,
        MAX(created_at) as ultimo_export
    FROM exportaciones
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY usuario_id
) e ON u.id = e.usuario_id;

-- Vista: resumen por organizacion (para superadmin)
CREATE OR REPLACE VIEW v_resumen_organizaciones AS
SELECT
    o.id,
    o.nombre,
    o.created_at,
    COUNT(DISTINCT u.id) as total_usuarios,
    COUNT(DISTINCT CASE WHEN u.last_sign_in_at > NOW() - INTERVAL '7 days' THEN u.id END) as usuarios_activos,
    COALESCE(SUM(b.busquedas), 0) as busquedas_mes,
    COALESCE(SUM(e.exports), 0) as exports_mes
FROM organizaciones o
LEFT JOIN usuarios u ON o.id = u.organizacion_id
LEFT JOIN (
    SELECT organizacion_id, COUNT(*) as busquedas
    FROM busquedas
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY organizacion_id
) b ON o.id = b.organizacion_id
LEFT JOIN (
    SELECT organizacion_id, COUNT(*) as exports
    FROM exportaciones
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY organizacion_id
) e ON o.id = e.organizacion_id
GROUP BY o.id, o.nombre, o.created_at;

-- ============================================================================
-- Funciones auxiliares
-- ============================================================================

-- Funcion para registrar accion en audit log
CREATE OR REPLACE FUNCTION log_accion(
    p_accion TEXT,
    p_recurso TEXT DEFAULT NULL,
    p_recurso_id TEXT DEFAULT NULL,
    p_detalle JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_usuario_id UUID;
    v_org_id UUID;
    v_log_id UUID;
BEGIN
    SELECT id, organizacion_id INTO v_usuario_id, v_org_id
    FROM usuarios WHERE auth_id = auth.uid();

    INSERT INTO audit_log (usuario_id, organizacion_id, accion, recurso, recurso_id, detalle)
    VALUES (v_usuario_id, v_org_id, p_accion, p_recurso, p_recurso_id, p_detalle)
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funcion para registrar busqueda
CREATE OR REPLACE FUNCTION registrar_busqueda(
    p_termino TEXT,
    p_filtros JSONB,
    p_resultados INTEGER,
    p_duracion_ms INTEGER DEFAULT NULL,
    p_pagina TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_usuario_id UUID;
    v_org_id UUID;
    v_busqueda_id UUID;
BEGIN
    SELECT id, organizacion_id INTO v_usuario_id, v_org_id
    FROM usuarios WHERE auth_id = auth.uid();

    INSERT INTO busquedas (usuario_id, organizacion_id, termino, filtros, resultados_count, duracion_ms, pagina)
    VALUES (v_usuario_id, v_org_id, p_termino, p_filtros, p_resultados, p_duracion_ms, p_pagina)
    RETURNING id INTO v_busqueda_id;

    RETURN v_busqueda_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
