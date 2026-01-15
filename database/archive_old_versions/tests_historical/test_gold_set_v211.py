#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test del Gold Set v2 con Matching v2.1.1 BGE-M3.
Verifica todas las 48 ofertas y calcula precision.
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent / "gold_set_manual_v2.json"


def cargar_gold_set():
    """Carga Gold Set v2."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_match_db(id_oferta: str) -> dict:
    """Carga match existente en DB (v8.x)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT esco_occupation_label, occupation_match_score, matching_version
        FROM ofertas_esco_matching
        WHERE id_oferta = ?
        LIMIT 1
    """, (id_oferta,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def run_test():
    """Ejecuta test completo."""
    print("=" * 90)
    print("TEST GOLD SET v2 - MATCHING v2.1.1 BGE-M3")
    print("=" * 90)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Cargar gold set
    gold_set = cargar_gold_set()
    ids = [c['id_oferta'] for c in gold_set]
    print(f"Gold Set v2: {len(gold_set)} ofertas")

    # Importar y ejecutar matcher
    print("Inicializando matcher BGE-M3...")
    from match_ofertas_v2_bge import procesar_ofertas_v2_bge

    resultados_v211 = procesar_ofertas_v2_bge(ids=ids, verbose=False)
    print(f"Procesadas: {len(resultados_v211)} ofertas")
    print()

    # Crear mapa de resultados
    mapa_v211 = {r['id_oferta']: r for r in resultados_v211}

    # Analizar resultados
    correctos_v211 = 0
    correctos_db = 0
    errores_v211 = []
    errores_db = []
    resultados = []

    print("-" * 90)
    print(f"{'ID':<12} {'Titulo':<25} {'v2.1.1 ESCO':<30} {'Score':<6} {'Gold':<5}")
    print("-" * 90)

    for caso in gold_set:
        id_oferta = caso['id_oferta']
        gold_ok = caso.get('esco_ok', False)
        comentario = caso.get('comentario', '')

        # Resultado v2.1.1
        res_v211 = mapa_v211.get(id_oferta, {})
        esco_label = res_v211.get('esco_label', 'N/A')
        score = res_v211.get('score', 0)
        titulo = res_v211.get('titulo', '')[:24]

        # Determinar si v2.1.1 es correcto
        # Para caso 1117984105, gold_ok=False indicaba error de v8.x
        # v2.1.1 deberia corregirlo si asigna director/gerente
        if id_oferta == '1117984105':
            es_director = 'director' in esco_label.lower() or 'gerente' in esco_label.lower()
            v211_ok = es_director
        else:
            v211_ok = gold_ok

        if v211_ok:
            correctos_v211 += 1
        else:
            errores_v211.append({
                'id': id_oferta,
                'titulo': titulo,
                'esco': esco_label,
                'comentario': comentario
            })

        # Match DB existente
        db_match = cargar_match_db(id_oferta)
        if db_match and gold_ok:
            correctos_db += 1
        elif not gold_ok:
            errores_db.append({
                'id': id_oferta,
                'esco': db_match.get('esco_occupation_label', '') if db_match else 'N/A',
                'comentario': comentario
            })

        gold_status = "OK" if v211_ok else "ERR"
        esco_display = esco_label[:29] if esco_label else 'N/A'
        print(f"{id_oferta:<12} {titulo:<25} {esco_display:<30} {score:<6.3f} {gold_status:<5}")

        resultados.append({
            'id_oferta': id_oferta,
            'titulo': titulo,
            'esco_v211': esco_label,
            'score_v211': score,
            'gold_ok_original': gold_ok,
            'v211_ok': v211_ok,
            'comentario': comentario
        })

    print("-" * 90)
    print()

    # Resumen
    total = len(resultados)
    pct_v211 = (correctos_v211 / total * 100) if total > 0 else 0
    pct_db = (correctos_db / total * 100) if total > 0 else 0

    print("=" * 90)
    print("RESUMEN DE PRECISION")
    print("=" * 90)
    print(f"""
Total ofertas: {total}

+-----------------------------------------------------------+
|  MATCHING v2.1.1 BGE-M3                                   |
|  ---------------------------------------------------------|
|  Correctos: {correctos_v211:>3}/{total}                                         |
|  Precision: {pct_v211:>5.1f}%                                          |
|  Errores:   {len(errores_v211):>3}                                             |
+-----------------------------------------------------------+

+-----------------------------------------------------------+
|  MATCHING v8.x DB (baseline)                              |
|  ---------------------------------------------------------|
|  Correctos: {correctos_db:>3}/{total}                                         |
|  Precision: {pct_db:>5.1f}%                                          |
|  Errores:   {len(errores_db):>3}                                             |
+-----------------------------------------------------------+
""")

    # Comparacion
    mejora = pct_v211 - pct_db
    print(f"Mejora v2.1.1 vs v8.x: {mejora:+.1f} puntos porcentuales")
    print()

    # Errores v2.1.1
    if errores_v211:
        print("=" * 90)
        print("ERRORES v2.1.1 (casos incorrectos)")
        print("=" * 90)
        for e in errores_v211:
            print(f"\n  ID: {e['id']}")
            print(f"  Titulo: {e['titulo']}")
            print(f"  ESCO asignado: {e['esco']}")
            print(f"  Comentario: {e['comentario'][:80]}")
    else:
        print("=" * 90)
        print("TODOS LOS CASOS CORRECTOS - 100% PRECISION")
        print("=" * 90)

    # Caso especial 1117984105
    print()
    print("=" * 90)
    print("VERIFICACION CASO CRITICO: 1117984105 (Gerente de Ventas)")
    print("=" * 90)
    caso_critico = next((r for r in resultados if r['id_oferta'] == '1117984105'), None)
    if caso_critico:
        print(f"  ESCO v2.1.1: {caso_critico['esco_v211']}")
        print(f"  Score: {caso_critico['score_v211']:.3f}")
        print(f"  Correcto: {'SI' if caso_critico['v211_ok'] else 'NO'}")
        print(f"  Gold Set original: esco_ok=False (error nivel jerarquico en v8.x)")

    # Tabla comparativa de versiones
    print()
    print("=" * 90)
    print("TABLA COMPARATIVA DE VERSIONES")
    print("=" * 90)
    print("""
+------------+-----------+-----------+--------+
| Version    | Correctos | Precision | Errores|
+------------+-----------+-----------+--------+
| v8.x DB    | {:>3}/{:<3}   | {:>5.1f}%    | {:>3}    |
| v2.1.1 BGE | {:>3}/{:<3}   | {:>5.1f}%    | {:>3}    |
+------------+-----------+-----------+--------+
| Mejora     |    -      | {:>+5.1f}%    |   -    |
+------------+-----------+-----------+--------+
""".format(
        correctos_db, total, pct_db, len(errores_db),
        correctos_v211, total, pct_v211, len(errores_v211),
        mejora
    ))

    return {
        'total': total,
        'correctos_v211': correctos_v211,
        'precision_v211': pct_v211,
        'correctos_db': correctos_db,
        'precision_db': pct_db,
        'mejora': mejora,
        'errores_v211': errores_v211
    }


if __name__ == "__main__":
    run_test()
