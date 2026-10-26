-- Migration 072: recálculo de la brecha de formación dentro de Supabase
-- (DEMO-MIERCOLES 1.2). Reemplaza populate_brecha_provincial.py, que traía
-- regice_cursos_skills sin paginar (1.000 de ~15K filas) y usaba conteos nacionales
-- como aproximación provincial. Todo corre sobre tablas de Supabase; no toca SQLite.

BEGIN;

-- 1. Nacional (misma lógica que 054)
TRUNCATE brecha_formacion_skills;

INSERT INTO brecha_formacion_skills
  (skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT
  os.skill_uri,
  MAX(os.preferred_label)      AS skill_label,
  COUNT(DISTINCT os.id_oferta) AS ofertas_count,
  COUNT(DISTINCT rcs.curso_id) AS cursos_count,
  CASE WHEN COUNT(DISTINCT rcs.curso_id) = 0 THEN 'brecha' ELSE 'cubierta' END AS estado
FROM ofertas_skills os
LEFT JOIN regice_cursos_skills rcs ON os.skill_uri = rcs.skill_uri
WHERE os.skill_uri IS NOT NULL
GROUP BY os.skill_uri;

-- 2. Provincial: demanda real por provincia vs cursos REGICE con sede en esa provincia.
-- Normalización MOL → REGICE: sin tildes, mayúscula inicial ('Río Negro' → 'Rio negro'),
-- CABA → 'Capital federal' (mismos valores que get_brecha_formacion_provincia).
TRUNCATE brecha_formacion_provincial;

INSERT INTO brecha_formacion_provincial
  (provincia, skill_uri, skill_label, ofertas_count, cursos_count, estado)
WITH demanda AS (
  SELECT od.provincia,
         CASE WHEN od.provincia = 'CABA' THEN 'Capital federal'
              ELSE upper(left(translate(od.provincia, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 1))
                   || lower(substr(translate(od.provincia, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 2))
         END AS prov_regice,
         os.skill_uri,
         MAX(os.preferred_label)      AS skill_label,
         COUNT(DISTINCT os.id_oferta) AS ofertas_count
  FROM ofertas_skills os
  JOIN ofertas_dashboard od ON od.id_oferta = os.id_oferta
  WHERE od.provincia IS NOT NULL AND os.skill_uri IS NOT NULL
  GROUP BY od.provincia, os.skill_uri
),
oferta AS (
  SELECT rs.provincia AS prov_regice, rcs.skill_uri,
         COUNT(DISTINCT rcs.curso_id) AS cursos_count
  FROM regice_cursos_skills rcs
  JOIN regice_cursos_sedes rcse ON rcse.curso_id = rcs.curso_id
  JOIN regice_sedes rs ON rs.sede_code = rcse.sede_code
  GROUP BY rs.provincia, rcs.skill_uri
)
SELECT d.provincia, d.skill_uri, d.skill_label, d.ofertas_count,
       COALESCE(o.cursos_count, 0),
       CASE WHEN COALESCE(o.cursos_count, 0) = 0 THEN 'brecha' ELSE 'cubierta' END
FROM demanda d
LEFT JOIN oferta o ON o.prov_regice = d.prov_regice AND o.skill_uri = d.skill_uri;

COMMIT;
