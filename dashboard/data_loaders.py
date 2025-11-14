"""
Data Loaders Module - Dashboard v4.5
====================================

Funciones de carga de datos desde SQLite para el dashboard operativo.

Organización:
1. CORE - Ofertas, Keywords, Alertas (funciones existentes mejoradas)
2. PIPELINE - Métricas end-to-end del pipeline completo
3. ESCO - Ocupaciones, Skills, Matching, Jerarquías
4. OPERACIONAL - Circuit Breaker, Rate Limiter, Métricas detalladas
5. UTILIDADES - Helpers y funciones auxiliares

Autor: Claude Code (OEDE)
Fecha: 2025-11-04
Versión: 4.5.0
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

DB_PATH = Path('database/bumeran_scraping.db')
TRACKING_FILE = Path('data/tracking/bumeran_scraped_ids.json')

# ==============================================================================
# 1. FUNCIONES CORE (Existentes Mejoradas)
# ==============================================================================

def cargar_ofertas() -> pd.DataFrame:
    """
    Carga todas las ofertas con todas las columnas.

    Returns:
        DataFrame con todas las ofertas
    """
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM ofertas ORDER BY scrapeado_en DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convertir fechas
    if 'fecha_publicacion_iso' in df.columns:
        df['fecha_publicacion_iso'] = pd.to_datetime(df['fecha_publicacion_iso'], errors='coerce')
    if 'scrapeado_en' in df.columns:
        df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'], errors='coerce')

    return df


def cargar_keywords() -> pd.DataFrame:
    """
    Carga performance de keywords.

    Returns:
        DataFrame con métricas de keywords
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            keyword,
            total_ofertas,
            total_nuevas,
            veces_ejecutado,
            ultima_ejecucion,
            esco_occupation_uri,
            esco_skill_uri,
            keyword_source
        FROM keywords_performance
        ORDER BY total_nuevas DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'ultima_ejecucion' in df.columns:
        df['ultima_ejecucion'] = pd.to_datetime(df['ultima_ejecucion'], errors='coerce')

    return df


def cargar_alertas(limit: int = 50) -> pd.DataFrame:
    """
    Carga últimas alertas del sistema.

    Args:
        limit: Número máximo de alertas

    Returns:
        DataFrame con alertas
    """
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT
            timestamp,
            level,
            type,
            message,
            context
        FROM alertas
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    return df


def cargar_metricas_scraping() -> pd.DataFrame:
    """
    Carga métricas de ejecuciones de scraping.

    Returns:
        DataFrame con métricas de scraping
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            start_time,
            end_time,
            total_time_seconds,
            pages_scraped,
            pages_failed,
            pages_total,
            success_rate,
            offers_total,
            offers_new,
            offers_duplicates,
            offers_per_second,
            validation_rate_avg,
            errors_count,
            warnings_count,
            incremental_mode,
            query
        FROM metricas_scraping
        ORDER BY start_time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'start_time' in df.columns:
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    if 'end_time' in df.columns:
        df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')

    return df


def cargar_calidad_parseo() -> pd.DataFrame:
    """
    Carga ofertas con datos de NLP para análisis de calidad.

    JOIN entre ofertas y ofertas_nlp.

    Returns:
        DataFrame con score de calidad NLP
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            o.empresa,
            o.descripcion,
            o.scrapeado_en,
            LENGTH(o.descripcion) as desc_length,
            n.experiencia_min_anios,
            n.nivel_educativo,
            n.soft_skills_list,
            n.skills_tecnicas_list,
            n.idioma_principal,
            CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END as tiene_salario,
            n.jornada_laboral,
            n.nlp_extraction_timestamp,
            n.nlp_version,
            n.nlp_confidence_score
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.descripcion IS NOT NULL AND o.descripcion != ''
        ORDER BY o.scrapeado_en DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Calcular score de calidad (0-7 campos presentes)
    df['score_calidad'] = (
        df['experiencia_min_anios'].notna().astype(int) +
        df['nivel_educativo'].notna().astype(int) +
        (df['soft_skills_list'].notna() & (df['soft_skills_list'] != '[]')).astype(int) +
        (df['skills_tecnicas_list'].notna() & (df['skills_tecnicas_list'] != '[]')).astype(int) +
        df['idioma_principal'].notna().astype(int) +
        df['tiene_salario'].astype(int) +
        df['jornada_laboral'].notna().astype(int)
    )

    # Categorizar por rango de longitud
    df['rango_longitud'] = pd.cut(
        df['desc_length'],
        bins=[0, 500, 1000, 2000, 5000, float('inf')],
        labels=['<500', '500-1K', '1K-2K', '2K-5K', '>5K']
    )

    if 'scrapeado_en' in df.columns:
        df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'], errors='coerce')

    return df


