#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Poblar tabla ofertas_esco_skills_detalle desde ofertas v8.3

Parsea los campos skills_matched_essential y skills_matched_optional
de ofertas_esco_matching y los expande a la tabla de detalle con
metadatos ESCO completos (skill_type, reusability, etc.)

v2.0: Usa ChromaDB para matching semantico global en lugar de SQL
v3.0: HIBRIDO - ChromaDB para matching global + SQL para contexto ocupacional
      Ahora is_essential/is_optional refleja la relación REAL en ESCO
      entre el skill y la ocupación de la oferta.

Uso:
    python populate_skills_detalle_v83.py              # Modo simulacion
    python populate_skills_detalle_v83.py --apply      # Aplicar cambios
    python populate_skills_detalle_v83.py --clear      # Limpiar tabla antes
    python populate_skills_detalle_v83.py --threshold 0.65  # Cambiar umbral

Autor: Sistema MOL
Fecha: 2025-12-01
"""

import sqlite3
import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import chromadb
from chromadb.utils import embedding_functions

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
CHROMA_PATH = Path(__file__).parent / 'esco_vectors'
EMBEDDING_MODEL = "BAAI/bge-m3"
DEFAULT_THRESHOLD = 0.70
VERSION = 'v8.3_esco_familias_funcionales'


def parse_skill_mapping(mapping_str: str) -> Tuple[str, str]:
    """
    Parsea un mapping del formato 'skill_oferta→skill_esco'

    Args:
        mapping_str: String con formato 'python→programacion en python'

    Returns:
        Tuple (skill_oferta, skill_esco)
    """
    # El separador puede ser → (unicode) o -> (ASCII)
    if '→' in mapping_str:
        parts = mapping_str.split('→', 1)
    elif '->' in mapping_str:
        parts = mapping_str.split('->', 1)
    else:
        # Si no hay separador, es el skill mismo
        return mapping_str.strip(), mapping_str.strip()

    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return mapping_str.strip(), mapping_str.strip()


def parse_skills_json(skills_str: str) -> List[str]:
    """
    Parsea un string JSON de skills o formato lista

    Args:
        skills_str: String JSON o lista separada por comas

    Returns:
        Lista de strings de mappings
    """
    if not skills_str:
        return []

    skills_str = skills_str.strip()

    # Intentar parsear como JSON
    try:
        if skills_str.startswith('['):
            parsed = json.loads(skills_str)
            if isinstance(parsed, list):
                return [str(s) for s in parsed if s]
    except json.JSONDecodeError:
        pass

    # Intentar parsear como lista separada por comas
    # Pero cuidado con las comas dentro de los mappings
    if '→' in skills_str or '->' in skills_str:
        # Split por ", " para listas como "python→prog, sql→db"
        items = re.split(r',\s*(?=[^→]*→|[^-]*->)', skills_str)
        return [s.strip().strip('"\'[]') for s in items if s.strip()]

    return [skills_str]


def get_esco_skill_chromadb(skills_collection, skill_text: str, threshold: float) -> Optional[Dict]:
    """
    Busca un skill ESCO usando ChromaDB (matching semantico global)

    Args:
        skills_collection: Coleccion ChromaDB de skills ESCO
        skill_text: Texto del skill a buscar
        threshold: Umbral de similaridad (0-1)

    Returns:
        Dict con datos del skill o None si no supera threshold
    """
    if not skill_text or not skill_text.strip():
        return None

    # Buscar en ChromaDB
    results = skills_collection.query(
        query_texts=[skill_text.strip()],
        n_results=1,
        include=["distances", "metadatas", "documents"]
    )

    if not results['distances'] or not results['distances'][0]:
        return None

    # ChromaDB devuelve distancia, similaridad = 1 - distancia
    distance = results['distances'][0][0]
    similarity = 1 - distance

    if similarity >= threshold:
        return {
            'skill_uri': results['ids'][0][0],
            'skill_label': results['documents'][0][0],
            'skill_type': results['metadatas'][0][0].get('type'),
            'skill_reusability': results['metadatas'][0][0].get('reusability'),
            'similarity': similarity,
            'match_method': 'chromadb_semantic'
        }
    else:
        # Devolver info para debug pero sin match
        return {
            'skill_uri': None,
            'skill_label': results['documents'][0][0],  # Mejor candidato
            'skill_type': None,
            'skill_reusability': None,
            'similarity': similarity,
            'match_method': 'chromadb_no_match',
            'below_threshold': True
        }


def skill_in_occupation(cursor, skill_uri: str, occupation_uri: str) -> Optional[str]:
    """
    Verifica si un skill está asociado a una ocupación en ESCO.

    Consulta la tabla esco_associations para determinar la relación
    entre un skill y una ocupación específica.

    Args:
        cursor: Cursor SQLite
        skill_uri: URI del skill ESCO
        occupation_uri: URI de la ocupación ESCO

    Returns:
        'essential', 'optional', o None si no hay relación
    """
    if not skill_uri or not occupation_uri:
        return None

    cursor.execute('''
        SELECT relation_type
        FROM esco_associations
        WHERE skill_uri = ?
          AND occupation_uri = ?
    ''', (skill_uri, occupation_uri))

    row = cursor.fetchone()
    if row:
        return row[0]  # 'essential' o 'optional'
    return None


def main():
    parser = argparse.ArgumentParser(description='Poblar ofertas_esco_skills_detalle desde v8.3')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios a la DB')
    parser.add_argument('--clear', action='store_true', help='Limpiar tabla antes de poblar')
    parser.add_argument('--limit', type=int, default=0, help='Limitar a N ofertas (0=todas)')
    parser.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD,
                        help=f'Umbral de similaridad ChromaDB (default: {DEFAULT_THRESHOLD})')
    args = parser.parse_args()

    print("=" * 80)
    print("POBLAR ofertas_esco_skills_detalle DESDE MATCHING v8.3 (ChromaDB)")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'APLICAR' if args.apply else 'SIMULACION'}")
    print(f"Threshold: {args.threshold}")
    print()

    # Conectar a ChromaDB
    if not CHROMA_PATH.exists():
        print("[ERROR] No existe la base ChromaDB")
        print("        Ejecute primero: python create_chromadb_esco.py")
        return

    print("[INFO] Conectando a ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    try:
        skills_collection = client.get_collection("esco_skills", embedding_function=ef)
        print(f"[OK] Coleccion esco_skills: {skills_collection.count():,} vectores")
    except Exception as e:
        print(f"[ERROR] No se encontro coleccion esco_skills: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verificar tabla existe
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='ofertas_esco_skills_detalle'
    ''')
    if not cursor.fetchone():
        print("[ERROR] Tabla ofertas_esco_skills_detalle no existe!")
        print("        Ejecuta primero: python create_tables_nlp_esco.py")
        return

    # Contar ofertas v8.3
    cursor.execute('''
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE matching_version = ?
    ''', (VERSION,))
    total_v83 = cursor.fetchone()[0]
    print(f"[INFO] Ofertas v8.3 en matching: {total_v83}")

    # Contar registros existentes en skills_detalle para ofertas v8.3
    cursor.execute('''
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle d
        JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
        WHERE m.matching_version = ?
    ''', (VERSION,))
    existing = cursor.fetchone()[0]
    print(f"[INFO] Registros existentes en skills_detalle (v8.3): {existing}")

    if args.clear and args.apply:
        print("\n[!] Limpiando registros existentes de ofertas v8.3...")
        cursor.execute('''
            DELETE FROM ofertas_esco_skills_detalle
            WHERE id_oferta IN (
                SELECT id_oferta FROM ofertas_esco_matching
                WHERE matching_version = ?
            )
        ''', (VERSION,))
        print(f"    Eliminados: {cursor.rowcount} registros")

    # Obtener ofertas v8.3 con skills
    query = '''
        SELECT
            id_oferta,
            esco_occupation_uri,
            skills_matched_essential,
            skills_matched_optional,
            skills_sin_match_json
        FROM ofertas_esco_matching
        WHERE matching_version = ?
    '''
    if args.limit > 0:
        query += f' LIMIT {args.limit}'

    cursor.execute(query, (VERSION,))
    ofertas = cursor.fetchall()
    print(f"\n[INFO] Procesando {len(ofertas)} ofertas...")

    # Estadisticas
    stats = {
        'ofertas_procesadas': 0,
        'skills_essential': 0,
        'skills_optional': 0,
        'skills_sin_match': 0,
        'esco_encontrados': 0,
        'esco_no_encontrados': 0,
        'insertados': 0
    }

    inserts = []
    errores = []

    for oferta in ofertas:
        id_oferta = oferta['id_oferta']
        occupation_uri = oferta['esco_occupation_uri']

        # Parsear skills essential
        essential_mappings = parse_skills_json(oferta['skills_matched_essential'])
        for mapping in essential_mappings:
            skill_oferta, skill_esco = parse_skill_mapping(mapping)
            if not skill_oferta:
                continue

            stats['skills_essential'] += 1

            # Buscar skill ESCO en ChromaDB (matching semantico global)
            esco_data = get_esco_skill_chromadb(skills_collection, skill_oferta, args.threshold)

            if esco_data and not esco_data.get('below_threshold'):
                stats['esco_encontrados'] += 1

                # HIBRIDO: Consultar contexto ocupacional real en ESCO
                relation = skill_in_occupation(cursor, esco_data['skill_uri'], occupation_uri)
                is_essential_real = 1 if relation == 'essential' else 0
                is_optional_real = 1 if relation == 'optional' else 0

                inserts.append({
                    'id_oferta': id_oferta,
                    'skill_mencionado': skill_oferta,
                    'skill_tipo_fuente': 'nlp_extraction',
                    'esco_skill_uri': esco_data['skill_uri'],
                    'esco_skill_label': esco_data['skill_label'],
                    'esco_skill_type': esco_data.get('skill_type'),
                    'esco_skill_reusability': esco_data.get('skill_reusability'),
                    'is_essential': is_essential_real,
                    'is_optional': is_optional_real,
                    'source_classification': 'essential',  # Viene de skills_matched_essential
                    'match_method': esco_data.get('match_method', 'chromadb_semantic'),
                    'match_score': esco_data.get('similarity')
                })
            else:
                stats['esco_no_encontrados'] += 1
                # Insertar sin URI ESCO (below threshold)
                best_candidate = esco_data.get('skill_label') if esco_data else skill_esco
                similarity = esco_data.get('similarity', 0) if esco_data else 0
                inserts.append({
                    'id_oferta': id_oferta,
                    'skill_mencionado': skill_oferta,
                    'skill_tipo_fuente': 'nlp_extraction',
                    'esco_skill_uri': None,
                    'esco_skill_label': best_candidate,
                    'esco_skill_type': None,
                    'esco_skill_reusability': None,
                    'is_essential': 0,  # Sin match ESCO, no podemos saber
                    'is_optional': 0,
                    'source_classification': 'essential',  # Viene de skills_matched_essential
                    'match_method': 'chromadb_no_match',
                    'match_score': similarity
                })

        # Parsear skills optional
        optional_mappings = parse_skills_json(oferta['skills_matched_optional'])
        for mapping in optional_mappings:
            skill_oferta, skill_esco = parse_skill_mapping(mapping)
            if not skill_oferta:
                continue

            stats['skills_optional'] += 1

            # Buscar skill ESCO en ChromaDB (matching semantico global)
            esco_data = get_esco_skill_chromadb(skills_collection, skill_oferta, args.threshold)

            if esco_data and not esco_data.get('below_threshold'):
                stats['esco_encontrados'] += 1

                # HIBRIDO: Consultar contexto ocupacional real en ESCO
                relation = skill_in_occupation(cursor, esco_data['skill_uri'], occupation_uri)
                is_essential_real = 1 if relation == 'essential' else 0
                is_optional_real = 1 if relation == 'optional' else 0

                inserts.append({
                    'id_oferta': id_oferta,
                    'skill_mencionado': skill_oferta,
                    'skill_tipo_fuente': 'nlp_extraction',
                    'esco_skill_uri': esco_data['skill_uri'],
                    'esco_skill_label': esco_data['skill_label'],
                    'esco_skill_type': esco_data.get('skill_type'),
                    'esco_skill_reusability': esco_data.get('skill_reusability'),
                    'is_essential': is_essential_real,
                    'is_optional': is_optional_real,
                    'source_classification': 'optional',  # Viene de skills_matched_optional
                    'match_method': esco_data.get('match_method', 'chromadb_semantic'),
                    'match_score': esco_data.get('similarity')
                })
            else:
                stats['esco_no_encontrados'] += 1
                best_candidate = esco_data.get('skill_label') if esco_data else skill_esco
                similarity = esco_data.get('similarity', 0) if esco_data else 0
                inserts.append({
                    'id_oferta': id_oferta,
                    'skill_mencionado': skill_oferta,
                    'skill_tipo_fuente': 'nlp_extraction',
                    'esco_skill_uri': None,
                    'esco_skill_label': best_candidate,
                    'esco_skill_type': None,
                    'esco_skill_reusability': None,
                    'is_essential': 0,  # Sin match ESCO, no podemos saber
                    'is_optional': 0,
                    'source_classification': 'optional',  # Viene de skills_matched_optional
                    'match_method': 'chromadb_no_match',
                    'match_score': similarity
                })

        stats['ofertas_procesadas'] += 1

    # Mostrar estadisticas
    print("\n" + "=" * 80)
    print("ESTADISTICAS:")
    print("-" * 80)
    print(f"  Ofertas procesadas:     {stats['ofertas_procesadas']:>6}")
    print(f"  Skills essential:       {stats['skills_essential']:>6}")
    print(f"  Skills optional:        {stats['skills_optional']:>6}")
    print(f"  Total mappings:         {len(inserts):>6}")
    print(f"  ESCO encontrados:       {stats['esco_encontrados']:>6} ({100*stats['esco_encontrados']/max(1,len(inserts)):.1f}%)")
    print(f"  ESCO no encontrados:    {stats['esco_no_encontrados']:>6}")

    # Muestra de inserts
    print("\n" + "-" * 80)
    print("MUESTRA DE REGISTROS A INSERTAR (primeros 10):")
    print("-" * 80)
    for i, ins in enumerate(inserts[:10]):
        tipo = 'E' if ins['is_essential'] else 'O'
        esco_ok = 'OK' if ins['esco_skill_uri'] else 'NO'
        print(f"  [{tipo}] {ins['skill_mencionado'][:30]:<30} -> {ins['esco_skill_label'][:30]:<30} [{esco_ok}]")

    # Aplicar cambios
    if args.apply:
        print("\n" + "=" * 80)
        print("[!] APLICANDO CAMBIOS...")

        insert_sql = '''
            INSERT INTO ofertas_esco_skills_detalle (
                id_oferta, skill_mencionado, skill_tipo_fuente,
                esco_skill_uri, esco_skill_label, esco_skill_type,
                esco_skill_reusability, is_essential_for_occupation,
                is_optional_for_occupation, source_classification,
                match_method, match_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        for ins in inserts:
            try:
                cursor.execute(insert_sql, (
                    ins['id_oferta'],
                    ins['skill_mencionado'],
                    ins['skill_tipo_fuente'],
                    ins['esco_skill_uri'],
                    ins['esco_skill_label'],
                    ins['esco_skill_type'],
                    ins['esco_skill_reusability'],
                    ins['is_essential'],
                    ins['is_optional'],
                    ins['source_classification'],
                    ins['match_method'],
                    ins.get('match_score')
                ))
                stats['insertados'] += 1
            except sqlite3.Error as e:
                errores.append(f"{ins['id_oferta']}: {e}")

        conn.commit()
        print(f"[OK] Insertados: {stats['insertados']} registros")

        if errores:
            print(f"[WARNING] Errores: {len(errores)}")
            for err in errores[:5]:
                print(f"  - {err}")
    else:
        print("\n" + "=" * 80)
        print("[!] Modo SIMULACION - cambios NO aplicados")
        print("    Use --apply para aplicar los cambios")

    conn.close()
    print("=" * 80)


if __name__ == '__main__':
    main()
