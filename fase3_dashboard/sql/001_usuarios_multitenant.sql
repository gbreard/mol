-- ============================================
-- MOL Dashboard - Schema Usuarios Multitenant
-- Version: 2.0 (con platform_admin y analytics)
-- Fecha: 2026-01-17
-- ============================================
-- Ejecutar en Supabase SQL Editor
-- ============================================

-- 1. ORGANIZACIONES (Tenants)
-- ============================================
CREATE TABLE IF NOT EXISTS organizaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    tipo TEXT CHECK (tipo IN ('gobierno', 'universidad', 'empresa', 'ong', 'otro')),
    jurisdiccion TEXT,
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE organizaciones IS 'Tenants del sistema - cada organizacion ve sus propios datos';

-- 2. USUARIOS (extiende auth.users)
-- ============================================
-- ROLES:
--   platform_admin: Acceso total a plataforma + analytics de uso
--   admin: Gestiona su organizacion
--   analista: Usa el dashboard, crea busquedas/alertas
--   lector: Solo lectura de datos agregados
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    organizacion_id UUID REFERENCES organizaciones(id),
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL,
    rol TEXT DEFAULT 'analista' CHECK (rol IN ('platform_admin', 'admin', 'analista', 'lector')),
    activo BOOLEAN DEFAULT true,
    ultimo_acceso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE usuarios IS 'Perfil extendido de usuarios con organizacion y rol';
COMMENT ON COLUMN usuarios.rol IS 'platform_admin=plataforma completa, admin=su org, analista=uso normal, lector=solo lectura';

-- 3. BUSQUEDAS GUARDADAS
-- ============================================
CREATE TABLE IF NOT EXISTS busquedas_guardadas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    filtros JSONB NOT NULL DEFAULT '{}',
    descripcion TEXT,
    es_publica BOOLEAN DEFAULT false,
    veces_usada INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE busquedas_guardadas IS 'Busquedas guardadas por usuario con filtros JSONB';
COMMENT ON COLUMN busquedas_guardadas.filtros IS 'Ej: {"provincia": "CABA", "isco_codes": ["2512"], "modalidad": "remoto"}';

-- 4. INTERESES (seguimiento)
-- ============================================
CREATE TABLE IF NOT EXISTS intereses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('ocupacion', 'skill', 'sector', 'empresa')),
    valor TEXT NOT NULL,
    etiqueta TEXT,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE intereses IS 'Ocupaciones, skills o sectores que el usuario quiere seguir';

-- 5. ALERTAS
-- ============================================
CREATE TABLE IF NOT EXISTS alertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('nuevas_ofertas', 'cambio_tendencia', 'umbral')),
    condiciones JSONB NOT NULL DEFAULT '{}',
    frecuencia TEXT DEFAULT 'diaria' CHECK (frecuencia IN ('inmediata', 'diaria', 'semanal')),
    canal TEXT DEFAULT 'email' CHECK (canal IN ('email', 'dashboard', 'ambos')),
    activa BOOLEAN DEFAULT true,
    ultima_ejecucion TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE alertas IS 'Alertas configurables por usuario';
COMMENT ON COLUMN alertas.condiciones IS 'Ej: {"filtros": {"isco_code": "2512"}, "minimo": 5}';

-- ============================================
-- 6. ANALYTICS DE USO DE PLATAFORMA
-- ============================================
-- Solo visible para platform_admin
-- ============================================

-- 6.1 EVENTOS DE USO (tracking de comportamiento)
CREATE TABLE IF NOT EXISTS eventos_uso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    organizacion_id UUID REFERENCES organizaciones(id) ON DELETE SET NULL,
    evento TEXT NOT NULL,
    categoria TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE eventos_uso IS 'Tracking de eventos de uso de la plataforma - solo platform_admin';
COMMENT ON COLUMN eventos_uso.evento IS 'login, logout, busqueda, descarga, alerta_creada, oferta_vista, filtro_aplicado, etc';
COMMENT ON COLUMN eventos_uso.categoria IS 'auth, busqueda, exportacion, configuracion, navegacion';
COMMENT ON COLUMN eventos_uso.metadata IS 'Datos adicionales del evento: filtros usados, duracion, resultado, etc';

