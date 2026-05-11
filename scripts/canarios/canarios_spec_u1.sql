-- ============================================================
-- Canarios SQL para SPEC U-1 v3.1
-- ============================================================
-- Cinco queries para detectar regresiones durante la implementación.
-- Cada query devuelve un único entero (n_rows). Comparar contra baseline
-- registrado en docs/diagnostico/baseline_canarios_post_F0.md.
--
-- Uso:
--   sqlite3 database/bumeran_scraping.db < scripts/canarios/canarios_spec_u1.sql
-- O desde Python:
--   python scripts/canarios/run_canarios.py
--
-- Umbrales de alarma (sobre baseline):
--   C-Q1: > +5%
--   C-Q2: > +1% (debe BAJAR drásticamente con C4)
--   C-Q3: > +5%
--   C-Q4: > +10% (en Supabase)
--   C-Q5: > ±20%
-- ============================================================

-- C-Q1: Ofertas con esco_occupation_uri vacía
-- Baseline: 3.762 (de las cuales 3.758 son del diccionario)
-- Esperado post-C2: < 50
SELECT 'C-Q1' AS canario,
       COUNT(*) AS valor,
       3762 AS baseline,
       'ofertas con esco_occupation_uri vacía' AS descripcion
FROM ofertas_esco_matching
WHERE esco_occupation_uri = '' OR esco_occupation_uri IS NULL;

-- C-Q2: Filas en ofertas_esco_skills_detalle con flags=0
-- Baseline: 1.116.011 (todas, regresión DIAG A)
-- Esperado post-C4: ~784.263
SELECT 'C-Q2' AS canario,
       COUNT(*) AS valor,
       1116011 AS baseline,
       'filas con is_essential=0 AND is_optional=0' AS descripcion
FROM ofertas_esco_skills_detalle
WHERE is_essential_for_occupation = 0
  AND is_optional_for_occupation = 0;

-- C-Q3: URIs con drift de labels (más de un label distinto por URI)
-- Baseline: 1.237
-- Esperado post-C1: < 50
SELECT 'C-Q3' AS canario,
       COUNT(*) AS valor,
       1237 AS baseline,
       'URIs con más de un esco_occupation_label distinto' AS descripcion
FROM (
    SELECT esco_occupation_uri, COUNT(DISTINCT esco_occupation_label) AS n_labels
    FROM ofertas_esco_matching
    WHERE esco_occupation_uri != '' AND esco_occupation_label != ''
    GROUP BY esco_occupation_uri
    HAVING n_labels > 1
);

-- C-Q4: skills "candidatas a zombie" en Supabase
-- Esta query corre en Supabase, NO acá.
-- Ver scripts/canarios/run_canarios.py
-- Baseline: 28.395 (mayoría es backlog según R9 §D — se reduce con sync)

-- C-Q5: Drift Local↔Supabase de ofertas_dashboard
-- Esta query corre comparando local + Supabase, NO acá.
-- Ver scripts/canarios/run_canarios.py
-- Baseline: ~3.834 (verificado 2026-05-05, NO 40K como decía SPEC v3.1)

-- ============================================================
-- C-Q6 (auxiliar): conteos de validación
-- ============================================================
SELECT 'C-Q6' AS canario,
       COUNT(*) AS valor,
       NULL AS baseline,
       'ofertas validadas locales (universo Supabase esperado)' AS descripcion
FROM ofertas_esco_matching
WHERE estado_validacion IN ('validado', 'validado_claude', 'validado_humano');

-- C-Q7: matching_version=spec_h_rematch (objetivo de C1)
SELECT 'C-Q7' AS canario,
       COUNT(*) AS valor,
       8221 AS baseline,
       'ofertas con matching_version=spec_h_rematch (objetivo C1)' AS descripcion
FROM ofertas_esco_matching
WHERE matching_version = 'spec_h_rematch';
