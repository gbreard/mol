# -*- coding: utf-8 -*-
"""
Tests: Auto-transición pendiente → validado_claude
====================================================

Verifica la política de transición automática:
- Ofertas sin errores bloqueantes → validado_claude
- Ofertas con V10/V02/NV02 → quedan pendiente
- Errores info/warning/bajo no bloquean
"""

import pytest
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Import the function under test
import sys
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "database"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


@pytest.fixture(scope="module")
def policy():
    """Load transition policy."""
    vr_path = PROJECT_ROOT / "config" / "validation_rules.json"
    if not vr_path.exists():
        vr_path = Path("/mnt/d/OEDE/Webscrapping/config/validation_rules.json")
    vr = json.loads(vr_path.read_text(encoding='utf-8'))
    return vr.get("politica_transicion", {})


@pytest.fixture(scope="module")
def db_conn():
    """Connection to real DB for integration checks."""
    db_path = Path("/mnt/d/OEDE/Webscrapping/database/bumeran_scraping.db")
    if not db_path.exists():
        db_path = PROJECT_ROOT / "database" / "bumeran_scraping.db"
    if not db_path.exists():
        pytest.skip("Database not found")
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestAutoTransicion:

    def test_oferta_sin_errores_transiciona(self, policy):
        """Oferta sin errores bloqueantes → validado_claude."""
        bloqueantes = set(policy.get("errores_bloqueantes", []))

        # V14 is not in bloqueantes
        assert "V14_descripcion_muy_corta" not in bloqueantes
        # V24 is not in bloqueantes
        assert "V24_skills_baja_coherencia" not in bloqueantes
        # V27 is not in bloqueantes
        assert "V27_divergencia_dual" not in bloqueantes

        # An offer with only these errors should transition
        # (verified by policy, not DB - unit test)
        mock_errors = {"V14_descripcion_muy_corta", "V24_skills_baja_coherencia"}
        has_blocking = bool(mock_errors & bloqueantes)
        assert not has_blocking, "V14+V24 should NOT block transition"

    def test_oferta_con_v10_no_transiciona(self, policy):
        """Oferta con V10 → queda pendiente."""
        bloqueantes = set(policy.get("errores_bloqueantes", []))
        assert "V10_match_score_muy_bajo" in bloqueantes

        mock_errors = {"V10_match_score_muy_bajo", "V14_descripcion_muy_corta"}
        has_blocking = bool(mock_errors & bloqueantes)
        assert has_blocking, "V10 should block transition"

    def test_oferta_con_v14_transiciona(self, policy):
        """V14 (descripción corta) no es bloqueante."""
        bloqueantes = set(policy.get("errores_bloqueantes", []))
        no_bloqueantes = set(policy.get("errores_no_bloqueantes", []))

        assert "V14_descripcion_muy_corta" in no_bloqueantes
        assert "V14_descripcion_muy_corta" not in bloqueantes

    def test_batch_transicion_7101(self, db_conn):
        """Post-transición: ~2 pendiente (V10+NV02), rest validado_claude."""
        pendientes = db_conn.execute(
            "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = 'pendiente'"
        ).fetchone()[0]

        validado_claude = db_conn.execute(
            "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = 'validado_claude'"
        ).fetchone()[0]

        # After transition: only 2 should remain pendiente
        assert pendientes <= 5, \
            f"Expected <= 5 pendientes after batch transition, got {pendientes}"

        # validado_claude should be the vast majority
        assert validado_claude >= 36000, \
            f"Expected >= 36000 validado_claude, got {validado_claude}"

        # The 2 pendientes should have blocking errors
        if pendientes > 0:
            blocked = db_conn.execute("""
                SELECT m.id_oferta, e.error_id
                FROM ofertas_esco_matching m
                JOIN validation_errors e ON e.id_oferta = m.id_oferta
                WHERE m.estado_validacion = 'pendiente'
                AND e.resuelto = 0
                AND e.error_id IN ('V02_isco_nulo_score_bajo', 'V10_match_score_muy_bajo', 'NV02_sector_no_canonico')
            """).fetchall()
            assert len(blocked) > 0, \
                "Pendiente offers should have blocking errors"
