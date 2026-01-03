#!/usr/bin/env python3
"""
Comparar versiones de Gold Set Excel
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent.parent

nuevo_path = project_root / "docs" / "MOL_Gold_Set_49_Ofertas_Validacion (15-12).xlsx"
anterior_path = project_root / "exports" / "MOL_Gold_Set_49_Validacion_POST_FIX.xlsx"

print("=" * 70)
print("COMPARACION GOLD SET EXCEL")
print("=" * 70)

# Cargar archivos
nuevo = pd.ExcelFile(nuevo_path)
anterior = pd.ExcelFile(anterior_path)

print(f"\n[ARCHIVO NUEVO] {nuevo_path.name}")
print(f"  Hojas: {len(nuevo.sheet_names)}")
for sheet in nuevo.sheet_names:
    df = pd.read_excel(nuevo, sheet_name=sheet)
    print(f"    - {sheet}: {len(df)} filas x {len(df.columns)} cols")

print(f"\n[ARCHIVO ANTERIOR] {anterior_path.name}")
print(f"  Hojas: {len(anterior.sheet_names)}")
for sheet in anterior.sheet_names:
    df = pd.read_excel(anterior, sheet_name=sheet)
    print(f"    - {sheet}: {len(df)} filas x {len(df.columns)} cols")

# Comparar hojas de ofertas
print("\n" + "=" * 70)
print("COMPARACION OFERTAS ORIGINALES")
print("=" * 70)

df_nuevo = pd.read_excel(nuevo, sheet_name='01_Ofertas_Originales')
df_anterior = pd.read_excel(anterior, sheet_name='1_Ofertas_Originales')

print(f"\nColumnas NUEVO ({len(df_nuevo.columns)}):")
for col in df_nuevo.columns:
    print(f"  - {col}")

print(f"\nColumnas ANTERIOR ({len(df_anterior.columns)}):")
for col in df_anterior.columns:
    print(f"  - {col}")

# Comparar NLP Extraccion
print("\n" + "=" * 70)
print("COMPARACION NLP EXTRACCION")
print("=" * 70)

df_nlp_nuevo = pd.read_excel(nuevo, sheet_name='02_NLP_Extraccion')
df_nlp_anterior = pd.read_excel(anterior, sheet_name='2_NLP_Extraccion')

print(f"\nColumnas NUEVO ({len(df_nlp_nuevo.columns)}):")
cols_nuevo = set(df_nlp_nuevo.columns)

print(f"\nColumnas ANTERIOR ({len(df_nlp_anterior.columns)}):")
cols_anterior = set(df_nlp_anterior.columns)

# Columnas nuevas
cols_nuevas = cols_nuevo - cols_anterior
if cols_nuevas:
    print(f"\n[NUEVAS COLUMNAS] ({len(cols_nuevas)}):")
    for col in sorted(cols_nuevas):
        print(f"  + {col}")

# Ver hoja de Resumen
print("\n" + "=" * 70)
print("HOJA 04_Resumen")
print("=" * 70)

df_resumen = pd.read_excel(nuevo, sheet_name='04_Resumen')
print(df_resumen.to_string(index=False))

# Ver hoja de Feedback NLP
print("\n" + "=" * 70)
print("HOJA 05_Feedback_NLP (primeras 10 filas)")
print("=" * 70)

df_feedback = pd.read_excel(nuevo, sheet_name='05_Feedback_NLP')
print(df_feedback.head(10).to_string(index=False))

# Ver hoja Comparacion si existe
print("\n" + "=" * 70)
print("HOJA Comparacion")
print("=" * 70)

try:
    df_comp = pd.read_excel(nuevo, sheet_name='Comparación')
    print(df_comp.to_string(index=False))
except:
    # Probar con encoding diferente
    for sheet in nuevo.sheet_names:
        if 'compar' in sheet.lower():
            df_comp = pd.read_excel(nuevo, sheet_name=sheet)
            print(df_comp.to_string(index=False))
            break

# Resumen de hojas nuevas
print("\n" + "=" * 70)
print("HOJAS NUEVAS (no en version anterior)")
print("=" * 70)

hojas_nuevas = [
    '03_Matching_ESCO',
    '05_Feedback_NLP',
    '06_Resumen_Errores',
    '07_Reglas_Mejora',
    '08_Feedback_Matching',
    '09_Feedback_Skills_NLP',
    '10_Matching_Skills_ESCO',
    '11_Ofertas_Skills_ESCO',
    '12_Diccionario_ESCO',
    '13_Dashboard',
    '14_Eval_Tareas_NLP',
    '15_Skills_Desde_Tareas',
    '16_Skills_Impl_Tareas_ESCO',
    '17_Skills_Completas_ESCO'
]

for hoja in hojas_nuevas:
    if hoja in nuevo.sheet_names:
        df = pd.read_excel(nuevo, sheet_name=hoja)
        print(f"  {hoja}: {len(df)} filas")
