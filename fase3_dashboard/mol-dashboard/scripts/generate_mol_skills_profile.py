"""
Genera mol_skills_profile.json comparando skills MOL vs ESCO.

LOGICA CLAVE:
- Agrupa por esco_occupation_uri (no ISCO)
- Compara skills por label normalizado (no URI)
- Extrae UUID de URI completa para matchear con occupation_full_detail.json
- Incluye URIs y descripciones de skills ESCO

Uso:
    python generate_mol_skills_profile.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from supabase import create_client

# Load credentials from config (NEVER hardcode keys)
_config_path = Path(__file__).resolve().parents[3] / "config" / "supabase_config.json"
if not _config_path.exists():
    print(f"ERROR: No se encontró {_config_path}")
    print("Crear config/supabase_config.json con url + service_role_key")
    sys.exit(1)

with open(_config_path, 'r') as _f:
    _config = json.load(_f)

SUPABASE_URL = _config["url"]
SUPABASE_KEY = _config["service_role_key"]


def normalize(label: str) -> str:
    """Normaliza label para comparacion."""
    if not label:
        return ""
    return label.strip().lower()


def load_esco_skills_index(base_path: str) -> dict:
    """Carga índice de skills ESCO por label normalizado."""
    skills_path = os.path.join(base_path, '..', '..', '..', 'database', 'embeddings', 'esco_skills_full.json')

    with open(skills_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Crear índice por label normalizado
    index = {}
    for uri, skill_data in data.get('skills', {}).items():
        label = skill_data.get('label', '')
        label_norm = normalize(label)
        if label_norm:
            index[label_norm] = {
                'uri': uri,
                'description': skill_data.get('description', ''),
                'L1': skill_data.get('L1', ''),
                'L2': skill_data.get('L2', '')
            }

    return index


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

    # 1b. Cargar índice de skills ESCO para URIs y descripciones
    print("\n1b. Cargando indice de skills ESCO...")
    esco_skills_index = load_esco_skills_index(script_dir)
    print(f"   {len(esco_skills_index)} skills ESCO indexadas")

    # 2. Conectar a Supabase
    print("\n2. Conectando a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 3. Consultar ofertas con ocupacion ESCO y sus skills
    print("\n3. Consultando ofertas con skills...")

    # Primero, obtener ofertas con esco_occupation_uri (con paginación)
    all_ofertas = []
    page_size = 1000
    offset = 0

    while True:
        ofertas_response = supabase.table('ofertas_dashboard') \
            .select('id_oferta, esco_occupation_uri, esco_occupation_label') \
            .not_.is_('esco_occupation_uri', 'null') \
            .range(offset, offset + page_size - 1) \
            .execute()

        if not ofertas_response.data:
            break

        all_ofertas.extend(ofertas_response.data)

        if len(ofertas_response.data) < page_size:
            break

        offset += page_size

    ofertas = {row['id_oferta']: row for row in all_ofertas}
    print(f"   {len(ofertas)} ofertas con ocupacion ESCO")

    # Luego, obtener skills de esas ofertas (con paginación)
    all_skills = []
    page_size = 1000
    offset = 0

    while True:
        skills_response = supabase.table('ofertas_skills') \
            .select('id_oferta, preferred_label') \
            .not_.is_('preferred_label', 'null') \
            .range(offset, offset + page_size - 1) \
            .execute()

        if not skills_response.data:
            break

        all_skills.extend(skills_response.data)
        print(f"   ... {len(all_skills)} registros de skills cargados")

        if len(skills_response.data) < page_size:
            break

        offset += page_size

    skills_response_data = all_skills
    print(f"   {len(skills_response_data)} registros de skills totales")

    # 4. Agrupar por ocupacion ESCO
    print("\n4. Agrupando por ocupacion ESCO...")

    occupations = {}
    total_skills_count = 0

    for skill_row in skills_response_data:
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

        skill_label_norm = normalize(skill_row['preferred_label'])
        if skill_label_norm:
            if skill_label_norm not in occupations[esco_uuid]['skills']:
                occupations[esco_uuid]['skills'][skill_label_norm] = {
                    'label_original': skill_row['preferred_label'],
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

        # Preparar mol_skills con porcentaje, URI y descripcion
        mol_skills_list = []
        for label_norm, data in sorted(mol_occ['skills'].items(), key=lambda x: -x[1]['frequency']):
            # Buscar URI y descripcion en indice ESCO
            esco_info = esco_skills_index.get(label_norm, {})

            mol_skills_list.append({
                'label_original': data['label_original'],
                'label_normalized': label_norm,
                'frequency': data['frequency'],
                'percentage': round(data['frequency'] / offer_count * 100, 1),
                'is_esco_essential': label_norm in esco_essential_set,
                'is_esco_optional': label_norm in esco_optional_set,
                'is_emerging': label_norm in emerging,
                'esco_uri': esco_info.get('uri', ''),
                'description': esco_info.get('description', ''),
                'L1': esco_info.get('L1', ''),
                'L2': esco_info.get('L2', '')
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
                'common_optional_labels': sorted(list(common_optional)),
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
