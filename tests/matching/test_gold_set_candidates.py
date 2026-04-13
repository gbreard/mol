# -*- coding: utf-8 -*-
"""
Tests: Gold Set Candidates filter
===================================

Verifica el endpoint de candidatas y la UI.
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
def candidates(supabase):
    r = supabase.rpc('get_gold_set_candidates', {'p_limit': 100}).execute()
    return r.data or []


@pytest.fixture(scope="module")
def gold_set_ids(supabase):
    r = supabase.table('gold_set').select('id_oferta').eq('activo', True).execute()
    return set(row['id_oferta'] for row in (r.data or []))


class TestGoldSetCandidates:

    def test_candidates_excluyen_gold_set_actual(self, candidates, gold_set_ids):
        """Ninguna oferta retornada está en gold_set."""
        in_gs = [c for c in candidates if c['id_oferta'] in gold_set_ids]
        assert len(in_gs) == 0, \
            f"{len(in_gs)} candidates already in gold_set: {[c['id_oferta'] for c in in_gs[:5]]}"

    def test_prioridad_1_primero(self, candidates):
        """P1 aparece antes que P2, P2 antes que P3."""
        if len(candidates) < 2:
            pytest.skip("Not enough candidates to test ordering")

        prioridades = [c['prioridad'] for c in candidates]

        # Verify sorted ascending
        for i in range(len(prioridades) - 1):
            assert prioridades[i] <= prioridades[i + 1], \
                f"Priority order broken at index {i}: P{prioridades[i]} before P{prioridades[i+1]}"

    def test_banner_visible_en_modo_gold_set(self):
        """Validation page has Gold Set banner with progress."""
        page_path = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx")
        if not page_path.exists():
            pytest.skip("Validation page not found")

        content = page_path.read_text()

        assert 'goldSetMode' in content, "goldSetMode state not found"
        assert 'Candidatas Gold Set' in content, "Gold Set toggle button not found"
        assert 'Modo Gold Set' in content, "Gold Set banner text not found"
        assert '49/150' not in content  # Should be dynamic, not hardcoded
        assert 'goldSetStats.total' in content, "Dynamic progress not found"
        assert '/150' in content, "150 target not found in banner"

    def test_badge_razon_visible(self):
        """OfertaList has priority badge with reason."""
        list_path = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard/components/validacion/OfertaList.tsx")
        if not list_path.exists():
            pytest.skip("OfertaList not found")

        content = list_path.read_text()

        assert 'goldSetCandidates' in content, "goldSetCandidates prop not found"
        assert 'PRIORITY_LABELS' in content, "PRIORITY_LABELS not found"
        assert 'Corrección tuya' in content, "P1 label not found"
        assert 'Regla nueva' in content, "P2 label not found"
        assert 'Divergencia' in content, "P3 label not found"
        assert 'Perfil Argentino' in content, "P4 label not found"
        assert 'candidateMap' in content, "candidateMap lookup not found"
