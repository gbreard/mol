# -*- coding: utf-8 -*-
"""
Tests E4.3: Dataset consolidation
===================================

Valida que dataset_summary.json:
1. Existe y es JSON válido
2. Conteos coinciden con suma de fuentes
3. Go/no-go calculado correctamente
4. Gap calculado correctamente
"""

import pytest
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FT_DIR = PROJECT_ROOT / "data" / "fine_tuning"
SUMMARY_PATH = FT_DIR / "dataset_summary.json"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def summary():
    if not SUMMARY_PATH.exists():
        pytest.skip("dataset_summary.json not found — run consolidate_training_dataset.py first")
    with open(SUMMARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def count_file(name):
    """Count items in a JSON array file."""
    path = FT_DIR / name
    if not path.exists():
        # Fallback for gold set
        path = PROJECT_ROOT / "database" / name
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding='utf-8'))
    return len(data) if isinstance(data, list) else 0


# ============================================================
# Tests
# ============================================================

class TestDatasetConsolidation:

    def test_dataset_summary_generado(self, summary):
        """dataset_summary.json existe y es JSON válido."""
        assert "generado_at" in summary
        assert "fuentes" in summary
        assert "totales" in summary
        assert isinstance(summary["fuentes"], dict)
        assert isinstance(summary["totales"], dict)

    def test_conteos_correctos(self, summary):
        """Totales coinciden con suma de fuentes."""
        fuentes = summary["fuentes"]

        # Sum alta confianza training sources (not gold set)
        alta_sum = sum(
            fuentes[k]["pares"]
            for k in ["train_human", "train_correcciones", "train_argentino"]
        )
        assert summary["totales"]["entrenamiento_alta_confianza"] == alta_sum, \
            f"Expected {alta_sum}, got {summary['totales']['entrenamiento_alta_confianza']}"

        # Sum validation
        val_sum = fuentes["validation_auto"]["pares"] + fuentes["validation_gold"]["pares"]
        assert summary["totales"]["validacion"] == val_sum, \
            f"Expected {val_sum}, got {summary['totales']['validacion']}"

        # Verify against actual files
        actual_human = count_file("train_human.json")
        actual_argentino = count_file("train_argentino.json")
        actual_validation = count_file("validation_auto.json")

        assert fuentes["train_human"]["pares"] == actual_human
        assert fuentes["train_argentino"]["pares"] == actual_argentino
        assert fuentes["validation_auto"]["pares"] == actual_validation

    def test_go_no_go_calculado(self, summary):
        """listo_para_fine_tuning = false (aún no cumple criterios)."""
        go = summary["totales"]["go_no_go"]
        assert "listo_para_fine_tuning" in go
        assert go["listo_para_fine_tuning"] is False, \
            "Expected listo_para_fine_tuning=false (not enough data yet)"

        # Verify thresholds
        assert go["pares_requeridos"] == 500
        assert go["gold_set_requerido"] == 150

    def test_gap_calculado_correctamente(self, summary):
        """gap = pares_requeridos - total_alta_confianza."""
        go = summary["totales"]["go_no_go"]
        expected_gap = go["pares_requeridos"] - go["pares_actuales"]
        assert go["gap"] == expected_gap, \
            f"Expected gap={expected_gap}, got {go['gap']}"

        expected_gold_gap = go["gold_set_requerido"] - go["gold_set_actual"]
        assert go["gap_gold_set"] == expected_gold_gap, \
            f"Expected gold gap={expected_gold_gap}, got {go['gap_gold_set']}"

        # gap should be positive (we don't have enough data)
        assert go["gap"] > 0, "Gap should be > 0 (not enough training data)"
        assert go["gap_gold_set"] > 0, "Gold gap should be > 0 (not enough gold set)"
