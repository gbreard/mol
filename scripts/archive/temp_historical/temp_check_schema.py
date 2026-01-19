# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

# Check schema
c.execute("SELECT sql FROM sqlite_master WHERE name = 'ofertas_nlp'")
row = c.fetchone()
if row:
    print("Schema ofertas_nlp:")
    print(row[0][:800])
