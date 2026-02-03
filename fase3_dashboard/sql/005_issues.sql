-- ============================================
-- MOL Dashboard - Sistema de Issues/Feedback
-- Version: 1.0
-- Fecha: 2026-02-03
-- ============================================
-- Sistema para reportar errores y sugerencias
-- desde el dashboard hacia el equipo de desarrollo
-- ============================================

-- 1. TABLA ISSUES
-- ============================================
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Contexto del issue
    id_oferta TEXT REFERENCES ofertas_dashboard(id_oferta) ON DELETE SET NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,

    -- Clasificacion
    tipo TEXT NOT NULL CHECK(tipo IN (
        'error_isco',      -- ISCO incorrecto
        'error_nlp',       -- Campo NLP mal extraido
        'error_skill',     -- Skill faltante o incorrecto
        'sugerencia',      -- Sugerencia de mejora
        'bug',             -- Bug del dashboard
        'otro'             -- Otro tipo
    )),
    campo_afectado TEXT,                  -- Ej: "isco_code", "provincia", "skills"
    valor_actual TEXT,                    -- Valor actual que tiene el campo
    valor_esperado TEXT,                  -- Valor correcto segun el usuario

    -- Estado del issue
    estado TEXT DEFAULT 'pendiente' CHECK(estado IN (
        'pendiente',       -- Recien creado
        'en_revision',     -- Equipo esta revisando
        'en_progreso',     -- Se esta trabajando
        'resuelto',        -- Solucionado
        'descartado',      -- No se hara
        'duplicado'        -- Duplicado de otro issue
    )),
    prioridad TEXT DEFAULT 'media' CHECK(prioridad IN (
        'baja', 'media', 'alta', 'critica'
    )),

    -- Tracking de resolucion
    resuelto_at TIMESTAMPTZ,
    resuelto_por TEXT,                    -- Nombre/email de quien resolvio
    solucion_aplicada TEXT,               -- Descripcion de la solucion
    config_modificada TEXT,               -- Archivo config que se modifico

    -- Agrupacion de issues similares
    agrupado_con UUID REFERENCES issues(id) ON DELETE SET NULL,

    -- Autor
    autor_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    autor_email TEXT,                     -- Para issues anonimos

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE issues IS 'Issues y feedback reportados desde el dashboard';
COMMENT ON COLUMN issues.tipo IS 'Tipo de error: error_isco, error_nlp, error_skill, sugerencia, bug, otro';
COMMENT ON COLUMN issues.agrupado_con IS 'Si el issue es similar a otro, se agrupa para resolverlos juntos';
COMMENT ON COLUMN issues.config_modificada IS 'Archivo config modificado para resolver: matching_rules_business.json, nlp_inference_rules.json, etc';

-- 2. TABLA ISSUE_COMMENTS (Historial de comentarios)
-- ============================================
CREATE TABLE IF NOT EXISTS issue_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,

    -- Autor
    autor_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    autor_nombre TEXT,                    -- Para mostrar en UI

    -- Contenido
    comentario TEXT NOT NULL,
    es_interno BOOLEAN DEFAULT false,     -- Si es nota interna (solo equipo)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE issue_comments IS 'Historial de comentarios en issues';
COMMENT ON COLUMN issue_comments.es_interno IS 'true = solo visible para el equipo, false = visible para el autor del issue';

-- 3. TABLA ISSUE_ATTACHMENTS (Adjuntos)
-- ============================================
CREATE TABLE IF NOT EXISTS issue_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,

    -- Archivo
    nombre TEXT NOT NULL,
    tipo_mime TEXT,
    url TEXT NOT NULL,                    -- URL en Supabase Storage
    tamano_bytes INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE issue_attachments IS 'Capturas de pantalla y archivos adjuntos a issues';

