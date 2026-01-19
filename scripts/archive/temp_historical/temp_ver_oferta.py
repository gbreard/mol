# -*- coding: utf-8 -*-
"""Ver oferta especifica."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

id_oferta = sys.argv[1] if len(sys.argv) > 1 else '2135143'

# Datos de la oferta original
cur.execute('''
    SELECT id_oferta, titulo, empresa, localizacion, descripcion
    FROM ofertas WHERE id_oferta = ?
''', (id_oferta,))
row = cur.fetchone()

if row:
    print('=== OFERTA ORIGINAL ===')
    print(f"ID: {row['id_oferta']}")
    print(f"Titulo: {row['titulo']}")
    print(f"Empresa: {row['empresa']}")
    print(f"Ubicacion: {row['localizacion']}")
    print(f"\nDescripcion:")
    print(row['descripcion'][:2000] if row['descripcion'] else 'N/A')
    print("\n" + "="*50)

    # Datos NLP
    cur.execute('''
        SELECT * FROM ofertas_nlp WHERE id_oferta = ?
    ''', (id_oferta,))
    nlp = cur.fetchone()

    if nlp:
        print('\n=== DATOS NLP EXTRAIDOS ===')
        campos_clave = [
            'titulo_limpio', 'provincia', 'localidad', 'area_funcional',
            'modalidad', 'nivel_seniority', 'skills_tecnicas_list',
            'soft_skills_list', 'tareas_explicitas', 'sector_empresa',
            'experiencia_min_anios', 'experiencia_max_anios', 'nivel_educativo'
        ]
        for campo in campos_clave:
            valor = nlp[campo] if campo in nlp.keys() else 'N/A'
            print(f"{campo}: {valor}")
else:
    print('Oferta no encontrada')

conn.close()
