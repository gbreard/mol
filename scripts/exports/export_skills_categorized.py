#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Gold Set con Skills Categorizadas L1/L2 para Dashboard
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import sqlite3
import json
import pandas as pd
from skills_implicit_extractor import SkillsImplicitExtractor
from match_ofertas_v3 import MatcherV3

def main():
    print("Generando Excel con Skills Categorizadas...")

    # Cargar Gold Set
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    # Conectar a BD
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Inicializar
    extractor = SkillsImplicitExtractor(verbose=False)
    matcher = MatcherV3(db_conn=conn, verbose=False)

    # Datos para sheets
    ofertas_data = []
    skills_detalle_data = []
    resumen_L1_data = []

    print(f"Procesando {len(gold_set)} ofertas...")

    for i, caso in enumerate(gold_set, 1):
        id_oferta = caso['id_oferta']
        print(f"  {i}/49: {id_oferta}")

        # Obtener datos oferta
        cur = conn.execute('''
            SELECT titulo_limpio, tareas_explicitas, area_funcional, nivel_seniority
            FROM ofertas_nlp WHERE id_oferta = ?
        ''', (id_oferta,))
        row = cur.fetchone()
        if not row:
            continue

        titulo, tareas, area, seniority = row
        titulo = titulo or ''
        tareas = tareas or ''

        # Extraer skills (ya vienen categorizadas)
        skills = extractor.extract_skills(titulo_limpio=titulo, tareas_explicitas=tareas)

        # Matching ESCO
        oferta = {'titulo_limpio': titulo, 'tareas_explicitas': tareas,
                  'area_funcional': area or '', 'nivel_seniority': seniority or ''}
        result = matcher.match(oferta)

        # Calcular resumen L1
        L1_counts = {}
        L2_counts = {}
        digitales = 0
        for s in skills:
            L1 = s.get('L1', 'T')
            L2 = s.get('L2')
            L1_counts[L1] = L1_counts.get(L1, 0) + 1
            if L2:
                L2_counts[L2] = L2_counts.get(L2, 0) + 1
            if s.get('es_digital'):
                digitales += 1

        # Agregar a ofertas
        ofertas_data.append({
            'ID': id_oferta,
            'Titulo': titulo,
            'Area': area or '',
            'Seniority': seniority or '',
            'ISCO': result.isco_code,
            'Ocupacion_ESCO': result.esco_label,
            'Skills_Total': len(skills),
            'Skills_Digitales': digitales,
            'Pct_Digitales': round(100 * digitales / len(skills), 1) if skills else 0,
            'L1_S1_Comunicacion': L1_counts.get('S1', 0),
            'L1_S3_Asistencia': L1_counts.get('S3', 0),
            'L1_S4_Gestion': L1_counts.get('S4', 0),
            'L1_S5_Digital': L1_counts.get('S5', 0),
            'L1_S6_Tecnicas': L1_counts.get('S6', 0),
            'L1_K_Conocimientos': L1_counts.get('K', 0),
            'L1_T_Transversales': L1_counts.get('T', 0)
        })

        # Agregar skills detalle
        for s in skills:
            skills_detalle_data.append({
                'ID_Oferta': id_oferta,
                'Titulo_Oferta': titulo[:50],
                'Skill_ESCO': s.get('skill_esco', ''),
                'Score': s.get('score', 0),
                'Origen': s.get('origen', ''),
                'L1': s.get('L1', ''),
                'L1_Nombre': s.get('L1_nombre', ''),
                'L2': s.get('L2', '') or '',
                'L2_Nombre': s.get('L2_nombre', '') or '',
                'Es_Digital': 'Sí' if s.get('es_digital') else 'No',
                'Metodo_Clasificacion': s.get('metodo', '')
            })

    matcher.close()
    conn.close()

    # Calcular resumen global L1
    global_L1 = {}
    global_L2 = {}
    total_skills = len(skills_detalle_data)

    for s in skills_detalle_data:
        L1 = s['L1']
        L2 = s['L2']
        global_L1[L1] = global_L1.get(L1, 0) + 1
        if L2:
            global_L2[L2] = global_L2.get(L2, 0) + 1

    for L1, count in sorted(global_L1.items()):
        resumen_L1_data.append({
            'Nivel': 'L1',
            'Codigo': L1,
            'Nombre': ofertas_data[0].get(f'L1_{L1}_', L1) if ofertas_data else L1,
            'Cantidad': count,
            'Porcentaje': round(100 * count / total_skills, 1)
        })

    for L2, count in sorted(global_L2.items(), key=lambda x: -x[1])[:20]:
        resumen_L1_data.append({
            'Nivel': 'L2',
            'Codigo': L2,
            'Nombre': skills_detalle_data[0].get('L2_Nombre', L2) if skills_detalle_data else L2,
            'Cantidad': count,
            'Porcentaje': round(100 * count / total_skills, 1)
        })

    # Crear DataFrames
    df_ofertas = pd.DataFrame(ofertas_data)
    df_skills = pd.DataFrame(skills_detalle_data)
    df_resumen = pd.DataFrame(resumen_L1_data)

    # Exportar a Excel
    output_path = Path(__file__).parent.parent / "exports" / f"gold_set_skills_L1L2_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_ofertas.to_excel(writer, sheet_name='Ofertas', index=False)
        df_skills.to_excel(writer, sheet_name='Skills_Detalle', index=False)
        df_resumen.to_excel(writer, sheet_name='Resumen_Categorias', index=False)

    print()
    print(f"Excel guardado: {output_path}")
    print(f"  - Ofertas: {len(ofertas_data)}")
    print(f"  - Skills: {len(skills_detalle_data)}")
    print(f"  - Promedio skills/oferta: {len(skills_detalle_data)/len(ofertas_data):.1f}")

if __name__ == "__main__":
    main()
