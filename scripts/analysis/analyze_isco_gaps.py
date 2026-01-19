#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze_isco_gaps.py
====================
Analiza los códigos ISCO faltantes en esco_occupations
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bumeran_scraping.db')

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Contar ocupaciones con/sin ISCO
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN isco_code IS NULL OR isco_code = '' THEN 1 ELSE 0 END) as sin_isco,
            SUM(CASE WHEN isco_code IS NOT NULL AND isco_code != '' THEN 1 ELSE 0 END) as con_isco
        FROM esco_occupations
    """)
    row = cursor.fetchone()
    print(f"Total ocupaciones: {row['total']}")
    print(f"Sin ISCO: {row['sin_isco']} ({row['sin_isco']/row['total']*100:.1f}%)")
    print(f"Con ISCO: {row['con_isco']} ({row['con_isco']/row['total']*100:.1f}%)")

    # Muestra de ocupaciones sin ISCO
    print("\n--- Muestra ocupaciones SIN codigo ISCO ---")
    cursor.execute("""
        SELECT preferred_label_es, esco_code, occupation_uri
        FROM esco_occupations
        WHERE isco_code IS NULL OR isco_code = ''
        LIMIT 15
    """)
    for row in cursor.fetchall():
        label = (row['preferred_label_es'] or '')[:55]
        print(f"  {label:<55} | {row['esco_code']}")

    # Verificar estructura de esco_code vs isco_code
    print("\n--- Ejemplos de ocupaciones CON codigo ISCO ---")
    cursor.execute("""
        SELECT preferred_label_es, esco_code, isco_code
        FROM esco_occupations
        WHERE isco_code IS NOT NULL AND isco_code != ''
        LIMIT 10
    """)
    for row in cursor.fetchall():
        label = (row['preferred_label_es'] or '')[:45]
        print(f"  {label:<45} | esco: {row['esco_code']} | isco: {row['isco_code']}")

    # Verificar si esco_code puede derivar isco_code
    print("\n--- Analisis de patrones esco_code ---")
    cursor.execute("""
        SELECT esco_code, isco_code, COUNT(*) as cnt
        FROM esco_occupations
        WHERE isco_code IS NOT NULL AND isco_code != ''
        GROUP BY esco_code
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"  esco_code: {row['esco_code']} -> isco_code: {row['isco_code']} ({row['cnt']} ocurrencias)")

    conn.close()


if __name__ == '__main__':
    main()
