# -*- coding: utf-8 -*-
"""
Análisis de GAP entre Skills Parseadas (LLM) vs Skills ESCO Esperadas
======================================================================

Compara las skills que las ofertas mencionan vs las skills que ESCO
dice que deberían tener esas ocupaciones.
"""
import pandas as pd
import json
from collections import Counter

# Cargar dataset enriquecido
df = pd.read_csv(
    r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_enriquecidas_esco_skills_20251028_205036.csv",
    encoding='utf-8',
    low_memory=False
)

print("=" * 100)
print("ANALISIS GAP: SKILLS PARSEADAS (LLM) vs SKILLS ESCO ESPERADAS")
print("=" * 100)

print(f"\n[INFO] Dataset: {len(df)} ofertas")

# === 1. Estadísticas generales ===
print("\n[1] COBERTURA DE SKILLS")
print("=" * 100)

print("\n  Skills parseadas del LLM:")
print(f"    Con soft_skills:          {df['soft_skills'].notna().sum():>3} ({df['soft_skills'].notna().sum()/len(df)*100:>5.1f}%)")
print(f"    Con skills_tecnicas:      {df['skills_tecnicas'].notna().sum():>3} ({df['skills_tecnicas'].notna().sum()/len(df)*100:>5.1f}%)")

print("\n  Skills ESCO esperadas (por ISCO):")
print(f"    Con skills esenciales:    {(df['esco_skills_esenciales_count'] > 0).sum():>3} ({(df['esco_skills_esenciales_count'] > 0).sum()/len(df)*100:>5.1f}%)")
print(f"    Con skills opcionales:    {(df['esco_skills_opcionales_count'] > 0).sum():>3} ({(df['esco_skills_opcionales_count'] > 0).sum()/len(df)*100:>5.1f}%)")

# === 2. Distribución de cantidad ===
print("\n[2] CANTIDAD DE SKILLS")
print("=" * 100)

print("\n  Skills parseadas por oferta:")
print(f"    Soft skills promedio:     {df['soft_skills_count'].mean():>5.1f}")
print(f"    Skills tecnicas promedio: {df['skills_tecnicas_count'].mean():>5.1f}")
print(f"    Total promedio:           {(df['soft_skills_count'].fillna(0) + df['skills_tecnicas_count'].fillna(0)).mean():>5.1f}")

print("\n  Skills ESCO por ocupacion:")
print(f"    Esenciales promedio:      {df['esco_skills_esenciales_count'].mean():>5.1f}")
print(f"    Opcionales promedio:      {df['esco_skills_opcionales_count'].mean():>5.1f}")
print(f"    Total promedio:           {df['esco_skills_total_count'].mean():>5.1f}")

# === 3. Top Skills Parseadas ===
print("\n[3] TOP 20 SOFT SKILLS MAS DEMANDADAS (parseadas del LLM)")
print("=" * 100)

all_soft = []
for skills in df['soft_skills'].dropna():
    try:
        skills_list = eval(skills) if isinstance(skills, str) else skills
        if isinstance(skills_list, list):
            all_soft.extend(skills_list)
    except:
        pass

if all_soft:
    soft_counter = Counter(all_soft)
    for i, (skill, count) in enumerate(soft_counter.most_common(20), 1):
        pct = count / len(df) * 100
        print(f"  {i:2}. {skill:40} {count:>3} ofertas ({pct:>5.1f}%)")
else:
    print("  No se encontraron soft skills parseadas")

# === 4. Top Skills ESCO Esenciales ===
print("\n[4] TOP 20 SKILLS ESCO ESENCIALES MAS FRECUENTES")
print("=" * 100)

all_esco_esenciales = []
for skills in df['esco_skills_esenciales'].dropna():
    try:
        skills_list = eval(skills) if isinstance(skills, str) else skills
        if isinstance(skills_list, list):
            all_esco_esenciales.extend(skills_list)
    except:
        pass

if all_esco_esenciales:
    esco_counter = Counter(all_esco_esenciales)
    for i, (skill, count) in enumerate(esco_counter.most_common(20), 1):
        pct = count / len(df) * 100
        print(f"  {i:2}. {skill:50} {count:>3} ocupaciones ({pct:>5.1f}%)")
else:
    print("  No se encontraron skills ESCO")

# === 5. Ejemplos de comparación ===
print("\n[5] EJEMPLOS DE COMPARACION (3 casos)")
print("=" * 100)

# Filtrar ofertas con datos completos
df_completos = df[
    df['soft_skills'].notna() &
    (df['esco_skills_esenciales_count'] > 0)
].head(3)

for idx, row in df_completos.iterrows():
    print(f"\n  CASO {idx+1}:")
    print(f"  Titulo:       {row['titulo']}")
    print(f"  ESCO:         {row['claude_esco_label']}")
    print(f"  ISCO:         {row['claude_isco_code']}")

    # Skills parseadas
    try:
        soft_parseadas = eval(row['soft_skills']) if isinstance(row['soft_skills'], str) else row['soft_skills']
        print(f"\n    Skills parseadas ({len(soft_parseadas)}):")
        for skill in soft_parseadas[:5]:
            print(f"      - {skill}")
        if len(soft_parseadas) > 5:
            print(f"      ... y {len(soft_parseadas)-5} mas")
    except:
        print(f"\n    Skills parseadas: Error al parsear")

    # Skills ESCO esenciales
    try:
        skills_esco = eval(row['esco_skills_esenciales']) if isinstance(row['esco_skills_esenciales'], str) else row['esco_skills_esenciales']
        print(f"\n    Skills ESCO esenciales ({len(skills_esco)}):")
        for skill in skills_esco[:5]:
            print(f"      - {skill}")
        if len(skills_esco) > 5:
            print(f"      ... y {len(skills_esco)-5} mas")
    except:
        print(f"\n    Skills ESCO: Error al parsear")

# === 6. Análisis de completitud ===
print("\n" + "=" * 100)
print("[6] ANALISIS DE COMPLETITUD")
print("=" * 100)

# Ofertas con ambos tipos de skills
ofertas_completas = df[
    df['soft_skills'].notna() &
    (df['esco_skills_esenciales_count'] > 0)
]

print(f"\n  Ofertas con skills parseadas Y skills ESCO:")
print(f"    Total:                    {len(ofertas_completas)} ({len(ofertas_completas)/len(df)*100:.1f}%)")

print(f"\n  Ofertas con solo skills parseadas:")
solo_parseadas = df[df['soft_skills'].notna() & (df['esco_skills_esenciales_count'] == 0)]
print(f"    Total:                    {len(solo_parseadas)} ({len(solo_parseadas)/len(df)*100:.1f}%)")

print(f"\n  Ofertas con solo skills ESCO:")
solo_esco = df[df['soft_skills'].isna() & (df['esco_skills_esenciales_count'] > 0)]
print(f"    Total:                    {len(solo_esco)} ({len(solo_esco)/len(df)*100:.1f}%)")

print(f"\n  Ofertas sin ninguna skill:")
sin_skills = df[df['soft_skills'].isna() & (df['esco_skills_esenciales_count'] == 0)]
print(f"    Total:                    {len(sin_skills)} ({len(sin_skills)/len(df)*100:.1f}%)")

print("\n" + "=" * 100)
print("[COMPLETADO]")
print("=" * 100)