def calcular_completitud() -> Dict[str, float]:
    """
    Calcula completitud de todos los campos de la tabla ofertas.

    Returns:
        Diccionario {campo: porcentaje_completitud}
    """
    conn = sqlite3.connect(DB_PATH)

    # Obtener total de registros
    query_total = "SELECT COUNT(*) as total FROM ofertas"
    total = pd.read_sql_query(query_total, conn).iloc[0]['total']

    # Obtener nombres de columnas
    query_cols = "PRAGMA table_info(ofertas)"
    cols_df = pd.read_sql_query(query_cols, conn)
    columnas = cols_df['name'].tolist()

    completitud = {}

    for columna in columnas:
        if columna == 'id_oferta':
            continue  # Skip PK

        query = f"""
            SELECT COUNT(*) as completos
            FROM ofertas
            WHERE {columna} IS NOT NULL AND {columna} != ''
        """
        completos = pd.read_sql_query(query, conn).iloc[0]['completos']
        completitud[columna] = (completos / total * 100) if total > 0 else 0

    conn.close()
    return completitud


def cargar_lista_tablas() -> pd.DataFrame:
    """
    Carga lista de todas las tablas en la base de datos.

    Returns:
        DataFrame con nombre y tipo de tablas
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            name,
            type
        FROM sqlite_master
        WHERE type IN ('table', 'view')
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_tabla_generica(tabla_nombre: str, limit: int = 100) -> Tuple[pd.DataFrame, int, int]:
    """
    Carga datos de cualquier tabla.

    Args:
        tabla_nombre: Nombre de la tabla
        limit: Número máximo de filas

    Returns:
        Tupla (DataFrame, total_registros, total_columnas)
    """
    conn = sqlite3.connect(DB_PATH)

    # Obtener total de registros
    query_total = f"SELECT COUNT(*) as total FROM {tabla_nombre}"
    total_registros = pd.read_sql_query(query_total, conn).iloc[0]['total']

    # Obtener datos
    query = f"SELECT * FROM {tabla_nombre} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)

    conn.close()

    total_columnas = len(df.columns)

    return df, total_registros, total_columnas


def cargar_ids_rastreados() -> Dict:
    """
    Carga IDs rastreados desde archivo JSON.

    Returns:
        Diccionario con IDs rastreados
    """
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {'ids': []}


# ==============================================================================
# 2. FUNCIONES PIPELINE (NUEVAS - PRIORIDAD #1)
# ==============================================================================

def cargar_pipeline_metrics() -> Dict[str, any]:
    """
    Carga métricas completas del pipeline end-to-end.

    Returns:
        Diccionario con métricas de cada etapa:
        - scraping: ofertas, success_rate, tiempo promedio, etc.
        - nlp: ofertas procesadas, score promedio, tiempo, etc.
        - esco: ofertas matcheadas, score promedio, skills, etc.
        - calidad_global: pipeline completeness, data quality index
    """
    conn = sqlite3.connect(DB_PATH)

    metrics = {}

    # === SCRAPING ===
    query_scraping = """
        SELECT
            COUNT(DISTINCT id_oferta) as total_ofertas,
            COUNT(DISTINCT CASE WHEN DATE(scrapeado_en) = DATE('now') THEN id_oferta END) as ofertas_hoy,
            COUNT(DISTINCT CASE WHEN DATE(scrapeado_en) >= DATE('now', '-7 days') THEN id_oferta END) as ofertas_semana
        FROM ofertas
    """
    scraping_data = pd.read_sql_query(query_scraping, conn).iloc[0].to_dict()

    # Success rate de última ejecución
    query_success = """
        SELECT success_rate, total_time_seconds
        FROM metricas_scraping
        ORDER BY start_time DESC
        LIMIT 1
    """
    last_exec = pd.read_sql_query(query_success, conn)
    if not last_exec.empty:
        scraping_data['success_rate_ultima'] = last_exec.iloc[0]['success_rate']
        scraping_data['tiempo_ultima_ejecucion'] = last_exec.iloc[0]['total_time_seconds']
    else:
        scraping_data['success_rate_ultima'] = None
        scraping_data['tiempo_ultima_ejecucion'] = None

    metrics['scraping'] = scraping_data

    # === NLP ===
    query_nlp = """
        SELECT
            COUNT(*) as total_procesadas,
            AVG(
                (CASE WHEN experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN nivel_educativo IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN soft_skills_list IS NOT NULL AND soft_skills_list != '[]' THEN 1 ELSE 0 END) +
                (CASE WHEN skills_tecnicas_list IS NOT NULL AND skills_tecnicas_list != '[]' THEN 1 ELSE 0 END) +
                (CASE WHEN idioma_principal IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN salario_min IS NOT NULL OR salario_max IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN jornada_laboral IS NOT NULL THEN 1 ELSE 0 END)
            ) as score_promedio
        FROM ofertas_nlp
    """
    nlp_data = pd.read_sql_query(query_nlp, conn).iloc[0].to_dict()

    # Porcentaje de ofertas con NLP
    total_ofertas = scraping_data['total_ofertas']
    nlp_data['porcentaje_procesadas'] = (nlp_data['total_procesadas'] / total_ofertas * 100) if total_ofertas > 0 else 0

    metrics['nlp'] = nlp_data

    # === ESCO ===
    query_esco = """
        SELECT
            COUNT(*) as total_matcheadas,
            AVG(occupation_match_score) as match_score_promedio,
            SUM(skills_demandados_total) as total_skills,
            SUM(skills_matcheados_esco) as total_skills_matcheados
        FROM ofertas_esco_matching
        WHERE esco_occupation_uri IS NOT NULL
    """
    esco_data = pd.read_sql_query(query_esco, conn)

    if not esco_data.empty:
        esco_metrics = esco_data.iloc[0].to_dict()
        esco_metrics['porcentaje_matcheadas'] = (esco_metrics['total_matcheadas'] / total_ofertas * 100) if total_ofertas > 0 else 0

        # Cobertura del diccionario argentino
        query_dict_arg = "SELECT COUNT(*) as total FROM diccionario_arg_esco"
        dict_count = pd.read_sql_query(query_dict_arg, conn).iloc[0]['total']
        esco_metrics['terminos_diccionario_arg'] = dict_count
    else:
        esco_metrics = {
            'total_matcheadas': 0,
            'match_score_promedio': 0,
            'total_skills': 0,
            'total_skills_matcheados': 0,
            'porcentaje_matcheadas': 0,
            'terminos_diccionario_arg': 0
        }

    metrics['esco'] = esco_metrics

    # === CALIDAD GLOBAL ===
    # Ofertas con datos en TODAS las etapas (scraping + NLP + ESCO)
    query_completeness = """
        SELECT COUNT(*) as completas
        FROM ofertas o
        INNER JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        INNER JOIN ofertas_esco_matching e ON o.id_oferta = e.id_oferta
        WHERE e.esco_occupation_uri IS NOT NULL
    """
    completeness_data = pd.read_sql_query(query_completeness, conn).iloc[0]

    pipeline_completeness = (completeness_data['completas'] / total_ofertas * 100) if total_ofertas > 0 else 0

    # Data Quality Index (promedio ponderado)
    data_quality_index = (
        scraping_data.get('success_rate_ultima', 0) * 0.3 +
        nlp_data.get('score_promedio', 0) / 7 * 100 * 0.3 +
        esco_metrics.get('match_score_promedio', 0) * 100 * 0.4
    ) if scraping_data.get('success_rate_ultima') is not None else 0

    # Alertas activas
    query_alertas = """
        SELECT
            level,
            COUNT(*) as count
        FROM alertas
        WHERE timestamp >= DATETIME('now', '-24 hours')
        GROUP BY level
    """
    alertas_df = pd.read_sql_query(query_alertas, conn)
    alertas_dict = dict(zip(alertas_df['level'], alertas_df['count']))

    metrics['calidad_global'] = {
        'pipeline_completeness_rate': pipeline_completeness,
        'data_quality_index': data_quality_index,
        'alertas_criticas': alertas_dict.get('ERROR', 0) + alertas_dict.get('CRITICAL', 0),
        'alertas_advertencias': alertas_dict.get('WARNING', 0)
    }

    conn.close()
    return metrics


def cargar_ofertas_con_problemas_pipeline() -> pd.DataFrame:
    """
    Carga ofertas que pasaron scraping pero fallaron en NLP o ESCO.

    Returns:
        DataFrame con ofertas problemáticas
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            o.empresa,
            o.scrapeado_en,
            CASE
                WHEN n.id_oferta IS NULL THEN 'NLP NO PROCESADO'
                WHEN e.id_oferta IS NULL THEN 'ESCO NO MATCHEADO'
                WHEN e.esco_occupation_uri IS NULL THEN 'ESCO SIN OCUPACIÓN'
                ELSE 'OK'
            END as etapa_fallida,
            CASE
                WHEN n.id_oferta IS NULL THEN 'Oferta no procesada por NLP'
                WHEN e.id_oferta IS NULL THEN 'Oferta no matcheada con ESCO'
                WHEN e.esco_occupation_uri IS NULL THEN 'No se encontró ocupación ESCO'
                ELSE NULL
            END as razon
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching e ON o.id_oferta = e.id_oferta
        WHERE n.id_oferta IS NULL
           OR e.id_oferta IS NULL
           OR e.esco_occupation_uri IS NULL
        ORDER BY o.scrapeado_en DESC
        LIMIT 100
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'scrapeado_en' in df.columns:
        df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'], errors='coerce')

    return df


