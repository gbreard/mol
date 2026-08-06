-- 026 — Observabilidad del traductor (FRENTE H, P0.a.2, 2026-08-06)
-- Nuevo valor de occupation_match_method: 'arbol_contexto' (el evaluador de las
-- reglas de contexto de Cyn). Estas columnas persisten su traza completa:
--   arbol_hub_id     → id (1..88) del hub del JSON 2.0 que decidió
--   arbol_regla_id   → regla que decidió (p.ej. 'D03' o 'inclusion')
--   arbol_camino     → 'D_directa' | 'inclusion' | 'convergencia'
--   arbol_traza_json → traza completa: hubs evaluados, términos matcheados y
--                      EL CAMPO de cada match (guarda b del laudo D3)
-- NULL para todo método distinto de arbol_contexto.

ALTER TABLE ofertas_esco_matching ADD COLUMN arbol_hub_id INTEGER;
ALTER TABLE ofertas_esco_matching ADD COLUMN arbol_regla_id TEXT;
ALTER TABLE ofertas_esco_matching ADD COLUMN arbol_camino TEXT;
ALTER TABLE ofertas_esco_matching ADD COLUMN arbol_traza_json TEXT;

CREATE INDEX IF NOT EXISTS idx_matching_arbol_hub ON ofertas_esco_matching(arbol_hub_id);
