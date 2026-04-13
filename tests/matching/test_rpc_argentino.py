# -*- coding: utf-8 -*-
"""
Tests E2.3: RPCs con is_argentino
==================================

Tests de integración que validan las RPCs expand_skills_semantic
y match_occupations_by_skills contra Supabase real.

Requieren:
- Supabase accesible con config/supabase_config.json
- Migraciones 055 y 056 ejecutadas en Supabase SQL Editor
- Datos: skills_embeddings, occupations_embeddings, esco_argentino poblados

Se skipean automáticamente si Supabase no está disponible.
"""

import pytest
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "database"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))


# ============================================================
# Fixtures
# ============================================================

def _get_supabase_client():
    """Helper para obtener cliente Supabase. Returns None si no disponible."""
    # Try worktree config first, then main repo
    candidates = [
        PROJECT_ROOT / "config" / "supabase_config.json",
        Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json"),
    ]
    config_path = None
    for p in candidates:
        if p.exists():
            config_path = p
            break
    if config_path is None:
        return None
    try:
        config = json.loads(config_path.read_text())
        from supabase import create_client
        return create_client(config['url'], config['service_role_key'])
    except Exception:
        return None


def _rpc_exists(client, rpc_name):
    """Verifica si una RPC existe llamándola con params inválidos y viendo el error."""
    try:
        # Try calling with minimal params
        if rpc_name == 'expand_skills_semantic':
            client.rpc(rpc_name, {'input_skill_uri': '__test__'}).execute()
        elif rpc_name == 'match_occupations_by_skills':
            client.rpc(rpc_name, {'skill_uris': ['__test__']}).execute()
        return True
    except Exception as e:
        error_msg = str(e)
        # "Could not find the function" = doesn't exist
        if 'PGRST202' in error_msg or 'could not find' in error_msg.lower():
            return False
        # Other errors mean the function exists but params/data don't match
        return True


@pytest.fixture(scope="module")
def supabase_client():
    client = _get_supabase_client()
    if client is None:
        pytest.skip("Supabase not available")
    return client


@pytest.fixture(scope="module")
def known_skill_uri(supabase_client):
    """Get a real skill_uri from skills_embeddings for testing."""
    r = supabase_client.table('skills_embeddings').select('skill_uri').limit(1).execute()
    if not r.data:
        pytest.skip("No skills in skills_embeddings")
    return r.data[0]['skill_uri']


@pytest.fixture(scope="module")
def known_occupation_with_profile(supabase_client):
    """Get an occupation_uri that has an esco_argentino profile."""
    r = supabase_client.table('esco_argentino').select(
        'esco_occupation_uri,skills_consolidadas'
    ).gt('total_skills', 0).limit(1).execute()
    if not r.data:
        pytest.skip("No esco_argentino profiles found")
    row = r.data[0]
    # Get a skill URI from the profile
    skills = row.get('skills_consolidadas', [])
    skill_uri = skills[0].get('esco_uri') if skills else None
    return {
        'occupation_uri': row['esco_occupation_uri'],
        'skill_uri': skill_uri,
    }


# ============================================================
# SQL file tests (siempre corren, sin Supabase)
# ============================================================

class TestSQLFiles:

    def test_expand_skills_semantic_sql_exists(self):
        sql_path = PROJECT_ROOT / "fase3_dashboard" / "sql" / "055_rpc_expand_skills_semantic.sql"
        assert sql_path.exists(), "Migration 055 not found"
        content = sql_path.read_text()
        assert "CREATE OR REPLACE FUNCTION expand_skills_semantic" in content
        assert "is_argentino" in content
        assert "occupation_uri" in content

    def test_match_occupations_argentino_sql_exists(self):
        sql_path = PROJECT_ROOT / "fase3_dashboard" / "sql" / "056_rpc_match_occupations_argentino.sql"
        assert sql_path.exists(), "Migration 056 not found"
        content = sql_path.read_text()
        assert "CREATE OR REPLACE FUNCTION match_occupations_by_skills" in content
        assert "prioritize_argentino" in content
        assert "argentino_skills" in content


# ============================================================
# Integration tests (requieren Supabase + migraciones ejecutadas)
# ============================================================