def cargar_pipeline_temporal() -> pd.DataFrame:
    """
    Carga evolución temporal del pipeline (por día).

    Returns:
        DataFrame con métricas diarias de cada etapa
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        WITH fechas AS (
            SELECT DISTINCT DATE(scrapeado_en) as fecha
            FROM ofertas
            WHERE scrapeado_en >= DATE('now', '-30 days')
        )
        SELECT
            f.fecha,
            COUNT(DISTINCT o.id_oferta) as ofertas_scrapeadas,
            COUNT(DISTINCT n.id_oferta) as ofertas_nlp,
            COUNT(DISTINCT CASE WHEN e.esco_occupation_uri IS NOT NULL THEN e.id_oferta END) as ofertas_esco,
            AVG(
                (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END) +
                (CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END) +
                (CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END)
            ) * 100 / 7 as calidad_nlp_pct,
            AVG(e.occupation_match_score) * 100 as calidad_esco_pct
        FROM fechas f
        LEFT JOIN ofertas o ON DATE(o.scrapeado_en) = f.fecha
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching e ON o.id_oferta = e.id_oferta
        GROUP BY f.fecha
        ORDER BY f.fecha DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    return df


def cargar_cobertura_scraping() -> Dict[str, any]:
    """
    Calcula cobertura de scraping vs total disponible en servidor Bumeran.

    Compara ofertas scrapeadas en BD con total disponible reportado por la API
    de Bumeran para determinar qué tan cerca estamos del 100% de cobertura.

    Returns:
        Diccionario con:
        - total_servidor: Total de ofertas disponibles en Bumeran (API)
        - total_scrapeado: Total de ofertas en nuestra BD
        - cobertura_pct: Porcentaje de cobertura (0-100)
        - ofertas_faltantes: Diferencia entre servidor y scrapeado
        - estado: 'CRITICO' (<60%), 'ADVERTENCIA' (60-90%), 'OPTIMO' (>90%)
        - timestamp: Fecha/hora de última actualización de cobertura
        - fuente: 'json' o 'database' según origen del dato de servidor
    """
    import glob
    from datetime import datetime

    conn = sqlite3.connect(DB_PATH)

    # Total scrapeado (nuestra base de datos)
    query_scrapeado = "SELECT COUNT(*) as total FROM ofertas"
    total_scrapeado = int(pd.read_sql_query(query_scrapeado, conn).iloc[0]['total'])

    conn.close()

    # Total servidor (buscar en archivos de cobertura más recientes)
    cobertura_dir = Path('01_sources/bumeran/data/metrics')
    total_servidor = None
    timestamp = None
    fuente = 'unknown'

    if cobertura_dir.exists():
        # Buscar archivos de cobertura ordenados por fecha (más reciente primero)
        pattern = str(cobertura_dir / 'cobertura_*.json')
        archivos_cobertura = sorted(glob.glob(pattern), reverse=True)

        if archivos_cobertura:
            try:
                # Leer el archivo más reciente
                with open(archivos_cobertura[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)

                total_servidor = data.get('total_api', 0)
                timestamp = data.get('timestamp', '')
                fuente = 'json'
            except Exception as e:
                # Si falla lectura JSON, usar fallback
                total_servidor = None
                fuente = 'error'

    # Fallback: si no hay datos de servidor, asumir que scrapeado = 100%
    if total_servidor is None or total_servidor == 0:
        total_servidor = total_scrapeado
        fuente = 'fallback'
        timestamp = datetime.now().isoformat()

    # Calcular métricas
    cobertura_pct = (total_scrapeado / total_servidor * 100) if total_servidor > 0 else 0
    ofertas_faltantes = max(0, total_servidor - total_scrapeado)

    # Determinar estado
    if cobertura_pct < 60:
        estado = 'CRITICO'
    elif cobertura_pct < 90:
        estado = 'ADVERTENCIA'
    else:
        estado = 'OPTIMO'

    return {
        'total_servidor': total_servidor,
        'total_scrapeado': total_scrapeado,
        'cobertura_pct': round(cobertura_pct, 2),
        'ofertas_faltantes': ofertas_faltantes,
        'estado': estado,
        'timestamp': timestamp,
        'fuente': fuente
    }


def cargar_cobertura_temporal(dias: int = 30) -> pd.DataFrame:
    """
    Carga evolución temporal de la cobertura de scraping (últimos N días).

    Calcula el acumulado de ofertas scrapeadas por día, permitiendo visualizar
    cómo crece la base de datos hacia el objetivo del 100% de cobertura.

    Args:
        dias: Número de días hacia atrás a consultar (default: 30)

    Returns:
        DataFrame con columnas:
        - fecha: Fecha (datetime)
        - ofertas_del_dia: Ofertas scrapeadas ese día específico
        - ofertas_acumuladas: Total acumulado de ofertas hasta esa fecha
    """
    conn = sqlite3.connect(DB_PATH)

    query = f"""
        SELECT
            DATE(scrapeado_en) as fecha,
            COUNT(*) as ofertas_del_dia
        FROM ofertas
        WHERE scrapeado_en >= DATE('now', '-{dias} days')
        GROUP BY DATE(scrapeado_en)
        ORDER BY fecha
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        # Si no hay datos, retornar DataFrame vacío con estructura correcta
        return pd.DataFrame(columns=['fecha', 'ofertas_del_dia', 'ofertas_acumuladas'])

    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Calcular acumulado
    df['ofertas_acumuladas'] = df['ofertas_del_dia'].cumsum()

    return df


