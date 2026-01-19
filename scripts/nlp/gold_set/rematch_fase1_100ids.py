#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rematch FASE 1 - Reprocesar matching en 100 IDs
===============================================

Reprocesa el matching para los 100 IDs de test usando:
1. Títulos limpios con regex v2.2
2. Matching v3.2.1 con penalización sector

Exporta comparación antes/después a Excel.

Ejecutar desde /database/:
    python ../scripts/nlp/gold_set/rematch_fase1_100ids.py
"""

import sqlite3
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Setup paths
BASE = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE / "database"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = BASE / "database" / "bumeran_scraping.db"


def get_100_ids():
    """Obtiene los 100 IDs de test."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute('''
        SELECT DISTINCT n.id_oferta
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.titulo_limpio IS NOT NULL
        ORDER BY n.id_oferta DESC
        LIMIT 100
    ''')
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def get_current_results():
    """Obtiene resultados actuales del matching."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    ids = get_100_ids()
    placeholders = ','.join(['?' for _ in ids])

    cur = conn.execute(f'''
        SELECT m.id_oferta, m.isco_code, m.esco_occupation_label,
               m.occupation_match_score, m.occupation_match_method,
               n.titulo_limpio, n.sector_empresa, n.area_funcional,
               n.nivel_seniority, n.tareas_explicitas,
               o.titulo as titulo_scraping
        FROM ofertas_esco_matching m
        JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        JOIN ofertas o ON m.id_oferta = o.id_oferta
        WHERE m.id_oferta IN ({placeholders})
    ''', ids)

    results = {row['id_oferta']: dict(row) for row in cur.fetchall()}
    conn.close()
    return results


def rematch_with_clean_titles(verbose=True):
    """
    Reprocesa matching con títulos limpios y penalización sector.
    """
    from limpiar_titulos import limpiar_titulo, cargar_config
    from match_ofertas_v3 import MatcherV3

    # Obtener resultados actuales
    current = get_current_results()
    ids = list(current.keys())

    print(f"IDs a procesar: {len(ids)}")

    # Cargar config limpieza
    titulo_config = cargar_config()

    # Inicializar matcher v3.2.1
    matcher = MatcherV3(verbose=False)
    print(f"Matcher version: {matcher.VERSION}")

    results = []
    changed = 0
    improved = 0
    same = 0

    for i, id_oferta in enumerate(ids):
        if i % 20 == 0:
            print(f"Procesando {i+1}/{len(ids)}...")

        old = current.get(id_oferta, {})

        # Limpiar título
        titulo_scraping = old.get("titulo_scraping", "")
        titulo_limpio = limpiar_titulo(titulo_scraping, titulo_config)

        # Preparar datos NLP
        oferta_nlp = {
            "titulo_limpio": titulo_limpio,  # Usar título limpio nuevo
            "titulo": titulo_limpio,
            "tareas_explicitas": old.get("tareas_explicitas", ""),
            "sector_empresa": old.get("sector_empresa", ""),
            "area_funcional": old.get("area_funcional", ""),
            "nivel_seniority": old.get("nivel_seniority", ""),
        }

        # Match
        try:
            result = matcher.match(oferta_nlp)
            new_isco = result.isco_code
            new_label = result.esco_label
            new_score = result.score
            new_method = result.metodo
        except Exception as e:
            print(f"Error en {id_oferta}: {e}")
            new_isco = old.get("isco_code", "")
            new_label = old.get("esco_occupation_label", "")
            new_score = 0
            new_method = "error"

        # Comparar
        old_isco = old.get("isco_code", "")
        isco_changed = new_isco != old_isco

        if isco_changed:
            changed += 1
            # Determinar si mejoró (difícil sin gold set, por ahora solo contamos cambios)

        results.append({
            "id_oferta": id_oferta,
            "titulo_scraping": titulo_scraping[:60],
            "titulo_limpio_old": old.get("titulo_limpio", "")[:40],
            "titulo_limpio_new": titulo_limpio[:40],
            "sector_empresa": old.get("sector_empresa", ""),
            "isco_old": old_isco,
            "isco_new": new_isco,
            "label_old": old.get("esco_occupation_label", "")[:40],
            "label_new": (new_label or "")[:40],
            "score_old": old.get("occupation_match_score", 0),
            "score_new": new_score,
            "method_old": old.get("occupation_match_method", ""),
            "method_new": new_method,
            "changed": isco_changed,
        })

    matcher.close()

    print(f"\nResultados:")
    print(f"  Total procesados: {len(ids)}")
    print(f"  ISCO cambió: {changed} ({changed*100//len(ids)}%)")

    return results


def export_to_csv(results, filename=None):
    """Exporta resultados a CSV."""
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"fase1_comparison_{ts}.csv"

    filepath = BASE / "exports" / filename

    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nExportado a: {filepath}")
    return filepath


def main():
    """Ejecuta rematch y exporta resultados."""
    print("=" * 70)
    print("REMATCH FASE 1 - 100 IDs")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    results = rematch_with_clean_titles(verbose=True)

    # Mostrar cambios
    print("\n" + "=" * 70)
    print("CAMBIOS DETECTADOS:")
    print("=" * 70)

    cambios = [r for r in results if r["changed"]]
    for c in cambios[:15]:
        print(f"\n[{c['id_oferta']}] {c['titulo_scraping'][:50]}...")
        print(f"  Sector: {c['sector_empresa']}")
        print(f"  ANTES: ISCO {c['isco_old']} - {c['label_old']}")
        print(f"  AHORA: ISCO {c['isco_new']} - {c['label_new']}")

    print(f"\nTotal cambios: {len(cambios)}/{len(results)}")

    # Exportar
    export_to_csv(results)

    return results


if __name__ == "__main__":
    main()
