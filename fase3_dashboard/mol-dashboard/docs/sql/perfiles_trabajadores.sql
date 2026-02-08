-- ============================================
-- TABLA: perfiles_trabajadores
-- Para Issue #7: Sistema de perfiles de oficina de empleo
-- ============================================

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS perfiles_trabajadores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    ocupaciones_trayectoria JSONB DEFAULT '[]'::jsonb,  -- Array de UUIDs de ocupaciones ESCO
    skills_seleccionadas JSONB DEFAULT '[]'::jsonb,     -- Array de URIs de skills
    skills_eliminadas JSONB DEFAULT '[]'::jsonb,        -- Skills que el trabajador NO tiene
    skills_agregadas JSONB DEFAULT '[]'::jsonb,         -- Skills agregadas manualmente
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)           -- Usuario que creó el perfil
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_perfiles_nombre ON perfiles_trabajadores(nombre);
CREATE INDEX IF NOT EXISTS idx_perfiles_created_at ON perfiles_trabajadores(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_perfiles_updated_at ON perfiles_trabajadores(updated_at DESC);

-- RLS (Row Level Security) - Opcional
ALTER TABLE perfiles_trabajadores ENABLE ROW LEVEL SECURITY;

-- Política: Todos los usuarios autenticados pueden ver y modificar perfiles
CREATE POLICY "Usuarios autenticados pueden CRUD perfiles"
ON perfiles_trabajadores
FOR ALL
USING (auth.uid() IS NOT NULL)
WITH CHECK (auth.uid() IS NOT NULL);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_perfiles_updated_at
    BEFORE UPDATE ON perfiles_trabajadores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios
COMMENT ON TABLE perfiles_trabajadores IS 'Perfiles de trabajadores para oficina de empleo (Issue #7)';
COMMENT ON COLUMN perfiles_trabajadores.ocupaciones_trayectoria IS 'UUIDs de ocupaciones ESCO de la trayectoria laboral';
COMMENT ON COLUMN perfiles_trabajadores.skills_seleccionadas IS 'URIs de skills que el trabajador tiene (calculadas + confirmadas)';
COMMENT ON COLUMN perfiles_trabajadores.skills_eliminadas IS 'URIs de skills que el trabajador NO tiene (removidas del perfil)';
COMMENT ON COLUMN perfiles_trabajadores.skills_agregadas IS 'URIs de skills agregadas manualmente via buscador';
