import sqlite3
from pathlib import Path

# Try bumeran_scraping.db instead
db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
print(f"DB path: {db_path}")
print(f"Exists: {db_path.exists()}")
conn = sqlite3.connect(str(db_path))

# List tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

# Check for ofertas or similar
for table in tables:
    name = table[0]
    if 'oferta' in name.lower():
        # Get schema
        schema = conn.execute(f"PRAGMA table_info({name})").fetchall()
        print(f"\n{name} columns:")
        for col in schema[:10]:
            print(f"  - {col[1]} ({col[2]})")

        # Get sample
        sample = conn.execute(f"SELECT id, titulo FROM {name} LIMIT 3").fetchall()
        print(f"\nSample IDs: {[s[0] for s in sample]}")

conn.close()
