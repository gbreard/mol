import sqlite3
conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tablas con 'match' o 'esco':")
for t in sorted(tables):
    if 'match' in t.lower() or 'esco' in t.lower():
        print(f"  {t}")
