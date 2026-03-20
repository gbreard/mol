#!/usr/bin/env python3
"""
Regenera skills_searchable.json incluyendo emergentes del perfil argentino.

Combina:
1. Skills ESCO base (14,257) — siempre presentes
2. Skills emergentes de mol_skills_profile.json — marcadas como source='argentina_emerging'

Cada skill tiene un campo 'source' que indica su origen:
- 'esco': viene de la taxonomía ESCO europea
- 'argentina_emerging': detectada en ofertas argentinas pero no está en ESCO para esa ocupación

Uso:
    python scripts/regenerate_skills_searchable.py
    python scripts/regenerate_skills_searchable.py --dry-run
"""

import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'public', 'data')

SKILLS_FILE = os.path.join(DATA_DIR, 'skills_searchable.json')
MOL_PROFILE_FILE = os.path.join(DATA_DIR, 'mol_skills_profile.json')
OUTPUT_FILE = SKILLS_FILE  # Sobrescribe el original


def load_esco_skills():
    """Carga las 14K skills ESCO base."""
    with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['skills']


def load_emergent_skills(min_occupations=3):
    """
    Extrae skills emergentes de mol_skills_profile.json.
    Solo incluye las que aparecen en al menos min_occupations ocupaciones.
    """
    if not os.path.exists(MOL_PROFILE_FILE):
        print(f'  WARN: {MOL_PROFILE_FILE} no existe. Solo skills ESCO.')
        return []

    with open(MOL_PROFILE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Agrupar emergentes por label normalizado
    emergent_map = {}
    for occ_data in data.get('occupations', {}).values():
        for sk in occ_data.get('mol_skills', []):
            if not sk.get('is_emerging'):
                continue

            label_norm = sk['label_normalized']
            if label_norm not in emergent_map:
                emergent_map[label_norm] = {
                    'label': sk['label_original'],
                    'label_normalized': label_norm,
                    'uri': sk.get('esco_uri'),
                    'occupations_count': 0,
                    'has_esco_uri': bool(sk.get('esco_uri')),
                }
            emergent_map[label_norm]['occupations_count'] += 1

    # Filtrar por frecuencia mínima
    filtered = [v for v in emergent_map.values() if v['occupations_count'] >= min_occupations]
    filtered.sort(key=lambda x: x['occupations_count'], reverse=True)

    return filtered


def merge_catalogo(esco_skills, emergent_skills):
    """
    Combina ESCO + emergentes en un catálogo unificado.
    Agrega campo 'source' a cada skill.
    Evita duplicados (por label normalizado).
    """
    # Indexar ESCO por label normalizado para detectar duplicados
    esco_labels = set()
    for sk in esco_skills:
        label_norm = sk['label'].lower().replace('á', 'a').replace('é', 'e')\
            .replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        esco_labels.add(label_norm)

    # Agregar source a ESCO skills
    for sk in esco_skills:
        sk['source'] = 'esco'

    # Agregar emergentes que no estén ya en ESCO
    added = 0
    skipped_duplicate = 0
    for em in emergent_skills:
        if em['label_normalized'] in esco_labels:
            skipped_duplicate += 1
            continue

        # Crear entry compatible con el formato de skills_searchable
        new_skill = {
            'id': em.get('uri') or f"arg_{em['label_normalized'].replace(' ', '_')[:50]}",
            'label': em['label'],
            'type': 'skill',  # Las emergentes son skills por defecto
            'L1': '',
            'L2': '',
            'essential': 0,
            'optional': 0,
            'total': em['occupations_count'],
            'description': f"Competencia emergente del mercado laboral argentino. "
                          f"Detectada en {em['occupations_count']} ocupaciones.",
            'source': 'argentina_emerging',
            'occupations_count': em['occupations_count'],
        }
        esco_skills.append(new_skill)
        esco_labels.add(em['label_normalized'])
        added += 1

    return esco_skills, added, skipped_duplicate


def main():
    dry_run = '--dry-run' in sys.argv

    print(f'=== Regenerar skills_searchable.json (ESCO + Argentinas) ===')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print()

    # 1. Cargar ESCO base
    esco_skills = load_esco_skills()
    print(f'Skills ESCO base: {len(esco_skills):,}')

    # 2. Cargar emergentes
    emergent = load_emergent_skills(min_occupations=3)
    print(f'Skills emergentes (>=3 ocupaciones): {len(emergent):,}')

    # 3. Merge
    merged, added, skipped = merge_catalogo(esco_skills, emergent)
    print(f'Agregadas al catálogo: {added:,}')
    print(f'Duplicadas (ya en ESCO): {skipped:,}')
    print(f'Total catálogo unificado: {len(merged):,}')

    # Stats
    esco_count = sum(1 for s in merged if s.get('source') == 'esco')
    arg_count = sum(1 for s in merged if s.get('source') == 'argentina_emerging')

    stats = {
        'total': len(merged),
        'skills_esco': esco_count,
        'skills_argentina_emerging': arg_count,
        'generated_at': datetime.now().isoformat(),
        'min_occupations_filter': 3,
    }

    print(f'\nStats: {json.dumps(stats, indent=2)}')

    if dry_run:
        print('\n[DRY RUN] No se guardó el archivo.')
        return

    # 4. Guardar
    output = {
        'skills': merged,
        'stats': stats,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f'\nGuardado: {OUTPUT_FILE} ({size_mb:.1f} MB)')


if __name__ == '__main__':
    main()
