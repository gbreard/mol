#!/usr/bin/env python3
"""
Sincroniza ofertas validadas desde SQLite local hacia Supabase.

Uso:
    python scripts/exports/sync_to_supabase.py              # Sync todas las validadas
    python scripts/exports/sync_to_supabase.py --since 2026-01-15  # Solo desde fecha
    python scripts/exports/sync_to_supabase.py --ids 123,456       # Ofertas específicas
    python scripts/exports/sync_to_supabase.py --dry-run           # Preview sin escribir
    python scripts/exports/sync_to_supabase.py --stats             # Ver estadísticas
    python scripts/exports/sync_to_supabase.py --full              # Sync completo (todas)
    python scripts/exports/sync_to_supabase.py --catalogs-only     # Solo catálogos ESCO

Autor: MOL Team
Versión: 2.0.0 - Soporte skills normalizados + nuevos schemas

Tablas Supabase:
    - ofertas_dashboard: Ofertas desnormalizadas para queries rápidas
    - ofertas_skills: Skills normalizados (N:M)
    - skills: Catálogo ESCO de skills
    - ocupaciones_esco: Catálogo ESCO de ocupaciones
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

# Nombres de tablas en Supabase (según fase3_dashboard/sql/)
TABLE_OFERTAS = 'ofertas_dashboard'
TABLE_SKILLS = 'ofertas_skills'
TABLE_SKILLS_CATALOG = 'skills'
TABLE_OCUPACIONES = 'ocupaciones_esco'


def load_config() -> Dict[str, str]:
    """Carga configuración de Supabase."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Config no encontrado: {CONFIG_PATH}\n"
            "Crear con: {\"url\": \"https://xxx.supabase.co\", \"anon_key\": \"...\"}"
        )

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if not config.get('url') or not config.get('service_role_key'):
        raise ValueError("Config incompleto: se requiere 'url' y 'service_role_key'")

    return config


def get_supabase_client():
    """Obtiene cliente de Supabase."""
    try:
        from supabase import create_client, Client
    except ImportError:
        logger.error("Instalar supabase: pip install supabase")
        sys.exit(1)

    config = load_config()
    client: Client = create_client(config['url'], config['service_role_key'])
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
    # v1.1: Aceptar validado_claude, validado_humano Y validado para poblar dashboard
    where_clauses = ["m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado')"]
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

def transform_oferta_for_supabase(oferta: Dict) -> Dict:
    """
    Transforma una oferta de SQLite al formato de ofertas_dashboard de Supabase.
    """
    return {
        'id_oferta': str(oferta.get('id_oferta')),
        'titulo': oferta.get('titulo'),
        'titulo_limpio': oferta.get('titulo_limpio'),
        'empresa': oferta.get('empresa'),
        'fecha_publicacion': oferta.get('fecha_publicacion_iso'),
        'url': oferta.get('url_oferta'),
        'portal': oferta.get('portal'),
        # Ubicación (prioriza NLP sobre scraping)
        'provincia': oferta.get('provincia') or oferta.get('provincia_normalizada'),
        'localidad': oferta.get('localidad') or oferta.get('localidad_normalizada'),
        # ESCO - columnas completas para perfil argentino
        'esco_occupation_uri': oferta.get('esco_occupation_uri'),
        'esco_occupation_label': oferta.get('esco_occupation_label'),
        'isco_code': oferta.get('isco_code'),
        'isco_label': oferta.get('esco_occupation_label') or oferta.get('isco_label'),
        'occupation_match_score': oferta.get('occupation_match_score'),
        'occupation_match_method': oferta.get('occupation_match_method'),
        # NLP
        'modalidad': oferta.get('modalidad'),
        'nivel_seniority': oferta.get('nivel_seniority'),
        'area_funcional': oferta.get('area_funcional'),
        'sector_empresa': oferta.get('sector_empresa'),
        # Salarios
        'salario_min': oferta.get('salario_min'),
        'salario_max': oferta.get('salario_max'),
        'moneda': oferta.get('moneda'),
        # Skills (JSONB para backward compatibility)
        'skills_tecnicas': oferta.get('skills_tecnicas_list'),
        'soft_skills': oferta.get('soft_skills_list'),
        # Estado
        'estado': oferta.get('estado_oferta', 'activa'),
        'fecha_sync': datetime.now().isoformat(),
    }


