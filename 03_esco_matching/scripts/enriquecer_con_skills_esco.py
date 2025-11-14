# -*- coding: utf-8 -*-
"""
Enriquecer dataset con Skills y Conocimientos de ESCO
======================================================

Para cada ocupación ESCO matched, traer:
- Skills esenciales
- Skills opcionales
- Conocimientos
"""
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Rutas
DATASET_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_completas_con_matching_claude_20251028_204443.csv"
ESCO_SKILLS_REL_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_skills_relaciones.json"
ESCO_SKILLS_INFO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_skills_info.json"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")

print("=" * 100)
print("ENRIQUECIMIENTO CON SKILLS Y CONOCIMIENTOS ESCO")
print("=" * 100)

# === 1. Cargar datos ===
print("\n[1/5] Cargando datos...")

df = pd.read_csv(DATASET_PATH, encoding='utf-8', low_memory=False)
print(f"  Dataset: {len(df)} ofertas")

with open(ESCO_SKILLS_REL_PATH, 'r', encoding='utf-8') as f:
    esco_ocu_skills = json.load(f)
print(f"  ESCO relaciones ocupacion-skills: {len(esco_ocu_skills)} ocupaciones")

with open(ESCO_SKILLS_INFO_PATH, 'r', encoding='utf-8') as f:
    esco_skills_info = json.load(f)
print(f"  ESCO skills info: {len(esco_skills_info)} skills")

# === 2. Explorar estructura skills ===
print("\n[2/5] Explorando estructura skills ESCO...")

# Ver estructura de una skill
sample_skill_id = list(esco_skills_info.keys())[0]
sample_skill = esco_skills_info[sample_skill_id]

print(f"\n  Ejemplo skill ID: {sample_skill_id}")
print(f"  Keys disponibles: {list(sample_skill.keys())}")

# Verificar si hay labels en español
if 'labels' in sample_skill:
    if 'es' in sample_skill['labels']:
        print(f"  Tiene label ES: {sample_skill['labels']['es']}")
    elif 'en' in sample_skill['labels']:
        print(f"  Solo label EN: {sample_skill['labels']['en']}")

# === 3. Función para obtener skills de una ocupación ===
def get_skills_for_occupation(esco_id):
    """
    Obtiene skills esenciales y opcionales para una ocupación ESCO

    Returns:
        dict con 'esenciales' y 'opcionales' (listas de nombres de skills)
    """
    if esco_id not in esco_ocu_skills:
        return {'esenciales': [], 'opcionales': [], 'esenciales_ids': [], 'opcionales_ids': []}

    ocu_data = esco_ocu_skills[esco_id]

    # Skills esenciales
    esenciales_ids = ocu_data.get('skills_esenciales', [])
    esenciales_nombres = []
    for skill_id in esenciales_ids:
        if skill_id in esco_skills_info:
            skill_data = esco_skills_info[skill_id]
            # Preferir español, sino inglés
            labels = skill_data.get('labels', {})
            nombre = labels.get('es', labels.get('en', skill_id))
            esenciales_nombres.append(nombre)

    # Skills opcionales
    opcionales_ids = ocu_data.get('skills_opcionales', [])
    opcionales_nombres = []
    for skill_id in opcionales_ids:
        if skill_id in esco_skills_info:
            skill_data = esco_skills_info[skill_id]
            labels = skill_data.get('labels', {})
            nombre = labels.get('es', labels.get('en', skill_id))
            opcionales_nombres.append(nombre)

    return {
        'esenciales': esenciales_nombres,
        'opcionales': opcionales_nombres,
        'esenciales_ids': esenciales_ids,
        'opcionales_ids': opcionales_ids
    }

# === 4. Enriquecer dataset ===
print("\n[3/5] Enriqueciendo dataset con skills ESCO...")

resultados = []
stats = {
    'con_skills_esenciales': 0,
    'con_skills_opcionales': 0,
    'sin_skills': 0
}

for idx, row in df.iterrows():
    esco_id = row['claude_esco_id']

    # Obtener skills ESCO
    skills_esco = get_skills_for_occupation(esco_id)

    # Estadísticas
    if skills_esco['esenciales']:
        stats['con_skills_esenciales'] += 1
    if skills_esco['opcionales']:
        stats['con_skills_opcionales'] += 1
    if not skills_esco['esenciales'] and not skills_esco['opcionales']:
        stats['sin_skills'] += 1

    # Agregar a fila
    row_dict = row.to_dict()
    row_dict['esco_skills_esenciales'] = skills_esco['esenciales']
    row_dict['esco_skills_esenciales_count'] = len(skills_esco['esenciales'])
    row_dict['esco_skills_opcionales'] = skills_esco['opcionales']
    row_dict['esco_skills_opcionales_count'] = len(skills_esco['opcionales'])
    row_dict['esco_skills_total_count'] = len(skills_esco['esenciales']) + len(skills_esco['opcionales'])

    resultados.append(row_dict)

