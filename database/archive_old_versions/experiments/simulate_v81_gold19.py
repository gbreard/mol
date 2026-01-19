#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simulacion v8.1 - Impacto en Gold Set 19 (sin aplicar cambios)"""

import sqlite3
import struct
from pathlib import Path
from matching_rules_v81 import calcular_ajustes_v81, requiere_revision_forzada

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_IDS = [
    '1118026700', '1118026729', '1118027188', '1118027243', '1118027261',
    '1118027276', '1118027662', '1118027834', '1118027941', '1118028027',
    '1118028038', '1118028201', '1118028376', '1118028657', '1118028681',
    '1118028828', '1118028833', '1118028887', '1118028891'
]
THRESHOLD_CONFIRMADO_SCORE = 0.60
THRESHOLD_CONFIRMADO_COVERAGE = 0.40
THRESHOLD_REVISION = 0.50

def parse_score(value):
    if value is None: return 0.0
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, bytes):
        if len(value) == 8: return struct.unpack('d', value)[0]
        elif len(value) == 4: return struct.unpack('f', value)[0]
    return 0.0

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(GOLD_SET_IDS))
    cursor.execute(f'''
        SELECT m.id_oferta, o.titulo, o.descripcion, m.esco_occupation_label,
               m.score_final_ponderado, m.match_confirmado, m.requiere_revision
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta IN ({placeholders})
    ''', GOLD_SET_IDS)

    print('=' * 105)
    print('SIMULACION v8.1 - Impacto de reglas en Gold Set 19')
    print('=' * 105)
    print(f"{'ID':<12} | {'TITULO':<28} | {'SC_ANT':>6} | {'SC_NVO':>6} | {'ANT':>4} | {'NVO':>4} | AJUSTES")
    print('-' * 105)

    conf_to_rev = 0
    total_ajustados = 0

    for row in cursor.fetchall():
        titulo = (row['titulo'] or '')[:28]
        desc = row['descripcion'] or ''
        label = row['esco_occupation_label'] or ''
        score_orig = parse_score(row['score_final_ponderado'])
        conf_ant = 'CONF' if row['match_confirmado'] else ('REV' if row['requiere_revision'] else 'RECH')

        ajuste_total, ajustes = calcular_ajustes_v81(titulo, desc, label)
        score_nuevo = max(0.0, min(1.0, score_orig + ajuste_total))
        forzar_rev = requiere_revision_forzada(titulo)

        # Determinar nuevo estado (usamos score como proxy de coverage para simplificar)
        if forzar_rev:
            conf_nvo = 'REV'
        elif score_nuevo >= THRESHOLD_CONFIRMADO_SCORE:
            conf_nvo = 'CONF'
        elif score_nuevo >= THRESHOLD_REVISION:
            conf_nvo = 'REV'
        else:
            conf_nvo = 'RECH'

        cambio = ''
        if conf_ant != conf_nvo:
            cambio = ' *'
        if conf_ant == 'CONF' and conf_nvo == 'REV':
            conf_to_rev += 1
        if ajuste_total != 0:
            total_ajustados += 1

        ajuste_str = str(ajustes) if ajustes else '-'
        print(f"{row['id_oferta']:<12} | {titulo:<28} | {score_orig:>6.3f} | {score_nuevo:>6.3f} | {conf_ant:>4} | {conf_nvo:>4}{cambio} | {ajuste_str[:35]}")

    print('=' * 105)
    print(f'Ofertas con ajuste de score: {total_ajustados}')
    print(f'CONF -> REV: {conf_to_rev} ofertas')
    print('=' * 105)
    conn.close()

if __name__ == '__main__':
    main()
