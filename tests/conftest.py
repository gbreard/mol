# -*- coding: utf-8 -*-
"""
Fixtures compartidos para tests MOL
====================================

Provee conexiones a BD, gold sets, y helpers comunes.
"""

import pytest
import sqlite3
import json
import struct
from pathlib import Path
from typing import Dict, List, Any


# Paths del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
METRICS_PATH = PROJECT_ROOT / "metrics"


# ============================================================================
# FIXTURES: Base de datos
# ============================================================================

@pytest.fixture(scope="session")
def db_path():
    """Path a la base de datos principal."""
    return DATABASE_PATH


@pytest.fixture(scope="function")
def db_connection(db_path):
    """Conexión a la BD que se cierra automáticamente."""
    if not db_path.exists():
        pytest.skip(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """Cursor de BD para consultas."""
    return db_connection.cursor()


# ============================================================================
# FIXTURES: Gold Sets
# ============================================================================

@pytest.fixture(scope="session")
def matching_gold_set():
    """Gold set de matching ESCO (v2)."""
    gold_set_path = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
    if not gold_set_path.exists():
        pytest.skip(f"Gold set not found: {gold_set_path}")
    with open(gold_set_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def nlp_gold_set():
    """Gold set de extracción NLP (placeholder)."""
    gold_set_path = Path(__file__).parent / "nlp" / "gold_set.json"
    if not gold_set_path.exists():
        return []  # Gold set vacío por ahora
    with open(gold_set_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# HELPERS
# ============================================================================

def parse_score(value) -> float:
    """Convierte score que puede ser float, bytes (float32) o None."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0


@pytest.fixture(scope="session")
def score_parser():
    """Helper para parsear scores de BD."""
    return parse_score


# ============================================================================
# FIXTURES: Métricas
# ============================================================================

@pytest.fixture(scope="session")
def metrics_path():
    """Path al directorio de métricas."""
    METRICS_PATH.mkdir(exist_ok=True)
    return METRICS_PATH


class TestResults:
    """Container para resultados de tests."""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details = []

    @property
    def precision(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def add_result(self, id_oferta: str, passed: bool, detail: Dict[str, Any] = None):
        self.total += 1
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        if detail:
            detail['id_oferta'] = id_oferta
            detail['passed'] = passed
            self.details.append(detail)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total': self.total,
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'precision': round(self.precision * 100, 1),
            'details': self.details
        }


@pytest.fixture
def test_results():
    """Container para acumular resultados de tests."""
    return TestResults()
