# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path

# Cargar datos
output_dir = Path(r"D:\OEDE\Webscrapping\data\processed")
archivos = list(output_dir.glob("zonajobs_esco_enriquecida_*.csv"))
ultimo = max(archivos, key=lambda x: x.stat().st_mtime)

print(f"Cargando: {ultimo.name}\n")
df = pd.read_csv(ultimo)

print("=" * 80)
print("MUESTRA DE RESULTADOS - OFERTAS ENRIQUECIDAS CON ESCO")
print("=" * 80)

# Mostrar 5 ofertas clasificadas
clasificadas = df[df['clasificada'] == True].head(5)

for idx, row in clasificadas.iterrows():
    print(f"\n{idx+1}. OFERTA ORIGINAL:")
    print(f"   Título: {row['titulo_original']}")
    print(f"   Empresa: {row['empresa']}")
    print(f"   Modalidad: {row['modalidad_trabajo']}")

    print(f"\n   MATCH ESCO:")
    print(f"   Ocupación: {row['esco_match_1_label']}")
    print(f"   ISCO 4D: {row['esco_match_1_isco_4d']}")
    print(f"   ISCO 2D: {row['esco_match_1_isco_2d']}")
    print(f"   Similitud: {row['esco_match_1_similitud']:.3f}")

    if pd.notna(row['esco_match_2_label']):
        print(f"\n   MATCHES ALTERNATIVOS:")
        print(f"   2. {row['esco_match_2_label']} (sim: {row['esco_match_2_similitud']:.3f})")
        if pd.notna(row['esco_match_3_label']):
            print(f"   3. {row['esco_match_3_label']} (sim: {row['esco_match_3_similitud']:.3f})")

    print(f"\n   SKILLS ESENCIALES ({int(row['skills_esenciales_count'])} total):")
    if pd.notna(row['skills_esenciales_top5']):
        skills = row['skills_esenciales_top5'].split('; ')
        for skill in skills:
            print(f"   • {skill}")

    if row['skills_opcionales_count'] > 0:
        print(f"\n   SKILLS OPCIONALES ({int(row['skills_opcionales_count'])} total):")
        if pd.notna(row['skills_opcionales_top5']):
            skills_opc = row['skills_opcionales_top5'].split('; ')
            for skill in skills_opc[:3]:
                print(f"   • {skill}")

    print("\n" + "-" * 80)

print("\n\nESTADÍSTICAS FINALES:")
print(f"Total ofertas procesadas: {len(df)}")
print(f"Clasificadas: {df['clasificada'].sum()} ({df['clasificada'].sum()/len(df)*100:.1f}%)")
print(f"Sin clasificar: {(~df['clasificada']).sum()}")
print(f"\nPromedio de similitud: {df[df['clasificada']]['esco_match_1_similitud'].mean():.3f}")
