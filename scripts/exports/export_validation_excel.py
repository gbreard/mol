#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Validation Excel - Genera Excel por etapa del pipeline para validación humana.

Usa el schema de config/excel_export_schema.json para determinar columnas y sheets.
Lee datos de las tablas persistidas (ofertas, ofertas_nlp, ofertas_esco_matching,
ofertas_esco_skills_detalle).

Uso:
    python export_validation_excel.py --etapa nlp --limit 50
    python export_validation_excel.py --etapa skills --ids 1118027834,1118026729
    python export_validation_excel.py --etapa matching --gold-set
    python export_validation_excel.py --etapa completo --gold-set

Etapas disponibles:
    - nlp: Scraping + NLP + Validacion_NLP
    - skills: Scraping + NLP + Skills_Resumen + Skills_Detalle + Validacion_Skills
    - matching: Scraping + NLP + Skills_Resumen + Matching + Validacion_Matching
    - completo: TODAS las sheets (8 total)
"""

import sys
import io
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Fix encoding for Windows (safe wrapper that handles subprocess)
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (ValueError, AttributeError, OSError):
    pass  # stdout already closed or unavailable


def safe_print(*args, **kwargs):
    """Print function that handles closed stdout gracefully."""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass  # stdout closed, ignore

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
SCHEMA_PATH = PROJECT_ROOT / "config" / "excel_export_schema.json"
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
ESCO_OCCUPATIONS_PATH = PROJECT_ROOT / "database" / "embeddings" / "esco_occupations_full.json"
OUTPUT_DIR = PROJECT_ROOT / "exports" / "validation"

# Cache para lookup ESCO
_ESCO_LOOKUP = None


def get_esco_lookup() -> Dict[str, Dict]:
    """
    Carga lookup de ocupaciones ESCO (uri -> {esco_code, esco_label, isco_code, isco_label}).
    Se cachea para evitar recargar.
    """
    global _ESCO_LOOKUP
    if _ESCO_LOOKUP is None:
        if ESCO_OCCUPATIONS_PATH.exists():
            with open(ESCO_OCCUPATIONS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _ESCO_LOOKUP = {occ['uri']: occ for occ in data.get('occupations', [])}
            safe_print(f"  Cargado lookup ESCO: {len(_ESCO_LOOKUP)} ocupaciones")
        else:
            _ESCO_LOOKUP = {}
            safe_print(f"  WARN: No se encontro {ESCO_OCCUPATIONS_PATH}")
    return _ESCO_LOOKUP


def load_schema() -> Dict:
    """Carga el schema de exportación."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_gold_set_ids() -> List[str]:
    """Carga IDs del Gold Set."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    return [str(caso['id_oferta']) for caso in gold_set]


def get_db_connection() -> sqlite3.Connection:
    """Conexión a SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def verificar_y_filtrar_validadas(offer_ids: List[str], conn: sqlite3.Connection) -> List[str]:
    """
    Verifica si hay ofertas ya validadas en la lista y las excluye con advertencia.

    Args:
        offer_ids: Lista de IDs a verificar
        conn: Conexión a BD

    Returns:
        Lista de IDs sin las ofertas validadas
    """
    if not offer_ids:
        return offer_ids

    placeholders = ','.join(['?'] * len(offer_ids))
    cur = conn.execute(f'''
        SELECT id_oferta FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders})
        AND estado_validacion = 'validado'
    ''', offer_ids)

    validadas = [str(row[0]) for row in cur.fetchall()]

    if validadas:
        safe_print(f"\n  [WARN] Se encontraron {len(validadas)} ofertas YA VALIDADAS en la lista:")
        safe_print(f"         {validadas[:5]}{'...' if len(validadas) > 5 else ''}")
        safe_print(f"         Estas ofertas seran EXCLUIDAS del export.\n")

        # Filtrar validadas
        offer_ids = [oid for oid in offer_ids if oid not in validadas]

    return offer_ids


