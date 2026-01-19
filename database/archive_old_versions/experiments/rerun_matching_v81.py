#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Re-ejecutar matching para ofertas v8.1 después del fix de descripcion_utf8"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Obtener IDs v8.1
c.execute("SELECT CAST(id_oferta AS TEXT) FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids = [r[0] for r in c.fetchall()]
print(f'IDs v8.1 a re-procesar: {len(ids)}')

# Borrar matching existente para estas ofertas
placeholders = ','.join(['?'] * len(ids))
c.execute(f'DELETE FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})', ids)
deleted = c.rowcount
conn.commit()
print(f'Registros de matching eliminados: {deleted}')

conn.close()
print('Listo para re-ejecutar matching')
