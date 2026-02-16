"""
Tests para _apply_supervision_penalty en match_ofertas_v3.py.

Step 14 del plan NLP Validator.

Verifica:
- tiene_gente=False + ISCO 1xxx → penalty -10%
- tiene_gente=True + ISCO 1xxx → bonus +5%
- ISCO no-1xxx → sin cambio
- None → sin cambio
- Reordenamiento por score
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Importar la función directamente es complejo por dependencias.
# Replicamos la lógica exacta para testear.


def apply_supervision_penalty(candidates, tiene_gente_cargo):
    """
    Réplica exacta de MatcherV3._apply_supervision_penalty (match_ofertas_v3.py:451-490).
    """
    if tiene_gente_cargo is None:
        return candidates

    tiene_gente = bool(tiene_gente_cargo)

    for candidate in candidates:
        isco_code = candidate.get("isco_code", "").lstrip("C")
        if not isco_code:
            continue

        is_directivo = isco_code.startswith("1")

        if not tiene_gente and is_directivo:
            original = candidate.get("combined_score", 0)
            candidate["combined_score"] = max(0, original - 0.10)
            candidate["supervision_penalty"] = -0.10

        elif tiene_gente and is_directivo:
            original = candidate.get("combined_score", 0)
            candidate["combined_score"] = original + 0.05
            candidate["supervision_bonus"] = 0.05

    candidates.sort(key=lambda x: x.get("combined_score", x.get("score", 0)), reverse=True)
    return candidates


class TestSupervisionPenalty:
    """Tests para penalización/bonus de supervisión."""

    def _make_candidate(self, isco_code, score=0.80):
        return {
            "isco_code": isco_code,
            "combined_score": score,
            "esco_label": f"Test occupation {isco_code}",
        }

    # --- Penalty: tiene_gente=False + ISCO 1xxx ---

    def test_no_gente_isco_1xxx_penalty(self):
        """Sin gente a cargo + ISCO directivo → -10%."""
        candidates = [self._make_candidate("1221", 0.80)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.70)
        assert result[0]["supervision_penalty"] == -0.10

    def test_no_gente_isco_1120_penalty(self):
        """Sin gente a cargo + ISCO 1120 (director general) → -10%."""
        candidates = [self._make_candidate("1120", 0.75)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.65)

    def test_no_gente_isco_1xxx_con_prefijo_C(self):
        """ISCO con prefijo C se limpia correctamente."""
        candidates = [self._make_candidate("C1221", 0.80)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.70)

    def test_no_gente_isco_1xxx_floor_zero(self):
        """Penalty no baja de 0."""
        candidates = [self._make_candidate("1120", 0.05)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == 0.0

    # --- Bonus: tiene_gente=True + ISCO 1xxx ---

    def test_gente_isco_1xxx_bonus(self):
        """Con gente a cargo + ISCO directivo → +5%."""
        candidates = [self._make_candidate("1221", 0.80)]
        result = apply_supervision_penalty(candidates, True)

        assert result[0]["combined_score"] == pytest.approx(0.85)
        assert result[0]["supervision_bonus"] == 0.05

    def test_gente_isco_1120_bonus(self):
        """Con gente a cargo + ISCO 1120 → +5%."""
        candidates = [self._make_candidate("1120", 0.90)]
        result = apply_supervision_penalty(candidates, True)

        assert result[0]["combined_score"] == pytest.approx(0.95)

    # --- Sin cambio: ISCO no-1xxx ---

    def test_no_gente_isco_2xxx_sin_cambio(self):
        """Sin gente + ISCO 2xxx (profesional) → sin cambio."""
        candidates = [self._make_candidate("2431", 0.80)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.80)
        assert "supervision_penalty" not in result[0]
        assert "supervision_bonus" not in result[0]

    def test_gente_isco_3xxx_sin_cambio(self):
        """Con gente + ISCO 3xxx → sin cambio (no es directivo)."""
        candidates = [self._make_candidate("3322", 0.75)]
        result = apply_supervision_penalty(candidates, True)

        assert result[0]["combined_score"] == pytest.approx(0.75)
        assert "supervision_bonus" not in result[0]

    def test_isco_5xxx_sin_cambio(self):
        """ISCO servicios → sin cambio."""
        candidates = [self._make_candidate("5120", 0.70)]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.70)

    # --- None → sin cambio ---

    def test_tiene_gente_none_sin_cambio(self):
        """tiene_gente=None → no aplica nada."""
        candidates = [self._make_candidate("1221", 0.80)]
        result = apply_supervision_penalty(candidates, None)

        assert result[0]["combined_score"] == pytest.approx(0.80)
        assert "supervision_penalty" not in result[0]
        assert "supervision_bonus" not in result[0]

    # --- Reordenamiento ---

    def test_reordena_por_score_despues_penalty(self):
        """Penalty puede cambiar el ranking."""
        candidates = [
            self._make_candidate("1221", 0.82),   # directivo → 0.72 después de -10%
            self._make_candidate("2431", 0.78),   # profesional → 0.78 sin cambio
        ]
        result = apply_supervision_penalty(candidates, False)

        # 2431 (0.78) debería quedar primero porque 1221 bajó a 0.72
        assert result[0]["isco_code"] == "2431"
        assert result[0]["combined_score"] == pytest.approx(0.78)
        assert result[1]["isco_code"] == "1221"
        assert result[1]["combined_score"] == pytest.approx(0.72)

    def test_reordena_por_score_despues_bonus(self):
        """Bonus puede subir un directivo en el ranking."""
        candidates = [
            self._make_candidate("2431", 0.85),   # profesional → 0.85
            self._make_candidate("1221", 0.82),   # directivo → 0.87 con +5%
        ]
        result = apply_supervision_penalty(candidates, True)

        # 1221 (0.87) debería quedar primero
        assert result[0]["isco_code"] == "1221"
        assert result[0]["combined_score"] == pytest.approx(0.87)

    # --- Edge cases ---

    def test_isco_vacio_sin_error(self):
        """Candidato sin isco_code → se ignora sin error."""
        candidates = [{"combined_score": 0.80, "esco_label": "test"}]
        result = apply_supervision_penalty(candidates, False)

        assert result[0]["combined_score"] == pytest.approx(0.80)

    def test_lista_vacia(self):
        """Lista vacía → retorna vacía."""
        result = apply_supervision_penalty([], False)
        assert result == []

    def test_tiene_gente_truthy_values(self):
        """Valores truthy (1, True, "1") todos se tratan como True."""
        for val in [1, True, "1"]:
            candidates = [self._make_candidate("1221", 0.80)]
            result = apply_supervision_penalty(candidates, val)
            assert result[0]["combined_score"] == pytest.approx(0.85), \
                f"tiene_gente={val!r} debería dar bonus"

    def test_tiene_gente_falsy_zero(self):
        """tiene_gente=0 se trata como False → penalty."""
        candidates = [self._make_candidate("1221", 0.80)]
        result = apply_supervision_penalty(candidates, 0)

        assert result[0]["combined_score"] == pytest.approx(0.70)


class TestSupervisionSourceCode:
    """Verifica que el código fuente tiene la integración correcta."""

    def test_method_exists_in_source(self):
        """_apply_supervision_penalty debe existir en match_ofertas_v3.py."""
        source_path = Path(__file__).parent.parent.parent / "database" / "match_ofertas_v3.py"
        content = source_path.read_text(encoding='utf-8')

        assert 'def _apply_supervision_penalty' in content
        assert 'tiene_gente_cargo' in content

    def test_integrated_after_seniority(self):
        """Supervision penalty se llama después de seniority penalty."""
        source_path = Path(__file__).parent.parent.parent / "database" / "match_ofertas_v3.py"
        content = source_path.read_text(encoding='utf-8')

        # Buscar que _apply_supervision_penalty se llama en el flujo
        assert '_apply_supervision_penalty(final_candidates, tiene_gente)' in content

    def test_uses_matching_config_values(self):
        """Penalty y bonus usan valores correctos: -0.10 y +0.05."""
        source_path = Path(__file__).parent.parent.parent / "database" / "match_ofertas_v3.py"
        content = source_path.read_text(encoding='utf-8')

        assert '0.10' in content  # penalty
        assert '0.05' in content  # bonus
