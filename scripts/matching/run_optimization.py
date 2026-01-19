# -*- coding: utf-8 -*-
"""
run_optimization.py - Script Unificado de Optimizacion NLP/Matching/Skills
==========================================================================

Ejecuta validacion por etapas, exporta a Excel con trazabilidad completa.

Uso:
    # Etapa 1: Validar NLP
    python run_optimization.py --limit 50 --nlp-only

    # Etapa 2: Validar Matching (despues de corregir NLP)
    python run_optimization.py --limit 50 --matching-only

    # Etapa 3: Validar Skills (despues de corregir Matching)
    python run_optimization.py --limit 50 --skills-only

    # IDs especificos
    python run_optimization.py --ids 123,456,789 --nlp-only
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

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))


def cargar_config_export():
    """Carga configuracion de columnas desde JSON."""
    config_path = BASE_DIR / "config" / "excel_export_schema.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_gold_set_manual():
    """Carga Gold Set manual con validaciones (49 casos)."""
    path = BASE_DIR / "database" / "gold_set_manual_v2.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {str(caso['id_oferta']): caso for caso in data}
    return {}


def obtener_ids_desde_bd(conn, limit: int, offset: int = 0):
    """Obtiene IDs de ofertas que tienen NLP procesado."""
    cur = conn.execute('''
        SELECT DISTINCT n.id_oferta
        FROM ofertas_nlp n
        ORDER BY n.id_oferta
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    return [row[0] for row in cur.fetchall()]


def cargar_datos_scraping(ids: list, conn, columnas: list) -> pd.DataFrame:
    """Carga datos de scraping (tabla ofertas) para los IDs dados."""
    if not ids:
        return pd.DataFrame()

    placeholders = ','.join(['?' for _ in ids])
    cols_str = ', '.join([f'o.{c}' for c in columnas if c != 'id_oferta'])

    query = f'''
        SELECT o.id_oferta, {cols_str}
        FROM ofertas o
        WHERE o.id_oferta IN ({placeholders})
        ORDER BY o.id_oferta
    '''

    df = pd.read_sql_query(query, conn, params=ids)
    return df


def cargar_datos_nlp(ids: list, conn, columnas: list) -> pd.DataFrame:
    """Carga datos NLP (tabla ofertas_nlp) para los IDs dados."""
    if not ids:
        return pd.DataFrame()

    placeholders = ','.join(['?' for _ in ids])
    cols_str = ', '.join([f'n.{c}' for c in columnas if c != 'id_oferta'])

    query = f'''
        SELECT n.id_oferta, {cols_str}
        FROM ofertas_nlp n
        WHERE n.id_oferta IN ({placeholders})
        ORDER BY n.id_oferta
    '''

    df = pd.read_sql_query(query, conn, params=ids)
    return df


def ejecutar_matching(ids: list, conn, df_nlp: pd.DataFrame, verbose: bool = False):
    """Ejecuta matching para los IDs dados."""
    from match_ofertas_v3 import MatcherV3

    matcher = MatcherV3(db_conn=conn, verbose=False)
    resultados = []

    for i, id_oferta in enumerate(ids, 1):
        row = df_nlp[df_nlp['id_oferta'] == id_oferta]
        if row.empty:
            continue

        row = row.iloc[0]
        titulo_limpio = row.get('titulo_limpio') or ''
        tareas = row.get('tareas_explicitas') or ''
        area = row.get('area_funcional') or ''
        seniority = row.get('nivel_seniority') or ''

        if verbose and i % 10 == 0:
            print(f"  Matching {i}/{len(ids)}...")

        try:
            oferta = {
                'titulo_limpio': titulo_limpio,
                'tareas_explicitas': tareas,
                'area_funcional': area,
                'nivel_seniority': seniority
            }
            result = matcher.match(oferta)

            alts = result.alternativas or []
            alt1 = alts[0] if len(alts) > 0 else {}
            alt2 = alts[1] if len(alts) > 1 else {}
            alt3 = alts[2] if len(alts) > 2 else {}

            resultados.append({
                'id_oferta': id_oferta,
                'isco_resultado': result.isco_code,
                'esco_label': result.esco_label,
                'esco_uri': result.esco_uri or '',
                'match_score': round(result.score, 3) if result.score else 0,
                'match_method': result.metodo,
                'alt1_isco': alt1.get('isco_code', ''),
                'alt1_label': alt1.get('esco_label', ''),
                'alt1_score': round(alt1.get('score', 0), 3) if alt1.get('score') else '',
                'alt2_isco': alt2.get('isco_code', ''),
                'alt2_label': alt2.get('esco_label', ''),
                'alt2_score': round(alt2.get('score', 0), 3) if alt2.get('score') else '',
                'alt3_isco': alt3.get('isco_code', ''),
                'alt3_label': alt3.get('esco_label', ''),
                'alt3_score': round(alt3.get('score', 0), 3) if alt3.get('score') else '',
            })
        except Exception as e:
            resultados.append({
                'id_oferta': id_oferta,
                'isco_resultado': 'ERROR',
                'esco_label': str(e)[:100],
                'esco_uri': '',
                'match_score': 0,
                'match_method': 'error',
                'alt1_isco': '', 'alt1_label': '', 'alt1_score': '',
                'alt2_isco': '', 'alt2_label': '', 'alt2_score': '',
                'alt3_isco': '', 'alt3_label': '', 'alt3_score': '',
            })

    matcher.close()
    return pd.DataFrame(resultados)


def ejecutar_skills(ids: list, df_nlp: pd.DataFrame, verbose: bool = False):
    """Extrae skills implicitas para los IDs dados."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    from skill_categorizer import SkillCategorizer

    extractor = SkillsImplicitExtractor(verbose=False)
    categorizer = SkillCategorizer()

    resumen = []
    detalle = []

    for i, id_oferta in enumerate(ids, 1):
        row = df_nlp[df_nlp['id_oferta'] == id_oferta]
        if row.empty:
            continue

        row = row.iloc[0]
        titulo_limpio = row.get('titulo_limpio') or ''
        tareas = row.get('tareas_explicitas') or ''

        if verbose and i % 10 == 0:
            print(f"  Skills {i}/{len(ids)}...")

        try:
            skills = extractor.extract_skills(titulo_limpio=titulo_limpio, tareas_explicitas=tareas)
            skills = categorizer.categorize_batch(skills)

            cats_l1 = {}
            digital_count = 0
            top_5 = []

            for s in skills:
                l1 = s.get('L1', 'unknown')
                cats_l1[l1] = cats_l1.get(l1, 0) + 1
                if s.get('es_digital'):
                    digital_count += 1
                if len(top_5) < 5:
                    top_5.append(s.get('skill_esco', '')[:30])

                detalle.append({
                    'id_oferta': id_oferta,
                    'skill_esco': s.get('skill_esco', ''),
                    'score': round(s.get('score', 0), 3),
                    'origen': s.get('origen', ''),
                    'L1': s.get('L1', ''),
                    'L1_nombre': s.get('L1_nombre', ''),
                    'L2': s.get('L2', ''),
                    'es_digital': s.get('es_digital', False)
                })

            resumen.append({
                'id_oferta': id_oferta,
                'skills_count': len(skills),
                'skills_digitales': digital_count,
                'categorias_L1': '; '.join([f"{k}:{v}" for k, v in sorted(cats_l1.items())]),
                'top_5_skills': '; '.join(top_5)
            })
        except Exception as e:
            resumen.append({
                'id_oferta': id_oferta,
                'skills_count': 0,
                'skills_digitales': 0,
                'categorias_L1': f'ERROR: {str(e)[:50]}',
                'top_5_skills': ''
            })

    return pd.DataFrame(resumen), pd.DataFrame(detalle)


