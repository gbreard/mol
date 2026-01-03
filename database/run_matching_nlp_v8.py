#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejecutar matching SOLO para ofertas con NLP v8.0 sin matching
"""

import sqlite3
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from match_ofertas_multicriteria import ESCOMatcher

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def get_nlp_v8_ids_without_matching():
    """Obtiene IDs con NLP v8.0 pero sin matching"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.id_oferta
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0' AND m.id_oferta IS NULL
    ''')

    ids = [str(row[0]) for row in cursor.fetchall()]
    conn.close()
    return ids

def main():
    print("=" * 70)
    print("MATCHING SOLO PARA OFERTAS CON NLP v8.0")
    print("=" * 70)

    # Get IDs
    ids = get_nlp_v8_ids_without_matching()
    print(f"\nOfertas con NLP v8.0 sin matching: {len(ids)}")

    if not ids:
        print("No hay ofertas pendientes.")
        return

    # Initialize matcher
    print("\nInicializando matcher...")
    matcher = ESCOMatcher(db_path=str(DB_PATH))

    # Get ofertas for these specific IDs
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f'''
        SELECT o.id_oferta, o.titulo, o.descripcion, o.empresa
        FROM ofertas o
        WHERE CAST(o.id_oferta AS TEXT) IN ({placeholders})
    ''', ids)

    ofertas = cursor.fetchall()
    conn.close()

    print(f"Ofertas encontradas en DB: {len(ofertas)}")

    # Process matching
    print(f"\nProcesando {len(ofertas)} ofertas...")
    matcher.process_ofertas_batch(ofertas)

    print("\n[OK] Matching completado")

if __name__ == "__main__":
    main()
