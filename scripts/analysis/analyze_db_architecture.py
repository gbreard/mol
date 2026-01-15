# -*- coding: utf-8 -*-
"""Analizar arquitectura completa de la base de datos MOL."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("ARQUITECTURA BASE DE DATOS MOL")
    print("=" * 80)

    # 1. Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"\nTotal tablas: {len(tables)}")
    print("\nTablas encontradas:")
    for t in tables:
        print(f"  - {t}")

    # 2. Analyze each table
    print("\n" + "=" * 80)
    print("ESTRUCTURA DE TABLAS")
    print("=" * 80)

    table_stats = []

    for table in tables:
        # Count records
        try:
            cursor.execute(f'SELECT COUNT(*) FROM [{table}]')
            count = cursor.fetchone()[0]
        except:
            count = 0

        # Get columns
        cursor.execute(f'PRAGMA table_info([{table}])')
        columns = cursor.fetchall()

        # Get indexes
        cursor.execute(f'PRAGMA index_list([{table}])')
        indexes = cursor.fetchall()

        # Get foreign keys
        cursor.execute(f'PRAGMA foreign_key_list([{table}])')
        fkeys = cursor.fetchall()

        print(f"\n### {table} ({count:,} registros)")
        print("-" * 60)

        print(f"  Columnas ({len(columns)}):")
        pk_cols = []
        for col in columns:
            pk = ' [PK]' if col[5] else ''
            null = 'NOT NULL' if col[3] else 'NULL'
            print(f"    {col[1]:35} {col[2]:15} {null:8}{pk}")
            if col[5]:
                pk_cols.append(col[1])

        if indexes:
            print(f"  Indices ({len(indexes)}):")
            for idx in indexes:
                cursor.execute(f'PRAGMA index_info([{idx[1]}])')
                idx_cols = [c[2] for c in cursor.fetchall()]
                unique = '[UNIQUE]' if idx[2] else ''
                print(f"    {idx[1]}: {idx_cols} {unique}")

        if fkeys:
            print(f"  Foreign Keys ({len(fkeys)}):")
            for fk in fkeys:
                print(f"    {fk[3]} -> {fk[2]}.{fk[4]}")

        # Collect stats
        problems = []
        if not indexes and count > 1000:
            problems.append("Sin índices (>1000 reg)")
        if not pk_cols:
            problems.append("Sin PK")

        table_stats.append({
            'table': table,
            'records': count,
            'columns': len(columns),
            'indexes': len(indexes),
            'fkeys': len(fkeys),
            'problems': problems
        })

    # 3. Summary table
    print("\n" + "=" * 80)
    print("RESUMEN DE SALUD DE BD")
    print("=" * 80)
    print(f"\n{'Tabla':<35} {'Reg':>10} {'Col':>5} {'Idx':>5} {'FK':>3} {'Problemas':<30}")
    print("-" * 95)

    total_records = 0
    for s in table_stats:
        prob_str = ", ".join(s['problems']) if s['problems'] else "OK"
        print(f"{s['table']:<35} {s['records']:>10,} {s['columns']:>5} {s['indexes']:>5} {s['fkeys']:>3} {prob_str:<30}")
        total_records += s['records']

    print("-" * 95)
    print(f"{'TOTAL':<35} {total_records:>10,}")

    # 4. Identify relationships
    print("\n" + "=" * 80)
    print("RELACIONES ENTRE TABLAS")
    print("=" * 80)

    # Check for common fields (id_oferta)
    tables_with_id_oferta = []
    for table in tables:
        cursor.execute(f'PRAGMA table_info([{table}])')
        columns = [c[1] for c in cursor.fetchall()]
        if 'id_oferta' in columns:
            tables_with_id_oferta.append(table)

    print(f"\nTablas con 'id_oferta' ({len(tables_with_id_oferta)}):")
    for t in tables_with_id_oferta:
        print(f"  - {t}")

    # Check ESCO tables
    esco_tables = [t for t in tables if 'esco' in t.lower()]
    print(f"\nTablas ESCO ({len(esco_tables)}):")
    for t in esco_tables:
        print(f"  - {t}")

    conn.close()
    print("\n" + "=" * 80)
    print("FIN DEL ANALISIS")
    print("=" * 80)

if __name__ == '__main__':
    main()
