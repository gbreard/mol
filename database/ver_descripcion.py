#!/usr/bin/env python3
import sqlite3
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

id_oferta = sys.argv[1] if len(sys.argv) > 1 else '1118105872'

conn = sqlite3.connect('bumeran_scraping.db')

# Descripcion completa
cur = conn.execute('SELECT descripcion FROM ofertas WHERE id_oferta = ?', (id_oferta,))
row = cur.fetchone()
print('='*70)
print('DESCRIPCION COMPLETA')
print('='*70)
print(row[0] if row else 'No encontrada')

# Tareas extraidas
print()
print('='*70)
print('TAREAS EXTRAIDAS (NLP)')
print('='*70)
cur = conn.execute('SELECT tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?', (id_oferta,))
row = cur.fetchone()
tareas = row[0] if row else ''
print(tareas)
print()
if tareas:
    lista = [t.strip() for t in tareas.split(';') if t.strip()]
    print(f'Cantidad de tareas: {len(lista)}')
    for i, t in enumerate(lista, 1):
        print(f'  {i}. {t}')

conn.close()
