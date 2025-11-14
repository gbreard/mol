# -*- coding: utf-8 -*-
"""
Crear Tabla de Referencia: ISCO → Skills ESCO
==============================================

Agrupamos skills por código ISCO (más eficiente)
"""
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Rutas
DATASET_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_completas_con_matching_claude_20251028_204443.csv"
ESCO_OCUPACIONES_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"
ESCO_SKILLS_REL_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_skills_relaciones.json"
ESCO_SKILLS_INFO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_skills_info.json"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")

print("=" * 100)
print("CREAR TABLA ISCO -> SKILLS ESCO")
print("=" * 100)

# === 1. Cargar datos ===
print("\n[1/5] Cargando datos...")

df = pd.read_csv(DATASET_PATH, encoding='utf-8', low_memory=False)
print(f"  Dataset: {len(df)} ofertas")

with open(ESCO_OCUPACIONES_PATH, 'r', encoding='utf-8') as f:
    esco_ocupaciones = json.load(f)
print(f"  ESCO ocupaciones: {len(esco_ocupaciones)} ocupaciones")

with open(ESCO_SKILLS_REL_PATH, 'r', encoding='utf-8') as f:
    esco_ocu_skills = json.load(f)
print(f"  ESCO relaciones: {len(esco_ocu_skills)} ocupaciones con skills")

with open(ESCO_SKILLS_INFO_PATH, 'r', encoding='utf-8') as f:
    esco_skills_info = json.load(f)
print(f"  ESCO skills: {len(esco_skills_info)} skills")

# === 2. Identificar ISCOs únicos del dataset ===
print("\n[2/5] Identificando ISCOs unicos en dataset...")

# Extraer ISCO base (4 dígitos)
df['isco_4d'] = df['claude_isco_code'].astype(str).str.split('.').str[0]
iscos_unicos = df['isco_4d'].unique()

print(f"  ISCOs unicos en dataset: {len(iscos_unicos)}")
print(f"  Ejemplos: {list(iscos_unicos[:5])}")

# === 3. Construir diccionario ISCO → Skills ===
print("\n[3/5] Construyendo diccionario ISCO -> Skills...")

def get_skill_name(skill_id):
    """Obtiene nombre de skill (preferir ES, sino EN)"""
    if skill_id not in esco_skills_info:
        return None
    skill_data = esco_skills_info[skill_id]
    labels = skill_data.get('labels', {})
    return labels.get('es', labels.get('en', skill_id))

# Diccionario para acumular skills por ISCO
isco_skills_dict = defaultdict(lambda: {
    'esenciales': set(),
    'opcionales': set(),
    'ocupaciones_esco': []
})

# Iterar sobre todas las ocupaciones ESCO
for esco_id, esco_data in esco_ocupaciones.items():
    if not esco_data:
        continue

    # Obtener ISCO de esta ocupación
    isco_completo = esco_data.get('codigo_isco', '')
    isco_4d = str(isco_completo).split('.')[0] if isco_completo else None

    if not isco_4d:
        continue

    # Obtener skills de esta ocupación
    if esco_id in esco_ocu_skills:
        skills_rel = esco_ocu_skills[esco_id]

        # Skills esenciales
        for skill_id in skills_rel.get('skills_esenciales', []):
            skill_name = get_skill_name(skill_id)
            if skill_name:
                isco_skills_dict[isco_4d]['esenciales'].add(skill_name)

        # Skills opcionales
        for skill_id in skills_rel.get('skills_opcionales', []):
            skill_name = get_skill_name(skill_id)
            if skill_name:
                isco_skills_dict[isco_4d]['opcionales'].add(skill_name)

        # Guardar referencia a ocupación ESCO
        label = esco_data.get('label_es', esco_data.get('label_en', ''))
        if label:
            isco_skills_dict[isco_4d]['ocupaciones_esco'].append(label)

# Convertir sets a listas
for isco in isco_skills_dict:
    isco_skills_dict[isco]['esenciales'] = sorted(list(isco_skills_dict[isco]['esenciales']))
    isco_skills_dict[isco]['opcionales'] = sorted(list(isco_skills_dict[isco]['opcionales']))
    isco_skills_dict[isco]['ocupaciones_esco'] = list(set(isco_skills_dict[isco]['ocupaciones_esco']))

print(f"  ISCOs con skills: {len(isco_skills_dict)}")

# === 4. Crear DataFrame tabla ISCO-Skills ===
print("\n[4/5] Creando tabla ISCO-Skills...")

tabla_isco_skills = []

