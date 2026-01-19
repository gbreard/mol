# -*- coding: utf-8 -*-
"""Debug de completar_nlp_gold_set_100.py para un ID específico."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from nlp_postprocessor import NLPPostprocessor
from limpiar_titulos import limpiar_titulo

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

pp = NLPPostprocessor(verbose=False)

id_oferta = '1118073615'
cursor.execute("""
    SELECT n.*, o.titulo, o.descripcion, o.localizacion
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta = ?
""", (id_oferta,))
row = cursor.fetchone()

if not row:
    print("No encontrado")
    sys.exit(1)

row_dict = dict(row)
titulo = row_dict.get('titulo', '')
descripcion = row_dict.get('descripcion', '')
localizacion = row_dict.get('localizacion', '')

print(f"ID: {id_oferta}")
print(f"area_funcional en BD: '{row_dict.get('area_funcional')}'")
print(f"tipo: {type(row_dict.get('area_funcional'))}")
print(f"bool(area_funcional): {bool(row_dict.get('area_funcional'))}")

# Proceso igual que el script
pre_data = pp.preprocess({'localizacion': localizacion, 'titulo': titulo})
titulo_limpio = limpiar_titulo(titulo) if titulo else None

nlp_data = {k: v for k, v in row_dict.items() if k not in ['titulo', 'descripcion', 'localizacion']}
nlp_data['titulo_limpio'] = titulo_limpio or nlp_data.get('titulo_limpio')

post_data = pp.postprocess(nlp_data, descripcion)

print(f"\npost_data['area_funcional']: '{post_data.get('area_funcional')}'")

# Condición del script
cond = not row_dict.get('area_funcional') and post_data.get('area_funcional')
print(f"\nCondicion (not row AND post): {cond}")
print(f"  not row_dict.get('area_funcional'): {not row_dict.get('area_funcional')}")
print(f"  post_data.get('area_funcional'): {post_data.get('area_funcional')}")

conn.close()
