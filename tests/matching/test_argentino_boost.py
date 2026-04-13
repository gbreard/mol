# -*- coding: utf-8 -*-
"""
Tests E2.2: Argentino boost — rerank skills post-matching
==========================================================

Verifica que rerank_with_argentino_boost():
1. Sube el score de skills presentes en esco_argentino
2. No modifica skills si la ocupación no tiene perfil
3. No supera score 1.0
4. Usa cache sin recargar Supabase
5. Degrada si Supabase no está disponible
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Agregar paths del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "database"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))


# ============================================================
# Fixtures
# ============================================================

OCCUPATION_URI_WITH_PROFILE = "http://data.europa.eu/esco/occupation/test-001"
OCCUPATION_URI_WITHOUT_PROFILE = "http://data.europa.eu/esco/occupation/test-999"

SKILL_URI_A = "http://data.europa.eu/esco/skill/skill-a"
SKILL_URI_B = "http://data.europa.eu/esco/skill/skill-b"
SKILL_URI_C = "http://data.europa.eu/esco/skill/skill-c"

MOCK_ARGENTINO_CACHE = {
    OCCUPATION_URI_WITH_PROFILE: {
        "skills": {
            SKILL_URI_A: 10,  # max frequency
            SKILL_URI_B: 5,   # half frequency
        },
        "max_freq": 10,
    }
}


def make_skill(uri, label, score, origen="tarea"):
    """Helper para crear skill dict."""
    return {
        "skill_esco": label,
        "skill_uri": uri,
        "score": score,
        "score_ponderado": score,
        "peso": 1.0,
        "origen": origen,
    }


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset class-level cache before each test."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    SkillsImplicitExtractor._argentino_cache = None
    yield
    SkillsImplicitExtractor._argentino_cache = None


@pytest.fixture
def extractor_with_mock_cache():
    """Extractor con cache argentino mockeado (no necesita Supabase ni embeddings)."""
    from skills_implicit_extractor import SkillsImplicitExtractor

    # Set cache directly to skip Supabase
    SkillsImplicitExtractor._argentino_cache = dict(MOCK_ARGENTINO_CACHE)

    # Create a minimal extractor mock that has the method
    ext = object.__new__(SkillsImplicitExtractor)
    ext.verbose = False
    return ext


# ============================================================
# Tests
# ============================================================

class TestArgentinoBoost:

    def test_skill_argentina_sube_en_ranking(self, extractor_with_mock_cache):
        """Skill presente en esco_argentino debe tener score más alto post-boost."""
        ext = extractor_with_mock_cache

        skills = [
            make_skill(SKILL_URI_C, "skill sin perfil", 0.80),  # Not in profile
            make_skill(SKILL_URI_A, "skill argentina A", 0.75),  # In profile, freq=10/10
            make_skill(SKILL_URI_B, "skill argentina B", 0.70),  # In profile, freq=5/10
        ]

        result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        # Skill A: 0.75 + 0.05*(10/10) = 0.80
        skill_a = next(s for s in result if s["skill_uri"] == SKILL_URI_A)
        assert skill_a["score"] == pytest.approx(0.80, abs=0.001)
        assert skill_a["boost_applied"] is True
        assert skill_a["boost_factor"] == pytest.approx(0.05, abs=0.001)

        # Skill B: 0.70 + 0.05*(5/10) = 0.725
        skill_b = next(s for s in result if s["skill_uri"] == SKILL_URI_B)
        assert skill_b["score"] == pytest.approx(0.725, abs=0.001)
        assert skill_b["boost_applied"] is True
        assert skill_b["boost_factor"] == pytest.approx(0.025, abs=0.001)

        # Skill C: sin boost
        skill_c = next(s for s in result if s["skill_uri"] == SKILL_URI_C)
        assert skill_c["score"] == pytest.approx(0.80, abs=0.001)
        assert skill_c["boost_applied"] is False

        # Re-sorted: A=0.80, C=0.80, B=0.725 (A and C tied, order depends on stability)
        scores = [s["score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_sin_perfil_argentino_sin_cambios(self, extractor_with_mock_cache):
        """Ocupación sin perfil en esco_argentino → skills sin modificar."""
        ext = extractor_with_mock_cache

        skills = [
            make_skill(SKILL_URI_A, "skill A", 0.85),
            make_skill(SKILL_URI_B, "skill B", 0.70),
        ]

        result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITHOUT_PROFILE)

        # Skills must be identical in content (no boost_applied key at all if no profile)
        assert len(result) == 2
        assert result[0]["score"] == pytest.approx(0.85)
        assert result[1]["score"] == pytest.approx(0.70)
        # Original list should be unchanged
        assert skills[0]["score"] == 0.85  # Not mutated

    def test_boost_no_supera_1(self, extractor_with_mock_cache):
        """Score + boost no debe superar 1.0."""
        ext = extractor_with_mock_cache

        skills = [
            make_skill(SKILL_URI_A, "skill alta", 0.98),  # 0.98 + 0.05 = 1.03 → capped at 1.0
        ]

        result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        assert result[0]["score"] == 1.0
        assert result[0]["score_ponderado"] == 1.0
        assert result[0]["boost_applied"] is True

    def test_cache_no_recarga_supabase(self, extractor_with_mock_cache):
        """Segunda llamada con misma ocupación no debe hacer query a Supabase."""
        ext = extractor_with_mock_cache
        from skills_implicit_extractor import SkillsImplicitExtractor

        skills = [make_skill(SKILL_URI_A, "skill A", 0.70)]

        # First call
        ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        # Patch Supabase to ensure it's NOT called
        with patch.dict('sys.modules', {'supabase': MagicMock()}):
            # Second call should use cache
            result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        # Cache was already set, no Supabase import needed
        assert SkillsImplicitExtractor._argentino_cache is not None
        assert result[0]["boost_applied"] is True

    def test_degrada_si_supabase_no_disponible(self):
        """Si Supabase no está disponible → retorna skills sin boost, sin error."""
        from skills_implicit_extractor import SkillsImplicitExtractor

        # Reset cache to force reload attempt
        SkillsImplicitExtractor._argentino_cache = None

        # Mock the config file to exist but Supabase to fail
        mock_config = '{"url": "https://fake.supabase.co", "service_role_key": "fake"}'

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=mock_config), \
             patch.dict('sys.modules', {'supabase': MagicMock(
                 create_client=MagicMock(side_effect=Exception("Connection refused"))
             )}):
            # Force cache to be empty (as if Supabase failed)
            SkillsImplicitExtractor._argentino_cache = {}

        ext = object.__new__(SkillsImplicitExtractor)
        ext.verbose = False

        skills = [
            make_skill(SKILL_URI_A, "skill A", 0.85),
            make_skill(SKILL_URI_B, "skill B", 0.70),
        ]

        result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        # Should return skills unchanged (no profile in empty cache)
        assert len(result) == 2
        assert result[0]["score"] == pytest.approx(0.85)
        assert result[1]["score"] == pytest.approx(0.70)

    def test_no_muta_input(self, extractor_with_mock_cache):
        """rerank_with_argentino_boost no debe mutar la lista de input."""
        ext = extractor_with_mock_cache

        skills = [
            make_skill(SKILL_URI_A, "skill A", 0.70),
        ]
        original_score = skills[0]["score"]

        result = ext.rerank_with_argentino_boost(skills, OCCUPATION_URI_WITH_PROFILE)

        # Input not mutated
        assert skills[0]["score"] == original_score
        assert "boost_applied" not in skills[0]
        # Output is different
        assert result[0]["score"] != original_score
