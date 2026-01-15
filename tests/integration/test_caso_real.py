# -*- coding: utf-8 -*-
"""Test del caso real 1118073615."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from nlp_postprocessor import NLPPostprocessor
from limpiar_titulos import limpiar_titulo

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

id_oferta = '1118073615'
cur.execute("""
    SELECT n.*, o.titulo, o.descripcion, o.localizacion
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta = ?
""", (id_oferta,))
row = cur.fetchone()
row_dict = dict(row)

titulo = row_dict.get('titulo', '')
descripcion = row_dict.get('descripcion', '')

print(f"ID: {id_oferta}")
print(f"Titulo original: {titulo}")
print(f"Titulo limpio BD: {row_dict.get('titulo_limpio')}")
print(f"Area actual BD: {row_dict.get('area_funcional')}")
print(f"Descripcion (primeros 300 chars):")
print(f"  {descripcion[:300]}")
print()

# Simular lo que hace completar_nlp_gold_set_100.py
pp = NLPPostprocessor(verbose=True)

titulo_limpio = limpiar_titulo(titulo) if titulo else None
print(f"\nTitulo limpio calculado: {titulo_limpio}")

nlp_data = {k: v for k, v in row_dict.items() if k not in ['titulo', 'descripcion', 'localizacion']}
nlp_data['titulo_limpio'] = titulo_limpio or nlp_data.get('titulo_limpio')

print(f"\nnlp_data['area_funcional'] antes: {nlp_data.get('area_funcional')}")
print(f"nlp_data['titulo_limpio']: {nlp_data.get('titulo_limpio')}")

post_data = pp.postprocess(nlp_data, descripcion)

print(f"\npost_data['area_funcional'] despues: {post_data.get('area_funcional')}")

conn.close()