def get_scraping_data(conn: sqlite3.Connection, offer_ids: List[str], columns: List[str]) -> List[Dict]:
    """Obtiene datos de scraping (tabla ofertas)."""
    # Mapeo de columnas del schema a columnas reales de la BD
    column_mapping = {
        'id_oferta': 'id_oferta',
        'descripcion_utf8': 'descripcion',  # Alias
    }

    # Construir SELECT con columnas disponibles
    available_cols = []
    cur = conn.execute("PRAGMA table_info(ofertas)")
    db_columns = {row[1] for row in cur.fetchall()}

    for col in columns:
        real_col = column_mapping.get(col, col)
        if real_col in db_columns:
            if col != real_col:
                available_cols.append(f"{real_col} as {col}")
            else:
                available_cols.append(col)

    if not available_cols:
        return []

    placeholders = ','.join(['?'] * len(offer_ids))
    query = f"SELECT {', '.join(available_cols)} FROM ofertas WHERE id_oferta IN ({placeholders})"

    cur = conn.execute(query, offer_ids)
    return [dict(row) for row in cur.fetchall()]


def get_nlp_data(conn: sqlite3.Connection, offer_ids: List[str], columns: List[str]) -> List[Dict]:
    """Obtiene datos NLP (tabla ofertas_nlp)."""
    cur = conn.execute("PRAGMA table_info(ofertas_nlp)")
    db_columns = {row[1] for row in cur.fetchall()}

    available_cols = [col for col in columns if col in db_columns]

    if not available_cols:
        return []

    placeholders = ','.join(['?'] * len(offer_ids))
    query = f"SELECT {', '.join(available_cols)} FROM ofertas_nlp WHERE id_oferta IN ({placeholders})"

    cur = conn.execute(query, offer_ids)
    return [dict(row) for row in cur.fetchall()]


def get_skills_detalle_data(conn: sqlite3.Connection, offer_ids: List[str], columns: List[str]) -> List[Dict]:
    """Obtiene datos de skills detalle (tabla ofertas_esco_skills_detalle)."""
    # Columnas que vienen del JSON source_classification
    json_derived_cols = {'L1', 'L1_nombre', 'L2', 'L2_nombre', 'es_digital'}
    needs_json = bool(json_derived_cols & set(columns))

    # Mapeo de columnas del schema a columnas reales de BD
    column_mapping = {
        'skill_esco': 'skill_mencionado',
        'score': 'match_score',
        'origen': 'skill_tipo_fuente',
    }

    cur = conn.execute("PRAGMA table_info(ofertas_esco_skills_detalle)")
    db_columns = {row[1] for row in cur.fetchall()}

    select_parts = ['id_oferta']
    for col in columns:
        if col in json_derived_cols:
            continue  # Se extraen del JSON despues
        if col == 'id_oferta':
            continue  # Ya incluido
        real_col = column_mapping.get(col, col)
        if real_col in db_columns:
            if col != real_col:
                select_parts.append(f"{real_col} as {col}")
            else:
                select_parts.append(col)

    # Siempre incluir source_classification si necesitamos campos JSON
    if needs_json and 'source_classification' not in select_parts:
        select_parts.append('source_classification')

    placeholders = ','.join(['?'] * len(offer_ids))
    query = f"SELECT {', '.join(select_parts)} FROM ofertas_esco_skills_detalle WHERE id_oferta IN ({placeholders})"

    cur = conn.execute(query, offer_ids)
    rows = [dict(row) for row in cur.fetchall()]

    # Post-procesar source_classification para extraer campos L1, L2, es_digital
    for row in rows:
        if needs_json and 'source_classification' in row and row['source_classification']:
            try:
                classification = json.loads(row['source_classification'])
                if 'L1' in columns:
                    row['L1'] = classification.get('L1', '')
                if 'L1_nombre' in columns:
                    row['L1_nombre'] = classification.get('L1_nombre', '')
                if 'L2' in columns:
                    row['L2'] = classification.get('L2', '')
                if 'L2_nombre' in columns:
                    row['L2_nombre'] = classification.get('L2_nombre', '')
                if 'es_digital' in columns:
                    row['es_digital'] = 'Si' if classification.get('es_digital') else 'No'
            except:
                for col in json_derived_cols:
                    if col in columns:
                        row[col] = ''
        # Eliminar source_classification del output final si no es requerido
        if 'source_classification' in row and 'source_classification' not in columns:
            del row['source_classification']

    return rows


