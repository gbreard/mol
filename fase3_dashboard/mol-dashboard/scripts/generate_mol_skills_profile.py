"""
Genera mol_skills_profile.json comparando skills MOL vs ESCO.

LOGICA CLAVE:
- Agrupa por esco_occupation_uri (no ISCO)
- Compara skills por label normalizado (no URI)
- Extrae UUID de URI completa para matchear con occupation_full_detail.json

Uso:
    python generate_mol_skills_profile.py
"""

import json
import os
from datetime import datetime
from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://uywzoyhjjofsvvsrrnek.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV5d3pveWhqam9mc3Z2c3JybmVrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODQ5NDUyNiwiZXhwIjoyMDg0MDcwNTI2fQ.wSqtg8rtnbN3howe7_A0HLeEuUwtciGxo71IiKd7Nh4"


def normalize(label: str) -> str:
    """Normaliza label para comparacion."""
    if not label:
        return ""
    return label.strip().lower()


def extract_uuid(uri: str) -> str:
    """Extrae UUID de URI ESCO completa."""
    if not uri:
        return ""
    # "http://data.europa.eu/esco/occupation/abc-123" -> "abc-123"
    return uri.split('/')[-1]


def main():
    print("=== Generando mol_skills_profile.json ===\n")

    # 1. Cargar occupation_full_detail.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, '..', 'public', 'data', 'occupation_full_detail.json')

    print(f"1. Cargando {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        esco_data = json.load(f)
    print(f"   {len(esco_data)} ocupaciones ESCO cargadas")

    # 2. Conectar a Supabase
    print("\n2. Conectando a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 3. Consultar ofertas con ocupacion ESCO y sus skills
    print("\n3. Consultando ofertas con skills...")

    # Primero, obtener ofertas con esco_occupation_uri
    ofertas_response = supabase.table('ofertas') \
        .select('id_oferta, esco_occupation_uri, esco_occupation_label') \
        .not_.is_('esco_occupation_uri', 'null') \
        .execute()

    ofertas = {row['id_oferta']: row for row in ofertas_response.data}
    print(f"   {len(ofertas)} ofertas con ocupacion ESCO")

    # Luego, obtener skills de esas ofertas
    skills_response = supabase.table('ofertas_skills') \
        .select('id_oferta, esco_skill_label') \
        .not_.is_('esco_skill_label', 'null') \
        .execute()

    print(f"   {len(skills_response.data)} registros de skills")

    # 4. Agrupar por ocupacion ESCO
    print("\n4. Agrupando por ocupacion ESCO...")

    occupations = {}
    total_skills_count = 0

    for skill_row in skills_response.data:
        id_oferta = skill_row['id_oferta']
        if id_oferta not in ofertas:
            continue

        oferta = ofertas[id_oferta]
        uri = oferta['esco_occupation_uri']
        esco_uuid = extract_uuid(uri)

        if not esco_uuid:
            continue

        if esco_uuid not in occupations:
            occupations[esco_uuid] = {
                'uri': uri,
                'label': oferta['esco_occupation_label'],
                'offer_ids': set(),
                'skills': {}
            }

        occupations[esco_uuid]['offer_ids'].add(id_oferta)

        skill_label_norm = normalize(skill_row['esco_skill_label'])
        if skill_label_norm:
            if skill_label_norm not in occupations[esco_uuid]['skills']:
                occupations[esco_uuid]['skills'][skill_label_norm] = {
                    'label_original': skill_row['esco_skill_label'],
                    'frequency': 0
                }
            occupations[esco_uuid]['skills'][skill_label_norm]['frequency'] += 1
            total_skills_count += 1

    print(f"   {len(occupations)} ocupaciones ESCO con ofertas MOL")
    print(f"   {total_skills_count} registros de skills procesados")

    # 5. Comparar con ESCO y calcular metricas
    print("\n5. Comparando con ESCO y calculando metricas...")

    result = {
        'version': '1.0.0',
        'generated_at': datetime.now().isoformat(),
        'stats': {
            'total_offers': len(ofertas),
            'total_occupations_with_mol': 0,
            'avg_skills_per_offer': 0.0
        },
        'occupations': {}
    }

    matched_count = 0
    total_mol_skills = 0

    for esco_uuid, mol_occ in occupations.items():
        if esco_uuid not in esco_data:
            continue  # Ocupacion no existe en JSON

        matched_count += 1
        esco_occ = esco_data[esco_uuid]

        # Sets normalizados
        mol_set = set(mol_occ['skills'].keys())

        # ESCO skills (essential + optional)
        esco_essential_labels = []
        esco_optional_labels = []

        # Skills
        for s in esco_occ.get('skills', {}).get('essential', []):
            esco_essential_labels.append(normalize(s.get('label', '')))
        for s in esco_occ.get('skills', {}).get('optional', []):
            esco_optional_labels.append(normalize(s.get('label', '')))

        # Knowledge
        for s in esco_occ.get('knowledge', {}).get('essential', []):
            esco_essential_labels.append(normalize(s.get('label', '')))
        for s in esco_occ.get('knowledge', {}).get('optional', []):
            esco_optional_labels.append(normalize(s.get('label', '')))

        esco_essential_set = set(filter(None, esco_essential_labels))
        esco_optional_set = set(filter(None, esco_optional_labels))
        esco_all = esco_essential_set | esco_optional_set

        # Calcular metricas
        common = mol_set & esco_essential_set
        common_optional = mol_set & esco_optional_set
        emerging = mol_set - esco_all
        missing = esco_essential_set - mol_set

        coverage_essential = (len(common) / len(esco_essential_set) * 100) if esco_essential_set else 0
        coverage_total = (len(mol_set & esco_all) / len(esco_all) * 100) if esco_all else 0

        offer_count = len(mol_occ['offer_ids'])

        # Preparar mol_skills con porcentaje
        mol_skills_list = []
        for label_norm, data in sorted(mol_occ['skills'].items(), key=lambda x: -x[1]['frequency']):
            mol_skills_list.append({
                'label_original': data['label_original'],
                'label_normalized': label_norm,
                'frequency': data['frequency'],
                'percentage': round(data['frequency'] / offer_count * 100, 1),
                'is_esco_essential': label_norm in esco_essential_set,
                'is_esco_optional': label_norm in esco_optional_set,
                'is_emerging': label_norm in emerging
            })

        total_mol_skills += len(mol_skills_list)

        result['occupations'][esco_uuid] = {
            'esco_uuid': esco_uuid,
            'esco_label': mol_occ['label'] or esco_occ.get('label', ''),
            'offer_count': offer_count,
            'mol_skills': mol_skills_list,
            'comparison': {
                'coverage_essential': round(coverage_essential, 1),
                'coverage_total': round(coverage_total, 1),
                'common_count': len(common),
                'common_optional_count': len(common_optional),
                'emerging_count': len(emerging),
                'missing_count': len(missing),
                'esco_essential_count': len(esco_essential_set),
                'esco_optional_count': len(esco_optional_set),
                'mol_unique_count': len(mol_set),
                'common_labels': sorted(list(common)),
                'emerging_labels': sorted(list(emerging)),
                'missing_labels': sorted(list(missing))
            }
        }

    result['stats']['total_occupations_with_mol'] = matched_count
    result['stats']['avg_skills_per_offer'] = round(total_mol_skills / len(ofertas), 1) if ofertas else 0

    print(f"   {matched_count} ocupaciones matcheadas con ESCO")

    # 6. Guardar resultado
    output_path = os.path.join(script_dir, '..', 'public', 'data', 'mol_skills_profile.json')
    print(f"\n6. Guardando {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   Archivo guardado ({file_size:.2f} MB)")

    # 7. Resumen
    print("\n=== RESUMEN ===")
    print(f"Ofertas analizadas: {result['stats']['total_offers']}")
    print(f"Ocupaciones ESCO con datos MOL: {result['stats']['total_occupations_with_mol']}")
    print(f"Skills promedio por oferta: {result['stats']['avg_skills_per_offer']}")

    # Top 5 ocupaciones por cobertura
    print("\nTop 5 ocupaciones por cobertura esencial:")
    sorted_occs = sorted(
        result['occupations'].values(),
        key=lambda x: -x['comparison']['coverage_essential']
    )[:5]
    for occ in sorted_occs:
        print(f"  - {occ['esco_label']}: {occ['comparison']['coverage_essential']}% ({occ['offer_count']} ofertas)")


if __name__ == '__main__':
    main()
