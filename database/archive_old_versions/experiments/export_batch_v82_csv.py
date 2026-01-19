#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exporta batch de ofertas procesadas con v8.2 a CSV con todas las variables.
"""

import sqlite3
import struct
import csv
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Excluir Gold Set 19 (ya se analizó aparte)
GOLD_SET_IDS = [
    "1118026700", "1118026729", "1118027188", "1118027243", "1118027261",
    "1118027276", "1118027662", "1118027834", "1118027941", "1118028027",
    "1118028038", "1118028201", "1118028376", "1118028657", "1118028681",
    "1118028828", "1118028833", "1118028887", "1118028891"
]


def parse_score(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 8:
            return struct.unpack('d', value)[0]
        elif len(value) == 4:
            return struct.unpack('f', value)[0]
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders_exclude = ','.join(['?'] * len(GOLD_SET_IDS))

    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            o.empresa,
            o.localizacion,
            o.modalidad_trabajo,
            o.tipo_trabajo,
            o.id_area,
            o.id_subarea,
            m.esco_occupation_uri,
            m.esco_occupation_label,
            m.isco_code,
            m.isco_nivel1,
            m.isco_nivel2,
            m.score_titulo,
            m.score_skills,
            m.score_descripcion,
            m.score_final_ponderado,
            m.skills_cobertura,
            m.skills_matcheados_esco,
            m.skills_demandados_total,
            m.match_confirmado,
            m.requiere_revision,
            m.matching_version,
            m.matching_timestamp
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta NOT IN ({placeholders_exclude})
        LIMIT 200
    ''', GOLD_SET_IDS)

    rows = cursor.fetchall()
    print(f"Ofertas encontradas: {len(rows)}")

    # Nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent / f'batch_v82_{timestamp}.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'id_oferta', 'titulo', 'empresa', 'localizacion', 'modalidad_trabajo',
            'tipo_trabajo', 'id_area', 'id_subarea', 'esco_occupation_uri',
            'esco_occupation_label', 'isco_code', 'isco_nivel1', 'isco_nivel2',
            'score_titulo', 'score_skills', 'score_descripcion', 'score_final_ponderado',
            'skills_cobertura', 'skills_matcheados_esco', 'skills_demandados_total',
            'match_confirmado', 'requiere_revision', 'matching_version',
            'matching_timestamp'
        ])

        for row in rows:
            writer.writerow([
                row['id_oferta'],
                row['titulo'],
                row['empresa'],
                row['localizacion'],
                row['modalidad_trabajo'],
                row['tipo_trabajo'],
                row['id_area'],
                row['id_subarea'],
                row['esco_occupation_uri'],
                row['esco_occupation_label'],
                row['isco_code'],
                row['isco_nivel1'],
                row['isco_nivel2'],
                parse_score(row['score_titulo']),
                parse_score(row['score_skills']),
                parse_score(row['score_descripcion']),
                parse_score(row['score_final_ponderado']),
                parse_score(row['skills_cobertura']),
                row['skills_matcheados_esco'],
                row['skills_demandados_total'],
                row['match_confirmado'],
                row['requiere_revision'],
                row['matching_version'],
                row['matching_timestamp']
            ])

    conn.close()
    print(f"\n[OK] Exportado a: {output_file}")
    print(f"     {len(rows)} registros")


if __name__ == '__main__':
    main()
