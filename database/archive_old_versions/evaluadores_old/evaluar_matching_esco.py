#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_matching_esco.py
========================
Script para evaluar la calidad del matching ESCO (Pipeline Híbrido BGE-M3 + ESCO-XLM)

Genera:
1. Análisis estadístico de scores
2. Muestra estratificada para revisión manual
3. CSV exportable para anotación
"""

import sqlite3
import os
import random
import csv
import re
from datetime import datetime
from collections import Counter


def limpiar_texto(texto):
    """Elimina emojis y caracteres no imprimibles del texto"""
    if not texto:
        return ''
    # Elimina emojis y caracteres Unicode especiales
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    texto = emoji_pattern.sub('', texto)
    # Reemplaza caracteres problemáticos
    texto = texto.encode('cp1252', errors='ignore').decode('cp1252')
    return texto

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), 'bumeran_scraping.db')
OUTPUT_DIR = os.path.dirname(__file__)


def conectar_db():
    """Conecta a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def analisis_estadistico(conn):
    """Genera métricas cuantitativas del matching"""
    cursor = conn.cursor()
    print("\n" + "=" * 70)
    print("ANÁLISIS ESTADÍSTICO DEL MATCHING ESCO")
    print("=" * 70)

    # 1. Estadísticas generales
    print("\n[1] ESTADÍSTICAS GENERALES")
    print("-" * 40)

    cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
    total_matches = cursor.fetchone()[0]
    print(f"  Total ofertas matcheadas: {total_matches:,}")

    cursor.execute("""
        SELECT
            MIN(occupation_match_score) as min_score,
            MAX(occupation_match_score) as max_score,
            AVG(occupation_match_score) as avg_score,
            AVG(rerank_score) as avg_rerank
        FROM ofertas_esco_matching
    """)
    stats = cursor.fetchone()
    print(f"  Score BGE-M3 (similarity):")
    print(f"    - Mínimo: {stats['min_score']:.4f}")
    print(f"    - Máximo: {stats['max_score']:.4f}")
    print(f"    - Promedio: {stats['avg_score']:.4f}")
    print(f"  Score ESCO-XLM (rerank): {stats['avg_rerank']:.4f}")

    # 2. Distribución de scores (histograma)
    print("\n[2] DISTRIBUCIÓN DE SCORES (occupation_match_score)")
    print("-" * 40)

    cursor.execute("""
        SELECT
            CASE
                WHEN occupation_match_score < 0.45 THEN '0.40-0.45'
                WHEN occupation_match_score < 0.50 THEN '0.45-0.50'
                WHEN occupation_match_score < 0.55 THEN '0.50-0.55'
                WHEN occupation_match_score < 0.60 THEN '0.55-0.60'
                WHEN occupation_match_score < 0.65 THEN '0.60-0.65'
                WHEN occupation_match_score < 0.70 THEN '0.65-0.70'
                WHEN occupation_match_score < 0.80 THEN '0.70-0.80'
                ELSE '0.80+'
            END as rango,
            COUNT(*) as cantidad
        FROM ofertas_esco_matching
        GROUP BY 1
        ORDER BY 1
    """)

    distribucion = cursor.fetchall()
    print(f"  {'Rango':<12} {'Cantidad':>10} {'%':>8} {'Barra'}")
    print(f"  {'-'*12} {'-'*10} {'-'*8} {'-'*30}")

    for row in distribucion:
        pct = (row['cantidad'] / total_matches) * 100
        bar = '#' * int(pct / 2)
        print(f"  {row['rango']:<12} {row['cantidad']:>10,} {pct:>7.1f}% {bar}")

    # 3. Top 20 ocupaciones más frecuentes
    print("\n[3] TOP 20 OCUPACIONES ESCO MÁS FRECUENTES")
    print("-" * 40)

    cursor.execute("""
        SELECT esco_occupation_label, COUNT(*) as cnt
        FROM ofertas_esco_matching
        GROUP BY esco_occupation_label
        ORDER BY cnt DESC
        LIMIT 20
    """)

    top_ocupaciones = cursor.fetchall()
    print(f"  {'#':>3} {'Ocupación':<55} {'Cant':>6} {'%':>6}")
    print(f"  {'-'*3} {'-'*55} {'-'*6} {'-'*6}")

    for i, row in enumerate(top_ocupaciones, 1):
        label = row['esco_occupation_label'][:52] + '...' if len(row['esco_occupation_label']) > 55 else row['esco_occupation_label']
        pct = (row['cnt'] / total_matches) * 100
        print(f"  {i:>3} {label:<55} {row['cnt']:>6,} {pct:>5.1f}%")

    # 4. Índice de concentración HHI
    print("\n[4] ÍNDICE DE CONCENTRACIÓN (HHI)")
    print("-" * 40)

    cursor.execute("""
        SELECT esco_occupation_label, COUNT(*) as cnt
        FROM ofertas_esco_matching
        GROUP BY esco_occupation_label
    """)

    todas_ocupaciones = cursor.fetchall()
    n_ocupaciones_distintas = len(todas_ocupaciones)

    # Calcular HHI (suma de cuadrados de participación)
    hhi = sum((row['cnt'] / total_matches * 100) ** 2 for row in todas_ocupaciones)

    print(f"  Ocupaciones distintas: {n_ocupaciones_distintas:,}")
    print(f"  Índice HHI: {hhi:.2f}")
    print(f"  Interpretación:")
    if hhi < 100:
        print(f"    -> ALTA DIVERSIDAD (HHI < 100)")
    elif hhi < 1000:
        print(f"    -> DIVERSIDAD MODERADA (100 < HHI < 1000)")
    elif hhi < 2500:
        print(f"    -> CONCENTRACIÓN MODERADA (1000 < HHI < 2500)")
    else:
        print(f"    -> ALTA CONCENTRACIÓN (HHI > 2500)")

    # 5. Comparación con problema anterior (74% en una ocupación)
    max_concentracion = max(row['cnt'] for row in todas_ocupaciones) / total_matches * 100
    print(f"\n  Concentración máxima: {max_concentracion:.1f}%")
    print(f"  (Antes del pipeline híbrido era 74%)")

    return {
        'total_matches': total_matches,
        'min_score': stats['min_score'],
        'max_score': stats['max_score'],
        'avg_score': stats['avg_score'],
        'avg_rerank': stats['avg_rerank'],
        'n_ocupaciones': n_ocupaciones_distintas,
        'hhi': hhi,
        'max_concentracion': max_concentracion
    }


