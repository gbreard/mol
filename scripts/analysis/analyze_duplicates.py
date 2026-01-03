"""
Analiza el patrón de duplicados en el CSV del scraping
"""

import pandas as pd

df = pd.read_csv('01_sources/bumeran/data/raw/bumeran_completo_20251030_223956.csv')

print("="*70)
print("ANALISIS DE DUPLICADOS EN CSV")
print("="*70)

print(f"\nTotal filas: {len(df):,}")
print(f"IDs unicos: {df['id_oferta'].nunique()}")
print(f"Duplicados: {len(df) - df['id_oferta'].nunique():,}")

print("\n" + "-"*70)
print("TOP 10 IDs MAS REPETIDOS:")
print("-"*70)

vc = df['id_oferta'].value_counts().head(10)
for id_of, count in vc.items():
    print(f"  ID {id_of}: aparece {count:,} veces")

print("\n" + "-"*70)
print("PATRON DE REPETICION:")
print("-"*70)

# Ver si todos los IDs aparecen la misma cantidad de veces
repeticiones_unicas = df['id_oferta'].value_counts().unique()
print(f"\nCantidades de repeticiones diferentes: {len(repeticiones_unicas)}")
print(f"Valores: {sorted(repeticiones_unicas)}")

if len(repeticiones_unicas) == 1:
    count = repeticiones_unicas[0]
    print(f"\n[!!!] CADA ID aparece EXACTAMENTE {count} veces")
    print(f"      Esto indica que las mismas {df['id_oferta'].nunique()} ofertas")
    print(f"      se repitieron en TODAS las {count} paginas scrapeadas")
else:
    print(f"\nLas repeticiones varian entre {min(repeticiones_unicas)} y {max(repeticiones_unicas)}")

print("\n" + "="*70)
