#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_skill_types_from_rdf.py
==============================
Actualiza el campo skill_type en esco_skills desde el archivo RDF.

El RDF tiene el tipo de skill en el predicado esco:skillType con valores:
- http://data.europa.eu/esco/skill-type/skill
- http://data.europa.eu/esco/skill-type/knowledge
- http://data.europa.eu/esco/skill-type/attitude (raro)

También extrae skill_reusability_level:
- sector-specific
- occupation-specific
- cross-sector
- transversal

Uso:
    python update_skill_types_from_rdf.py

Tiempo estimado: 15-30 minutos (RDF de 1.26 GB)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

try:
    from rdflib import Graph, Namespace, RDF, SKOS, Literal, URIRef
    from rdflib.namespace import DCTERMS
except ImportError:
    print("ERROR: rdflib no instalado. Ejecutar: pip install rdflib")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: tqdm no instalado. No habrá barra de progreso.")
    tqdm = None

# Rutas
RDF_PATH = Path(r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf')
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Namespaces ESCO
ESCO = Namespace("http://data.europa.eu/esco/model#")
ESCO_SKILL_TYPE = Namespace("http://data.europa.eu/esco/skill-type/")
ESCO_REUSE = Namespace("http://data.europa.eu/esco/skill-reusability-level/")


def main():
    print("=" * 70)
    print("ACTUALIZACIÓN DE SKILL_TYPE DESDE RDF")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Verificar archivos
    if not RDF_PATH.exists():
        print(f"ERROR: RDF no encontrado: {RDF_PATH}")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"ERROR: BD no encontrada: {DB_PATH}")
        sys.exit(1)

    print(f"\n[1] Cargando RDF ({RDF_PATH.stat().st_size / 1024 / 1024:.0f} MB)...")
    print("    Esto puede tomar 10-20 minutos...")

    graph = Graph()
    graph.parse(RDF_PATH, format='xml')
    print(f"    [OK] {len(graph):,} triples cargados")

    # Conectar a BD
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener skills existentes
    cursor.execute("SELECT skill_uri FROM esco_skills")
    existing_skills = {row[0] for row in cursor.fetchall()}
    print(f"\n[2] Skills en BD: {len(existing_skills):,}")

    # Extraer tipos del RDF
    print("\n[3] Extrayendo skill_type y reusability_level del RDF...")

    stats = {
        'skill': 0,
        'knowledge': 0,
        'attitude': 0,
        'unknown': 0,
        'updated': 0,
        'reusability_updated': 0
    }

    # Query para obtener todos los skills con su tipo
    skill_types = {}
    skill_reusability = {}

    # Buscar skillType
    for skill_uri in existing_skills:
        skill_ref = URIRef(skill_uri)

        # Buscar tipo
        for type_obj in graph.objects(skill_ref, ESCO.skillType):
            type_str = str(type_obj)
            if 'skill-type/skill' in type_str:
                skill_types[skill_uri] = 'skill'
                stats['skill'] += 1
            elif 'skill-type/knowledge' in type_str:
                skill_types[skill_uri] = 'knowledge'
                stats['knowledge'] += 1
            elif 'skill-type/attitude' in type_str:
                skill_types[skill_uri] = 'attitude'
                stats['attitude'] += 1
            break

        # Buscar reusability level
        for reuse_obj in graph.objects(skill_ref, ESCO.skillReusabilityLevel):
            reuse_str = str(reuse_obj).split('/')[-1]
            skill_reusability[skill_uri] = reuse_str
            break

    print(f"    Tipos encontrados:")
    print(f"      - skill: {stats['skill']:,}")
    print(f"      - knowledge: {stats['knowledge']:,}")
    print(f"      - attitude: {stats['attitude']:,}")
    print(f"    Reusability levels: {len(skill_reusability):,}")

    # Actualizar BD
    print("\n[4] Actualizando base de datos...")

    for skill_uri, skill_type in skill_types.items():
        cursor.execute("""
            UPDATE esco_skills
            SET skill_type = ?
            WHERE skill_uri = ?
        """, (skill_type, skill_uri))
        stats['updated'] += 1

    for skill_uri, reuse_level in skill_reusability.items():
        cursor.execute("""
            UPDATE esco_skills
            SET skill_reusability_level = ?
            WHERE skill_uri = ?
        """, (reuse_level, skill_uri))
        stats['reusability_updated'] += 1

    conn.commit()

    # Verificar
    print("\n[5] Verificando actualización...")
    cursor.execute("""
        SELECT skill_type, COUNT(*)
        FROM esco_skills
        GROUP BY skill_type
    """)
    print("    Distribución skill_type:")
    for row in cursor.fetchall():
        print(f"      {row[0] or 'NULL'}: {row[1]:,}")

    cursor.execute("""
        SELECT skill_reusability_level, COUNT(*)
        FROM esco_skills
        WHERE skill_reusability_level IS NOT NULL
        GROUP BY skill_reusability_level
    """)
    print("    Distribución reusability_level:")
    for row in cursor.fetchall():
        print(f"      {row[0]}: {row[1]:,}")

    conn.close()

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Skills actualizados (tipo): {stats['updated']:,}")
    print(f"  Skills actualizados (reusability): {stats['reusability_updated']:,}")
    print(f"  Tipos: skill={stats['skill']}, knowledge={stats['knowledge']}, attitude={stats['attitude']}")
    print("=" * 70)


if __name__ == '__main__':
    main()
