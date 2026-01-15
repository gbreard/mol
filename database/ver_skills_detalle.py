#!/usr/bin/env python3
import sqlite3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

id_oferta = sys.argv[1] if len(sys.argv) > 1 else '1118105872'

conn = sqlite3.connect('bumeran_scraping.db')

print(f'SKILLS EXTRAIDAS PARA {id_oferta}')
print('='*70)
cur = conn.execute('''
    SELECT skill_mencionado, match_score, esco_skill_type, skill_tipo_fuente
    FROM ofertas_esco_skills_detalle
    WHERE id_oferta = ?
    ORDER BY match_score DESC
''', (id_oferta,))
skills = cur.fetchall()
for row in skills:
    fuente = row[3] or '?'
    print(f'{row[0]:<55} score={row[1]:.3f} L1={row[2]} fuente={fuente}')

print(f'\nTotal skills: {len(skills)}')

print()
print('='*70)
print('TAREAS EN NLP (input para extracción de skills)')
print('='*70)
cur = conn.execute('SELECT tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?', (id_oferta,))
row = cur.fetchone()
print(row[0] if row else 'N/A')

print()
print('='*70)
print('DESCRIPCION ORIGINAL (responsabilidades reales)')
print('='*70)
cur = conn.execute('SELECT descripcion FROM ofertas WHERE id_oferta = ?', (id_oferta,))
row = cur.fetchone()
desc = row[0] if row else ''
# Extraer solo la parte de responsabilidades
if 'Responsabilidades' in desc:
    start = desc.find('Responsabilidades')
    end = desc.find('Requisitos', start)
    if end == -1:
        end = start + 800
    print(desc[start:end])
else:
    print(desc[:800])

conn.close()
