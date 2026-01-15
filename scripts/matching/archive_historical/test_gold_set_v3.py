#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Gold Set v3 - Validacion del pipeline skills-first
========================================================

Compara resultados de match_ofertas_v3 contra el Gold Set manual.
"""

import sqlite3
import json
import sys
import io
from pathlib import Path
from typing import Dict, List, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from match_ofertas_v3 import MatcherV3


def load_gold_set() -> List[Dict]:
    """Carga el Gold Set manual."""
    gold_path = Path(__file__).parent / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_oferta_nlp(conn: sqlite3.Connection, id_oferta: str) -> Dict:
    """Obtiene datos NLP de una oferta."""
    cur = conn.execute('''
        SELECT titulo, titulo_limpio, tareas_explicitas, area_funcional,
               nivel_seniority, sector_empresa
        FROM ofertas_nlp
        WHERE id_aviso = ?
    ''', (id_oferta,))

    row = cur.fetchone()
    if not row:
        return None

    return {
        "titulo": row[0],
        "titulo_limpio": row[1],
        "tareas_explicitas": row[2],
        "area_funcional": row[3],
        "nivel_seniority": row[4],
        "sector_empresa": row[5]
    }


def test_gold_set():
    """Test principal del Gold Set con v3."""
    print("=" * 70)
    print("TEST: Gold Set v3 - Skills First Pipeline")
    print("=" * 70)

    # Cargar Gold Set
    gold_set = load_gold_set()
    print(f"\nGold Set: {len(gold_set)} casos")

    # Conectar a BD
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Inicializar matcher v3
    print("\nInicializando MatcherV3...")
    matcher = MatcherV3(db_conn=conn, verbose=False)

    # Contadores
    total = 0
    correctos = 0
    errores_v21 = 0
    errores_v3 = 0
    corregidos_v3 = 0
    nuevos_errores_v3 = 0
    sin_datos = 0

    # Detalle de errores
    detalles_errores = []
    detalles_corregidos = []

    print("\n" + "-" * 70)

    for caso in gold_set:
        id_oferta = caso["id_oferta"]
        era_ok_v21 = caso.get("esco_ok", True)
        isco_esperado = caso.get("isco_esperado", "")
        comentario = caso.get("comentario", "")

        # Obtener datos NLP
        oferta = get_oferta_nlp(conn, id_oferta)
        if not oferta:
            sin_datos += 1
            continue

        total += 1

        # Ejecutar matching v3
        result = matcher.match(oferta)
        isco_obtenido = result.isco_code or ""

        # Evaluar resultado
        if era_ok_v21:
            # Era correcto en v2.1 - debe seguir correcto
            if result.status != "error":
                correctos += 1
            else:
                nuevos_errores_v3 += 1
                detalles_errores.append({
                    "id": id_oferta,
                    "titulo": oferta.get("titulo_limpio", "")[:40],
                    "isco_v3": isco_obtenido,
                    "tipo": "REGRESION",
                    "comentario": comentario
                })
        else:
            # Era error en v2.1 - verificar si v3 lo corrige
            errores_v21 += 1

            # Comparar ISCO (primeros 4 digitos)
            isco_esp_4 = isco_esperado[:4] if isco_esperado else ""
            isco_obt_4 = isco_obtenido[:4] if isco_obtenido else ""

            if isco_esp_4 == isco_obt_4:
                corregidos_v3 += 1
                correctos += 1
                detalles_corregidos.append({
                    "id": id_oferta,
                    "titulo": oferta.get("titulo_limpio", "")[:40],
                    "isco_esperado": isco_esperado,
                    "isco_v3": isco_obtenido,
                    "metodo": result.metodo
                })
                print(f"[CORREGIDO] {id_oferta}: {oferta.get('titulo_limpio', '')[:35]}")
                print(f"            Esperado: {isco_esperado}, V3: {isco_obtenido} ({result.metodo})")
            else:
                errores_v3 += 1
                detalles_errores.append({
                    "id": id_oferta,
                    "titulo": oferta.get("titulo_limpio", "")[:40],
                    "isco_esperado": isco_esperado,
                    "isco_v3": isco_obtenido,
                    "tipo": "PERSISTE",
                    "metodo": result.metodo
                })
                print(f"[PERSISTE]  {id_oferta}: {oferta.get('titulo_limpio', '')[:35]}")
                print(f"            Esperado: {isco_esperado}, V3: {isco_obtenido}")

    # Cerrar
    matcher.close()
    conn.close()

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total casos evaluados: {total}")
    print(f"Sin datos en BD: {sin_datos}")
    print()
    print(f"Correctos v3: {correctos}/{total} ({100*correctos/total:.1f}%)")
    print(f"Errores v2.1 originales: {errores_v21}")
    print(f"  - Corregidos por v3: {corregidos_v3}")
    print(f"  - Persisten en v3: {errores_v3}")
    print(f"Nuevos errores v3 (regresiones): {nuevos_errores_v3}")

    # Mejora
    if errores_v21 > 0:
        mejora = 100 * corregidos_v3 / errores_v21
        print(f"\nMejora en casos problematicos: {corregidos_v3}/{errores_v21} ({mejora:.1f}%)")

    # Detalle de corregidos
    if detalles_corregidos:
        print("\n" + "-" * 70)
        print("CASOS CORREGIDOS POR V3:")
        print("-" * 70)
        for d in detalles_corregidos:
            print(f"  {d['id']}: {d['titulo']}")
            print(f"    ISCO: {d['isco_esperado']} -> {d['isco_v3']} ({d['metodo']})")

    # Detalle de errores persistentes
    if detalles_errores:
        print("\n" + "-" * 70)
        print("ERRORES PENDIENTES:")
        print("-" * 70)
        for d in detalles_errores:
            print(f"  {d['id']}: {d['titulo']}")
            print(f"    Esperado: {d.get('isco_esperado', 'N/A')}, V3: {d['isco_v3']}")
            print(f"    Tipo: {d['tipo']}")

    return correctos, total


if __name__ == "__main__":
    test_gold_set()
