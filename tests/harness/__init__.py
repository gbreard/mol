"""Harness de medición de ocupación (SPEC S1C-F0.5-build).

Infraestructura read-only para medir la precisión del matcher de ocupación
contra el Gold Set, a doble nivel (ISCO-4 + ESCO granular).

NO persiste en producción. NO toca los gold sets preexistentes
(database/gold_set_manual_v2.json es de la regresión vieja de 49 casos).
Los snapshots y baselines viven solo en tests/harness/.
"""
