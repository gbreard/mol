-- Migration 065: agrega campo ofertas_ejemplo jsonb a catálogo MOL
-- Permite vincular una entrada del catálogo a las ofertas concretas que
-- la motivaron, para revisión humana del equipo.
--
-- Fecha: 2026-04-28
-- Spec: docs/plan/15_PERFILES_POLIVALENTES_AR.md
--
-- Schema esperado del campo:
--   ofertas_ejemplo: jsonb (array de objetos)
--     [
--       { "id_oferta": "8088943442", "titulo": "Patient & Diagnostic Manager",
--         "esco_actual": "1221.4 director comercial", "fecha_deteccion": "2026-04-28" },
--       ...
--     ]

ALTER TABLE catalogo_mol_ocupaciones
  ADD COLUMN IF NOT EXISTS ofertas_ejemplo jsonb DEFAULT '[]'::jsonb;

ALTER TABLE catalogo_mol_skills
  ADD COLUMN IF NOT EXISTS ofertas_ejemplo jsonb DEFAULT '[]'::jsonb;

COMMENT ON COLUMN catalogo_mol_ocupaciones.ofertas_ejemplo IS
  'Array JSON con ofertas concretas que motivaron la entrada (id_oferta, titulo, esco_actual, fecha_deteccion). Para revisión humana del equipo. NO necesariamente exhaustivo — un sample representativo.';

COMMENT ON COLUMN catalogo_mol_skills.ofertas_ejemplo IS
  'Idem catalogo_mol_ocupaciones.ofertas_ejemplo pero para skills detectadas.';

-- Índice GIN para queries por id_oferta dentro del array
CREATE INDEX IF NOT EXISTS idx_catalogo_ocup_ofertas_ejemplo
  ON catalogo_mol_ocupaciones USING GIN (ofertas_ejemplo);
