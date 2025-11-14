# -*- coding: utf-8 -*-
"""
Preparar CSV Final para Dashboard Shiny
========================================

Toma el dataset con URLs y lo prepara en formato óptimo para Shiny:
- Skills convertidas a strings
- Columnas adicionales (ISCO nivel 1/2 con nombres)
- Fechas formateadas
- Reordenamiento de columnas
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

# Rutas
INPUT_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_esco_con_urls_20251028_212124.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\Visual--")

print("=" * 100)
print("PREPARAR CSV PARA DASHBOARD SHINY")
print("=" * 100)

# === 1. Cargar datos ===
print("\n[1/5] Cargando dataset con URLs...")
df = pd.read_csv(INPUT_PATH, encoding='utf-8', low_memory=False)
print(f"  Cargado: {len(df)} ofertas, {len(df.columns)} columnas")

# === 2. Convertir skills a strings ===
print("\n[2/5] Convirtiendo skills a formato string...")

def skills_to_string(skills_col):
    """Convierte lista de skills a string separado por ' | '"""
    if pd.isna(skills_col) or skills_col == '' or skills_col == '[]':
        return ""

    try:
        # Si es string que parece lista Python
        if isinstance(skills_col, str) and skills_col.startswith('['):
            skills_list = eval(skills_col)
        else:
            skills_list = skills_col

        if isinstance(skills_list, list):
            # Filtrar None y vacíos
            skills_clean = [str(s) for s in skills_list if s and str(s).strip()]
            return " | ".join(skills_clean) if skills_clean else ""
        else:
            return str(skills_col).strip()
    except:
        return str(skills_col).strip() if pd.notna(skills_col) else ""

# Aplicar a todas las columnas de skills
skill_cols = ['soft_skills', 'skills_tecnicas', 'esco_skills_esenciales', 'esco_skills_opcionales']
for col in skill_cols:
    if col in df.columns:
        print(f"  Procesando: {col}")
        df[col] = df[col].apply(skills_to_string)

# También certificaciones si existe
if 'certificaciones_list' in df.columns:
    df['certificaciones_list'] = df['certificaciones_list'].apply(skills_to_string)

print("  OK: Skills convertidas")

# === 3. Procesar fechas ===
print("\n[3/5] Procesando fechas...")

if 'fecha_publicacion' in df.columns:
    df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
    # Crear periodo YYYY-MM-DD
    df['periodo'] = df['fecha_publicacion'].dt.strftime('%Y-%m-%d')
else:
    df['periodo'] = datetime.now().strftime('%Y-%m-%d')

print("  OK: Fechas formateadas")

# === 4. Crear columnas adicionales ===
print("\n[4/5] Creando columnas adicionales...")

# ISCO niveles
df['isco_nivel1'] = df['claude_isco_code'].astype(str).str[0]
df['isco_nivel2'] = df['claude_isco_code'].astype(str).str.split('.').str[0].str[:2]
df['isco_4d'] = df['claude_isco_code'].astype(str).str.split('.').str[0]

# Nombres ISCO nivel 1
isco1_labels = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales',
    '3': 'Técnicos y profesionales de nivel medio',
    '4': 'Personal de apoyo administrativo',
    '5': 'Trabajadores de servicios y ventas',
    '6': 'Agricultores y trabajadores agropecuarios',
    '7': 'Oficiales, operarios y artesanos',
    '8': 'Operadores de instalaciones y máquinas',
    '9': 'Ocupaciones elementales'
}

df['isco_nivel1_nombre'] = df['isco_nivel1'].map(isco1_labels)

# Skills totales
df['skills_parseadas_total'] = df['soft_skills_count'].fillna(0) + df['skills_tecnicas_count'].fillna(0)

# Flags útiles
df['tiene_url'] = df['url_oferta'].notna()
df['tiene_skills_parseadas'] = (df['soft_skills'].notna()) & (df['soft_skills'] != '')
df['tiene_skills_esco'] = (df['esco_skills_total_count'].fillna(0) > 0)

print("  OK: Columnas adicionales creadas")

# === 5. Reordenar columnas ===
print("\n[5/5] Reordenando columnas...")

# Orden óptimo para el dashboard
columnas_orden = [
    # Identificación básica
    'fecha_publicacion', 'periodo', 'fuente', 'url_oferta', 'source_id',
    'empresa', 'localizacion', 'titulo', 'descripcion',

    # ESCO Matching (lo más importante)
    'claude_esco_id', 'claude_esco_label', 'claude_isco_code',
    'isco_nivel1', 'isco_nivel1_nombre', 'isco_nivel2', 'isco_4d',
    'claude_confidence', 'claude_razonamiento', 'claude_patron',

    # Skills ESCO (核心valor)
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
    'esco_occupation_id', 'esco_occupation_label', 'esco_codigo_isco',
    'esco_match_score', 'esco_confianza',

    # Flags
    'tiene_url', 'tiene_skills_parseadas', 'tiene_skills_esco',

    # Metadata
    'hybrid_method', 'hybrid_llm_called', 'is_complete'
]

# Asegurar todas las columnas
columnas_existentes = [col for col in columnas_orden if col in df.columns]
columnas_faltantes = [col for col in df.columns if col not in columnas_existentes]

df_final = df[columnas_existentes + columnas_faltantes]

# === 6. Guardar ===
output_path = OUTPUT_DIR / "ofertas_esco_shiny.csv"
df_final.to_csv(output_path, index=False, encoding='utf-8')

print("\n" + "=" * 100)
print("DATASET LISTO PARA SHINY")
print("=" * 100)

print(f"\n  Archivo:            {output_path}")
print(f"  Tamaño:             {output_path.stat().st_size / 1024:.1f} KB")
print(f"  Filas:              {len(df_final)}")
print(f"  Columnas:           {len(df_final.columns)}")

print("\n  Columnas principales (primeras 15):")
for i, col in enumerate(columnas_existentes[:15], 1):
    print(f"    {i:2}. {col}")

print("\n  Estadísticas:")
print(f"    Con URL:            {df_final['tiene_url'].sum()} ({df_final['tiene_url'].sum()/len(df_final)*100:.1f}%)")
print(f"    Con skills ESCO:    {df_final['tiene_skills_esco'].sum()} ({df_final['tiene_skills_esco'].sum()/len(df_final)*100:.1f}%)")
print(f"    Con skills parseadas: {df_final['tiene_skills_parseadas'].sum()} ({df_final['tiene_skills_parseadas'].sum()/len(df_final)*100:.1f}%)")

print(f"\n    Fuentes únicas:     {df_final['fuente'].nunique()}")
print(f"    Empresas únicas:    {df_final['empresa'].nunique()}")
print(f"    Provincias únicas:  {df_final['localizacion'].nunique()}")
print(f"    ISCO nivel 1:       {df_final['isco_nivel1'].nunique()}")
print(f"    Ocupaciones ESCO:   {df_final['claude_esco_label'].nunique()}")

print("\n" + "=" * 100)
print("[COMPLETADO] Dataset optimizado y listo para el dashboard Shiny")
print("=" * 100)
