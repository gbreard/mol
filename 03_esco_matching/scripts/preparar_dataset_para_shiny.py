# -*- coding: utf-8 -*-
"""
Preparar Dataset ESCO para Dashboard Shiny
===========================================

Convertir dataset enriquecido a formato óptimo para Shiny:
- CSV limpio sin encoding issues
- Columnas simplificadas y bien nombradas
- Skills en formato string (no listas Python)
- Fechas en formato estándar
"""
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Rutas
INPUT_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_enriquecidas_esco_skills_20251028_205036.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\Visual--")

print("=" * 100)
print("PREPARAR DATASET PARA SHINY")
print("=" * 100)

# Cargar dataset
print("\n[1/4] Cargando dataset enriquecido...")
df = pd.read_csv(INPUT_PATH, encoding='utf-8', low_memory=False)
print(f"  Cargado: {len(df)} ofertas, {len(df.columns)} columnas")

# Convertir skills de string a lista limpia, luego a string separado por comas
print("\n[2/4] Procesando skills...")

def convert_skills_to_string(skills_col):
    """Convierte lista de skills a string separado por comas"""
    if pd.isna(skills_col):
        return ""

    try:
        # Si es string que parece lista, evaluar
        if isinstance(skills_col, str):
            skills_list = eval(skills_col)
        else:
            skills_list = skills_col

        # Convertir a string separado por " | "
        if isinstance(skills_list, list):
            return " | ".join(str(s) for s in skills_list if s)
        else:
            return str(skills_list)
    except:
        return str(skills_col) if pd.notna(skills_col) else ""

# Procesar columnas de skills
for col in ['soft_skills', 'skills_tecnicas', 'esco_skills_esenciales', 'esco_skills_opcionales']:
    if col in df.columns:
        print(f"  Procesando: {col}")
        df[col] = df[col].apply(convert_skills_to_string)

# Convertir certificaciones si existe
if 'certificaciones_list' in df.columns:
    df['certificaciones_list'] = df['certificaciones_list'].apply(convert_skills_to_string)

print("  OK: Skills convertidas a strings")

# Asegurar formato de fechas
print("\n[3/4] Procesando fechas...")
if 'fecha_publicacion' in df.columns:
    df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
    # Crear columna de periodo (YYYY-MM-DD)
    df['periodo'] = df['fecha_publicacion'].dt.strftime('%Y-%m-%d')
else:
    df['periodo'] = datetime.now().strftime('%Y-%m-%d')

print("  OK: Fechas procesadas")

# Crear columnas adicionales útiles para el dashboard
print("\n[4/4] Creando columnas adicionales...")

# ISCO nivel 1 y 2
df['isco_nivel1'] = df['claude_isco_code'].astype(str).str[0]
df['isco_nivel2'] = df['claude_isco_code'].astype(str).str.split('.').str[0].str[:2]

# Mapeo de nombres ISCO nivel 1
isco1_labels = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales',
    '3': 'Técnicos y profesionales nivel medio',
    '4': 'Personal de apoyo administrativo',
    '5': 'Trabajadores de servicios y ventas',
    '6': 'Agricultores y trabajadores agropecuarios',
    '7': 'Oficiales, operarios y artesanos',
    '8': 'Operadores de instalaciones y máquinas',
    '9': 'Ocupaciones elementales'
}

df['isco_nivel1_nombre'] = df['isco_nivel1'].map(isco1_labels)

# Skills totales parseadas
df['skills_parseadas_total'] = df['soft_skills_count'].fillna(0) + df['skills_tecnicas_count'].fillna(0)

# Flag de completitud
df['tiene_skills_parseadas'] = (df['soft_skills'].notna() & (df['soft_skills'] != ''))
df['tiene_skills_esco'] = (df['esco_skills_total_count'] > 0)
df['datos_completos'] = df['tiene_skills_parseadas'] & df['tiene_skills_esco']

print("  OK: Columnas adicionales creadas")

# Reordenar columnas para mejor visualización en Shiny
columnas_orden = [
    # Identificación
    'fecha_publicacion', 'periodo', 'fuente', 'empresa', 'localizacion', 'titulo',

    # ESCO Matching (lo más importante)
    'claude_esco_label', 'claude_isco_code', 'isco_nivel1', 'isco_nivel1_nombre', 'isco_nivel2',
    'claude_confidence', 'claude_razonamiento',

    # Skills ESCO
    'esco_skills_esenciales', 'esco_skills_esenciales_count',
    'esco_skills_opcionales', 'esco_skills_opcionales_count',
    'esco_skills_total_count',

    # Skills Parseadas
    'soft_skills', 'soft_skills_count',
    'skills_tecnicas', 'skills_tecnicas_count',
    'skills_parseadas_total',

    # Requisitos
    'nivel_educativo', 'experiencia_min_anios', 'experiencia_max_anios',
    'idioma_principal', 'certificaciones_list',

    # Matching original (comparación)
    'esco_occupation_label', 'esco_codigo_isco',
    'esco_match_score', 'esco_confianza',

    # Flags
    'tiene_skills_parseadas', 'tiene_skills_esco', 'datos_completos',

    # Otros
    'descripcion'
]

# Asegurar que todas las columnas existan
columnas_existentes = [col for col in columnas_orden if col in df.columns]
columnas_faltantes = [col for col in df.columns if col not in columnas_existentes]

df_final = df[columnas_existentes + columnas_faltantes]

# Guardar CSV para Shiny
output_path = OUTPUT_DIR / "ofertas_esco_para_shiny.csv"
df_final.to_csv(output_path, index=False, encoding='utf-8')

print("\n" + "=" * 100)
print("DATASET PREPARADO PARA SHINY")
print("=" * 100)

print(f"\n  Filas:              {len(df_final)}")
print(f"  Columnas:           {len(df_final.columns)}")
print(f"  Archivo:            {output_path}")
print(f"  Tamaño:             {output_path.stat().st_size / 1024:.1f} KB")

print("\n  Columnas principales:")
for i, col in enumerate(columnas_existentes[:10], 1):
    print(f"    {i:2}. {col}")

print(f"\n  ... y {len(df_final.columns) - 10} columnas más")

# Estadísticas rápidas
print("\n  Estadísticas:")
print(f"    Fechas únicas:      {df_final['periodo'].nunique()}")
print(f"    Fuentes:            {df_final['fuente'].nunique()}")
print(f"    Empresas:           {df_final['empresa'].nunique()}")
print(f"    ISCOs nivel 1:      {df_final['isco_nivel1'].nunique()}")
print(f"    Ocupaciones ESCO:   {df_final['claude_esco_label'].nunique()}")

print("\n" + "=" * 100)
print("[COMPLETADO] Dataset listo para usar en Shiny")
print("=" * 100)