def cargar_cobertura_temporal_completa(dias: int = 30) -> pd.DataFrame:
    """
    Carga evolución temporal COMPLETA de cobertura: disponibles en Bumeran Y scrapeadas.

    Lee archivos JSON históricos de cobertura (con total_api de Bumeran) y combina
    con datos de scraping de la BD para mostrar ambas series temporales evolutivas.

    Args:
        dias: Número de días hacia atrás a consultar (default: 30)

    Returns:
        DataFrame con columnas:
        - fecha: Fecha (datetime)
        - total_api: Total ofertas disponibles en Bumeran ese día
        - total_scrapeado: Total ofertas scrapeadas acumuladas hasta ese día
        - gap: Diferencia (total_api - total_scrapeado)
        - cobertura_pct: Porcentaje de cobertura
    """
    import glob
    from datetime import datetime, timedelta

    # Directorio de archivos de cobertura
    cobertura_dir = Path('01_sources/bumeran/data/metrics')

    if not cobertura_dir.exists():
        return pd.DataFrame(columns=['fecha', 'total_api', 'total_scrapeado', 'gap', 'cobertura_pct'])

    # Buscar archivos de cobertura
    pattern = str(cobertura_dir / 'cobertura_*.json')
    archivos_cobertura = sorted(glob.glob(pattern))

    if not archivos_cobertura:
        return pd.DataFrame(columns=['fecha', 'total_api', 'total_scrapeado', 'gap', 'cobertura_pct'])

    # Leer todos los archivos JSON
    data_list = []
    for archivo in archivos_cobertura:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraer timestamp y convertir a fecha
            timestamp_str = data.get('timestamp', '')
            if timestamp_str:
                fecha = pd.to_datetime(timestamp_str).date()

                data_list.append({
                    'fecha': fecha,
                    'total_api': data.get('total_api', 0),
                    'total_scrapeado': data.get('total_scrapeado', 0),
                    'cobertura_pct': data.get('cobertura_pct', 0),
                    'ofertas_faltantes': data.get('ofertas_faltantes', 0)
                })
        except Exception:
            continue

    if not data_list:
        return pd.DataFrame(columns=['fecha', 'total_api', 'total_scrapeado', 'gap', 'cobertura_pct'])

    # Crear DataFrame
    df = pd.DataFrame(data_list)

    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Calcular gap
    df['gap'] = df['total_api'] - df['total_scrapeado']

    # Ordenar por fecha
    df = df.sort_values('fecha')

    # Filtrar últimos N días
    fecha_limite = pd.Timestamp.now() - timedelta(days=dias)
    df = df[df['fecha'] >= fecha_limite]

    # Eliminar duplicados (mantener el más reciente de cada día)
    df = df.drop_duplicates(subset=['fecha'], keep='last')

    return df


