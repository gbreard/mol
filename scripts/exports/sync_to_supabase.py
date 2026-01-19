#!/usr/bin/env python3
"""
Sincroniza ofertas validadas desde SQLite local hacia Supabase.

Uso:
    python scripts/exports/sync_to_supabase.py              # Sync todas las validadas
    python scripts/exports/sync_to_supabase.py --since 2026-01-15  # Solo desde fecha
    python scripts/exports/sync_to_supabase.py --ids 123,456       # Ofertas específicas
    python scripts/exports/sync_to_supabase.py --dry-run           # Preview sin escribir
    python scripts/exports/sync_to_supabase.py --stats             # Ver estadísticas

Autor: MOL Team
Versión: 1.0.0
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
BATCH_SIZE = 100  # Ofertas por batch para evitar timeouts


def load_config() -> Dict[str, str]:
    """Carga configuración de Supabase."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Config no encontrado: {CONFIG_PATH}\n"
            "Crear con: {\"url\": \"https://xxx.supabase.co\", \"anon_key\": \"...\"}"
        )

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if not config.get('url') or not config.get('anon_key'):
        raise ValueError("Config incompleto: se requiere 'url' y 'anon_key'")

    return config


def get_supabase_client():
    """Obtiene cliente de Supabase."""
    try:
        from supabase import create_client, Client
    except ImportError:
        logger.error("Instalar supabase: pip install supabase")
        sys.exit(1)

    config = load_config()
    client: Client = create_client(config['url'], config['anon_key'])
    return client


