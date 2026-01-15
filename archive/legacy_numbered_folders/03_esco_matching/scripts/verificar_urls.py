# -*- coding: utf-8 -*-
"""Verificar columnas de URLs disponibles"""
import pandas as pd

df = pd.read_csv(
    r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv",
    encoding='utf-8',
    low_memory=False
)

# Buscar columnas con URLs
url_cols = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'href' in col.lower()]

print("=" * 80)
print("COLUMNAS CON URLs EN EL DATASET")
print("=" * 80)

if url_cols:
    print(f"\nEncontradas {len(url_cols)} columnas:\n")
    for col in url_cols:
        print(f"  - {col}")

    print("\n" + "=" * 80)
    print("EJEMPLOS DE DATOS")
    print("=" * 80)

    for col in url_cols[:3]:  # Primeras 3 columnas
        print(f"\n{col}:")
        ejemplos = df[col].dropna().head(3).tolist()
        for ej in ejemplos:
            print(f"  {ej}")
else:
    print("\nNo se encontraron columnas con URLs")

    # Buscar otras columnas que puedan contener identificadores
    print("\nBuscando columnas con 'id' o 'source'...")
    id_cols = [col for col in df.columns if 'id' in col.lower() or 'source' in col.lower()]

    for col in id_cols[:5]:
        print(f"\n{col}:")
        print(f"  {df[col].head(3).tolist()}")

print("\n" + "=" * 80)
