-- 015: Add columns for validation panel (Cynthia workflow)
-- These columns enable human reviewers to see full offer details without leaving the dashboard.

-- descripcion: Full job posting text (from scraping)
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS descripcion text;

-- tareas_explicitas: Tasks extracted by NLP
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS tareas_explicitas text;

-- mision_rol: Role mission extracted by NLP
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS mision_rol text;

-- decision_metodo: How ISCO was decided (regla_prioridad, semantico_default, dual_coinciden, etc.)
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS decision_metodo text;

-- regla_aplicada: Business rule ID if a rule was applied (e.g. R260_gestor_operativo)
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS regla_aplicada text;
