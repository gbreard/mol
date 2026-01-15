#!/usr/bin/env python3
"""
Analisis de cobertura por campo para llegar al 95%
"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

print('=' * 70)
print('ANALISIS DETALLADO POR CAMPO - Estado Actual')
print('=' * 70)
print()

# Análisis campo por campo
campos = [
    ('experiencia_min_anios', 'Experiencia'),
    ('nivel_educativo', 'Educacion'),
    ('idioma_principal', 'Idioma'),
    ('jornada_laboral', 'Jornada'),
    ('skills_tecnicas_list', 'Skills Tecnicas'),
    ('soft_skills_list', 'Soft Skills'),
    ('salario_min', 'Salario')
]

print('CAMPO                    |  NULL   |  CON VALOR  |  % COBERTURA')
print('-' * 70)

resultados_campos = []

for campo_db, campo_nombre in campos:
    if 'list' in campo_db:
        cursor.execute(f'''
            SELECT
                SUM(CASE WHEN {campo_db} IS NULL OR {campo_db} = '[]' THEN 1 ELSE 0 END) as nulls,
                SUM(CASE WHEN {campo_db} IS NOT NULL AND {campo_db} != '[]' THEN 1 ELSE 0 END) as con_valor,
                COUNT(*) as total
            FROM ofertas_nlp
        ''')
    else:
        cursor.execute(f'''
            SELECT
                SUM(CASE WHEN {campo_db} IS NULL THEN 1 ELSE 0 END) as nulls,
                SUM(CASE WHEN {campo_db} IS NOT NULL THEN 1 ELSE 0 END) as con_valor,
                COUNT(*) as total
            FROM ofertas_nlp
        ''')

    nulls, con_valor, total = cursor.fetchone()
    pct_cobertura = (con_valor / total * 100) if total > 0 else 0

    print(f'{campo_nombre:24} |  {nulls:5,} |  {con_valor:6,}   |  {pct_cobertura:5.1f}%')
    resultados_campos.append((campo_nombre, pct_cobertura, 95 - pct_cobertura))

print()
print('=' * 70)
print('GAPS PARA LLEGAR AL 95%')
print('=' * 70)
print()

# Ordenar por gap descendente
resultados_campos.sort(key=lambda x: x[2], reverse=True)

print('CAMPO                    |  ACTUAL  |  META  |  GAP')
print('-' * 70)
for campo, pct_actual, gap in resultados_campos:
    print(f'{campo:24} |  {pct_actual:5.1f}%  |  95.0% |  {gap:+5.1f}%')

print()
print('=' * 70)
print('ESTRATEGIA PARA LLEGAR AL 95%')
print('=' * 70)
print()

# Calcular cuántas ofertas necesitamos mejorar por campo
cursor.execute('SELECT COUNT(*) FROM ofertas_nlp')
total_ofertas = cursor.fetchone()[0]

print(f'Total ofertas: {total_ofertas:,}')
print()
print('Ofertas adicionales que necesitan valor:')
print()

for campo_db, campo_nombre in campos:
    if 'list' in campo_db:
        cursor.execute(f'''
            SELECT SUM(CASE WHEN {campo_db} IS NOT NULL AND {campo_db} != '[]' THEN 1 ELSE 0 END)
            FROM ofertas_nlp
        ''')
    else:
        cursor.execute(f'''
            SELECT SUM(CASE WHEN {campo_db} IS NOT NULL THEN 1 ELSE 0 END)
            FROM ofertas_nlp
        ''')

    con_valor = cursor.fetchone()[0] or 0
    necesarias_95 = int(total_ofertas * 0.95)
    gap_ofertas = necesarias_95 - con_valor

    if gap_ofertas > 0:
        print(f'{campo_nombre:24}: {gap_ofertas:5,} ofertas mas')

conn.close()
