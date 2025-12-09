#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show complete ISCO/ESCO info for Gold Set"""

import sqlite3
import json
from pathlib import Path

# Load Gold Set
with open(Path(__file__).parent / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
gold_ids = [str(case['id_oferta']) for case in gold_set]

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
c = conn.cursor()

# Get matching results
placeholders = ','.join(['?'] * len(gold_ids))
c.execute(f'''
    SELECT m.id_oferta, m.isco_code, m.isco_label, m.esco_occupation_label, o.titulo
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    WHERE m.id_oferta IN ({placeholders})
''', gold_ids)

print('=' * 120)
print('GOLD SET - MAPEO ISCO/ESCO COMPLETO')
print('=' * 120)
print()
print(f'| {"ISCO":4} | {"ISCO Label (30 chars)":<30} | {"ESCO Label (35 chars)":<35} | {"Titulo Oferta (25 chars)":<25} |')
print(f'|------|{"-"*32}|{"-"*37}|{"-"*27}|')

for row in c.fetchall():
    id_oferta, isco_code, isco_label, esco_label, titulo = row
    isco = isco_code or 'N/A'
    isco_l = (isco_label or 'N/A')[:30]
    esco_l = (esco_label or 'N/A')[:35]
    titulo_s = (titulo or 'N/A')[:25]
    print(f'| {isco:4} | {isco_l:<30} | {esco_l:<35} | {titulo_s:<25} |')

print()
print('=' * 120)

# Summary by ISCO group
print()
print('RESUMEN POR GRUPO ISCO (NIVEL 1):')
print('-' * 50)
c.execute(f'''
    SELECT isco_nivel1, COUNT(*) as cnt
    FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders}) AND isco_nivel1 IS NOT NULL
    GROUP BY isco_nivel1
    ORDER BY isco_nivel1
''', gold_ids)

isco_groups = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales científicos e intelectuales',
    '3': 'Técnicos y profesionales de nivel medio',
    '4': 'Personal de apoyo administrativo',
    '5': 'Trabajadores de servicios y vendedores',
    '6': 'Agricultores y trabajadores calificados',
    '7': 'Oficiales, operarios y artesanos',
    '8': 'Operadores de instalaciones y máquinas',
    '9': 'Ocupaciones elementales'
}

for row in c.fetchall():
    nivel1, cnt = row
    desc = isco_groups.get(str(nivel1), 'Desconocido')
    print(f'  ISCO {nivel1}: {cnt:2} ofertas - {desc}')

conn.close()
