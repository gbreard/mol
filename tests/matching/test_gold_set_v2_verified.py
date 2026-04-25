# -*- coding: utf-8 -*-
"""
Tests: gold set v2 — casos verificados por validadores humanos.

A diferencia de gold_set.json v1 (boolean esco_ok), este usa isco_esperado
explícito. Fuentes: Cynthia Vázquez + Diego Schleser (2026-04-22/23).

Dos categorías de casos:
  - rule_verified: reglas Rxxx ya aplicadas — test valida que no se rompen.
  - rule_pending: casos que Spec A corrige — test detecta si el fix funcionó.

Uso:
    pytest tests/matching/test_gold_set_v2_verified.py -v
    pytest tests/matching/test_gold_set_v2_verified.py::test_casos_verified_no_rompen -v
    pytest tests/matching/test_gold_set_v2_verified.py::test_casos_pending_corregidos -v

Para ejecutar SOLO los casos de una regla específica:
    pytest tests/matching/test_gold_set_v2_verified.py -v -k "R345"
"""
import pytest
import json
import sqlite3
from pathlib import Path
from collections import defaultdict


GOLD_SET_PATH = Path(__file__).parent / "gold_set_v2.json"


@pytest.fixture(scope="module")
def gold_set():
    """Carga el JSON una sola vez por módulo."""
    with open(GOLD_SET_PATH, encoding='utf-8') as f:
        return json.load(f)["casos"]


@pytest.fixture(scope="module")
def casos_verified(gold_set):
    """Casos con regla ya aplicada — regresión."""
    return [c for c in gold_set if c["categoria"] == "rule_verified"]


@pytest.fixture(scope="module")
def casos_pending(gold_set):
    """Casos pendientes de fix en Spec A."""
    return [c for c in gold_set if c["categoria"] == "rule_pending"]


