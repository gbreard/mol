# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

cur = conn.execute('''
    SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
           n.area_funcional, n.nivel_seniority,
           o.titulo as titulo_original, o.descripcion
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta = ?
''', ('2123908',))

row = cur.fetchone()
if row:
    print(f"ID: {row['id_oferta']}")
    print(f"Titulo Original: {row['titulo_original']}")
    print(f"Titulo Limpio: {row['titulo_limpio']}")
    print(f"Area: {row['area_funcional']}")
    print(f"Seniority: {row['nivel_seniority']}")
    tareas = row['tareas_explicitas'] or ''
    print(f"Tareas ({len(tareas)} chars): {tareas[:300]}...")
else:
    print("No encontrado en BD")

conn.close()
