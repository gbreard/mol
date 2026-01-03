# -*- coding: utf-8 -*-
"""
Generar Gold Set NLP desde datos existentes
==========================================

Lee las 20 ofertas seleccionadas y genera el gold_set.json
usando los valores actuales extraídos por NLP.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
CANDIDATES_PATH = Path(__file__).parent / "nlp_gold_set_candidates.json"
OUTPUT_PATH = Path(__file__).parent.parent / "tests" / "nlp" / "gold_set.json"

def get_nlp_data(conn, id_oferta):
    """Obtiene datos NLP para una oferta."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            n.id_oferta,
            o.titulo,
            n.area_funcional,
            n.nivel_seniority,
            n.tiene_gente_cargo,
            n.tareas_explicitas,
            n.sector_empresa,
            n.tipo_oferta,
            n.licencia_conducir,
            n.tipo_licencia,
            n.es_tercerizado,
            n.skills_tecnicas_list,
            n.soft_skills_list
        FROM ofertas_nlp n
        JOIN ofertas o ON CAST(n.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE n.id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    if not row:
        return None

    # Parse tareas_list from JSON if present
    tareas_raw = row[5]
    tareas_list = []
    if tareas_raw:
        try:
            tareas_list = json.loads(tareas_raw) if isinstance(tareas_raw, str) else tareas_raw
        except:
            pass

    return {
        "id_oferta": str(row[0]),
        "titulo": row[1],
        "area_funcional": row[2],
        "nivel_seniority": row[3],
        "tiene_gente_cargo": bool(row[4]) if row[4] is not None else None,
        "tareas_list": tareas_list[:5] if tareas_list else [],  # Max 5 items
        "sector_empresa": row[6],
        "tipo_oferta": row[7],
        "licencia_conducir": bool(row[8]) if row[8] is not None else None,
        "tipo_licencia": row[9],
        "es_tercerizado": bool(row[10]) if row[10] is not None else None
    }


def main():
    # Load candidates
    with open(CANDIDATES_PATH, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    ids = candidates['ids']
    by_category = candidates['by_category']

    conn = sqlite3.connect(DB_PATH)

    gold_set = []
    found_count = 0
    missing_count = 0

    # Create category lookup
    id_to_category = {}
    for cat, offers in by_category.items():
        for offer in offers:
            id_to_category[offer['id_oferta']] = cat

    print("=" * 70)
    print("GENERANDO GOLD SET NLP")
    print("=" * 70)

    for id_oferta in ids:
        data = get_nlp_data(conn, id_oferta)
        categoria = id_to_category.get(id_oferta, "unknown")

        if data:
            found_count += 1
            entry = {
                "id_oferta": data["id_oferta"],
                "titulo": data["titulo"],
                "categoria": categoria,
                "expected": {
                    "area_funcional": data["area_funcional"],
                    "nivel_seniority": data["nivel_seniority"],
                    "tiene_gente_cargo": data["tiene_gente_cargo"],
                    "tareas_list": data["tareas_list"],
                    "sector_empresa": data["sector_empresa"],
                    "tipo_oferta": data["tipo_oferta"],
                    "licencia_conducir": data["licencia_conducir"],
                    "es_tercerizado": data["es_tercerizado"]
                }
            }
            gold_set.append(entry)
            print(f"  [OK] {id_oferta}: {data['titulo'][:40]}...")
        else:
            missing_count += 1
            print(f"  [--] {id_oferta}: Sin datos NLP")

    conn.close()

    # Save gold set
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(gold_set, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"RESULTADO: {found_count} con datos, {missing_count} sin datos")
    print(f"Gold set guardado en: {OUTPUT_PATH}")
    print("=" * 70)

    # Coverage report
    print("\n## COBERTURA POR CAMPO")
    print("-" * 50)

    campos = ["area_funcional", "nivel_seniority", "tiene_gente_cargo",
              "sector_empresa", "tipo_oferta", "licencia_conducir", "es_tercerizado"]

    for campo in campos:
        con_valor = sum(1 for g in gold_set if g["expected"].get(campo) is not None)
        sin_valor = len(gold_set) - con_valor

        # Get sample values
        ejemplos = []
        for g in gold_set:
            val = g["expected"].get(campo)
            if val is not None and val not in ejemplos:
                ejemplos.append(str(val)[:20])
            if len(ejemplos) >= 3:
                break

        print(f"{campo:25} | {con_valor:>2}/{len(gold_set)} | {', '.join(ejemplos)}")

    return gold_set


if __name__ == "__main__":
    main()
