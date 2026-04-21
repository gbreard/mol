# -*- coding: utf-8 -*-
"""
Tests M-10 Parte 2: Gold Set con skills esperadas
===================================================
"""

import pytest
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
GOLD_SET_PATH = Path("/mnt/d/OEDE/Webscrapping/database/gold_set_manual_v2.json")


def _get_supabase_client():
    for p in [PROJECT_ROOT / "config" / "supabase_config.json",
              Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json")]:
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


class TestM10GoldSetSkills:

    def test_migracion_573_skills(self, supabase):
        """gold_set_skills has ~573 rows (587 minus deduped)."""
        r = supabase.table('gold_set_skills').select('id', count='exact', head=True).execute()
        assert r.count >= 550, f"Expected >= 550 skills, got {r.count}"
        assert r.count <= 600, f"Expected <= 600 skills, got {r.count}"

    def test_matcheo_uri_exacto(self, supabase):
        """At least some skills have exact URI match."""
        r = supabase.table('gold_set_skills').select('id', count='exact', head=True).not_.is_('skill_uri', 'null').execute()
        total = supabase.table('gold_set_skills').select('id', count='exact', head=True).execute()
        pct = r.count / total.count * 100 if total.count > 0 else 0
        print(f"With URI: {r.count}/{total.count} ({pct:.1f}%)")
        assert r.count >= 40, f"Expected >= 40 exact URI matches, got {r.count}"

    def test_metricas_skills_en_gold_set(self):
        """Gold Set test reports skill precision and recall."""
        test_file = Path("/mnt/d/OEDE/Webscrapping/tests/matching/test_gold_set_manual.py")
        if not test_file.exists():
            pytest.skip("Gold Set test not found")
        content = test_file.read_text()
        assert 'evaluate_skills' in content, "evaluate_skills function not found"
        assert 'precision_promedio' in content or 'precision_skills' in content
        assert 'recall_promedio' in content or 'recall_skills' in content
        assert 'skills_mas_faltantes' in content

    def test_sync_incluye_skills(self):
        """JSON local has skills_esperadas per offer."""
        if not GOLD_SET_PATH.exists():
            pytest.skip("gold_set_manual_v2.json not found")

        data = json.loads(GOLD_SET_PATH.read_text(encoding='utf-8'))
        with_skills = sum(1 for e in data if e.get('skills_esperadas'))
        assert with_skills >= 45, \
            f"Expected >= 45 offers with skills_esperadas, got {with_skills}"

        # Check structure
        sample = next(e for e in data if e.get('skills_esperadas'))
        assert isinstance(sample['skills_esperadas'], list)
        assert len(sample['skills_esperadas']) > 0
        assert isinstance(sample['skills_esperadas'][0], str)
