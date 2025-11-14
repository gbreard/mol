# -*- coding: utf-8 -*-
"""Analizar errores en el matching"""
import pandas as pd

df = pd.read_csv(
    r"D:\OEDE\Webscrapping\03_esco_matching\data\matching_manual_claude_20251028_202311.csv",
    encoding='utf-8'
)

print("\n" + "=" * 100)
print("ERRORES GRAVES DETECTADOS")
print("=" * 100)

# Error 1: Chofer avícola → Demostrador de promociones
print("\n[ERROR 1] Chofer avícola matcheado INCORRECTAMENTE:")
error1 = df[df['titulo'].str.contains('Avicola', case=False, na=False)]
for idx, row in error1.iterrows():
    print(f"  Titulo:       {row['titulo']}")
    print(f"  Claude ESCO:  {row['claude_esco_label']} (ISCO {row['claude_isco_code']})")
    print(f"  DEBERIA SER:  Conductor de camión/reparto")
    print(f"  Patron usado: {row['claude_patron']}")
    break

# Error 2: Asistente → Responsable
print("\n[ERROR 2] Asistente → Responsable (rango jerárquico INCORRECTO):")
error2 = df[df['titulo'].str.contains('Asistente.*Marketing', case=False, na=False)]
for idx, row in error2.iterrows():
    print(f"  Titulo:       {row['titulo']}")
    print(f"  Claude ESCO:  {row['claude_esco_label']} (ISCO {row['claude_isco_code']})")
    print(f"  ISCO 1221 = DIRECTOR/GERENTE (nivel jerárquico alto)")
    print(f"  DEBERIA SER:  Asistente/Ayudante (ISCO 4xxx o 3xxx)")
    break

# Revisar especificidad ISCO
print("\n" + "=" * 100)
print("PROBLEMA DE ESPECIFICIDAD ISCO")
print("=" * 100)
print("\nClaude usa ISCO hasta 4 dígitos")
print("LLM/Fuzzy original usa ISCO con decimales (más específico)")
print("\nEjemplos:")

ejemplos = df.head(10)
for idx, row in ejemplos.iterrows():
    claude_isco = str(row['claude_isco_code'])
    fuzzy_isco = str(row['fuzzy_isco_code'])

    if '.' in fuzzy_isco:
        print(f"\n  Titulo: {row['titulo'][:60]}")
        print(f"    Claude ISCO: {claude_isco} (genérico)")
        print(f"    Fuzzy ISCO:  {fuzzy_isco} (específico)")

print("\n" + "=" * 100)
