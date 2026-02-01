#!/usr/bin/env python3
"""
Genera JSON optimizado para busqueda de skills en frontend.

Combina esco_skills_full.json con conteos de demanda por ocupaciones.

Output: public/data/skills_searchable.json (~3 MB)
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
BASE_PATH = Path(__file__).parent.parent.parent.parent / "database/embeddings"
SKILLS_FULL_FILE = BASE_PATH / "esco_skills_full.json"
SKILL_TO_OCCUPATIONS_FILE = BASE_PATH / "esco_skill_to_occupations.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/skills_searchable.json"


def get_skill_id(uri: str) -> str:
    """Extract skill ID from URI."""
    return uri.split('/')[-1]


def main():
    print("=" * 60)
    print("Generando JSON de skills buscables")
    print("=" * 60)

    # Load full skills metadata
    print("\n1. Cargando metadata completa de skills...")
    with open(SKILLS_FULL_FILE, 'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    # skills is a dict with URIs as keys
    skills_full = list(skills_data['skills'].values())
    print(f"   - {len(skills_full)} skills cargadas")

    # Load skill to occupations index
    print("\n2. Cargando indice skill -> ocupaciones...")
    with open(SKILL_TO_OCCUPATIONS_FILE, 'r', encoding='utf-8') as f:
        skill_to_occ = json.load(f)
    skill_occupations = skill_to_occ['skill_to_occupations']
    print(f"   - {len(skill_occupations)} skills con relaciones a ocupaciones")

    # Build output
    print("\n3. Construyendo lista optimizada...")
    output_skills = []
    stats = {
        'skills': 0,
        'knowledge': 0,
        'with_occupations': 0,
        'without_occupations': 0
    }

    for skill in skills_full:
        uri = skill.get('uri', '')
        skill_id = get_skill_id(uri)
        label = skill.get('label', '')
        skill_type = skill.get('type', 'skill')
        l1 = skill.get('L1', '')
        l2 = skill.get('L2', l1)  # Fallback to L1 if L2 missing

        # Get occupation counts
        occ_data = skill_occupations.get(uri, {})
        essential_count = len(occ_data.get('essential_for', []))
        optional_count = len(occ_data.get('optional_for', []))

        # Get description (extracted from RDF)
        description = skill.get('description', '')

        # Build record
        record = {
            'id': skill_id,
            'label': label,
            'type': skill_type,
            'L1': l1,
            'L2': l2,
            'essential': essential_count,
            'optional': optional_count,
            'total': essential_count + optional_count,
            'description': description
        }
        output_skills.append(record)

        # Stats
        if skill_type == 'knowledge':
            stats['knowledge'] += 1
        else:
            stats['skills'] += 1

        if essential_count + optional_count > 0:
            stats['with_occupations'] += 1
        else:
            stats['without_occupations'] += 1

    # Sort by total demand (most demanded first), then alphabetically
    print("\n4. Ordenando por demanda...")
    output_skills.sort(key=lambda x: (-x['total'], x['label'].lower()))

    # Build output object
    output = {
        'skills': output_skills,
        'stats': {
            'total': len(output_skills),
            'skills': stats['skills'],
            'knowledge': stats['knowledge'],
            'with_occupations': stats['with_occupations'],
            'without_occupations': stats['without_occupations']
        }
    }

    # Save
    print("\n5. Guardando archivo...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    file_size = OUTPUT_FILE.stat().st_size
    print(f"\n{'=' * 60}")
    print(f"COMPLETADO!")
    print(f"{'=' * 60}")
    print(f"Archivo: {OUTPUT_FILE}")
    print(f"Tamano: {file_size / 1024:.1f} KB ({file_size / 1024 / 1024:.2f} MB)")
    print(f"\nEstadisticas:")
    print(f"  - Total skills: {stats['skills'] + stats['knowledge']}")
    print(f"  - Skills: {stats['skills']}")
    print(f"  - Knowledge: {stats['knowledge']}")
    print(f"  - Con ocupaciones: {stats['with_occupations']}")
    print(f"  - Sin ocupaciones: {stats['without_occupations']}")

    # Top 10 most demanded
    print(f"\nTop 10 skills mas demandadas:")
    for i, skill in enumerate(output_skills[:10], 1):
        print(f"  {i}. {skill['label'][:50]} ({skill['total']} ocupaciones)")


if __name__ == "__main__":
    main()
