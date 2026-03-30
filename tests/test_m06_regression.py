# -*- coding: utf-8 -*-
"""
M-06: Tests de regresión — Verificar que nada se rompió.

Usa el mismo mock extractor que los unitarios.
Verifica que el comportamiento sin track_failures es idéntico al original.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def extractor():
    """Extractor mock idéntico al de test_m06_skills_failures.py."""
    from database.skills_implicit_extractor import SkillsImplicitExtractor

    ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    ext.verbose = False
    ext.top_k = 3
    ext.threshold = 0.40

    ext.metadata = [
        {"label": "instalar cableado eléctrico", "uri": "http://esco/skill/001"},
        {"label": "trabajar en equipo", "uri": "http://esco/skill/002"},
        {"label": "gestionar inventario", "uri": "http://esco/skill/003"},
        {"label": "reparar equipamiento eléctrico", "uri": "http://esco/skill/004"},
        {"label": "preparar informes financieros", "uri": "http://esco/skill/005"},
    ]

    dim = 32
    ext.embeddings = np.zeros((5, dim), dtype=np.float32)
    ext.embeddings[0, 0:6] = 1.0
    ext.embeddings[1, 6:12] = 1.0
    ext.embeddings[2, 12:18] = 1.0
    ext.embeddings[3, 18:24] = 1.0
    ext.embeddings[4, 24:30] = 1.0
    norms = np.linalg.norm(ext.embeddings, axis=1, keepdims=True)
    ext.embeddings = ext.embeddings / norms

    ext.sinonimos_skills = {"tareas_a_skills": {}, "soft_skills_argentinas": {}}
    ext.equiv_lookup = {}
    ext.equiv_groups = {}
    ext.weights_config = {"skills_genericas": {"lista": [], "peso": 0.5}}
    ext.terminology_config = {"terminos": {}}

    def _encode(text, normalize_embeddings=True):
        vec = np.zeros(dim, dtype=np.float32)
        text_lower = text.lower()
        if "cableado" in text_lower or "instalar" in text_lower:
            vec[0:6] = 1.0
        elif "equipo" in text_lower:
            vec[6:12] = 1.0
        else:
            vec[30:32] = 1.0
        norm = np.linalg.norm(vec)
        if norm > 0 and normalize_embeddings:
            vec = vec / norm
        return vec

    ext.model = MagicMock()
    ext.model.encode = _encode
    return ext


class TestRegressionExtractFromTasks:

    def test_retorno_es_list_sin_flag(self, extractor):
        """Sin track_failures, retorna List (no tuple)."""
        result = extractor.extract_from_tasks("instalar cableado industrial")
        assert isinstance(result, list)
        assert not isinstance(result, tuple)

    def test_retorno_es_list_flag_false(self, extractor):
        """Con track_failures=False, retorna List."""
        result = extractor.extract_from_tasks(
            "instalar cableado industrial",
            track_failures=False
        )
        assert isinstance(result, list)

    def test_skills_matcheadas_identicas(self, extractor):
        """Las skills matcheadas son idénticas con y sin track_failures."""
        tareas = "instalar cableado industrial; trabajar en equipo multidisciplinario"

        result_sin = extractor.extract_from_tasks(tareas, track_failures=False)
        matcheadas_con, _ = extractor.extract_from_tasks(tareas, track_failures=True)

        # Misma cantidad
        assert len(result_sin) == len(matcheadas_con)

        # Mismos labels
        labels_sin = sorted([s["skill_esco"] for s in result_sin])
        labels_con = sorted([s["skill_esco"] for s in matcheadas_con])
        assert labels_sin == labels_con

        # Mismos scores
        scores_sin = sorted([s["score"] for s in result_sin])
        scores_con = sorted([s["score"] for s in matcheadas_con])
        assert scores_sin == scores_con


class TestRegressionExtractSkills:

    def test_retorno_es_list_sin_flag(self, extractor):
        """Sin track_failures, retorna List (no tuple)."""
        result = extractor.extract_skills(
            titulo_limpio="instalar cableado industrial"
        )
        assert isinstance(result, list)
        assert not isinstance(result, tuple)

    def test_skills_matcheadas_identicas(self, extractor):
        """Skills idénticas con y sin track_failures."""
        result_sin = extractor.extract_skills(
            titulo_limpio="instalar cableado industrial",
            tareas_explicitas="trabajar en equipo",
            track_failures=False
        )
        matcheadas_con, _ = extractor.extract_skills(
            titulo_limpio="instalar cableado industrial",
            tareas_explicitas="trabajar en equipo",
            track_failures=True
        )

        assert len(result_sin) == len(matcheadas_con)
        labels_sin = sorted([s["skill_esco"] for s in result_sin])
        labels_con = sorted([s["skill_esco"] for s in matcheadas_con])
        assert labels_sin == labels_con


class TestRegressionExtractSkillsDual:

    def test_skills_final_identicas(self, extractor):
        """skills_final es idéntica con y sin track_failures."""
        result_sin = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            tareas_explicitas="trabajar en equipo",
            track_failures=False
        )
        result_con = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            tareas_explicitas="trabajar en equipo",
            track_failures=True
        )

        labels_sin = sorted([s["skill_esco"] for s in result_sin["skills_final"]])
        labels_con = sorted([s["skill_esco"] for s in result_con["skills_final"]])
        assert labels_sin == labels_con

    def test_dual_coinciden_no_cambia(self, extractor):
        """dual_coinciden_skills no cambia con track_failures."""
        result_sin = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            track_failures=False
        )
        result_con = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            track_failures=True
        )
        assert result_sin["dual_coinciden_skills"] == result_con["dual_coinciden_skills"]
        assert result_sin["metodo_primario"] == result_con["metodo_primario"]
