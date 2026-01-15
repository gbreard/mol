# -*- coding: utf-8 -*-
"""Reprocesar una oferta con postprocessor."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from nlp_postprocessor import NLPPostprocessor
from limpiar_titulos import limpiar_titulo

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"

id_oferta = sys.argv[1] if len(sys.argv) > 1 else '2135143'

# Forzar recarga de configs
NLPPostprocessor._config_loaded = False
NLPPostprocessor._config_cache = None

pp = NLPPostprocessor(verbose=True)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Obtener datos
cur.execute('''
    SELECT n.*, o.titulo, o.descripcion, o.localizacion
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta = ?
''', (id_oferta,))
row = cur.fetchone()

if not row:
    print(f"Oferta {id_oferta} no encontrada")
    sys.exit(1)

row_dict = dict(row)
titulo = row_dict.get('titulo', '')
descripcion = row_dict.get('descripcion', '')
localizacion = row_dict.get('localizacion', '')

print(f"=== OFERTA {id_oferta} ===")
print(f"Titulo: {titulo}")
print(f"Descripcion (100 chars): {descripcion[:100]}...")
print()

# Preprocesar
pre_data = pp.preprocess({'localizacion': localizacion, 'titulo': titulo})
print(f"Preprocesado: {pre_data}")

# Limpiar titulo
titulo_limpio = limpiar_titulo(titulo) if titulo else None

# Preparar datos NLP (sin campos de oferta original)
nlp_data = {k: v for k, v in row_dict.items()
            if k not in ['titulo', 'descripcion', 'localizacion']}
nlp_data['titulo_limpio'] = titulo_limpio

# Forzar None para que se re-infiera
nlp_data['area_funcional'] = None
nlp_data['modalidad'] = None
nlp_data['sector_empresa'] = None
nlp_data['tareas_explicitas'] = None  # Reset tareas para probar extracción completa

# Postprocesar
print("\n=== POSTPROCESANDO ===")
post_data = pp.postprocess(nlp_data, descripcion)

print(f"\n=== RESULTADO ===")
print(f"area_funcional: {post_data.get('area_funcional')}")
print(f"modalidad: {post_data.get('modalidad')}")
print(f"sector_empresa: {post_data.get('sector_empresa')}")
print(f"nivel_seniority: {post_data.get('nivel_seniority')}")
print(f"tareas_explicitas: {post_data.get('tareas_explicitas')}")

# Guardar automáticamente
cur.execute('''
    UPDATE ofertas_nlp
    SET area_funcional = ?, modalidad = ?, sector_empresa = ?, tareas_explicitas = ?
    WHERE id_oferta = ?
''', (post_data.get('area_funcional'), post_data.get('modalidad'),
      post_data.get('sector_empresa'), post_data.get('tareas_explicitas'), id_oferta))
conn.commit()
print("\n[OK] Guardado en BD")

conn.close()
