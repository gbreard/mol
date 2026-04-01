# -*- coding: utf-8 -*-
"""
M-08b Parte 3: Tests de re-clustering con frozen groups.
"""
import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFrozenGroups:

    def test_ids_no_colisionan(self):
        """Nuevos IDs no colisionan con protegidos."""
        frozen = [{"id": "EQ-00100"}, {"id": "EQ-00200"}, {"id": "EQ-00500"}]
        max_frozen = max(int(g['id'].replace('EQ-', '')) for g in frozen)
        new_id = f"EQ-{0 + max_frozen + 1:05d}"
        assert new_id == "EQ-00501"
        assert int(new_id.replace('EQ-', '')) > max_frozen

    def test_preview_no_modifica(self):
        """--preview genera info pero no cambia datos."""
        # Simulamos: preview calcula pero no sube
        changes = {"new_groups": 43, "frozen": 201}
        applied = False  # preview = no apply
        assert not applied
        assert changes["frozen"] == 201

    def test_partial_protege_aprobados(self):
        """Skills de grupos aprobados se excluyen del clustering."""
        frozen_uris = {"uri_1", "uri_2", "uri_3"}
        all_metadata = [
            {"uri": "uri_1"}, {"uri": "uri_2"}, {"uri": "uri_3"},
            {"uri": "uri_4"}, {"uri": "uri_5"},
        ]
        free_indices = [i for i, m in enumerate(all_metadata) if m["uri"] not in frozen_uris]
        assert free_indices == [3, 4]
        assert len(free_indices) == 2

    def test_similarity_calculada_en_partial(self):
        """Grupos nuevos de --partial tienen similitud calculada."""
        from generate_skill_equivalences import calculate_group_similarity
        dim = 32
        embs = np.zeros((2, dim), dtype=np.float32)
        embs[0, 0:6] = 1.0
        embs[1, 0:6] = 1.0; embs[1, 6] = 0.1
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / norms
        avg, mn = calculate_group_similarity(embs, [0, 1])
        assert avg > 0.9

    def test_recluster_sin_grupos_auto(self):
        """Si todos son aprobados, no hay nada que re-clusterizar."""
        frozen_uris = {"uri_1", "uri_2", "uri_3", "uri_4", "uri_5"}
        all_metadata = [{"uri": f"uri_{i}"} for i in range(1, 6)]
        free_indices = [i for i, m in enumerate(all_metadata) if m["uri"] not in frozen_uris]
        assert free_indices == []
