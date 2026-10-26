-- Migration 075: la UI ofrece el nivel 'experto' pero el CHECK lo rechazaba
-- ("Error guardando skills"). DEMO-MIERCOLES, bug 2 del gate.

ALTER TABLE perfil_skills DROP CONSTRAINT IF EXISTS perfil_skills_nivel_check;
ALTER TABLE perfil_skills ADD CONSTRAINT perfil_skills_nivel_check
  CHECK (nivel = ANY (ARRAY['basico'::text, 'intermedio'::text, 'avanzado'::text, 'experto'::text]));