def crear_df_validacion(ids: list, tipo: str, gold_set: dict) -> pd.DataFrame:
    """Crea DataFrame de validacion con columnas vacias para completar."""
    rows = []
    for id_oferta in ids:
        val = gold_set.get(str(id_oferta), {})

        if tipo == 'nlp':
            rows.append({
                'id_oferta': id_oferta,
                'nlp_correcto': '',
                'nlp_comentario': ''
            })
        elif tipo == 'matching':
            rows.append({
                'id_oferta': id_oferta,
                'isco_esperado': val.get('isco_esperado', ''),
                'esco_esperado': val.get('esco_esperado', ''),
                'estado': 'PENDIENTE' if id_oferta not in gold_set else ('OK' if val.get('esco_ok') else 'ERROR'),
                'matching_correcto': '',
                'matching_comentario': val.get('comentario', '')
            })
        elif tipo == 'skills':
            rows.append({
                'id_oferta': id_oferta,
                'skills_correcto': '',
                'skills_comentario': ''
            })

    return pd.DataFrame(rows)


def ajustar_anchos_excel(writer):
    """Ajusta anchos de columnas en todas las sheets."""
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


def exportar_excel(etapa: str, config: dict, dataframes: dict, output_dir: Path):
    """Exporta Excel segun configuracion de etapa."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    nombre_archivo = config['etapas'][etapa]['nombre_archivo'].replace('{timestamp}', timestamp)
    output_path = output_dir / nombre_archivo

    sheets_config = config['etapas'][etapa]['sheets']

    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        for sheet_name, col_key in sheets_config.items():
            if col_key in dataframes and not dataframes[col_key].empty:
                dataframes[col_key].to_excel(writer, sheet_name=sheet_name, index=False)

        ajustar_anchos_excel(writer)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Script unificado de optimizacion NLP/Matching/Skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  %(prog)s --limit 50 --nlp-only        # Validar NLP para 50 ofertas
  %(prog)s --limit 50 --matching-only   # Validar Matching para 50 ofertas
  %(prog)s --limit 50 --skills-only     # Validar Skills para 50 ofertas
  %(prog)s --ids 123,456 --nlp-only     # Validar NLP para IDs especificos
        '''
    )

    # Seleccion de ofertas
    parser.add_argument('--limit', type=int, help='Procesar N ofertas desde BD')
    parser.add_argument('--offset', type=int, default=0, help='Offset para --limit (default: 0)')
    parser.add_argument('--ids', type=str, help='IDs especificos separados por coma')

    # Modo de ejecucion (mutuamente excluyentes)
    grupo_modo = parser.add_mutually_exclusive_group(required=True)
    grupo_modo.add_argument('--nlp-only', action='store_true', help='Solo validar NLP')
    grupo_modo.add_argument('--matching-only', action='store_true', help='Solo validar Matching')
    grupo_modo.add_argument('--skills-only', action='store_true', help='Solo validar Skills')

    # Opciones
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo detallado')
    parser.add_argument('--no-export', action='store_true', help='No exportar Excel')

    args = parser.parse_args()

    if not args.limit and not args.ids:
        parser.error("Especificar --limit N o --ids ID1,ID2,...")

    # Determinar etapa
    if args.nlp_only:
        etapa = "nlp"
    elif args.matching_only:
        etapa = "matching"
    else:
        etapa = "skills"

    print("=" * 70)
    print(f"OPTIMIZACION - ETAPA: {etapa.upper()}")
    print("=" * 70)

    # Cargar configuracion
    config = cargar_config_export()
    print(f"Config cargada: {len(config['columnas'])} grupos de columnas")

    # Conectar BD
    db_path = BASE_DIR / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Obtener IDs
    if args.ids:
        ids_a_procesar = [id.strip() for id in args.ids.split(',')]
        print(f"IDs especificados: {len(ids_a_procesar)}")
    else:
        ids_a_procesar = obtener_ids_desde_bd(conn, args.limit, args.offset)
        print(f"IDs desde BD (limit={args.limit}, offset={args.offset}): {len(ids_a_procesar)}")

    if not ids_a_procesar:
        print("No hay ofertas para procesar")
        conn.close()
        return

    # Cargar gold set
    gold_set = cargar_gold_set_manual()
    print(f"Gold Set cargado: {len(gold_set)} casos")

    # =================================================================
    # CARGAR DATOS SEGUN ETAPA
    # =================================================================
    dataframes = {}

    # Sheet 1: Scraping (siempre)
    print("\nCargando datos de scraping...")
    cols_scraping = config['columnas']['scraping']
    df_scraping = cargar_datos_scraping(ids_a_procesar, conn, cols_scraping)
    dataframes['scraping'] = df_scraping
    print(f"  -> {len(df_scraping)} filas, {len(df_scraping.columns)} columnas")

    # Sheet 2: NLP (siempre)
    print("Cargando datos NLP...")
    cols_nlp = config['columnas']['nlp']
    df_nlp = cargar_datos_nlp(ids_a_procesar, conn, cols_nlp)
    dataframes['nlp'] = df_nlp
    print(f"  -> {len(df_nlp)} filas, {len(df_nlp.columns)} columnas")

    # Sheet 3: Matching (si matching o skills)
    if etapa in ['matching', 'skills']:
        print("Ejecutando matching...")
        df_matching = ejecutar_matching(ids_a_procesar, conn, df_nlp, args.verbose)
        dataframes['matching'] = df_matching
        print(f"  -> {len(df_matching)} resultados")

    # Sheets 4-5: Skills (si skills)
    if etapa == 'skills':
        print("Extrayendo skills...")
        df_skills_resumen, df_skills_detalle = ejecutar_skills(ids_a_procesar, df_nlp, args.verbose)
        dataframes['skills_resumen'] = df_skills_resumen
        dataframes['skills_detalle'] = df_skills_detalle
        print(f"  -> {len(df_skills_resumen)} ofertas, {len(df_skills_detalle)} skills totales")

    # Sheet Validacion
    print("Creando sheet de validacion...")
    if etapa == 'nlp':
        dataframes['validacion_nlp'] = crear_df_validacion(ids_a_procesar, 'nlp', gold_set)
    elif etapa == 'matching':
        dataframes['validacion_matching'] = crear_df_validacion(ids_a_procesar, 'matching', gold_set)
    else:
        dataframes['validacion_skills'] = crear_df_validacion(ids_a_procesar, 'skills', gold_set)

    conn.close()

    # =================================================================
    # ESTADISTICAS
    # =================================================================
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Etapa: {etapa.upper()}")
    print(f"Total ofertas: {len(ids_a_procesar)}")

    if 'matching' in dataframes:
        df_m = dataframes['matching']
        errores = len(df_m[df_m['isco_resultado'] == 'ERROR'])
        print(f"Matching ejecutado: {len(df_m)} ({errores} errores)")

    if 'skills_resumen' in dataframes:
        df_s = dataframes['skills_resumen']
        total_skills = df_s['skills_count'].sum()
        print(f"Skills extraidas: {total_skills} total")

    # =================================================================
    # EXPORTAR
    # =================================================================
    if not args.no_export:
        output_dir = BASE_DIR / config.get('output_dir', 'exports/optimization')
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = exportar_excel(etapa, config, dataframes, output_dir)
        print(f"\nExcel guardado: {output_path}")

        # Mostrar sheets generadas
        print("\nSheets generadas:")
        for sheet_name in config['etapas'][etapa]['sheets'].keys():
            print(f"  - {sheet_name}")


if __name__ == "__main__":
    main()
