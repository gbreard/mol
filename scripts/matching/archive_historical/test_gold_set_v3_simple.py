#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Gold Set v3 - Validacion simplificada
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


def load_gold_set() -> List[Dict]:
    """Carga el Gold Set manual."""
    gold_path = Path(__file__).parent / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_oferta_nlp(conn: sqlite3.Connection, id_oferta: str) -> Dict:
    """Obtiene datos NLP de una oferta."""
    cur = conn.execute('''
        SELECT titulo_limpio, tareas_explicitas, area_funcional,
               nivel_seniority, sector_empresa
        FROM ofertas_nlp
        WHERE id_oferta = ?
    ''', (id_oferta,))

    row = cur.fetchone()
    if not row:
        return None

    return {
        "titulo": row[0],  # titulo_limpio as titulo
        "titulo_limpio": row[0],
        "tareas_explicitas": row[1],
        "area_funcional": row[2],
        "nivel_seniority": row[3],
        "sector_empresa": row[4]
    }


def run_test():
    """Test principal del Gold Set con v3."""
    from match_ofertas_v3 import MatcherV3

    results = []
    results.append("=" * 70)
    results.append("TEST: Gold Set v3 - Skills First Pipeline")
    results.append("=" * 70)

    # Cargar Gold Set
    gold_set = load_gold_set()
    results.append(f"\nGold Set: {len(gold_set)} casos")

    # Conectar a BD
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Inicializar matcher v3
    results.append("\nInicializando MatcherV3...")
    matcher = MatcherV3(db_conn=conn, verbose=False)

    # Contadores
    total = 0
    correctos = 0
    errores_v21 = 0
    corregidos_v3 = 0
    errores_v3 = 0
    nuevos_errores_v3 = 0
    sin_datos = 0

    detalles_corregidos = []
    detalles_errores = []

    results.append("\n" + "-" * 70)

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
                    "titulo": (oferta.get("titulo_limpio") or "")[:40],
                    "isco_v3": isco_obtenido,
                    "tipo": "REGRESION"
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
                    "titulo": (oferta.get("titulo_limpio") or "")[:40],
                    "isco_esperado": isco_esperado,
                    "isco_v3": isco_obtenido,
                    "metodo": result.metodo
                })
            else:
                errores_v3 += 1
                detalles_errores.append({
                    "id": id_oferta,
                    "titulo": (oferta.get("titulo_limpio") or "")[:40],
                    "isco_esperado": isco_esperado,
                    "isco_v3": isco_obtenido,
                    "tipo": "PERSISTE",
                    "metodo": result.metodo
                })

    # Cerrar
    matcher.close()
    conn.close()

    # Resumen
    results.append("\n" + "=" * 70)
    results.append("RESUMEN")
    results.append("=" * 70)
    results.append(f"Total casos evaluados: {total}")
    results.append(f"Sin datos en BD: {sin_datos}")
    results.append("")
    results.append(f"Correctos v3: {correctos}/{total} ({100*correctos/total:.1f}%)")
    results.append(f"Errores v2.1 originales: {errores_v21}")
    results.append(f"  - Corregidos por v3: {corregidos_v3}")
    results.append(f"  - Persisten en v3: {errores_v3}")
    results.append(f"Nuevos errores v3 (regresiones): {nuevos_errores_v3}")

    # Mejora
    if errores_v21 > 0:
        mejora = 100 * corregidos_v3 / errores_v21
        results.append(f"\nMejora en casos problematicos: {corregidos_v3}/{errores_v21} ({mejora:.1f}%)")

    # Detalle de corregidos
    if detalles_corregidos:
        results.append("\n" + "-" * 70)
        results.append("CASOS CORREGIDOS POR V3:")
        results.append("-" * 70)
        for d in detalles_corregidos:
            results.append(f"  {d['id']}: {d['titulo']}")
            results.append(f"    ISCO: {d['isco_esperado']} -> {d['isco_v3']} ({d['metodo']})")

    # Detalle de errores persistentes
    if detalles_errores:
        results.append("\n" + "-" * 70)
        results.append("ERRORES PENDIENTES:")
        results.append("-" * 70)
        for d in detalles_errores:
            results.append(f"  {d['id']}: {d['titulo']}")
            results.append(f"    Esperado: {d.get('isco_esperado', 'N/A')}, V3: {d['isco_v3']}")
            results.append(f"    Tipo: {d['tipo']}")

    return "\n".join(results), correctos, total


if __name__ == "__main__":
    try:
        output, c, t = run_test()

        # Write to file
        output_path = Path(__file__).parent / "test_v3_results.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        print(f"Results written to: {output_path}")
        print(f"RESULT: {c}/{t}")

    except Exception as e:
        import traceback
        error_path = Path(__file__).parent / "test_v3_error.txt"
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {type(e).__name__}: {e}\n\n")
            traceback.print_exc(file=f)
        print(f"Error logged to: {error_path}")
