import sqlite3
conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Todas las tablas:")
for t in sorted(tables):
    print(f"  {t}")

nlp_tables = [t for t in tables if 'nlp' in t.lower()]
print(f"\nTablas con 'nlp': {nlp_tables}")
