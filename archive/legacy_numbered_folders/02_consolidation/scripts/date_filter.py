"""
Filtrado por Ventana Temporal
==============================

Módulo para filtrar ofertas laborales por fecha de publicación.
Implementa ventana móvil de X días desde HOY hacia atrás.

Uso:
    from date_filter import filter_by_date_window

    df_filtered = filter_by_date_window(df, date_column='fecha_publicacion', days=7)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def filter_by_date_window(
    df: pd.DataFrame,
    date_column: str = 'fecha_publicacion',
    days: int = 7,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Filtra DataFrame por ventana temporal (últimos N días)

    Args:
        df: DataFrame con ofertas laborales
        date_column: Nombre de la columna con fecha de publicación
        days: Días hacia atrás desde HOY (default: 7)
        verbose: Si True, imprime estadísticas (default: True)

    Returns:
        DataFrame filtrado con solo ofertas dentro de la ventana temporal

    Examples:
        # Filtrar ofertas de últimos 7 días
        >>> df_recent = filter_by_date_window(df, days=7)

        # Filtrar ofertas del último mes
        >>> df_month = filter_by_date_window(df, days=30)

        # Usar columna de fecha personalizada
        >>> df_custom = filter_by_date_window(df, date_column='fecha_hora_publicacion', days=15)
    """
    if df.empty:
        logger.warning("DataFrame vacío - retornando sin cambios")
        return df

    if date_column not in df.columns:
        logger.error(f"Columna '{date_column}' no encontrada en DataFrame")
        logger.info(f"Columnas disponibles: {list(df.columns)}")
        return df

    # Estadísticas iniciales
    total_original = len(df)

    # Crear copia para no modificar original
    df_work = df.copy()

    # Convertir a datetime si es string
    df_work[date_column] = pd.to_datetime(df_work[date_column], errors='coerce')

    # Contar valores nulos ANTES del filtro
    null_dates_before = df_work[date_column].isna().sum()

    # Calcular fecha de corte (HOY - N días)
    cutoff_date = datetime.now() - timedelta(days=days)

    if verbose:
        logger.info(f"Filtrando ofertas publicadas desde: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Ventana temporal: últimos {days} días")

    # Filtrar: fecha >= cutoff_date (excluye nulos automáticamente)
    mask = df_work[date_column] >= cutoff_date
    df_filtered = df_work[mask].copy()

    # Estadísticas finales
    total_final = len(df_filtered)
    removed = total_original - total_final
    removed_null = null_dates_before
    removed_old = removed - removed_null

    if verbose:
        logger.info(f"")
        logger.info(f"RESULTADOS DEL FILTRADO:")
        logger.info(f"  Ofertas originales: {total_original:,}")
        logger.info(f"  Ofertas filtradas: {total_final:,}")
        logger.info(f"  Removidas (total): {removed:,}")
        logger.info(f"    - Sin fecha: {removed_null:,}")
        logger.info(f"    - Fuera de ventana: {removed_old:,}")
        logger.info(f"  Tasa de retención: {(total_final/total_original*100):.1f}%")

    return df_filtered


def get_date_stats(df: pd.DataFrame, date_column: str = 'fecha_publicacion') -> dict:
    """
    Obtiene estadísticas sobre las fechas en el DataFrame

    Args:
        df: DataFrame con ofertas
        date_column: Nombre de la columna de fecha

    Returns:
        Dict con estadísticas:
            - total: Total de registros
            - con_fecha: Registros con fecha válida
            - sin_fecha: Registros sin fecha
            - fecha_min: Fecha más antigua
            - fecha_max: Fecha más reciente
            - dias_span: Días entre min y max
    """
    if df.empty:
        return {
            'total': 0,
            'con_fecha': 0,
            'sin_fecha': 0,
            'fecha_min': None,
            'fecha_max': None,
            'dias_span': 0
        }

    if date_column not in df.columns:
        logger.error(f"Columna '{date_column}' no encontrada")
        return None

    # Convertir a datetime
    df_temp = df.copy()
    df_temp[date_column] = pd.to_datetime(df_temp[date_column], errors='coerce')

    # Calcular estadísticas
    total = len(df_temp)
    con_fecha = df_temp[date_column].notna().sum()
    sin_fecha = df_temp[date_column].isna().sum()

    fecha_min = df_temp[date_column].min()
    fecha_max = df_temp[date_column].max()

    if pd.notna(fecha_min) and pd.notna(fecha_max):
        dias_span = (fecha_max - fecha_min).days
    else:
        dias_span = 0

    stats = {
        'total': total,
        'con_fecha': con_fecha,
        'sin_fecha': sin_fecha,
        'fecha_min': fecha_min,
        'fecha_max': fecha_max,
        'dias_span': dias_span
    }

    return stats


