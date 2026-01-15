#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analiza cobertura de familias funcionales v8.3"""

import sqlite3
from matching_rules_v83 import (
    es_oferta_admin_contable, es_oferta_comercial_ventas,
    es_oferta_servicios_atencion, es_oferta_operario_produccion,
    es_oferta_salud_farmacia, es_oferta_programa_pasantia,
    es_oferta_ventas_vehiculos, es_oferta_barista_gastronomia,
    es_oferta_profesional_juridico, es_oferta_nivel_junior
)

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT o.id_oferta, o.titulo, o.descripcion_utf8,
           m.esco_occupation_label, m.score_final_ponderado,
           m.match_confirmado, m.requiere_revision
    FROM ofertas o
    JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.esco_occupation_label IS NOT NULL
''')
ofertas = cursor.fetchall()

familias = {
    'admin_contable': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'comercial_ventas': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'servicios_atencion': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'operario_produccion': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'salud_farmacia': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'programa_pasantia': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'ventas_vehiculos': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'barista_gastronomia': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'profesional_juridico': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'nivel_junior': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []},
    'SIN_FAMILIA': {'count': 0, 'confirmados': 0, 'revision': 0, 'ejemplos': []}
}

for row in ofertas:
    id_oferta, titulo, desc, esco_label, score, confirmado, revision = row
    desc = desc or ''

    if es_oferta_admin_contable(titulo, desc):
        familia = 'admin_contable'
    elif es_oferta_comercial_ventas(titulo, desc):
        familia = 'comercial_ventas'
    elif es_oferta_servicios_atencion(titulo, desc):
        familia = 'servicios_atencion'
    elif es_oferta_operario_produccion(titulo, desc):
        familia = 'operario_produccion'
    elif es_oferta_salud_farmacia(titulo, desc):
        familia = 'salud_farmacia'
    elif es_oferta_programa_pasantia(titulo, desc):
        familia = 'programa_pasantia'
    elif es_oferta_ventas_vehiculos(titulo, desc):
        familia = 'ventas_vehiculos'
    elif es_oferta_barista_gastronomia(titulo, desc):
        familia = 'barista_gastronomia'
    elif es_oferta_profesional_juridico(titulo, desc):
        familia = 'profesional_juridico'
    elif es_oferta_nivel_junior(titulo, desc):
        familia = 'nivel_junior'
    else:
        familia = 'SIN_FAMILIA'

    familias[familia]['count'] += 1
    if confirmado:
        familias[familia]['confirmados'] += 1
    if revision:
        familias[familia]['revision'] += 1

    if len(familias[familia]['ejemplos']) < 3:
        familias[familia]['ejemplos'].append({
            'titulo': titulo[:55] if titulo else 'N/A',
            'esco': esco_label[:45] if esco_label else 'N/A',
            'score': round(score, 2) if score else 0
        })

total = len(ofertas)
print('=' * 80)
print('COBERTURA DE FAMILIAS FUNCIONALES v8.3')
print('=' * 80)
print(f'Total ofertas con matching: {total:,}')
print()

sorted_fam = sorted(familias.items(), key=lambda x: x[1]['count'], reverse=True)

print(f"{'FAMILIA':<25} | {'COUNT':>6} | {'%':>6} | {'REVISION':>8} | {'%REV':>6}")
print('-' * 70)

for nombre, data in sorted_fam:
    pct = (data['count'] / total * 100) if total > 0 else 0
    pct_rev = (data['revision'] / data['count'] * 100) if data['count'] > 0 else 0
    print(f"{nombre:<25} | {data['count']:>6,} | {pct:>5.1f}% | {data['revision']:>8,} | {pct_rev:>5.1f}%")

print()
print('=' * 80)
print('EJEMPLOS POR FAMILIA (Top 6)')
print('=' * 80)

for nombre, data in sorted_fam[:6]:
    print(f"\n--- {nombre} ({data['count']:,} ofertas, {data['revision']} en revision) ---")
    for ej in data['ejemplos']:
        print(f"  [{ej['score']:.2f}] {ej['titulo']}")
        print(f"         -> {ej['esco']}")

# Ofertas SIN_FAMILIA - analizar patrones
print()
print('=' * 80)
print('ANALISIS DE OFERTAS SIN FAMILIA ASIGNADA')
print('=' * 80)

cursor.execute('''
    SELECT o.titulo, COUNT(*) as n
    FROM ofertas o
    JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.esco_occupation_label IS NOT NULL
    GROUP BY LOWER(SUBSTR(o.titulo, 1, 30))
    ORDER BY n DESC
    LIMIT 20
''')
print("\nPatrones de titulo mas frecuentes (primeras 30 chars):")
for row in cursor.fetchall():
    print(f"  {row[1]:>4}x  {row[0][:50]}")

conn.close()
