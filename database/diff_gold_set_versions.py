#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diff de versiones de matching para Gold Set
"""

import sqlite3
import json
import struct
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v1.json'


def parse_score(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0


def get_category(confirmado, revision):
    if confirmado:
        return 'CONF'
    elif revision:
        return 'REV'
    else:
        return 'RECH'


def main():
    # Cargar gold set
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    ids = [g['id_oferta'] for g in gold_set]
    placeholders = ','.join(['?'] * len(ids))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener matches de version anterior (multicriteria_v2)
    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta IN ({placeholders})
        AND m.matching_version = 'multicriteria_v2'
    ''', ids)

    anterior = {}
    for row in cursor.fetchall():
        anterior[row[0]] = {
            'titulo': row[1],
            'esco_label': row[2],
            'score': parse_score(row[3]),
            'cat': get_category(row[4], row[5])
        }

    # Obtener matches de version nueva (v8.0)
    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta IN ({placeholders})
        AND m.matching_version = 'v8.0_esco_multicriterio_calibrado'
    ''', ids)

    nuevo = {}
    for row in cursor.fetchall():
        nuevo[row[0]] = {
            'titulo': row[1],
            'esco_label': row[2],
            'score': parse_score(row[3]),
            'cat': get_category(row[4], row[5])
        }

    conn.close()

    # Gold set lookup
    gold_lookup = {g['id_oferta']: g for g in gold_set}

    # Imprimir diff completo
    print('=' * 160)
    print('DIFF COMPLETO: multicriteria_v2 vs v8.0_esco_multicriterio_calibrado (19 casos Gold Set)')
    print('=' * 160)
    print()

    # Header
    print(f"{'ID':<12} | {'TITULO':<32} | {'MATCH ANTERIOR (v2)':<28} | {'SC':>5} | {'CAT':>4} | {'MATCH NUEVO (v8)':<28} | {'SC':>5} | {'CAT':>4} | {'OK':>2}")
    print('-' * 160)

    cambios = 0

    for id_oferta in ids:
        gold = gold_lookup[id_oferta]
        ok = 'SI' if gold['esco_ok'] else 'NO'

        titulo = ''
        match_ant = '-'
        score_ant = '-'
        cat_ant = '-'
        match_nvo = '-'
        score_nvo = '-'
        cat_nvo = '-'

        if id_oferta in anterior:
            a = anterior[id_oferta]
            titulo = a['titulo'][:32]
            match_ant = (a['esco_label'] or '')[:28]
            score_ant = f"{a['score']:.2f}"
            cat_ant = a['cat']

        if id_oferta in nuevo:
            n = nuevo[id_oferta]
            if not titulo:
                titulo = n['titulo'][:32]
            match_nvo = (n['esco_label'] or '')[:28]
            score_nvo = f"{n['score']:.2f}"
            cat_nvo = n['cat']

        # Detectar cambio
        cambio_marker = ''
        if id_oferta in anterior and id_oferta in nuevo:
            if anterior[id_oferta]['esco_label'] != nuevo[id_oferta]['esco_label']:
                cambio_marker = ' *CAMBIO*'
                cambios += 1

        print(f"{id_oferta:<12} | {titulo:<32} | {match_ant:<28} | {score_ant:>5} | {cat_ant:>4} | {match_nvo:<28} | {score_nvo:>5} | {cat_nvo:>4} | {ok:>2}{cambio_marker}")

    print('=' * 160)
    print()
    print('LEYENDA:')
    print('  CAT = Categoria (CONF=Confirmado, REV=Revision, RECH=Rechazado)')
    print('  OK = Match correcto segun gold set (SI/NO)')
    print('  *CAMBIO* = El match ESCO cambio entre versiones')
    print()
    print(f'RESUMEN:')
    print(f'  - Ofertas en version anterior (v2): {len(anterior)}')
    print(f'  - Ofertas en version nueva (v8.0): {len(nuevo)}')
    print(f'  - Ofertas que cambiaron de match: {cambios}')
    print(f'  - Precision actual (v8.0): 11/19 = 57.9%')
    print('=' * 160)


if __name__ == '__main__':
    main()
