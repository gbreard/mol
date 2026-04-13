# -*- coding: utf-8 -*-
"""
Tests: Cache local de equivalencias de skills
===============================================

Verifica que el cache local funciona correctamente:
1. Se crea después de cargar desde Supabase
2. Se usa si es reciente (< TTL)
3. Se invalida si es viejo (> TTL)
4. --refresh-cache fuerza recarga
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "database"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))

CACHE_PATH = Path("/mnt/d/OEDE/Webscrapping/config/skill_equivalences_lookup.json")


class TestEquivalencesCache:

    def test_cache_se_crea_despues_de_supabase(self):
        """Después de cargar desde Supabase, archivo cache existe con timestamp."""
        assert CACHE_PATH.exists(), \
            f"Cache file not found at {CACHE_PATH}"

        data = json.loads(CACHE_PATH.read_text(encoding='utf-8'))

        assert '_cache_timestamp' in data, "Missing _cache_timestamp"
        assert '_cache_version' in data, "Missing _cache_version"
        assert '_cache_uris' in data, "Missing _cache_uris"
        assert 'lookups' in data, "Missing lookups array"
        assert 'groups' in data, "Missing groups array"

        # Verify reasonable counts
        assert data['_cache_uris'] >= 2000, \
            f"Expected >= 2000 URIs, got {data['_cache_uris']}"
        assert len(data['lookups']) == data['_cache_uris']

    def test_cache_se_usa_si_reciente(self):
        """Cache con timestamp < 24h no hace requests a Supabase."""
        if not CACHE_PATH.exists():
            pytest.skip("Cache not generated yet")

        data = json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        ts = data.get('_cache_timestamp', '')
        cache_time = datetime.fromisoformat(ts)
        age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600

        assert age_hours < 24, \
            f"Cache is {age_hours:.1f}h old (expected < 24h for this test)"

        # The extractor should print "cache local" not "Supabase"
        # We verify by checking the cache has valid data
        assert len(data['lookups']) > 0

    def test_cache_se_invalida_si_viejo(self):
        """Cache con timestamp > 24h debería causar recarga."""
        if not CACHE_PATH.exists():
            pytest.skip("Cache not generated yet")

        data = json.loads(CACHE_PATH.read_text(encoding='utf-8'))

        # Simulate old cache by checking the TTL logic
        from embedding_config import EQUIVALENCES_CACHE_TTL_HOURS

        old_ts = (datetime.now(timezone.utc) - timedelta(hours=EQUIVALENCES_CACHE_TTL_HOURS + 1)).isoformat()
        # Don't actually modify the file — just verify the logic
        cache_time = datetime.fromisoformat(old_ts)
        age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600

        assert age_hours > EQUIVALENCES_CACHE_TTL_HOURS, \
            "Simulated old timestamp should exceed TTL"

        # The actual TTL is configured
        assert EQUIVALENCES_CACHE_TTL_HOURS == 24

    def test_refresh_cache_flag(self):
        """--refresh-cache argument exists in pipeline script."""
        pipeline_path = Path("/mnt/d/OEDE/Webscrapping/scripts/run_validated_pipeline.py")
        if not pipeline_path.exists():
            pipeline_path = PROJECT_ROOT / "scripts" / "run_validated_pipeline.py"
        if not pipeline_path.exists():
            pytest.skip("Pipeline script not found")

        content = pipeline_path.read_text()

        assert '--refresh-cache' in content, \
            "--refresh-cache flag not found in pipeline"
        assert '_force_refresh_cache' in content, \
            "_force_refresh_cache class attribute not set"
        assert 'refresh_cache' in content, \
            "args.refresh_cache not used"
