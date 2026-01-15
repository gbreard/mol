#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_esco_taxonomy.py
========================
Extrae la taxonomía completa de skills ESCO del RDF y genera JSON para categorización.

Extrae:
- skillType: skill | knowledge | attitude
- skillReusabilityLevel: transversal | cross-sector | sector-specific | occupation-specific
- broaderUri: skill padre en la jerarquía (para categorías L1/L2)

Output:
- config/esco_skills_taxonomy.json - Taxonomía completa
- Actualiza esco_skills en BD con reusability_level

Uso:
    python database/extract_esco_taxonomy.py

Tiempo estimado: 15-30 minutos (RDF de 1.26 GB)
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from rdflib import Graph, Namespace, URIRef
except ImportError:
    print("ERROR: rdflib no instalado. Ejecutar: pip install rdflib")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
    print("INFO: tqdm no instalado, sin barra de progreso")

# Rutas
RDF_PATH = Path(r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf')
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
CONFIG_PATH = Path(__file__).parent.parent / 'config'
OUTPUT_JSON = CONFIG_PATH / 'esco_skills_taxonomy.json'

# Namespaces ESCO
ESCO = Namespace("http://data.europa.eu/esco/model#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def load_existing_skills(db_path):
    """Carga skills existentes de la BD."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT skill_uri, preferred_label_es, skill_type
        FROM esco_skills
    """)
    skills = {row[0]: {'label': row[1], 'skill_type': row[2]} for row in cursor.fetchall()}
    conn.close()
    return skills


def extract_from_rdf(rdf_path, existing_uris):
    """Extrae taxonomía del RDF."""
    print(f"\n[1] Cargando RDF ({rdf_path.stat().st_size / 1024 / 1024:.0f} MB)...")
    print("    Esto puede tomar 10-20 minutos...")

    graph = Graph()
    graph.parse(rdf_path, format='xml')
    print(f"    [OK] {len(graph):,} triples cargados")

    print("\n[2] Extrayendo taxonomía...")

    taxonomy = {}
    stats = {
        'skill_type': defaultdict(int),
        'reusability': defaultdict(int),
        'has_broader': 0,
        'skill_groups': set()
    }

    # Iterar sobre skills existentes
    iterator = tqdm(existing_uris, desc="Procesando") if tqdm else existing_uris

    for skill_uri in iterator:
        skill_ref = URIRef(skill_uri)

        entry = {
            'skill_type': None,
            'reusability_level': None,
            'broader_uri': None,
            'broader_label': None,
            'skill_group': None
        }

        # Buscar skillType
        for type_obj in graph.objects(skill_ref, ESCO.skillType):
            type_str = str(type_obj).split('/')[-1]
            entry['skill_type'] = type_str
            stats['skill_type'][type_str] += 1
            break

        # Buscar skillReusabilityLevel
        for reuse_obj in graph.objects(skill_ref, ESCO.skillReusabilityLevel):
            reuse_str = str(reuse_obj).split('/')[-1]
            entry['reusability_level'] = reuse_str
            stats['reusability'][reuse_str] += 1
            break

        # Buscar broader (jerarquía) usando SKOS
        for broader_obj in graph.objects(skill_ref, SKOS.broader):
            broader_uri = str(broader_obj)
            entry['broader_uri'] = broader_uri
            stats['has_broader'] += 1

            # Obtener label del broader
            for label in graph.objects(broader_obj, SKOS.prefLabel):
                # Preferir español
                if hasattr(label, 'language') and label.language == 'es':
                    entry['broader_label'] = str(label)
                    break
                elif entry['broader_label'] is None:
                    entry['broader_label'] = str(label)

            # Si el broader es un skill group, guardarlo
            if 'skill-group' in broader_uri or 'isced-f' in broader_uri:
                entry['skill_group'] = broader_uri
                stats['skill_groups'].add(broader_uri)
            break

        taxonomy[skill_uri] = entry

    print(f"\n    Estadísticas:")
    print(f"      skill_type: {dict(stats['skill_type'])}")
    print(f"      reusability_level: {dict(stats['reusability'])}")
    print(f"      Con broader (jerarquía): {stats['has_broader']}")
    print(f"      Skill groups únicos: {len(stats['skill_groups'])}")

    return taxonomy, stats


def update_database(db_path, taxonomy):
    """Actualiza la BD con reusability_level."""
    print("\n[3] Actualizando base de datos...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    for skill_uri, data in taxonomy.items():
        if data['reusability_level']:
            cursor.execute("""
                UPDATE esco_skills
                SET skill_reusability_level = ?
                WHERE skill_uri = ?
            """, (data['reusability_level'], skill_uri))
            updated += 1

    conn.commit()
    print(f"    [OK] {updated:,} registros actualizados con reusability_level")

    # Verificar
    cursor.execute("""
        SELECT skill_reusability_level, COUNT(*)
        FROM esco_skills
        WHERE skill_reusability_level IS NOT NULL
        GROUP BY skill_reusability_level
    """)
    print("\n    Distribución reusability_level en BD:")
    for row in cursor.fetchall():
        print(f"      {row[0]}: {row[1]:,}")

    conn.close()


def generate_taxonomy_json(existing_skills, taxonomy, output_path):
    """Genera JSON de taxonomía para skill_categorizer."""
    print("\n[4] Generando JSON de taxonomía...")

    # Estructura del JSON
    output = {
        "version": "1.0",
        "description": "Taxonomía oficial ESCO para categorización de skills",
        "generated_at": datetime.now().isoformat(),
        "source": "esco-v1.2.0.rdf",
        "stats": {
            "total_skills": len(taxonomy),
            "with_type": sum(1 for t in taxonomy.values() if t['skill_type']),
            "with_reusability": sum(1 for t in taxonomy.values() if t['reusability_level']),
            "with_hierarchy": sum(1 for t in taxonomy.values() if t['broader_uri'])
        },
        "reusability_levels": {
            "transversal": "Competencias transversales (aplican a cualquier trabajo)",
            "cross-sector": "Competencias inter-sectoriales",
            "sector-specific": "Competencias específicas de un sector",
            "occupation-specific": "Competencias específicas de una ocupación"
        },
        "skill_types": {
            "skill": "Habilidad práctica",
            "knowledge": "Conocimiento teórico",
            "attitude": "Actitud/comportamiento"
        },
        "skills": {}
    }

    # Agregar cada skill
    for uri, data in taxonomy.items():
        label = existing_skills.get(uri, {}).get('label', '')
        output["skills"][uri] = {
            "label": label,
            "type": data['skill_type'],
            "reusability": data['reusability_level'],
            "broader_uri": data['broader_uri'],
            "broader_label": data['broader_label'],
            "is_transversal": data['reusability_level'] == 'transversal',
            "is_digital": False  # Se llenará con heurística o mapeo manual
        }

    # Guardar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"    [OK] Guardado en: {output_path}")
    print(f"    Tamaño: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

    return output


def main():
    print("=" * 70)
    print("EXTRACCIÓN DE TAXONOMÍA ESCO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Verificar archivos
    if not RDF_PATH.exists():
        print(f"ERROR: RDF no encontrado: {RDF_PATH}")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"ERROR: BD no encontrada: {DB_PATH}")
        sys.exit(1)

    # Cargar skills existentes
    print("\n[0] Cargando skills existentes de BD...")
    existing_skills = load_existing_skills(DB_PATH)
    print(f"    [OK] {len(existing_skills):,} skills")

    # Extraer del RDF
    taxonomy, stats = extract_from_rdf(RDF_PATH, existing_skills.keys())

    # Actualizar BD
    update_database(DB_PATH, taxonomy)

    # Generar JSON
    output = generate_taxonomy_json(existing_skills, taxonomy, OUTPUT_JSON)

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Skills procesados: {len(taxonomy):,}")
    print(f"  Con skill_type: {output['stats']['with_type']:,}")
    print(f"  Con reusability_level: {output['stats']['with_reusability']:,}")
    print(f"  Con jerarquía (broader): {output['stats']['with_hierarchy']:,}")
    print(f"\n  JSON generado: {OUTPUT_JSON}")
    print("=" * 70)


if __name__ == '__main__':
    main()
