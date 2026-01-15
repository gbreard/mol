#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Medición de Cobertura - v3.1 vs v3.2

Compara la cobertura alcanzada entre diferentes versiones del diccionario.

Fecha: 2025-10-31
Autor: Script generado por Claude Code
"""

import pandas as pd
import json
from datetime import datetime
import glob
import os

# ============================================================================
# CONFIGURACION
# ============================================================================

DATA_DIR = '../01_sources/bumeran/data/raw/'
TRACKING_FILE = '../01_sources/bumeran/tracking/scraped_ids.json'
TOTAL_OFERTAS_BUMERAN = 12207  # Actualizar con valor real

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_tracking():
    """Carga archivo de tracking de IDs scrapeados"""
    with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def consolidar_csvs(patron='bumeran_*.csv'):
    """Consolida todos los CSVs que coinciden con el patrón"""
    archivos = glob.glob(os.path.join(DATA_DIR, patron))

    if not archivos:
        print(f'No se encontraron archivos con patrón: {patron}')
        return pd.DataFrame()

    print(f'Consolidando {len(archivos)} archivos CSV...')

    dfs = []
    for archivo in archivos:
        try:
            df = pd.read_csv(archivo, encoding='utf-8')
            dfs.append(df)
            print(f'  - {os.path.basename(archivo)}: {len(df)} ofertas')
        except Exception as e:
            print(f'  ERROR leyendo {archivo}: {e}')

    if not dfs:
        return pd.DataFrame()

    df_consolidado = pd.concat(dfs, ignore_index=True)

    # Deduplicar por aviso_id
    ofertas_antes = len(df_consolidado)
    df_consolidado = df_consolidado.drop_duplicates(subset=['aviso_id'], keep='first')
    ofertas_despues = len(df_consolidado)

    print(f'\nConsolidación:')
    print(f'  Total filas: {ofertas_antes:,}')
    print(f'  Duplicados eliminados: {ofertas_antes - ofertas_despues:,}')
    print(f'  Ofertas únicas: {ofertas_despues:,}')

    return df_consolidado

def analizar_cobertura():
    """Análisis completo de cobertura"""
    print('='*70)
    print('ANALISIS DE COBERTURA - DICCIONARIO v3.1 vs v3.2')
    print('='*70)
    print()

    # 1. Cargar tracking
    print('1. Cargando tracking de IDs scrapeados...')
    tracking = cargar_tracking()
    ids_scrapeados = set(tracking.get('scraped_ids', []))
    print(f'   Total IDs en tracking: {len(ids_scrapeados):,}')
    print()

    # 2. Consolidar todos los CSVs disponibles
    print('2. Consolidando todos los CSVs disponibles...')
    df_todas = consolidar_csvs('bumeran_*.csv')

    if df_todas.empty:
        print('ERROR: No se encontraron datos para analizar')
        return

    print()

    # 3. Identificar ofertas por versión del diccionario
    print('3. Clasificando ofertas por versión del diccionario...')

    # Buscar CSVs específicos de cada versión
    csv_v3_1 = glob.glob(os.path.join(DATA_DIR, 'bumeran_ultra_exhaustiva_v3_1*.csv'))
    csv_v3_2 = glob.glob(os.path.join(DATA_DIR, 'bumeran_ultra_exhaustiva_v3_2*.csv'))

    ofertas_v3_1 = set()
    ofertas_v3_2 = set()

    # IDs de v3.1
    if csv_v3_1:
        for archivo in csv_v3_1:
            df = pd.read_csv(archivo, encoding='utf-8')
            ofertas_v3_1.update(df['aviso_id'].tolist())
        print(f'   Ofertas con v3.1: {len(ofertas_v3_1):,}')

    # IDs de v3.2
    if csv_v3_2:
        for archivo in csv_v3_2:
            df = pd.read_csv(archivo, encoding='utf-8')
            ofertas_v3_2.update(df['aviso_id'].tolist())
        print(f'   Ofertas con v3.2: {len(ofertas_v3_2):,}')

    # Ofertas nuevas capturadas por v3.2
    ofertas_nuevas_v3_2 = ofertas_v3_2 - ofertas_v3_1
    print(f'   Ofertas NUEVAS con v3.2: {len(ofertas_nuevas_v3_2):,}')
    print()

    # 4. Calcular métricas de cobertura
    print('4. Calculando métricas de cobertura...')

    total_unicas = len(df_todas)
    cobertura_actual = (total_unicas / TOTAL_OFERTAS_BUMERAN) * 100

    print(f'   Total ofertas en Bumeran: {TOTAL_OFERTAS_BUMERAN:,}')
    print(f'   Total ofertas scrapeadas: {total_unicas:,}')
    print(f'   Cobertura actual: {cobertura_actual:.2f}%')
    print()

    # 5. Comparación v3.1 vs v3.2
    if ofertas_v3_1 and ofertas_v3_2:
        print('5. Comparación v3.1 vs v3.2:')

        cobertura_v3_1 = (len(ofertas_v3_1) / TOTAL_OFERTAS_BUMERAN) * 100
        cobertura_v3_2 = (len(ofertas_v3_2) / TOTAL_OFERTAS_BUMERAN) * 100
        mejora_absoluta = len(ofertas_v3_2) - len(ofertas_v3_1)
        mejora_porcentual = cobertura_v3_2 - cobertura_v3_1

        print(f'   v3.1 (1,000 keywords):')
        print(f'     - Ofertas: {len(ofertas_v3_1):,}')
        print(f'     - Cobertura: {cobertura_v3_1:.2f}%')
        print()
        print(f'   v3.2 (1,148 keywords):')
        print(f'     - Ofertas: {len(ofertas_v3_2):,}')
        print(f'     - Cobertura: {cobertura_v3_2:.2f}%')
        print()
        print(f'   MEJORA:')
        print(f'     - Ofertas adicionales: +{mejora_absoluta:,}')
        print(f'     - Mejora en cobertura: +{mejora_porcentual:.2f} puntos porcentuales')
        print(f'     - Incremento relativo: +{(mejora_absoluta/len(ofertas_v3_1)*100):.2f}%')
        print()

    # 6. Análisis temporal
    print('6. Análisis temporal de ofertas:')
    df_todas['fecha_publicacion_iso'] = pd.to_datetime(df_todas['fecha_publicacion_iso'], errors='coerce')

    fecha_min = df_todas['fecha_publicacion_iso'].min()
    fecha_max = df_todas['fecha_publicacion_iso'].max()
    dias_rango = (fecha_max - fecha_min).days

    print(f'   Rango temporal: {fecha_min.date()} a {fecha_max.date()}')
    print(f'   Días de cobertura: {dias_rango}')
    print()

    # 7. Distribución por fuente
    print('7. Distribución de ofertas por categoría:')
    if 'rubro' in df_todas.columns:
        top_rubros = df_todas['rubro'].value_counts().head(10)
        for rubro, count in top_rubros.items():
            print(f'   - {rubro}: {count:,} ofertas')
    print()

    # 8. Resumen final
    print('='*70)
    print('RESUMEN FINAL')
    print('='*70)
    print(f'Fecha de análisis: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Total ofertas únicas: {total_unicas:,}')
    print(f'Cobertura alcanzada: {cobertura_actual:.2f}%')

    if ofertas_nuevas_v3_2:
        print(f'Ofertas nuevas con v3.2: +{len(ofertas_nuevas_v3_2):,}')
        print(f'Mejora de cobertura: +{mejora_porcentual:.2f} puntos')

    print('='*70)

    # 9. Guardar reporte
    reporte = {
        'fecha_analisis': datetime.now().isoformat(),
        'total_ofertas_bumeran': TOTAL_OFERTAS_BUMERAN,
        'total_scrapeadas': total_unicas,
        'cobertura_porcentaje': round(cobertura_actual, 2),
        'v3.1': {
            'ofertas': len(ofertas_v3_1),
            'keywords': 1000,
            'cobertura': round(cobertura_v3_1, 2) if ofertas_v3_1 else 0
        },
        'v3.2': {
            'ofertas': len(ofertas_v3_2),
            'keywords': 1148,
            'cobertura': round(cobertura_v3_2, 2) if ofertas_v3_2 else 0
        },
        'mejora': {
            'ofertas_adicionales': mejora_absoluta if ofertas_v3_1 and ofertas_v3_2 else 0,
            'puntos_porcentuales': round(mejora_porcentual, 2) if ofertas_v3_1 and ofertas_v3_2 else 0
        }
    }

    reporte_path = '../data/analysis/reporte_cobertura_v3_2.json'
    with open(reporte_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f'\nReporte guardado: {reporte_path}')
    print()

if __name__ == '__main__':
    analizar_cobertura()