-- 4. INDICES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_issues_estado ON issues(estado);
CREATE INDEX IF NOT EXISTS idx_issues_tipo ON issues(tipo);
CREATE INDEX IF NOT EXISTS idx_issues_prioridad ON issues(prioridad);
CREATE INDEX IF NOT EXISTS idx_issues_oferta ON issues(id_oferta);
CREATE INDEX IF NOT EXISTS idx_issues_autor ON issues(autor_id);
CREATE INDEX IF NOT EXISTS idx_issues_fecha ON issues(created_at);
CREATE INDEX IF NOT EXISTS idx_issues_pendientes ON issues(estado)
    WHERE estado IN ('pendiente', 'en_revision', 'en_progreso');

CREATE INDEX IF NOT EXISTS idx_comments_issue ON issue_comments(issue_id);
CREATE INDEX IF NOT EXISTS idx_attachments_issue ON issue_attachments(issue_id);

-- 5. VISTAS
-- ============================================

-- Vista: Issues pendientes (para el equipo)
CREATE OR REPLACE VIEW v_issues_pendientes AS
SELECT
    i.id,
    i.titulo,
    i.tipo,
    i.prioridad,
    i.estado,
    i.id_oferta,
    i.campo_afectado,
    i.valor_actual,
    i.valor_esperado,
    i.autor_email,
    i.created_at,
    (SELECT COUNT(*) FROM issue_comments c WHERE c.issue_id = i.id) as comentarios_count
FROM issues i
WHERE i.estado IN ('pendiente', 'en_revision', 'en_progreso')
ORDER BY
    CASE i.prioridad
        WHEN 'critica' THEN 1
        WHEN 'alta' THEN 2
        WHEN 'media' THEN 3
        WHEN 'baja' THEN 4
    END,
    i.created_at;

-- Vista: Resumen de issues por tipo
CREATE OR REPLACE VIEW v_issues_por_tipo AS
SELECT
    tipo,
    COUNT(*) FILTER (WHERE estado = 'pendiente') as pendientes,
    COUNT(*) FILTER (WHERE estado IN ('en_revision', 'en_progreso')) as en_progreso,
    COUNT(*) FILTER (WHERE estado = 'resuelto') as resueltos,
    COUNT(*) FILTER (WHERE estado = 'descartado') as descartados,
    COUNT(*) as total
FROM issues
GROUP BY tipo
ORDER BY total DESC;

-- Vista: Efectividad de resoluciones (para metricas)
CREATE OR REPLACE VIEW v_issues_metricas AS
SELECT
    DATE_TRUNC('week', created_at) as semana,
    COUNT(*) as creados,
    COUNT(*) FILTER (WHERE estado = 'resuelto') as resueltos,
    AVG(EXTRACT(EPOCH FROM (resuelto_at - created_at)) / 3600)
        FILTER (WHERE resuelto_at IS NOT NULL) as horas_promedio_resolucion
FROM issues
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY semana DESC;

-- Vista: Issues agrupados (similares)
CREATE OR REPLACE VIEW v_issues_agrupados AS
SELECT
    COALESCE(agrupado_con, id) as grupo_id,
    COUNT(*) as issues_en_grupo,
    MIN(created_at) as primer_reporte,
    MAX(created_at) as ultimo_reporte,
    ARRAY_AGG(DISTINCT tipo) as tipos,
    MIN(estado) as estado_grupo
FROM issues
GROUP BY COALESCE(agrupado_con, id)
HAVING COUNT(*) > 1
ORDER BY issues_en_grupo DESC;

-- 6. ROW LEVEL SECURITY
-- ============================================

ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE issue_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE issue_attachments ENABLE ROW LEVEL SECURITY;

-- Politicas para issues
-- Usuarios autenticados pueden ver sus propios issues
CREATE POLICY "issues_select_own" ON issues
    FOR SELECT USING (
        autor_id = auth.uid()
        OR is_platform_admin()
    );

