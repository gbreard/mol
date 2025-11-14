#!/usr/bin/env python3
"""
Analiza la calidad del parseo NLP de ofertas
Identifica patrones en ofertas bien/mal parseadas
"""

import sqlite3
import json
from collections import Counter

def analizar_calidad():
    conn = sqlite3.connect('bumeran_scraping.db')
    cursor = conn.cursor()

    print('=' * 70)
    print('ANALISIS DE CALIDAD DE PARSEO NLP')
    print('=' * 70)

    # Calcular score de calidad por oferta
    cursor.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            SUBSTR(o.descripcion, 1, 200) as desc_preview,
            LENGTH(o.descripcion) as desc_length,
            DATE(o.fecha_publicacion_datetime) as fecha,
            CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END as tiene_exp,
            CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END as tiene_edu,
            CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END as tiene_soft,
            CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END as tiene_tec,
            CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END as tiene_idioma,
            CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END as tiene_salario,
            CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END as tiene_jornada,
            o.descripcion
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.descripcion IS NOT NULL
    ''')

    rows = cursor.fetchall()

    print(f'\nTotal ofertas analizadas: {len(rows):,}\n')

    # Calcular score de calidad (suma de campos parseados)
    calidad_por_oferta = []
    for row in rows:
        score = sum(row[5:12])  # Suma de campos booleanos
        calidad_por_oferta.append({
            'id': row[0],
            'titulo': row[1],
            'preview': row[2],
            'length': row[3],
            'fecha': row[4],
            'score': score,
            'descripcion': row[12]
        })

    # Ordenar por score
    calidad_por_oferta.sort(key=lambda x: x['score'])

    # Top 5 peor parseadas
    print('TOP 5 OFERTAS CON PARSEO MAS POBRE (score mas bajo):')
    print('=' * 70)
    for i, oferta in enumerate(calidad_por_oferta[:5], 1):
        print(f'\n{i}. ID: {oferta["id"]} | Score: {oferta["score"]}/7')
        print(f'   Titulo: {oferta["titulo"][:60]}...')
        print(f'   Fecha: {oferta["fecha"]}')
        print(f'   Longitud descripcion: {oferta["length"]} chars')
        print(f'   Descripcion preview:')
        print(f'   "{oferta["preview"]}..."')

    # Top 5 mejor parseadas
    print('\n' + '=' * 70)
    print('TOP 5 OFERTAS CON MEJOR PARSEO (score mas alto):')
    print('=' * 70)
    for i, oferta in enumerate(calidad_por_oferta[-5:], 1):
        print(f'\n{i}. ID: {oferta["id"]} | Score: {oferta["score"]}/7')
        print(f'   Titulo: {oferta["titulo"][:60]}...')
        print(f'   Fecha: {oferta["fecha"]}')
        print(f'   Longitud descripcion: {oferta["length"]} chars')

    # Distribución de scores
    print('\n' + '=' * 70)
    print('DISTRIBUCION DE SCORES DE CALIDAD:')
    print('=' * 70)
    score_dist = Counter(o['score'] for o in calidad_por_oferta)

    for score in sorted(score_dist.keys()):
        count = score_dist[score]
        pct = (count / len(calidad_por_oferta)) * 100
        bar = '#' * int(pct / 2)
        print(f'Score {score}/7: {count:4,} ofertas ({pct:5.1f}%) {bar}')

    # Promedio de score
    avg_score = sum(o['score'] for o in calidad_por_oferta) / len(calidad_por_oferta)
    print(f'\nScore promedio: {avg_score:.2f}/7')

    # Análisis por longitud de descripción
    print('\n' + '=' * 70)
    print('CALIDAD DE PARSEO POR LONGITUD DE DESCRIPCION:')
    print('=' * 70)

    rangos = [
        (0, 500, 'Muy corta'),
        (500, 1000, 'Corta'),
        (1000, 2000, 'Media'),
        (2000, 5000, 'Larga'),
        (5000, 999999, 'Muy larga')
    ]

    for min_len, max_len, label in rangos:
        ofertas_rango = [o for o in calidad_por_oferta if min_len <= o['length'] < max_len]
        if ofertas_rango:
            avg = sum(o['score'] for o in ofertas_rango) / len(ofertas_rango)
            print(f'{label:15} ({min_len:5}-{max_len:5} chars): {len(ofertas_rango):4,} ofertas | Score promedio: {avg:.2f}/7')

    # Análisis por fecha
    print('\n' + '=' * 70)
    print('CALIDAD DE PARSEO POR FECHA:')
    print('=' * 70)

    from collections import defaultdict
    por_fecha = defaultdict(list)
    for o in calidad_por_oferta:
        if o['fecha']:
            por_fecha[o['fecha']].append(o['score'])

    fechas_ordenadas = sorted(por_fecha.keys())
    for fecha in fechas_ordenadas[:10]:  # Primeras 10 fechas
        scores = por_fecha[fecha]
        avg = sum(scores) / len(scores)
        print(f'{fecha}: {len(scores):3,} ofertas | Score promedio: {avg:.2f}/7')

    if len(fechas_ordenadas) > 10:
        print(f'... y {len(fechas_ordenadas) - 10} fechas mas')

    # Guardar ejemplo de descripción mal parseada para análisis
    print('\n' + '=' * 70)
    print('EJEMPLO DE DESCRIPCION MAL PARSEADA:')
    print('=' * 70)
    peor = calidad_por_oferta[0]
    print(f'\nID: {peor["id"]}')
    print(f'Titulo: {peor["titulo"]}')
    print(f'Score: {peor["score"]}/7')
    print(f'\nDescripcion completa:')
    print('-' * 70)
    print(peor['descripcion'][:500])
    print('...')

    conn.close()

if __name__ == '__main__':
    analizar_calidad()