def muestra_estratificada(conn, n_por_rango=10):
    """Extrae ejemplos aleatorios de cada rango de score"""
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("MUESTRA ESTRATIFICADA PARA REVISIÓN MANUAL")
    print("=" * 70)

    rangos = [
        ("BAJO (< 0.50)", 0, 0.50),
        ("MEDIO-BAJO (0.50-0.60)", 0.50, 0.60),
        ("MEDIO-ALTO (0.60-0.70)", 0.60, 0.70),
        ("ALTO (> 0.70)", 0.70, 1.0)
    ]

    todas_muestras = []

    for nombre_rango, min_score, max_score in rangos:
        print(f"\n[{nombre_rango}]")
        print("-" * 60)

        # Obtener IDs en este rango
        cursor.execute("""
            SELECT m.id_oferta, o.titulo, o.descripcion,
                   m.esco_occupation_label, m.occupation_match_score, m.rerank_score
            FROM ofertas_esco_matching m
            JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
            WHERE m.occupation_match_score >= ? AND m.occupation_match_score < ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (min_score, max_score, n_por_rango))

        muestras = cursor.fetchall()

        if not muestras:
            print(f"  (No hay ofertas en este rango)")
            continue

        for i, m in enumerate(muestras, 1):
            # Descripción más larga (500 chars) para mejor evaluación
            desc_raw = (m['descripcion'] or '')[:500].replace('\n', ' ').strip()
            if len(m['descripcion'] or '') > 500:
                desc_raw += '...'
            descripcion_corta = limpiar_texto(desc_raw)

            rerank_str = f"{m['rerank_score']:.4f}" if m['rerank_score'] else 'N/A'
            titulo_limpio = limpiar_texto(m['titulo'])
            esco_limpio = limpiar_texto(m['esco_occupation_label'])

            print(f"\n  [{i}] ID: {m['id_oferta']}")
            print(f"      TITULO OFERTA: {titulo_limpio}")
            print(f"      OCUPACION ESCO: {esco_limpio}")
            print(f"      SCORE BGE-M3: {m['occupation_match_score']:.4f}")
            print(f"      SCORE ESCO-XLM: {rerank_str}")
            print(f"      DESCRIPCION:")
            print(f"      {descripcion_corta}")

            todas_muestras.append({
                'rango': nombre_rango,
                'id_oferta': m['id_oferta'],
                'titulo': m['titulo'],
                'esco_occupation_label': m['esco_occupation_label'],
                'occupation_match_score': m['occupation_match_score'],
                'rerank_score': m['rerank_score'],
                'descripcion': (m['descripcion'] or '')[:1000],  # Más descripción en CSV
                'evaluacion': ''  # Para llenar manualmente
            })

    return todas_muestras


def exportar_csv(muestras, filename='muestra_evaluacion_esco.csv'):
    """Exporta la muestra a CSV para revisión manual"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['rango', 'id_oferta', 'titulo', 'esco_occupation_label',
                      'occupation_match_score', 'rerank_score', 'descripcion',
                      'evaluacion_correcto', 'evaluacion_parcial', 'evaluacion_incorrecto', 'notas']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in muestras:
            row = {
                'rango': m['rango'],
                'id_oferta': m['id_oferta'],
                'titulo': m['titulo'],
                'esco_occupation_label': m['esco_occupation_label'],
                'occupation_match_score': f"{m['occupation_match_score']:.4f}",
                'rerank_score': f"{m['rerank_score']:.4f}" if m['rerank_score'] else '',
                'descripcion': m['descripcion'],
                'evaluacion_correcto': '',
                'evaluacion_parcial': '',
                'evaluacion_incorrecto': '',
                'notas': ''
            }
            writer.writerow(row)

    print(f"\n[OK] CSV exportado: {filepath}")
    return filepath


