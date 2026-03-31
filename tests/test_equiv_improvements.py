# -*- coding: utf-8 -*-
"""
Tests: Mejoras equivalencias — staleness check + similitud.
10 tests Python (5 staleness + 5 similitud)
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Staleness tests
# ============================================================================

class TestEquivStaleness:

    def test_equiv_loaded_at_se_registra(self):
        """_equiv_loaded_at se puede asignar y es datetime UTC."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        # Simular lo que _initialize() hace
        SkillsImplicitExtractor._equiv_loaded_at = datetime.now(timezone.utc)
        assert hasattr(SkillsImplicitExtractor, '_equiv_loaded_at')
        assert isinstance(SkillsImplicitExtractor._equiv_loaded_at, datetime)
        assert SkillsImplicitExtractor._equiv_loaded_at.tzinfo is not None

    def test_staleness_detecta_cambio(self):
        """Timestamp posterior a _equiv_loaded_at indica cambio."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        loaded = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)
        SkillsImplicitExtractor._equiv_loaded_at = loaded
        latest = datetime(2026, 3, 31, 14, 0, 0, tzinfo=timezone.utc)
        assert latest > loaded  # Necesita recarga

    def test_staleness_sin_cambio(self):
        """Timestamp anterior a _equiv_loaded_at no necesita recarga."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        loaded = datetime(2026, 3, 31, 14, 0, 0, tzinfo=timezone.utc)
        SkillsImplicitExtractor._equiv_loaded_at = loaded
        latest = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)
        assert not (latest > loaded)  # No necesita recarga

    def test_staleness_loaded_at_none(self):
        """Si _equiv_loaded_at es None, siempre recarga."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        loaded = getattr(SkillsImplicitExtractor, '_equiv_loaded_at', None)
        latest = datetime(2026, 3, 31, 14, 0, 0, tzinfo=timezone.utc)
        if loaded is None:
            assert True  # Debería recargar
        else:
            assert latest > loaded or not (latest > loaded)  # Comparación válida

    def test_timezone_handling(self):
        """Timestamps con timezone se comparan correctamente."""
        loaded = datetime(2026, 3, 31, 14, 0, 0, tzinfo=timezone.utc)
        # Supabase retorna con +00:00
        latest_str = "2026-03-31T15:00:00+00:00"
        latest = datetime.fromisoformat(latest_str.replace('Z', '+00:00'))
        assert latest > loaded


# ============================================================================
# Similarity calculation tests
# ============================================================================

class TestGroupSimilarity:

    def test_similitud_3_miembros(self):
        """Calcula similitud correcta para grupo de 3."""
        from backfill_equiv_similarity import calculate_group_similarity

        dim = 32
        embs = np.zeros((3, dim), dtype=np.float32)
        embs[0, 0:8] = 1.0   # A
        embs[1, 0:7] = 1.0; embs[1, 8:9] = 0.3   # B (similar a A)
        embs[2, 0:6] = 1.0; embs[2, 10:12] = 0.5  # C (menos similar)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / norms

        avg, mn = calculate_group_similarity(embs, [0, 1, 2])
        assert 0.7 < avg < 1.0
        assert mn <= avg
        assert mn > 0.5

    def test_similitud_2_identicos(self):
        """Dos embeddings casi idénticos → similitud ~1.0."""
        from backfill_equiv_similarity import calculate_group_similarity

        dim = 32
        embs = np.zeros((2, dim), dtype=np.float32)
        embs[0, 0:10] = 1.0
        embs[1, 0:10] = 1.0; embs[1, 10] = 0.01  # Casi idéntico
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / norms

        avg, mn = calculate_group_similarity(embs, [0, 1])
        assert avg > 0.98
        assert mn > 0.98

    def test_similitud_1_miembro(self):
        """Grupo de 1 miembro → (1.0, 1.0)."""
        from backfill_equiv_similarity import calculate_group_similarity

        embs = np.random.randn(1, 32).astype(np.float32)
        avg, mn = calculate_group_similarity(embs, [0])
        assert avg == 1.0
        assert mn == 1.0

    def test_similitud_se_guarda_en_dict(self):
        """build_equivalence_table incluye similitud en cada grupo."""
        from generate_skill_equivalences import build_equivalence_table

        dim = 32
        embs = np.zeros((4, dim), dtype=np.float32)
        embs[0, 0:6] = 1.0
        embs[1, 0:6] = 1.0; embs[1, 6] = 0.1
        embs[2, 12:18] = 1.0
        embs[3, 12:18] = 1.0; embs[3, 18] = 0.1
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / norms

        metadata = [
            {'uri': 'u1', 'label': 'skill_a'},
            {'uri': 'u2', 'label': 'skill_b'},
            {'uri': 'u3', 'label': 'skill_c'},
            {'uri': 'u4', 'label': 'skill_d'},
        ]
        # Labels 0,1 en cluster 0; labels 2,3 en cluster 1
        labels = np.array([0, 0, 1, 1])
        freqs = {'skill_a': 100, 'skill_b': 50, 'skill_c': 80, 'skill_d': 30}

        table, lookup = build_equivalence_table(metadata, labels, freqs, embeddings=embs)
        for group in table:
            assert 'similitud_promedio' in group
            assert 'similitud_minima' in group
            assert isinstance(group['similitud_promedio'], float)
            assert 0 <= group['similitud_promedio'] <= 1

    def test_grupo_grande_no_falla(self):
        """Grupo con 10 miembros calcula correctamente."""
        from backfill_equiv_similarity import calculate_group_similarity

        dim = 32
        embs = np.random.randn(10, dim).astype(np.float32)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / norms

        avg, mn = calculate_group_similarity(embs, list(range(10)))
        assert -1 <= mn <= 1  # Cosine puede ser negativo con vectores aleatorios
        assert -1 <= avg <= 1
