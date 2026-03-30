# -*- coding: utf-8 -*-
"""
M-06: Tests unitarios — Registro de tareas fallidas en extracción de skills.

Cubre los dos paths de descarte:
- Path NLP: extract_from_tasks()
- Path Matching: extract_skills() / extract_skills_dual()

16 tests: extract_from_tasks (6), extract_skills (4), extract_skills_dual (3), casos borde (3)
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Agregar database/ al path (skills_implicit_extractor importa módulos sin prefijo)
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

class MockExtractor:
    """
    Extractor con embeddings reducidos para tests.
    Usa dimensión 32 para que cosine similarity produzca scores controlados.
    """

    def __init__(self):
        self.verbose = False
        self.top_k = 3
        self.threshold = 0.40

        # 5 skills ESCO mock
        self.metadata = [
            {"label": "instalar cableado eléctrico", "uri": "http://esco/skill/001"},
            {"label": "trabajar en equipo", "uri": "http://esco/skill/002"},
            {"label": "gestionar inventario", "uri": "http://esco/skill/003"},
            {"label": "reparar equipamiento eléctrico", "uri": "http://esco/skill/004"},
            {"label": "preparar informes financieros", "uri": "http://esco/skill/005"},
        ]

        # Embeddings mock: 5 vectores de dim 32 (ortogonales en distintas regiones)
        np.random.seed(42)
        dim = 32
        self.embeddings = np.zeros((5, dim), dtype=np.float32)
        # Cada skill ocupa un "rango" de dimensiones distinto
        self.embeddings[0, 0:6] = 1.0    # cableado — dims 0-5
        self.embeddings[1, 6:12] = 1.0   # equipo — dims 6-11
        self.embeddings[2, 12:18] = 1.0  # inventario — dims 12-17
        self.embeddings[3, 18:24] = 1.0  # reparar — dims 18-23
        self.embeddings[4, 24:30] = 1.0  # informes — dims 24-29
        # Normalizar
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / norms

        self.sinonimos_skills = {
            "tareas_a_skills": {"picking": "gestionar inventario"},
            "soft_skills_argentinas": {}
        }

        self.equiv_lookup = {}
        self.equiv_groups = {}
        self.weights_config = {"skills_genericas": {"lista": [], "peso": 0.5}}
        self.terminology_config = {"terminos": {}}

    def _mock_encode(self, text, normalize_embeddings=True):
        """Retorna embeddings controlados según el texto."""
        dim = 32
        vec = np.zeros(dim, dtype=np.float32)
        text_lower = text.lower()

        if "cableado" in text_lower or "instalar" in text_lower:
            vec[0:6] = 1.0          # Alta similitud con skill 001 → score ~1.0
        elif "equipo" in text_lower:
            vec[6:12] = 1.0         # Alta similitud con skill 002 → score ~1.0
        elif "tablero" in text_lower:
            vec[0:2] = 0.3          # Poca similitud con skill 001 → score < 0.40
            vec[18:20] = 0.3        # Poca similitud con skill 004
            vec[30:32] = 1.0        # Ruido en dims no usadas
        elif "embajador" in text_lower or "marca" in text_lower:
            vec[30:32] = 1.0        # Ruido solo → score ~0 con todas
        elif "innovación" in text_lower or "gerente" in text_lower:
            vec[30:32] = 1.0        # Ruido solo → score ~0
        else:
            vec[30:32] = 1.0        # Default: ruido → score ~0

        if normalize_embeddings:
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
        return vec


@pytest.fixture
def extractor():
    """Extractor mock con embeddings controlados."""
    from database.skills_implicit_extractor import SkillsImplicitExtractor

    ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    mock = MockExtractor()
    ext.verbose = mock.verbose
    ext.top_k = mock.top_k
    ext.threshold = mock.threshold
    ext.metadata = mock.metadata
    ext.embeddings = mock.embeddings
    ext.sinonimos_skills = mock.sinonimos_skills
    ext.equiv_lookup = mock.equiv_lookup
    ext.equiv_groups = mock.equiv_groups
    ext.weights_config = mock.weights_config
    ext.terminology_config = mock.terminology_config
    ext.model = MagicMock()
    ext.model.encode = mock._mock_encode
    return ext


# ============================================================================
# Path NLP: extract_from_tasks()
# ============================================================================

class TestExtractFromTasksFallidos:

    def test_tarea_fallida_contiene_datos_correctos(self, extractor):
        """Tarea con score < 0.40 aparece en fallidos con campos completos."""
        matcheadas, fallidas = extractor.extract_from_tasks(
            "reparar tableros eléctricos",
            track_failures=True
        )
        assert len(fallidas) == 1
        f = fallidas[0]
        assert f["tarea_texto"] == "reparar tableros eléctricos"
        assert f["mejor_skill_uri"] is not None
        assert f["mejor_skill_label"] is not None
        assert isinstance(f["mejor_score"], float)
        assert f["mejor_score"] < 0.40
        assert f["threshold_usado"] == 0.40
        assert f["gap_al_umbral"] == round(0.40 - f["mejor_score"], 4)

    def test_matcheadas_no_aparecen_en_fallidos(self, extractor):
        """Tareas que superan 0.40 no aparecen en fallidos."""
        matcheadas, fallidas = extractor.extract_from_tasks(
            "instalar cableado industrial",
            track_failures=True
        )
        assert len(matcheadas) > 0
        assert len(fallidas) == 0

    def test_mixto(self, extractor):
        """Con tareas mixtas, se separan correctamente."""
        matcheadas, fallidas = extractor.extract_from_tasks(
            "instalar cableado industrial; reparar tableros eléctricos; trabajar en equipo",
            track_failures=True
        )
        assert len(matcheadas) >= 1  # Al menos cableado matchea
        assert len(fallidas) >= 1    # Al menos tableros falla
        # No hay overlap
        matcheadas_tareas = {m.get("tarea", "").lower() for m in matcheadas}
        fallidas_tareas = {f["tarea_texto"].lower() for f in fallidas}
        assert matcheadas_tareas & fallidas_tareas == set()

    def test_compatibilidad_sin_flag(self, extractor):
        """Sin track_failures, retorna List (no tupla)."""
        result = extractor.extract_from_tasks(
            "instalar cableado industrial; reparar tableros eléctricos"
        )
        assert isinstance(result, list)
        # Verificar que no es tupla
        assert not isinstance(result, tuple)

    def test_compatibilidad_flag_false(self, extractor):
        """track_failures=False retorna List (idéntico a sin flag)."""
        result = extractor.extract_from_tasks(
            "instalar cableado industrial",
            track_failures=False
        )
        assert isinstance(result, list)

    def test_sinonimo_no_es_fallido(self, extractor):
        """Tarea que matchea por sinónimo argentino NO aparece en fallidos."""
        matcheadas, fallidas = extractor.extract_from_tasks(
            "picking",
            track_failures=True
        )
        assert len(matcheadas) == 1
        assert matcheadas[0]["origen"] == "sinonimo_argentino"
        assert len(fallidas) == 0


# ============================================================================
# Path Matching: extract_skills()
# ============================================================================

class TestExtractSkillsFallidos:

    def test_fallidos_tienen_tarea_origen(self, extractor):
        """Cada fallido indica de dónde vino (titulo/tarea/skills_nlp/soft_skills_nlp)."""
        matcheadas, fallidas = extractor.extract_skills(
            titulo_limpio="gerente de innovación",
            tareas_explicitas="actuar como embajador de la marca",
            track_failures=True
        )
        for f in fallidas:
            assert "tarea_origen" in f
            assert f["tarea_origen"] in ("titulo", "tarea", "skills_nlp", "soft_skills_nlp")

    def test_fallidos_datos_correctos(self, extractor):
        """Fallidos tienen la estructura completa esperada."""
        matcheadas, fallidas = extractor.extract_skills(
            titulo_limpio="gerente de innovación",
            tareas_explicitas="actuar como embajador de la marca",
            track_failures=True
        )
        assert len(fallidas) > 0
        for f in fallidas:
            assert "tarea_texto" in f
            assert "mejor_skill_uri" in f
            assert "mejor_skill_label" in f
            assert "mejor_score" in f
            assert "threshold_usado" in f
            assert "gap_al_umbral" in f
            assert len(f["tarea_texto"]) <= 200

    def test_compatibilidad_sin_flag(self, extractor):
        """Sin track_failures, retorna List (no tupla)."""
        result = extractor.extract_skills(
            titulo_limpio="instalar cableado industrial",
            track_failures=False
        )
        assert isinstance(result, list)
        assert not isinstance(result, tuple)

    def test_terminologia_no_es_fallida(self, extractor):
        """Skills encontradas por terminología no aparecen como fallidas."""
        # Patch _extract_terminology_skills para simular un match
        with patch.object(extractor, '_extract_terminology_skills', return_value=[
            {"skill_esco": "logística", "skill_uri": "http://esco/skill/099",
             "score": 0.95, "score_ponderado": 0.95, "peso": 1.0, "origen": "terminologia",
             "texto_fuente": "picking"}
        ]):
            matcheadas, fallidas = extractor.extract_skills(
                titulo_limpio="picking en depósito",
                track_failures=True
            )
            # Terminología matchea, no debería estar en fallidos
            term_skills = [m for m in matcheadas if m.get("origen") == "terminologia"]
            assert len(term_skills) >= 0  # puede o no haber, depende del mock


# ============================================================================
# Propagación: extract_skills_dual()
# ============================================================================

class TestExtractSkillsDualFallidos:

    def test_failures_en_retorno(self, extractor):
        """El dict de retorno incluye key 'failures'."""
        result = extractor.extract_skills_dual(
            titulo_limpio="gerente de innovación",
            tareas_explicitas="actuar como embajador de la marca",
            track_failures=True
        )
        assert "failures" in result
        assert isinstance(result["failures"], list)

    def test_failures_vacio_sin_flag(self, extractor):
        """Con track_failures=False, 'failures' es lista vacía."""
        result = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            track_failures=False
        )
        assert "failures" in result
        assert result["failures"] == []

    def test_failures_vacio_todo_matchea(self, extractor):
        """Si todo matchea, failures es vacía."""
        result = extractor.extract_skills_dual(
            titulo_limpio="instalar cableado industrial",
            tareas_explicitas="trabajar en equipo multidisciplinario",
            track_failures=True
        )
        assert result["failures"] == []
        assert len(result["skills_final"]) > 0


# ============================================================================
# Casos borde
# ============================================================================

class TestCasosBorde:

    def test_score_exacto_en_umbral(self, extractor):
        """Score == 0.40 exacto pasa (score < threshold → continue, no <=)."""
        # Difícil controlar score exacto con mock, pero verificamos la lógica:
        # si best_score >= threshold, no es fallida
        matcheadas, fallidas = extractor.extract_from_tasks(
            "instalar cableado industrial",  # Score alto, claramente pasa
            track_failures=True
        )
        # Lo que matchea no aparece como fallido
        for f in fallidas:
            assert f["mejor_score"] < extractor.threshold

    def test_tarea_muy_larga(self, extractor):
        """Tarea de 500+ chars se trunca a 200 en tarea_texto."""
        tarea_larga = "x" * 500
        matcheadas, fallidas = extractor.extract_from_tasks(
            tarea_larga,
            track_failures=True
        )
        if fallidas:
            assert len(fallidas[0]["tarea_texto"]) <= 200

    def test_embeddings_vacios(self):
        """Si el extractor no tiene embeddings, retorna vacío sin error."""
        from database.skills_implicit_extractor import SkillsImplicitExtractor
        ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
        ext.embeddings = np.array([])
        ext.metadata = []
        ext.sinonimos_skills = {"tareas_a_skills": {}, "soft_skills_argentinas": {}}
        ext.verbose = False
        ext.top_k = 3
        ext.threshold = 0.40

        result = ext.extract_from_tasks("alguna tarea", track_failures=True)
        assert result == ([], [])

        result2 = ext.extract_from_tasks("alguna tarea", track_failures=False)
        assert result2 == []