-- Usuarios pueden crear issues
CREATE POLICY "issues_insert" ON issues
    FOR INSERT WITH CHECK (
        autor_id = auth.uid() OR autor_id IS NULL
    );

-- Solo plataform_admin puede actualizar issues
CREATE POLICY "issues_update" ON issues
    FOR UPDATE USING (is_platform_admin());

-- Solo platform_admin puede borrar
CREATE POLICY "issues_delete" ON issues
    FOR DELETE USING (is_platform_admin());

-- Politicas para comentarios
CREATE POLICY "comments_select" ON issue_comments
    FOR SELECT USING (
        is_platform_admin()
        OR (
            NOT es_interno
            AND issue_id IN (SELECT id FROM issues WHERE autor_id = auth.uid())
        )
    );

CREATE POLICY "comments_insert" ON issue_comments
    FOR INSERT WITH CHECK (
        autor_id = auth.uid()
        OR is_platform_admin()
    );

-- Politicas para attachments
CREATE POLICY "attachments_select" ON issue_attachments
    FOR SELECT USING (
        is_platform_admin()
        OR issue_id IN (SELECT id FROM issues WHERE autor_id = auth.uid())
    );

CREATE POLICY "attachments_insert" ON issue_attachments
    FOR INSERT WITH CHECK (
        is_platform_admin()
        OR issue_id IN (SELECT id FROM issues WHERE autor_id = auth.uid())
    );

-- 7. FUNCIONES
-- ============================================

-- Funcion: Crear issue rapidamente
CREATE OR REPLACE FUNCTION crear_issue(
    p_titulo TEXT,
    p_tipo TEXT,
    p_id_oferta TEXT DEFAULT NULL,
    p_descripcion TEXT DEFAULT NULL,
    p_campo_afectado TEXT DEFAULT NULL,
    p_valor_actual TEXT DEFAULT NULL,
    p_valor_esperado TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_issue_id UUID;
    v_autor_email TEXT;
BEGIN
    -- Obtener email del usuario actual
    SELECT email INTO v_autor_email FROM usuarios WHERE id = auth.uid();

    INSERT INTO issues (
        id_oferta, titulo, descripcion, tipo,
        campo_afectado, valor_actual, valor_esperado,
        autor_id, autor_email
    ) VALUES (
        p_id_oferta, p_titulo, p_descripcion, p_tipo,
        p_campo_afectado, p_valor_actual, p_valor_esperado,
        auth.uid(), COALESCE(v_autor_email, 'anonimo@mol.gob.ar')
    )
    RETURNING id INTO v_issue_id;

    RETURN v_issue_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funcion: Resolver issue
CREATE OR REPLACE FUNCTION resolver_issue(
    p_issue_id UUID,
    p_solucion TEXT,
    p_config_modificada TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT is_platform_admin() THEN
        RAISE EXCEPTION 'Solo platform_admin puede resolver issues';
    END IF;

    UPDATE issues
    SET
        estado = 'resuelto',
        resuelto_at = NOW(),
        resuelto_por = (SELECT email FROM usuarios WHERE id = auth.uid()),
        solucion_aplicada = p_solucion,
        config_modificada = p_config_modificada,
        updated_at = NOW()
    WHERE id = p_issue_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funcion: Agrupar issues similares
CREATE OR REPLACE FUNCTION agrupar_issues(
    p_issue_principal UUID,
    p_issues_secundarios UUID[]
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    IF NOT is_platform_admin() THEN
        RAISE EXCEPTION 'Solo platform_admin puede agrupar issues';
    END IF;

    UPDATE issues
    SET agrupado_con = p_issue_principal
    WHERE id = ANY(p_issues_secundarios)
      AND id != p_issue_principal;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 8. TRIGGER: Actualizar updated_at
-- ============================================

CREATE TRIGGER trigger_issues_updated
    BEFORE UPDATE ON issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- FIN DEL SCRIPT v1.0
-- ============================================
