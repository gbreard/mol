# -*- coding: utf-8 -*-
"""Re-ejecutar matching para caso Repositor."""
import sys
sys.path.insert(0, r'D:\OEDE\Webscrapping\database')

from match_ofertas_multicriteria import MultiCriteriaMatcher

print("Inicializando matcher...")
matcher = MultiCriteriaMatcher()

print("\nRe-ejecutando matching para caso Repositor (1117990944)...")
matcher.process_ofertas(limit=1, ids=['1117990944'])

print("\nVerificando resultado en DB...")
import sqlite3
conn = sqlite3.connect(r'D:\OEDE\Webscrapping\database\bumeran_scraping.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.esco_occupation_uri
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    WHERE m.id_oferta = '1117990944'
''')
row = cursor.fetchone()
if row:
    print(f"  ID: {row[0]}")
    print(f"  Titulo: {row[1]}")
    print(f"  ESCO: {row[2]}")
    print(f"  URI: {row[3]}")
else:
    print("  No encontrado")

conn.close()
print("\nOK")
