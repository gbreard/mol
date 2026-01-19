#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Gold Set Analysis - Tareas, Skills Implicitas y Matching ESCO
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add database folder to path
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import pandas as pd
from match_ofertas_v3 import MatcherV3
from skills_implicit_extractor import SkillsImplicitExtractor

def load_gold_set():
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("Generando Excel de analisis Gold Set...")

    # Connect to DB
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Initialize components
    matcher = MatcherV3(db_conn=conn, verbose=False)
    skills_extractor = SkillsImplicitExtractor(verbose=False)

    gold_set = load_gold_set()

    data = []

    for i, caso in enumerate(gold_set, 1):
        id_oferta = caso["id_oferta"]
        print(f"  Procesando {i}/49: {id_oferta}...")

        # Get offer data
        cur = conn.execute('''
            SELECT titulo_limpio, tareas_explicitas, area_funcional,
                   nivel_seniority, sector_empresa, skills_tecnicas_list,
                   soft_skills_list
            FROM ofertas_nlp
            WHERE id_oferta = ?
        ''', (id_oferta,))
        row = cur.fetchone()

        if not row:
            print(f"    WARNING: No data for {id_oferta}")
            continue

        titulo = row[0] or ""
        tareas = row[1] or ""
        area = row[2] or ""
        seniority = row[3] or ""
        sector = row[4] or ""
        skills_tecnicas = row[5] or ""
        soft_skills = row[6] or ""

        # Extract implicit skills
        implicit_skills = skills_extractor.extract_skills(
            titulo_limpio=titulo,
            tareas_explicitas=tareas
        )

        # Format implicit skills for Excel
        skills_list = [s['skill_esco'] for s in implicit_skills]
        skills_scores = [f"{s['skill_esco']} ({s['score']:.2f})" for s in implicit_skills[:10]]

        # Run matching
        oferta = {
            'titulo_limpio': titulo,
            'tareas_explicitas': tareas,
            'area_funcional': area,
            'nivel_seniority': seniority,
            'sector_empresa': sector
        }
        result = matcher.match(oferta)

        # Build row
        data.append({
            'ID': id_oferta,
            'Titulo': titulo,
            'Area_Funcional': area,
            'Seniority': seniority,
            'Sector': sector,
            'Tareas_Explicitas': tareas[:500] if tareas else "",
            'Skills_Tecnicas_NLP': skills_tecnicas[:300] if skills_tecnicas else "",
            'Soft_Skills_NLP': soft_skills[:200] if soft_skills else "",
            'Skills_Implicitas_Count': len(implicit_skills),
            'Skills_Implicitas_Top10': "; ".join(skills_scores),
            'Skills_Implicitas_All': "; ".join(skills_list),
            'ISCO_Resultado': result.isco_code,
            'ESCO_Label': result.esco_label,
            'Match_Score': round(result.score, 3),
            'Match_Metodo': result.metodo,
            'Skills_Matched_Count': len(result.skills_matched) if result.skills_matched else 0,
            'Skills_Matched': "; ".join(result.skills_matched[:5]) if result.skills_matched else "",
            'Alternativas': "; ".join([f"{a['isco_code']}:{a['esco_label'][:30]}" for a in (result.alternativas or [])[:3]]),
            'Gold_ISCO_Esperado': caso.get('isco_esperado', ''),
            'Gold_Comentario': caso.get('comentario', '')
        })

    matcher.close()
    conn.close()

    # Create DataFrame
    df = pd.DataFrame(data)

    # Export to Excel with formatting
    output_path = Path(__file__).parent.parent / "exports" / f"gold_set_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    output_path.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Gold Set Analysis')

        # Auto-adjust column widths
        worksheet = writer.sheets['Gold Set Analysis']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            # Cap at 50 for readability
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"].width = adjusted_width

    print(f"\nExcel guardado en: {output_path}")
    print(f"Total ofertas: {len(data)}")
    print(f"Promedio skills implicitas: {sum(d['Skills_Implicitas_Count'] for d in data)/len(data):.1f}")

    return output_path

if __name__ == "__main__":
    main()
