# -*- coding: utf-8 -*-
"""Verificar versiones NLP en Gold Set 100."""
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
db_path = BASE_DIR / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# Cargar IDs
with open(BASE_DIR / "database" / "gold_set_nlp_100_ids.json") as f:
    ids = json.load(f)

# Versiones
placeholders = ','.join(['?'] * len(ids))
cur = conn.execute(f'''
    SELECT nlp_version, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    GROUP BY nlp_version
''', ids)

print("=" * 50)
print("VERSIONES NLP EN GOLD SET 100")
print("=" * 50)
for row in cur:
    print(f"  {row['nlp_version']}: {row['cnt']} ofertas")

# ID 2123908
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, nlp_version, area_funcional, nivel_seniority
    FROM ofertas_nlp WHERE id_oferta = ?
''', ('2123908',))
row = cur.fetchone()
if row:
    print(f"\nID 2123908 (el que preocupaba):")
    print(f"  Version: {row['nlp_version']}")
    print(f"  Titulo: {row['titulo_limpio']}")
    print(f"  Area: {row['area_funcional']}")
    print(f"  Seniority: {row['nivel_seniority']}")

conn.close()
