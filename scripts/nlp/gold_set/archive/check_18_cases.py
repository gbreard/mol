# -*- coding: utf-8 -*-
"""Verificar estado actual de los 18 casos con error del Excel"""
import sqlite3
from pathlib import Path

# IDs de los 18 casos con error en el Excel
error_ids = [
    '1118027941', '1118028027', '1118018714', '1117995368', '2162667',
    '1118026729', '1118027276', '1117984105', '1118018461', '1118009739',
    '1118000814', '1118020225', '2165052', '1118028376', '2165301',
    '1118023904', '2170124', '1117977340'
]

# Conectar a BD (la principal es bumeran_scraping.db)
db_path = Path(__file__).parent.parent / 'database' / 'bumeran_scraping.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Primero ver las tablas disponibles
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tablas en BD: {tables}")

# Ver columnas de ofertas_esco_matching
cursor.execute("PRAGMA table_info(ofertas_esco_matching)")
match_cols = [c[1] for c in cursor.fetchall()]
print(f"Columnas ofertas_esco_matching: {match_cols}")

# Ver columnas de ofertas
cursor.execute("PRAGMA table_info(ofertas)")
ofertas_cols = [c[1] for c in cursor.fetchall()]
print(f"Columnas ofertas: {[c for c in ofertas_cols if 'titulo' in c.lower()]}")

print("\n" + "=" * 100)
print("VERIFICACION DE 18 CASOS - ESTADO ACTUAL DEL PIPELINE")
print("=" * 100)

for id_oferta in error_ids:
    # Join ofertas + ofertas_esco_matching con nombres correctos de columnas
    query = """
        SELECT o.titulo, m.esco_occupation_label, m.isco_code, m.occupation_match_score, m.occupation_match_method
        FROM ofertas o
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE o.id_oferta = ?
    """
    cursor.execute(query, (id_oferta,))
    row = cursor.fetchone()
    if row:
        titulo = (str(row[0])[:50] + '...') if row[0] and len(str(row[0])) > 50 else (row[0] or 'N/A')
        esco = (str(row[1])[:45] + '...') if row[1] and len(str(row[1])) > 45 else (row[1] or 'Sin matching')
        isco = row[2] if row[2] else 'N/A'
        score = f'{row[3]:.3f}' if row[3] else 'N/A'
        method = str(row[4])[:30] if row[4] else 'N/A'
        print(f"\nID: {id_oferta}")
        print(f"  Titulo: {titulo}")
        print(f"  ESCO: {esco}")
        print(f"  ISCO: {isco} | Score: {score} | Metodo: {method}")
    else:
        print(f"\nID: {id_oferta} - NO ENCONTRADO EN BD")

conn.close()