def get_skills_resumen_data(conn: sqlite3.Connection, offer_ids: List[str]) -> List[Dict]:
    """Genera resumen de skills por oferta."""
    resumen = []

    for oid in offer_ids:
        cur = conn.execute('''
            SELECT
                skill_mencionado as skill,
                match_score as score,
                esco_skill_type as L1,
                source_classification
            FROM ofertas_esco_skills_detalle
            WHERE id_oferta = ?
            ORDER BY match_score DESC
        ''', (oid,))

        skills = cur.fetchall()

        skills_count = len(skills)
        skills_digitales = 0
        L1_counts = {}
        top_skills = []

        for s in skills:
            # Contar L1
            L1 = s['L1'] or 'T'
            L1_counts[L1] = L1_counts.get(L1, 0) + 1

            # Contar digitales
            try:
                if s['source_classification']:
                    classification = json.loads(s['source_classification'])
                    if classification.get('es_digital'):
                        skills_digitales += 1
            except:
                pass

            # Top skills
            if len(top_skills) < 5:
                top_skills.append(s['skill'])

        resumen.append({
            'id_oferta': oid,
            'skills_count': skills_count,
            'skills_digitales': skills_digitales,
            'categorias_L1': ', '.join(f"{k}:{v}" for k, v in sorted(L1_counts.items())),
            'top_5_skills': '; '.join(top_skills)
        })

    return resumen


def get_matching_data(conn: sqlite3.Connection, offer_ids: List[str], columns: List[str]) -> List[Dict]:
    """Obtiene datos de matching (tabla ofertas_esco_matching).

    Enriquece con esco_code e isco_label desde esco_occupations_full.json usando el URI.
    El JSON tiene los labels ISCO correctos (grupos ISCO-08), mientras que la BD tiene
    los labels de ocupación ESCO.
    """
    # Columnas que se obtienen del lookup JSON (no de BD directamente)
    # isco_label: la BD tiene el label ESCO, queremos el label ISCO-08
    lookup_cols = {'esco_code', 'isco_label'}

    # Mapeo de columnas del schema a columnas reales de BD
    column_mapping = {
        'esco_uri': 'esco_occupation_uri',
        'esco_label': 'esco_occupation_label',
        'match_score': 'occupation_match_score',
        'match_method': 'occupation_match_method',
    }

    cur = conn.execute("PRAGMA table_info(ofertas_esco_matching)")
    db_columns = {row[1] for row in cur.fetchall()}

    # Necesitamos URI y/o isco_code para hacer lookup
    need_lookup = bool(lookup_cols & set(columns))

    select_parts = []
    for col in columns:
        if col in lookup_cols:
            continue  # Se obtiene del lookup
        real_col = column_mapping.get(col, col)
        if real_col in db_columns:
            if col != real_col:
                select_parts.append(f"{real_col} as {col}")
            else:
                select_parts.append(col)
        elif col.startswith('alt'):
            # Alternativas no están en la tabla actual, poner NULL
            select_parts.append(f"NULL as {col}")

    # Asegurar que tenemos el URI para lookup de esco_code
    if need_lookup and 'esco_occupation_uri' not in select_parts and 'esco_occupation_uri as esco_uri' not in select_parts:
        select_parts.append('esco_occupation_uri')

    # Asegurar que tenemos isco_code para lookup de isco_label
    if 'isco_label' in columns and 'isco_code' not in select_parts:
        select_parts.append('isco_code')

    if not select_parts:
        return []

    placeholders = ','.join(['?'] * len(offer_ids))
    query = f"SELECT {', '.join(select_parts)} FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})"

    cur = conn.execute(query, offer_ids)
    rows = [dict(row) for row in cur.fetchall()]

    # Enriquecer con datos del lookup ESCO
    if need_lookup:
        esco_lookup = get_esco_lookup()

        # Cargar tabla de labels ISCO del JSON
        if ESCO_OCCUPATIONS_PATH.exists():
            with open(ESCO_OCCUPATIONS_PATH, 'r', encoding='utf-8') as f:
                esco_data = json.load(f)
            isco_labels = esco_data.get('isco_labels', {})
        else:
            isco_labels = {}

        for row in rows:
            # Obtener URI (puede estar como esco_uri o esco_occupation_uri)
            uri = row.get('esco_uri') or row.get('esco_occupation_uri', '')

            # Lookup esco_code desde URI
            if 'esco_code' in columns:
                if uri and uri in esco_lookup:
                    row['esco_code'] = esco_lookup[uri].get('esco_code', '')
                else:
                    row['esco_code'] = ''

            # Lookup isco_label desde isco_code
            if 'isco_label' in columns:
                isco_code = row.get('isco_code', '')
                if isco_code and isco_code in isco_labels:
                    row['isco_label'] = isco_labels[isco_code]
                else:
                    # Fallback: usar el label del lookup por URI
                    if uri and uri in esco_lookup:
                        row['isco_label'] = esco_lookup[uri].get('isco_label', '')
                    else:
                        row['isco_label'] = ''

            # Limpiar columna temporal si no era requerida
            if 'esco_occupation_uri' in row and 'esco_uri' not in columns and 'esco_occupation_uri' not in columns:
                del row['esco_occupation_uri']

    return rows


