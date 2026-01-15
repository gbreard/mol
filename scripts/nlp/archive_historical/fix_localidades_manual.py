# -*- coding: utf-8 -*-
"""Corrección manual de localidades vacías."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# Correcciones manuales de localidad basadas en el scraping
# El formato del scraping es "Ciudad, Provincia"
fixes = [
    ('2123908', 'Capital Federal'),  # scraping: Capital Federal, Buenos Aires
    ('2130257', 'Capital Federal'),  # scraping: Capital Federal, Buenos Aires
    ('2144019', 'Moreno'),           # scraping: Moreno, Buenos Aires
    ('2145519', 'Capital Federal'),  # scraping: Capital Federal, Buenos Aires
    ('2155040', 'Capital Federal'),  # scraping: Capital Federal, Buenos Aires
    ('2163782', 'Capital Federal'),  # scraping: Capital Federal, Buenos Aires
]

print("Corrigiendo localidades manualmente:")
for id_oferta, localidad in fixes:
    cur.execute("""
        UPDATE ofertas_nlp
        SET localidad = ?
        WHERE id_oferta = ? AND (localidad IS NULL OR localidad = '')
    """, (localidad, id_oferta))
    if cur.rowcount > 0:
        print(f"  {id_oferta} -> localidad = {localidad}")
    else:
        print(f"  {id_oferta} -> ya tenia localidad, no actualizado")

conn.commit()
conn.close()
print("\nHecho!")