for isco, data in isco_skills_dict.items():
    tabla_isco_skills.append({
        'isco_code': isco,
        'esco_ocupaciones_count': len(data['ocupaciones_esco']),
        'esco_ocupaciones_ejemplos': data['ocupaciones_esco'][:5],  # Top 5
        'skills_esenciales': data['esenciales'],
        'skills_esenciales_count': len(data['esenciales']),
        'skills_opcionales': data['opcionales'],
        'skills_opcionales_count': len(data['opcionales']),
        'skills_total_count': len(data['esenciales']) + len(data['opcionales'])
    })

df_tabla_isco = pd.DataFrame(tabla_isco_skills)
df_tabla_isco = df_tabla_isco.sort_values('isco_code')

# Guardar tabla ISCO-Skills
tabla_isco_path = OUTPUT_DIR / "tabla_isco_skills_referencia.csv"
df_tabla_isco.to_csv(tabla_isco_path, index=False, encoding='utf-8')

print(f"  Tabla ISCO-Skills creada: {len(df_tabla_isco)} ISCOs")
print(f"  Guardada en: {tabla_isco_path}")

# Guardar también en JSON para fácil reutilización
tabla_isco_json_path = OUTPUT_DIR / "tabla_isco_skills_referencia.json"
with open(tabla_isco_json_path, 'w', encoding='utf-8') as f:
    json.dump(dict(isco_skills_dict), f, ensure_ascii=False, indent=2)

print(f"  Guardada también en JSON: {tabla_isco_json_path}")

# === 5. Enriquecer dataset con merge por ISCO ===
print("\n[5/5] Enriqueciendo dataset (merge por ISCO)...")

# Merge dataset con tabla ISCO
df_enriquecido = df.merge(
    df_tabla_isco[['isco_code', 'skills_esenciales', 'skills_esenciales_count',
                   'skills_opcionales', 'skills_opcionales_count', 'skills_total_count']],
    left_on='isco_4d',
    right_on='isco_code',
    how='left'
)

# Renombrar columnas para claridad
df_enriquecido.rename(columns={
    'skills_esenciales': 'esco_skills_esenciales',
    'skills_esenciales_count': 'esco_skills_esenciales_count',
    'skills_opcionales': 'esco_skills_opcionales',
    'skills_opcionales_count': 'esco_skills_opcionales_count',
    'skills_total_count': 'esco_skills_total_count'
}, inplace=True)

# Eliminar columna auxiliar
df_enriquecido.drop(columns=['isco_code', 'isco_4d'], inplace=True)

# Guardar dataset enriquecido
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dataset_enriquecido_path = OUTPUT_DIR / f"ofertas_enriquecidas_esco_skills_{timestamp}.csv"

df_enriquecido.to_csv(dataset_enriquecido_path, index=False, encoding='utf-8')

# === RESULTADOS ===
print("\n" + "=" * 100)
print("RESULTADOS")
print("=" * 100)

print(f"\n  [1] TABLA ISCO-SKILLS REFERENCIA")
print(f"      Total ISCOs:              {len(df_tabla_isco)}")
print(f"      Archivo:                  {tabla_isco_path}")

print(f"\n  [2] DATASET ENRIQUECIDO")
print(f"      Total ofertas:            {len(df_enriquecido)}")
print(f"      Total columnas:           {len(df_enriquecido.columns)}")
print(f"      Archivo:                  {dataset_enriquecido_path}")

print(f"\n  [3] ESTADISTICAS SKILLS ESCO")
print(f"      Ofertas con skills:       {df_enriquecido['esco_skills_total_count'].notna().sum()}/{len(df_enriquecido)}")

print(f"\n      Skills esenciales por ISCO:")
print(f"        Promedio:               {df_tabla_isco['skills_esenciales_count'].mean():.1f}")
print(f"        Mediana:                {df_tabla_isco['skills_esenciales_count'].median():.0f}")
print(f"        Max:                    {df_tabla_isco['skills_esenciales_count'].max():.0f}")

print(f"\n      Skills opcionales por ISCO:")
print(f"        Promedio:               {df_tabla_isco['skills_opcionales_count'].mean():.1f}")
print(f"        Mediana:                {df_tabla_isco['skills_opcionales_count'].median():.0f}")
print(f"        Max:                    {df_tabla_isco['skills_opcionales_count'].max():.0f}")

# Top 5 ISCOs con más skills
print(f"\n  [4] TOP 5 ISCOs CON MAS SKILLS TOTALES:")
top_iscos = df_tabla_isco.nlargest(5, 'skills_total_count')
for idx, row in top_iscos.iterrows():
    print(f"\n      ISCO {row['isco_code']}: {row['skills_total_count']} skills totales")
    print(f"        Esenciales: {row['skills_esenciales_count']}, Opcionales: {row['skills_opcionales_count']}")
    print(f"        Ejemplos ocupaciones: {row['esco_ocupaciones_ejemplos'][0] if row['esco_ocupaciones_ejemplos'] else 'N/A'}")

print("\n" + "=" * 100)
print("[COMPLETADO]")
print("=" * 100)
