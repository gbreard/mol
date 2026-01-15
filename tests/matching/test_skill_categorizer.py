#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test del SkillCategorizer con datos reales del Gold Set."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import sqlite3
from skill_categorizer import SkillCategorizer
from skills_implicit_extractor import SkillsImplicitExtractor

def main():
    categorizer = SkillCategorizer()
    extractor = SkillsImplicitExtractor(verbose=False)

    # Conectar a BD
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Test con una oferta del Gold Set
    cur = conn.execute(
        'SELECT titulo_limpio, tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?',
        ('1118028038',)
    )
    row = cur.fetchone()

    titulo, tareas = row[0] or '', row[1] or ''
    print(f"Titulo: {titulo}")
    print(f"Tareas: {tareas[:100]}..." if len(tareas) > 100 else f"Tareas: {tareas}")
    print()

    # Extraer skills
    skills = extractor.extract_skills(titulo_limpio=titulo, tareas_explicitas=tareas)
    print(f"Skills extraidas: {len(skills)}")
    print()

    # Categorizar
    skills = categorizer.categorize_batch(skills)

    # Mostrar resultados
    print("Categorización (top 10):")
    for s in skills[:10]:
        skill_name = s.get("skill_esco", "")[:40]
        L1 = s.get("L1", "?")
        L2 = s.get("L2", "-") or "-"
        digital = "Sí" if s.get("es_digital") else "No"
        metodo = s.get("metodo", "?")
        print(f"  {skill_name:40} | {L1}/{L2:6} | Dig:{digital} | {metodo}")

    # Resumen
    summary = categorizer.get_summary(skills)
    print()
    print("Resumen:")
    print(f"  Por L1: {summary['por_L1']}")
    print(f"  Por L2: {summary['por_L2']}")
    print(f"  Digitales: {summary['digitales_count']}/{summary['total']}")

    conn.close()

if __name__ == "__main__":
    main()
