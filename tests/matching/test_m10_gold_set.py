# -*- coding: utf-8 -*-
"""
Tests M-10: Gold Set dinámico
==============================

Tests de integración contra Supabase real.
Verifica RPCs, migración, sync, y formato compatible.
"""

import pytest
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _get_supabase_client():
    candidates = [
        PROJECT_ROOT / "config" / "supabase_config.json",
        Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json"),
    ]
    for p in candidates:
        if p.exists():
            config = json.loads(p.read_text())
            from supabase import create_client
            return create_client(config['url'], config['service_role_key'])
    return None


@pytest.fixture(scope="module")
def supabase():
    client = _get_supabase_client()
    if not client:
        pytest.skip("Supabase not available")
    return client


# ============================================================
# Tests
# ============================================================

class TestM10GoldSet:

    def test_agregar_caso_correcto(self, supabase):
        """RPC agregar_a_gold_set inserta caso esco_ok=true."""
        result = supabase.rpc('agregar_a_gold_set', {
            'p_id_oferta': '_test_ok_001',
            'p_esco_ok': True,
            'p_comentario': 'Test case correcto',
            'p_agregado_por': 'pytest',
        }).execute()

        assert result.data is not None
        assert result.data['id_oferta'] == '_test_ok_001'
        assert result.data['total'] >= 1

        # Cleanup
        supabase.table('gold_set').delete().eq('id_oferta', '_test_ok_001').execute()

    def test_agregar_caso_con_error(self, supabase):
        """RPC agregar_a_gold_set inserta caso esco_ok=false con tipo_error e isco_esperado."""
        result = supabase.rpc('agregar_a_gold_set', {
            'p_id_oferta': '_test_err_001',
            'p_esco_ok': False,
            'p_tipo_error': 'dominio_incorrecto',
            'p_isco_esperado': '4321',
            'p_esco_esperado': 'Jefe de almacen',
            'p_comentario': 'Test caso error',
            'p_agregado_por': 'pytest',
        }).execute()

        assert result.data is not None

        # Verify fields persisted
        row = supabase.table('gold_set').select('*').eq('id_oferta', '_test_err_001').single().execute()
        assert row.data['esco_ok'] is False
        assert row.data['tipo_error'] == 'dominio_incorrecto'
        assert row.data['isco_esperado'] == '4321'
        assert row.data['esco_esperado'] == 'Jefe de almacen'

        # Cleanup
        supabase.table('gold_set').delete().eq('id_oferta', '_test_err_001').execute()

    def test_no_duplicados_upsert(self, supabase):
        """Insertar mismo id_oferta dos veces → UPSERT, no duplicado."""
        # Insert first
        supabase.rpc('agregar_a_gold_set', {
            'p_id_oferta': '_test_dup_001',
            'p_esco_ok': True,
            'p_comentario': 'Version 1',
            'p_agregado_por': 'pytest',
        }).execute()

        # Upsert with changes
        r2 = supabase.rpc('agregar_a_gold_set', {
            'p_id_oferta': '_test_dup_001',
            'p_esco_ok': False,
            'p_tipo_error': 'homonimia',
            'p_comentario': 'Version 2 — changed to error',
            'p_agregado_por': 'pytest',
        }).execute()

        assert r2.data['is_update'] is True

        # Verify only 1 row
        rows = supabase.table('gold_set').select('id').eq('id_oferta', '_test_dup_001').execute()
        assert len(rows.data) == 1

        # Verify updated
        row = supabase.table('gold_set').select('esco_ok,comentario').eq('id_oferta', '_test_dup_001').single().execute()
        assert row.data['esco_ok'] is False
        assert 'Version 2' in row.data['comentario']

        # Cleanup
        supabase.table('gold_set').delete().eq('id_oferta', '_test_dup_001').execute()

    def test_sync_genera_json_compatible(self, supabase):
        """sync_gold_set.py genera JSON compatible con test_gold_set_manual.py."""
        gold_set_path = Path("/mnt/d/OEDE/Webscrapping/database/gold_set_manual_v2.json")
        if not gold_set_path.exists():
            pytest.skip("gold_set_manual_v2.json not found in main repo")

        data = json.loads(gold_set_path.read_text(encoding='utf-8'))

        # Must be a list
        assert isinstance(data, list)

        # Each entry must have id_oferta and esco_ok
        for entry in data:
            assert 'id_oferta' in entry, f"Missing id_oferta in {entry}"
            assert 'esco_ok' in entry, f"Missing esco_ok in {entry}"
            assert isinstance(entry['esco_ok'], bool)

        # Error entries must have tipo_error
        errors = [e for e in data if not e['esco_ok']]
        for e in errors:
            assert 'tipo_error' in e or 'comentario' in e, \
                f"Error entry {e['id_oferta']} missing tipo_error and comentario"

    def test_kpi_muestra_49_post_migracion(self, supabase):
        """get_gold_set_stats retorna 49 total después de migración."""
        result = supabase.rpc('get_gold_set_stats').execute()

        stats = result.data
        assert stats is not None
        assert stats['total'] == 49, f"Expected 49, got {stats['total']}"
        assert stats['correctos'] == 40
        assert stats['errores'] == 9
        assert 'por_tipo_error' in stats
        assert 'agregados_este_mes' in stats

    def test_alerta_aparece_bajo_100(self):
        """KPI card shows alert when gold set < 100."""
        metricas_path = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard/app/admin/metricas/page.tsx")
        if not metricas_path.exists():
            pytest.skip("metricas page not found")

        content = metricas_path.read_text()

        # Verify alert condition exists
        assert 'goldSetStats.total < 100' in content, \
            "Alert condition goldSetStats.total < 100 not found"
        assert '150 para habilitar' in content, \
            "Alert text about 150 threshold not found"
        assert 'Alt+6' in content, \
            "Alt+6 shortcut reference not found in alert"
