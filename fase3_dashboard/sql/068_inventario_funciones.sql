-- 068_inventario_funciones.sql
-- Fase 5 (B.3) — INVENTARIO, SOLO LECTURA. No modifica nada.
--
-- POR QUE
-- El grep del repo encontro UNA sola funcion que filtra ofertas por estado
-- (004_catalogos_esco.sql:208, dentro de buscar_skill). Es sospechosamente poco
-- para lo que el §8 de la spec anticipaba, y la hipotesis es que hay funciones y
-- vistas creadas directamente en el SQL Editor que nunca se versionaron en
-- fase3_dashboard/sql/. Si el switch de la Etapa C se hace contra el inventario
-- del repo, esos consumidores quedan leyendo `estado` (legacy) mientras el resto
-- del sistema pasa a `estado_ciclo`, y el panel muestra numeros inconsistentes
-- entre secciones.
--
-- Este script lista el universo REAL de la base. Ejecutar en la misma sesion de
-- SQL Editor que el 067 y pegar los tres outputs.

-- ---------------------------------------------------------------------------
-- CONSULTA 1 — funciones que mencionan 'estado' en su definicion
-- ---------------------------------------------------------------------------
-- Incluye RPCs del dashboard y triggers. La definicion completa permite ver
-- CUAL estado usan: el de ofertas_dashboard (lo que hay que migrar) o el de
-- otra tabla (issues, emergentes, solicitudes: NO se tocan).
SELECT
    p.proname                                        AS funcion,
    pg_get_function_identity_arguments(p.oid)        AS argumentos,
    pg_get_functiondef(p.oid)                        AS definicion
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND pg_get_functiondef(p.oid) ILIKE '%estado%'
ORDER BY p.proname;

-- ---------------------------------------------------------------------------
-- CONSULTA 2 — vistas que mencionan 'estado'
-- ---------------------------------------------------------------------------
SELECT
    viewname   AS vista,
    definition AS definicion
FROM pg_views
WHERE schemaname = 'public'
  AND definition ILIKE '%estado%'
ORDER BY viewname;

-- ---------------------------------------------------------------------------
-- CONSULTA 3 — el subconjunto que importa: lo que toca ofertas_dashboard
-- ---------------------------------------------------------------------------
-- Las dos consultas anteriores traen ruido (la mayoria de los `estado` del
-- sistema son de issues/emergentes/solicitudes). Esta acota a lo que realmente
-- hay que migrar en la Etapa C: funciones y vistas que mencionan a la vez
-- ofertas_dashboard y estado.
SELECT 'funcion' AS tipo, p.proname AS nombre
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND pg_get_functiondef(p.oid) ILIKE '%ofertas_dashboard%'
  AND pg_get_functiondef(p.oid) ILIKE '%estado%'
UNION ALL
SELECT 'vista' AS tipo, viewname AS nombre
FROM pg_views
WHERE schemaname = 'public'
  AND definition ILIKE '%ofertas_dashboard%'
  AND definition ILIKE '%estado%'
ORDER BY tipo, nombre;

-- ---------------------------------------------------------------------------
-- QUE HACER CON EL OUTPUT
-- ---------------------------------------------------------------------------
-- La CONSULTA 3 es la lista de trabajo de B.3: por cada nombre que aparezca se
-- prepara el diff a estado_ciclo, y todos se aplican JUNTOS en el switch de la
-- Etapa C (no antes: mientras el dashboard lea `estado`, cambiar una funcion
-- suelta desincroniza el panel).
--
-- Si la CONSULTA 3 devuelve solo `buscar_skill`, el inventario del repo estaba
-- completo y la sospecha era infundada — tambien es un resultado util.
