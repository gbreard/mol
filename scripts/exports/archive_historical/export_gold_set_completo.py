#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Gold Set Completo con NLP corregido + Matching ESCO + Skills L1/L2
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
    print("EXPORT GOLD SET COMPLETO")
    print("NLP Corregido + Matching ESCO + Skills Categorizadas")
    print("=" * 70)

    # Paths
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    exports_path = Path(__file__).parent.parent / "exports"
    exports_path.mkdir(exist_ok=True)

    # Cargar Gold Set
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    print(f"\nProcesando {len(gold_set)} ofertas del Gold Set...")

    # Conectar BD
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Importar módulos de matching y skills
    try:
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3(db_conn=conn, verbose=False)
        print("  [OK] Matcher v3 cargado")
    except Exception as e:
        print(f"  [WARN] No se pudo cargar Matcher v2: {e}")
        matcher = None

    try:
        from skills_implicit_extractor import SkillsImplicitExtractor
        from skill_categorizer import SkillCategorizer
        extractor = SkillsImplicitExtractor(verbose=False)
        categorizer = SkillCategorizer()
        print("  [OK] Extractor de skills cargado")
    except Exception as e:
        print(f"  [WARN] No se pudo cargar extractor: {e}")
        extractor = None
        categorizer = None

    # Datos para sheets
    ofertas_data = []
    skills_data = []
    scraping_data = []  # Datos originales del scraping

    print("\nProcesando ofertas...")

    for i, caso in enumerate(gold_set, 1):
        id_oferta = str(caso['id_oferta'])
        esco_ok = caso.get('esco_ok', True)  # True = matching validado como correcto
        comentario_gold = caso.get('comentario', '')

        # Obtener datos NLP y scraping
        cur = conn.execute('''
            SELECT n.*,
                   o.titulo as titulo_original,
                   o.descripcion,
                   o.empresa,
                   o.localizacion,
                   o.fecha_publicacion_iso,
                   o.url_oferta,
                   o.modalidad_trabajo,
                   o.tipo_trabajo
            FROM ofertas_nlp n
            JOIN ofertas o ON n.id_oferta = o.id_oferta
            WHERE n.id_oferta = ?
        ''', (id_oferta,))
        row = cur.fetchone()

        if not row:
            print(f"  [SKIP] {id_oferta} - no encontrado")
            continue

        # Guardar datos originales del scraping
        scraping_data.append({
            'ID': id_oferta,
            'Titulo_Original': row['titulo_original'] or '',
            'Empresa': row['empresa'] or '',
            'Localizacion': row['localizacion'] or '',
            'Fecha_Publicacion': row['fecha_publicacion_iso'] or '',
            'Modalidad_Scraping': row['modalidad_trabajo'] or '',
            'Tipo_Trabajo': row['tipo_trabajo'] or '',
            'URL': row['url_oferta'] or '',
            'Descripcion_Completa': row['descripcion'] or ''
        })

        # Extraer campos
        titulo_limpio = row['titulo_limpio'] or ''
        titulo_original = row['titulo_original'] or ''
        tareas = row['tareas_explicitas'] or ''
        area = row['area_funcional'] or ''
        seniority = row['nivel_seniority'] or ''

        # Matching ESCO
        isco_code = ''
        esco_label = ''
        match_score = 0
        match_method = ''

        if matcher:
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

        # Skills
        skills_list = []
        skills_count = 0
        skills_digitales = 0
        L1_counts = {}

        if extractor and categorizer:
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

        # Verificar matching (usa validación manual del gold set)
        match_ok = '✓' if esco_ok else '✗'

        # Agregar fila con todos los campos NLP relevantes
        ofertas_data.append({
            # Identificación
            'ID': id_oferta,
            'Titulo_Original': titulo_original[:60],
            'Titulo_Limpio': titulo_limpio,
            'Empresa': row['empresa'] or '',

            # Ubicación
            'Localidad': row['localidad'] or '',
            'Provincia': row['provincia'] or '',
            'Modalidad': row['modalidad'] or '',
            'Zona_Residencia_Req': row['zona_residencia_req'] or '',

            # Clasificación
            'Sector': row['sector_empresa'] or '',
            'Area_Funcional': area,
            'Seniority': seniority,
            'Tipo_Contrato': row['tipo_contrato'] or '',
            'Jornada_Laboral': row['jornada_laboral'] or '',
            'Tipo_Oferta': row['tipo_oferta'] or '',

            # Requisitos persona
            'Requisito_Sexo': row['requisito_sexo'] or row['requerimiento_sexo'] or '',
            'Requisito_Edad_Min': row['requisito_edad_min'],
            'Requisito_Edad_Max': row['requisito_edad_max'],
            'Nivel_Educativo': row['nivel_educativo'] or '',
            'Titulo_Excluyente': row['titulo_excluyente'] or '',
            'Carrera_Especifica': row['carrera_especifica'] or '',

            # Experiencia
            'Experiencia_Min': row['experiencia_min_anios'],
            'Experiencia_Max': row['experiencia_max_anios'],
            'Experiencia_Area': row['experiencia_area'] or '',

            # Idiomas
            'Idioma_Principal': row['idioma_principal'] or '',
            'Nivel_Idioma': row['nivel_idioma_principal'] or '',

            # Licencias y movilidad
            'Licencia_Conducir': row['licencia_conducir'] or '',
            'Tipo_Licencia': row['tipo_licencia'] or '',
            'Requiere_Movilidad': row['requiere_movilidad_propia'] or '',
            'Requiere_Viajar': row['requiere_viajar'] or '',

            # Condiciones trabajo
            'Horario_Flexible': row['horario_flexible'] or '',
            'Turnos_Rotativos': row['trabajo_turnos_rotativos'] or '',
            'Fines_Semana': row['trabajo_fines_semana'] or '',
            'Tiene_Gente_Cargo': row['tiene_gente_cargo'] or '',

            # Salario
            'Salario_Min': row['salario_min'],
            'Salario_Max': row['salario_max'],
            'Moneda': row['moneda'] or '',

            # Skills y tareas
            'Tareas': tareas[:150] + '...' if len(tareas) > 150 else tareas,
            'Skills_Tecnicas': row['skills_tecnicas_list'] or '',
            'Soft_Skills': row['soft_skills_list'] or '',
            'Certificaciones': row['certificaciones_list'] or '',
            'Beneficios': row['beneficios_list'] or '',

            # Matching ESCO
            'ISCO_Code': isco_code,
            'Ocupacion_ESCO': esco_label[:60] if esco_label else '',
            'Match_Score': round(match_score, 3) if match_score else '',
            'Match_Method': match_method,
            'Gold_Set_OK': match_ok,
            'Comentario_Validacion': comentario_gold[:80] if comentario_gold else '',

            # Skills implícitas
            'Skills_Implicitas_Count': skills_count,
            'Skills_Digitales': skills_digitales,
            'L1_S5_Digital': L1_counts.get('S5', 0),
            'L1_T_Transversal': L1_counts.get('T', 0),
            'L1_S6_Tecnicas': L1_counts.get('S6', 0),
            'L1_S4_Gestion': L1_counts.get('S4', 0),
            'Top_Skills': '; '.join(skills_list[:5])
        })

        if i % 10 == 0:
            print(f"  {i}/{len(gold_set)} procesadas...")

    # Cerrar matcher
    if matcher:
        matcher.close()
    conn.close()

    # Crear DataFrames
    df_ofertas = pd.DataFrame(ofertas_data)
    df_skills = pd.DataFrame(skills_data)
    df_scraping = pd.DataFrame(scraping_data)

    # Calcular estadísticas
    total = len(ofertas_data)
    correctos = len([o for o in ofertas_data if o['Gold_Set_OK'] == '✓'])
    precision = 100 * correctos / total if total > 0 else 0

    # Resumen
    resumen_data = [
        {'Metrica': 'Total Ofertas', 'Valor': total},
        {'Metrica': 'Matching Correcto', 'Valor': correctos},
        {'Metrica': 'Precision Matching', 'Valor': f'{precision:.1f}%'},
        {'Metrica': 'Total Skills Extraidas', 'Valor': len(skills_data)},
        {'Metrica': 'Promedio Skills/Oferta', 'Valor': f'{len(skills_data)/total:.1f}' if total > 0 else 0},
        {'Metrica': 'Fecha Export', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M')},
    ]
    df_resumen = pd.DataFrame(resumen_data)

    # Exportar
    filename = f"gold_set_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
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
    print(f"  Matching correcto: {correctos}/{total} ({precision:.1f}%)")
    print(f"  Skills extraídas: {len(skills_data)}")
    print()
    print(f"  Excel guardado: {output_path}")
    print()
    print("Sheets:")
    print("  1. Resumen - Métricas generales")
    print("  2. Ofertas_NLP_Matching - Todos los campos NLP + Matching")
    print("  3. Scraping_Original - Datos crudos del scraping (titulo, descripcion, etc)")
    print("  4. Skills_Detalle - Skills implícitas con categorías L1/L2")

if __name__ == "__main__":
    main()
