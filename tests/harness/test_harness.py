#!/usr/bin/env python3
"""SPEC S1C-F0.5-build · Tests binarios del harness de medición.

Criterios de aceptación verificados (cada test es un criterio binario):
  1. El runner corre sobre el Gold Set sin tocar producción (read-only).
  2. La comparación reporta a dos niveles distintos (ISCO-4 y ESCO) con números separados.
  3. Los casos `true` quedan con su target implícito capturado y marcado pendiente.
  4. El baseline se guarda fechado en tests/harness/.
  5. Aislamiento: el snapshot NO es ni pisa database/gold_set_manual_v2.json (regresión vieja).
"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parent
# Los módulos del harness se importan entre sí por nombre simple
# (from ground_truth import ...). Aseguramos que el dir esté en sys.path.
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))
PROJECT_ROOT = HARNESS_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
REGRESSION_FILE = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
FECHA = "2026-06-17"

SNAPSHOT = HARNESS_DIR / f"gold_set_snapshot_{FECHA}.json"
BASELINE_JSON = HARNESS_DIR / f"baseline_{FECHA}.json"
BASELINE_MD = HARNESS_DIR / f"baseline_{FECHA}.md"


# ---- Criterio 5: aislamiento del snapshot ----

def test_snapshot_no_es_la_regresion_vieja():
    """El snapshot del harness es un archivo NUEVO, distinto del de la regresión de 49."""
    assert SNAPSHOT.exists(), "falta el snapshot fechado"
    assert SNAPSHOT.resolve() != REGRESSION_FILE.resolve()
    # La regresión vieja sigue teniendo sus 49 casos (no fue pisada por 113).
    reg = json.loads(REGRESSION_FILE.read_text(encoding="utf-8"))
    assert isinstance(reg, list)
    assert len(reg) == 49, f"la regresión vieja cambió de tamaño: {len(reg)}"


def test_snapshot_tiene_113_y_marca_true_sin_esperado():
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["totales"]["n_casos"] == 113
    # Hay casos true sin esperado explícito (target implícito).
    assert snap["totales"]["n_true_sin_esperado"] > 0
    for c in snap["casos"]:
        if c["esco_ok"] and not c["isco_esperado"] and not c["esco_esperado"]:
            assert c["es_true_sin_esperado"] is True


# ---- Criterio 2: doble nivel resuelto por separado ----

def test_ground_truth_resuelve_dos_niveles():
    from ground_truth import load_ground_truth

    conn = sqlite3.connect(str(DB_PATH))
    try:
        casos = load_ground_truth(SNAPSHOT, conn)
    finally:
        conn.close()
    assert len(casos) == 113
    # ISCO-4 y ESCO son campos independientes (un caso puede tener uno y no el otro).
    con_isco = [c for c in casos if c.isco4_esperado]
    con_esco = [c for c in casos if c.esco_uri_esperado]
    assert len(con_isco) >= 18
    assert len(con_esco) >= 11
    # Los 2 sin resolver a ESCO son ausencias genuinas, marcados explícitamente.
    sin_resolver = [c for c in casos if c.esco_label_sin_resolver]
    assert len(sin_resolver) == 2
    ids_sin = {c.id_oferta for c in sin_resolver}
    assert ids_sin == {"1118027941", "1117984105"}


# ---- Criterio 1: runner read-only ----

def test_runner_no_toca_produccion():
    """Corre el matcher sobre 2 casos y verifica que producción no cambió.

    run_matcher_over_ids con verify_readonly=True lanza RuntimeError si algún
    conteo de tabla de producción cambia. Además comprobamos los conteos a mano.
    """
    from runner import PRODUCTION_TABLES, run_matcher_over_ids

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    ids = [str(c["id_oferta"]) for c in snap["casos"][:2]]

    conn = sqlite3.connect(str(DB_PATH))
    try:
        before = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in PRODUCTION_TABLES}
        recs = run_matcher_over_ids(ids, conn, verify_readonly=True)
        after = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in PRODUCTION_TABLES}
    finally:
        conn.close()
    assert len(recs) == 2
    assert before == after, "el harness modificó conteos de producción"


# ---- Criterio 4: baseline fechado en tests/harness/ ----

def test_baseline_existe_fechado_en_harness():
    assert BASELINE_JSON.exists(), "falta baseline JSON fechado"
    assert BASELINE_MD.exists(), "falta baseline resumen legible"
    assert BASELINE_JSON.parent.resolve() == HARNESS_DIR.resolve()
    b = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    assert b["fecha_baseline"] == FECHA
    assert b["n_casos"] == 113


# ---- Criterio 2 (cont.): el baseline reporta dos niveles con números separados ----

def test_baseline_reporta_dos_niveles_separados():
    b = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    assert "precision_isco4_explicito" in b
    assert "precision_esco_explicito" in b
    assert "precision_isco4_sobre_errores" in b
    assert "precision_esco_sobre_errores" in b
    # Son números independientes (distinto medible/precisión por nivel).
    isco = b["precision_isco4_sobre_errores"]
    esco = b["precision_esco_sobre_errores"]
    assert isco["precision"] is not None
    assert esco["precision"] is not None
    # ISCO-4 sobre errores es mayor que ESCO granular (la brecha real está en ESCO).
    assert isco["precision"] >= esco["precision"]


# ---- Criterio 3: target implícito capturado y marcado pendiente ----

def test_true_sin_esperado_tienen_target_implicito_pendiente():
    b = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    assert b["n_target_implicito_capturado"] > 0
    capturados = [c for c in b["casos"] if c.get("target_implicito")]
    assert len(capturados) == b["n_target_implicito_capturado"]
    for c in capturados:
        ti = c["target_implicito"]
        assert ti["validacion_cyn"] == "pendiente"
        # captura el output del baseline (al menos uno de los dos niveles)
        assert ti["isco4"] is not None or ti["esco_uri"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
