#!/usr/bin/env python3
"""
Generador de CSV para Shiny Dashboard desde Base de Datos
==========================================================

Genera CSV completo desde bumeran_scraping.db con:
- Todas las 5,704 ofertas
- Datos NLP (v4.0 o v5.1 activos)
- Matching ESCO BGE-M3
- Variable temporal fecha_publicacion
- Skills en formato pipe-separated
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def skills_to_string(skills_val) -> str:
    """
    Convierte lista de skills (JSON o Python list) a string separado por ' | '
    """
    if skills_val is None or skills_val == '' or skills_val == '[]':
        return ""

    try:
        # Si es string que parece JSON
        if isinstance(skills_val, str):
            if skills_val.startswith('['):
                skills_list = json.loads(skills_val)
            else:
                # Ya es string simple
                return skills_val.strip()
        elif isinstance(skills_val, list):
            skills_list = skills_val
        else:
            return str(skills_val).strip() if skills_val else ""

        # Filtrar None y vacíos
        if isinstance(skills_list, list):
            skills_clean = [str(s).strip() for s in skills_list if s and str(s).strip()]
            return " | ".join(skills_clean) if skills_clean else ""
        else:
            return str(skills_list).strip()

    except:
        return str(skills_val).strip() if skills_val else ""


def parsear_extracted_data(extracted_json: str) -> Dict[str, Any]:
    """
    Parsea el JSON de extracted_data de ofertas_nlp_history
    Retorna diccionario con campos extraídos
    """
    if not extracted_json:
        return {}

    try:
        data = json.loads(extracted_json)
        return {
            'soft_skills': skills_to_string(data.get('soft_skills_list')),
            'soft_skills_count': len(data.get('soft_skills_list', [])) if isinstance(data.get('soft_skills_list'), list) else 0,
            'skills_tecnicas': skills_to_string(data.get('skills_tecnicas_list')),
            'skills_tecnicas_count': len(data.get('skills_tecnicas_list', [])) if isinstance(data.get('skills_tecnicas_list'), list) else 0,
            'nivel_educativo': data.get('nivel_educativo', ''),
            'experiencia_min_anios': data.get('experiencia_min_anios'),
            'experiencia_max_anios': data.get('experiencia_max_anios'),
            'idioma_principal': data.get('idioma_principal', ''),
            'certificaciones_list': skills_to_string(data.get('certificaciones_list'))
        }
    except Exception as e:
        print(f"  [!] Error parseando extracted_data: {e}")
        return {}


def parsear_esco_skills(esco_skills_json: str) -> tuple:
    """
    Parsea JSON de skills ESCO esenciales/opcionales
    Retorna (string_pipe_separated, count)
    """
    if not esco_skills_json or esco_skills_json == '[]':
        return ("", 0)

    try:
        skills_list = json.loads(esco_skills_json)
        if not isinstance(skills_list, list):
            return ("", 0)

        # Filtrar y limpiar
        skills_clean = [str(s).strip() for s in skills_list if s and str(s).strip()]

        if skills_clean:
            return (" | ".join(skills_clean), len(skills_clean))
        else:
            return ("", 0)

    except:
        return ("", 0)


def obtener_codigo_isco_desde_uri(uri: str) -> str:
    """
    Extrae código ISCO-08 del URI ESCO
    Ejemplo: 'http://data.europa.eu/esco/isco/C2422' -> '2422'
    """
    if not uri:
        return ""

    try:
        # El código está después de 'isco/C'
        if '/isco/C' in uri:
            code = uri.split('/isco/C')[-1]
            return code
        return ""
    except:
        return ""


def main():
    print("=" * 100)
    print("GENERADOR DE CSV PARA SHINY DASHBOARD")
    print("Fuente: bumeran_scraping.db (Matching ESCO BGE-M3)")
    print("=" * 100)
    print()

    conn = conectar_db()

    # === 1. QUERY PRINCIPAL CON JOINS ===
    print("[1/6] Cargando datos desde base de datos...")

    query = """
    SELECT
        o.id_oferta,
        o.titulo,
        o.empresa,
        o.descripcion,
        o.localizacion,
        o.url_oferta,
        o.fecha_publicacion_datetime AS fecha_publicacion,
        o.portal AS fuente,

        -- NLP History (extracción activa v4.0 o v5.1)
        h.extracted_data,
        h.nlp_version,

        -- ESCO Matching (BGE-M3)
        e.esco_occupation_uri,
        e.esco_occupation_label,
        e.occupation_match_score,
        e.occupation_match_method,
        e.esco_skills_esenciales_json,
        e.esco_skills_opcionales_json,
        e.confidence_score AS esco_confidence,

        -- ESCO Occupation details
        esc.preferred_label_es AS esco_preferred_label,
        esc.isco_code AS esco_isco_code

    FROM ofertas o

    LEFT JOIN ofertas_nlp_history h
        ON o.id_oferta = h.id_oferta
        AND h.is_active = 1

    LEFT JOIN ofertas_esco_matching e
        ON o.id_oferta = e.id_oferta

    LEFT JOIN esco_occupations esc
        ON e.esco_occupation_uri = esc.occupation_uri

    ORDER BY o.id_oferta
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"  Ofertas cargadas: {len(df):,}")
    print(f"  Con NLP activo: {df['extracted_data'].notna().sum():,}")
    print(f"  Con ESCO matching: {df['esco_occupation_label'].notna().sum():,}")

    # === 2. PARSEAR EXTRACTED_DATA (NLP) ===
    print()
    print("[2/6] Parseando datos NLP extraídos...")

    nlp_data = df['extracted_data'].apply(lambda x: parsear_extracted_data(x) if pd.notna(x) else {})

    df['soft_skills'] = nlp_data.apply(lambda x: x.get('soft_skills', ''))
    df['soft_skills_count'] = nlp_data.apply(lambda x: x.get('soft_skills_count', 0))
    df['skills_tecnicas'] = nlp_data.apply(lambda x: x.get('skills_tecnicas', ''))
    df['skills_tecnicas_count'] = nlp_data.apply(lambda x: x.get('skills_tecnicas_count', 0))
    df['nivel_educativo'] = nlp_data.apply(lambda x: x.get('nivel_educativo', ''))
    df['experiencia_min_anios'] = nlp_data.apply(lambda x: x.get('experiencia_min_anios'))
    df['experiencia_max_anios'] = nlp_data.apply(lambda x: x.get('experiencia_max_anios'))
    df['idioma_principal'] = nlp_data.apply(lambda x: x.get('idioma_principal', ''))
    df['certificaciones_list'] = nlp_data.apply(lambda x: x.get('certificaciones_list', ''))

    print(f"  OK: Campos NLP parseados")

    # === 3. PARSEAR ESCO SKILLS ===
    print()
    print("[3/6] Parseando skills ESCO...")

    esco_esenciales = df['esco_skills_esenciales_json'].apply(parsear_esco_skills)
    esco_opcionales = df['esco_skills_opcionales_json'].apply(parsear_esco_skills)

    df['esco_skills_esenciales'] = esco_esenciales.apply(lambda x: x[0])
    df['esco_skills_esenciales_count'] = esco_esenciales.apply(lambda x: x[1])
    df['esco_skills_opcionales'] = esco_opcionales.apply(lambda x: x[0])
    df['esco_skills_opcionales_count'] = esco_opcionales.apply(lambda x: x[1])
    df['esco_skills_total_count'] = df['esco_skills_esenciales_count'] + df['esco_skills_opcionales_count']

    print(f"  OK: Skills ESCO parseadas")

    # === 4. PROCESAR FECHAS Y CREAR COLUMNAS CALCULADAS ===
    print()
    print("[4/6] Creando columnas calculadas...")

    # Fecha publicación y periodo
    df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
    df['periodo'] = df['fecha_publicacion'].dt.strftime('%Y-%m-%d')

    # Rellenar fecha_publicacion faltante con fecha actual
    df['fecha_publicacion'] = df['fecha_publicacion'].fillna(pd.Timestamp.now())
    df['periodo'] = df['periodo'].fillna(datetime.now().strftime('%Y-%m-%d'))

    # Código ISCO desde URI o desde campo directo
    df['claude_isco_code'] = df['esco_isco_code'].fillna('')

    # Si no hay código ISCO, intentar extraer del URI
    mask_sin_isco = (df['claude_isco_code'] == '') & (df['esco_occupation_uri'].notna())
    if mask_sin_isco.sum() > 0:
        df.loc[mask_sin_isco, 'claude_isco_code'] = df.loc[mask_sin_isco, 'esco_occupation_uri'].apply(obtener_codigo_isco_desde_uri)

    # LIMPIAR: Remover prefijo 'C' de códigos ISCO si existe
    df['claude_isco_code'] = df['claude_isco_code'].astype(str).str.replace('^C', '', regex=True)

    # Remover '.0' de códigos ISCO (pueden quedar como float)
    df['claude_isco_code'] = df['claude_isco_code'].str.replace('\\.0$', '', regex=True)

    # Niveles ISCO (ahora sin el prefijo 'C' y sin decimales)
    df['isco_nivel1'] = df['claude_isco_code'].astype(str).str[0]
    df['isco_nivel2'] = df['claude_isco_code'].astype(str).str[:2]
    df['isco_4d'] = df['claude_isco_code'].astype(str).str.split('.').str[0]

    # Reemplazar valores vacíos y 'nan' con None para evitar problemas en R
    df['isco_nivel1'] = df['isco_nivel1'].replace(['', 'n'], None)
    df['isco_nivel2'] = df['isco_nivel2'].replace(['', 'na'], None)
    df['isco_4d'] = df['isco_4d'].replace(['', 'nan'], None)

    # Nombres ISCO nivel 1
    isco1_labels = {
        '1': 'Directores y gerentes',
        '2': 'Profesionales',
        '3': 'Técnicos y profesionales de nivel medio',
        '4': 'Personal de apoyo administrativo',
        '5': 'Trabajadores de servicios y ventas',
        '6': 'Agricultores y trabajadores agropecuarios',
        '7': 'Oficiales, operarios y artesanos',
        '8': 'Operadores de instalaciones y máquinas',
        '9': 'Ocupaciones elementales'
    }
    df['isco_nivel1_nombre'] = df['isco_nivel1'].map(isco1_labels)

    # Skills totales parseadas
    df['skills_parseadas_total'] = df['soft_skills_count'] + df['skills_tecnicas_count']

    # Flags útiles
    df['tiene_url'] = df['url_oferta'].notna()
    df['tiene_skills_parseadas'] = (df['soft_skills'].notna()) & (df['soft_skills'] != '')
    df['tiene_skills_esco'] = (df['esco_skills_total_count'] > 0)

    # Separar localización en provincia y localidad
    # Formato esperado: "Localidad, Provincia" o solo "Localidad"
    def separar_localizacion(loc_str):
        """
        Separa localización en (localidad, provincia)
        Ejemplos:
          '11 de Septiembre, Buenos Aires' -> ('11 de Septiembre', 'Buenos Aires')
          'Capital Federal' -> ('Capital Federal', 'CABA')
          None -> ('', '')
        """
        if pd.isna(loc_str) or not loc_str:
            return ('', '')

        loc_str = str(loc_str).strip()

        # Si contiene coma, separar
        if ',' in loc_str:
            parts = loc_str.split(',', 1)
            localidad = parts[0].strip()
            provincia = parts[1].strip()
            return (localidad, provincia)
        else:
            # Si no tiene coma, solo tenemos localidad
            # Casos especiales
            if loc_str in ['Capital Federal', 'CABA', 'Ciudad de Buenos Aires']:
                return (loc_str, 'CABA')
            else:
                # Dejamos localidad y provincia vacía
                return (loc_str, '')

    # Aplicar separación
    loc_separada = df['localizacion'].apply(separar_localizacion)
    df['localidad'] = loc_separada.apply(lambda x: x[0])
    df['provincia'] = loc_separada.apply(lambda x: x[1])

    # Columnas adicionales (compatibilidad con Shiny anterior)
    df['source_id'] = df['id_oferta']  # Alias
    df['claude_esco_id'] = df['esco_occupation_uri']
    df['claude_esco_label'] = df['esco_occupation_label']
    df['claude_confidence'] = df['esco_confidence']
    df['claude_razonamiento'] = ""  # No disponible en matching BGE-M3
    df['claude_patron'] = df['occupation_match_method'].fillna('')

    # Compatibilidad con nombres antiguos
    df['esco_occupation_id'] = df['esco_occupation_uri']
    df['esco_codigo_isco'] = df['claude_isco_code']
    df['esco_match_score'] = df['occupation_match_score']
    df['esco_match_method'] = df['occupation_match_method'].fillna('bge-m3')

    # Metadata
    df['hybrid_method'] = df['nlp_version'].fillna('unknown')
    df['hybrid_llm_called'] = False  # No aplica en este contexto
    df['is_complete'] = df['extracted_data'].notna()
    df['esco_skills_overlap'] = 0  # Placeholder
    df['fuente_consolidado'] = df['fuente'].fillna('bumeran')

    print(f"  OK: Columnas calculadas creadas")

    # === 5. REORDENAR COLUMNAS ===
    print()
    print("[5/6] Reordenando columnas para Shiny...")

    # Orden específico esperado por Shiny
    columnas_orden = [
        # Identificación básica
        'fecha_publicacion', 'periodo', 'fuente', 'url_oferta', 'source_id',
        'empresa', 'localizacion', 'localidad', 'provincia', 'titulo', 'descripcion',

        # ESCO Matching (lo más importante)
        'claude_esco_id', 'claude_esco_label', 'claude_isco_code',
        'isco_nivel1', 'isco_nivel1_nombre', 'isco_nivel2', 'isco_4d',
        'claude_confidence', 'claude_razonamiento', 'claude_patron',

        # Skills ESCO
        'esco_skills_esenciales', 'esco_skills_esenciales_count',
        'esco_skills_opcionales', 'esco_skills_opcionales_count',
        'esco_skills_total_count',

        # Skills Parseadas
        'soft_skills', 'soft_skills_count',
        'skills_tecnicas', 'skills_tecnicas_count',
        'skills_parseadas_total',

        # Requisitos
        'nivel_educativo', 'experiencia_min_anios', 'experiencia_max_anios',
        'idioma_principal', 'certificaciones_list',

        # Matching original (comparación)
        'esco_occupation_id', 'esco_occupation_label', 'esco_codigo_isco',
        'esco_match_score', 'esco_confianza',

        # Flags
        'tiene_url', 'tiene_skills_parseadas', 'tiene_skills_esco',

        # Metadata
        'hybrid_method', 'hybrid_llm_called', 'is_complete',
        'esco_skills_overlap', 'esco_match_method', 'fuente_consolidado'
    ]

    # Asegurar todas las columnas
    columnas_existentes = [col for col in columnas_orden if col in df.columns]
    df_final = df[columnas_existentes]

    print(f"  OK: {len(columnas_existentes)} columnas ordenadas")

    # === 6. GUARDAR CSV ===
    print()
    print("[6/6] Guardando CSV...")

    # IMPORTANTE: Forzar columnas ISCO a string para evitar problemas en R
    # Convertir a string y limpiar valores nan
    for col in ['isco_nivel1', 'isco_nivel2', 'isco_4d', 'claude_isco_code']:
        if col in df_final.columns:
            # Rellenar NaN con vac emptio, convertir a string
            df_final[col] = df_final[col].fillna('').astype(str)
            # Limpiar 'nan' string
            df_final[col] = df_final[col].replace('nan', '')

    print("  Convirtiendo ISCO a strings...")
    print(f"    Tipos de datos ISCO:")
    for col in ['isco_nivel1', 'isco_nivel2', 'isco_4d']:
        if col in df_final.columns:
            print(f"      {col}: {df_final[col].dtype}")

    output_dir = Path(r"D:\OEDE\Webscrapping\Visual--")
    output_path = output_dir / "ofertas_esco_shiny.csv"

    # Forzar quote en todas las columnas para preservar tipos
    df_final.to_csv(output_path, index=False, encoding='utf-8', quotechar='"', quoting=1)  # QUOTE_ALL=1

    print()
    print("=" * 100)
    print("CSV GENERADO EXITOSAMENTE")
    print("=" * 100)
    print()
    print(f"  Archivo:              {output_path}")
    print(f"  Tamaño:               {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Filas:                {len(df_final):,}")
    print(f"  Columnas:             {len(df_final.columns)}")
    print()
    print("  Estadísticas:")
    print(f"    Con URL:              {df_final['tiene_url'].sum():,} ({df_final['tiene_url'].sum()/len(df_final)*100:.1f}%)")
    print(f"    Con skills ESCO:      {df_final['tiene_skills_esco'].sum():,} ({df_final['tiene_skills_esco'].sum()/len(df_final)*100:.1f}%)")
    print(f"    Con skills parseadas: {df_final['tiene_skills_parseadas'].sum():,} ({df_final['tiene_skills_parseadas'].sum()/len(df_final)*100:.1f}%)")
    print()
    print(f"    Fuentes únicas:       {df_final['fuente'].nunique()}")
    print(f"    Empresas únicas:      {df_final['empresa'].nunique():,}")
    print(f"    Provincias únicas:    {df_final['localizacion'].nunique()}")
    print(f"    ISCO nivel 1:         {df_final['isco_nivel1'].nunique()}")
    print(f"    Ocupaciones ESCO:     {df_final['claude_esco_label'].nunique():,}")
    print()
    print("  Rango temporal:")
    try:
        # Convertir a tz-naive para evitar errores de comparación
        fecha_min = pd.to_datetime(df_final['fecha_publicacion']).dt.tz_localize(None).min()
        fecha_max = pd.to_datetime(df_final['fecha_publicacion']).dt.tz_localize(None).max()
        print(f"    Fecha más antigua:    {fecha_min}")
        print(f"    Fecha más reciente:   {fecha_max}")
    except Exception as e:
        print(f"    [!] No se pudieron calcular rangos temporales: {e}")
    print()
    print("=" * 100)
    print("[COMPLETADO] Dataset listo para Shiny Dashboard")
    print("=" * 100)
    print()


if __name__ == '__main__':
    main()
