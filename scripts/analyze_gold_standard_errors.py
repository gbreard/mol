#!/usr/bin/env python3
"""
Analizar errores del Gold Standard Excel (15-12)
Para identificar qué campos fallan y cómo mejorarlos
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from pathlib import Path

excel_path = Path("D:/OEDE/Webscrapping/docs/MOL_Gold_Set_49_Ofertas_Validacion (15-12).xlsx")

print("=" * 70)
print("ANALISIS DE ERRORES - GOLD STANDARD (15-12)")
print("=" * 70)

# 1. Feedback NLP - Errores identificados
print("\n[1] FEEDBACK NLP - ERRORES IDENTIFICADOS")
print("-" * 70)
df_feedback = pd.read_excel(excel_path, sheet_name='05_Feedback_NLP')
print(f"Total errores documentados: {len(df_feedback)}")
print("\nColumnas disponibles:")
for col in df_feedback.columns:
    print(f"  - {col}")

print("\nErrores por campo:")
if 'Campo' in df_feedback.columns:
    errores_por_campo = df_feedback['Campo'].value_counts()
    for campo, count in errores_por_campo.items():
        print(f"  {campo}: {count} errores")

print("\nErrores por tipo:")
if 'Tipo Error' in df_feedback.columns:
    errores_por_tipo = df_feedback['Tipo Error'].value_counts()
    for tipo, count in errores_por_tipo.items():
        print(f"  {tipo}: {count}")

# 2. Resumen de errores
print("\n\n[2] RESUMEN DE ERRORES")
print("-" * 70)
df_resumen = pd.read_excel(excel_path, sheet_name='06_Resumen_Errores')
print(df_resumen.to_string(index=False))

# 3. Reglas de mejora propuestas
print("\n\n[3] REGLAS DE MEJORA PROPUESTAS")
print("-" * 70)
df_reglas = pd.read_excel(excel_path, sheet_name='07_Reglas_Mejora')
print(f"Total reglas: {len(df_reglas)}")
print("\nColumnas:")
for col in df_reglas.columns:
    print(f"  - {col}")
print("\nPrimeras 15 reglas:")
print(df_reglas.head(15).to_string(index=False))

# 4. Feedback detallado - mostrar ejemplos
print("\n\n[4] EJEMPLOS DE ERRORES CON SUGERENCIAS")
print("-" * 70)
if 'Sugerencia para Prompt/Regex' in df_feedback.columns:
    for i, row in df_feedback.head(10).iterrows():
        print(f"\n--- Error {i+1} ---")
        print(f"ID: {row.get('ID', 'N/A')}")
        print(f"Campo: {row.get('Campo', 'N/A')}")
        print(f"Valor NLP: {row.get('Valor Actual NLP', 'N/A')}")
        print(f"Valor Esperado: {row.get('Valor Esperado', 'N/A')}")
        print(f"Tipo Error: {row.get('Tipo Error', 'N/A')}")
        sugerencia = row.get('Sugerencia para Prompt/Regex', 'N/A')
        if len(str(sugerencia)) > 200:
            sugerencia = str(sugerencia)[:200] + "..."
        print(f"Sugerencia: {sugerencia}")

# 5. Análisis de cobertura
print("\n\n[5] METRICAS DE COBERTURA (del Resumen)")
print("-" * 70)
df_resumen_gral = pd.read_excel(excel_path, sheet_name='04_Resumen')
print(df_resumen_gral.to_string(index=False))
