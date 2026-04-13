# -*- coding: utf-8 -*-
"""
Tests M-11 + M-12
==================

M-11: Training pairs ↔ rules linkage
M-12: Rule effectiveness RPC + alert in admin
"""

import pytest
import json
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


@pytest.fixture(scope="module")
def training_pairs():
    tp_path = Path("/mnt/d/OEDE/Webscrapping/config/training_pairs.json")
    if not tp_path.exists():
        tp_path = PROJECT_ROOT / "config" / "training_pairs.json"
    if not tp_path.exists():
        pytest.skip("training_pairs.json not found")
    return json.loads(tp_path.read_text(encoding='utf-8')).get('pares', [])


@pytest.fixture(scope="module")
def matching_rules():
    rules_path = Path("/mnt/d/OEDE/Webscrapping/config/matching_rules_business.json")
    if not rules_path.exists():
        rules_path = PROJECT_ROOT / "config" / "matching_rules_business.json"
    if not rules_path.exists():
        pytest.skip("matching_rules_business.json not found")
    return json.loads(rules_path.read_text(encoding='utf-8')).get('reglas_forzar_isco', {})


# ============================================================
# M-11 Tests
# ============================================================

class TestM11TrainingPairsRules:

    def test_training_pairs_tienen_reglas_generadas(self, training_pairs):
        """Al menos algunos pares tienen reglas_generadas no vacío."""
        with_rules = [p for p in training_pairs if p.get('reglas_generadas')]
        assert len(with_rules) > 0, "No training pairs have reglas_generadas"
        # Should be around 42 based on the run
        assert len(with_rules) >= 10, \
            f"Expected >= 10 pairs with rules, got {len(with_rules)}"

        # Verify format
        for p in with_rules[:5]:
            assert isinstance(p['reglas_generadas'], list)
            for r in p['reglas_generadas']:
                assert r.startswith('R'), f"Rule '{r}' doesn't start with R"

    def test_reglas_tienen_training_pair_id(self, matching_rules):
        """Al menos algunas reglas tienen training_pair_ids en _linaje."""
        with_tp = []
        for rid, r in matching_rules.items():
            if not isinstance(r, dict):
                continue
            tp_ids = r.get('_linaje', {}).get('training_pair_ids')
            if tp_ids:
                with_tp.append(rid)

        assert len(with_tp) > 0, "No rules have training_pair_ids in _linaje"
        assert len(with_tp) >= 10, \
            f"Expected >= 10 rules with training_pair_ids, got {len(with_tp)}"

        # Verify format
        sample_rule = matching_rules[with_tp[0]]
        tp_ids = sample_rule['_linaje']['training_pair_ids']
        assert isinstance(tp_ids, list)
        assert all(tp.startswith('TP-') for tp in tp_ids)


# ============================================================
# M-12 Tests
# ============================================================

class TestM12ReglasEfectividad:

    def test_reporte_incluye_efectividad_reglas(self, supabase):
        """RPC get_reglas_efectividad retorna sección con top 10, sin uso, baja coincidencia."""
        result = supabase.rpc('get_reglas_efectividad', {'p_dias': 30}).execute()

        data = result.data
        assert data is not None

        # Required fields
        assert 'top_10' in data
        assert 'sin_uso_reciente_count' in data
        assert 'baja_coincidencia_count' in data
        assert 'sin_uso_reciente' in data
        assert 'baja_coincidencia' in data

        # top_10 should have entries
        assert len(data['top_10']) > 0, "Expected at least 1 rule in top_10"

        # Each top_10 entry has required fields
        for entry in data['top_10']:
            assert 'regla' in entry
            assert 'usos_total' in entry
            assert 'usos_periodo' in entry
            assert 'pct_coincidencia' in entry

    def test_alerta_reglas_sin_uso(self):
        """Admin metricas page has alert condition for rules sin uso."""
        metricas_path = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard/app/admin/metricas/page.tsx")
        if not metricas_path.exists():
            pytest.skip("metricas page not found")

        content = metricas_path.read_text()

        assert 'sin_uso_reciente_count' in content, \
            "Alert for sin_uso_reciente_count not found in metricas page"
        assert 'baja_coincidencia_count' in content, \
            "Alert for baja_coincidencia_count not found in metricas page"
        assert 'reglas sin uso' in content, \
            "Alert text 'reglas sin uso' not found"
