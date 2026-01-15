#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selecciona 50 ofertas aleatorias nuevas, las procesa por el pipeline completo
y exporta a Excel para validación manual.

Pipeline: Limpieza título → NLP → Postprocessor → Matching → Skills → Categorías L1/L2
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

import sqlite3
import json
import pandas as pd

def main():
    print("=" * 70)
    print("SELECCIÓN DE 50 OFERTAS NUEVAS + PROCESAMIENTO PIPELINE")
    print("=" * 70)

    # Paths
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    exports_path = Path(__file__).parent.parent / "exports"
    exports_path.mkdir(exist_ok=True)

    # Cargar IDs actuales del Gold Set (para excluir)
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    ids_excluir = [str(x['id_oferta']) for x in gold_set]
    print(f"\nExcluyendo {len(ids_excluir)} ofertas del Gold Set actual")

    # Conectar BD
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Seleccionar 50 ofertas aleatorias
    placeholders = ','.join(['?' for _ in ids_excluir])
    query = f'''
        SELECT o.id_oferta, o.titulo, o.descripcion, o.empresa,
               o.localizacion, o.fecha_publicacion_iso, o.url_oferta,
               o.modalidad_trabajo, o.tipo_trabajo
        FROM ofertas o
        WHERE o.descripcion IS NOT NULL
          AND LENGTH(o.descripcion) > 200
          AND o.id_oferta NOT IN ({placeholders})
        ORDER BY RANDOM()
        LIMIT 50
    '''

    cur = conn.execute(query, ids_excluir)
    ofertas_nuevas = cur.fetchall()

    print(f"Ofertas seleccionadas: {len(ofertas_nuevas)}")

    # Guardar IDs seleccionados
    ids_nuevos = [row['id_oferta'] for row in ofertas_nuevas]
    ids_file = exports_path / f"50_ofertas_ids_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(ids_file, 'w', encoding='utf-8') as f:
        json.dump(ids_nuevos, f, indent=2)
    print(f"IDs guardados en: {ids_file}")

    # Importar módulos del pipeline
    print("\nCargando módulos del pipeline...")

    try:
        from limpiar_titulos import limpiar_titulo
        print("  [OK] limpiar_titulos")
    except Exception as e:
        print(f"  [WARN] limpiar_titulos: {e}")
        limpiar_titulo = lambda x: x

    try:
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3(db_conn=conn, verbose=False)
        print("  [OK] MatcherV3")
    except Exception as e:
        print(f"  [WARN] MatcherV3: {e}")
        matcher = None

    try:
        from skills_implicit_extractor import SkillsImplicitExtractor
        from skill_categorizer import SkillCategorizer
        extractor = SkillsImplicitExtractor(verbose=False)
        categorizer = SkillCategorizer()
        print("  [OK] Skills extractor + categorizer")
    except Exception as e:
        print(f"  [WARN] Skills: {e}")
        extractor = None
        categorizer = None

    # Datos para sheets
    ofertas_data = []
    skills_data = []
    scraping_data = []

    print(f"\nProcesando {len(ofertas_nuevas)} ofertas...")
    print("-" * 70)

    for i, row in enumerate(ofertas_nuevas, 1):
        id_oferta = str(row['id_oferta'])
        titulo_original = row['titulo'] or ''
        descripcion = row['descripcion'] or ''

        # 1. Limpiar título
        titulo_limpio = limpiar_titulo(titulo_original)

        # 2. Obtener datos NLP existentes (si hay)
        cur_nlp = conn.execute('''
            SELECT * FROM ofertas_nlp WHERE id_oferta = ?
        ''', (id_oferta,))
        nlp_row = cur_nlp.fetchone()

        # Usar datos NLP si existen, sino valores por defecto
        if nlp_row:
            area = nlp_row['area_funcional'] or ''
            seniority = nlp_row['nivel_seniority'] or ''
            tareas = nlp_row['tareas_explicitas'] or ''
            provincia = nlp_row['provincia'] or ''
            localidad = nlp_row['localidad'] or ''
            modalidad = nlp_row['modalidad'] or ''
            sector = nlp_row['sector_empresa'] or ''
            skills_tecnicas = nlp_row['skills_tecnicas_list'] or ''
            soft_skills = nlp_row['soft_skills_list'] or ''
        else:
            area = seniority = tareas = provincia = localidad = modalidad = sector = ''
            skills_tecnicas = soft_skills = ''

        # Guardar datos originales del scraping
        scraping_data.append({
            'ID': id_oferta,
            'Titulo_Original': titulo_original,
            'Empresa': row['empresa'] or '',
            'Localizacion': row['localizacion'] or '',
            'Fecha_Publicacion': row['fecha_publicacion_iso'] or '',
            'Modalidad_Scraping': row['modalidad_trabajo'] or '',
            'Tipo_Trabajo': row['tipo_trabajo'] or '',
            'URL': row['url_oferta'] or '',
            'Descripcion': descripcion[:500] + '...' if len(descripcion) > 500 else descripcion
        })

        # 3. Matching ESCO
        isco_code = ''
        esco_label = ''
        match_score = 0
        match_method = ''

        if matcher and titulo_limpio:
            try:
                oferta = {
                    'titulo_limpio': titulo_limpio,
                    'tareas_explicitas': tareas,
                    'area_funcional': area,
                    'nivel_seniority': seniority
                }
                result = matcher.match(oferta)
                isco_code = result.isco_code
                esco_label = result.esco_label
                match_score = result.score
                match_method = result.method
            except Exception as e:
                pass

        # 4. Skills implícitas
        skills_list = []
        skills_count = 0
        skills_digitales = 0
        L1_counts = {}

        if extractor and categorizer and titulo_limpio:
            try:
                skills = extractor.extract_skills(titulo_limpio=titulo_limpio, tareas_explicitas=tareas)
                skills = categorizer.categorize_batch(skills)
                skills_count = len(skills)

                for s in skills:
                    L1 = s.get('L1', 'T')
                    L1_counts[L1] = L1_counts.get(L1, 0) + 1
                    if s.get('es_digital'):
                        skills_digitales += 1

                    skills_data.append({
                        'ID_Oferta': id_oferta,
                        'Titulo': titulo_limpio[:40],
                        'Skill': s.get('skill_esco', ''),
                        'Score': round(s.get('score', 0), 3),
                        'L1': s.get('L1', ''),
                        'L1_Nombre': s.get('L1_nombre', ''),
                        'L2': s.get('L2', '') or '',
                        'Es_Digital': 'Sí' if s.get('es_digital') else 'No',
                        'Origen': s.get('origen', '')
                    })

                skills_list = [s.get('skill_esco', '') for s in skills[:10]]
            except Exception as e:
                pass

        # Agregar fila con todos los campos
        ofertas_data.append({
            # Identificación
            'ID': id_oferta,
            'Titulo_Original': titulo_original[:60],
            'Titulo_Limpio': titulo_limpio,
            'Empresa': row['empresa'] or '',

            # Ubicación
            'Localidad': localidad,
            'Provincia': provincia,
            'Modalidad': modalidad,

            # Clasificación
            'Sector': sector,
            'Area_Funcional': area,
            'Seniority': seniority,

            # Skills NLP
            'Skills_Tecnicas': skills_tecnicas,
            'Soft_Skills': soft_skills,
            'Tareas': tareas[:150] + '...' if len(tareas) > 150 else tareas,

            # Matching ESCO
            'ISCO_Code': isco_code,
            'Ocupacion_ESCO': esco_label[:60] if esco_label else '',
            'Match_Score': round(match_score, 3) if match_score else '',
            'Match_Method': match_method,

            # Para validación manual
            'Match_OK': '',  # Usuario llena
            'Comentario': '',  # Usuario llena

            # Skills implícitas
            'Skills_Implicitas_Count': skills_count,
            'Skills_Digitales': skills_digitales,
            'L1_S5_Digital': L1_counts.get('S5', 0),
            'L1_T_Transversal': L1_counts.get('T', 0),
            'L1_S6_Tecnicas': L1_counts.get('S6', 0),
            'Top_Skills': '; '.join(skills_list[:5])
        })

        # Progreso
        if i % 10 == 0:
            print(f"  {i}/{len(ofertas_nuevas)} procesadas...")

    # Cerrar matcher
    if matcher:
        matcher.close()
    conn.close()

    # Crear DataFrames
    df_ofertas = pd.DataFrame(ofertas_data)
    df_skills = pd.DataFrame(skills_data)
    df_scraping = pd.DataFrame(scraping_data)

    # Resumen
    total = len(ofertas_data)
    con_matching = len([o for o in ofertas_data if o['ISCO_Code']])
    con_skills = len([o for o in ofertas_data if o['Skills_Implicitas_Count'] > 0])

    resumen_data = [
        {'Metrica': 'Total Ofertas Seleccionadas', 'Valor': total},
        {'Metrica': 'Con Matching ESCO', 'Valor': con_matching},
        {'Metrica': 'Con Skills Implicitas', 'Valor': con_skills},
        {'Metrica': 'Total Skills Extraidas', 'Valor': len(skills_data)},
        {'Metrica': 'Promedio Skills/Oferta', 'Valor': f'{len(skills_data)/total:.1f}' if total > 0 else 0},
        {'Metrica': 'Fecha Export', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M')},
        {'Metrica': 'IDs File', 'Valor': str(ids_file.name)},
    ]
    df_resumen = pd.DataFrame(resumen_data)

    # Exportar
    filename = f"50_ofertas_nuevas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    output_path = exports_path / filename

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        df_ofertas.to_excel(writer, sheet_name='Ofertas_NLP_Matching', index=False)
        df_scraping.to_excel(writer, sheet_name='Scraping_Original', index=False)
        df_skills.to_excel(writer, sheet_name='Skills_Detalle', index=False)

    print()
    print("=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"  Ofertas procesadas: {total}")
    print(f"  Con matching ESCO: {con_matching}")
    print(f"  Skills extraídas: {len(skills_data)}")
    print()
    print(f"  Excel guardado: {output_path}")
    print()
    print("Sheets:")
    print("  1. Resumen - Métricas generales")
    print("  2. Ofertas_NLP_Matching - Datos NLP + Matching (llenar Match_OK/Comentario)")
    print("  3. Scraping_Original - Datos crudos del scraping")
    print("  4. Skills_Detalle - Skills implícitas con categorías L1/L2")
    print()
    print("PRÓXIMO PASO: Revisar Excel y validar Match_OK para cada oferta")

if __name__ == "__main__":
    main()
