#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Gold Set Final - Version limpia sin comentarios de validacion
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import pandas as pd
from match_ofertas_v3 import MatcherV3
from skills_implicit_extractor import SkillsImplicitExtractor

def main():
    print("Generando Excel final Gold Set v3.0...")

    # Load Gold Set IDs
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    matcher = MatcherV3(db_conn=conn, verbose=False)
    skills_extractor = SkillsImplicitExtractor(verbose=False)

    data = []
    for i, caso in enumerate(gold_set, 1):
        id_oferta = caso['id_oferta']
        print(f'  {i}/49: {id_oferta}')

        cur = conn.execute('''
            SELECT titulo_limpio, tareas_explicitas, area_funcional,
                   nivel_seniority, sector_empresa
            FROM ofertas_nlp WHERE id_oferta = ?
        ''', (id_oferta,))
        row = cur.fetchone()
        if not row:
            continue

        titulo, tareas, area, seniority, sector = row
        titulo = titulo or ''
        tareas = tareas or ''

        # Extract implicit skills
        implicit_skills = skills_extractor.extract_skills(
            titulo_limpio=titulo,
            tareas_explicitas=tareas
        )
        skills_top = [f"{s['skill_esco']} ({s['score']:.2f})" for s in implicit_skills[:15]]
        skills_all = [s['skill_esco'] for s in implicit_skills]

        # Run matching
        oferta = {
            'titulo_limpio': titulo,
            'tareas_explicitas': tareas,
            'area_funcional': area or '',
            'nivel_seniority': seniority or ''
        }
        result = matcher.match(oferta)

        data.append({
            'ID': id_oferta,
            'Titulo': titulo,
            'Area_Funcional': area or '',
            'Seniority': seniority or '',
            'Tareas_Explicitas': tareas,
            'Skills_Implicitas_Qty': len(implicit_skills),
            'Skills_Implicitas_Top15': '; '.join(skills_top),
            'Skills_Implicitas_Todas': '; '.join(skills_all),
            'ISCO_Code': result.isco_code,
            'Ocupacion_ESCO': result.esco_label,
            'Match_Score': round(result.score, 3),
            'Metodo_Match': result.metodo,
            'Skills_que_Matchearon': '; '.join(result.skills_matched[:10]) if result.skills_matched else ''
        })

    matcher.close()
    conn.close()

    df = pd.DataFrame(data)
    output = Path(__file__).parent.parent / "exports" / f"gold_set_v3_final_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matching v3.0 Final')

    print(f'\nExcel guardado: {output}')
    print(f'Total ofertas: {len(data)}')
    print(f'Skills implicitas promedio: {sum(d["Skills_Implicitas_Qty"] for d in data)/len(data):.1f}')

if __name__ == "__main__":
    main()
