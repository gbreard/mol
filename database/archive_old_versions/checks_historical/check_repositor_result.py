# -*- coding: utf-8 -*-
"""Verificar resultado Repositor (1117990944) despues del bypass."""
import sqlite3

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
c = sqlite3.connect(db_path)

print("="*60)
print("RESULTADO REPOSITOR (1117990944) - DESPUES DEL BYPASS")
print("="*60)

sql = """SELECT esco_occupation_label, isco_code, occupation_match_method,
         score_final_ponderado, match_confirmado
         FROM ofertas_esco_matching WHERE id_oferta='1117990944'"""
row = c.execute(sql).fetchone()
if row:
    print(f"  ESCO Label: {row[0]}")
    print(f"  ISCO Code:  {row[1]}")
    print(f"  Metodo:     {row[2]}")
    print(f"  Score:      {row[3]}")
    print(f"  Confirmado: {row[4]}")
else:
    print("  (no hay resultado)")

c.close()
