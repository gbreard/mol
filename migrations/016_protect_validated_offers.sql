-- Migration 016: Protección de Ofertas Validadas
-- Fecha: 2026-01-20
-- Propósito: Defense in depth - triggers que previenen modificación de ofertas validadas
--
-- PROBLEMA RESUELTO:
-- Ofertas con estado_validacion='validado' estaban siendo reprocesadas accidentalmente
-- porque algunos scripts no tenían filtros adecuados.
--
-- SOLUCIÓN:
-- 1. Trigger que bloquea UPDATE de campos de matching en ofertas validadas
-- 2. Trigger que solo permite transición validado -> en_revision (desbloqueo admin)
--
-- USO:
-- Para desbloquear una oferta validada (caso excepcional):
--   python scripts/admin_unlock_validated.py --ids 123,456 --motivo "razón"

-- ============================================
-- TRIGGER 1: Bloquear UPDATE de matching data
-- ============================================
-- Previene cambios en isco_code, score, etc. cuando estado='validado'
-- EXCEPTO si se está cambiando el estado (transición de desbloqueo)

DROP TRIGGER IF EXISTS protect_validated_matching;

CREATE TRIGGER protect_validated_matching
BEFORE UPDATE ON ofertas_esco_matching
WHEN OLD.estado_validacion = 'validado'
  AND NEW.estado_validacion = 'validado'  -- Solo bloquea si NO es cambio de estado
  AND (
    OLD.isco_code != NEW.isco_code OR
    OLD.esco_occupation_label != NEW.esco_occupation_label OR
    OLD.occupation_match_score != NEW.occupation_match_score
  )
BEGIN
    SELECT RAISE(ABORT, 'ERROR: No se puede modificar oferta validada. Use admin_unlock_validated.py primero para desbloquearla.');
END;

-- ============================================
-- TRIGGER 2: Controlar transiciones de estado
-- ============================================
-- Solo permite: validado -> en_revision (para desbloqueo admin)
-- Bloquea: validado -> pendiente, validado -> rechazado, etc.

DROP TRIGGER IF EXISTS protect_validated_status;

CREATE TRIGGER protect_validated_status
BEFORE UPDATE OF estado_validacion ON ofertas_esco_matching
WHEN OLD.estado_validacion = 'validado'
  AND NEW.estado_validacion NOT IN ('validado', 'en_revision')
BEGIN
    SELECT RAISE(ABORT, 'ERROR: Oferta validada solo puede pasar a en_revision. Use admin_unlock_validated.py.');
END;

-- ============================================
-- VISTA: Verificar ofertas protegidas
-- ============================================
DROP VIEW IF EXISTS v_ofertas_protegidas;

CREATE VIEW v_ofertas_protegidas AS
SELECT
    estado_validacion,
    COUNT(*) as cantidad,
    CASE estado_validacion
        WHEN 'validado' THEN 'PROTEGIDA - No se puede modificar'
        WHEN 'descartado' THEN 'PROTEGIDA - No se puede modificar'
        WHEN 'en_revision' THEN 'DESBLOQUEDA - Se puede reprocesar'
        WHEN 'pendiente' THEN 'NORMAL - Se puede reprocesar'
        ELSE 'NORMAL - Se puede reprocesar'
    END as proteccion
FROM ofertas_esco_matching
GROUP BY estado_validacion
ORDER BY cantidad DESC;

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Listar triggers creados
SELECT name, sql FROM sqlite_master
WHERE type = 'trigger'
AND name LIKE 'protect%';