def get_sqlite_connection() -> sqlite3.Connection:
    """Conecta a SQLite local."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"BD no encontrada: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# EXTRACCIÓN DE DATOS DESDE SQLITE
# ============================================================

# Campos a extraer de cada tabla
CAMPOS_OFERTAS = [
    'id_oferta', 'titulo', 'empresa', 'descripcion', 'localizacion',
    'modalidad_trabajo', 'url_oferta', 'portal', 'fecha_publicacion_iso',
    'scrapeado_en', 'provincia_normalizada', 'localidad_normalizada',
    'estado_oferta', 'fecha_ultimo_visto', 'dias_publicada'
]

CAMPOS_NLP = [
    'id_oferta', 'titulo_limpio', 'tareas_explicitas', 'mision_rol',
    'area_funcional', 'nivel_seniority', 'sector_empresa', 'tipo_oferta',
    'tipo_contrato', 'provincia', 'localidad', 'modalidad', 'jornada_laboral',
    'nivel_educativo', 'titulo_requerido', 'experiencia_min_anios',
    'tiene_gente_cargo', 'requiere_movilidad_propia',
    'skills_tecnicas_list', 'soft_skills_list', 'tecnologias_list',
    'herramientas_list', 'nlp_extraction_timestamp', 'nlp_version'
]

CAMPOS_MATCHING = [
    'id_oferta', 'esco_occupation_uri', 'esco_occupation_label',
    'isco_code', 'isco_label', 'occupation_match_score', 'occupation_match_method',
    'skills_oferta_json', 'skills_matched_essential',
    'skills_demandados_total', 'skills_matcheados_esco',
    'matching_timestamp', 'matching_version', 'run_id',
    'estado_validacion', 'validado_timestamp', 'validado_por'
]

CAMPOS_SKILLS = [
    'id_oferta', 'skill_mencionado', 'skill_tipo_fuente',
    'esco_skill_uri', 'esco_skill_label', 'match_score', 'skill_type'
]


def extraer_ofertas_validadas(
    conn: sqlite3.Connection,
    since: Optional[str] = None,
    ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extrae ofertas validadas con datos de scraping + NLP + matching.

    Args:
        conn: Conexión SQLite
        since: Fecha mínima de validación (ISO format)
        ids: Lista de IDs específicos

    Returns:
        Lista de diccionarios con datos desnormalizados
    """
    # Construir WHERE clause
    where_clauses = ["m.estado_validacion = 'validado'"]
    params = []

    if since:
        where_clauses.append("m.validado_timestamp >= ?")
        params.append(since)

    if ids:
        placeholders = ','.join(['?' for _ in ids])
        where_clauses.append(f"m.id_oferta IN ({placeholders})")
        params.extend(ids)

    where_sql = ' AND '.join(where_clauses)

    # Query principal con JOINs
    query = f"""
    SELECT
        -- Scraping
        o.id_oferta, o.titulo, o.empresa, o.descripcion, o.localizacion,
        o.modalidad_trabajo, o.url_oferta, o.portal, o.fecha_publicacion_iso,
        o.scrapeado_en, o.provincia_normalizada, o.localidad_normalizada,
        o.estado_oferta, o.fecha_ultimo_visto, o.dias_publicada,
        -- NLP
        n.titulo_limpio, n.tareas_explicitas, n.mision_rol,
        n.area_funcional, n.nivel_seniority, n.sector_empresa, n.tipo_oferta,
        n.tipo_contrato, n.provincia, n.localidad, n.modalidad, n.jornada_laboral,
        n.nivel_educativo, n.titulo_requerido, n.experiencia_min_anios,
        n.tiene_gente_cargo, n.requiere_movilidad_propia,
        n.skills_tecnicas_list, n.soft_skills_list, n.tecnologias_list,
        n.herramientas_list, n.nlp_extraction_timestamp, n.nlp_version,
        -- Matching
        m.esco_occupation_uri, m.esco_occupation_label,
        m.isco_code, m.isco_label, m.occupation_match_score, m.occupation_match_method,
        m.skills_oferta_json, m.skills_matched_essential,
        m.skills_demandados_total, m.skills_matcheados_esco,
        m.matching_timestamp, m.matching_version, m.run_id,
        m.estado_validacion, m.validado_timestamp, m.validado_por
    FROM ofertas o
    INNER JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
    INNER JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
    WHERE {where_sql}
    ORDER BY m.validado_timestamp DESC
    """

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    # Convertir a lista de dicts
    ofertas = []
    for row in rows:
        oferta = dict(row)

        # Parsear campos JSON
        for campo in ['skills_tecnicas_list', 'soft_skills_list', 'tecnologias_list',
                      'herramientas_list', 'skills_oferta_json', 'skills_matched_essential']:
            if oferta.get(campo):
                try:
                    oferta[campo] = json.loads(oferta[campo])
                except (json.JSONDecodeError, TypeError):
                    pass

        # Convertir booleanos
        for campo in ['tiene_gente_cargo', 'requiere_movilidad_propia']:
            if oferta.get(campo) is not None:
                oferta[campo] = bool(oferta[campo])

        ofertas.append(oferta)

    return ofertas


def extraer_skills_detalle(
    conn: sqlite3.Connection,
    offer_ids: List[str]
) -> List[Dict[str, Any]]:
    """Extrae skills detalle para las ofertas especificadas."""
    if not offer_ids:
        return []

    placeholders = ','.join(['?' for _ in offer_ids])
    query = f"""
    SELECT
        d.id_oferta,
        d.skill_mencionado,
        d.skill_tipo_fuente,
        d.esco_skill_uri,
        d.esco_skill_label,
        d.match_score,
        d.esco_skill_type as skill_type,
        d.source_classification
    FROM ofertas_esco_skills_detalle d
    WHERE d.id_oferta IN ({placeholders})
    """

    cursor = conn.execute(query, offer_ids)
    rows = cursor.fetchall()

    skills = []
    for row in rows:
        skill = dict(row)

        # Parsear source_classification para extraer l1, l2, es_digital
        # Nota: PostgreSQL convierte columnas a minúsculas
        if skill.get('source_classification'):
            try:
                sc = json.loads(skill['source_classification'])
                skill['l1'] = sc.get('L1')
                skill['l1_nombre'] = sc.get('L1_nombre')
                skill['l2'] = sc.get('L2')
                skill['l2_nombre'] = sc.get('L2_nombre')
                skill['es_digital'] = sc.get('es_digital', False)
            except (json.JSONDecodeError, TypeError):
                skill['l1'] = None
                skill['l1_nombre'] = None
                skill['l2'] = None
                skill['l2_nombre'] = None
                skill['es_digital'] = False

        # Remover campo intermedio
        skill.pop('source_classification', None)

        skills.append(skill)

    return skills