def upsert_ofertas(client, ofertas: List[Dict], dry_run: bool = False) -> int:
    """
    Upsert ofertas a Supabase (tabla ofertas_dashboard).

    Returns:
        Número de ofertas procesadas
    """
    if not ofertas:
        return 0

    # Transformar al formato de Supabase
    ofertas_transformed = [transform_oferta_for_supabase(o) for o in ofertas]

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(ofertas_transformed)} ofertas")
        return len(ofertas_transformed)

    # Procesar en batches
    total = 0
    for i in range(0, len(ofertas_transformed), BATCH_SIZE):
        batch = ofertas_transformed[i:i + BATCH_SIZE]

        try:
            result = client.table(TABLE_OFERTAS).upsert(
                batch,
                on_conflict='id_oferta'
            ).execute()
            total += len(batch)
            logger.info(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} ofertas")
        except Exception as e:
            logger.error(f"Error en batch {i//BATCH_SIZE + 1}: {e}")
            raise

    return total


def transform_skill_for_supabase(skill: Dict) -> Dict:
    """
    Transforma un skill de SQLite al formato de ofertas_skills de Supabase.
    """
    return {
        'id_oferta': str(skill.get('id_oferta')),
        'skill_uri': skill.get('esco_skill_uri') or skill.get('skill_uri'),
        'preferred_label': skill.get('esco_skill_label') or skill.get('preferred_label'),
        'l1': skill.get('l1') or skill.get('L1'),
        'l1_nombre': skill.get('l1_nombre') or skill.get('L1_nombre'),
        'l2': skill.get('l2') or skill.get('L2'),
        'l2_nombre': skill.get('l2_nombre') or skill.get('L2_nombre'),
        'es_digital': skill.get('es_digital', False),
        'origen': skill.get('skill_tipo_fuente') or skill.get('origen', 'merged'),
        'score': skill.get('match_score') or skill.get('score'),
        'es_esencial': skill.get('es_esencial', False),
    }


def upsert_skills(client, skills: List[Dict], dry_run: bool = False) -> int:
    """
    Upsert skills normalizados a Supabase (tabla ofertas_skills).

    Usa delete + insert por oferta para evitar duplicados.
    """
    if not skills:
        return 0

    # Transformar al formato de Supabase
    skills_transformed = [transform_skill_for_supabase(s) for s in skills]

    # Filtrar skills sin URI (inválidos)
    skills_transformed = [s for s in skills_transformed if s.get('skill_uri')]

    # Deduplicar por (id_oferta, skill_uri) - quedarse con el primero
    seen = set()
    skills_unique = []
    for s in skills_transformed:
        key = (s['id_oferta'], s['skill_uri'])
        if key not in seen:
            seen.add(key)
            skills_unique.append(s)

    if len(skills_unique) < len(skills_transformed):
        logger.warning(f"Se eliminaron {len(skills_transformed) - len(skills_unique)} skills duplicados")

    skills_transformed = skills_unique

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(skills_transformed)} skills")
        return len(skills_transformed)

    # Obtener IDs únicos de ofertas
    offer_ids = list(set(s['id_oferta'] for s in skills_transformed))

    # Eliminar skills existentes para estas ofertas (para evitar duplicados)
    try:
        for oid in offer_ids:
            client.table(TABLE_SKILLS).delete().eq('id_oferta', oid).execute()
    except Exception as e:
        logger.warning(f"Error eliminando skills existentes: {e}")

    # Insertar nuevas
    total = 0
    for i in range(0, len(skills_transformed), BATCH_SIZE):
        batch = skills_transformed[i:i + BATCH_SIZE]

        try:
            result = client.table(TABLE_SKILLS).upsert(
                batch,
                on_conflict='id_oferta,skill_uri'
            ).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando skills batch {i//BATCH_SIZE + 1}: {e}")
            raise

    return total


def transform_ocupacion_for_supabase(ocupacion: Dict) -> Dict:
    """
    Transforma una ocupación al formato de ocupaciones_esco de Supabase.
    """
    return {
        'esco_uri': ocupacion.get('uri'),
        'isco_code': ocupacion.get('isco_code'),
        'isco_label': ocupacion.get('isco_label'),
        'preferred_label_es': ocupacion.get('label'),
        'preferred_label_en': ocupacion.get('label_en'),
        'description_es': ocupacion.get('description'),
    }


def upsert_esco_ocupaciones(client, ocupaciones: List[Dict], dry_run: bool = False) -> int:
    """Upsert ocupaciones ESCO (tabla ocupaciones_esco)."""
    if not ocupaciones:
        return 0

    # Eliminar duplicados por URI
    seen = set()
    unique_ocupaciones = []
    for o in ocupaciones:
        uri = o.get('uri')
        if uri and uri not in seen:
            seen.add(uri)
            unique_ocupaciones.append(transform_ocupacion_for_supabase(o))

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(unique_ocupaciones)} ocupaciones ESCO")
        return len(unique_ocupaciones)

    try:
        result = client.table(TABLE_OCUPACIONES).upsert(
            unique_ocupaciones,
            on_conflict='esco_uri'
        ).execute()
        return len(unique_ocupaciones)
    except Exception as e:
        logger.error(f"Error upserting ocupaciones: {e}")
        raise


