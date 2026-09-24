-- 069_switch_estado_ciclo.sql
-- Fase 5 (Etapa C) — EL SWITCH. NO EJECUTAR TODAVIA.
--
-- Este es el UNICO objeto server-side a migrar. El inventario contra la base
-- (068) devolvio 22 funciones que tocan ofertas_dashboard y NINGUNA filtra por
-- estado; la unica que lo usa es esta vista. Definicion original en
-- 004_catalogos_esco.sql:196-211.
--
-- PRECONDICIONES
--   1. 067 ejecutado; las 6 columnas existen.
--   2. estado_ciclo poblado en ofertas_dashboard (B.4).
--   3. El codigo del dashboard que lee `estado` ya desplegado leyendo
--      estado_ciclo. Esto se ejecuta JUNTO con ese deploy, no antes.
--
-- QUE CAMBIA PARA EL USUARIO
-- El legacy declaraba baja a toda oferta no vista en la ultima corrida, y el
-- scraping de Bumeran es rotativo (165 de 1.148 keywords por dia): el filtro
-- barria casi todo. Con estado_ciclo el universo de ofertas activas detras de
-- esta vista pasa de un puñado a ~7 mil. Las empresas no aparecen: estaban, y
-- el filtro roto las escondia.
--
-- ROLLBACK: `estado` se sigue poblando en paralelo una semana mas. Volver es
-- re-ejecutar la definicion vieja (al pie).

CREATE OR REPLACE VIEW v_empresas_activas AS
SELECT
    e.id,
    e.nombre,
    e.sector,
    e.tamano,
    e.provincia_sede,
    e.ofertas_activas,
    COUNT(o.id_oferta) as ofertas_actuales
FROM empresas e
LEFT JOIN ofertas_dashboard o ON e.nombre_normalizado = LOWER(TRIM(o.empresa))
WHERE o.estado_ciclo = 'activa'        -- <<< UNICO CAMBIO. Era: o.estado = 'activa'
GROUP BY e.id
HAVING e.ofertas_activas > 0 OR COUNT(o.id_oferta) > 0
ORDER BY ofertas_actuales DESC;

-- ---------------------------------------------------------------------------
-- OBSERVACION (no se corrige aca; es una decision aparte)
-- ---------------------------------------------------------------------------
-- El WHERE sobre `o` anula el LEFT JOIN: una empresa sin ofertas activas se
-- descarta en el WHERE antes de llegar al HAVING, asi que la rama
-- `e.ofertas_activas > 0` del HAVING esta muerta. Si la intencion era listar
-- tambien empresas conocidas sin ofertas vivas, la condicion va en el ON:
--     LEFT JOIN ofertas_dashboard o
--            ON e.nombre_normalizado = LOWER(TRIM(o.empresa))
--           AND o.estado_ciclo = 'activa'
-- Cambiarlo altera el conjunto de filas mas alla del switch, asi que queda
-- fuera de la Etapa C: mezclarlo haria imposible atribuir el salto de numeros.
--
-- ---------------------------------------------------------------------------
-- VERIFICACION (correr despues)
-- ---------------------------------------------------------------------------
-- SELECT COUNT(*) AS empresas, SUM(ofertas_actuales) AS ofertas
--   FROM v_empresas_activas;
--
-- ---------------------------------------------------------------------------
-- ROLLBACK
-- ---------------------------------------------------------------------------
-- Identica, con  WHERE o.estado = 'activa'
