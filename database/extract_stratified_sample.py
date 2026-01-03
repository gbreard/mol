#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extracción de muestra estratificada del matching ESCO v8.0
"""

import sqlite3
import csv
import struct
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def parse_score(value):
    """Convierte score que puede ser float, bytes (float32) o None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return None

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query base
    query_template = '''
    SELECT
        m.id_oferta,
        o.titulo,
        m.esco_occupation_label,
        e.isco_code,
        CASE
            WHEN e.isco_code IS NOT NULL AND LENGTH(e.isco_code) >= 2
            THEN SUBSTR(e.isco_code, 2, 1)
            ELSE 'N/A'
        END as isco_nivel1,
        m.score_final_ponderado as score_final,
        m.skills_cobertura as coverage,
        m.match_confirmado,
        m.requiere_revision
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    LEFT JOIN esco_occupations e ON m.esco_occupation_uri = e.occupation_uri
    WHERE m.matching_version = 'v8.0_esco_multicriterio_calibrado'
      AND {condition}
    ORDER BY m.score_final_ponderado DESC
    LIMIT 20
    '''

    # Tres grupos
    grupos = [
        ('CONFIRMADO', 'm.match_confirmado = 1'),
        ('REVISION', 'm.requiere_revision = 1'),
        ('RECHAZADO', 'm.match_confirmado = 0 AND m.requiere_revision = 0')
    ]

    all_rows = []
    for nombre, condition in grupos:
        query = query_template.format(condition=condition)
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f'{nombre}: {len(rows)} ofertas')
        for r in rows:
            score_val = parse_score(r['score_final'])
            cov_val = parse_score(r['coverage'])
            all_rows.append({
                'grupo': nombre,
                'id_oferta': r['id_oferta'],
                'titulo': (r['titulo'] or '')[:60],
                'esco_label': (r['esco_occupation_label'] or '')[:45],
                'isco_code': r['isco_code'] or 'N/A',
                'isco_nivel1': r['isco_nivel1'],
                'score_final': score_val,
                'coverage': cov_val,
                'confirmado': r['match_confirmado'],
                'revision': r['requiere_revision']
            })

    # Guardar CSV
    csv_path = Path(__file__).parent / 'muestreo_estratificado_v8.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['grupo','id_oferta','titulo','esco_label','isco_code','isco_nivel1','score_final','coverage','confirmado','revision'])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f'\nCSV guardado: {csv_path}')
    print(f'Total registros: {len(all_rows)}')

    # Mostrar tabla Markdown
    print('\n\n## MUESTREO ESTRATIFICADO v8.0\n')

    for grupo_nombre in ['CONFIRMADO', 'REVISION', 'RECHAZADO']:
        grupo_rows = [r for r in all_rows if r['grupo'] == grupo_nombre]
        print(f'\n### {grupo_nombre} ({len(grupo_rows)} ofertas)\n')
        print('| id | titulo | esco_label | ISCO | score | coverage | eval |')
        print('|---|---|---|---|---|---|---|')
        for r in grupo_rows:
            titulo_short = r['titulo'][:40] + '...' if len(r['titulo']) > 40 else r['titulo']
            esco_short = r['esco_label'][:35] + '...' if len(r['esco_label']) > 35 else r['esco_label']
            score_str = f"{r['score_final']:.3f}" if r['score_final'] is not None else 'N/A'
            cov_str = f"{r['coverage']:.3f}" if r['coverage'] is not None else 'N/A'
            print(f"| {r['id_oferta']} | {titulo_short} | {esco_short} | {r['isco_nivel1']} | {score_str} | {cov_str} | |")

    conn.close()

if __name__ == '__main__':
    main()
