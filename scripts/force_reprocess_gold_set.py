#!/usr/bin/env python3
"""
FORZAR reproceso de TODAS las 49 ofertas Gold Set
- Hace backup
- Borra registros NLP existentes
- Reprocesa desde cero
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "database"))

def get_gold_set_ids():
    gs_path = project_root / "database" / "gold_set_manual_v2.json"
    with open(gs_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    return [item['id_oferta'] for item in gold_set]

def backup_and_delete(gold_ids):
    """Backup y borrar registros NLP del Gold Set"""
    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    placeholders = ','.join(['?' for _ in gold_ids])

    # Crear backup
    backup_table = f"ofertas_nlp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[BACKUP] Creando tabla {backup_table}...")
    cursor.execute(f"""
        CREATE TABLE {backup_table} AS
        SELECT * FROM ofertas_nlp WHERE id_oferta IN ({placeholders})
    """, gold_ids)

    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
    count_backup = cursor.fetchone()[0]
    print(f"[BACKUP] {count_backup} registros guardados")

    # Borrar registros
    print(f"[DELETE] Borrando {count_backup} registros de ofertas_nlp...")
    cursor.execute(f"DELETE FROM ofertas_nlp WHERE id_oferta IN ({placeholders})", gold_ids)

    conn.commit()
    conn.close()

    return count_backup, backup_table

def get_stats():
    """Obtener estadísticas actuales"""
    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    gold_ids = get_gold_set_ids()
    placeholders = ','.join(['?' for _ in gold_ids])

    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN skills_tecnicas_list LIKE '%[regex]%' THEN 1 ELSE 0 END) as con_regex_tec,
            SUM(CASE WHEN soft_skills_list LIKE '%[regex]%' THEN 1 ELSE 0 END) as con_regex_soft,
            SUM(CASE WHEN skills_tecnicas_list IS NOT NULL
                     AND skills_tecnicas_list != '[]'
                     AND length(skills_tecnicas_list) > 5 THEN 1 ELSE 0 END) as con_skills,
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
        "con_regex_tec": row[1] or 0,
        "con_regex_soft": row[2] or 0,
        "con_skills": row[3] or 0,
        "con_soft": row[4] or 0
    }

if __name__ == "__main__":
    print("=" * 70)
    print("FORZAR REPROCESO GOLD SET COMPLETO (49 OFERTAS)")
    print("=" * 70)

    gold_ids = get_gold_set_ids()
    print(f"\nOfertas en Gold Set: {len(gold_ids)}")

    # Stats ANTES
    antes = get_stats()
    print(f"\n[ANTES]")
    print(f"  Registros NLP:           {antes['total']}")
    print(f"  Con skills_tec [regex]:  {antes['con_regex_tec']}")
    print(f"  Con soft_skills [regex]: {antes['con_regex_soft']}")

    if "--run" not in sys.argv:
        print("\n>>> Ejecutar con --run para forzar reproceso <<<")
        sys.exit(0)

    # Paso 1: Backup y borrar
    print("\n" + "-" * 70)
    print("PASO 1: BACKUP Y BORRAR")
    print("-" * 70)
    count, backup_table = backup_and_delete(gold_ids)

    # Paso 2: Reprocesar
    print("\n" + "-" * 70)
    print("PASO 2: REPROCESAR 49 OFERTAS")
    print("-" * 70)

    from process_nlp_from_db_v10 import NLPExtractorV10

    extractor = NLPExtractorV10(verbose=False)
    result = extractor.process_batch(limit=len(gold_ids), ids_especificos=gold_ids)

    print(f"\nResultado:")
    print(f"  Procesadas: {result.get('total_success', 0)}")
    print(f"  Errores:    {result.get('total_errors', 0)}")

    # Stats DESPUES
    print("\n" + "-" * 70)
    print("PASO 3: VERIFICAR CONSISTENCIA")
    print("-" * 70)

    despues = get_stats()
    print(f"\n[DESPUES]")
    print(f"  Registros NLP:           {despues['total']}")
    print(f"  Con skills_tec [regex]:  {despues['con_regex_tec']}")
    print(f"  Con soft_skills [regex]: {despues['con_regex_soft']}")
    print(f"  Con skills_tecnicas:     {despues['con_skills']}/{despues['total']} ({100*despues['con_skills']/despues['total']:.0f}%)")
    print(f"  Con soft_skills:         {despues['con_soft']}/{despues['total']} ({100*despues['con_soft']/despues['total']:.0f}%)")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Backup creado:     {backup_table}")
    print(f"Ofertas procesadas: {result.get('total_success', 0)}/49")
    print(f"Con merge [regex]:  {despues['con_regex_tec']}/49 skills_tec, {despues['con_regex_soft']}/49 soft_skills")

    if despues['con_regex_tec'] >= 45 and despues['con_regex_soft'] >= 45:
        print("\n[OK] Gold Set actualizado consistentemente con merge LLM+regex")
    else:
        print("\n[WARN] Algunas ofertas pueden no tener skills detectables")