def get_control_data(conn: sqlite3.Connection, offer_ids: List[str], columns: List[str]) -> List[Dict]:
    """Obtiene datos combinados para pestaña Control (revision rapida).

    Combina datos de ofertas, ofertas_nlp y ofertas_esco_matching en una sola vista.
    """
    # Cargar lookup ESCO para isco_label y esco_code
    esco_lookup = get_esco_lookup()

    if ESCO_OCCUPATIONS_PATH.exists():
        with open(ESCO_OCCUPATIONS_PATH, 'r', encoding='utf-8') as f:
            esco_data = json.load(f)
        isco_labels = esco_data.get('isco_labels', {})
    else:
        isco_labels = {}

    placeholders = ','.join(['?'] * len(offer_ids))
    query = f"""
        SELECT
            m.id_oferta,
            o.titulo,
            o.empresa,
            m.isco_code,
            m.esco_occupation_uri as esco_uri,
            m.esco_occupation_label as esco_label,
            m.occupation_match_score as match_score,
            n.provincia,
            n.localidad,
            n.sector_empresa,
            n.sector_confianza,
            n.es_intermediario,
            n.clae_code,
            n.clae_seccion,
            n.area_funcional,
            n.nivel_seniority
        FROM ofertas_esco_matching m
        LEFT JOIN ofertas o ON m.id_oferta = o.id_oferta
        LEFT JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        WHERE m.id_oferta IN ({placeholders})
    """

    cur = conn.execute(query, offer_ids)
    rows = [dict(row) for row in cur.fetchall()]

    # Enriquecer con esco_code e isco_label desde lookup
    for row in rows:
        uri = row.get('esco_uri', '')
        isco_code = row.get('isco_code', '')

        # esco_code desde URI
        if uri and uri in esco_lookup:
            row['esco_code'] = esco_lookup[uri].get('esco_code', '')
        else:
            row['esco_code'] = ''

        # isco_label desde isco_code
        if isco_code and isco_code in isco_labels:
            row['isco_label'] = isco_labels[isco_code]
        elif uri and uri in esco_lookup:
            row['isco_label'] = esco_lookup[uri].get('isco_label', '')
        else:
            row['isco_label'] = ''

        # Limpiar URI si no está en columns
        if 'esco_uri' not in columns and 'esco_uri' in row:
            del row['esco_uri']

    return rows


def create_validation_sheet(offer_ids: List[str], validation_type: str) -> List[Dict]:
    """Crea sheet de validación vacía para que humanos completen."""
    schema = load_schema()
    columns = schema['columnas'].get(f'validacion_{validation_type}', [])

    rows = []
    for oid in offer_ids:
        row = {'id_oferta': oid}
        for col in columns:
            if col != 'id_oferta':
                row[col] = ''  # Vacío para que humano complete
        rows.append(row)

    return rows


