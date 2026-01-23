-- =====================================================
-- Migración 020: Vistas de Agregación Skills L1/L2
-- Fecha: 2026-01-23
-- Versión: v2.4
-- =====================================================
--
-- Crea vistas para agregar skills por categorías L1 y L2 de ESCO.
-- Los datos L1/L2 vienen de los campos JSON skills_semantico_json
-- y skills_regla_json en ofertas_esco_matching.
--
-- Categorías L1 ESCO:
--   S1-S8: Skills específicas por área
--   K: Knowledge (conocimientos)
--   T1-T6: Transversales
--   A: Attitudes (actitudes)
-- =====================================================

-- Vista: Extrae skills individuales de los JSON para análisis
-- Nota: Usa json_each para expandir el array JSON
DROP VIEW IF EXISTS v_skills_detalle_l1_l2;
CREATE VIEW v_skills_detalle_l1_l2 AS
SELECT
    m.id_oferta,
    m.isco_code,
    m.esco_occupation_label,
    json_extract(skill.value, '$.skill_esco') as skill_esco,
    json_extract(skill.value, '$.skill_uri') as skill_uri,
    json_extract(skill.value, '$.L1') as L1,
    json_extract(skill.value, '$.L1_nombre') as L1_nombre,
    json_extract(skill.value, '$.L2') as L2,
    json_extract(skill.value, '$.L2_nombre') as L2_nombre,
    json_extract(skill.value, '$.es_digital') as es_digital,
    json_extract(skill.value, '$.score') as score,
    json_extract(skill.value, '$.origen') as origen,
    CASE
        WHEN json_extract(skill.value, '$.origen') = 'regla' THEN 'regla'
        ELSE 'semantico'
    END as tipo_fuente
FROM ofertas_esco_matching m
CROSS JOIN json_each(
    CASE
        WHEN m.skills_semantico_json IS NOT NULL AND m.skills_semantico_json != '[]'
        THEN m.skills_semantico_json
        ELSE '[]'
    END
) as skill
WHERE m.estado_validacion IS NOT NULL;

-- Vista: Agregación por L1 (nivel 1 de categoría)
DROP VIEW IF EXISTS v_skills_por_l1;
CREATE VIEW v_skills_por_l1 AS
SELECT
    L1,
    L1_nombre,
    COUNT(*) as total_menciones,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill,
    SUM(CASE WHEN es_digital = 1 THEN 1 ELSE 0 END) as menciones_digital,
    ROUND(AVG(score), 3) as score_promedio,
    COUNT(DISTINCT skill_esco) as skills_distintas
FROM v_skills_detalle_l1_l2
WHERE L1 IS NOT NULL
GROUP BY L1, L1_nombre
ORDER BY total_menciones DESC;

-- Vista: Agregación por L1 y L2 (dos niveles)
DROP VIEW IF EXISTS v_skills_por_l1_l2;
CREATE VIEW v_skills_por_l1_l2 AS
SELECT
    L1,
    L1_nombre,
    L2,
    L2_nombre,
    COUNT(*) as total_menciones,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill,
    COUNT(DISTINCT skill_esco) as skills_distintas,
    ROUND(AVG(score), 3) as score_promedio
FROM v_skills_detalle_l1_l2
WHERE L1 IS NOT NULL
GROUP BY L1, L1_nombre, L2, L2_nombre
ORDER BY L1, total_menciones DESC;

-- Vista: Skills digitales (es_digital = true)
DROP VIEW IF EXISTS v_skills_digitales;
CREATE VIEW v_skills_digitales AS
SELECT
    skill_esco,
    L1,
    L1_nombre,
    L2,
    L2_nombre,
    COUNT(*) as total_menciones,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill,
    ROUND(AVG(score), 3) as score_promedio
FROM v_skills_detalle_l1_l2
WHERE es_digital = 1
GROUP BY skill_esco, L1, L1_nombre, L2, L2_nombre
ORDER BY total_menciones DESC;

-- Vista: Resumen por ISCO con distribución L1
DROP VIEW IF EXISTS v_isco_skills_l1_profile;
CREATE VIEW v_isco_skills_l1_profile AS
SELECT
    isco_code,
    esco_occupation_label,
    L1,
    L1_nombre,
    COUNT(*) as total_skills,
    COUNT(DISTINCT skill_esco) as skills_distintas,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY isco_code), 1) as pct_del_total
FROM v_skills_detalle_l1_l2
WHERE L1 IS NOT NULL AND isco_code IS NOT NULL
GROUP BY isco_code, esco_occupation_label, L1, L1_nombre
ORDER BY isco_code, total_skills DESC;

-- Vista: Top skills por L1 (las más frecuentes en cada categoría)
DROP VIEW IF EXISTS v_top_skills_por_l1;
CREATE VIEW v_top_skills_por_l1 AS
SELECT
    L1,
    L1_nombre,
    skill_esco,
    total_menciones,
    ofertas_con_skill,
    ranking
FROM (
    SELECT
        L1,
        L1_nombre,
        skill_esco,
        COUNT(*) as total_menciones,
        COUNT(DISTINCT id_oferta) as ofertas_con_skill,
        ROW_NUMBER() OVER (PARTITION BY L1 ORDER BY COUNT(*) DESC) as ranking
    FROM v_skills_detalle_l1_l2
    WHERE L1 IS NOT NULL
    GROUP BY L1, L1_nombre, skill_esco
)
WHERE ranking <= 10;  -- Top 10 por categoría

-- Vista: Resumen general de categorías L1
DROP VIEW IF EXISTS v_resumen_l1;
CREATE VIEW v_resumen_l1 AS
SELECT
    (SELECT COUNT(*) FROM v_skills_detalle_l1_l2) as total_skills,
    (SELECT COUNT(DISTINCT id_oferta) FROM v_skills_detalle_l1_l2) as total_ofertas,
    (SELECT COUNT(DISTINCT skill_esco) FROM v_skills_detalle_l1_l2) as skills_distintas,
    (SELECT COUNT(*) FROM v_skills_detalle_l1_l2 WHERE es_digital = 1) as skills_digitales,
    (SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM v_skills_detalle_l1_l2), 1)
     FROM v_skills_detalle_l1_l2 WHERE es_digital = 1) as pct_digitales,
    (SELECT COUNT(DISTINCT L1) FROM v_skills_detalle_l1_l2) as categorias_l1_usadas,
    (SELECT COUNT(DISTINCT L2) FROM v_skills_detalle_l1_l2 WHERE L2 IS NOT NULL) as categorias_l2_usadas;

-- =====================================================
-- Índices para mejorar performance (opcional)
-- =====================================================
-- No se pueden crear índices en vistas, pero estos índices
-- mejoran las queries sobre la tabla base:
-- CREATE INDEX IF NOT EXISTS idx_matching_skills_json
--     ON ofertas_esco_matching(skills_semantico_json);
-- CREATE INDEX IF NOT EXISTS idx_matching_estado
--     ON ofertas_esco_matching(estado_validacion);