# === 5. Crear DataFrame enriquecido ===
print("\n[4/5] Creando DataFrame enriquecido...")

df_enriquecido = pd.DataFrame(resultados)

# Reordenar columnas
columnas_orden = [
    # Metadatos
    'fecha_publicacion', 'fuente', 'empresa', 'localizacion', 'titulo', 'descripcion',

    # Matching Claude
    'claude_esco_id', 'claude_esco_label', 'claude_isco_code',
    'claude_confidence', 'claude_razonamiento', 'claude_patron',

    # NUEVO: Skills ESCO
    'esco_skills_esenciales', 'esco_skills_esenciales_count',
    'esco_skills_opcionales', 'esco_skills_opcionales_count',
    'esco_skills_total_count',

    # Matching Fuzzy/LLM original
    'esco_occupation_id', 'esco_occupation_label', 'esco_codigo_isco',
    'esco_match_score', 'esco_skills_overlap', 'esco_match_method', 'esco_confianza',

    # Skills parseadas del LLM
    'soft_skills', 'soft_skills_count',
    'skills_tecnicas', 'skills_tecnicas_count',

    # Otros requisitos
    'nivel_educativo', 'experiencia_min_anios', 'experiencia_max_anios',
    'idioma_principal', 'certificaciones_list',

    # Flags
    'hybrid_method', 'hybrid_llm_called', 'is_complete'
]

# Asegurar que todas existan
columnas_existentes = [col for col in columnas_orden if col in df_enriquecido.columns]
columnas_faltantes = [col for col in df_enriquecido.columns if col not in columnas_existentes]

df_enriquecido = df_enriquecido[columnas_existentes + columnas_faltantes]

# === 6. Guardar ===
print("\n[5/5] Guardando dataset enriquecido...")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = OUTPUT_DIR / f"ofertas_enriquecidas_esco_skills_{timestamp}.csv"

df_enriquecido.to_csv(output_path, index=False, encoding='utf-8')

# === RESULTADOS ===
print("\n" + "=" * 100)
print("RESULTADOS")
print("=" * 100)

print(f"\n  Filas:                      {len(df_enriquecido)}")
print(f"  Columnas totales:           {len(df_enriquecido.columns)} (+5 nuevas)")

print(f"\n  Cobertura Skills ESCO:")
print(f"    Con skills esenciales:    {stats['con_skills_esenciales']:>3} ({stats['con_skills_esenciales']/len(df)*100:>5.1f}%)")
print(f"    Con skills opcionales:    {stats['con_skills_opcionales']:>3} ({stats['con_skills_opcionales']/len(df)*100:>5.1f}%)")
print(f"    Sin skills:               {stats['sin_skills']:>3} ({stats['sin_skills']/len(df)*100:>5.1f}%)")

# Estadísticas de skills
print(f"\n  Skills esenciales por ocupacion:")
print(f"    Promedio:                 {df_enriquecido['esco_skills_esenciales_count'].mean():.1f}")
print(f"    Mediana:                  {df_enriquecido['esco_skills_esenciales_count'].median():.0f}")
print(f"    Max:                      {df_enriquecido['esco_skills_esenciales_count'].max():.0f}")

print(f"\n  Skills opcionales por ocupacion:")
print(f"    Promedio:                 {df_enriquecido['esco_skills_opcionales_count'].mean():.1f}")
print(f"    Mediana:                  {df_enriquecido['esco_skills_opcionales_count'].median():.0f}")
print(f"    Max:                      {df_enriquecido['esco_skills_opcionales_count'].max():.0f}")

print(f"\n  Skills totales por ocupacion:")
print(f"    Promedio:                 {df_enriquecido['esco_skills_total_count'].mean():.1f}")
print(f"    Mediana:                  {df_enriquecido['esco_skills_total_count'].median():.0f}")
print(f"    Max:                      {df_enriquecido['esco_skills_total_count'].max():.0f}")

print(f"\n  Guardado: {output_path}")
print("=" * 100)

# === EJEMPLO ===
print("\n[EJEMPLO] Ocupacion con mas skills esenciales:")
max_idx = df_enriquecido['esco_skills_esenciales_count'].idxmax()
ejemplo = df_enriquecido.loc[max_idx]

print(f"\n  Titulo:      {ejemplo['titulo']}")
print(f"  ESCO:        {ejemplo['claude_esco_label']}")
print(f"  ISCO:        {ejemplo['claude_isco_code']}")
print(f"\n  Skills esenciales ({len(ejemplo['esco_skills_esenciales'])} total):")
for i, skill in enumerate(eval(str(ejemplo['esco_skills_esenciales']))[:10], 1):
    print(f"    {i}. {skill}")
if len(ejemplo['esco_skills_esenciales']) > 10:
    print(f"    ... y {len(ejemplo['esco_skills_esenciales']) - 10} mas")

print("\n[COMPLETADO]")
