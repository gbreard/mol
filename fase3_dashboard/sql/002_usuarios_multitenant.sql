-- MOL Dashboard - Sistema de Usuarios Multi-tenant
-- Ejecutar DESPUES de 001_supabase_schema.sql y ANTES de 003_sistema_admin.sql

-- TABLA: organizaciones

CREATE TABLE IF NOT EXISTS organizaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLA: usuarios

CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE,  -- Referencia a auth.users
    email TEXT UNIQUE NOT NULL,
    nombre TEXT,
    organizacion_id UUID REFERENCES organizaciones(id),
    rol TEXT NOT NULL DEFAULT 'lector',
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT rol_valido CHECK (rol IN ('platform_admin', 'admin', 'analista', 'lector'))
);

CREATE INDEX IF NOT EXISTS idx_usuarios_auth_id ON usuarios(auth_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_org ON usuarios(organizacion_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- RLS para usuarios

ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- Organizaciones: lectura para usuarios de la org, escritura para platform_admin
CREATE POLICY "Lectura organizaciones propias" ON organizaciones
    FOR SELECT USING (
        id IN (SELECT organizacion_id FROM usuarios WHERE auth_id = auth.uid())
        OR
        EXISTS (SELECT 1 FROM usuarios WHERE auth_id = auth.uid() AND rol = 'platform_admin')
    );

CREATE POLICY "Escritura organizaciones platform_admin" ON organizaciones
    FOR ALL USING (
        EXISTS (SELECT 1 FROM usuarios WHERE auth_id = auth.uid() AND rol = 'platform_admin')
    );

-- Usuarios: lectura para admins de la org, escritura para admins
CREATE POLICY "Lectura usuarios misma org" ON usuarios
    FOR SELECT USING (
        organizacion_id IN (SELECT organizacion_id FROM usuarios WHERE auth_id = auth.uid())
        OR
        EXISTS (SELECT 1 FROM usuarios WHERE auth_id = auth.uid() AND rol = 'platform_admin')
        OR
        auth_id = auth.uid()
    );

CREATE POLICY "Escritura usuarios admin" ON usuarios
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM usuarios
            WHERE auth_id = auth.uid()
            AND rol IN ('admin', 'platform_admin')
            AND (organizacion_id = usuarios.organizacion_id OR rol = 'platform_admin')
        )
        OR
        auth_id = auth.uid()
    );

-- GRANTS

GRANT SELECT ON organizaciones TO authenticated;
GRANT SELECT ON usuarios TO authenticated;
GRANT ALL ON organizaciones TO service_role;
GRANT ALL ON usuarios TO service_role;

-- Funcion helper para obtener usuario actual

CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
    SELECT id FROM usuarios WHERE auth_id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_current_user_rol()
RETURNS TEXT AS $$
    SELECT rol FROM usuarios WHERE auth_id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_current_user_org()
RETURNS UUID AS $$
    SELECT organizacion_id FROM usuarios WHERE auth_id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER;
