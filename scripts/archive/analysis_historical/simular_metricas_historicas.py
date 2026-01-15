#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Simulación de Métricas Históricas
============================================

Genera métricas históricas realistas basadas en los datos existentes
para poblar las tablas de métricas y poder visualizar el dashboard completo.

Fecha: 2025-10-31
"""

import sqlite3
import pandas as pd
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
import re

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
KEYWORDS_FILE = PROJECT_ROOT / "data" / "config" / "master_keywords.json"

# ============================================================================
# FUNCIONES DE SIMULACIÓN
# ============================================================================

def cargar_keywords():
    """Carga keywords del diccionario v3.2"""
    with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Obtener keywords de la estrategia ultra_exhaustiva_v3_2
    estrategia = data.get('estrategias', {}).get('ultra_exhaustiva_v3_2', {})
    keywords = estrategia.get('keywords', [])

    return keywords

def analizar_keywords_en_ofertas(conn):
    """Analiza qué keywords aparecen en las ofertas existentes"""
    print('Analizando keywords en ofertas...')

    # Cargar ofertas
    df = pd.read_sql_query('SELECT id_oferta, titulo, descripcion FROM ofertas', conn)

    # Cargar keywords
    keywords = cargar_keywords()

    # Contar apariciones
    keyword_counts = {}

    for keyword in keywords:
        # Buscar keyword en títulos y descripciones (case insensitive)
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        count = 0
        for _, row in df.iterrows():
            titulo = str(row['titulo']).lower()
            desc = str(row['descripcion']).lower() if pd.notna(row['descripcion']) else ''

            if pattern.search(titulo) or pattern.search(desc):
                count += 1

        if count > 0:
            keyword_counts[keyword] = count

    print(f'  Keywords encontrados en ofertas: {len(keyword_counts)}')
    print(f'  Keywords sin resultados: {len(keywords) - len(keyword_counts)}')

    return keyword_counts

def simular_metricas_scraping(conn, num_ejecuciones=5):
    """Simula métricas de ejecuciones de scraping"""
    print()
    print('='*70)
    print('SIMULANDO MÉTRICAS DE SCRAPING')
    print('='*70)
    print()

    cursor = conn.cursor()

    # Obtener fecha más antigua de ofertas
    cursor.execute('SELECT MIN(scrapeado_en) FROM ofertas')
    fecha_min_str = cursor.fetchone()[0]
    fecha_min = datetime.fromisoformat(fecha_min_str)

    # Generar 5 ejecuciones simuladas
    ofertas_acumuladas = 0
    total_ofertas = 5479  # Total actual en DB

    for i in range(num_ejecuciones):
        # Calcular fecha de esta ejecución
        dias_atras = (num_ejecuciones - i - 1) * 2  # Cada 2 días
        fecha_ejecucion = datetime.now() - timedelta(days=dias_atras)

        # Simular métricas realistas
        if i == 0:
            # Primera ejecución: muchas ofertas
            ofertas_nuevas = random.randint(2000, 2500)
            ofertas_duplicadas = 0
        elif i == num_ejecuciones - 1:
            # Última ejecución: pocas ofertas (modo incremental)
            ofertas_nuevas = 31  # Dato real del último test
            ofertas_duplicadas = random.randint(100, 200)
        else:
            # Ejecuciones intermedias
            ofertas_nuevas = random.randint(500, 1200)
            ofertas_duplicadas = random.randint(50, 150)

        ofertas_acumuladas += ofertas_nuevas
        ofertas_total = ofertas_nuevas + ofertas_duplicadas

        # Métricas de ejecución
        tiempo_total = random.uniform(10, 20) * 60  # 10-20 minutos en segundos
        pages_scraped = random.randint(800, 1200)
        pages_failed = random.randint(0, 10)
        pages_total = pages_scraped + pages_failed

        start_time = fecha_ejecucion - timedelta(seconds=tiempo_total)

        metrica = {
            'start_time': start_time.isoformat(),
            'end_time': fecha_ejecucion.isoformat(),
            'total_time_seconds': tiempo_total,
            'pages_scraped': pages_scraped,
            'pages_failed': pages_failed,
            'pages_total': pages_total,
            'success_rate': pages_scraped / pages_total * 100,
            'avg_time_per_page': tiempo_total / pages_scraped,
            'offers_total': ofertas_total,
            'offers_new': ofertas_nuevas,
            'offers_duplicates': ofertas_duplicadas,
            'offers_per_second': ofertas_total / tiempo_total,
            'validation_rate_avg': random.uniform(95, 100),
            'validation_rate_min': random.uniform(85, 95),
            'validation_rate_max': 100.0,
            'errors_count': pages_failed,
            'warnings_count': random.randint(0, 5),
            'incremental_mode': 1 if i > 0 else 0,
            'query': f'estrategia_v3.{i}',
            'created_at': fecha_ejecucion.isoformat()
        }

        # Insertar
        cursor.execute('''
            INSERT INTO metricas_scraping (
                start_time, end_time, total_time_seconds,
                pages_scraped, pages_failed, pages_total,
                success_rate, avg_time_per_page,
                offers_total, offers_new, offers_duplicates,
                offers_per_second, validation_rate_avg,
                validation_rate_min, validation_rate_max,
                errors_count, warnings_count,
                incremental_mode, query, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(metrica.values()))

        print(f'  Ejecución {i+1}/{num_ejecuciones}:')
        print(f'    Fecha: {fecha_ejecucion.strftime("%Y-%m-%d %H:%M")}')
        print(f'    Ofertas nuevas: {ofertas_nuevas:,}')
        print(f'    Tiempo: {tiempo_total/60:.1f} min')

    conn.commit()
    print()
    print(f'[OK] {num_ejecuciones} métricas de scraping generadas')

def simular_keywords_performance(conn, keyword_counts):
    """Simula performance de keywords"""
    print()
    print('='*70)
    print('SIMULANDO PERFORMANCE DE KEYWORDS')
    print('='*70)
    print()

    cursor = conn.cursor()

    # Obtener todas las keywords
    keywords_all = cargar_keywords()

    # Generar performance para cada keyword
    registros_generados = 0

    for keyword in keywords_all:
        ofertas_encontradas = keyword_counts.get(keyword, 0)

        # Simular 3 ejecuciones para cada keyword
        for i in range(3):
            dias_atras = (2 - i) * 3  # Cada 3 días
            fecha = datetime.now() - timedelta(days=dias_atras)

            # Simular métricas
            if ofertas_encontradas > 0:
                # Keyword exitoso
                ofertas = random.randint(int(ofertas_encontradas * 0.8), int(ofertas_encontradas * 1.2))
                ofertas_nuevas = random.randint(int(ofertas * 0.6), ofertas)
                ofertas_duplicadas = ofertas - ofertas_nuevas
                tiempo = random.uniform(2, 8)
                exito = 1
            else:
                # Keyword sin resultados
                ofertas = 0
                ofertas_nuevas = 0
                ofertas_duplicadas = 0
                tiempo = random.uniform(1, 3)
                exito = 0

            cursor.execute('''
                INSERT INTO keywords_performance (
                    keyword, estrategia, ofertas_encontradas,
                    ofertas_nuevas, ofertas_duplicadas,
                    tiempo_ejecucion, exito,
                    scraping_date, fuente
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                keyword,
                f'ultra_exhaustiva_v3.{i}',
                ofertas,
                ofertas_nuevas,
                ofertas_duplicadas,
                tiempo,
                exito,
                fecha.isoformat(),
                'bumeran'
            ))

            registros_generados += 1

    conn.commit()

    print(f'[OK] {registros_generados:,} registros de keywords generados')
    print(f'    Keywords productivos: {len(keyword_counts)}')
    print(f'    Keywords sin resultados: {len(keywords_all) - len(keyword_counts)}')

def simular_alertas(conn):
    """Simula alertas del sistema"""
    print()
    print('='*70)
    print('SIMULANDO ALERTAS')
    print('='*70)
    print()

    cursor = conn.cursor()

    alertas_ejemplos = [
        {
            'level': 'INFO',
            'message': 'Sistema de scraping iniciado correctamente',
            'context': json.dumps({'version': 'v3.2', 'keywords': 1148}),
            'created_at': (datetime.now() - timedelta(days=7)).isoformat()
        },
        {
            'level': 'WARNING',
            'message': 'Circuit breaker: 5 fallos consecutivos detectados',
            'context': json.dumps({'keyword': 'blockchain', 'attempts': 5}),
            'created_at': (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            'level': 'WARNING',
            'message': 'Rate limiter: delay aumentado a 10s',
            'context': json.dumps({'reason': 'rate_limit_exceeded', 'new_delay': 10.0}),
            'created_at': (datetime.now() - timedelta(days=4)).isoformat()
        },
        {
            'level': 'INFO',
            'message': 'Scraping completado: 1,248 ofertas nuevas capturadas',
            'context': json.dumps({'ofertas': 1248, 'tiempo': 15.2}),
            'created_at': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'level': 'INFO',
            'message': 'Sistema incremental: 98.5% duplicados filtrados',
            'context': json.dumps({'duplicados': 5432, 'nuevos': 31}),
            'created_at': datetime.now().isoformat()
        }
    ]

    for alerta in alertas_ejemplos:
        cursor.execute('''
            INSERT INTO alertas (level, message, context, created_at)
            VALUES (?, ?, ?, ?)
        ''', (alerta['level'], alerta['message'], alerta['context'], alerta['created_at']))

    conn.commit()

    print(f'[OK] {len(alertas_ejemplos)} alertas generadas')

def generar_reporte(conn):
    """Genera reporte final de simulación"""
    print()
    print('='*70)
    print('REPORTE FINAL')
    print('='*70)
    print()

    cursor = conn.cursor()

    # Métricas
    cursor.execute('SELECT COUNT(*) FROM metricas_scraping')
    total_metricas = cursor.fetchone()[0]

    # Keywords
    cursor.execute('SELECT COUNT(DISTINCT keyword) FROM keywords_performance')
    total_keywords = cursor.fetchone()[0]

    # Alertas
    cursor.execute('SELECT COUNT(*) FROM alertas')
    total_alertas = cursor.fetchone()[0]

    print(f'Datos generados:')
    print(f'  Métricas de scraping:    {total_metricas}')
    print(f'  Keywords performance:    {total_keywords} keywords')
    print(f'  Alertas:                 {total_alertas}')
    print()
    print('[OK] Base de datos poblada exitosamente')
    print()
    print('El dashboard ahora puede mostrar:')
    print('  - Evolución de performance entre scrapings')
    print('  - Keywords más productivos')
    print('  - Alertas y monitoreo del sistema')
    print('  - Eficiencia iterativa')
    print()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    print()
    print('='*70)
    print('SIMULACIÓN DE MÉTRICAS HISTÓRICAS'.center(70))
    print('='*70)
    print()
    print(f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Base de datos: {DB_PATH}')
    print()

    # Conectar a DB
    conn = sqlite3.connect(DB_PATH)

    try:
        # 1. Analizar keywords en ofertas existentes
        keyword_counts = analizar_keywords_en_ofertas(conn)

        # 2. Simular métricas de scraping
        simular_metricas_scraping(conn, num_ejecuciones=5)

        # 3. Simular performance de keywords
        simular_keywords_performance(conn, keyword_counts)

        # 4. Simular alertas
        simular_alertas(conn)

        # 5. Generar reporte
        generar_reporte(conn)

    except Exception as e:
        print(f'[ERROR] {e}')
        conn.rollback()
        return 1
    finally:
        conn.close()

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
