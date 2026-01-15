# -*- coding: utf-8 -*-
"""Verificar IDs expandidos y descripcion."""
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
db_path = BASE_DIR / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))

# 1. Verificar IDs expandidos en ofertas_nlp
print("=" * 60)
print("1. IDS EXPANDIDOS EN ofertas_nlp")
print("=" * 60)
cur = conn.execute("""
    SELECT id_oferta FROM ofertas_nlp
    WHERE id_oferta LIKE '%/_2' ESCAPE '/'
       OR id_oferta LIKE '%/_3' ESCAPE '/'
       OR id_oferta LIKE '%/_4' ESCAPE '/'
    LIMIT 20
""")
expanded = [r[0] for r in cur.fetchall()]
print(f"Encontrados: {len(expanded)}")
for eid in expanded[:10]:
    print(f"  - {eid}")

# 2. Verificar columnas de ofertas (descripcion)
print("\n" + "=" * 60)
print("2. COLUMNAS DE TABLA ofertas")
print("=" * 60)
cur = conn.execute("PRAGMA table_info(ofertas)")
cols = [r[1] for r in cur.fetchall()]
print(f"Columnas: {cols}")

# 3. Verificar ID 2123908 y sus expansiones
print("\n" + "=" * 60)
print("3. ID 2123908 Y EXPANSIONES")
print("=" * 60)
cur = conn.execute("""
    SELECT id_oferta, titulo_limpio, nlp_version
    FROM ofertas_nlp
    WHERE id_oferta LIKE '2123908%'
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1][:50]}... (v{r[2]})")

conn.close()
