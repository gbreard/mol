"""
Test SQLite Integration
=======================

Quick test to verify SQLite database is working correctly.
"""

import sqlite3
from pathlib import Path

# Conectar a la base de datos
db_path = Path('database/bumeran_scraping.db')

if not db_path.exists():
    print(f"ERROR: Base de datos no existe: {db_path}")
    exit(1)

print(f"Conectando a: {db_path}")
print(f"Tamano: {db_path.stat().st_size / 1024:.2f} KB")
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Contar ofertas
cursor.execute("SELECT COUNT(*) FROM ofertas")
count = cursor.fetchone()[0]
print(f"Total ofertas en DB: {count:,}")

if count > 0:
    # Primeras 5 ofertas
    cursor.execute("SELECT id_oferta, titulo, empresa FROM ofertas LIMIT 5")
    print("\nPrimeras 5 ofertas:")
    for row in cursor.fetchall():
        id_oferta, titulo, empresa = row
        print(f"  [{id_oferta}] {titulo[:40]}... - {empresa}")

    # Última oferta
    cursor.execute("SELECT id_oferta, titulo, scrapeado_en FROM ofertas ORDER BY scrapeado_en DESC LIMIT 1")
    row = cursor.fetchone()
    print(f"\nUltima oferta scrapeada:")
    print(f"  ID: {row[0]}")
    print(f"  Titulo: {row[1]}")
    print(f"  Scrapeado: {row[2]}")

# Contar métricas
cursor.execute("SELECT COUNT(*) FROM metricas_scraping")
metricas_count = cursor.fetchone()[0]
print(f"\nTotal ejecuciones registradas: {metricas_count}")

# Contar alertas
cursor.execute("SELECT COUNT(*) FROM alertas")
alertas_count = cursor.fetchone()[0]
print(f"Total alertas: {alertas_count}")

conn.close()

print("\n[OK] Test completado")
