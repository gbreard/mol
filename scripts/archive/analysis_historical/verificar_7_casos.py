# -*- coding: utf-8 -*-
"""Verificar los 7 casos problemáticos después del reprocesamiento."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

ids_verificar = ['2123908', '2130257', '2144019', '2145519', '2155040', '2163782', '2153268']

print("VERIFICACION DE CASOS PROBLEMATICOS:")
print("=" * 80)

for id_oferta in ids_verificar:
    cur.execute('''
        SELECT n.id_oferta, n.titulo_limpio, n.provincia, n.localidad, n.area_funcional, o.localizacion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        id_o, titulo, prov, loc, area, loc_scrap = row
        titulo = titulo or ""
        print(f"{id_o}: {titulo[:45]}")
        print(f"  scraping:   {loc_scrap}")
        print(f"  provincia:  {prov}")
        print(f"  localidad:  {loc}")
        print(f"  area:       {area}")

        # Verificar problemas
        problemas = []
        if not loc:
            problemas.append("SIN LOCALIDAD")
        if "tecnic" in titulo.lower() and area and "recursos" in area.lower():
            problemas.append("AREA MAL (tecnico->RRHH)")

        if problemas:
            print(f"  [!] PROBLEMAS: {', '.join(problemas)}")
        else:
            print(f"  [OK]")
        print()

conn.close()