def transform_skill_catalog_for_supabase(skill: Dict) -> Dict:
    """
    Transforma un skill al formato del catálogo skills de Supabase.
    """
    return {
        'skill_uri': skill.get('uri'),
        'preferred_label_es': skill.get('label'),
        'preferred_label_en': skill.get('label_en'),
        'l1': skill.get('l1'),
        'l1_nombre': skill.get('l1_nombre'),
        'l2': skill.get('l2'),
        'l2_nombre': skill.get('l2_nombre'),
        'es_digital': skill.get('es_digital', False),
        'skill_type': skill.get('skill_type'),
    }


def upsert_esco_skills(client, skills: List[Dict], dry_run: bool = False) -> int:
    """Upsert skills ESCO al catálogo (tabla skills)."""
    if not skills:
        return 0

    # Transformar y eliminar duplicados
    seen = set()
    unique_skills = []
    for s in skills:
        uri = s.get('uri')
        if uri and uri not in seen:
            seen.add(uri)
            unique_skills.append(transform_skill_catalog_for_supabase(s))

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(unique_skills)} skills ESCO")
        return len(unique_skills)

    try:
        result = client.table(TABLE_SKILLS_CATALOG).upsert(
            unique_skills,
            on_conflict='skill_uri'
        ).execute()
        return len(unique_skills)
    except Exception as e:
        logger.error(f"Error upserting skills ESCO: {e}")
        raise


# ============================================================
# SINCRONIZACIÓN DE ERRORES (validation_errors → issues)
# ============================================================

TABLE_ISSUES = 'issues'

# Mapeo de error_id a tipo de issue en Supabase
ERROR_TYPE_MAP = {
    'V01_titulo_muy_corto': 'error_nlp',
    'V02_titulo_no_limpio': 'error_nlp',
    'V03_skills_insuficientes': 'error_skill',
    'V04_skills_no_coherentes': 'error_skill',
    'V05_area_no_matchea': 'error_nlp',
    'V06_sector_inconsistente': 'error_nlp',
    'V07_ubicacion_generica': 'error_nlp',
    'V08_modalidad_inferida': 'error_nlp',
    'V09_seniority_nulo': 'error_nlp',
    'V10_match_score_muy_bajo': 'error_isco',
    'V11_isco_generico': 'error_isco',
    'V12_dual_difieren': 'error_isco',
    'V20_sector_salud_no_sanitario': 'sugerencia',
}

# Mapeo de severidad a prioridad
SEVERITY_MAP = {
    'alto': 'alta',
    'medio': 'media',
    'bajo': 'baja',
    'info': 'baja',
}