def extraer_esco_ocupaciones_usadas(
    conn: sqlite3.Connection,
    offer_ids: List[str]
) -> List[Dict[str, Any]]:
    """Extrae ocupaciones ESCO usadas en las ofertas."""
    if not offer_ids:
        return []

    placeholders = ','.join(['?' for _ in offer_ids])
    query = f"""
    SELECT DISTINCT
        m.esco_occupation_uri as uri,
        m.esco_occupation_label as label,
        m.isco_code,
        m.isco_label,
        '' as description
    FROM ofertas_esco_matching m
    WHERE m.id_oferta IN ({placeholders})
    AND m.esco_occupation_uri IS NOT NULL
    """

    cursor = conn.execute(query, offer_ids)
    return [dict(row) for row in cursor.fetchall()]


def extraer_esco_skills_usadas(
    conn: sqlite3.Connection,
    offer_ids: List[str]
) -> List[Dict[str, Any]]:
    """Extrae skills ESCO usadas en las ofertas."""
    if not offer_ids:
        return []

    placeholders = ','.join(['?' for _ in offer_ids])
    query = f"""
    SELECT DISTINCT
        d.esco_skill_uri as uri,
        d.esco_skill_label as label,
        d.esco_skill_type as skill_type,
        d.source_classification
    FROM ofertas_esco_skills_detalle d
    WHERE d.id_oferta IN ({placeholders})
    AND d.esco_skill_uri IS NOT NULL
    """

    cursor = conn.execute(query, offer_ids)
    rows = cursor.fetchall()

    skills = []
    seen_uris = set()

    for row in rows:
        skill = dict(row)

        # Evitar duplicados
        if skill['uri'] in seen_uris:
            continue
        seen_uris.add(skill['uri'])

        # Parsear clasificación (lowercase para PostgreSQL)
        if skill.get('source_classification'):
            try:
                sc = json.loads(skill['source_classification'])
                skill['l1'] = sc.get('L1')
                skill['l1_nombre'] = sc.get('L1_nombre')
                skill['l2'] = sc.get('L2')
                skill['l2_nombre'] = sc.get('L2_nombre')
                skill['es_digital'] = sc.get('es_digital', False)
            except (json.JSONDecodeError, TypeError):
                skill['l1'] = None
                skill['l1_nombre'] = None
                skill['l2'] = None
                skill['l2_nombre'] = None
                skill['es_digital'] = False

        skill.pop('source_classification', None)
        skills.append(skill)

    return skills


# ============================================================
# UPLOAD A SUPABASE
# ============================================================

def upsert_ofertas(client, ofertas: List[Dict], dry_run: bool = False) -> int:
    """
    Upsert ofertas a Supabase.

    Returns:
        Número de ofertas procesadas
    """
    if not ofertas:
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(ofertas)} ofertas")
        return len(ofertas)

    # Procesar en batches
    total = 0
    for i in range(0, len(ofertas), BATCH_SIZE):
        batch = ofertas[i:i + BATCH_SIZE]

        try:
            result = client.table('ofertas').upsert(batch).execute()
            total += len(batch)
            logger.info(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} ofertas")
        except Exception as e:
            logger.error(f"Error en batch {i//BATCH_SIZE + 1}: {e}")
            raise

    return total


