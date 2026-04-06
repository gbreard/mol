-- Migration 050: Ajustes para M1 — Perfil de Competencias
-- Agrega columnas a perfiles y amplía CHECK de perfil_skills

-- ============================================================
-- 1. PERFILES — agregar ocupaciones, estado, validado_at
-- ============================================================

ALTER TABLE perfiles ADD COLUMN IF NOT EXISTS ocupaciones jsonb DEFAULT '[]';
ALTER TABLE perfiles ADD COLUMN IF NOT EXISTS estado text DEFAULT 'borrador';
ALTER TABLE perfiles ADD COLUMN IF NOT EXISTS validado_at timestamptz;

-- ============================================================
-- 2. PERFIL_SKILLS — agregar 'estructurado' a via_captura
-- ============================================================

ALTER TABLE perfil_skills DROP CONSTRAINT IF EXISTS perfil_skills_via_captura_check;
ALTER TABLE perfil_skills ADD CONSTRAINT perfil_skills_via_captura_check
  CHECK (via_captura IN ('ocupacion','tarea','texto','formacion','estructurado'));
