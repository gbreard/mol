#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Re-matchear skills de ofertas contra TODOS los skills ESCO usando ChromaDB

Corrige el bug del matching actual que solo compara contra skills de la
ocupación matcheada. Este script hace matching global semántico.

Uso:
    python rematch_skills_chromadb.py              # Preview (no aplica cambios)
    python rematch_skills_chromadb.py --apply      # Aplicar cambios
    python rematch_skills_chromadb.py --threshold 0.65  # Cambiar umbral

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
from collections import defaultdict

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
CHROMA_PATH = Path(__file__).parent / 'esco_vectors'

# Modelo de embeddings (mismo que usa ChromaDB)
EMBEDDING_MODEL = "BAAI/bge-m3"

# Umbral de similaridad (0.70 = 70% similar)
DEFAULT_THRESHOLD = 0.70


def main():
    parser = argparse.ArgumentParser(description='Re-matchear skills con ChromaDB')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios a la base')
    parser.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD,
                        help=f'Umbral de similaridad (default: {DEFAULT_THRESHOLD})')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limitar a N registros (para testing)')
    args = parser.parse_args()

    print("=" * 80)
    print("RE-MATCHEAR SKILLS CON CHROMADB (MATCHING GLOBAL)")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Umbral similaridad: {args.threshold}")
    print(f"Modo: {'APLICAR' if args.apply else 'PREVIEW (sin cambios)'}")
    print()

    # Verificar que existe ChromaDB
    if not CHROMA_PATH.exists():
        print("[ERROR] No existe la base ChromaDB")
        print("        Ejecute primero: python create_chromadb_esco.py")
        return

    # Conectar a ChromaDB
    print("[INFO] Conectando a ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    try:
        skills_collection = client.get_collection("esco_skills", embedding_function=ef)
        print(f"[OK] Colección esco_skills: {skills_collection.count():,} vectores")
    except Exception as e:
        print(f"[ERROR] No se encontró la colección esco_skills: {e}")
        return

    # Conectar a SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener skills únicos a re-matchear
    query = '''
        SELECT DISTINCT skill_mencionado
        FROM ofertas_esco_skills_detalle
        WHERE skill_mencionado IS NOT NULL
    '''
    if args.limit:
        query += f' LIMIT {args.limit}'

    cursor.execute(query)
    unique_skills = [row['skill_mencionado'] for row in cursor.fetchall()]
    print(f"[INFO] Skills únicos a procesar: {len(unique_skills)}")

    # Procesar cada skill
    results = {}
    improved = 0
    unchanged = 0
    no_match = 0

    print("\n[INFO] Procesando skills...")

    for skill in tqdm(unique_skills, desc="Matching"):
        # Buscar en ChromaDB
        query_result = skills_collection.query(
            query_texts=[skill],
            n_results=3,  # Top 3 para análisis
            include=["distances", "metadatas", "documents"]
        )

        # ChromaDB devuelve distancia, no similaridad
        # Similaridad = 1 - distancia (para coseno normalizado)
        distances = query_result['distances'][0]
        documents = query_result['documents'][0]
        ids = query_result['ids'][0]
        metadatas = query_result['metadatas'][0]

        if distances:
            best_distance = distances[0]
            best_similarity = 1 - best_distance
            best_label = documents[0]
            best_uri = ids[0]
            best_type = metadatas[0].get('type', 'unknown')

            if best_similarity >= args.threshold:
                results[skill] = {
                    'uri': best_uri,
                    'label': best_label,
                    'similarity': best_similarity,
                    'type': best_type,
                    'status': 'matched'
                }
                improved += 1
            else:
                results[skill] = {
                    'uri': None,
                    'label': None,
                    'similarity': best_similarity,
                    'type': None,
                    'status': 'below_threshold',
                    'best_candidate': best_label
                }
                no_match += 1
        else:
            results[skill] = {
                'uri': None,
                'label': None,
                'similarity': 0,
                'type': None,
                'status': 'no_result'
            }
            no_match += 1

    # Estadísticas
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS")
    print("-" * 40)
    print(f"  Skills procesados:    {len(unique_skills)}")
    print(f"  Con match (>={args.threshold}): {improved}")
    print(f"  Sin match (<{args.threshold}):  {no_match}")
    print(f"  Sin cambio:           {unchanged}")

    # Mostrar ejemplos de mejoras
    print("\n" + "-" * 40)
    print("EJEMPLOS DE NUEVOS MATCHS:")
    print("-" * 40)
    count = 0
    for skill, data in results.items():
        if data['status'] == 'matched' and count < 15:
            print(f"  \"{skill}\" -> \"{data['label']}\" ({data['similarity']:.2f}) [{data['type']}]")
            count += 1

    # Mostrar ejemplos sin match
    print("\n" + "-" * 40)
    print("EJEMPLOS SIN MATCH (threshold bajo):")
    print("-" * 40)
    count = 0
    for skill, data in results.items():
        if data['status'] == 'below_threshold' and count < 10:
            print(f"  \"{skill}\" -> \"{data.get('best_candidate', '?')}\" ({data['similarity']:.2f}) [RECHAZADO]")
            count += 1

    # Aplicar cambios
    if args.apply:
        print("\n" + "=" * 80)
        print("[!] APLICANDO CAMBIOS...")

        # Agregar columnas si no existen
        try:
            cursor.execute('ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN match_score_global REAL')
            print("[INFO] Columna match_score_global agregada")
        except:
            pass

        try:
            cursor.execute('ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN match_method TEXT')
            print("[INFO] Columna match_method agregada")
        except:
            pass

        try:
            cursor.execute('ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN esco_skill_label_global TEXT')
            print("[INFO] Columna esco_skill_label_global agregada")
        except:
            pass

        try:
            cursor.execute('ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN esco_skill_uri_global TEXT')
            print("[INFO] Columna esco_skill_uri_global agregada")
        except:
            pass

        # Actualizar registros
        updated = 0
        for skill, data in tqdm(results.items(), desc="Actualizando"):
            if data['status'] == 'matched':
                cursor.execute('''
                    UPDATE ofertas_esco_skills_detalle
                    SET match_score_global = ?,
                        match_method = 'chromadb_global',
                        esco_skill_label_global = ?,
                        esco_skill_uri_global = ?
                    WHERE skill_mencionado = ?
                ''', (data['similarity'], data['label'], data['uri'], skill))
                updated += cursor.rowcount
            else:
                cursor.execute('''
                    UPDATE ofertas_esco_skills_detalle
                    SET match_score_global = ?,
                        match_method = 'chromadb_no_match'
                    WHERE skill_mencionado = ?
                ''', (data['similarity'], skill))

        conn.commit()
        print(f"[OK] Registros actualizados: {updated}")
    else:
        print("\n" + "=" * 80)
        print("[!] Modo PREVIEW - cambios NO aplicados")
        print("    Use --apply para aplicar los cambios")

    conn.close()
    print("=" * 80)


if __name__ == '__main__':
    main()