def upsert_skills(client, skills: List[Dict], dry_run: bool = False) -> int:
    """Upsert skills a Supabase (con delete previo por oferta)."""
    if not skills:
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(skills)} skills")
        return len(skills)

    # Obtener IDs únicos de ofertas
    offer_ids = list(set(s['id_oferta'] for s in skills))

    # Eliminar skills existentes para estas ofertas (para evitar duplicados)
    try:
        for oid in offer_ids:
            client.table('ofertas_skills').delete().eq('id_oferta', oid).execute()
    except Exception as e:
        logger.warning(f"Error eliminando skills existentes: {e}")

    # Insertar nuevas
    total = 0
    for i in range(0, len(skills), BATCH_SIZE):
        batch = skills[i:i + BATCH_SIZE]

        try:
            result = client.table('ofertas_skills').insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando skills batch {i//BATCH_SIZE + 1}: {e}")
            raise

    return total


def upsert_esco_ocupaciones(client, ocupaciones: List[Dict], dry_run: bool = False) -> int:
    """Upsert ocupaciones ESCO."""
    if not ocupaciones:
        return 0

    # Eliminar duplicados por URI
    seen = set()
    unique_ocupaciones = []
    for o in ocupaciones:
        if o['uri'] not in seen:
            seen.add(o['uri'])
            unique_ocupaciones.append(o)

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(unique_ocupaciones)} ocupaciones ESCO")
        return len(unique_ocupaciones)

    try:
        result = client.table('esco_occupations').upsert(unique_ocupaciones).execute()
        return len(unique_ocupaciones)
    except Exception as e:
        logger.error(f"Error upserting ocupaciones: {e}")
        raise


def upsert_esco_skills(client, skills: List[Dict], dry_run: bool = False) -> int:
    """Upsert skills ESCO."""
    if not skills:
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(skills)} skills ESCO")
        return len(skills)

    try:
        result = client.table('esco_skills').upsert(skills).execute()
        return len(skills)
    except Exception as e:
        logger.error(f"Error upserting skills ESCO: {e}")
        raise


# ============================================================
# ESTADÍSTICAS
# ============================================================

def mostrar_stats_supabase(client):
    """Muestra estadísticas de lo que hay en Supabase."""
    print("\n" + "="*60)
    print("ESTADÍSTICAS SUPABASE")
    print("="*60)

    try:
        # Contar ofertas
        result = client.table('ofertas').select('id_oferta', count='exact').execute()
        ofertas_count = result.count if result.count else 0
        print(f"Ofertas: {ofertas_count}")

        # Contar skills
        result = client.table('ofertas_skills').select('id', count='exact').execute()
        skills_count = result.count if result.count else 0
        print(f"Skills detalle: {skills_count}")

        # Contar ocupaciones ESCO
        result = client.table('esco_occupations').select('uri', count='exact').execute()
        ocu_count = result.count if result.count else 0
        print(f"Ocupaciones ESCO: {ocu_count}")

        # Contar skills ESCO
        result = client.table('esco_skills').select('uri', count='exact').execute()
        esco_skills_count = result.count if result.count else 0
        print(f"Skills ESCO: {esco_skills_count}")

        # Última actualización
        result = client.table('ofertas').select('updated_at').order('updated_at', desc=True).limit(1).execute()
        if result.data:
            print(f"Última actualización: {result.data[0]['updated_at']}")

    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")

    print("="*60 + "\n")