# ===============================================================================
# SECCIÓN 3: FUNCIONES ESCO ANALYTICS (Nuevas - Prioridad Alta)
# ===============================================================================

def cargar_esco_ocupaciones_top(limit: int = 20) -> pd.DataFrame:
    """
    Carga las ocupaciones ESCO más demandadas.

    Args:
        limit: Número de ocupaciones a retornar

    Returns:
        DataFrame con ocupaciones top y métricas
    """
    conn = sqlite3.connect(DB_PATH)

    query = f"""
        SELECT
            em.esco_occupation_uri,
            o.preferredLabel as ocupacion,
            o.isco_code,
            o.isco_group,
            COUNT(DISTINCT em.id_oferta) as ofertas_count,
            AVG(em.occupation_match_score) as match_score_promedio,
            COUNT(DISTINCT sd.skill_uri) as skills_asociadas,
            GROUP_CONCAT(DISTINCT of.provincia) as provincias
        FROM ofertas_esco_matching em
        INNER JOIN esco_occupations o ON em.esco_occupation_uri = o.uri
        LEFT JOIN ofertas_esco_skills_detalle sd ON em.id_oferta = sd.id_oferta
        LEFT JOIN ofertas of ON em.id_oferta = of.id_oferta
        WHERE em.esco_occupation_uri IS NOT NULL
        GROUP BY em.esco_occupation_uri, o.preferredLabel, o.isco_code, o.isco_group
        ORDER BY ofertas_count DESC
        LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_esco_skills_top(limit: int = 30) -> pd.DataFrame:
    """
    Carga las skills ESCO más demandadas.

    Args:
        limit: Número de skills a retornar

    Returns:
        DataFrame con skills top y métricas
    """
    conn = sqlite3.connect(DB_PATH)

    query = f"""
        SELECT
            sd.skill_uri,
            s.preferredLabel as skill,
            s.skillType as tipo,
            COUNT(DISTINCT sd.id_oferta) as ofertas_count,
            AVG(sd.match_score) as match_score_promedio,
            COUNT(DISTINCT em.esco_occupation_uri) as ocupaciones_relacionadas,
            sd.es_esencial,
            COUNT(CASE WHEN sd.es_esencial = 1 THEN 1 END) as veces_esencial,
            COUNT(CASE WHEN sd.es_opcional = 1 THEN 1 END) as veces_opcional
        FROM ofertas_esco_skills_detalle sd
        LEFT JOIN esco_skills s ON sd.skill_uri = s.uri
        LEFT JOIN ofertas_esco_matching em ON sd.id_oferta = em.id_oferta
        WHERE sd.skill_uri IS NOT NULL
        GROUP BY sd.skill_uri, s.preferredLabel, s.skillType, sd.es_esencial
        ORDER BY ofertas_count DESC
        LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_esco_matching_quality() -> Dict[str, any]:
    """
    Carga métricas de calidad del matching ESCO.

    Returns:
        Dict con estadísticas de calidad
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    metrics = {}

    # Total ofertas matcheadas
    cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching WHERE esco_occupation_uri IS NOT NULL")
    metrics['ofertas_matcheadas'] = cursor.fetchone()[0]

    # Distribución de match scores
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            AVG(occupation_match_score) as score_promedio,
            MIN(occupation_match_score) as score_min,
            MAX(occupation_match_score) as score_max,
            COUNT(CASE WHEN occupation_match_score >= 0.8 THEN 1 END) as alta_confianza,
            COUNT(CASE WHEN occupation_match_score >= 0.6 AND occupation_match_score < 0.8 THEN 1 END) as media_confianza,
            COUNT(CASE WHEN occupation_match_score < 0.6 THEN 1 END) as baja_confianza
        FROM ofertas_esco_matching
        WHERE esco_occupation_uri IS NOT NULL
    """)

    row = cursor.fetchone()
    metrics['score_stats'] = {
        'total': row[0],
        'promedio': row[1],
        'min': row[2],
        'max': row[3],
        'alta_confianza': row[4],
        'media_confianza': row[5],
        'baja_confianza': row[6]
    }

    # Total skills identificadas
    cursor.execute("SELECT COUNT(DISTINCT skill_uri) FROM ofertas_esco_skills_detalle")
    metrics['skills_unicas'] = cursor.fetchone()[0]

    # Skills esenciales vs opcionales
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN es_esencial = 1 THEN 1 END) as esenciales,
            COUNT(CASE WHEN es_opcional = 1 THEN 1 END) as opcionales
        FROM ofertas_esco_skills_detalle
    """)
    row = cursor.fetchone()
    metrics['skills_breakdown'] = {
        'esenciales': row[0],
        'opcionales': row[1]
    }

    # Gap analysis: ofertas sin matching
    cursor.execute("""
        SELECT COUNT(*)
        FROM ofertas o
        LEFT JOIN ofertas_esco_matching e ON o.id_oferta = e.id_oferta
        WHERE e.id_oferta IS NULL
    """)
    metrics['ofertas_sin_match'] = cursor.fetchone()[0]

    conn.close()
    return metrics


def cargar_esco_skills_sin_match() -> pd.DataFrame:
    """
    Carga skills extraídas por NLP que no fueron matcheadas con ESCO.

    Returns:
        DataFrame con skills no matcheadas (gap analysis)
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            n.id_oferta,
            o.titulo,
            n.skills_tecnicas_list,
            n.soft_skills_list,
            e.esco_occupation_uri
        FROM ofertas_nlp n
        INNER JOIN ofertas o ON n.id_oferta = o.id_oferta
        LEFT JOIN ofertas_esco_matching e ON n.id_oferta = e.id_oferta
        WHERE (n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]')
           OR (n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]')
        ORDER BY o.scrapeado_en DESC
        LIMIT 100
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_esco_jerarquia() -> pd.DataFrame:
    """
    Carga jerarquía ISCO para navegación en árbol.

    Returns:
        DataFrame con códigos ISCO y conteo de ofertas
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            o.isco_code,
            o.isco_group,
            COUNT(DISTINCT em.id_oferta) as ofertas_count,
            COUNT(DISTINCT o.uri) as ocupaciones_count,
            GROUP_CONCAT(DISTINCT o.preferredLabel, '; ') as ocupaciones_ejemplo
        FROM esco_occupations o
        LEFT JOIN ofertas_esco_matching em ON o.uri = em.esco_occupation_uri
        WHERE o.isco_code IS NOT NULL
        GROUP BY o.isco_code, o.isco_group
        ORDER BY o.isco_code
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_esco_ocupacion_detalle(occupation_uri: str) -> Dict[str, any]:
    """
    Carga detalle completo de una ocupación ESCO.

    Args:
        occupation_uri: URI de la ocupación ESCO

    Returns:
        Dict con información completa de la ocupación
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    detalle = {}

    # Info básica de la ocupación
    cursor.execute("""
        SELECT
            uri,
            preferredLabel,
            altLabels,
            description,
            isco_code,
            isco_group
        FROM esco_occupations
        WHERE uri = ?
    """, (occupation_uri,))

    row = cursor.fetchone()
    if row:
        detalle['info'] = {
            'uri': row[0],
            'nombre': row[1],
            'alternativas': row[2],
            'descripcion': row[3],
            'isco_code': row[4],
            'isco_group': row[5]
        }

    # Ofertas asociadas
    cursor.execute("""
        SELECT COUNT(*)
        FROM ofertas_esco_matching
        WHERE esco_occupation_uri = ?
    """, (occupation_uri,))
    detalle['ofertas_count'] = cursor.fetchone()[0]

    # Skills esenciales para esta ocupación
    cursor.execute("""
        SELECT
            s.preferredLabel,
            COUNT(DISTINCT sd.id_oferta) as veces_solicitada,
            AVG(sd.match_score) as match_score_promedio
        FROM ofertas_esco_skills_detalle sd
        INNER JOIN ofertas_esco_matching em ON sd.id_oferta = em.id_oferta
        LEFT JOIN esco_skills s ON sd.skill_uri = s.uri
        WHERE em.esco_occupation_uri = ?
          AND sd.es_esencial = 1
        GROUP BY s.preferredLabel
        ORDER BY veces_solicitada DESC
        LIMIT 10
    """, (occupation_uri,))

    detalle['skills_esenciales'] = [
        {'skill': row[0], 'veces': row[1], 'score': row[2]}
        for row in cursor.fetchall()
    ]

    conn.close()
    return detalle


