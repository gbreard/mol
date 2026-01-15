#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test completo del SkillCategorizer con todo el Gold Set."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import sqlite3
import json
from skill_categorizer import SkillCategorizer
from skills_implicit_extractor import SkillsImplicitExtractor

def main():
    categorizer = SkillCategorizer()
    extractor = SkillsImplicitExtractor(verbose=False)

    # Cargar Gold Set
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    # Conectar a BD
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Acumuladores
    total_skills = 0
    total_digitales = 0
    global_L1 = {}
    global_L2 = {}
    metodos = {"manual": 0, "heuristica": 0, "default": 0}

    print(f"Procesando {len(gold_set)} ofertas del Gold Set...")
    print()

    for caso in gold_set:
        id_oferta = caso['id_oferta']

        cur = conn.execute(
            'SELECT titulo_limpio, tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?',
            (id_oferta,)
        )
        row = cur.fetchone()
        if not row:
            continue

        titulo, tareas = row[0] or '', row[1] or ''

        # Extraer y categorizar
        skills = extractor.extract_skills(titulo_limpio=titulo, tareas_explicitas=tareas)
        skills = categorizer.categorize_batch(skills)

        for s in skills:
            total_skills += 1
            if s.get("es_digital"):
                total_digitales += 1

            L1 = s.get("L1", "?")
            L2 = s.get("L2")
            metodo = s.get("metodo", "default")

            global_L1[L1] = global_L1.get(L1, 0) + 1
            if L2:
                global_L2[L2] = global_L2.get(L2, 0) + 1
            metodos[metodo] = metodos.get(metodo, 0) + 1

    conn.close()

    # Resultados
    print("=" * 60)
    print("RESULTADOS GOLD SET - CATEGORIZACIÓN DE SKILLS")
    print("=" * 60)
    print()
    print(f"Total skills extraídas: {total_skills}")
    print(f"Promedio por oferta: {total_skills / len(gold_set):.1f}")
    print()

    print("Distribución por L1:")
    for L1 in sorted(global_L1.keys()):
        count = global_L1[L1]
        pct = 100 * count / total_skills
        nombre = categorizer.categorias_L1.get(L1, "Desconocido")
        print(f"  {L1:3} {nombre:30} {count:4} ({pct:5.1f}%)")

    print()
    print(f"Skills digitales: {total_digitales} ({100*total_digitales/total_skills:.1f}%)")

    print()
    print("Método de clasificación:")
    for m, count in sorted(metodos.items(), key=lambda x: -x[1]):
        pct = 100 * count / total_skills
        print(f"  {m:12} {count:4} ({pct:5.1f}%)")

    print()
    print("Top 15 categorías L2:")
    for L2, count in sorted(global_L2.items(), key=lambda x: -x[1])[:15]:
        pct = 100 * count / total_skills
        nombre = categorizer.categorias_L2.get(L2, "")
        print(f"  {L2:6} {nombre:25} {count:4} ({pct:5.1f}%)")

if __name__ == "__main__":
    main()