-- 6.2 METRICAS DE PLATAFORMA (snapshots diarios)
CREATE TABLE IF NOT EXISTS metricas_plataforma (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha DATE NOT NULL UNIQUE,
    -- Fase 1: Scraping
    ofertas_scrapeadas_total INTEGER DEFAULT 0,
    ofertas_scrapeadas_dia INTEGER DEFAULT 0,
    ofertas_activas INTEGER DEFAULT 0,
    ofertas_cerradas INTEGER DEFAULT 0,
    -- Fase 2: Procesamiento
    ofertas_con_nlp INTEGER DEFAULT 0,
    ofertas_con_matching INTEGER DEFAULT 0,
    ofertas_validadas INTEGER DEFAULT 0,
    reglas_negocio_count INTEGER DEFAULT 0,
    -- Fase 3: Uso de plataforma
    usuarios_activos_dia INTEGER DEFAULT 0,
    usuarios_activos_semana INTEGER DEFAULT 0,
    usuarios_activos_mes INTEGER DEFAULT 0,
    busquedas_realizadas INTEGER DEFAULT 0,
    descargas_csv INTEGER DEFAULT 0,
    alertas_activas INTEGER DEFAULT 0,
    -- Organizaciones
    organizaciones_activas INTEGER DEFAULT 0,
    usuarios_total INTEGER DEFAULT 0,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE metricas_plataforma IS 'Snapshot diario de metricas de las 3 fases - solo platform_admin';

-- 6.3 SESIONES DE USUARIO
CREATE TABLE IF NOT EXISTS sesiones_usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    inicio TIMESTAMPTZ NOT NULL DEFAULT now(),
    fin TIMESTAMPTZ,
    duracion_segundos INTEGER,
    paginas_visitadas INTEGER DEFAULT 0,
    acciones_realizadas INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE sesiones_usuario IS 'Tracking de sesiones para medir engagement';

-- ============================================
-- 7. INDICES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_usuarios_org ON usuarios(organizacion_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);
CREATE INDEX IF NOT EXISTS idx_busquedas_usuario ON busquedas_guardadas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_intereses_usuario ON intereses(usuario_id);
CREATE INDEX IF NOT EXISTS idx_intereses_tipo ON intereses(tipo);
CREATE INDEX IF NOT EXISTS idx_alertas_usuario ON alertas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_alertas_activas ON alertas(activa) WHERE activa = true;
-- Indices para analytics
CREATE INDEX IF NOT EXISTS idx_eventos_usuario ON eventos_uso(usuario_id);
CREATE INDEX IF NOT EXISTS idx_eventos_fecha ON eventos_uso(created_at);
CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos_uso(evento);
CREATE INDEX IF NOT EXISTS idx_eventos_categoria ON eventos_uso(categoria);
CREATE INDEX IF NOT EXISTS idx_metricas_fecha ON metricas_plataforma(fecha);
CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones_usuario(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_inicio ON sesiones_usuario(inicio);

-- ============================================
-- 8. FUNCIONES AUXILIARES
-- ============================================

-- Funcion para verificar si usuario es platform_admin
CREATE OR REPLACE FUNCTION is_platform_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM usuarios
        WHERE id = auth.uid()
        AND rol = 'platform_admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funcion para obtener organizacion del usuario actual
CREATE OR REPLACE FUNCTION get_user_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN (SELECT organizacion_id FROM usuarios WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_organizaciones_updated_at ON organizaciones;
CREATE TRIGGER update_organizaciones_updated_at
    BEFORE UPDATE ON organizaciones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_busquedas_updated_at ON busquedas_guardadas;
CREATE TRIGGER update_busquedas_updated_at
    BEFORE UPDATE ON busquedas_guardadas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- 9. TRIGGER: Crear perfil en registro
-- ============================================
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.usuarios (id, email, nombre, apellido)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'nombre', 'Nuevo'),
        COALESCE(NEW.raw_user_meta_data->>'apellido', 'Usuario')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_profile();

-- ============================================
-- 10. ROW LEVEL SECURITY
-- ============================================

-- Habilitar RLS
ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE busquedas_guardadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE intereses ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_uso ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_plataforma ENABLE ROW LEVEL SECURITY;
ALTER TABLE sesiones_usuario ENABLE ROW LEVEL SECURITY;

-- ============================================
-- POLITICAS PARA ORGANIZACIONES
-- ============================================
-- Platform admin ve todas, resto ve solo su org
CREATE POLICY "org_select" ON organizaciones
    FOR SELECT USING (
        is_platform_admin()
        OR id = get_user_org_id()
    );

-- Solo platform_admin puede crear/modificar orgs
CREATE POLICY "org_insert" ON organizaciones
    FOR INSERT WITH CHECK (is_platform_admin());

CREATE POLICY "org_update" ON organizaciones
    FOR UPDATE USING (is_platform_admin());

-- ============================================
-- POLITICAS PARA USUARIOS
-- ============================================
-- Platform admin ve todos, resto ve su org
CREATE POLICY "usuarios_select" ON usuarios
    FOR SELECT USING (
        is_platform_admin()
        OR organizacion_id = get_user_org_id()
        OR id = auth.uid()
    );

-- Actualizar solo perfil propio (excepto platform_admin)
CREATE POLICY "usuarios_update" ON usuarios
    FOR UPDATE USING (
        is_platform_admin()
        OR id = auth.uid()
    );

-- ============================================
-- POLITICAS PARA BUSQUEDAS
-- ============================================
-- Ver propias, publicas de su org, o todas si platform_admin
CREATE POLICY "busquedas_select" ON busquedas_guardadas
    FOR SELECT USING (
        is_platform_admin()
        OR usuario_id = auth.uid()
        OR (
            es_publica = true
            AND usuario_id IN (
                SELECT id FROM usuarios WHERE organizacion_id = get_user_org_id()
            )
        )
    );

CREATE POLICY "busquedas_insert" ON busquedas_guardadas
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "busquedas_update" ON busquedas_guardadas
    FOR UPDATE USING (usuario_id = auth.uid() OR is_platform_admin());

CREATE POLICY "busquedas_delete" ON busquedas_guardadas
    FOR DELETE USING (usuario_id = auth.uid() OR is_platform_admin());

-- ============================================
-- POLITICAS PARA INTERESES
-- ============================================
CREATE POLICY "intereses_select" ON intereses
    FOR SELECT USING (
        is_platform_admin()
        OR usuario_id = auth.uid()
    );

CREATE POLICY "intereses_insert" ON intereses
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "intereses_update" ON intereses
    FOR UPDATE USING (usuario_id = auth.uid());

CREATE POLICY "intereses_delete" ON intereses
    FOR DELETE USING (usuario_id = auth.uid());

-- ============================================
-- POLITICAS PARA ALERTAS
-- ============================================
CREATE POLICY "alertas_select" ON alertas
    FOR SELECT USING (
        is_platform_admin()
        OR usuario_id = auth.uid()
    );

CREATE POLICY "alertas_insert" ON alertas
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "alertas_update" ON alertas
    FOR UPDATE USING (usuario_id = auth.uid());

CREATE POLICY "alertas_delete" ON alertas
    FOR DELETE USING (usuario_id = auth.uid());

-- ============================================
-- POLITICAS PARA ANALYTICS (solo platform_admin)
-- ============================================
CREATE POLICY "eventos_select" ON eventos_uso
    FOR SELECT USING (is_platform_admin());

CREATE POLICY "eventos_insert" ON eventos_uso
    FOR INSERT WITH CHECK (true);  -- Cualquiera puede generar eventos

CREATE POLICY "metricas_select" ON metricas_plataforma
    FOR SELECT USING (is_platform_admin());

CREATE POLICY "metricas_insert" ON metricas_plataforma
    FOR INSERT WITH CHECK (is_platform_admin());

CREATE POLICY "metricas_update" ON metricas_plataforma
    FOR UPDATE USING (is_platform_admin());

CREATE POLICY "sesiones_select" ON sesiones_usuario
    FOR SELECT USING (
        is_platform_admin()
        OR usuario_id = auth.uid()
    );

CREATE POLICY "sesiones_insert" ON sesiones_usuario
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "sesiones_update" ON sesiones_usuario
    FOR UPDATE USING (usuario_id = auth.uid());

-- ============================================
-- 11. VISTAS PARA ANALYTICS
-- ============================================

-- Vista: Resumen de uso por organizacion (para platform_admin)
CREATE OR REPLACE VIEW v_uso_por_organizacion AS
SELECT
    o.id AS organizacion_id,
    o.nombre AS organizacion,
    COUNT(DISTINCT u.id) AS usuarios_total,
    COUNT(DISTINCT CASE WHEN u.ultimo_acceso > now() - interval '30 days' THEN u.id END) AS usuarios_activos_mes,
    COUNT(DISTINCT b.id) AS busquedas_guardadas,
    COUNT(DISTINCT a.id) AS alertas_activas,
    COUNT(DISTINCT e.id) AS eventos_ultimo_mes
FROM organizaciones o
LEFT JOIN usuarios u ON u.organizacion_id = o.id
LEFT JOIN busquedas_guardadas b ON b.usuario_id = u.id
LEFT JOIN alertas a ON a.usuario_id = u.id AND a.activa = true
LEFT JOIN eventos_uso e ON e.organizacion_id = o.id AND e.created_at > now() - interval '30 days'
GROUP BY o.id, o.nombre;

-- Vista: Eventos recientes (para platform_admin)
CREATE OR REPLACE VIEW v_eventos_recientes AS
SELECT
    e.created_at,
    e.evento,
    e.categoria,
    u.nombre || ' ' || u.apellido AS usuario,
    o.nombre AS organizacion,
    e.metadata
FROM eventos_uso e
LEFT JOIN usuarios u ON u.id = e.usuario_id
LEFT JOIN organizaciones o ON o.id = e.organizacion_id
ORDER BY e.created_at DESC
LIMIT 1000;

-- ============================================
-- 12. DATOS INICIALES
-- ============================================

-- Organizacion OEDE (principal - platform level)
INSERT INTO organizaciones (id, nombre, tipo, jurisdiccion)
VALUES ('00000000-0000-0000-0000-000000000001', 'OEDE', 'gobierno', 'nacional')
ON CONFLICT (id) DO NOTHING;

-- Snapshot inicial de metricas
INSERT INTO metricas_plataforma (fecha, ofertas_scrapeadas_total, ofertas_validadas, organizaciones_activas)
VALUES (CURRENT_DATE, 0, 0, 1)
ON CONFLICT (fecha) DO NOTHING;

-- ============================================
-- FIN DEL SCRIPT v2.0
-- ============================================
