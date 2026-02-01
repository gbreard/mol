#!/usr/bin/env python3
"""
Genera JSON con ocupaciones similares pre-calculadas.

Para cada ocupacion calcula Jaccard similarity con todas las demas
basandose en skills esenciales compartidas.

Output: public/data/occupation_similarity.json (~2 MB)
"""

import json
from pathlib import Path
from collections import defaultdict
import sys

# Paths
BASE_PATH = Path(__file__).parent.parent.parent.parent / "database/embeddings"
OCCUPATION_SKILLS_FILE = BASE_PATH / "esco_occupation_skills.json"
METADATA_FILE = BASE_PATH / "esco_occupations_metadata.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/occupation_similarity.json"


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def get_occupation_id(uri: str) -> str:
    """Extract occupation ID from URI."""
    return uri.split('/')[-1]


def main():
    print("=" * 60)
    print("Generando JSON de ocupaciones similares")
    print("=" * 60)

    # Load occupation skills
    print("\n1. Cargando skills por ocupacion...")
    with open(OCCUPATION_SKILLS_FILE, 'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    occupation_skills = skills_data['occupation_skills']
    print(f"   - {len(occupation_skills)} ocupaciones con skills")

    # Load metadata for labels
    print("\n2. Cargando metadata de ocupaciones...")
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    uri_to_label = {occ['uri']: occ['label'] for occ in metadata}
    uri_to_isco = {occ['uri']: occ['isco_code'] for occ in metadata}
    print(f"   - {len(metadata)} ocupaciones en metadata")

    # Build essential skills sets for each occupation
    print("\n3. Construyendo sets de skills esenciales...")
    essential_skills_by_occ = {}
    for uri, skills in occupation_skills.items():
        essential_uris = set()
        for skill in skills.get('essential', []):
            essential_uris.add(skill.get('skill_uri', ''))
        essential_skills_by_occ[uri] = essential_uris

    occupations_list = list(essential_skills_by_occ.keys())
    n_occupations = len(occupations_list)
    print(f"   - {n_occupations} ocupaciones procesadas")

    # Calculate similarity matrix (only upper triangle)
    print("\n4. Calculando similitudes (esto puede tomar un momento)...")
    similarity_results = defaultdict(list)

    total_comparisons = n_occupations * (n_occupations - 1) // 2
    comparisons_done = 0
    last_percent = 0

    for i, uri_a in enumerate(occupations_list):
        skills_a = essential_skills_by_occ[uri_a]
        if not skills_a:
            continue

        for j in range(i + 1, n_occupations):
            uri_b = occupations_list[j]
            skills_b = essential_skills_by_occ[uri_b]

            if not skills_b:
                continue

            # Calculate Jaccard
            jaccard = jaccard_similarity(skills_a, skills_b)

            if jaccard > 0.1:  # Only store if similarity > 10%
                shared = len(skills_a & skills_b)

                # Add to both directions
                similarity_results[uri_a].append({
                    'uri': uri_b,
                    'jaccard': round(jaccard, 4),
                    'shared': shared
                })
                similarity_results[uri_b].append({
                    'uri': uri_a,
                    'jaccard': round(jaccard, 4),
                    'shared': shared
                })

            comparisons_done += 1
            percent = int(comparisons_done / total_comparisons * 100)
            if percent > last_percent and percent % 10 == 0:
                print(f"   - {percent}% completado...")
                last_percent = percent

    print(f"   - {comparisons_done:,} comparaciones realizadas")

    # Sort and keep top 10 for each occupation
    print("\n5. Seleccionando top 10 similares por ocupacion...")
    output = {}
    for uri in occupations_list:
        occ_id = get_occupation_id(uri)
        similar_list = similarity_results.get(uri, [])

        # Sort by jaccard descending
        similar_sorted = sorted(similar_list, key=lambda x: -x['jaccard'])[:10]

        # Convert URIs to IDs and add labels
        similar_with_labels = []
        for sim in similar_sorted:
            sim_id = get_occupation_id(sim['uri'])
            sim_label = uri_to_label.get(sim['uri'], 'Unknown')
            sim_isco = uri_to_isco.get(sim['uri'], '')
            similar_with_labels.append({
                'id': sim_id,
                'label': sim_label,
                'isco': sim_isco,
                'jaccard': sim['jaccard'],
                'shared': sim['shared']
            })

        if similar_with_labels:  # Only include if has similar occupations
            output[occ_id] = similar_with_labels

    # Save output
    print("\n6. Guardando archivo...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    file_size = OUTPUT_FILE.stat().st_size
    print(f"\n{'=' * 60}")
    print(f"COMPLETADO!")
    print(f"{'=' * 60}")
    print(f"Archivo: {OUTPUT_FILE}")
    print(f"Tamano: {file_size / 1024:.1f} KB ({file_size / 1024 / 1024:.2f} MB)")
    print(f"Ocupaciones con similares: {len(output)}")

    # Stats
    total_similar = sum(len(v) for v in output.values())
    avg_similar = total_similar / len(output) if output else 0
    print(f"Total relaciones de similitud: {total_similar}")
    print(f"Promedio similares por ocupacion: {avg_similar:.1f}")


if __name__ == "__main__":
    main()
