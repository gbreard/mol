#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix_isco_codes.py
=================
Completa los códigos ISCO faltantes en esco_occupations
usando el archivo JSON extraído del RDF oficial de ESCO.

Este script:
1. Lee el JSON con ocupaciones ESCO + códigos ISCO
2. Identifica ocupaciones en la DB sin código ISCO
3. Actualiza los códigos ISCO faltantes por URI
"""

import sqlite3
import json
import os
from datetime import datetime

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), 'bumeran_scraping.db')
ISCO_JSON_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"

def main():
    print("=" * 70)
    print("COMPLETAR CÓDIGOS ISCO FALTANTES")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Cargar JSON con códigos ISCO
    print(f"\n[1] Cargando JSON: {ISCO_JSON_PATH}")
    with open(ISCO_JSON_PATH, 'r', encoding='utf-8') as f:
        isco_data = json.load(f)
    print(f"    Ocupaciones en JSON: {len(isco_data):,}")

    # Crear mapeo URI -> código ISCO
    uri_to_isco = {}
    for occ_id, occ_info in isco_data.items():
        uri = occ_info.get('uri', '')
        isco_4d = occ_info.get('codigo_isco_4d')
        if uri and isco_4d:
            # Formato ISCO en DB es "C" + 4 dígitos (ej: "C2359")
            uri_to_isco[uri] = f"C{isco_4d}"

    print(f"    Ocupaciones con ISCO 4D: {len(uri_to_isco):,}")

    # 2. Conectar a la base de datos
    print(f"\n[2] Conectando a: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 3. Obtener ocupaciones sin código ISCO
    print("\n[3] Buscando ocupaciones sin código ISCO...")
    cursor.execute("""
        SELECT occupation_uri, preferred_label_es, isco_code
        FROM esco_occupations
        WHERE isco_code IS NULL OR isco_code = ''
    """)
    sin_isco = cursor.fetchall()
    print(f"    Ocupaciones sin ISCO: {len(sin_isco):,}")

    # 4. Actualizar códigos ISCO
    print("\n[4] Actualizando códigos ISCO...")
    actualizados = 0
    no_encontrados = 0
    errores = []

    for row in sin_isco:
        uri = row['occupation_uri']
        label = row['preferred_label_es']

        if uri in uri_to_isco:
            nuevo_isco = uri_to_isco[uri]
            try:
                cursor.execute("""
                    UPDATE esco_occupations
                    SET isco_code = ?
                    WHERE occupation_uri = ?
                """, (nuevo_isco, uri))
                actualizados += 1

                if actualizados <= 5:
                    print(f"    [OK] {label[:50]} -> {nuevo_isco}")
            except Exception as e:
                errores.append(f"{label}: {e}")
        else:
            no_encontrados += 1
            if no_encontrados <= 5:
                print(f"    [!] No encontrado en JSON: {label[:50]}")

    # 5. Commit cambios
    conn.commit()
    print(f"\n[5] Commit realizado")

    # 6. Verificar resultado
    print("\n[6] Verificando resultado...")
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN isco_code IS NULL OR isco_code = '' THEN 1 ELSE 0 END) as sin_isco,
            SUM(CASE WHEN isco_code IS NOT NULL AND isco_code != '' THEN 1 ELSE 0 END) as con_isco
        FROM esco_occupations
    """)
    stats = cursor.fetchone()

    # 7. Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Actualizados: {actualizados:,}")
    print(f"  No encontrados en JSON: {no_encontrados:,}")
    print(f"  Errores: {len(errores)}")
    print(f"\n  ESTADO FINAL:")
    print(f"    Total ocupaciones: {stats['total']:,}")
    print(f"    Con ISCO: {stats['con_isco']:,} ({stats['con_isco']/stats['total']*100:.1f}%)")
    print(f"    Sin ISCO: {stats['sin_isco']:,} ({stats['sin_isco']/stats['total']*100:.1f}%)")

    if errores:
        print(f"\n  ERRORES:")
        for e in errores[:10]:
            print(f"    - {e}")

    print("=" * 70)

    conn.close()


if __name__ == '__main__':
    main()