class TestExpandSkillsSemantic:

    def test_expand_retorna_campo_is_argentino(self, supabase_client, known_skill_uri):
        """RPC retorna is_argentino en cada resultado."""
        if not _rpc_exists(supabase_client, 'expand_skills_semantic'):
            pytest.skip("RPC expand_skills_semantic not deployed yet")

        result = supabase_client.rpc('expand_skills_semantic', {
            'input_skill_uri': known_skill_uri,
            'match_threshold': 0.50,
            'match_count': 5,
        }).execute()

        if result.data:
            for row in result.data:
                assert 'is_argentino' in row, f"Missing is_argentino field in {row.keys()}"
                assert isinstance(row['is_argentino'], bool)

    def test_skills_argentinas_primero(self, supabase_client, known_occupation_with_profile):
        """Skills is_argentino=TRUE aparecen antes que skills con mismo score."""
        if not _rpc_exists(supabase_client, 'expand_skills_semantic'):
            pytest.skip("RPC expand_skills_semantic not deployed yet")

        skill_uri = known_occupation_with_profile['skill_uri']
        occupation_uri = known_occupation_with_profile['occupation_uri']

        if not skill_uri:
            pytest.skip("No skill_uri in esco_argentino profile")

        result = supabase_client.rpc('expand_skills_semantic', {
            'input_skill_uri': skill_uri,
            'match_threshold': 0.40,
            'match_count': 20,
            'occupation_uri': occupation_uri,
        }).execute()

        if not result.data:
            pytest.skip("No results from expand_skills_semantic")

        # Verify ordering: all is_argentino=True should come before is_argentino=False
        saw_false = False
        for row in result.data:
            if not row['is_argentino']:
                saw_false = True
            elif saw_false:
                # Found is_argentino=True after is_argentino=False → order wrong
                pytest.fail("is_argentino=TRUE found after is_argentino=FALSE — ordering broken")

    def test_sin_occupation_uri_is_argentino_false(self, supabase_client, known_skill_uri):
        """Sin occupation_uri → todos los resultados tienen is_argentino=FALSE."""
        if not _rpc_exists(supabase_client, 'expand_skills_semantic'):
            pytest.skip("RPC expand_skills_semantic not deployed yet")

        result = supabase_client.rpc('expand_skills_semantic', {
            'input_skill_uri': known_skill_uri,
            'match_threshold': 0.50,
            'match_count': 5,
            # occupation_uri omitted → NULL
        }).execute()

        if result.data:
            for row in result.data:
                assert row['is_argentino'] is False, \
                    f"Expected is_argentino=FALSE without occupation_uri, got {row}"


class TestMatchOccupationsArgentino:

    def test_match_occupations_con_prioritize(self, supabase_client, known_occupation_with_profile):
        """Con prioritize_argentino=TRUE, ocupaciones con skills argentinas tienen score más alto."""
        if not _rpc_exists(supabase_client, 'match_occupations_by_skills'):
            pytest.skip("RPC match_occupations_by_skills not deployed (v2 with argentino)")

        skill_uri = known_occupation_with_profile['skill_uri']
        if not skill_uri:
            pytest.skip("No skill_uri in esco_argentino profile")

        # Without prioritize
        r1 = supabase_client.rpc('match_occupations_by_skills', {
            'skill_uris': [skill_uri],
            'similarity_threshold': 0.40,
            'max_results': 10,
            'prioritize_argentino': False,
        }).execute()

        # With prioritize
        r2 = supabase_client.rpc('match_occupations_by_skills', {
            'skill_uris': [skill_uri],
            'similarity_threshold': 0.40,
            'max_results': 10,
            'prioritize_argentino': True,
        }).execute()

        if not r1.data or not r2.data:
            pytest.skip("No results from match_occupations_by_skills")

        # Check that argentino_skills field exists
        for row in r2.data:
            assert 'argentino_skills' in row, f"Missing argentino_skills field"

        # If any occupation has argentino_skills > 0, its score should be higher with prioritize
        occ_uri = known_occupation_with_profile['occupation_uri']
        score_without = next((r['best_similarity'] for r in r1.data if r['occupation_uri'] == occ_uri), None)
        score_with = next((r['best_similarity'] for r in r2.data if r['occupation_uri'] == occ_uri), None)

        if score_without is not None and score_with is not None:
            assert score_with >= score_without, \
                f"Expected score_with ({score_with}) >= score_without ({score_without}) for argentino occupation"
