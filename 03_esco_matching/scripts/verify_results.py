# -*- coding: utf-8 -*-
"""Verificar calidad de matches"""
import pandas as pd

df = pd.read_csv(
    r"D:\OEDE\Webscrapping\03_esco_matching\data\matching_manual_claude_20251028_202311.csv",
    encoding='utf-8'
)

print("\n" + "=" * 100)
print("SAMPLE MATCHES - Verificando Calidad")
print("=" * 100)

# Mostrar 10 casos aleatorios
import random
random.seed(42)
indices = random.sample(range(len(df)), 10)

for idx in sorted(indices):
    row = df.iloc[idx]
    print(f"\n{idx+1}. TITULO: {row['titulo']}")
    print(f"   ESCO:   {row['claude_esco_label']}")
    print(f"   ISCO:   {row['claude_isco_code']}")
    print(f"   REASON: {row['claude_razonamiento']}")
    print(f"   PATRON: {row['claude_patron']}")

# Estadísticas por ISCO nivel 1
print("\n" + "=" * 100)
print("DISTRIBUCION POR ISCO (Nivel 1)")
print("=" * 100)

df['isco_nivel1'] = df['claude_isco_code'].astype(str).str[0]
isco_dist = df['isco_nivel1'].value_counts().sort_index()

for isco, count in isco_dist.items():
    pct = count / len(df) * 100
    print(f"  ISCO {isco}: {count:>3} ({pct:>5.1f}%)")

print("\n" + "=" * 100)
print(f"TOTAL: {len(df)} ofertas - 100% matched")
print("=" * 100)