def main():
    print("\n" + "=" * 70)
    print("EVALUACIÓN DE CALIDAD - MATCHING ESCO")
    print(f"Pipeline: BGE-M3 + ESCO-XLM (Híbrido)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Conectar
    conn = conectar_db()
    print(f"\n[OK] Conectado a: {DB_PATH}")

    # 1. Análisis estadístico
    stats = analisis_estadistico(conn)

    # 2. Muestra estratificada
    muestras = muestra_estratificada(conn, n_por_rango=10)

    # 3. Exportar CSV
    csv_path = exportar_csv(muestras)

    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DE EVALUACIÓN")
    print("=" * 70)
    print(f"  Total ofertas matcheadas: {stats['total_matches']:,}")
    print(f"  Ocupaciones distintas: {stats['n_ocupaciones']}")
    print(f"  Score promedio BGE-M3: {stats['avg_score']:.4f}")
    print(f"  Índice HHI: {stats['hhi']:.2f}")
    print(f"  Concentración máxima: {stats['max_concentracion']:.1f}%")
    print(f"\n  Muestras generadas: {len(muestras)}")
    print(f"  CSV para revisión: {csv_path}")
    print("\n" + "=" * 70)
    print("[OK] EVALUACIÓN COMPLETADA")
    print("=" * 70)

    conn.close()


if __name__ == '__main__':
    main()