def cargar_esco_ocupaciones_por_provincia() -> pd.DataFrame:
    """
    Carga distribución geográfica de ocupaciones ESCO.

    Returns:
        DataFrame con ocupaciones por provincia
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            o.provincia,
            oc.preferredLabel as ocupacion,
            em.esco_occupation_uri,
            COUNT(DISTINCT em.id_oferta) as ofertas_count
        FROM ofertas o
        INNER JOIN ofertas_esco_matching em ON o.id_oferta = em.id_oferta
        LEFT JOIN esco_occupations oc ON em.esco_occupation_uri = oc.uri
        WHERE o.provincia IS NOT NULL
          AND em.esco_occupation_uri IS NOT NULL
        GROUP BY o.provincia, oc.preferredLabel, em.esco_occupation_uri
        ORDER BY o.provincia, ofertas_count DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def cargar_diccionario_arg_stats() -> Dict[str, any]:
    """
    Carga estadísticas de uso del diccionario argentino.

    Returns:
        Dict con métricas del diccionario
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}

    # Total términos en diccionario
    cursor.execute("SELECT COUNT(*) FROM diccionario_arg_esco")
    stats['total_terminos'] = cursor.fetchone()[0]

    # Términos por tipo
    cursor.execute("""
        SELECT tipo, COUNT(*) as count
        FROM diccionario_arg_esco
        GROUP BY tipo
    """)
    stats['por_tipo'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Cobertura (términos usados en matching)
    # Esto requeriría un campo de tracking que no tenemos aún
    # Por ahora devolvemos estructura vacía
    stats['cobertura'] = {
        'terminos_usados': 0,
        'terminos_no_usados': stats['total_terminos']
    }

    conn.close()
    return stats


def cargar_esco_temporal() -> pd.DataFrame:
    """
    Carga evolución temporal de ocupaciones ESCO (trending).

    Returns:
        DataFrame con ocupaciones por fecha
    """
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            DATE(o.scrapeado_en) as fecha,
            oc.preferredLabel as ocupacion,
            em.esco_occupation_uri,
            COUNT(DISTINCT em.id_oferta) as ofertas_count
        FROM ofertas o
        INNER JOIN ofertas_esco_matching em ON o.id_oferta = em.id_oferta
        LEFT JOIN esco_occupations oc ON em.esco_occupation_uri = oc.uri
        WHERE o.scrapeado_en >= DATE('now', '-30 days')
          AND em.esco_occupation_uri IS NOT NULL
        GROUP BY DATE(o.scrapeado_en), oc.preferredLabel, em.esco_occupation_uri
        ORDER BY fecha DESC, ofertas_count DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    return df


def cargar_esco_associations(occupation_uri: str = None, skill_uri: str = None) -> pd.DataFrame:
    """
    Carga asociaciones ocupación-skill desde ESCO.

    Args:
        occupation_uri: Filtrar por ocupación (opcional)
        skill_uri: Filtrar por skill (opcional)

    Returns:
        DataFrame con asociaciones
    """
    conn = sqlite3.connect(DB_PATH)

    where_clauses = []
    params = []

    if occupation_uri:
        where_clauses.append("occupation_uri = ?")
        params.append(occupation_uri)

    if skill_uri:
        where_clauses.append("skill_uri = ?")
        params.append(skill_uri)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    query = f"""
        SELECT
            a.occupation_uri,
            o.preferredLabel as ocupacion,
            a.skill_uri,
            s.preferredLabel as skill,
            a.relationType as tipo_relacion
        FROM esco_associations a
        LEFT JOIN esco_occupations o ON a.occupation_uri = o.uri
        LEFT JOIN esco_skills s ON a.skill_uri = s.uri
        WHERE {where_sql}
        LIMIT 500
    """

    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


# ===============================================================================
# SECCIÓN 4: FUNCIONES OPERACIONALES (Circuit Breaker, Rate Limiter)
# ===============================================================================

def cargar_circuit_breaker_stats() -> pd.DataFrame:
    """
    Carga estadísticas del Circuit Breaker.

    Returns:
        DataFrame con métricas de circuit breaker
    """
    conn = sqlite3.connect(DB_PATH)

    # Verificar si tabla existe
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='circuit_breaker_stats'
    """)

    if not cursor.fetchone():
        conn.close()
        return pd.DataFrame()  # Tabla no existe aún

    query = """
        SELECT
            timestamp,
            estado,
            fallos_consecutivos,
            total_requests,
            total_fallos,
            ultimo_error
        FROM circuit_breaker_stats
        ORDER BY timestamp DESC
        LIMIT 100
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    return df


def cargar_rate_limiter_stats() -> pd.DataFrame:
    """
    Carga estadísticas del Rate Limiter.

    Returns:
        DataFrame con métricas de rate limiting
    """
    conn = sqlite3.connect(DB_PATH)

    # Verificar si tabla existe
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='rate_limiter_stats'
    """)

    if not cursor.fetchone():
        conn.close()
        return pd.DataFrame()  # Tabla no existe aún

    query = """
        SELECT
            timestamp,
            delay_actual,
            requests_last_minute,
            requests_total
        FROM rate_limiter_stats
        ORDER BY timestamp DESC
        LIMIT 100
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    return df


def cargar_circuit_breaker_history() -> Dict[str, any]:
    """
    Carga historial de cambios de estado del Circuit Breaker.

    Returns:
        Dict con métricas históricas
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si tabla existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='circuit_breaker_stats'
    """)

    if not cursor.fetchone():
        conn.close()
        return {'exists': False}

    history = {'exists': True}

    # Conteo por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as count
        FROM circuit_breaker_stats
        GROUP BY estado
    """)
    history['por_estado'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Último estado
    cursor.execute("""
        SELECT estado, fallos_consecutivos, timestamp
        FROM circuit_breaker_stats
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        history['estado_actual'] = {
            'estado': row[0],
            'fallos': row[1],
            'timestamp': row[2]
        }

    conn.close()
    return history


