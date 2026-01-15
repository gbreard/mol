#!/usr/bin/env python3
"""
Reprocesar TODAS las 49 ofertas del Gold Set (forzado)
"""

import sys
import json
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "database"))

from process_nlp_from_db_v10 import NLPExtractorV10

def get_gold_set_ids():
    gs_path = project_root / "database" / "gold_set_manual_v2.json"
    with open(gs_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    return [item['id_oferta'] for item in gold_set]

def get_coverage_stats():
    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    gold_ids = get_gold_set_ids()
    placeholders = ','.join(['?' for _ in gold_ids])

    # Contar ofertas con [regex] en skills
    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN skills_tecnicas_list LIKE '%[regex]%' THEN 1 ELSE 0 END) as con_regex_tec,
            SUM(CASE WHEN soft_skills_list LIKE '%[regex]%' THEN 1 ELSE 0 END) as con_regex_soft,
            SUM(CASE WHEN skills_tecnicas_list IS NOT NULL
                     AND skills_tecnicas_list != '[]'
                     AND length(skills_tecnicas_list) > 5 THEN 1 ELSE 0 END) as con_skills_tec,
            SUM(CASE WHEN soft_skills_list IS NOT NULL
                     AND soft_skills_list != '[]'
                     AND length(soft_skills_list) > 5 THEN 1 ELSE 0 END) as con_soft
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, gold_ids)

    row = cursor.fetchone()
    conn.close()

    return {
        "total": row[0],
        "con_regex_tec": row[1],
        "con_regex_soft": row[2],
        "con_skills_tec": row[3],
        "con_soft": row[4]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("REPROCESAR GOLD SET COMPLETO (49 OFERTAS)")
    print("=" * 60)

    gold_ids = get_gold_set_ids()
    print(f"\n[1] Total ofertas a reprocesar: {len(gold_ids)}")

    # Stats ANTES
    antes = get_coverage_stats()
    print(f"\n[2] ESTADO ANTES:")
    print(f"    Con skills_tecnicas [regex]: {antes['con_regex_tec']}/{antes['total']}")
    print(f"    Con soft_skills [regex]:     {antes['con_regex_soft']}/{antes['total']}")
    print(f"    Sin actualizar:              {antes['total'] - max(antes['con_regex_tec'], antes['con_regex_soft'])}")

    if "--run" not in sys.argv:
        print("\n    Ejecutar con --run para reprocesar todas")
        sys.exit(0)

    print(f"\n[3] REPROCESANDO {len(gold_ids)} OFERTAS...")

    extractor = NLPExtractorV10(verbose=False)
    result = extractor.process_batch(limit=len(gold_ids), ids_especificos=gold_ids)

    print(f"\n    Procesadas: {result.get('total_success', 0)}")
    print(f"    Errores:    {result.get('total_errors', 0)}")

    # Stats DESPUES
    despues = get_coverage_stats()
    print(f"\n[4] ESTADO DESPUES:")
    print(f"    Con skills_tecnicas [regex]: {despues['con_regex_tec']}/{despues['total']}")
    print(f"    Con soft_skills [regex]:     {despues['con_regex_soft']}/{despues['total']}")
    print(f"    Con skills_tecnicas total:   {despues['con_skills_tec']}/{despues['total']} ({100*despues['con_skills_tec']/despues['total']:.0f}%)")
    print(f"    Con soft_skills total:       {despues['con_soft']}/{despues['total']} ({100*despues['con_soft']/despues['total']:.0f}%)")

    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    print(f"Ofertas actualizadas con merge LLM+regex: {despues['con_regex_tec']}/{despues['total']}")
