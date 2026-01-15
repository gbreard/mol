#!/usr/bin/env python3
"""Test fix R14 para auditor médico."""
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from match_ofertas_v3 import MatcherV3

conn = sqlite3.connect('bumeran_scraping.db')
conn.row_factory = sqlite3.Row

id_oferta = sys.argv[1] if len(sys.argv) > 1 else '1118105872'

# Get NLP data
cur = conn.execute('SELECT * FROM ofertas_nlp WHERE id_oferta = ?', (id_oferta,))
row = cur.fetchone()
oferta_nlp = dict(row)

print(f"Titulo: {oferta_nlp.get('titulo_limpio')}")
print(f"Sector: {oferta_nlp.get('sector_empresa')}")
print(f"Area: {oferta_nlp.get('area_funcional')}")
print()

# Match with verbose
matcher = MatcherV3(verbose=True)
result = matcher.match_and_persist(id_oferta, oferta_nlp)

print()
print('='*50)
print('NUEVO RESULTADO')
print('='*50)
print(f'ISCO: {result.isco_code}')
print(f'Label: {result.esco_label}')
print(f'Metodo: {result.metodo}')
print(f'Score: {result.score}')

conn.close()