def extraer_errores_pendientes(conn: sqlite3.Connection, offer_ids: Optional[List[str]] = None) -> List[Dict]:
    """
    Extrae errores de validación NO resueltos de SQLite.
    Solo errores de ofertas que ya están en Supabase.
    """
    query = """
        SELECT
            ve.id,
            ve.id_oferta,
            ve.error_id,
            ve.severidad,
            ve.mensaje,
            ve.campo_afectado,
            ve.valor_actual,
            ve.detectado_timestamp,
            ve.resuelto
        FROM validation_errors ve
        WHERE ve.resuelto = 0
    """
    params = []

    if offer_ids:
        placeholders = ','.join(['?' for _ in offer_ids])
        query += f" AND ve.id_oferta IN ({placeholders})"
        params.extend(offer_ids)

    cursor = conn.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def transform_error_to_issue(error: Dict) -> Dict:
    """
    Transforma un error de validation_errors al formato de issues de Supabase.
    """
    error_id = error.get('error_id', '')
    tipo = ERROR_TYPE_MAP.get(error_id, 'otro')
    prioridad = SEVERITY_MAP.get(error.get('severidad', 'medio'), 'media')

    return {
        'id_oferta': error.get('id_oferta'),
        'titulo': f"[AUTO] {error.get('mensaje', error_id)}",
        'descripcion': f"Error detectado automáticamente por el validador.\n\nCódigo: {error_id}\nSeveridad original: {error.get('severidad')}",
        'tipo': tipo,
        'prioridad': prioridad,
        'campo_afectado': error.get('campo_afectado'),
        'valor_actual': error.get('valor_actual'),
        'estado': 'pendiente',
        'autor_email': 'auto-validator@mol.gob.ar',
    }


