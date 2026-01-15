#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script temporal para verificar estructura de DB"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ver esquema de esco_skills
    print("=== esco_skills ===")
    cursor.execute('PRAGMA table_info(esco_skills)')
    for row in cursor.fetchall():
        print(row)

    print()

    # Contar ofertas v8.3
    cursor.execute('''SELECT COUNT(*) FROM ofertas_esco_matching
                      WHERE matching_version = "v8.3_esco_familias_funcionales"''')
    print(f"Total ofertas v8.3: {cursor.fetchone()[0]}")

    # Ver cuantos registros hay ya en ofertas_esco_skills_detalle
    cursor.execute('SELECT COUNT(*) FROM ofertas_esco_skills_detalle')
    print(f"Registros en skills_detalle: {cursor.fetchone()[0]}")

    # Ver ejemplo de skills_matched (sin caracteres especiales)
    print("\n=== skills_matched ejemplo (ASCII) ===")
    cursor.execute('''SELECT id_oferta, skills_matched_essential, skills_matched_optional
                      FROM ofertas_esco_matching
                      WHERE matching_version = "v8.3_esco_familias_funcionales"
                      AND skills_matched_essential IS NOT NULL
                      LIMIT 2''')
    for row in cursor.fetchall():
        print(f"ID: {row[0]}")
        # Reemplazar flecha por ASCII
        essential = row[1].replace('\u2192', ' -> ') if row[1] else 'NULL'
        optional = row[2].replace('\u2192', ' -> ') if row[2] else 'NULL'
        print(f"  Essential: {essential[:200]}...")
        print(f"  Optional: {optional[:200]}...")

    conn.close()

if __name__ == '__main__':
    main()
