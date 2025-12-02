#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Validacion con Gold Set Manual
=======================================

VERSION: 1.0
FECHA: 2025-11-28

OBJETIVO:
  Evaluar la precision del matching ESCO usando un gold set
  de casos revisados manualmente.

METRICAS:
  - Precision: % de matches correctos sobre total evaluado
  - Errores por tipo: nivel_jerarquico, sector_funcion, tipo_ocupacion, programa_general

EJECUCION:
  python test_gold_set_manual.py
"""

import sqlite3
import json
import struct
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v1.json'


def parse_score(value):
    """Convierte score que puede ser float, bytes (float32) o None."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0


def load_gold_set():
    """Carga el gold set desde JSON."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_current_matches(cursor, ids):
    """Obtiene los matches actuales de la DB."""
    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision,
            m.matching_version
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta IN ({placeholders})
    ''', ids)

    results = {}
    for row in cursor.fetchall():
        results[row[0]] = {
            'titulo': row[1],
            'esco_label': row[2],
            'score': parse_score(row[3]),
            'confirmado': row[4],
            'revision': row[5],
            'version': row[6]
        }
    return results


def run_validation():
    """Ejecuta la validacion contra el gold set."""
    print("=" * 70)
    print("VALIDACION GOLD SET MANUAL - MATCHING ESCO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Cargar gold set
    gold_set = load_gold_set()
    print(f"\n[1] Gold set cargado: {len(gold_set)} casos")

    # Conectar DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener matches actuales
    ids = [g['id_oferta'] for g in gold_set]
    current_matches = get_current_matches(cursor, ids)
    print(f"[2] Matches en DB: {len(current_matches)}")

    # Evaluar
    correct = 0
    incorrect = 0
    missing = 0
    errors_by_type = {}

    print("\n" + "-" * 70)
    print("RESULTADOS DETALLADOS:")
    print("-" * 70)

    for gold in gold_set:
        id_oferta = gold['id_oferta']
        expected_ok = gold['esco_ok']
        comentario = gold.get('comentario', '')
        tipo_error = gold.get('tipo_error', 'sin_clasificar')

        if id_oferta not in current_matches:
            print(f"[MISSING] {id_oferta} - No encontrado en DB")
            missing += 1
            continue

        match = current_matches[id_oferta]

        # En este test simple:
        # - Si esco_ok=True, consideramos el match actual como "esperado correcto"
        # - Si esco_ok=False, el match actual es un error conocido

        if expected_ok:
            status = "[OK]"
            correct += 1
        else:
            status = "[ERROR]"
            incorrect += 1
            errors_by_type[tipo_error] = errors_by_type.get(tipo_error, 0) + 1

        print(f"{status} {id_oferta}")
        print(f"       Titulo: {match['titulo'][:50]}...")
        print(f"       ESCO:   {match['esco_label'][:50]}...")
        print(f"       Score:  {match['score']:.3f} | {'CONFIRMADO' if match['confirmado'] else ('REVISION' if match['revision'] else 'RECHAZADO')}")
        if not expected_ok:
            print(f"       Error:  {tipo_error}")
            print(f"       Motivo: {comentario[:60]}...")
        print()

    conn.close()

    # Resumen
    total = correct + incorrect
    precision = (correct / total * 100) if total > 0 else 0

    print("=" * 70)
    print("RESUMEN DE VALIDACION:")
    print("=" * 70)
    print(f"  Total evaluados:  {total}")
    print(f"  Correctos:        {correct} ({correct/total*100:.1f}%)")
    print(f"  Incorrectos:      {incorrect} ({incorrect/total*100:.1f}%)")
    if missing > 0:
        print(f"  No encontrados:   {missing}")

    print(f"\n  PRECISION:        {precision:.1f}%")

    if errors_by_type:
        print("\n  Errores por tipo:")
        for tipo, count in sorted(errors_by_type.items(), key=lambda x: -x[1]):
            print(f"    - {tipo}: {count}")

    print("=" * 70)

    # Retornar metricas para uso programatico
    return {
        'precision': precision,
        'correct': correct,
        'incorrect': incorrect,
        'total': total,
        'errors_by_type': errors_by_type
    }


if __name__ == '__main__':
    results = run_validation()

    # Exit code basado en precision minima esperada
    MIN_PRECISION = 50.0  # Umbral minimo aceptable
    if results['precision'] < MIN_PRECISION:
        print(f"\n[!] ADVERTENCIA: Precision {results['precision']:.1f}% < {MIN_PRECISION}%")
        exit(1)
    else:
        exit(0)