def export_validation(
    etapa: str,
    offer_ids: List[str] = None,
    use_gold_set: bool = False,
    limit: int = None,
    output_path: str = None
) -> str:
    """
    Exporta Excel de validación para la etapa especificada.

    Args:
        etapa: 'nlp', 'skills', 'matching', o 'completo'
        offer_ids: Lista de IDs específicos
        use_gold_set: Si True, usa IDs del Gold Set
        limit: Límite de ofertas
        output_path: Path de salida (opcional)

    Returns:
        Path del archivo generado
    """
    import pandas as pd

    # Cargar schema
    schema = load_schema()

    if etapa not in schema['etapas']:
        raise ValueError(f"Etapa '{etapa}' no válida. Opciones: {list(schema['etapas'].keys())}")

    etapa_config = schema['etapas'][etapa]

    # Determinar IDs a exportar
    conn = get_db_connection()

    if use_gold_set:
        offer_ids = load_gold_set_ids()
        safe_print(f"Usando Gold Set: {len(offer_ids)} ofertas")
        # Gold Set siempre se exporta completo (sin filtrar validadas)
    elif offer_ids:
        offer_ids = [str(oid) for oid in offer_ids]
        # Verificar y filtrar ofertas ya validadas (con advertencia)
        offer_ids = verificar_y_filtrar_validadas(offer_ids, conn)
    else:
        # Obtener IDs de ofertas con NLP procesado que NO estén validadas ni descartadas
        # FIX: Antes no filtraba por estado_validacion, causando que ofertas ya validadas
        # volvieran a aparecer en lotes nuevos
        cur = conn.execute('''
            SELECT n.id_oferta
            FROM ofertas_nlp n
            LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
            WHERE m.estado_validacion IS NULL
               OR m.estado_validacion NOT IN ('validado', 'descartado')
            ORDER BY n.id_oferta DESC
            LIMIT ?
        ''', (limit or 100,))
        offer_ids = [str(row[0]) for row in cur.fetchall()]
        safe_print(f"  [PROTECCION] Excluidas ofertas con estado 'validado' o 'descartado'")

    if limit:
        offer_ids = offer_ids[:limit]

    safe_print(f"Exportando {len(offer_ids)} ofertas para etapa '{etapa}'...")

    # Generar datos para cada sheet
    sheets_data = {}

    for sheet_name, column_key in etapa_config['sheets'].items():
        safe_print(f"  Generando sheet: {sheet_name}...")

        columns = schema['columnas'].get(column_key, [])

        if column_key == 'scraping':
            data = get_scraping_data(conn, offer_ids, columns)
        elif column_key == 'nlp':
            data = get_nlp_data(conn, offer_ids, columns)
        elif column_key == 'skills_resumen':
            data = get_skills_resumen_data(conn, offer_ids)
        elif column_key == 'skills_detalle':
            data = get_skills_detalle_data(conn, offer_ids, columns)
        elif column_key == 'matching':
            data = get_matching_data(conn, offer_ids, columns)
        elif column_key == 'control':
            data = get_control_data(conn, offer_ids, columns)
        elif column_key.startswith('validacion_'):
            val_type = column_key.replace('validacion_', '')
            data = create_validation_sheet(offer_ids, val_type)
        else:
            data = []

        if data:
            df = pd.DataFrame(data)
            # Reordenar columnas según el schema
            ordered_cols = [col for col in columns if col in df.columns]
            # Agregar columnas extra que no están en el schema al final
            extra_cols = [col for col in df.columns if col not in ordered_cols]
            df = df[ordered_cols + extra_cols]
            sheets_data[sheet_name] = df
            safe_print(f"    -> {len(data)} filas")
        else:
            safe_print(f"    -> Sin datos")

    conn.close()

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generar nombre de archivo
    if output_path:
        output_file = Path(output_path)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = etapa_config['nombre_archivo'].replace('{timestamp}', timestamp)
        output_file = OUTPUT_DIR / filename

    # Escribir Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in sheets_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    safe_print(f"\nExcel generado: {output_file}")
    safe_print(f"Sheets: {list(sheets_data.keys())}")

    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description='Exporta Excel de validación por etapa del pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python export_validation_excel.py --etapa nlp --limit 50
  python export_validation_excel.py --etapa skills --gold-set
  python export_validation_excel.py --etapa matching --ids 1118027834,1118026729
  python export_validation_excel.py --etapa completo --gold-set
        '''
    )

    parser.add_argument('--etapa', required=True,
                        choices=['nlp', 'skills', 'matching', 'completo'],
                        help='Etapa del pipeline a exportar')
    parser.add_argument('--ids', type=str,
                        help='IDs de ofertas separados por coma')
    parser.add_argument('--gold-set', action='store_true',
                        help='Usar ofertas del Gold Set')
    parser.add_argument('--limit', type=int,
                        help='Límite de ofertas a exportar')
    parser.add_argument('--output', type=str,
                        help='Path de salida (opcional)')

    args = parser.parse_args()

    # Parsear IDs si se proporcionaron
    offer_ids = None
    if args.ids:
        offer_ids = [oid.strip() for oid in args.ids.split(',')]

    # Exportar
    output_path = export_validation(
        etapa=args.etapa,
        offer_ids=offer_ids,
        use_gold_set=args.gold_set,
        limit=args.limit,
        output_path=args.output
    )

    safe_print(f"\nListo! Archivo: {output_path}")


if __name__ == "__main__":
    main()
