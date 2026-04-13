# -*- coding: utf-8 -*-
"""
Tests E4.2: Pares contrastivos desde esco_argentino
=====================================================

Valida que train_argentino.json:
1. Tiene los pares esperados (288 con URI, 3 sin URI skipeadas)
2. Formato contrastivo correcto
3. Negatives no están en el perfil argentino
4. Positive es la skill curada
"""

import pytest
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
TRAIN_PATH = PROJECT_ROOT / "data" / "fine_tuning" / "train_argentino.json"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def train_data():
    if not TRAIN_PATH.exists():
        pytest.skip("train_argentino.json not found — run generate_training_pairs_from_argentino.py first")
    with open(TRAIN_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="module")
def argentino_profiles():
    """Load esco_argentino skill URIs per occupation from Supabase."""
    candidates = [
        PROJECT_ROOT / "config" / "supabase_config.json",
        Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json"),
    ]
    config_path = None
    for p in candidates:
        if p.exists():
            config_path = p
            break
    if not config_path:
        pytest.skip("supabase_config.json not found")

    try:
        config = json.loads(config_path.read_text())
        from supabase import create_client
        client = create_client(config['url'], config['service_role_key'])
        result = client.table('esco_argentino').select(
            'esco_occupation_uri,skills_consolidadas'
        ).execute()

        profiles = {}  # occ_uri → set of skill URIs
        for row in (result.data or []):
            occ_uri = row['esco_occupation_uri']
            uris = set()
            for s in (row.get('skills_consolidadas') or []):
                u = s.get('esco_uri') or s.get('uri')
                if u:
                    uris.add(u)
            profiles[occ_uri] = uris
        return profiles
    except Exception as e:
        pytest.skip(f"Cannot load esco_argentino: {e}")


# ============================================================
# Tests
# ============================================================

class TestArgentinoTrainingPairs:

    def test_genera_288_pares(self, train_data):
        """Output tiene 288 pares (291 total - 3 sin URI)."""
        # 291 total assignments, 3 have no URI → 288 with contrastive pairs
        assert len(train_data) == 288, f"Expected 288 pairs, got {len(train_data)}"

    def test_formato_contrastivo_correcto(self, train_data):
        """Cada par tiene query, positive, negatives (lista 1-5)."""
        required_fields = {"query", "positive", "negatives", "occupation_context",
                           "occupation_label", "source", "confianza", "split"}

        for i, pair in enumerate(train_data):
            missing = required_fields - set(pair.keys())
            assert not missing, f"Pair {i} missing fields: {missing}"

            assert isinstance(pair["query"], str) and len(pair["query"]) > 0, \
                f"Pair {i}: query empty"
            assert isinstance(pair["positive"], str) and len(pair["positive"]) > 0, \
                f"Pair {i}: positive empty"
            assert isinstance(pair["negatives"], list), \
                f"Pair {i}: negatives not a list"
            assert 1 <= len(pair["negatives"]) <= 5, \
                f"Pair {i}: negatives count {len(pair['negatives'])} not in [1,5]"
            assert pair["confianza"] == "alta"
            assert pair["split"] == "train"
            assert pair["source"] == "esco_argentino_v1.0"

    def test_negatives_no_en_perfil_argentino(self, train_data, argentino_profiles):
        """Ningún negative está en esco_argentino para esa ocupación."""
        violations = []
        for i, pair in enumerate(train_data):
            occ_uri = pair["occupation_context"]
            profile_uris = argentino_profiles.get(occ_uri, set())

            for neg in pair["negatives"]:
                # negative format is "uri label"
                neg_uri = neg.split(" ", 1)[0]
                if neg_uri in profile_uris:
                    violations.append(f"Pair {i}: negative {neg_uri[:50]} is in argentino profile")

        assert not violations, f"{len(violations)} violations:\n" + "\n".join(violations[:5])

    def test_positive_es_skill_curada(self, train_data, argentino_profiles):
        """Positive coincide con la skill de la asignación esco_argentino."""
        violations = []
        for i, pair in enumerate(train_data):
            occ_uri = pair["occupation_context"]
            profile_uris = argentino_profiles.get(occ_uri, set())

            # positive format is "uri label"
            pos_uri = pair["positive"].split(" ", 1)[0]
            if pos_uri not in profile_uris:
                violations.append(f"Pair {i}: positive {pos_uri[:50]} not in argentino profile for {occ_uri[:50]}")

        assert not violations, f"{len(violations)} violations:\n" + "\n".join(violations[:5])
