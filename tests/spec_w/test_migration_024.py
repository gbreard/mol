# -*- coding: utf-8 -*-
"""
Tests SPEC W Etapa 1 — Migration 024
=====================================

Verifica que el schema de `audit_actions` + columnas nuevas en
`ofertas_dashboard` está aplicado correctamente y que el trigger de
inmutabilidad funciona.

Refs:
    docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.1
    docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (D1, D3, D5)
    migrations/024_spec_w_audit_actions.sql

Los tests corren contra la BD real de Supabase via Management API.
"""

import json
from pathlib import Path

import httpx
import pytest


CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "supabase_config.json"


@pytest.fixture(scope="module")
def supabase_query():
    if not CONFIG_PATH.exists():
        pytest.skip(f"Missing config: {CONFIG_PATH}")
    cfg = json.loads(CONFIG_PATH.read_text())
    ref = cfg["project_ref"]
    token = cfg["management_api_token"]
    endpoint = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def run(sql: str):
        return httpx.post(endpoint, headers=headers, json={"query": sql}, timeout=30)

    return run


def _ok(response: httpx.Response):
    assert response.status_code < 400, f"Query failed: {response.text}"
    return response.json()


def _expect_error(response: httpx.Response, substring: str):
    assert response.status_code >= 400, (
        f"Expected error but got {response.status_code}: {response.text}"
    )
    assert substring in response.text, (
        f"Expected error message to contain '{substring}', got: {response.text}"
    )


def test_audit_actions_table_exists(supabase_query):
    rows = _ok(supabase_query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name='audit_actions';
    """))
    assert len(rows) == 1, "audit_actions table not found in public schema"


def test_audit_actions_columns(supabase_query):
    rows = _ok(supabase_query("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='audit_actions'
        ORDER BY ordinal_position;
    """))

    by_name = {r["column_name"]: r for r in rows}
    expected = {
        "id": ("bigint", "NO"),
        "id_oferta": ("text", "NO"),
        "validador": ("text", "NO"),
        "timestamp": ("timestamp without time zone", "YES"),
        "action_type": ("text", "NO"),
        "target_type": ("text", "YES"),
        "target_id": ("text", "YES"),
        "target_value": ("text", "YES"),
        "note": ("text", "YES"),
        "run_id": ("text", "YES"),
        "matching_version": ("text", "YES"),
        "source": ("text", "NO"),
    }
    assert set(by_name.keys()) == set(expected.keys()), (
        f"Column set mismatch. Expected {set(expected)}, got {set(by_name)}"
    )
    for col, (data_type, is_nullable) in expected.items():
        assert by_name[col]["data_type"] == data_type, (
            f"{col}: expected {data_type}, got {by_name[col]['data_type']}"
        )
        assert by_name[col]["is_nullable"] == is_nullable, (
            f"{col}: expected nullable={is_nullable}, got {by_name[col]['is_nullable']}"
        )


def test_audit_actions_check_constraints(supabase_query):
    # action_type inválido debe fallar
    r = supabase_query("""
        INSERT INTO audit_actions (id_oferta, validador, action_type)
        VALUES ('TEST_INVALID_ACTION', 'test@test.com', 'invent_action');
    """)
    _expect_error(r, "audit_actions_action_type_check")

    # source inválido debe fallar
    r = supabase_query("""
        INSERT INTO audit_actions (id_oferta, validador, action_type, source)
        VALUES ('TEST_INVALID_SOURCE', 'test@test.com', 'mark_revised', 'martian');
    """)
    _expect_error(r, "audit_actions_source_check")

    # target_type inválido debe fallar
    r = supabase_query("""
        INSERT INTO audit_actions (id_oferta, validador, action_type, target_type)
        VALUES ('TEST_INVALID_TARGET', 'test@test.com', 'mark_revised', 'planet');
    """)
    _expect_error(r, "audit_actions_target_type_check")


def test_audit_actions_no_update(supabase_query):
    # Insertar fila para probar (cada test usa id_oferta único)
    r = _ok(supabase_query("""
        INSERT INTO audit_actions (id_oferta, validador, action_type, source)
        VALUES ('TEST_NO_UPDATE', 'test@test.com', 'mark_revised', 'human')
        RETURNING id;
    """))
    assert len(r) == 1
    inserted_id = r[0]["id"]

    # UPDATE debe fallar
    upd = supabase_query(f"""
        UPDATE audit_actions SET validador='hacker' WHERE id={inserted_id};
    """)
    _expect_error(upd, "append-only")


def test_audit_actions_no_delete(supabase_query):
    r = _ok(supabase_query("""
        INSERT INTO audit_actions (id_oferta, validador, action_type, source)
        VALUES ('TEST_NO_DELETE', 'test@test.com', 'mark_revised', 'human')
        RETURNING id;
    """))
    assert len(r) == 1
    inserted_id = r[0]["id"]

    delr = supabase_query(f"DELETE FROM audit_actions WHERE id={inserted_id};")
    _expect_error(delr, "append-only")


def test_ofertas_dashboard_new_columns(supabase_query):
    rows = _ok(supabase_query("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name='ofertas_dashboard'
          AND column_name IN ('estado_revision', 'denominacion_arg', 'denominacion_esp')
        ORDER BY column_name;
    """))
    found = {r["column_name"]: r["data_type"] for r in rows}
    assert found == {
        "denominacion_arg": "text",
        "denominacion_esp": "text",
        "estado_revision": "text",
    }, f"Expected 3 new columns, got: {found}"


def test_estado_revision_check_constraint(supabase_query):
    # Encontrar una oferta cualquiera para probar el constraint sin tocar prod
    r = _ok(supabase_query("""
        SELECT id_oferta FROM ofertas_dashboard LIMIT 1;
    """))
    if not r:
        pytest.skip("No hay ofertas en ofertas_dashboard para test de constraint")
    sample_id = r[0]["id_oferta"]

    # Capturar valor actual para restaurar al final
    current = _ok(supabase_query(f"""
        SELECT estado_revision FROM ofertas_dashboard
        WHERE id_oferta='{sample_id}';
    """))
    original = current[0]["estado_revision"]

    try:
        # Valor inválido debe fallar
        bad = supabase_query(f"""
            UPDATE ofertas_dashboard SET estado_revision='basura'
            WHERE id_oferta='{sample_id}';
        """)
        _expect_error(bad, "ofertas_dashboard_estado_revision_check")

        # Valores válidos deben funcionar
        for valid in ("revisada", "mal_extraida_total"):
            ok = supabase_query(f"""
                UPDATE ofertas_dashboard SET estado_revision='{valid}'
                WHERE id_oferta='{sample_id}';
            """)
            assert ok.status_code < 400, f"valid value '{valid}' rejected: {ok.text}"

        # NULL también debe funcionar
        ok_null = supabase_query(f"""
            UPDATE ofertas_dashboard SET estado_revision=NULL
            WHERE id_oferta='{sample_id}';
        """)
        assert ok_null.status_code < 400
    finally:
        # Restaurar valor original
        original_sql = "NULL" if original is None else f"'{original}'"
        supabase_query(f"""
            UPDATE ofertas_dashboard SET estado_revision={original_sql}
            WHERE id_oferta='{sample_id}';
        """)