def print_date_distribution(df: pd.DataFrame, date_column: str = 'fecha_publicacion', bins: int = 10):
    """
    Imprime distribución de ofertas por fecha

    Args:
        df: DataFrame con ofertas
        date_column: Nombre de la columna de fecha
        bins: Número de bins para el histograma
    """
    if df.empty:
        logger.warning("DataFrame vacío")
        return

    if date_column not in df.columns:
        logger.error(f"Columna '{date_column}' no encontrada")
        return

    # Convertir a datetime
    df_temp = df.copy()
    df_temp[date_column] = pd.to_datetime(df_temp[date_column], errors='coerce')

    # Remover nulos
    df_temp = df_temp[df_temp[date_column].notna()]

    if df_temp.empty:
        logger.warning("No hay fechas válidas para mostrar distribución")
        return

    # Agrupar por día
    df_temp['fecha_solo'] = df_temp[date_column].dt.date
    daily_counts = df_temp.groupby('fecha_solo').size().sort_index()

    print("\n" + "="*70)
    print("DISTRIBUCIÓN DE OFERTAS POR FECHA")
    print("="*70)
    print(f"Total ofertas: {len(df_temp):,}")
    print(f"Período: {daily_counts.index[0]} a {daily_counts.index[-1]}")
    print(f"Días con ofertas: {len(daily_counts)}")
    print("\nTop 10 días con más ofertas:")
    top_days = daily_counts.nlargest(10)
    for fecha, count in top_days.items():
        print(f"  {fecha}: {count:,} ofertas")
    print("="*70)


if __name__ == "__main__":
    # Test del módulo
    print("Test del módulo date_filter.py")
    print("="*70)

    # Crear DataFrame de ejemplo
    test_data = pd.DataFrame({
        'id_oferta': range(1, 101),
        'titulo': ['Oferta ' + str(i) for i in range(1, 101)],
        'fecha_publicacion': pd.date_range(end=datetime.now(), periods=100, freq='6H')
    })

    print(f"\nDataFrame de prueba: {len(test_data)} ofertas")
    print(f"Período: {test_data['fecha_publicacion'].min()} a {test_data['fecha_publicacion'].max()}")

    # Test 1: Filtrar últimos 7 días
    print("\n" + "-"*70)
    print("TEST 1: Filtrar últimos 7 días")
    print("-"*70)
    df_7d = filter_by_date_window(test_data, days=7, verbose=True)

    # Test 2: Filtrar últimos 3 días
    print("\n" + "-"*70)
    print("TEST 2: Filtrar últimos 3 días")
    print("-"*70)
    df_3d = filter_by_date_window(test_data, days=3, verbose=True)

    # Test 3: Estadísticas
    print("\n" + "-"*70)
    print("TEST 3: Estadísticas de fechas")
    print("-"*70)
    stats = get_date_stats(test_data)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test 4: Distribución
    print("\n" + "-"*70)
    print("TEST 4: Distribución de ofertas")
    print("-"*70)
    print_date_distribution(test_data)

    print("\n" + "="*70)
    print("Tests completados exitosamente!")
    print("="*70)
