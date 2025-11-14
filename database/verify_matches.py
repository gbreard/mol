#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Contar matches
cursor.execute('SELECT COUNT(*) FROM ofertas_esco_matching')
count = cursor.fetchone()[0]
print(f'Total matches guardados: {count:,}')

# Ver primeros 5
cursor.execute('''
    SELECT id_oferta, esco_occupation_label, occupation_match_score
    FROM ofertas_esco_matching
    ORDER BY occupation_match_score DESC
    LIMIT 5
''')
rows = cursor.fetchall()

print('\nTop 5 matches por score:')
for r in rows:
    print(f'  Oferta {r[0]}: {r[1][:50]}... (score: {r[2]:.3f})')

# Estadísticas
cursor.execute('SELECT AVG(occupation_match_score), MIN(occupation_match_score), MAX(occupation_match_score) FROM ofertas_esco_matching')
avg, min_score, max_score = cursor.fetchone()
print(f'\nEstadísticas de scores:')
print(f'  Promedio: {avg:.3f}')
print(f'  Mínimo:   {min_score:.3f}')
print(f'  Máximo:   {max_score:.3f}')

conn.close()
