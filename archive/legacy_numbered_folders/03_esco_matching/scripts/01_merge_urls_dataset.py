# -*- coding: utf-8 -*-
"""
Recuperar URLs del Archivo Consolidado
=======================================

Hace merge entre el dataset enriquecido ESCO y el archivo consolidado original
para recuperar las URLs de las ofertas que se perdieron en el pipeline.
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

# Rutas
DATASET_ESCO = r"D:\OEDE\Webscrapping\03_esco_matching\data\ofertas_enriquecidas_esco_skills_20251028_205036.csv"
CONSOLIDADO = r"D:\OEDE\Webscrapping\02_consolidation\data\consolidated\ofertas_consolidadas_20251025_125307.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")

print("=" * 100)
print("RECUPERAR URLs DEL ARCHIVO CONSOLIDADO")
print("=" * 100)

# === 1. Cargar datos ===
print("\n[1/4] Cargando datos...")

df_esco = pd.read_csv(DATASET_ESCO, encoding='utf-8', low_memory=False)
print(f"  Dataset ESCO: {len(df_esco)} ofertas, {len(df_esco.columns)} columnas")

df_consolidado = pd.read_csv(CONSOLIDADO, encoding='utf-8', low_memory=False)
print(f"  Consolidado:  {len(df_consolidado)} ofertas, {len(df_consolidado.columns)} columnas")

# === 2. Preparar columnas para merge ===
print("\n[2/4] Preparando columnas para merge...")

# Normalizar fechas para matching
df_esco['fecha_norm'] = pd.to_datetime(df_esco['fecha_publicacion'], errors='coerce', dayfirst=True).dt.date
df_consolidado['fecha_norm'] = pd.to_datetime(df_consolidado['fechas.fecha_publicacion'], errors='coerce', dayfirst=True).dt.date

# Normalizar títulos (lowercase y sin espacios extra)
df_esco['titulo_norm'] = df_esco['titulo'].str.lower().str.strip()
df_consolidado['titulo_norm'] = df_consolidado['informacion_basica.titulo'].str.lower().str.strip()

# Normalizar empresas
df_esco['empresa_norm'] = df_esco['empresa'].fillna('').str.lower().str.strip()
df_consolidado['empresa_norm'] = df_consolidado['informacion_basica.empresa'].fillna('').str.lower().str.strip()

print("  OK: Columnas normalizadas")

# === 3. Hacer merge ===
print("\n[3/4] Haciendo merge...")

# Seleccionar columnas del consolidado que queremos recuperar
cols_recuperar = ['_metadata.url_oferta', '_metadata.source', '_metadata.source_id']

# Verificar que existan
cols_disponibles = [col for col in cols_recuperar if col in df_consolidado.columns]
print(f"  Columnas a recuperar: {cols_disponibles}")

# Preparar dataframe de URLs - ELIMINAR DUPLICADOS primero
df_urls = df_consolidado[['titulo_norm', 'empresa_norm', 'fecha_norm'] + cols_disponibles].copy()

# Eliminar duplicados quedándose con el primero
df_urls_unique = df_urls.drop_duplicates(subset=['titulo_norm', 'empresa_norm', 'fecha_norm'], keep='first')

print(f"  Filas consolidado original: {len(df_urls)}")
print(f"  Filas unicas para merge: {len(df_urls_unique)}")

# Merge
df_merged = df_esco.merge(
    df_urls_unique,
    on=['titulo_norm', 'empresa_norm', 'fecha_norm'],
    how='left',
    suffixes=('', '_consolidado')
)

# Verificar resultados del merge
urls_recuperadas = df_merged['_metadata.url_oferta'].notna().sum()
print(f"\n  URLs recuperadas: {urls_recuperadas}/{len(df_merged)} ({urls_recuperadas/len(df_merged)*100:.1f}%)")

# === 4. Limpiar y renombrar ===
print("\n[4/4] Limpiando dataset final...")

# Renombrar columnas recuperadas
if '_metadata.url_oferta' in df_merged.columns:
    df_merged.rename(columns={'_metadata.url_oferta': 'url_oferta'}, inplace=True)
if '_metadata.source' in df_merged.columns:
    df_merged.rename(columns={'_metadata.source': 'fuente_consolidado'}, inplace=True)
if '_metadata.source_id' in df_merged.columns:
    df_merged.rename(columns={'_metadata.source_id': 'source_id'}, inplace=True)

# Eliminar columnas auxiliares de normalización
df_merged.drop(columns=['titulo_norm', 'empresa_norm', 'fecha_norm'], inplace=True, errors='ignore')

# Reordenar: poner URL cerca del inicio
cols_orden = ['fecha_publicacion', 'fuente', 'url_oferta', 'source_id', 'empresa', 'localizacion', 'titulo']
cols_existentes = [col for col in cols_orden if col in df_merged.columns]
cols_resto = [col for col in df_merged.columns if col not in cols_existentes]

df_final = df_merged[cols_existentes + cols_resto]

# === 5. Guardar ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = OUTPUT_DIR / f"ofertas_esco_con_urls_{timestamp}.csv"

df_final.to_csv(output_path, index=False, encoding='utf-8')

print("\n" + "=" * 100)
print("RESULTADO")
print("=" * 100)

print(f"\n  Filas:              {len(df_final)}")
print(f"  Columnas:           {len(df_final.columns)}")
print(f"  URLs recuperadas:   {urls_recuperadas} ({urls_recuperadas/len(df_final)*100:.1f}%)")
print(f"  Archivo:            {output_path}")

# Mostrar casos sin URL (para debugging)
sin_url = df_final[df_final['url_oferta'].isna()]
if len(sin_url) > 0:
    print(f"\n  [!] Ofertas SIN URL: {len(sin_url)}")
    print("\n  Primeras 5 sin URL:")
    for idx, row in sin_url.head(5).iterrows():
        print(f"    - {row['titulo']} | {row['empresa']} | {row['fecha_publicacion']}")
else:
    print(f"\n  [OK] TODAS las ofertas tienen URL!")

# Mostrar ejemplos de URLs recuperadas
print("\n  Ejemplos de URLs recuperadas:")
urls_ejemplos = df_final[df_final['url_oferta'].notna()]['url_oferta'].head(3)
for url in urls_ejemplos:
    print(f"    {url}")

print("\n" + "=" * 100)
print("[COMPLETADO]")
print("=" * 100)
