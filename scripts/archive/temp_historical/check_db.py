# -*- coding: utf-8 -*-
import sqlite3

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
conn = sqlite3.connect(db_path)

# List tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tablas en bumeran_scraping.db:")
for t in tables:
    print(f"  - {t[0]}")

# Check if ofertas_nlp exists
if ('ofertas_nlp',) in tables:
    count = conn.execute("SELECT COUNT(*) FROM ofertas_nlp").fetchone()[0]
    print(f"\nofertas_nlp tiene {count} registros")

conn.close()
