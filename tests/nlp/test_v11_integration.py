# -*- coding: utf-8 -*-
"""Test de integración v11 con postprocessor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from process_nlp_from_db_v11 import NLPExtractorV11
import sqlite3

# Test con ID del Gold Set
print("Inicializando extractor v11...")
extractor = NLPExtractorV11(verbose=True, enable_implicit_skills=False)

# Obtener una oferta de prueba
db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute('''
    SELECT id_oferta, descripcion, titulo, empresa, localizacion
    FROM ofertas WHERE id_oferta = '1118073615'
''')
row = cur.fetchone()
conn.close()

if row:
    id_of, desc, titulo, empresa, loc = row
    print(f'\nProcesando: {id_of}')
    print(f'Titulo: {titulo[:60]}...')
    print(f'Ubicacion: {loc}')

    result = extractor.process_oferta(
        id_oferta=str(id_of),
        descripcion=desc or '',
        titulo=titulo or '',
        empresa=empresa or '',
        ubicacion=loc or ''
    )

    if result:
        data = result['extracted_data']
        print(f'\n=== RESULTADO ===')
        print(f'area_funcional: {data.get("area_funcional")}')
        print(f'provincia: {data.get("provincia")}')
        print(f'localidad: {data.get("localidad")}')
        print(f'modalidad: {data.get("modalidad")}')
        print(f'nivel_seniority: {data.get("nivel_seniority")}')
        print(f'titulo_limpio: {data.get("titulo_limpio")}')
else:
    print('Oferta no encontrada')
