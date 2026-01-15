# -*- coding: utf-8 -*-
"""
run_matching_gold_set_100.py - Correr Matching sobre Gold Set NLP 100
=====================================================================

Ejecuta el matching v3 sobre los 100+ IDs del Gold Set NLP y exporta
a Excel para validacion manual.

Input: database/gold_set_nlp_100_ids.json (101 IDs)
Output: Excel con resultados para validacion manual

Uso:
    python run_matching_gold_set_100.py
    python run_matching_gold_set_100.py --verbose
"""

import sys
import io
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))

from match_ofertas_v3 import MatcherV3
from skills_implicit_extractor import SkillsImplicitExtractor
from skill_categorizer import SkillCategorizer


def cargar_gold_set_ids():
    """Carga IDs del Gold Set NLP 100."""
    path = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_gold_set_manual():
    """Carga Gold Set manual con validaciones (49 casos)."""
    path = BASE_DIR / "database" / "gold_set_manual_v2.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {str(caso['id_oferta']): caso for caso in data}
    return {}


def cargar_datos_oferta(id_oferta: str, conn):
    """Carga datos NLP y scraping de una oferta.

    Para registros expandidos (ej: 2123908_2), obtiene descripción
    del registro original (2123908).
    """
    # Intentar JOIN directo primero
    cur = conn.execute('''
        SELECT n.*,
               o.titulo as titulo_original,
               o.descripcion,
               o.empresa,
               o.localizacion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        return dict(row)

    # Si no existe y es un ID expandido (contiene _), buscar datos del original
    if '_' in str(id_oferta):
        id_original = id_oferta.rsplit('_', 1)[0]

        # Obtener datos NLP del registro expandido
        cur = conn.execute('SELECT * FROM ofertas_nlp WHERE id_oferta = ?', (id_oferta,))
        row_nlp = cur.fetchone()
        if not row_nlp:
            return None

        datos = dict(row_nlp)

        # Obtener descripción y otros datos del registro original
        cur = conn.execute('''
            SELECT titulo as titulo_original, descripcion, empresa, localizacion
            FROM ofertas WHERE id_oferta = ?
        ''', (id_original,))
        row_orig = cur.fetchone()
        if row_orig:
            datos['titulo_original'] = row_orig[0]
            datos['descripcion'] = row_orig[1]
            datos['empresa'] = row_orig[2]
            datos['localizacion'] = row_orig[3]

        return datos

    return None


def main():
    parser = argparse.ArgumentParser(description='Matching Gold Set NLP 100')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo detallado')
    args = parser.parse_args()

    print("=" * 70)
    print("MATCHING GOLD SET NLP 100")
    print("=" * 70)

    # Cargar IDs
    gold_ids = cargar_gold_set_ids()
    print(f"IDs a procesar: {len(gold_ids)}")

    # Cargar validaciones existentes (Gold Set 49)
    validaciones = cargar_gold_set_manual()
    print(f"Validaciones existentes: {len(validaciones)} casos")

    # Conectar BD
    db_path = BASE_DIR / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Cargar componentes
    print("\nCargando componentes...")
    matcher = MatcherV3(db_conn=conn, verbose=False)
    extractor = SkillsImplicitExtractor(verbose=False)
    categorizer = SkillCategorizer()
    print("  [OK] Matcher v3, Extractor y Categorizer cargados")

    # Procesar ofertas
    print("\nProcesando ofertas...")
    resultados = []
    skills_detalle = []

    for i, id_oferta in enumerate(gold_ids, 1):
        datos = cargar_datos_oferta(id_oferta, conn)

        if not datos:
            print(f"  [SKIP] {id_oferta} - no encontrado")
            continue

        titulo_limpio = datos.get('titulo_limpio') or ''
        titulo_original = datos.get('titulo_original') or ''
        tareas = datos.get('tareas_explicitas') or ''
        area = datos.get('area_funcional') or ''
        seniority = datos.get('nivel_seniority') or ''
        empresa = datos.get('empresa') or ''
        descripcion = datos.get('descripcion') or ''

        if args.verbose:
            print(f"\n[{i}/{len(gold_ids)}] {id_oferta}: {titulo_limpio[:50]}...")

        # Matching
        oferta = {
            'titulo_limpio': titulo_limpio,
            'tareas_explicitas': tareas,
            'area_funcional': area,
            'nivel_seniority': seniority
        }

        try:
            result = matcher.match(oferta)
            isco_resultado = result.isco_code
            esco_resultado = result.esco_label
            esco_uri = result.esco_uri  # URI completa ESCO para mayor granularidad
            match_score = result.score
            match_method = result.metodo

            # Alternativas
            alts = result.alternativas or []
            alt1 = alts[0] if len(alts) > 0 else {}
            alt2 = alts[1] if len(alts) > 1 else {}
            alt3 = alts[2] if len(alts) > 2 else {}

        except Exception as e:
            isco_resultado = 'ERROR'
            esco_resultado = str(e)
            esco_uri = ''
            match_score = 0
            match_method = 'error'
            alt1, alt2, alt3 = {}, {}, {}

        # Skills extraidas y categorizadas
        try:
            skills = extractor.extract_skills(titulo_limpio=titulo_limpio, tareas_explicitas=tareas)
            # Categorizar skills con L1/L2
            skills = categorizer.categorize_batch(skills)
            skills_count = len(skills)
            top_skills = '; '.join([s.get('skill_esco', '')[:30] for s in skills[:5]])

            # Contar categorías
            cats_l1 = {}
            digital_count = 0
            for s in skills:
                l1 = s.get('L1', 'unknown')
                cats_l1[l1] = cats_l1.get(l1, 0) + 1
                if s.get('es_digital'):
                    digital_count += 1

                skills_detalle.append({
                    'id_oferta': id_oferta,
                    'titulo': titulo_limpio[:40],
                    'skill': s.get('skill_esco', ''),
                    'score': round(s.get('score', 0), 3),
                    'origen': s.get('origen', ''),
                    'L1': s.get('L1', ''),
                    'L1_nombre': s.get('L1_nombre', ''),
                    'L2': s.get('L2', ''),
                    'es_digital': s.get('es_digital', False)
                })

            # Resumen categorías para el registro
            cats_resumen = '; '.join([f"{k}:{v}" for k, v in sorted(cats_l1.items())])
        except:
            skills_count = 0
            top_skills = ''
            cats_resumen = ''
            digital_count = 0

        # Buscar validacion existente
        validacion = validaciones.get(id_oferta, {})
        isco_esperado = validacion.get('isco_esperado', '')
        esco_esperado = validacion.get('esco_esperado', '')
        esco_ok = validacion.get('esco_ok')
        comentario = validacion.get('comentario', '')

        # Determinar estado
        if id_oferta in validaciones:
            # Caso del Gold Set 49
            if esco_ok is True:
                estado = 'OK_validado'
            elif esco_ok is False:
                # Era error, verificar si ahora matchea correctamente
                if isco_esperado and isco_resultado == isco_esperado:
                    estado = 'CORREGIDO'
                else:
                    estado = 'ERROR'
            else:
                estado = 'sin_estado'
        else:
            # Caso nuevo, sin validar
            estado = 'PENDIENTE'

        resultados.append({
            'id_oferta': id_oferta,
            'titulo_original': titulo_original[:60],
            'titulo_limpio': titulo_limpio,
            'descripcion': descripcion[:500],
            'empresa': empresa[:30],
            'area_funcional': area,
            'nivel_seniority': seniority,

            # Resultado matching
            'isco_resultado': isco_resultado,
            'ocupacion_resultado': esco_resultado[:60] if esco_resultado else '',
            'esco_label_completo': esco_resultado or '',  # Label completo sin truncar
            'esco_uri': esco_uri or '',  # URI ESCO para granularidad específica
            'match_score': round(match_score, 3) if match_score else '',
            'match_method': match_method,

            # Alternativas
            'alt1_isco': alt1.get('isco_code', ''),
            'alt1_ocupacion': alt1.get('esco_label', '')[:40] if alt1.get('esco_label') else '',
            'alt2_isco': alt2.get('isco_code', ''),
            'alt2_ocupacion': alt2.get('esco_label', '')[:40] if alt2.get('esco_label') else '',
            'alt3_isco': alt3.get('isco_code', ''),
            'alt3_ocupacion': alt3.get('esco_label', '')[:40] if alt3.get('esco_label') else '',

            # Skills y categorías
            'skills_count': skills_count,
            'top_skills': top_skills,
            'categorias_L1': cats_resumen,
            'skills_digitales': digital_count,

            # Validacion (existente o por completar)
            'isco_esperado': isco_esperado,
            'ocupacion_esperada': esco_esperado,
            'estado': estado,
            'comentario': comentario[:80] if comentario else '',

            # Para validacion manual (completar si PENDIENTE)
            'validar_isco': '' if estado == 'PENDIENTE' else '',
            'validar_ocupacion': '' if estado == 'PENDIENTE' else '',
            'validar_correcto': '' if estado == 'PENDIENTE' else '',
            'validar_comentario': '' if estado == 'PENDIENTE' else ''
        })

        if not args.verbose and i % 20 == 0:
            print(f"  {i}/{len(gold_ids)} procesadas...")

    # Cerrar
    matcher.close()
    conn.close()

    # Crear DataFrames
    df_resultados = pd.DataFrame(resultados)
    df_skills = pd.DataFrame(skills_detalle)

    # Estadisticas
    total = len(resultados)
    ok_validados = len([r for r in resultados if r['estado'] == 'OK_validado'])
    corregidos = len([r for r in resultados if r['estado'] == 'CORREGIDO'])
    errores = len([r for r in resultados if r['estado'] == 'ERROR'])
    pendientes = len([r for r in resultados if r['estado'] == 'PENDIENTE'])

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total ofertas: {total}")
    print(f"  OK validados (Gold Set 49): {ok_validados}")
    print(f"  Corregidos (eran error, ahora OK): {corregidos}")
    print(f"  Errores (siguen mal): {errores}")
    print(f"  PENDIENTES (sin validar): {pendientes}")
    print(f"\nPrecision actual: {100*(ok_validados+corregidos)/(ok_validados+corregidos+errores):.1f}%" if (ok_validados+corregidos+errores) > 0 else "")

    # Resumen para sheet
    resumen_data = [
        {'Metrica': 'Total Ofertas', 'Valor': total},
        {'Metrica': 'Ya Validados OK', 'Valor': ok_validados},
        {'Metrica': 'Corregidos', 'Valor': corregidos},
        {'Metrica': 'Errores', 'Valor': errores},
        {'Metrica': 'PENDIENTES Validar', 'Valor': pendientes},
        {'Metrica': 'Precision Actual', 'Valor': f'{100*(ok_validados+corregidos)/(ok_validados+corregidos+errores):.1f}%' if (ok_validados+corregidos+errores) > 0 else 'N/A'},
        {'Metrica': 'Fecha Export', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M')},
    ]
    df_resumen = pd.DataFrame(resumen_data)

    # Exportar
    output_dir = BASE_DIR / "exports" / "matching_gold_set"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_path = output_dir / f"Matching_Gold_Set_100_{timestamp}.xlsx"

    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        df_resultados.to_excel(writer, sheet_name='Matching_Resultados', index=False)
        df_skills.to_excel(writer, sheet_name='Skills_Detalle', index=False)

        # Ajustar anchos
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

    print(f"\nExcel guardado: {output_path}")
    print("\nSheets:")
    print("  1. Resumen - Metricas generales")
    print("  2. Matching_Resultados - Resultados + columnas para validar")
    print("  3. Skills_Detalle - Skills extraidas por oferta")
    print("\nCOLUMNAS PARA VALIDAR (casos PENDIENTE):")
    print("  - validar_isco: Codigo ISCO correcto")
    print("  - validar_ocupacion: Label ocupacion correcta")
    print("  - validar_correcto: SI/NO")
    print("  - validar_comentario: Notas")


if __name__ == "__main__":
    main()