def sync_validation_errors_to_issues(client, conn: sqlite3.Connection, offer_ids: Optional[List[str]] = None, dry_run: bool = False) -> int:
    """
    Sincroniza errores de validación pendientes a la tabla issues en Supabase.

    - Solo sincroniza errores NO resueltos
    - No duplica issues (verifica si ya existe por id_oferta + titulo)
    - Marca como resueltos en Supabase los que se resolvieron localmente
    """
    # 1. Obtener errores pendientes locales
    errores_locales = extraer_errores_pendientes(conn, offer_ids)
    logger.info(f"Errores pendientes locales: {len(errores_locales)}")

    if not errores_locales and not dry_run:
        # Si no hay errores pendientes, marcar todos como resueltos en Supabase
        try:
            client.table(TABLE_ISSUES).update({
                'estado': 'resuelto',
                'resuelto_por': 'auto-sync',
                'solucion_aplicada': 'Resuelto automáticamente (sin errores pendientes)'
            }).eq('autor_email', 'auto-validator@mol.gob.ar').in_('estado', ['pendiente', 'en_progreso']).execute()
            logger.info("Marcados como resueltos todos los issues automáticos previos")
        except Exception as e:
            logger.warning(f"No se pudieron actualizar issues: {e}")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sincronizaría {len(errores_locales)} errores como issues")
        return len(errores_locales)

    # 2. Obtener issues automáticos existentes en Supabase
    try:
        existing = client.table(TABLE_ISSUES).select('id, id_oferta, titulo, estado').eq('autor_email', 'auto-validator@mol.gob.ar').execute()
        existing_keys = {(i['id_oferta'], i['titulo']): i for i in (existing.data or [])}
    except Exception as e:
        logger.warning(f"No se pudieron obtener issues existentes: {e}")
        existing_keys = {}

    # 3. Preparar nuevos issues
    nuevos = []
    for error in errores_locales:
        issue = transform_error_to_issue(error)
        key = (issue['id_oferta'], issue['titulo'])
        if key not in existing_keys:
            nuevos.append(issue)

    # 4. Insertar nuevos
    if nuevos:
        try:
            # Insertar en batches
            for i in range(0, len(nuevos), 50):
                batch = nuevos[i:i + 50]
                client.table(TABLE_ISSUES).insert(batch).execute()
            logger.info(f"Insertados {len(nuevos)} nuevos issues")
        except Exception as e:
            logger.error(f"Error insertando issues: {e}")

    # 5. Marcar como resueltos los que ya no están pendientes localmente
    errores_ids = {e['id_oferta'] for e in errores_locales}
    for key, existing_issue in existing_keys.items():
        id_oferta, titulo = key
        if id_oferta not in errores_ids and existing_issue['estado'] in ('pendiente', 'en_progreso'):
            try:
                client.table(TABLE_ISSUES).update({
                    'estado': 'resuelto',
                    'resuelto_por': 'auto-sync',
                    'solucion_aplicada': 'Resuelto automáticamente'
                }).eq('id', existing_issue['id']).execute()
            except Exception as e:
                logger.warning(f"No se pudo marcar issue {existing_issue['id']} como resuelto: {e}")

    return len(nuevos)


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
        result = client.table(TABLE_OFERTAS).select('id_oferta', count='exact').execute()
        ofertas_count = result.count if result.count else 0
        print(f"Ofertas (ofertas_dashboard): {ofertas_count}")

        # Contar skills normalizados
        result = client.table(TABLE_SKILLS).select('id', count='exact').execute()
        skills_count = result.count if result.count else 0
        print(f"Skills (ofertas_skills): {skills_count}")

        # Contar ocupaciones ESCO
        result = client.table(TABLE_OCUPACIONES).select('esco_uri', count='exact').execute()
        ocu_count = result.count if result.count else 0
        print(f"Ocupaciones ESCO: {ocu_count}")

        # Contar skills ESCO (catálogo)
        result = client.table(TABLE_SKILLS_CATALOG).select('skill_uri', count='exact').execute()
        esco_skills_count = result.count if result.count else 0
        print(f"Skills ESCO (catálogo): {esco_skills_count}")

        # Última actualización
        result = client.table(TABLE_OFERTAS).select('fecha_sync').order('fecha_sync', desc=True).limit(1).execute()
        if result.data:
            print(f"Última sincronización: {result.data[0]['fecha_sync']}")

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
        WHERE estado_validacion IN ('validado_claude', 'validado_humano', 'validado')
    """)
    row = cursor.fetchone()
    print(f"Ofertas validadas: {row['total']}")
    print(f"Primera validación: {row['primera']}")
    print(f"Última validación: {row['ultima']}")

    # Skills
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle d
        JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado')
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
    parser.add_argument('--full', action='store_true', help='Sync completo (todas las validadas)')
    parser.add_argument('--catalogs-only', action='store_true', help='Solo sincronizar catálogos ESCO')
    parser.add_argument('--regenerate-profiles', action='store_true', help='Regenerar perfiles MOL vs ESCO después del sync')
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

        logger.info("Sincronizando errores de validación...")
        n_issues = sync_validation_errors_to_issues(client, conn, ids_para_sync, dry_run=args.dry_run)

        # Actualizar sistema_estado con el conteo real de errores pendientes
        if not args.dry_run:
            try:
                errores_count = conn.execute('SELECT COUNT(*) FROM validation_errors WHERE resuelto = 0').fetchone()[0]
                # Obtener ID del registro más reciente
                estado_result = client.table('sistema_estado').select('id').order('timestamp', desc=True).limit(1).execute()
                if estado_result.data:
                    client.table('sistema_estado').update({
                        'fase2_errores_sin_resolver': errores_count
                    }).eq('id', estado_result.data[0]['id']).execute()
                    logger.info(f"Actualizado sistema_estado.fase2_errores_sin_resolver = {errores_count}")
            except Exception as e:
                logger.warning(f"No se pudo actualizar sistema_estado: {e}")

        # Resumen
        print("\n" + "="*60)
        print("RESUMEN" + (" [DRY-RUN]" if args.dry_run else ""))
        print("="*60)
        print(f"Ofertas sincronizadas:    {n_ofertas}")
        print(f"Skills detalle:           {n_skills}")
        print(f"Ocupaciones ESCO:         {n_ocup}")
        print(f"Skills ESCO:              {n_esco}")
        print(f"Issues sincronizados:     {n_issues}")
        print("="*60)

        if not args.dry_run:
            logger.info("Sincronización completada exitosamente!")

            # Regenerar perfiles MOL vs ESCO automáticamente después de cada sync
            # (antes era opcional con --regenerate-profiles, ahora siempre se ejecuta)
            logger.info("\n" + "="*60)
            logger.info("REGENERANDO PERFILES MOL vs ESCO")
            logger.info("="*60)
            try:
                import subprocess
                script_path = PROJECT_ROOT / "fase3_dashboard" / "mol-dashboard" / "scripts" / "generate_mol_skills_profile.py"
                if script_path.exists():
                    result = subprocess.run(
                        ['python3', str(script_path)],
                        cwd=str(script_path.parent),
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info("Perfiles MOL regenerados exitosamente")
                        # Mostrar últimas líneas del output
                        for line in result.stdout.strip().split('\n')[-5:]:
                            logger.info(f"  {line}")
                    else:
                        logger.error(f"Error regenerando perfiles: {result.stderr}")
                else:
                    logger.warning(f"Script no encontrado: {script_path}")
            except Exception as e:
                logger.error(f"Error ejecutando generador de perfiles: {e}")

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
