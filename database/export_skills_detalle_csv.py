#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exportar tabla ofertas_esco_skills_detalle a CSV

Incluye todos los campos con metadatos ESCO completos.

Uso:
    python export_skills_detalle_csv.py                    # Exportar todo
    python export_skills_detalle_csv.py --version v8.3    # Solo version v8.3
    python export_skills_detalle_csv.py --output mi_archivo.csv

Autor: Sistema MOL
Fecha: 2025-12-01
"""

import sqlite3
import csv
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


def main():
    parser = argparse.ArgumentParser(description='Exportar ofertas_esco_skills_detalle a CSV')
    parser.add_argument('--output', type=str, default=None, help='Archivo CSV de salida')
    parser.add_argument('--version', type=str, default=None, help='Filtrar por matching_version')
    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = args.output or f'skills_detalle_export_{timestamp}.csv'
    output_path = Path(__file__).parent / output_file

    print("=" * 80)
    print("EXPORTAR ofertas_esco_skills_detalle A CSV")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Construir query con JOIN a ofertas y ocupaciones
    if args.version:
        query = '''
            SELECT
                d.id,
                d.id_oferta,
                o.titulo AS titulo_oferta,
                m.esco_occupation_label AS ocupacion_esco,
                m.isco_code,
                d.skill_mencionado,
                d.skill_tipo_fuente,
                d.esco_skill_uri,
                d.esco_skill_label,
                d.esco_skill_type,
                d.esco_skill_reusability,
                d.is_essential_for_occupation AS is_essential,
                d.is_optional_for_occupation AS is_optional,
                d.match_method,
                m.matching_version
            FROM ofertas_esco_skills_detalle d
            LEFT JOIN ofertas o ON d.id_oferta = o.id_oferta
            LEFT JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
            WHERE m.matching_version LIKE ?
            ORDER BY d.id_oferta, d.is_essential_for_occupation DESC, d.skill_mencionado
        '''
        cursor.execute(query, (f'%{args.version}%',))
    else:
        query = '''
            SELECT
                d.id,
                d.id_oferta,
                o.titulo AS titulo_oferta,
                m.esco_occupation_label AS ocupacion_esco,
                m.isco_code,
                d.skill_mencionado,
                d.skill_tipo_fuente,
                d.esco_skill_uri,
                d.esco_skill_label,
                d.esco_skill_type,
                d.esco_skill_reusability,
                d.is_essential_for_occupation AS is_essential,
                d.is_optional_for_occupation AS is_optional,
                d.match_method,
                m.matching_version
            FROM ofertas_esco_skills_detalle d
            LEFT JOIN ofertas o ON d.id_oferta = o.id_oferta
            LEFT JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
            ORDER BY d.id_oferta, d.is_essential_for_occupation DESC, d.skill_mencionado
        '''
        cursor.execute(query)

    rows = cursor.fetchall()
    print(f"[INFO] Registros a exportar: {len(rows)}")

    if len(rows) == 0:
        print("[WARNING] No hay registros para exportar")
        conn.close()
        return

    # Obtener nombres de columnas
    columns = rows[0].keys()

    # Escribir CSV
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(list(row))

    conn.close()

    # Estadisticas
    print(f"\n[OK] Exportado a: {output_path}")
    print(f"     Columnas: {len(columns)}")
    print(f"     Registros: {len(rows)}")

    # Resumen por skill_type
    print("\n" + "-" * 40)
    print("RESUMEN POR TIPO DE SKILL:")
    type_counts = {}
    for row in rows:
        skill_type = row['esco_skill_type'] or 'sin_tipo'
        type_counts[skill_type] = type_counts.get(skill_type, 0) + 1
    for k, v in sorted(type_counts.items()):
        print(f"  {k}: {v}")

    # Resumen essential/optional
    essential_count = sum(1 for r in rows if r['is_essential'])
    optional_count = sum(1 for r in rows if r['is_optional'])
    print(f"\n  ESSENTIAL: {essential_count}")
    print(f"  OPTIONAL:  {optional_count}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