def mostrar_stats_local(conn: sqlite3.Connection):
    """Muestra estadísticas de SQLite local."""
    print("\n" + "="*60)
    print("ESTADÍSTICAS SQLITE LOCAL")
    print("="*60)

    cursor = conn.execute("""
        SELECT COUNT(*) as total,
               MIN(validado_timestamp) as primera,
               MAX(validado_timestamp) as ultima
        FROM ofertas_esco_matching
        WHERE estado_validacion = 'validado'
    """)
    row = cursor.fetchone()
    print(f"Ofertas validadas: {row['total']}")
    print(f"Primera validación: {row['primera']}")
    print(f"Última validación: {row['ultima']}")

    # Skills
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle d
        JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
        WHERE m.estado_validacion = 'validado'
    """)
    print(f"Skills detalle: {cursor.fetchone()[0]}")

    print("="*60 + "\n")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Sincroniza ofertas validadas a Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python sync_to_supabase.py                    # Sync todas las validadas
  python sync_to_supabase.py --since 2026-01-15 # Solo desde fecha
  python sync_to_supabase.py --ids 123,456      # Ofertas específicas
  python sync_to_supabase.py --dry-run          # Preview sin escribir
  python sync_to_supabase.py --stats            # Ver estadísticas
        """
    )

    parser.add_argument('--since', type=str, help='Fecha mínima de validación (YYYY-MM-DD)')
    parser.add_argument('--ids', type=str, help='IDs de ofertas separados por coma')
    parser.add_argument('--dry-run', action='store_true', help='Preview sin escribir')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parsear IDs si se proporcionaron
    offer_ids = None
    if args.ids:
        offer_ids = [id.strip() for id in args.ids.split(',')]

    try:
        # Conectar
        logger.info("Conectando a SQLite local...")
        conn = get_sqlite_connection()

        logger.info("Conectando a Supabase...")
        client = get_supabase_client()

        # Solo stats?
        if args.stats:
            mostrar_stats_local(conn)
            mostrar_stats_supabase(client)
            return

        # Extraer datos
        logger.info("Extrayendo ofertas validadas...")
        ofertas = extraer_ofertas_validadas(conn, since=args.since, ids=offer_ids)
        logger.info(f"  Encontradas: {len(ofertas)} ofertas")

        if not ofertas:
            logger.warning("No hay ofertas para sincronizar")
            return

        # IDs para queries relacionadas
        ids_para_sync = [o['id_oferta'] for o in ofertas]

        logger.info("Extrayendo skills detalle...")
        skills = extraer_skills_detalle(conn, ids_para_sync)
        logger.info(f"  Encontradas: {len(skills)} skills")

        logger.info("Extrayendo ocupaciones ESCO usadas...")
        ocupaciones = extraer_esco_ocupaciones_usadas(conn, ids_para_sync)
        logger.info(f"  Encontradas: {len(ocupaciones)} ocupaciones")

        logger.info("Extrayendo skills ESCO usadas...")
        esco_skills = extraer_esco_skills_usadas(conn, ids_para_sync)
        logger.info(f"  Encontradas: {len(esco_skills)} skills ESCO")

        # Upload
        print("\n" + "="*60)
        print("SINCRONIZANDO A SUPABASE" + (" [DRY-RUN]" if args.dry_run else ""))
        print("="*60)

        logger.info("Subiendo ofertas...")
        n_ofertas = upsert_ofertas(client, ofertas, dry_run=args.dry_run)

        logger.info("Subiendo skills detalle...")
        n_skills = upsert_skills(client, skills, dry_run=args.dry_run)

        logger.info("Subiendo ocupaciones ESCO...")
        n_ocup = upsert_esco_ocupaciones(client, ocupaciones, dry_run=args.dry_run)

        logger.info("Subiendo skills ESCO...")
        n_esco = upsert_esco_skills(client, esco_skills, dry_run=args.dry_run)

        # Resumen
        print("\n" + "="*60)
        print("RESUMEN" + (" [DRY-RUN]" if args.dry_run else ""))
        print("="*60)
        print(f"Ofertas sincronizadas:    {n_ofertas}")
        print(f"Skills detalle:           {n_skills}")
        print(f"Ocupaciones ESCO:         {n_ocup}")
        print(f"Skills ESCO:              {n_esco}")
        print("="*60)

        if not args.dry_run:
            logger.info("Sincronización completada exitosamente!")

    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