@pytest.fixture(scope="module")
def db_cursor():
    """Conexión a BD read-only para el módulo."""
    db_path = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"
    if not db_path.exists():
        pytest.skip(f"BD no encontrada: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    yield conn.cursor()
    conn.close()


def _query_isco(cursor, id_oferta):
    """Devuelve (isco_code, esco_label, regla_aplicada, titulo_esco_code) o None."""
    cursor.execute(
        "SELECT isco_code, esco_occupation_label, regla_aplicada, titulo_esco_code "
        "FROM ofertas_esco_matching WHERE id_oferta = ?",
        (id_oferta,)
    )
    row = cursor.fetchone()
    return row if row else None


# ============================================================================
# TESTS INDIVIDUALES PARAMETRIZADOS (uno por caso)
# ============================================================================

def _get_cases(categoria):
    """Helper para parametrizar. Lee JSON al import-time."""
    with open(GOLD_SET_PATH, encoding='utf-8') as f:
        casos = json.load(f)["casos"]
    return [c for c in casos if c["categoria"] == categoria]


@pytest.mark.parametrize("caso", _get_cases("rule_verified"),
                          ids=lambda c: f"{c['id_oferta']}_{c.get('regla_aplicable', 'no-rule')}")
def test_caso_verified(caso, db_cursor):
    """Cada caso verified debe seguir con su ISCO/ESCO esperado."""
    row = _query_isco(db_cursor, caso["id_oferta"])
    assert row is not None, f"Oferta {caso['id_oferta']} no existe en BD"
    isco_actual, esco_actual, regla_actual, esco_code_actual = row

    assert isco_actual == caso["isco_esperado"], (
        f"Oferta {caso['id_oferta']} ({caso['titulo'][:40]}): "
        f"esperaba ISCO {caso['isco_esperado']}, got {isco_actual}. "
        f"Regla aplicada: {regla_actual}"
    )
    # SPEC J: validar también esco_code específico (granularidad real)
    if caso.get("esco_code_esperado"):
        assert esco_code_actual == caso["esco_code_esperado"], (
            f"Oferta {caso['id_oferta']}: "
            f"esperaba esco_code {caso['esco_code_esperado']}, got {esco_code_actual}. "
            f"Regla: {regla_actual}"
        )


@pytest.mark.parametrize("caso", _get_cases("rule_pending"),
                          ids=lambda c: f"{c['id_oferta']}_{c.get('regla_aplicable', 'no-rule')}")
def test_caso_pending(caso, db_cursor):
    """Cada caso pending debe tener el ISCO esperado (verifica Spec A).

    NOTA: Estos tests FALLAN antes de aplicar Spec A. Ese es el punto:
    fallan → aplicamos Spec A → pasan.
    """
    if caso.get("skip_in_test"):
        pytest.skip(caso.get("notas", "skip marcado en JSON"))

    row = _query_isco(db_cursor, caso["id_oferta"])
    assert row is not None, f"Oferta {caso['id_oferta']} no existe en BD"
    isco_actual, esco_actual, regla_actual, esco_code_actual = row

    assert isco_actual == caso["isco_esperado"], (
        f"Oferta {caso['id_oferta']} ({caso['titulo'][:40]}): "
        f"esperaba ISCO {caso['isco_esperado']} (vía regla {caso.get('regla_aplicable', '?')}), "
        f"got {isco_actual}. Fuente: {caso['source']}"
    )


# ============================================================================
# TESTS AGREGADOS: cobertura + sanity checks
# ============================================================================

class TestGoldSetCoverage:
    """Sanity checks sobre el gold set en sí (no sobre la BD)."""

    def test_todos_casos_tienen_isco(self, gold_set):
        """Todo caso debe tener isco_esperado válido (4 dígitos)."""
        for caso in gold_set:
            isco = caso.get("isco_esperado", "")
            assert len(isco) == 4 and isco.isdigit(), \
                f"Caso {caso['id_oferta']}: ISCO inválido '{isco}'"

    def test_todos_casos_tienen_source(self, gold_set):
        """Todo caso debe trazar a un validador humano."""
        for caso in gold_set:
            assert caso.get("source"), f"Caso {caso['id_oferta']} sin source"
            src = caso["source"]
            assert any(v in src for v in ["cynthia", "diego", "verified_manual"]), \
                f"Caso {caso['id_oferta']}: source inválida '{src}'"

    def test_categoria_valida(self, gold_set):
        valid = {"rule_verified", "rule_pending"}
        for caso in gold_set:
            assert caso.get("categoria") in valid, \
                f"Caso {caso['id_oferta']}: categoría inválida"


class TestResumen:
    """Tests de reporte — no fallan, solo informan."""

    def test_resumen_verified_vs_pending(self, casos_verified, casos_pending, db_cursor, capsys):
        """Imprime resumen para consola (pytest -s para verlo)."""
        ok_v = fail_v = 0
        for c in casos_verified:
            row = _query_isco(db_cursor, c["id_oferta"])
            if row and row[0] == c["isco_esperado"]:
                ok_v += 1
            else:
                fail_v += 1

        ok_p = fail_p = 0
        for c in casos_pending:
            row = _query_isco(db_cursor, c["id_oferta"])
            if row and row[0] == c["isco_esperado"]:
                ok_p += 1
            else:
                fail_p += 1

        print(f"\n{'='*60}")
        print(f"GOLD SET v2 — Resumen")
        print(f"{'='*60}")
        print(f"Verified: {ok_v}/{len(casos_verified)} OK, {fail_v} regresiones")
        print(f"Pending:  {ok_p}/{len(casos_pending)} OK, {fail_p} sin fix aún")
        print(f"{'='*60}")

        # No assert — solo informa


# ============================================================================
# TESTS AGRUPADOS POR REGLA (útil para CI/CD)
# ============================================================================

class TestReglasOperariosSpecA:
    """Tests específicos del Spec A (reglas R345-R352).

    Si estos fallan, Spec A no se aplicó o las reglas no están correctamente
    definidas (ej: esco_label no existe, ver commit 43ae1ed5).
    """

    def _check_regla(self, casos_pending, db_cursor, regla_id):
        casos = [c for c in casos_pending if c.get("regla_aplicable") == regla_id]
        if not casos:
            pytest.skip(f"No hay casos pending para regla {regla_id}")
        failures = []
        for c in casos:
            row = _query_isco(db_cursor, c["id_oferta"])
            if not row or row[0] != c["isco_esperado"]:
                failures.append(
                    f"  {c['id_oferta']} ({c['titulo'][:40]}): "
                    f"esperaba {c['isco_esperado']}, got {row[0] if row else 'N/A'}"
                )
        assert not failures, f"Regla {regla_id} no aplicada correctamente:\n" + "\n".join(failures)

    def test_r345_operario_cnc(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R345_operario_cnc")

    def test_r346_operario_corte_laser(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R346_operario_corte_laser")

    def test_r347_operario_metalurgico(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R347_operario_metalurgico")

    def test_r348_operario_plastico_soplado(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R348_operario_plastico_soplado")

    def test_r349_operario_envasado(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R349_operario_envasado")

    def test_r350_operario_deposito(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R350_operario_deposito_logistica")

    def test_r351_operario_despacho(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R351_operario_despacho")

    def test_r352_operario_ensamble_armas(self, casos_pending, db_cursor):
        self._check_regla(casos_pending, db_cursor, "R352_operario_ensamble_armas")
