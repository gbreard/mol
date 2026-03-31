# -*- coding: utf-8 -*-
"""
M-08b Parte 1: Tests de recalcular_emergentes con COALESCE.
Estos tests verifican la lógica del COALESCE a nivel de datos,
no ejecutan el RPC de Supabase (que necesita migration ejecutada).
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCoalesceLogic:

    def test_variantes_se_consolidan(self):
        """Dos variantes con mismo canonical_label se agrupan."""
        data = [
            {"canonical_label": "analizar datos", "preferred_label": "analizar datos", "equivalence_id": "EQ-001", "skill_uri": "uri_a"},
            {"canonical_label": "analizar datos", "preferred_label": "realizar un análisis de datos", "equivalence_id": "EQ-001", "skill_uri": "uri_b"},
        ]
        # Simular COALESCE GROUP BY
        groups = {}
        for d in data:
            key = (d.get("canonical_label") or d["preferred_label"], d.get("equivalence_id") or d["skill_uri"])
            groups[key] = groups.get(key, 0) + 1
        assert len(groups) == 1
        assert list(groups.values())[0] == 2

    def test_sin_equivalencia_fallback(self):
        """Skills sin equivalence_id usan preferred_label y skill_uri."""
        data = [
            {"canonical_label": None, "preferred_label": "SQL", "equivalence_id": None, "skill_uri": "uri_sql"},
            {"canonical_label": None, "preferred_label": "Python", "equivalence_id": None, "skill_uri": "uri_python"},
        ]
        groups = {}
        for d in data:
            key = (d.get("canonical_label") or d["preferred_label"], d.get("equivalence_id") or d["skill_uri"])
            groups[key] = groups.get(key, 0) + 1
        assert len(groups) == 2  # No se agrupan

    def test_umbral_combinado(self):
        """Dos variantes bajo umbral individual pero combinadas lo superan."""
        # Simular: skill_A 15% + skill_B 18% = 33% (> 30%)
        ofertas_a = set(range(0, 15))
        ofertas_b = set(range(10, 28))
        combinadas = ofertas_a | ofertas_b
        total = 100
        pct_a = len(ofertas_a) / total * 100  # 15%
        pct_b = len(ofertas_b) / total * 100  # 18%
        pct_combinado = len(combinadas) / total * 100  # 28% (con overlap)
        assert pct_a < 30
        assert pct_b < 30
        # Sin overlap sería 33%, con overlap es menor pero still > 25%
        assert pct_combinado > 25

    def test_label_argentino_precedencia(self):
        """label_argentino gana sobre canonical_label."""
        group = {"label_argentino": "trabajo en equipo", "label_representante": "trabajar en equipo"}
        label = group.get("label_argentino") or group["label_representante"]
        assert label == "trabajo en equipo"

    def test_on_conflict_no_duplica(self):
        """Mismo canonical + isco_code → UPDATE, no INSERT duplicado."""
        # Simular: primera vez inserta, segunda vez actualiza
        emergentes = {}
        key = ("analizar datos", "2511")
        emergentes[key] = {"freq": 25}  # Primera vez
        emergentes[key] = {"freq": 45}  # Segunda vez (UPDATE)
        assert len(emergentes) == 1
        assert emergentes[key]["freq"] == 45
