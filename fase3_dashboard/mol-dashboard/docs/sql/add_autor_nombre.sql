-- ============================================
-- Agregar columna autor_nombre a tabla issues
-- Para Issue: Mostrar nombre completo del autor
-- ============================================

-- 1. Agregar columna
ALTER TABLE issues ADD COLUMN IF NOT EXISTS autor_nombre TEXT;

-- 2. Actualizar issues existentes (creados por Diego)
UPDATE issues
SET autor_nombre = 'Diego Javier Schleser'
WHERE autor_email = 'admin@oede.gob.ar';

-- 3. Verificar
SELECT id, titulo, autor_email, autor_nombre
FROM issues
ORDER BY created_at DESC;
