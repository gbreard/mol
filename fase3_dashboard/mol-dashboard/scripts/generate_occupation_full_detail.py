#!/usr/bin/env python3
"""
Genera JSON con detalle completo de cada ocupacion.

Para cada ocupacion incluye:
- Label y ISCO
- Skills esenciales y opcionales (separadas de conocimientos)
- Conocimientos esenciales y opcionales
- Referencias a ocupaciones similares

Output: public/data/occupation_full_detail.json (~15 MB)

IMPORTANTE: Ejecutar generate_occupation_similarity.py ANTES de este script.
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
BASE_PATH = Path(__file__).parent.parent.parent.parent / "database/embeddings"
OCCUPATION_SKILLS_FILE = BASE_PATH / "esco_occupation_skills.json"
SKILLS_FULL_FILE = BASE_PATH / "esco_skills_full.json"
METADATA_FILE = BASE_PATH / "esco_occupations_metadata.json"
SIMILARITY_FILE = Path(__file__).parent.parent / "public/data/occupation_similarity.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/occupation_full_detail.json"


def get_id_from_uri(uri: str) -> str:
    """Extract ID from URI."""
    return uri.split('/')[-1]


def main():
    print("=" * 60)
    print("Generando JSON de detalle completo de ocupaciones")
    print("=" * 60)

    # Load occupation metadata
    print("\n1. Cargando metadata de ocupaciones...")
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    uri_to_meta = {occ['uri']: occ for occ in metadata}
    print(f"   - {len(metadata)} ocupaciones")

    # Load occupation skills
    print("\n2. Cargando skills por ocupacion...")
    with open(OCCUPATION_SKILLS_FILE, 'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    occupation_skills = skills_data['occupation_skills']
    print(f"   - {len(occupation_skills)} ocupaciones con skills")

    # Load full skills metadata (to get type: skill vs knowledge)
    print("\n3. Cargando metadata de skills...")
    with open(SKILLS_FULL_FILE, 'r', encoding='utf-8') as f:
        skills_full_data = json.load(f)
    # skills is a dict with URIs as keys, values have the metadata
    skill_meta = skills_full_data['skills']  # Already keyed by URI
    print(f"   - {len(skill_meta)} skills con metadata")

    # Load similarity data (if exists)
    similarity_data = {}
    if SIMILARITY_FILE.exists():
        print("\n4. Cargando datos de similitud...")
        with open(SIMILARITY_FILE, 'r', encoding='utf-8') as f:
            similarity_data = json.load(f)
        print(f"   - {len(similarity_data)} ocupaciones con similares")
    else:
        print("\n4. ADVERTENCIA: No se encontro occupation_similarity.json")
        print("   Ejecuta generate_occupation_similarity.py primero")

    # Build output
    print("\n5. Construyendo detalle por ocupacion...")
    output = {}
    stats = {
        'total': 0,
        'with_skills': 0,
        'with_knowledge': 0,
        'with_similar': 0,
        'skills_count': 0,
        'knowledge_count': 0
    }

    for uri, meta in uri_to_meta.items():
        occ_id = get_id_from_uri(uri)
        label = meta['label']
        isco = meta['isco_code']

        # Get skills for this occupation
        occ_skills = occupation_skills.get(uri, {'essential': [], 'optional': []})

        # Separate skills vs knowledge
        skills_essential = []
        skills_optional = []
        knowledge_essential = []
        knowledge_optional = []

        for skill in occ_skills.get('essential', []):
            skill_uri = skill.get('skill_uri', '')
            skill_label = skill.get('skill_label', '')
            skill_id = get_id_from_uri(skill_uri)
            skill_info = skill_meta.get(skill_uri, {})
            skill_type = skill_info.get('type', 'skill')
            l1 = skill_info.get('L1', '')
            l2 = skill_info.get('L2', l1)
            description = skill_info.get('description', '')

            record = {
                'id': skill_id,
                'label': skill_label,
                'L1': l1,
                'L2': l2,
                'description': description
            }

            if skill_type == 'knowledge':
                knowledge_essential.append(record)
            else:
                skills_essential.append(record)

        for skill in occ_skills.get('optional', []):
            skill_uri = skill.get('skill_uri', '')
            skill_label = skill.get('skill_label', '')
            skill_id = get_id_from_uri(skill_uri)
            skill_info = skill_meta.get(skill_uri, {})
            skill_type = skill_info.get('type', 'skill')
            l1 = skill_info.get('L1', '')
            l2 = skill_info.get('L2', l1)
            description = skill_info.get('description', '')

            record = {
                'id': skill_id,
                'label': skill_label,
                'L1': l1,
                'L2': l2,
                'description': description
            }

            if skill_type == 'knowledge':
                knowledge_optional.append(record)
            else:
                skills_optional.append(record)

        # Sort alphabetically
        skills_essential.sort(key=lambda x: x['label'].lower())
        skills_optional.sort(key=lambda x: x['label'].lower())
        knowledge_essential.sort(key=lambda x: x['label'].lower())
        knowledge_optional.sort(key=lambda x: x['label'].lower())

        # Get similar occupations
        similar = similarity_data.get(occ_id, [])

        # Build record
        record = {
            'label': label,
            'isco': isco,
            'skills': {
                'essential': skills_essential,
                'optional': skills_optional
            },
            'knowledge': {
                'essential': knowledge_essential,
                'optional': knowledge_optional
            },
            'similar': similar,
            'counts': {
                'skills_essential': len(skills_essential),
                'skills_optional': len(skills_optional),
                'knowledge_essential': len(knowledge_essential),
                'knowledge_optional': len(knowledge_optional),
                'total_skills': len(skills_essential) + len(skills_optional),
                'total_knowledge': len(knowledge_essential) + len(knowledge_optional),
                'similar': len(similar)
            }
        }

        output[occ_id] = record

        # Stats
        stats['total'] += 1
        if skills_essential or skills_optional:
            stats['with_skills'] += 1
            stats['skills_count'] += len(skills_essential) + len(skills_optional)
        if knowledge_essential or knowledge_optional:
            stats['with_knowledge'] += 1
            stats['knowledge_count'] += len(knowledge_essential) + len(knowledge_optional)
        if similar:
            stats['with_similar'] += 1

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
    print(f"\nEstadisticas:")
    print(f"  - Total ocupaciones: {stats['total']}")
    print(f"  - Con skills: {stats['with_skills']}")
    print(f"  - Con knowledge: {stats['with_knowledge']}")
    print(f"  - Con similares: {stats['with_similar']}")
    print(f"  - Total skills guardadas: {stats['skills_count']}")
    print(f"  - Total knowledge guardadas: {stats['knowledge_count']}")

    # Sample output
    print(f"\nEjemplo (primera ocupacion):")
    first_id = list(output.keys())[0]
    first = output[first_id]
    print(f"  ID: {first_id}")
    print(f"  Label: {first['label']}")
    print(f"  ISCO: {first['isco']}")
    print(f"  Skills ess/opt: {first['counts']['skills_essential']}/{first['counts']['skills_optional']}")
    print(f"  Knowledge ess/opt: {first['counts']['knowledge_essential']}/{first['counts']['knowledge_optional']}")
    print(f"  Similares: {first['counts']['similar']}")


if __name__ == "__main__":
    main()
