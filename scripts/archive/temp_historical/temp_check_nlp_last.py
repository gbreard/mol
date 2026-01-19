# -*- coding: utf-8 -*-
"""Verificar ultimo procesamiento NLP en BD."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Ver estructura de ofertas_nlp
print("=" * 60)
print("ESTRUCTURA TABLA ofertas_nlp:")
print("=" * 60)
cur.execute("PRAGMA table_info(ofertas_nlp)")
cols = [c[1] for c in cur.fetchall()]
print(f"Total columnas: {len(cols)}")
# Mostrar columnas clave
key_cols = ['id', 'oferta_id', 'version', 'nlp_version', 'created_at', 'updated_at', 'processed_at']
for kc in key_cols:
    if kc in cols:
        print(f"  - {kc}")

# 2. Ver tabla nlp_versions
print("\n" + "=" * 60)
print("TABLA nlp_versions:")
print("=" * 60)
cur.execute("SELECT * FROM nlp_versions ORDER BY id DESC LIMIT 10")
rows = cur.fetchall()
if rows:
    col_names = [d[0] for d in cur.description]
    print(f"Columnas: {col_names}")
    for row in rows:
        print(f"  {dict(row)}")
else:
    print("  (vacia)")

# 3. Contar registros en ofertas_nlp por version
print("\n" + "=" * 60)
print("CONTEO POR VERSION EN ofertas_nlp:")
print("=" * 60)
if 'nlp_version' in cols:
    cur.execute("""
        SELECT nlp_version, COUNT(*) as cnt
        FROM ofertas_nlp
        GROUP BY nlp_version
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} ofertas")
elif 'version' in cols:
    cur.execute("""
        SELECT version, COUNT(*) as cnt
        FROM ofertas_nlp
        GROUP BY version
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} ofertas")

# 4. Ver ultimos 5 registros procesados
print("\n" + "=" * 60)
print("ULTIMOS 5 REGISTROS PROCESADOS (ofertas_nlp):")
print("=" * 60)
# Buscar columna de fecha
date_col = None
for c in ['processed_at', 'updated_at', 'created_at']:
    if c in cols:
        date_col = c
        break

if date_col:
    ver_col = 'nlp_version' if 'nlp_version' in cols else 'version' if 'version' in cols else None
    if ver_col:
        cur.execute(f"""
            SELECT oferta_id, {ver_col}, {date_col}, titulo_limpio
            FROM ofertas_nlp
            ORDER BY {date_col} DESC
            LIMIT 5
        """)
    else:
        cur.execute(f"""
            SELECT oferta_id, {date_col}, titulo_limpio
            FROM ofertas_nlp
            ORDER BY {date_col} DESC
            LIMIT 5
        """)
    for row in cur.fetchall():
        print(f"  {dict(row)}")

# 5. Total registros
print("\n" + "=" * 60)
print("TOTALES:")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM ofertas_nlp")
print(f"  Total en ofertas_nlp: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM ofertas")
print(f"  Total en ofertas: {cur.fetchone()[0]}")

conn.close()
