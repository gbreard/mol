#!/usr/bin/env python3
"""Check database statistics for export_to_s3"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Count ofertas
cursor.execute('SELECT COUNT(*) FROM ofertas')
print(f'Total ofertas: {cursor.fetchone()[0]}')

# Count ofertas with matching
cursor.execute('SELECT COUNT(*) FROM ofertas_esco_matching')
print(f'Ofertas con matching: {cursor.fetchone()[0]}')

# Status fields
cursor.execute('''
    SELECT
        SUM(CASE WHEN match_confirmado = 1 THEN 1 ELSE 0 END) as confirmados,
        SUM(CASE WHEN requiere_revision = 1 THEN 1 ELSE 0 END) as revision,
        COUNT(*) as total
    FROM ofertas_esco_matching
''')
row = cursor.fetchone()
print(f'Confirmados: {row[0]}, Revision: {row[1]}, Total: {row[2]}')

# Score distribution
cursor.execute('''
    SELECT
        SUM(CASE WHEN score_final_ponderado >= 0.60 THEN 1 ELSE 0 END) as alto,
        SUM(CASE WHEN score_final_ponderado >= 0.50 AND score_final_ponderado < 0.60 THEN 1 ELSE 0 END) as medio,
        SUM(CASE WHEN score_final_ponderado < 0.50 THEN 1 ELSE 0 END) as bajo,
        AVG(score_final_ponderado) as promedio
    FROM ofertas_esco_matching
''')
row = cursor.fetchone()
print(f'Score >= 0.60: {row[0]}, 0.50-0.60: {row[1]}, < 0.50: {row[2]}')
if row[3]:
    print(f'Score promedio: {row[3]:.3f}')

# Check for candidates table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f'Todas las tablas: {tables}')

# Matching version
cursor.execute('SELECT DISTINCT matching_version FROM ofertas_esco_matching LIMIT 5')
versions = [r[0] for r in cursor.fetchall()]
print(f'Versions: {versions}')

# Sample row from matching
cursor.execute('SELECT id_oferta, esco_occupation_label, score_final_ponderado, match_confirmado, requiere_revision FROM ofertas_esco_matching LIMIT 3')
print('\nSample matches:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
