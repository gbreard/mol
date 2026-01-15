# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id_oferta, titulo_limpio FROM ofertas_nlp WHERE id_oferta LIKE '2123908%' ORDER BY id_oferta")
print("Registros expandidos de 2123908:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")
