#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Migración de Datos Históricos a SQLite

Migra todos los CSVs históricos a la base de datos SQLite, deduplicando
y actualizando el tracking para el sistema incremental.

Fecha: 2025-10-31
"""

import pandas as pd
import sqlite3
import json
import glob
import sys
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CSV_DIR = PROJECT_ROOT / "01_sources" / "bumeran" / "data" / "raw"
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
TRACKING_FILE = PROJECT_ROOT / "01_sources" / "bumeran" / "tracking" / "scraped_ids.json"

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_todos_los_csvs():
    """Carga y consolida todos los CSVs históricos"""
    print('='*70)
    print('PASO 1: CARGANDO CSVs HISTÓRICOS')
    print('='*70)
    print()

    csv_files = list(CSV_DIR.glob("bumeran_*.csv"))
    print(f'Archivos CSV encontrados: {len(csv_files)}')
    print()

    if not csv_files:
        print('ERROR: No se encontraron archivos CSV')
        return None

    dfs = []
    total_filas = 0

    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            dfs.append(df)
            total_filas += len(df)
            print(f'  OK {csv_file.name[:60]:60s} | {len(df):>6,} ofertas')
        except Exception as e:
            print(f'  ERROR {csv_file.name[:60]:60s} | ERROR: {e}')

    if not dfs:
        print('ERROR: No se pudieron leer los CSVs')
        return None

    print()
    print(f'Total filas leídas: {total_filas:,}')
    print()

    # Consolidar todos los DataFrames
    print('Consolidando DataFrames...')
    df_consolidado = pd.concat(dfs, ignore_index=True)
    print(f'  [OK] DataFrame consolidado: {len(df_consolidado):,} filas')

    return df_consolidado

def deduplicar_ofertas(df):
    """Deduplica ofertas por id_oferta (aviso_id)"""
    print()
    print('='*70)
    print('PASO 2: DEDUPLICANDO OFERTAS')
    print('='*70)
    print()

    ofertas_antes = len(df)

    # Identificar columna de ID
    if 'id_oferta' in df.columns:
        id_col = 'id_oferta'
    elif 'aviso_id' in df.columns:
        id_col = 'aviso_id'
    else:
        print('ERROR: No se encontró columna de ID (id_oferta o aviso_id)')
        return None

    print(f'Columna de ID: {id_col}')
    print(f'Ofertas antes de deduplicar: {ofertas_antes:,}')
    print()

    # Deduplicar manteniendo la primera ocurrencia
    df_dedup = df.drop_duplicates(subset=[id_col], keep='first')

    ofertas_despues = len(df_dedup)
    duplicados = ofertas_antes - ofertas_despues

    print(f'Ofertas después de deduplicar: {ofertas_despues:,}')
    print(f'Duplicados eliminados: {duplicados:,} ({duplicados/ofertas_antes*100:.2f}%)')
    print()

    return df_dedup, id_col

def normalizar_columnas(df, id_col):
    """Normaliza nombres de columnas para coincidir con esquema SQLite"""
    print('='*70)
    print('PASO 3: NORMALIZANDO COLUMNAS')
    print('='*70)
    print()

    # Mapeo de columnas
    column_mapping = {
        'aviso_id': 'id_oferta',
        'id_aviso': 'id_oferta',
    }

    # Renombrar columnas
    df_norm = df.rename(columns=column_mapping)

    # Asegurar que existe scrapeado_en
    if 'scrapeado_en' not in df_norm.columns:
        df_norm['scrapeado_en'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('  [OK] Agregada columna scrapeado_en')

    print(f'  [OK] DataFrame normalizado: {len(df_norm.columns)} columnas')
    print()

    return df_norm

def cargar_a_sqlite(df):
    """Carga DataFrame consolidado a SQLite"""
    print('='*70)
    print('PASO 4: CARGANDO A SQLITE')
    print('='*70)
    print()

    # Crear backup de DB actual
    import shutil
    if DB_PATH.exists():
        backup_path = DB_PATH.with_suffix('.db.backup')
        shutil.copy2(DB_PATH, backup_path)
        print(f'  [OK] Backup creado: {backup_path}')
        print()

    # Conectar a SQLite
    conn = sqlite3.connect(DB_PATH)

    # Obtener columnas de la tabla SQLite
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(ofertas)')
    columnas_sqlite = [row[1] for row in cursor.fetchall()]

    print(f'  Columnas en tabla SQLite: {len(columnas_sqlite)}')
    print(f'  Columnas en DataFrame: {len(df.columns)}')

    # Filtrar solo columnas que existen en SQLite
    columnas_validas = [col for col in df.columns if col in columnas_sqlite]
    columnas_excluidas = [col for col in df.columns if col not in columnas_sqlite]

    print(f'  Columnas a insertar: {len(columnas_validas)}')
    if columnas_excluidas:
        print(f'  Columnas excluidas: {len(columnas_excluidas)} ({", ".join(columnas_excluidas[:5])}...)')
    print()

    df_filtrado = df[columnas_validas]

    # Limpiar tabla ofertas
    print('  Limpiando tabla ofertas...')
    conn.execute('DELETE FROM ofertas')
    conn.commit()
    print('  [OK] Tabla ofertas limpiada')
    print()

    # Cargar datos
    print(f'  Cargando {len(df_filtrado):,} ofertas a SQLite...')

    try:
        df_filtrado.to_sql('ofertas', conn, if_exists='append', index=False)
        conn.commit()
        print(f'  [OK] {len(df_filtrado):,} ofertas cargadas exitosamente')
    except Exception as e:
        print(f'  [ERROR] ERROR al cargar: {e}')
        conn.rollback()
        conn.close()
        return False

    # Verificar
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total_db = cursor.fetchone()[0]

    print()
    print(f'  Verificación: {total_db:,} ofertas en base de datos')

    conn.close()

    if total_db != len(df_filtrado):
        print(f'  [WARNING] Discrepancia en conteo')
        return False

    print('  [OK] Verificación exitosa')
    print()

    return True

def actualizar_tracking(df, id_col):
    """Actualiza archivo de tracking con todos los IDs"""
    print('='*70)
    print('PASO 5: ACTUALIZANDO TRACKING')
    print('='*70)
    print()

    # Extraer todos los IDs
    ids_unicos = df[id_col].unique().tolist()

    print(f'  IDs únicos extraídos: {len(ids_unicos):,}')

    # Crear nuevo tracking
    tracking = {
        'scraped_ids': ids_unicos,
        'last_updated': datetime.now().isoformat(),
        'total_count': len(ids_unicos)
    }

    # Crear backup del tracking actual
    if TRACKING_FILE.exists():
        backup_path = TRACKING_FILE.with_suffix('.json.backup')
        import shutil
        shutil.copy2(TRACKING_FILE, backup_path)
        print(f'  [OK] Backup de tracking creado: {backup_path}')

    # Guardar nuevo tracking
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)

    print(f'  [OK] Tracking actualizado: {len(ids_unicos):,} IDs')
    print()

    return True

def generar_reporte_final():
    """Genera reporte final de la migración"""
    print('='*70)
    print('REPORTE FINAL DE MIGRACIÓN')
    print('='*70)
    print()

    # SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total_ofertas = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT id_oferta) FROM ofertas')
    ofertas_unicas = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(scrapeado_en), MAX(scrapeado_en) FROM ofertas')
    fecha_min, fecha_max = cursor.fetchone()

    conn.close()

    # Tracking
    with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
        tracking = json.load(f)

    # Mostrar reporte
    print(f'Base de Datos SQLite:')
    print(f'  Total ofertas:        {total_ofertas:,}')
    print(f'  Ofertas únicas:       {ofertas_unicas:,}')
    print(f'  Rango temporal:       {fecha_min} a {fecha_max}')
    print()

    print(f'Tracking Incremental:')
    print(f'  IDs rastreados:       {len(tracking["scraped_ids"]):,}')
    print(f'  Última actualización: {tracking["last_updated"]}')
    print()

    # Tamaño DB
    import os
    db_size = os.path.getsize(DB_PATH)
    print(f'Tamaño base de datos:   {db_size:,} bytes ({db_size/1024/1024:.2f} MB)')
    print()

    print('='*70)
    print('[COMPLETADO] MIGRACION COMPLETADA EXITOSAMENTE')
    print('='*70)
    print()
    print('Próximos scrapeos se ejecutarán de forma INCREMENTAL')
    print(f'desde una base de {total_ofertas:,} ofertas.')
    print()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    print()
    print('='*70)
    print('    MIGRACION DE DATOS HISTORICOS A SQLITE    '.center(70))
    print('='*70)
    print()
    print(f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    # Confirmar con usuario
    respuesta = input('¿Desea continuar con la migración? (S/N): ')
    if respuesta.upper() != 'S':
        print('Migración cancelada.')
        return

    print()

    # Paso 1: Cargar CSVs
    df_consolidado = cargar_todos_los_csvs()
    if df_consolidado is None:
        print('ERROR: No se pudieron cargar los CSVs')
        return 1

    # Paso 2: Deduplicar
    resultado = deduplicar_ofertas(df_consolidado)
    if resultado is None:
        print('ERROR: No se pudo deduplicar')
        return 1

    df_dedup, id_col = resultado

    # Paso 3: Normalizar
    df_norm = normalizar_columnas(df_dedup, id_col)

    # Paso 4: Cargar a SQLite
    if not cargar_a_sqlite(df_norm):
        print('ERROR: Fallo al cargar a SQLite')
        return 1

    # Paso 5: Actualizar tracking
    if not actualizar_tracking(df_norm, 'id_oferta'):
        print('ERROR: Fallo al actualizar tracking')
        return 1

    # Reporte final
    generar_reporte_final()

    return 0

if __name__ == '__main__':
    sys.exit(main())
