#!/usr/bin/env python3
"""
Genera un JSON optimizado para el frontend con:
- Lista de ocupaciones ESCO (id, label, isco)
- Por cada ocupacion, solo los L2 codes de sus skills (no labels)

Esto reduce el tamano de 30MB a ~1MB
"""

import json
from pathlib import Path

# Paths
BASE_PATH = Path(__file__).parent.parent.parent.parent / "database/embeddings"
METADATA_FILE = BASE_PATH / "esco_occupations_metadata.json"
SKILLS_FILE = BASE_PATH / "esco_occupation_skills.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/occupations_skills_index.json"

def main():
    print("Cargando metadata de ocupaciones...")
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print(f"  - {len(metadata)} ocupaciones")

    print("Cargando skills por ocupacion...")
    with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    occupation_skills = skills_data['occupation_skills']
    print(f"  - {len(occupation_skills)} ocupaciones con skills")

    print("Construyendo indice optimizado...")

    # Crear lista de ocupaciones ordenada por label
    occupations = []
    for occ in sorted(metadata, key=lambda x: x['label'].lower()):
        occ_id = occ['uri'].split('/')[-1]
        occupations.append({
            'id': occ_id,
            'label': occ['label'],
            'isco': occ['isco_code']
        })

    # Crear mapping de occupation_id -> L2 codes
    skills_by_occupation = {}
    for uri, skills in occupation_skills.items():
        occ_id = uri.split('/')[-1]

        essential_l2 = set()
        optional_l2 = set()

        for skill in skills.get('essential', []):
            l2 = skill.get('L2', skill.get('L1', ''))
            if l2:
                essential_l2.add(l2)

        for skill in skills.get('optional', []):
            l2 = skill.get('L2', skill.get('L1', ''))
            if l2:
                optional_l2.add(l2)

        skills_by_occupation[occ_id] = {
            'e': sorted(list(essential_l2)),  # essential
            'o': sorted(list(optional_l2))    # optional
        }

    # Construir output
    output = {
        'occupations': occupations,
        'skills': skills_by_occupation,
        'stats': {
            'total_occupations': len(occupations),
            'occupations_with_skills': len(skills_by_occupation)
        }
    }

    # Guardar
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    print(f"\nGuardado en: {OUTPUT_FILE}")
    print(f"Tamano: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
