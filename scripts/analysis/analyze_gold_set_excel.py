# -*- coding: utf-8 -*-
"""
Analizar todas las pestañas del Gold Set Excel
"""
import pandas as pd
import sys
import io
import os

# Forzar UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

excel_path = r'D:\OEDE\Webscrapping\docs\MOL_Gold_Set_49_Ofertas_Validacion (15-12).xlsx'

# Pestañas clave a analizar en detalle
PESTANAS_CLAVE = [
    '02_NLP_Extraccion',
    '03_Matching_ESCO',
    '14_Eval_Tareas_NLP',
    '15_Skills_Desde_Tareas',
    '16_Skills_Impl_Tareas_ESCO',
    '17_Skills_Completas_ESCO',
    '07_Reglas_Mejora'
]

xl = pd.ExcelFile(excel_path)

print('=' * 80)
print('TODAS LAS PESTANAS')
print('=' * 80)
for i, sheet in enumerate(xl.sheet_names):
    print(f'{i+1:2}. {sheet}')
print()

# Analizar pestañas clave
for sheet_name in PESTANAS_CLAVE:
    if sheet_name not in xl.sheet_names:
        print(f'PESTANA NO ENCONTRADA: {sheet_name}')
        continue

    print('=' * 80)
    print(f'PESTANA: {sheet_name}')
    print('=' * 80)

    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    print(f'Filas: {len(df)}, Columnas: {len(df.columns)}')
    print()

    # Listar columnas
    print('Columnas:')
    for i, col in enumerate(df.columns):
        col_str = str(col).replace('\n', ' ')[:50]
        print(f'  {i+1:2}. {col_str}')
    print()

    # Mostrar valores únicos para columnas categóricas pequeñas
    for col in df.columns:
        if df[col].nunique() < 10 and df[col].notna().sum() > 0:
            print(f'  {col}: {list(df[col].dropna().unique()[:5])}')
    print()

# Análisis especial de tareas
print('=' * 80)
print('ANALISIS ESPECIAL: TAREAS IMPLICITAS')
print('=' * 80)

if '16_Skills_Impl_Tareas_ESCO' in xl.sheet_names:
    df_impl = pd.read_excel(excel_path, sheet_name='16_Skills_Impl_Tareas_ESCO')
    print(f'Pestaña 16_Skills_Impl_Tareas_ESCO:')
    print(f'  Filas: {len(df_impl)}')
    print(f'  Columnas: {list(df_impl.columns)}')
    print()
    if len(df_impl) > 0:
        print('Muestra (3 filas):')
        for i, row in df_impl.head(3).iterrows():
            print(f'\n  Fila {i+1}:')
            for col in df_impl.columns:
                val = str(row[col])[:80] if pd.notna(row[col]) else 'NULL'
                print(f'    {col}: {val}')

if '14_Eval_Tareas_NLP' in xl.sheet_names:
    df_tareas = pd.read_excel(excel_path, sheet_name='14_Eval_Tareas_NLP')
    print(f'\nPestaña 14_Eval_Tareas_NLP:')
    print(f'  Filas: {len(df_tareas)}')
    print(f'  Columnas: {list(df_tareas.columns)}')

# Análisis NLP Extraccion
print('=' * 80)
print('ANALISIS: NLP EXTRACCION')
print('=' * 80)

if '02_NLP_Extraccion' in xl.sheet_names:
    df_nlp = pd.read_excel(excel_path, sheet_name='02_NLP_Extraccion')
    print(f'Columnas en 02_NLP_Extraccion:')
    for col in df_nlp.columns:
        non_null = df_nlp[col].notna().sum()
        print(f'  {col}: {non_null}/{len(df_nlp)} no nulos')
