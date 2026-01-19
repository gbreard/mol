# -*- coding: utf-8 -*-
"""
Merge resultados de matching manual con datos originales completos
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

# Rutas
ORIGINAL_PATH = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv"
MATCHING_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\matching_manual_claude_20251028_203400.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")

print("=" * 100)
print("MERGE: DATOS COMPLETOS + MATCHING MANUAL CLAUDE")
print("=" * 100)

# Cargar original (con TODOS los datos parseados)
print("\n[1/3] Cargando CSV original completo...")
df_original = pd.read_csv(ORIGINAL_PATH, encoding='utf-8', low_memory=False)
print(f"  OK: {len(df_original)} filas, {len(df_original.columns)} columnas")
print(f"  Columnas: {list(df_original.columns)}")

# Cargar matching manual
print("\n[2/3] Cargando matching manual Claude...")
df_matching = pd.read_csv(MATCHING_PATH, encoding='utf-8')
print(f"  OK: {len(df_matching)} filas, {len(df_matching.columns)} columnas")

# Verificar que ambos tienen mismo número de filas
if len(df_original) != len(df_matching):
    print(f"\n[ERROR] Diferente número de filas:")
    print(f"  Original: {len(df_original)}")
    print(f"  Matching: {len(df_matching)}")
    raise ValueError("Los DataFrames deben tener el mismo número de filas")

# Verificar que titulos coinciden (mismo orden)
titulos_match = (df_original['titulo'] == df_matching['titulo']).all()
print(f"\n  Titulos coinciden en orden: {titulos_match}")

if not titulos_match:
    print("\n[WARNING] Titulos no coinciden exactamente, haciendo merge por titulo...")
    # Merge por titulo
    df_final = df_original.merge(
        df_matching.drop(columns=['fuzzy_esco_label', 'fuzzy_isco_code', 'fuzzy_confidence']),
        on='titulo',
        how='left'
    )
else:
    # Agregar columnas de matching al original
    print("\n[3/3] Agregando columnas de matching manual...")
    df_final = df_original.copy()

    # Agregar solo las columnas nuevas de Claude (no duplicar fuzzy)
    columnas_claude = ['claude_esco_id', 'claude_esco_label', 'claude_isco_code',
                       'claude_confidence', 'claude_razonamiento', 'claude_patron']

    for col in columnas_claude:
        if col in df_matching.columns:
            df_final[col] = df_matching[col]

print(f"\n  Total columnas finales: {len(df_final.columns)}")

# Reordenar columnas para mejor lectura
columnas_orden = [
    # Metadatos oferta
    'fecha_publicacion', 'fuente', 'empresa', 'localizacion', 'titulo', 'descripcion',

    # Matching Claude (NUEVO)
    'claude_esco_id', 'claude_esco_label', 'claude_isco_code',
    'claude_confidence', 'claude_razonamiento', 'claude_patron',

    # Matching Fuzzy/LLM original (para comparación)
    'esco_occupation_id', 'esco_occupation_label', 'esco_codigo_isco',
    'esco_match_score', 'esco_skills_overlap', 'esco_match_method', 'esco_confianza',

    # Datos parseados del LLM
    'soft_skills', 'soft_skills_count',
    'skills_tecnicas', 'skills_tecnicas_count',
    'nivel_educativo', 'experiencia_min_anios', 'experiencia_max_anios',
    'idioma_principal', 'certificaciones_list',

    # Flags
    'hybrid_method', 'hybrid_llm_called', 'is_complete'
]

# Asegurar que todas las columnas existan
columnas_existentes = [col for col in columnas_orden if col in df_final.columns]
columnas_faltantes = [col for col in df_final.columns if col not in columnas_existentes]

df_final = df_final[columnas_existentes + columnas_faltantes]

# Guardar
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = OUTPUT_DIR / f"ofertas_completas_con_matching_claude_{timestamp}.csv"

df_final.to_csv(output_path, index=False, encoding='utf-8')

print("\n" + "=" * 100)
print("RESULTADOS")
print("=" * 100)
print(f"\n  Filas:              {len(df_final)}")
print(f"  Columnas totales:   {len(df_final.columns)}")
print(f"\n  Nuevas columnas Claude:")
for col in columnas_claude:
    if col in df_final.columns:
        print(f"    - {col}")

print(f"\n  Guardado: {output_path}")
print("=" * 100)

# Estadísticas rápidas
print("\n[ESTADISTICAS]")
print(f"\n  Matching Claude:")
print(f"    100% coverage: {df_final['claude_esco_label'].notna().sum()} ofertas")

print(f"\n  Datos parseados:")
print(f"    Con soft skills:      {df_final['soft_skills'].notna().sum()} ({df_final['soft_skills'].notna().sum()/len(df_final)*100:.1f}%)")
print(f"    Con skills técnicas:  {df_final['skills_tecnicas'].notna().sum()} ({df_final['skills_tecnicas'].notna().sum()/len(df_final)*100:.1f}%)")
print(f"    Con nivel educativo:  {df_final['nivel_educativo'].notna().sum()} ({df_final['nivel_educativo'].notna().sum()/len(df_final)*100:.1f}%)")
print(f"    Con experiencia:      {df_final['experiencia_min_anios'].notna().sum()} ({df_final['experiencia_min_anios'].notna().sum()/len(df_final)*100:.1f}%)")

print("\n[COMPLETADO]")
