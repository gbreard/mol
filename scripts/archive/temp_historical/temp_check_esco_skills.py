# -*- coding: utf-8 -*-
"""Verificar estructura tabla esco_skills."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ver si existe tabla esco_skills
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='esco_skills'")
exists = cur.fetchone()
print(f"Tabla esco_skills existe: {exists is not None}")

if exists:
    cur.execute("PRAGMA table_info(esco_skills)")
    print("\nColumnas:")
    for col in cur.fetchall():
        print(f"  {col[1]} ({col[2]})")

    cur.execute("SELECT COUNT(*) FROM esco_skills")
    print(f"\nTotal registros: {cur.fetchone()[0]}")

    # Ver si tiene skill_type
    cur.execute("SELECT skill_type, COUNT(*) FROM esco_skills GROUP BY skill_type")
    print("\nDistribucion skill_type:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Ver si tiene skill_reusability_level
    cur.execute("SELECT skill_reusability_level, COUNT(*) FROM esco_skills WHERE skill_reusability_level IS NOT NULL GROUP BY skill_reusability_level")
    print("\nDistribucion skill_reusability_level:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Ver ejemplo
    cur.execute("SELECT skill_uri, preferred_label, skill_type, skill_reusability_level FROM esco_skills LIMIT 3")
    print("\nEjemplos:")
    for row in cur.fetchall():
        print(f"  URI: {row[0][:50]}...")
        print(f"  Label: {row[1]}")
        print(f"  Type: {row[2]}, Reusability: {row[3]}")
        print()

conn.close()
