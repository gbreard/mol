-- Migration 072: recálculo de la brecha de formación dentro de Supabase
-- (DEMO-MIERCOLES 1.2). Reemplaza populate_brecha_provincial.py, que traía
-- regice_cursos_skills sin paginar (1.000 de ~15K filas) y usaba conteos nacionales
-- como aproximación provincial. Todo corre sobre tablas de Supabase; no toca SQLite.

-- Se corre en 3 pasos (la Management API corta la conexión a los ~120 s y una
-- transacción larga se revierte): primero se calcula en tablas de staging y después
-- se reemplaza en una transacción corta, así las tablas reales nunca quedan vacías.

-- Paso 1: staging nacional (misma lógica que 054)
DROP TABLE IF EXISTS _brecha_nac_new;
CREATE TABLE _brecha_nac_new AS
-- Se agrega cada lado por separado: el LEFT JOIN directo de 054 multiplicaba las
-- 2,6M filas de ofertas_skills por los cursos de cada skill (mismo resultado, >120 s)
WITH demanda AS (
  -- UNIQUE (id_oferta, skill_uri): COUNT(*) = COUNT(DISTINCT id_oferta) por skill, sin ordenar 2,6M filas
  SELECT skill_uri, MAX(preferred_label) AS skill_label, COUNT(*) AS ofertas_count
  FROM ofertas_skills
  WHERE skill_uri IS NOT NULL
  GROUP BY skill_uri
),
cursos AS (
  SELECT skill_uri, COUNT(DISTINCT curso_id) AS cursos_count
  FROM regice_cursos_skills
  GROUP BY skill_uri
)
SELECT d.skill_uri, d.skill_label, d.ofertas_count,
       COALESCE(c.cursos_count, 0) AS cursos_count,
       CASE WHEN COALESCE(c.cursos_count, 0) = 0 THEN 'brecha' ELSE 'cubierta' END AS estado
FROM demanda d
LEFT JOIN cursos c ON c.skill_uri = d.skill_uri;

-- Paso 2: staging provincial: demanda real por provincia vs cursos REGICE con sede
-- en esa provincia. Normalización MOL → REGICE: sin tildes, mayúscula inicial
-- ('Río Negro' → 'Rio negro'), CABA → 'Capital federal' (como get_brecha_formacion_provincia).
DROP TABLE IF EXISTS _brecha_prov_new;
CREATE TABLE _brecha_prov_new AS
WITH demanda AS (
  SELECT od.provincia,
         CASE WHEN od.provincia = 'CABA' THEN 'Capital federal'
              ELSE upper(left(translate(od.provincia, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 1))
                   || lower(substr(translate(od.provincia, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 2))
         END AS prov_regice,
         os.skill_uri,
         MAX(os.preferred_label)      AS skill_label,
         COUNT(*) AS ofertas_count  -- UNIQUE (id_oferta, skill_uri)
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
       COALESCE(o.cursos_count, 0) AS cursos_count,
       CASE WHEN COALESCE(o.cursos_count, 0) = 0 THEN 'brecha' ELSE 'cubierta' END AS estado
FROM demanda d
LEFT JOIN oferta o ON o.prov_regice = d.prov_regice AND o.skill_uri = d.skill_uri;

-- Paso 3: reemplazo atómico
BEGIN;
TRUNCATE brecha_formacion_skills;
INSERT INTO brecha_formacion_skills (skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT skill_uri, skill_label, ofertas_count, cursos_count, estado FROM _brecha_nac_new
-- 10 skills transversales (origen 'titulo') llegan sin preferred_label y no figuran en
-- esco_skills ni skills_embeddings: se excluyen hasta resolver su nombre (pendiente)
WHERE skill_label IS NOT NULL;
TRUNCATE brecha_formacion_provincial;
INSERT INTO brecha_formacion_provincial (provincia, skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT provincia, skill_uri, skill_label, ofertas_count, cursos_count, estado FROM _brecha_prov_new
WHERE skill_label IS NOT NULL;
COMMIT;
DROP TABLE _brecha_nac_new;
DROP TABLE _brecha_prov_new;
