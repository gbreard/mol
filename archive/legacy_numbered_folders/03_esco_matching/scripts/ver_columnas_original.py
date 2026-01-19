# -*- coding: utf-8 -*-
"""Ver columnas del CSV original"""
import pandas as pd

df = pd.read_csv(
    r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv",
    encoding='utf-8',
    low_memory=False
)

print("=" * 100)
print(f"COLUMNAS DEL CSV ORIGINAL (Total: {len(df.columns)})")
print("=" * 100)

for i, col in enumerate(df.columns, 1):
    print(f"{i:2}. {col}")

print("\n" + "=" * 100)
print(f"Total filas: {len(df)}")
print("=" * 100)
