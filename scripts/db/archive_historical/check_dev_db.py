"""Check ofertas_laborales_DEV.db content"""
import sqlite3
import os

db_path = r'D:\OEDE\Webscrapping\ofertas_laborales_DEV.db'
main_db = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'

print(f"=== ofertas_laborales_DEV.db ===")
print(f"Tamaño: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tablas ({len(tables)}): {tables}\n")

# Count records
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} registros")

# Get date range if ofertas table exists
if 'ofertas' in tables:
    print("\n--- Rango de fechas en ofertas ---")
    cursor.execute("SELECT MIN(fecha_publicacion), MAX(fecha_publicacion) FROM ofertas")
    min_date, max_date = cursor.fetchone()
    print(f"Desde: {min_date}")
    print(f"Hasta: {max_date}")

conn.close()

# Compare with main DB
print(f"\n=== Comparación con BD principal ===")
main_conn = sqlite3.connect(main_db)
main_cursor = main_conn.cursor()
main_cursor.execute("SELECT COUNT(*) FROM ofertas")
main_count = main_cursor.fetchone()[0]
print(f"BD principal (database/bumeran_scraping.db): {main_count} ofertas")
main_conn.close()
