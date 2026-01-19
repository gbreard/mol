# -*- coding: utf-8 -*-
"""
Análisis de gap entre NLP v11 y Matching v2.1.1
"""
import pandas as pd
import sqlite3
import sys
import io

# Forzar UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Leer Excel de validación
print('=' * 70)
print('1. EXCEL VALIDACION GOLD SET (15-12)')
print('=' * 70)

df = pd.read_excel(r'D:\OEDE\Webscrapping\docs\MOL_Gold_Set_49_Ofertas_Validacion (15-12).xlsx')
print(f'Filas: {len(df)}')
print(f'\nColumnas ({len(df.columns)}):')
for i, col in enumerate(df.columns):
    print(f'  {i+1}. {col}')

# 2. Buscar columnas de tareas
print('\n' + '=' * 70)
print('2. COLUMNAS RELACIONADAS CON TAREAS')
print('=' * 70)

tareas_cols = [c for c in df.columns if 'tarea' in c.lower()]
print(f'Columnas con "tarea": {tareas_cols}')

# 3. Verificar estructura ofertas_nlp
print('\n' + '=' * 70)
print('3. COLUMNAS OFERTAS_NLP EN BD')
print('=' * 70)

conn = sqlite3.connect(r'D:\OEDE\Webscrapping\database\bumeran_scraping.db')
cur = conn.execute('PRAGMA table_info(ofertas_nlp)')
cols_bd = [row[1] for row in cur.fetchall()]
print(f'Total columnas en BD: {len(cols_bd)}')

# Columnas de tareas en BD
tareas_bd = [c for c in cols_bd if 'tarea' in c.lower()]
print(f'\nColumnas de tareas en BD: {tareas_bd}')

# 4. Comparar NLP v11 schema vs Matching requirements
print('\n' + '=' * 70)
print('4. COMPARACION NLP v11 vs MATCHING v2.1.1')
print('=' * 70)

# Variables que usa el matching (del código)
matching_vars = [
    'titulo_limpio',
    'area_funcional',
    'nivel_seniority',
    'tiene_gente_cargo',
    'sector_empresa',
    'skills_tecnicas_list',
    'tareas_explicitas',
    'tareas_inferidas',  # <- Importante!
    'tecnologias_list',
    'mision_rol',
    'tipo_oferta',
    'calidad_texto',
    'conocimientos_especificos_list'
]

# Variables que entrega NLP v11 schema
nlp_v11_vars = [
    'titulo_limpio',  # titulo_ocupacion en schema pero titulo_limpio en BD
    'provincia',
    'localidad',
    'sector_empresa',
    'tareas_explicitas',
    'skills_tecnicas_list',
    'soft_skills_list',
    'tecnologias_list',
    'herramientas_list',
    'experiencia_min_anios',
    'experiencia_max_anios',
    'nivel_educativo',
    'titulo_requerido',
    'requerimiento_edad',
    'requerimiento_sexo'
]

print('\nVariables que MATCHING necesita:')
for v in matching_vars:
    en_bd = 'SI' if v in cols_bd else 'NO'
    en_v11 = 'SI' if v in nlp_v11_vars else 'NO'
    status = 'OK' if en_bd == 'SI' else 'FALTA'
    print(f'  {v:35} BD:{en_bd}  v11:{en_v11}  [{status}]')

# 5. Verificar ofertas v11 específicamente
print('\n' + '=' * 70)
print('5. DATOS EN OFERTAS v11 (muestra)')
print('=' * 70)

cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, area_funcional, nivel_seniority,
           tiene_gente_cargo, sector_empresa, tareas_explicitas, tareas_inferidas
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
    LIMIT 5
''')
for row in cur:
    print(f'\nID: {row[0]}')
    print(f'  titulo_limpio: {row[1]}')
    print(f'  area_funcional: {row[2]}')
    print(f'  nivel_seniority: {row[3]}')
    print(f'  tiene_gente_cargo: {row[4]}')
    print(f'  sector_empresa: {row[5]}')
    print(f'  tareas_explicitas: {str(row[6])[:80] if row[6] else None}...')
    print(f'  tareas_inferidas: {str(row[7])[:80] if row[7] else None}...')

conn.close()

# 6. Revisar contenido del Excel para tareas
print('\n' + '=' * 70)
print('6. CONTENIDO EXCEL - TAREAS')
print('=' * 70)

if tareas_cols:
    for col in tareas_cols:
        print(f'\nColumna: {col}')
        print(f'  Valores no nulos: {df[col].notna().sum()}/{len(df)}')
        if df[col].notna().any():
            sample = df[col].dropna().iloc[0]
            print(f'  Ejemplo: {str(sample)[:100]}...')
