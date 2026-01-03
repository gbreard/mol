import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("TABLAS EN LA BD:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Check for NLP-related tables
print("\nBUSCANDO TABLAS NLP:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%nlp%'")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%parsing%'")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%extract%'")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

conn.close()
