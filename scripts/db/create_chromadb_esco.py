#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crear base de vectores ChromaDB con skills y ocupaciones ESCO

Genera embeddings para todos los datos ESCO y los almacena en ChromaDB
para búsqueda semántica eficiente.

Uso:
    python create_chromadb_esco.py              # Crear colecciones
    python create_chromadb_esco.py --rebuild    # Recrear desde cero

Autor: Sistema MOL
Fecha: 2025-12-01
"""

import sqlite3
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import argparse
from datetime import datetime
from tqdm import tqdm

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
CHROMA_PATH = Path(__file__).parent / 'esco_vectors'

# Modelo de embeddings (mismo que usa el matching actual)
EMBEDDING_MODEL = "BAAI/bge-m3"


def main():
    parser = argparse.ArgumentParser(description='Crear base ChromaDB con ESCO')
    parser.add_argument('--rebuild', action='store_true', help='Recrear colecciones desde cero')
    args = parser.parse_args()

    print("=" * 80)
    print("CREAR BASE DE VECTORES CHROMADB CON DATOS ESCO")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ruta ChromaDB: {CHROMA_PATH}")
    print(f"Modelo embeddings: {EMBEDDING_MODEL}")
    print()

    # Conectar a SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Crear cliente ChromaDB persistente
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Configurar función de embeddings
    print("[INFO] Cargando modelo de embeddings...")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # =========================================================================
    # COLECCIÓN: esco_skills (~13,890 skills)
    # =========================================================================
    print("\n" + "-" * 40)
    print("COLECCIÓN: esco_skills")
    print("-" * 40)

    # Verificar si existe
    existing_collections = [c.name for c in client.list_collections()]

    if "esco_skills" in existing_collections:
        if args.rebuild:
            print("[!] Eliminando colección existente...")
            client.delete_collection("esco_skills")
        else:
            skills_col = client.get_collection("esco_skills", embedding_function=ef)
            count = skills_col.count()
            print(f"[OK] Colección ya existe con {count:,} vectores")
            print("     Use --rebuild para recrear")
            conn.close()
            return

    # Crear colección
    skills_collection = client.create_collection(
        name="esco_skills",
        embedding_function=ef,
        metadata={"description": "Skills ESCO para matching semántico"}
    )

    # Cargar skills desde SQLite
    cursor.execute('''
        SELECT skill_uri, preferred_label_es, skill_type, skill_reusability_level
        FROM esco_skills
        WHERE preferred_label_es IS NOT NULL
    ''')
    skills = cursor.fetchall()
    print(f"[INFO] Skills ESCO en SQLite: {len(skills):,}")

    # Insertar en batches (ChromaDB límite ~5000 por batch)
    BATCH_SIZE = 1000
    total_inserted = 0

    for i in tqdm(range(0, len(skills), BATCH_SIZE), desc="Insertando skills"):
        batch = skills[i:i + BATCH_SIZE]

        documents = []
        ids = []
        metadatas = []

        for skill in batch:
            # Documento = texto para embedding
            doc = skill['preferred_label_es']
            if not doc or len(doc.strip()) == 0:
                continue

            documents.append(doc)
            ids.append(skill['skill_uri'])
            metadatas.append({
                "type": skill['skill_type'] or "unknown",
                "reusability": skill['skill_reusability_level'] or "unknown",
                "label": doc
            })

        if documents:
            skills_collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            total_inserted += len(documents)

    print(f"[OK] Insertados: {total_inserted:,} skills")

    # =========================================================================
    # COLECCIÓN: esco_occupations (~3,000 ocupaciones)
    # =========================================================================
    print("\n" + "-" * 40)
    print("COLECCIÓN: esco_occupations")
    print("-" * 40)

    if "esco_occupations" in existing_collections and not args.rebuild:
        occ_col = client.get_collection("esco_occupations", embedding_function=ef)
        count = occ_col.count()
        print(f"[OK] Colección ya existe con {count:,} vectores")
    else:
        if "esco_occupations" in existing_collections:
            client.delete_collection("esco_occupations")

        occ_collection = client.create_collection(
            name="esco_occupations",
            embedding_function=ef,
            metadata={"description": "Ocupaciones ESCO para matching semántico"}
        )

        # Cargar ocupaciones
        cursor.execute('''
            SELECT occupation_uri, preferred_label_es, isco_code, description_es
            FROM esco_occupations
            WHERE preferred_label_es IS NOT NULL
        ''')
        occupations = cursor.fetchall()
        print(f"[INFO] Ocupaciones ESCO en SQLite: {len(occupations):,}")

        for i in tqdm(range(0, len(occupations), BATCH_SIZE), desc="Insertando ocupaciones"):
            batch = occupations[i:i + BATCH_SIZE]

            documents = []
            ids = []
            metadatas = []

            for occ in batch:
                doc = occ['preferred_label_es']
                if not doc or len(doc.strip()) == 0:
                    continue

                documents.append(doc)
                ids.append(occ['occupation_uri'])
                metadatas.append({
                    "isco_code": occ['isco_code'] or "",
                    "label": doc,
                    "has_description": 1 if occ['description_es'] else 0
                })

            if documents:
                occ_collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )

        print(f"[OK] Insertadas: {occ_collection.count():,} ocupaciones")

    conn.close()

    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Ruta: {CHROMA_PATH}")
    print(f"Colecciones:")

    for col in client.list_collections():
        count = client.get_collection(col.name).count()
        print(f"  - {col.name}: {count:,} vectores")

    print("\n[OK] Base ChromaDB creada exitosamente")
    print("=" * 80)


if __name__ == '__main__':
    main()
