# -*- coding: utf-8 -*-
"""Corrige los problemas detectados en las 51 ofertas nuevas."""
import sqlite3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from nlp_postprocessor import NLPPostprocessor

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

pp = NLPPostprocessor(verbose=False)

print("=" * 70)
print("CORRIGIENDO PROBLEMAS EN 51 OFERTAS NUEVAS")
print("=" * 70)

# 1. Corregir localidades vacías
ids_loc_vacia = ['2123908', '2130257', '2144019', '2145519', '2155040', '2163782']

print("\n1. LOCALIDADES VACIAS:")
print("-" * 70)

for id_oferta in ids_loc_vacia:
    cur.execute("""
        SELECT o.localizacion, n.provincia, n.localidad
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))
    row = cur.fetchone()
    if row:
        loc_scraping, prov_actual, loc_actual = row
        print(f"\n{id_oferta}:")
        print(f"  scraping: {loc_scraping}")
        print(f"  actual:   prov={prov_actual}, loc={loc_actual}")

        # Usar preprocesador para extraer
        pre_data = pp.preprocess({'ubicacion': loc_scraping})
        nueva_prov = pre_data.get('provincia')
        nueva_loc = pre_data.get('localidad')

        # Normalizar si es array
        if isinstance(nueva_loc, list):
            nueva_loc = nueva_loc[0] if nueva_loc else None
        if isinstance(nueva_prov, list):
            nueva_prov = nueva_prov[0] if nueva_prov else None

        print(f"  extraido: prov={nueva_prov}, loc={nueva_loc}")

        # Actualizar si obtuvimos valores
        updates = []
        params = []
        if nueva_prov and not prov_actual:
            updates.append('provincia = ?')
            params.append(nueva_prov)
        if nueva_loc and not loc_actual:
            updates.append('localidad = ?')
            params.append(nueva_loc)

        if updates:
            params.append(id_oferta)
            cur.execute(f"UPDATE ofertas_nlp SET {', '.join(updates)} WHERE id_oferta = ?", params)
            print(f"  -> ACTUALIZADO")
        else:
            print(f"  -> No se pudo extraer localidad")

# 2. Corregir área mal asignada
print("\n\n2. AREA MAL ASIGNADA:")
print("-" * 70)

id_tecnico = '2153268'
cur.execute("""
    SELECT titulo_limpio, area_funcional, sector_empresa
    FROM ofertas_nlp
    WHERE id_oferta = ?
""", (id_tecnico,))
row = cur.fetchone()
if row:
    titulo, area, sector = row
    print(f"\n{id_tecnico}: {titulo}")
    print(f"  area actual: {area}")
    print(f"  sector: {sector}")

    # Técnico Mecánico/Electromecánico debe ser Ingeniería o Mantenimiento
    nueva_area = "Ingenieria"
    cur.execute("UPDATE ofertas_nlp SET area_funcional = ? WHERE id_oferta = ?",
                (nueva_area, id_tecnico))
    print(f"  -> CORREGIDO a: {nueva_area}")

conn.commit()
conn.close()

print("\n" + "=" * 70)
print("CORRECCIONES APLICADAS")
print("=" * 70)