# ===============================================================================
# SECCIÓN 5: FUNCIONES DE UTILIDAD
# ===============================================================================

def get_table_schema(tabla_nombre: str) -> List[Dict[str, str]]:
    """
    Obtiene el schema (columnas y tipos) de una tabla.

    Args:
        tabla_nombre: Nombre de la tabla

    Returns:
        Lista de dicts con info de columnas
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({tabla_nombre})")
        columns = cursor.fetchall()

        schema = [
            {
                'cid': col[0],
                'name': col[1],
                'type': col[2],
                'notnull': bool(col[3]),
                'default_value': col[4],
                'pk': bool(col[5])
            }
            for col in columns
        ]

        return schema

    except sqlite3.Error as e:
        logger.error(f"Error al obtener schema de {tabla_nombre}: {e}")
        return []

    finally:
        conn.close()


def validate_table_name(tabla_nombre: str) -> bool:
    """
    Valida que una tabla exista en la base de datos.

    Args:
        tabla_nombre: Nombre de la tabla a validar

    Returns:
        True si la tabla existe, False en caso contrario
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla_nombre,))

    exists = cursor.fetchone() is not None
    conn.close()

    return exists


def format_number(num: float, decimals: int = 2) -> str:
    """
    Formatea un número para visualización.

    Args:
        num: Número a formatear
        decimals: Decimales a mostrar

    Returns:
        String formateado
    """
    if num is None:
        return 'N/A'

    if abs(num) >= 1_000_000:
        return f"{num/1_000_000:.{decimals}f}M"
    elif abs(num) >= 1_000:
        return f"{num/1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"


def calculate_percentage(parte: float, total: float, decimals: int = 1) -> float:
    """
    Calcula porcentaje con manejo de división por cero.

    Args:
        parte: Valor parcial
        total: Valor total
        decimals: Decimales a redondear

    Returns:
        Porcentaje calculado o 0 si total es 0
    """
    if total == 0 or total is None:
        return 0.0

    return round((parte / total) * 100, decimals)


# ===============================================================================
# FIN DEL MÓDULO data_loaders.py
# ===============================================================================
# Total funciones: ~35
# - Sección 1 (CORE): 9 funciones
# - Sección 2 (PIPELINE): 3 funciones
# - Sección 3 (ESCO): 10 funciones
# - Sección 4 (OPERACIONAL): 3 funciones
# - Sección 5 (UTILIDADES): 4 funciones
# ===============================================================================
