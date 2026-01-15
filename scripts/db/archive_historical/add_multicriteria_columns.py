#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
add_multicriteria_columns.py
============================
Agrega columnas para matching multicriteria a ofertas_esco_matching
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'bumeran_scraping.db')

def main():
    print("=" * 70)
    print("AGREGAR COLUMNAS MULTICRITERIA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columnas a agregar
    nuevas_columnas = [
        ("score_titulo", "REAL", "Score del matching por título (peso 50%)"),
        ("score_skills", "REAL", "Score del matching por skills (peso 40%)"),
        ("score_descripcion", "REAL", "Score del matching por descripción (peso 10%)"),
        ("score_final_ponderado", "REAL", "Score final ponderado"),
        ("skills_oferta_json", "TEXT", "Skills extraídos de la oferta (de ofertas_nlp)"),
        ("skills_matched_essential", "TEXT", "Skills esenciales que matchearon"),
        ("skills_matched_optional", "TEXT", "Skills opcionales que matchearon"),
        ("skills_cobertura", "REAL", "% de skills ESCO cubiertos por la oferta"),
        ("match_confirmado", "INTEGER", "1 si score > 0.75 (confirmado automático)"),
        ("requiere_revision", "INTEGER", "1 si 0.50 < score <= 0.75"),
        ("isco_code", "TEXT", "Código ISCO-08 de la ocupación asignada"),
        ("isco_nivel1", "TEXT", "ISCO nivel 1 (Gran grupo)"),
        ("isco_nivel2", "TEXT", "ISCO nivel 2 (Subgrupo principal)"),
    ]

    # Obtener columnas existentes
    cursor.execute("PRAGMA table_info(ofertas_esco_matching)")
    columnas_existentes = {row[1] for row in cursor.fetchall()}

    print(f"\n[1] Columnas existentes: {len(columnas_existentes)}")

    # Agregar columnas nuevas
    print("\n[2] Agregando columnas nuevas...")
    agregadas = 0
    ya_existen = 0

    for col_name, col_type, col_desc in nuevas_columnas:
        if col_name not in columnas_existentes:
            try:
                cursor.execute(f"ALTER TABLE ofertas_esco_matching ADD COLUMN {col_name} {col_type}")
                print(f"    [+] {col_name} ({col_type})")
                agregadas += 1
            except Exception as e:
                print(f"    [!] Error agregando {col_name}: {e}")
        else:
            print(f"    [=] {col_name} ya existe")
            ya_existen += 1

    conn.commit()

    # Verificar resultado
    print(f"\n[3] Resultado:")
    print(f"    Agregadas: {agregadas}")
    print(f"    Ya existían: {ya_existen}")

    # Mostrar schema final
    print("\n[4] Schema final de ofertas_esco_matching:")
    cursor.execute("PRAGMA table_info(ofertas_esco_matching)")
    for row in cursor.fetchall():
        print(f"    {row[1]:<35} {row[2]}")

    conn.close()
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
