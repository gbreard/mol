# -*- coding: utf-8 -*-
"""
Tests de performance — Migration 024.1
========================================

Verifica que los filtros nuevos cumplen el SLA de performance:
- datos_incompletos: < 50 ms (count + filter LIMIT)
- estado_revision IS NULL: < 100 ms (filter LIMIT 50)

Refs:
    docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (D8)
    migrations/024_1_spec_w_performance_filtros.sql

NOTA: estado_revision IS NULL en modo "count exact" tarda ~2.8s sobre
68K filas porque la mayoría (98%) son NULL. Eso es esperado y se mitiga
en el frontend con `count: 'planned'`. Este test NO chequea ese caso.
"""

import json
import re
from pathlib import Path

import httpx
import pytest


CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "supabase_config.json"


@pytest.fixture(scope="module")
def explain_query():
    if not CONFIG_PATH.exists():
        pytest.skip(f"Missing config: {CONFIG_PATH}")
    cfg = json.loads(CONFIG_PATH.read_text())
    ref = cfg["project_ref"]
    token = cfg["management_api_token"]
    endpoint = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def run(sql: str):
        r = httpx.post(endpoint, headers=headers, json={"query": sql}, timeout=60)
        assert r.status_code < 400, f"query failed: {r.text}"
        return r.json()

    return run


def _extract_execution_time_ms(plan_rows) -> float:
    """Extrae 'Execution Time: X ms' del output de EXPLAIN ANALYZE."""
    for row in plan_rows:
        line = row.get("QUERY PLAN", "")
        match = re.search(r"Execution Time:\s*([\d.]+)\s*ms", line)
        if match:
            return float(match.group(1))
    raise AssertionError(f"No Execution Time line found in plan: {plan_rows}")


def test_datos_incompletos_filter_under_50ms(explain_query):
    plan = explain_query(
        "EXPLAIN ANALYZE SELECT COUNT(*) FROM ofertas_dashboard WHERE datos_incompletos = true;"
    )
    ms = _extract_execution_time_ms(plan)
    assert ms < 50, f"datos_incompletos count tardó {ms} ms (esperado < 50ms)"


def test_estado_revision_pendiente_filter_under_100ms(explain_query):
    plan = explain_query(
        "EXPLAIN ANALYZE SELECT id_oferta FROM ofertas_dashboard WHERE estado_revision IS NULL LIMIT 50;"
    )
    ms = _extract_execution_time_ms(plan)
    assert ms < 100, f"estado_revision IS NULL LIMIT 50 tardó {ms} ms (esperado < 100ms)"


def test_datos_incompletos_count_matches_expected(explain_query):
    rows = explain_query(
        "SELECT COUNT(*) FROM ofertas_dashboard WHERE datos_incompletos = true;"
    )
    assert len(rows) == 1
    count = rows[0]["count"]
    # Esperamos un rango razonable post-migration (~3-7K ofertas, 5-10% del total).
    assert 1000 < count < 15000, (
        f"datos_incompletos count = {count} fuera del rango esperado 1K–15K"
    )


def test_estado_revision_pendiente_count_returns_value(explain_query):
    """Smoke test: el filtro devuelve un valor coherente con el universo."""
    rows = explain_query(
        "SELECT COUNT(*) FROM ofertas_dashboard WHERE estado_revision IS NULL;"
    )
    assert len(rows) == 1
    pending_count = rows[0]["count"]

    total_rows = explain_query("SELECT COUNT(*) FROM ofertas_dashboard;")
    total = total_rows[0]["count"]

    # Inicialmente prácticamente todo el universo (98%+) está pendiente.
    assert pending_count > total * 0.9, (
        f"pendientes={pending_count} debería ser > 90% del total ({total})"
    )


def test_datos_incompletos_uses_index(explain_query):
    """Confirma que el planner usa el índice parcial (no Seq Scan)."""
    plan = explain_query(
        "EXPLAIN ANALYZE SELECT COUNT(*) FROM ofertas_dashboard WHERE datos_incompletos = true;"
    )
    plan_text = "\n".join(r["QUERY PLAN"] for r in plan)
    assert "idx_ofertas_datos_incompletos" in plan_text, (
        f"Planner no usó idx_ofertas_datos_incompletos. Plan:\n{plan_text}"
    )


def test_estado_revision_pendiente_uses_index(explain_query):
    """Confirma que el LIMIT con IS NULL usa el índice parcial."""
    plan = explain_query(
        "EXPLAIN ANALYZE SELECT id_oferta FROM ofertas_dashboard WHERE estado_revision IS NULL LIMIT 50;"
    )
    plan_text = "\n".join(r["QUERY PLAN"] for r in plan)
    assert "idx_ofertas_dashboard_estado_pendiente" in plan_text, (
        f"Planner no usó idx_ofertas_dashboard_estado_pendiente. Plan:\n{plan_text}"
    )
