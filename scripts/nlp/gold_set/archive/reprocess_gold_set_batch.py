#!/usr/bin/env python3
"""
Reprocesar Gold Set en batch y medir cobertura
"""

import sys
import json
import sqlite3
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "database"))

from process_nlp_from_db_v10 import NLPExtractorV10

def get_gold_set_ids():
    """Obtener IDs del Gold Set"""
    gs_path = project_root / "database" / "gold_set_manual_v2.json"
    with open(gs_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    return [item['id_oferta'] for item in gold_set]

def get_current_coverage():
    """Obtener cobertura actual desde BD"""
    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    gold_ids = get_gold_set_ids()
    placeholders = ','.join(['?' for _ in gold_ids])

    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN skills_tecnicas_list IS NOT NULL
                     AND skills_tecnicas_list != '[]'
                     AND skills_tecnicas_list != 'null'
                     AND length(skills_tecnicas_list) > 5 THEN 1 ELSE 0 END) as con_skills_tec,
            SUM(CASE WHEN soft_skills_list IS NOT NULL
                     AND soft_skills_list != '[]'
                     AND soft_skills_list != 'null'
                     AND length(soft_skills_list) > 5 THEN 1 ELSE 0 END) as con_soft
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, gold_ids)

    row = cursor.fetchone()
    conn.close()

    return {
        "total": row[0],
        "con_skills_tecnicas": row[1],
        "con_soft_skills": row[2]
    }

def get_ids_sin_skills():
    """Obtener IDs que no tienen skills (para reprocesar)"""
    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    gold_ids = get_gold_set_ids()
    placeholders = ','.join(['?' for _ in gold_ids])

    # IDs sin skills tecnicas o sin soft skills
    cursor.execute(f"""
        SELECT id_oferta
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
          AND (skills_tecnicas_list IS NULL
               OR skills_tecnicas_list = '[]'
               OR skills_tecnicas_list = 'null'
               OR soft_skills_list IS NULL
               OR soft_skills_list = '[]'
               OR soft_skills_list = 'null')
    """, gold_ids)

    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def reprocess_batch(ids, verbose=False):
    """Reprocesar batch de ofertas"""
    extractor = NLPExtractorV10(verbose=verbose)
    result = extractor.process_batch(limit=len(ids), ids_especificos=ids)
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("REPROCESAR GOLD SET CON FIX DE PERSISTENCIA")
    print("=" * 60)

    # Cobertura ANTES
    print("\n[1] COBERTURA ACTUAL (ANTES):")
    antes = get_current_coverage()
    print(f"    Total ofertas: {antes['total']}")
    print(f"    Con skills_tecnicas: {antes['con_skills_tecnicas']} ({100*antes['con_skills_tecnicas']/antes['total']:.1f}%)")
    print(f"    Con soft_skills: {antes['con_soft_skills']} ({100*antes['con_soft_skills']/antes['total']:.1f}%)")

    # IDs a reprocesar
    ids_pendientes = get_ids_sin_skills()
    print(f"\n[2] OFERTAS A REPROCESAR: {len(ids_pendientes)}")

    if len(ids_pendientes) > 0:
        print(f"    IDs: {ids_pendientes[:5]}..." if len(ids_pendientes) > 5 else f"    IDs: {ids_pendientes}")

        # Preguntar si continuar
        if len(sys.argv) > 1 and sys.argv[1] == "--run":
            print("\n[3] REPROCESANDO...")
            result = reprocess_batch(ids_pendientes, verbose=False)
            print(f"    Procesadas: {result.get('total_success', 0)}")
            print(f"    Errores: {result.get('total_errors', 0)}")

            # Cobertura DESPUES
            print("\n[4] COBERTURA DESPUES:")
            despues = get_current_coverage()
            print(f"    Total ofertas: {despues['total']}")
            print(f"    Con skills_tecnicas: {despues['con_skills_tecnicas']} ({100*despues['con_skills_tecnicas']/despues['total']:.1f}%)")
            print(f"    Con soft_skills: {despues['con_soft_skills']} ({100*despues['con_soft_skills']/despues['total']:.1f}%)")

            # Comparativa
            print("\n" + "=" * 60)
            print("COMPARATIVA FINAL")
            print("=" * 60)
            print(f"{'Campo':<25} {'Antes':<15} {'Despues':<15} {'Mejora':<10}")
            print("-" * 60)
            mejora_tec = despues['con_skills_tecnicas'] - antes['con_skills_tecnicas']
            mejora_soft = despues['con_soft_skills'] - antes['con_soft_skills']
            print(f"{'skills_tecnicas_list':<25} {antes['con_skills_tecnicas']}/{antes['total']} ({100*antes['con_skills_tecnicas']/antes['total']:.0f}%)      {despues['con_skills_tecnicas']}/{despues['total']} ({100*despues['con_skills_tecnicas']/despues['total']:.0f}%)      +{mejora_tec}")
            print(f"{'soft_skills_list':<25} {antes['con_soft_skills']}/{antes['total']} ({100*antes['con_soft_skills']/antes['total']:.0f}%)      {despues['con_soft_skills']}/{despues['total']} ({100*despues['con_soft_skills']/despues['total']:.0f}%)      +{mejora_soft}")
        else:
            print("\n    Ejecutar con --run para reprocesar")
    else:
        print("    [OK] Todas las ofertas ya tienen skills")

        # Mostrar cobertura final
        print("\n" + "=" * 60)
        print("COBERTURA FINAL GOLD SET")
        print("=" * 60)
        print(f"skills_tecnicas_list: {antes['con_skills_tecnicas']}/{antes['total']} ({100*antes['con_skills_tecnicas']/antes['total']:.1f}%)")
        print(f"soft_skills_list: {antes['con_soft_skills']}/{antes['total']} ({100*antes['con_soft_skills']/antes['total']:.1f}%)")
