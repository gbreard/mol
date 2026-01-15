# -*- coding: utf-8 -*-
"""
Mostrar 10 ejemplos de campos críticos NLP v10.
"""

import sqlite3
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Cargar Gold Set IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    gold_ids = [str(g['id_oferta']) for g in gold_data]
    placeholders = ','.join(['?'] * len(gold_ids))

    # Primero obtener columnas existentes
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columnas_existentes = {row[1] for row in cursor.fetchall()}

    # Campos críticos para mostrar (verificar que existen)
    campos_deseados = [
        'area_funcional', 'nivel_seniority',
        'modalidad', 'provincia', 'experiencia_min_anios',
        'skills_tecnicas_list', 'mision_rol'
    ]
    campos = [c for c in campos_deseados if c in columnas_existentes]

    query = f"""
        SELECT n.id_oferta, o.titulo, {', '.join(['n.' + c for c in campos])}
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.nlp_version = '10.0.0' AND n.id_oferta IN ({placeholders})
        LIMIT 10
    """
    cursor.execute(query, gold_ids)

    print("=" * 100)
    print("10 EJEMPLOS DE CAMPOS CRITICOS - NLP v10.0.0")
    print("=" * 100)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"\n[{i}] ID: {row['id_oferta']}")
        titulo = row['titulo'][:60] if row['titulo'] else "N/A"
        print(f"    Titulo: {titulo}...")
        print(f"    Area Funcional: {row['area_funcional'] if 'area_funcional' in campos else 'N/A'}")
        print(f"    Seniority: {row['nivel_seniority'] if 'nivel_seniority' in campos else 'N/A'}")
        print(f"    Modalidad: {row['modalidad'] if 'modalidad' in campos else 'N/A'}")
        print(f"    Provincia: {row['provincia'] if 'provincia' in campos else 'N/A'}")
        print(f"    Exp Min (anios): {row['experiencia_min_anios'] if 'experiencia_min_anios' in campos else 'N/A'}")

        # Skills técnicas (truncar si es muy largo)
        if 'skills_tecnicas_list' in campos:
            skills = row['skills_tecnicas_list']
            if skills:
                try:
                    skills_list = json.loads(skills) if isinstance(skills, str) else skills
                    skills_str = ', '.join(skills_list[:5]) if isinstance(skills_list, list) else str(skills)[:50]
                except:
                    skills_str = str(skills)[:50]
                print(f"    Skills: {skills_str}")
            else:
                print(f"    Skills: N/A")

        # Misión rol (truncar)
        if 'mision_rol' in campos:
            mision = row['mision_rol']
            if mision:
                print(f"    Mision: {mision[:80]}...")
            else:
                print(f"    Mision: N/A")

    conn.close()


if __name__ == "__main__":
    main()
