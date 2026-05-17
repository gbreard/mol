#!/usr/bin/env python3
"""
Sincroniza ofertas validadas desde SQLite local hacia Supabase.

Uso:
    python scripts/exports/sync_to_supabase.py              # Incremental automático
    python scripts/exports/sync_to_supabase.py --full       # Sync completo (todas)
    python scripts/exports/sync_to_supabase.py --since 2026-01-15  # Solo desde fecha
    python scripts/exports/sync_to_supabase.py --ids 123,456       # Ofertas específicas
    python scripts/exports/sync_to_supabase.py --dry-run           # Preview sin escribir
    python scripts/exports/sync_to_supabase.py --stats             # Ver estadísticas
    python scripts/exports/sync_to_supabase.py --catalogs-only     # Solo catálogos ESCO

Sin argumentos: lee last_sync_timestamp de config/supabase_sync_log.json y solo
sincroniza ofertas con matching_timestamp o validado_timestamp posterior.
Usar --full para forzar sync completo de todas las validadas.

Autor: MOL Team
Versión: 2.2.0 - Sync incremental automático (lee last_sync_timestamp)

Tablas Supabase:
    - ofertas_dashboard: Ofertas desnormalizadas para queries rápidas
    - ofertas_skills: Skills normalizados (N:M)
    - skills: Catálogo ESCO de skills
    - ocupaciones_esco: Catálogo ESCO de ocupaciones
    - sistema_estado: Métricas de las 3 fases del pipeline (v2.1)
"""

import argparse
import difflib
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import unicodedata
from unicodedata import normalize as unicode_normalize

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
INDEC_PATH = PROJECT_ROOT / "config" / "indec_localidades.json"
INDEC_CORRECCIONES_PATH = PROJECT_ROOT / "config" / "indec_correcciones.json"
CLAE_NOMENCLADOR_PATH = PROJECT_ROOT / "config" / "clae_nomenclador.json"

# Nombres de tablas en Supabase (según fase3_dashboard/sql/)
TABLE_OFERTAS = 'ofertas_dashboard'
TABLE_SKILLS = 'ofertas_skills'
TABLE_SKILLS_CATALOG = 'skills'
TABLE_OCUPACIONES = 'ocupaciones_esco'
TABLE_TENSION = 'tension_ocupaciones'
TABLE_CONCENTRACION = 'concentracion_ocupacional'
TABLE_BRECHA = 'brecha_calificacion'
TABLE_DIGITALIZACION = 'digitalizacion_sector'
TABLE_TRANSICION = 'transicion_skills_ocupacion'
TABLE_VELOCIDAD = 'velocidad_cobertura'
TABLE_REMOTO = 'indice_trabajo_remoto'


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
    'area_funcional', 'nivel_seniority', 'sector_empresa',
    'clae_code', 'clae_grupo', 'clae_seccion', 'clae_score', 'clae_metodo', 'tipo_oferta',
    'tipo_contrato', 'provincia', 'localidad', 'modalidad',
    'nivel_educativo', 'titulo_requerido', 'experiencia_min_anios',
    'tiene_gente_cargo',
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
    where_clauses = ["m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')"]
    params = []

    if since:
        # Incluir ofertas con validado_timestamp O matching_timestamp posterior
        # (una oferta ya validada puede reprocesarse por regla nueva → matching_timestamp cambia)
        where_clauses.append("(m.validado_timestamp >= ? OR m.matching_timestamp >= ?)")
        params.extend([since, since])

    if ids:
        placeholders = ','.join(['?' for _ in ids])
        where_clauses.append(f"m.id_oferta IN ({placeholders})")
        params.extend(ids)

    where_sql = ' AND '.join(where_clauses)

    # Query principal con JOINs
    query = f"""
    SELECT
        -- Scraping (use NLP id_oferta for sub-offers)
        n.id_oferta, o.titulo, o.empresa, o.descripcion, o.localizacion,
        o.modalidad_trabajo, o.url_oferta, o.portal, o.fecha_publicacion_iso,
        o.scrapeado_en, o.provincia_normalizada, o.localidad_normalizada,
        o.estado_oferta, o.fecha_ultimo_visto, o.dias_publicada,
        o.categoria_permanencia,
        o.es_republicacion, o.numero_republicacion,
        -- Multi-position lineage
        n.parent_id_oferta, n.es_suboferta,
        -- NLP
        n.titulo_limpio, n.tareas_explicitas, n.mision_rol,
        n.area_funcional, n.nivel_seniority, n.sector_empresa,
        n.clae_code, n.clae_grupo, n.clae_seccion, n.clae_score, n.clae_metodo, n.tipo_oferta,
        n.tipo_contrato, n.provincia, n.localidad, n.modalidad,
        o.tipo_trabajo,
        n.nivel_educativo, n.titulo_requerido, n.experiencia_min_anios,
        n.tiene_gente_cargo,
        n.skills_tecnicas_list, n.soft_skills_list, n.tecnologias_list,
        n.herramientas_list, n.nlp_extraction_timestamp, n.nlp_version,
        -- Matching
        m.esco_occupation_uri, m.esco_occupation_label,
        m.isco_code, m.isco_label, m.occupation_match_score, m.occupation_match_method,
        m.skills_oferta_json, m.skills_matched_essential,
        m.skills_demandados_total, m.skills_matcheados_esco,
        m.matching_timestamp, m.matching_version, m.run_id,
        m.estado_validacion, m.validado_timestamp, m.validado_por,
        m.decision_metodo, m.regla_aplicada
    FROM ofertas o
    INNER JOIN ofertas_nlp n ON o.id_oferta = CASE
        WHEN n.es_suboferta = 1 THEN CAST(n.parent_id_oferta AS INTEGER)
        ELSE n.id_oferta END
    INNER JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
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
        for campo in ['tiene_gente_cargo']:
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
        d.source_classification,
        d.is_essential_for_occupation,
        d.is_optional_for_occupation
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
# LOOKUP DEPARTAMENTO INDEC
# ============================================================

# Cache global - se carga una sola vez
_indec_data = None
_indec_correcciones = None
_clae_secciones = None


def _normalizar_key(texto: str) -> str:
    """Normaliza texto para lookup: lowercase, sin tildes."""
    if not texto:
        return ""
    nfkd = unicode_normalize('NFKD', texto)
    sin_tildes = ''.join(c for c in nfkd if not (0x0300 <= ord(c) <= 0x036F))
    return sin_tildes.strip().lower()


def _cargar_indec():
    """Carga datos INDEC y correcciones (lazy, una sola vez)."""
    global _indec_data, _indec_correcciones

    if _indec_data is None:
        if INDEC_PATH.exists():
            with open(INDEC_PATH, 'r', encoding='utf-8') as f:
                _indec_data = json.load(f)
            logger.debug(f"INDEC cargado: {_indec_data.get('_total_localidades_unicas', 0)} localidades")
        else:
            logger.warning(f"INDEC no encontrado: {INDEC_PATH}")
            _indec_data = {"por_provincia": {}}

    if _indec_correcciones is None:
        if INDEC_CORRECCIONES_PATH.exists():
            with open(INDEC_CORRECCIONES_PATH, 'r', encoding='utf-8') as f:
                _indec_correcciones = json.load(f)
        else:
            logger.warning(f"Correcciones no encontradas: {INDEC_CORRECCIONES_PATH}")
            _indec_correcciones = {"correcciones": [], "barrios_caba": [], "meta_areas": [], "multi_localidad": []}


def lookup_departamento(localidad: str, provincia: str) -> Optional[str]:
    """
    Busca el departamento/partido INDEC para una localidad.

    Orden de prioridad:
    1. Correcciones manuales (exactas por input + provincia)
    2. Barrios CABA
    3. Meta-áreas (Buenos Aires, Gran Buenos Aires)
    4. Multi-localidad (Wilde, Avellaneda)
    5. Lookup exacto en INDEC (key normalizada)
    6. Fuzzy match en INDEC (difflib, cutoff=0.85)
    7. None si no se encuentra

    Args:
        localidad: Nombre de localidad (puede ser None)
        provincia: Nombre de provincia (puede ser None)

    Returns:
        Departamento/partido o None
    """
    _cargar_indec()

    if not localidad:
        # Sin localidad: si provincia es CABA, departamento es CABA
        if provincia and _normalizar_key(provincia) == 'caba':
            return 'CABA'
        return None

    loc_key = _normalizar_key(localidad)
    prov_key = _normalizar_key(provincia) if provincia else ""

    # 1. Correcciones manuales
    for corr in _indec_correcciones.get("correcciones", []):
        corr_input = _normalizar_key(corr["input"])
        corr_prov = _normalizar_key(corr.get("provincia", ""))

        if corr_input == loc_key:
            # Si la corrección tiene provincia, debe coincidir
            if corr_prov and corr_prov != prov_key:
                continue
            return corr.get("departamento")

    # 2. Barrios CABA
    for barrio in _indec_correcciones.get("barrios_caba", []):
        if _normalizar_key(barrio["input"]) == loc_key:
            return barrio.get("departamento", "CABA")

    # 3. Meta-áreas
    for meta in _indec_correcciones.get("meta_areas", []):
        meta_prov = _normalizar_key(meta.get("provincia", ""))
        if _normalizar_key(meta["input"]) == loc_key:
            if meta_prov and meta_prov != prov_key:
                continue
            return meta.get("departamento")  # Puede ser None

    # 4. Multi-localidad
    for multi in _indec_correcciones.get("multi_localidad", []):
        if _normalizar_key(multi["input"]) == loc_key:
            return multi.get("departamento")

    # 5. Provincia CABA sin localidad específica
    if prov_key == 'caba':
        return 'CABA'

    # 6. Lookup exacto en INDEC
    por_provincia = _indec_data.get("por_provincia", {})

    if prov_key in por_provincia:
        locs = por_provincia[prov_key].get("localidades", {})
        if loc_key in locs:
            return locs[loc_key]["departamento"]

    # 7. Fuzzy match en la misma provincia
    if prov_key in por_provincia:
        locs = por_provincia[prov_key].get("localidades", {})
        all_keys = list(locs.keys())
        matches = difflib.get_close_matches(loc_key, all_keys, n=1, cutoff=0.85)
        if matches:
            dept = locs[matches[0]]["departamento"]
            logger.debug(f"Fuzzy match: '{localidad}' ~ '{locs[matches[0]]['nombre']}' → {dept}")
            return dept

    # 8. Buscar en todas las provincias (último recurso)
    for pk, pdata in por_provincia.items():
        if pk == prov_key:
            continue
        locs = pdata.get("localidades", {})
        if loc_key in locs:
            logger.debug(f"Cross-province match: '{localidad}' found in {pdata['nombre']} → {locs[loc_key]['departamento']}")
            return locs[loc_key]["departamento"]

    return None


def _get_clae_descripcion_seccion(clae_seccion: str | None) -> str | None:
    """Devuelve el nombre legible de una sección CLAE (ej: 'G' → 'Comercio')."""
    global _clae_secciones

    if not clae_seccion:
        return None

    if _clae_secciones is None:
        if CLAE_NOMENCLADOR_PATH.exists():
            with open(CLAE_NOMENCLADOR_PATH, 'r', encoding='utf-8') as f:
                nomenclador = json.load(f)
            # Crear mapeo sección → nombre corto (title case, sin detalles)
            _clae_secciones = {}
            NOMBRES_CORTOS = {
                'A': 'Agricultura y Pesca',
                'B': 'Minería',
                'C': 'Industria Manufacturera',
                'D': 'Electricidad y Gas',
                'E': 'Agua y Saneamiento',
                'F': 'Construcción',
                'G': 'Comercio',
                'H': 'Transporte y Almacenamiento',
                'I': 'Alojamiento y Gastronomía',
                'J': 'Tecnología y Comunicaciones',
                'K': 'Finanzas y Seguros',
                'L': 'Servicios Inmobiliarios',
                'M': 'Servicios Profesionales',
                'N': 'Servicios Administrativos',
                'O': 'Administración Pública',
                'P': 'Enseñanza',
                'Q': 'Salud',
                'R': 'Arte y Esparcimiento',
                'S': 'Otros Servicios',
                'Z': 'Otros Sectores',
            }
            for sec in nomenclador.get('secciones', {}):
                _clae_secciones[sec] = NOMBRES_CORTOS.get(sec, sec)
            logger.debug(f"CLAE secciones cargadas: {len(_clae_secciones)}")
        else:
            logger.warning(f"CLAE nomenclador no encontrado: {CLAE_NOMENCLADOR_PATH}")
            _clae_secciones = {}

    return _clae_secciones.get(clae_seccion.upper().strip())


# Normalización de provincias NLP → nombres oficiales
# CABA es jurisdicción separada de Buenos Aires provincia.
# "Capital Federal" es nombre viejo → normalizar a CABA.
_PROVINCIA_NORMALIZACION = {
    'capital federal': 'CABA',
    'c.a.b.a.': 'CABA',
    'ciudad autonoma de buenos aires': 'CABA',
    'ciudad autónoma de buenos aires': 'CABA',
    'cordoba': 'Córdoba',
    'tucuman': 'Tucumán',
    'neuquen': 'Neuquén',
    'entre rios': 'Entre Ríos',
    'rio negro': 'Río Negro',
}

# Localidades/barrios que indican CABA (cuando scraping dice provincia=Buenos Aires)
_LOCALIDADES_CABA = {
    'capital federal', 'caba', 'palermo', 'recoleta', 'retiro',
    'saavedra', 'mataderos', 'villa pueyrredon', 'puerto madero',
    'belgrano', 'caballito', 'flores', 'barracas', 'almagro',
    'san telmo', 'villa crespo', 'colegiales', 'nuñez', 'liniers',
    'villa urquiza', 'villa devoto', 'boedo', 'san cristobal',
    'parque patricios', 'la boca', 'monserrat', 'balvanera',
    'constitucion', 'once', 'congreso', 'microcentro',
}


def _normalizar_ubicacion(provincia: str, localidad: str) -> tuple:
    """
    Normaliza provincia y localidad al vocabulario oficial del dashboard.

    Reglas:
    - CABA es provincia separada de Buenos Aires
    - Capital Federal (nombre viejo) → CABA
    - Si scraping dice Buenos Aires + localidad es barrio CABA → provincia=CABA, localidad=None
    - Localidades de CABA quedan vacías (comunas no se publican)
    - Tildes: Cordoba→Córdoba, Tucuman→Tucumán, etc.
    """
    if not provincia:
        return provincia, localidad

    key = provincia.strip().lower()

    # 1. Normalizar nombre de provincia (tildes, Capital Federal→CABA)
    prov_norm = _PROVINCIA_NORMALIZACION.get(key, provincia.strip())

    # 2. Si provincia=Buenos Aires pero localidad es barrio/zona CABA → reclasificar
    if prov_norm == 'Buenos Aires' and localidad:
        if localidad.strip().lower() in _LOCALIDADES_CABA:
            return 'CABA', None

    # 3. Si provincia=CABA → localidad vacía (comunas no se publican)
    if prov_norm == 'CABA':
        return 'CABA', None

    return prov_norm, localidad


# ============================================================
# UPLOAD A SUPABASE
# ============================================================

def transform_oferta_for_supabase(oferta: Dict) -> Dict:
    """
    Transforma una oferta de SQLite al formato de ofertas_dashboard de Supabase.
    """
    # Ubicación: NLP primero (99% cobertura), scraping fallback (4%)
    # Normalizar: CABA separado de Buenos Aires, tildes, Capital Federal→CABA
    raw_provincia = oferta.get('provincia') or oferta.get('provincia_normalizada')
    raw_localidad = oferta.get('localidad') or oferta.get('localidad_normalizada')
    provincia_norm, localidad_norm = _normalizar_ubicacion(raw_provincia, raw_localidad)

    return {
        'id_oferta': str(oferta.get('id_oferta')),
        'titulo': oferta.get('titulo'),
        'titulo_limpio': oferta.get('titulo_limpio'),
        'empresa': oferta.get('empresa'),
        'fecha_publicacion': oferta.get('fecha_publicacion_iso'),
        'url': oferta.get('url_oferta'),
        'portal': oferta.get('portal'),
        # Ubicación (NLP + normalización de provincias)
        'provincia': provincia_norm,
        'localidad': localidad_norm,
        'departamento': lookup_departamento(localidad_norm, provincia_norm),
        # ESCO - columnas completas para perfil argentino
        'esco_occupation_uri': oferta.get('esco_occupation_uri'),
        'esco_occupation_label': oferta.get('esco_occupation_label'),
        'isco_code': oferta.get('isco_code'),
        'isco_label': oferta.get('esco_occupation_label') or oferta.get('isco_label'),
        'occupation_match_score': oferta.get('occupation_match_score'),
        'occupation_match_method': oferta.get('occupation_match_method'),
        # NLP - Atributos básicos
        'modalidad': oferta.get('modalidad'),
        'nivel_seniority': oferta.get('nivel_seniority'),
        'area_funcional': oferta.get('area_funcional'),
        'sector_empresa': oferta.get('sector_empresa'),
        'clae_code': oferta.get('clae_code'),
        'clae_grupo': oferta.get('clae_grupo'),
        'clae_seccion': oferta.get('clae_seccion'),
        'clae_descripcion_seccion': _get_clae_descripcion_seccion(oferta.get('clae_seccion')),
        'clae_score': oferta.get('clae_score'),
        'clae_metodo': oferta.get('clae_metodo'),
        # NLP - Requerimientos (para tab Requerimientos del dashboard)
        'nivel_educativo': oferta.get('nivel_educativo'),
        'experiencia_min_anios': oferta.get('experiencia_min_anios'),
        'tiene_gente_cargo': oferta.get('tiene_gente_cargo'),
        'jornada_laboral': (oferta.get('tipo_trabajo') or '').lower() or None,
        # Salarios
        'salario_min': oferta.get('salario_min'),
        'salario_max': oferta.get('salario_max'),
        'moneda': oferta.get('moneda'),
        # Skills (JSONB para backward compatibility)
        'skills_tecnicas': oferta.get('skills_tecnicas_list'),
        'soft_skills': oferta.get('soft_skills_list'),
        # Estado
        'estado': oferta.get('estado_oferta', 'activa'),
        'categoria_permanencia': oferta.get('categoria_permanencia'),
        'es_republicacion': bool(oferta.get('es_republicacion')) if oferta.get('es_republicacion') is not None else False,
        'numero_republicacion': oferta.get('numero_republicacion'),
        # Multi-position lineage
        'parent_id_oferta': oferta.get('parent_id_oferta'),
        'es_suboferta': bool(oferta.get('es_suboferta')) if oferta.get('es_suboferta') is not None else False,
        # Validación panel — campos para revisión humana
        'descripcion': oferta.get('descripcion'),
        'tareas_explicitas': oferta.get('tareas_explicitas'),
        'mision_rol': oferta.get('mision_rol'),
        'decision_metodo': oferta.get('decision_metodo'),
        'regla_aplicada': oferta.get('regla_aplicada'),
        'run_id': oferta.get('run_id'),
        'matching_version': oferta.get('matching_version'),
        'fecha_sync': datetime.now().isoformat(),
    }


def _detect_valid_columns(client, table: str) -> set:
    """Detecta columnas válidas en Supabase probando un SELECT vacío."""
    try:
        result = client.table(table).select('*').limit(0).execute()
        # PostgREST returns column names in the response even with 0 rows
        # If we have data, extract keys from first row; otherwise return empty (all allowed)
        return set()  # Can't detect from empty result, allow all
    except Exception:
        return set()


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
    invalid_cols = set()  # Columnas que Supabase no reconoce (se detectan al primer error)

    for i in range(0, len(ofertas_transformed), BATCH_SIZE):
        batch = ofertas_transformed[i:i + BATCH_SIZE]

        # Filtrar columnas inválidas detectadas previamente
        if invalid_cols:
            batch = [{k: v for k, v in row.items() if k not in invalid_cols} for row in batch]

        try:
            result = client.table(TABLE_OFERTAS).upsert(
                batch,
                on_conflict='id_oferta'
            ).execute()
            total += len(batch)
            logger.info(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} ofertas")
        except Exception as e:
            error_msg = str(e)
            # Detectar columnas que no existen en Supabase
            if 'PGRST204' in error_msg or 'does not exist' in error_msg:
                import re
                col_match = re.search(r"'(\w+)' column", error_msg)
                if col_match:
                    col_name = col_match.group(1)
                    invalid_cols.add(col_name)
                    logger.warning(f"Columna '{col_name}' no existe en Supabase, omitiendo. "
                                   f"Ejecutar: ALTER TABLE {TABLE_OFERTAS} ADD COLUMN {col_name} TEXT;")
                    # Reintentar este batch sin la columna inválida
                    batch = [{k: v for k, v in row.items() if k not in invalid_cols} for row in batch]
                    try:
                        result = client.table(TABLE_OFERTAS).upsert(
                            batch, on_conflict='id_oferta'
                        ).execute()
                        total += len(batch)
                        logger.info(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} ofertas (sin {invalid_cols})")
                        continue
                    except Exception as e2:
                        logger.error(f"Error en batch {i//BATCH_SIZE + 1} (reintento): {e2}")
                        raise
            logger.error(f"Error en batch {i//BATCH_SIZE + 1}: {e}")
            raise

    if invalid_cols:
        logger.warning(f"Columnas omitidas (no existen en Supabase): {invalid_cols}")
        logger.warning(f"Para agregar, ejecutar en Supabase SQL Editor:")
        for col in invalid_cols:
            logger.warning(f"  ALTER TABLE {TABLE_OFERTAS} ADD COLUMN IF NOT EXISTS {col} TEXT;")

    return total


_equiv_cache = None  # Module-level cache for equivalence lookup

def load_equivalences_lookup(client) -> Dict[str, Dict]:
    """
    Load skill_equivalence_lookup + skill_equivalences from Supabase.
    Returns: {skill_uri: {equivalence_id, canonical_label}}
    """
    global _equiv_cache
    if _equiv_cache is not None:
        return _equiv_cache

    equiv_map = {}
    try:
        # Load lookup table (paginated)
        uri_to_eq = {}
        offset = 0
        while True:
            batch = client.table('skill_equivalence_lookup').select(
                'skill_uri,equivalence_id'
            ).range(offset, offset + 999).execute()
            if not batch.data:
                break
            for row in batch.data:
                uri_to_eq[row['skill_uri']] = row['equivalence_id']
            offset += len(batch.data)
            if len(batch.data) < 1000:
                break

        # Load equivalences (for canonical labels)
        eq_labels = {}
        offset = 0
        while True:
            batch = client.table('skill_equivalences').select(
                'id,label_representante,label_argentino'
            ).range(offset, offset + 999).execute()
            if not batch.data:
                break
            for row in batch.data:
                eq_labels[row['id']] = row.get('label_argentino') or row['label_representante']
            offset += len(batch.data)
            if len(batch.data) < 1000:
                break

        # Build combined map
        for uri, eq_id in uri_to_eq.items():
            equiv_map[uri] = {
                'equivalence_id': eq_id,
                'canonical_label': eq_labels.get(eq_id),
            }

        logger.info(f"Equivalencias cargadas: {len(equiv_map)} URIs → {len(eq_labels)} grupos")
    except Exception as e:
        logger.warning(f"No se pudieron cargar equivalencias: {e}")

    _equiv_cache = equiv_map
    return equiv_map


# Valores aceptados por el check constraint `ofertas_skills_origen_check`
# Ver migrations de Supabase. Si llega un valor fuera de esta lista lo mapeamos.
_ORIGEN_ALIAS = {
    'soft_skills_nlp': 'skills_nlp',      # soft skills detectadas por LLM → categoría skills_nlp
    'terminologia_argentina': 'terminologia',
    'sinonimo_argentino': 'terminologia',
    'regla_cynthia': 'regla',
    'regla_issue': 'regla',
}


def transform_skill_for_supabase(skill: Dict, equiv_map: Optional[Dict] = None) -> Dict:
    """
    Transforma un skill de SQLite al formato de ofertas_skills de Supabase.
    Si equiv_map se provee, agrega equivalence_id y canonical_label.
    """
    skill_uri = skill.get('esco_skill_uri') or skill.get('skill_uri')
    equiv = (equiv_map or {}).get(skill_uri, {})

    origen_raw = skill.get('skill_tipo_fuente') or skill.get('origen', 'merged')
    origen = _ORIGEN_ALIAS.get(origen_raw, origen_raw)

    return {
        'id_oferta': str(skill.get('id_oferta')),
        'skill_uri': skill_uri,
        'preferred_label': skill.get('esco_skill_label') or skill.get('preferred_label'),
        'l1': skill.get('l1') or skill.get('L1'),
        'l1_nombre': skill.get('l1_nombre') or skill.get('L1_nombre'),
        'l2': skill.get('l2') or skill.get('L2'),
        'l2_nombre': skill.get('l2_nombre') or skill.get('L2_nombre'),
        'es_digital': skill.get('es_digital', False),
        'origen': origen,
        'score': skill.get('match_score') or skill.get('score'),
        # SPEC U-1 H16 fix: mapear flags ESCO desde columnas locales backfilleadas por C4
        'es_esencial': bool(skill.get('is_essential_for_occupation', 0)),
        'es_opcional': bool(skill.get('is_optional_for_occupation', 0)),
        'equivalence_id': equiv.get('equivalence_id'),
        'canonical_label': equiv.get('canonical_label'),
    }


def upsert_skills(client, skills: List[Dict], dry_run: bool = False) -> int:
    """
    Upsert skills normalizados a Supabase (tabla ofertas_skills).

    Usa delete + insert por oferta para evitar duplicados.
    """
    if not skills:
        return 0

    # Load equivalences for canonical labels
    equiv_map = load_equivalences_lookup(client)

    # Transformar al formato de Supabase
    skills_transformed = [transform_skill_for_supabase(s, equiv_map) for s in skills]

    # Filtrar skills sin URI (inválidos)
    skills_transformed = [s for s in skills_transformed if s.get('skill_uri')]

    # Deduplicar por (id_oferta, skill_uri) - quedarse con mayor score
    seen = {}
    for s in skills_transformed:
        key = (s['id_oferta'], s['skill_uri'])
        if key not in seen or (s.get('score') or 0) > (seen[key].get('score') or 0):
            seen[key] = s
    skills_unique = list(seen.values())

    if len(skills_unique) < len(skills_transformed):
        logger.warning(f"Se eliminaron {len(skills_transformed) - len(skills_unique)} skills duplicados por URI")

    # Segunda pasada: dedup semántica por label normalizado (sin acentos)
    # Atrapa variantes como "negocio electronico" vs "negocio electrónico"
    def _normalize_label(label):
        if not label:
            return ''
        nfkd = unicodedata.normalize('NFKD', label)
        return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    seen_labels = {}
    skills_final = []
    for s in skills_unique:
        label_key = (s['id_oferta'], _normalize_label(s.get('preferred_label', '')))
        if label_key[1] == '':
            # Sin label, no se puede deduplicar semánticamente
            skills_final.append(s)
            continue
        if label_key not in seen_labels:
            seen_labels[label_key] = s
            skills_final.append(s)
        else:
            existing = seen_labels[label_key]
            if (s.get('score') or 0) > (existing.get('score') or 0):
                skills_final.remove(existing)
                seen_labels[label_key] = s
                skills_final.append(s)

    if len(skills_final) < len(skills_unique):
        logger.warning(f"Se eliminaron {len(skills_unique) - len(skills_final)} skills duplicados semánticos (label normalizado)")

    # Tercera pasada: dedup por (id_oferta, equivalence_id) para skills del mismo grupo
    seen_equiv = {}
    skills_deduped = []
    for s in skills_final:
        eq_id = s.get('equivalence_id')
        if eq_id:
            key = (s['id_oferta'], eq_id)
            if key not in seen_equiv:
                seen_equiv[key] = s
                skills_deduped.append(s)
            else:
                existing = seen_equiv[key]
                if (s.get('score') or 0) > (existing.get('score') or 0):
                    skills_deduped.remove(existing)
                    seen_equiv[key] = s
                    skills_deduped.append(s)
        else:
            skills_deduped.append(s)

    if len(skills_deduped) < len(skills_final):
        logger.info(f"Se eliminaron {len(skills_final) - len(skills_deduped)} skills duplicados por equivalencia")

    skills_transformed = skills_deduped

    if dry_run:
        logger.info(f"[DRY-RUN] Upsert {len(skills_transformed)} skills")
        return len(skills_transformed)

    # Obtener IDs únicos de ofertas
    offer_ids = list(set(s['id_oferta'] for s in skills_transformed))

    # Eliminar skills existentes para estas ofertas (para evitar duplicados)
    # Usar batches de DELETEs para evitar HTTP/2 stream limit (20K)
    delete_batch_size = 500
    for di in range(0, len(offer_ids), delete_batch_size):
        delete_chunk = offer_ids[di:di + delete_batch_size]
        for oid in delete_chunk:
            for attempt in range(3):
                try:
                    client.table(TABLE_SKILLS).delete().eq('id_oferta', oid).execute()
                    break
                except Exception as e:
                    if attempt < 2:
                        import time
                        logger.warning(f"Retry DELETE {oid} (attempt {attempt+1}): {e}")
                        time.sleep(2)
                    else:
                        logger.warning(f"Error eliminando skills {oid} (skip): {e}")
        if di > 0 and di % 2000 == 0:
            logger.info(f"  Skills DELETE progress: {di}/{len(offer_ids)}")

    # Insertar nuevas con retry para manejar HTTP/2 connection reset
    total = 0
    for i in range(0, len(skills_transformed), BATCH_SIZE):
        batch = skills_transformed[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        for attempt in range(3):
            try:
                result = client.table(TABLE_SKILLS).upsert(
                    batch,
                    on_conflict='id_oferta,skill_uri'
                ).execute()
                total += len(batch)
                break
            except Exception as e:
                if attempt < 2:
                    import time
                    logger.warning(f"Retry skills batch {batch_num} (attempt {attempt+1}): {e}")
                    time.sleep(3)
                else:
                    logger.error(f"Error insertando skills batch {batch_num} after 3 attempts: {e}")
                    raise

        if batch_num % 50 == 0:
            logger.info(f"  Skills INSERT progress: {total}/{len(skills_transformed)}")

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
# SINCRONIZACIÓN DE SISTEMA_ESTADO
# ============================================================

TABLE_SISTEMA_ESTADO = 'sistema_estado'


def calcular_estado_sistema(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calcula métricas del estado actual del sistema desde SQLite.
    Estas métricas alimentan /admin/scraping y /admin/arquitectura.
    """
    estado = {}

    # === FASE 1: ADQUISICIÓN ===
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN estado_oferta = 'activa' THEN 1 ELSE 0 END) as activas,
            SUM(CASE WHEN estado_oferta = 'cerrada' THEN 1 ELSE 0 END) as cerradas,
            MAX(scrapeado_en) as ultimo_scraping
        FROM ofertas
    """)
    row = cursor.fetchone()
    estado['fase1_ofertas_totales'] = row['total'] or 0
    estado['fase1_ofertas_activas'] = row['activas'] or 0
    estado['fase1_ofertas_cerradas'] = row['cerradas'] or 0
    estado['fase1_ultimo_scraping'] = row['ultimo_scraping']

    # Días desde último scraping
    if row['ultimo_scraping']:
        try:
            from datetime import datetime
            ultimo = datetime.fromisoformat(row['ultimo_scraping'].replace('Z', '+00:00'))
            dias = (datetime.now(ultimo.tzinfo) - ultimo).days
            estado['fase1_dias_desde_scraping'] = max(0, dias)
        except:
            estado['fase1_dias_desde_scraping'] = 0
    else:
        estado['fase1_dias_desde_scraping'] = 0

    # Ofertas por fuente/portal
    cursor = conn.execute("""
        SELECT portal, COUNT(*) as cantidad
        FROM ofertas
        WHERE estado_oferta = 'activa'
        GROUP BY portal
    """)
    fuentes = {}
    for row in cursor.fetchall():
        if row['portal']:
            fuentes[row['portal']] = row['cantidad']
    estado['fase1_fuentes'] = fuentes

    # === FASE 2: PROCESAMIENTO ===
    # Con NLP
    cursor = conn.execute("SELECT COUNT(*) FROM ofertas_nlp")
    estado['fase2_con_nlp'] = cursor.fetchone()[0] or 0

    # Sin NLP
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas o
        WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = o.id_oferta)
    """)
    estado['fase2_sin_nlp'] = cursor.fetchone()[0] or 0

    # Con matching
    cursor = conn.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
    estado['fase2_con_matching'] = cursor.fetchone()[0] or 0

    # Pendientes matching
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_nlp n
        WHERE NOT EXISTS (SELECT 1 FROM ofertas_esco_matching m WHERE m.id_oferta = n.id_oferta)
    """)
    estado['fase2_pendientes_matching'] = cursor.fetchone()[0] or 0

    # Validadas (todos los estados de validación)
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
    """)
    estado['fase2_validadas'] = cursor.fetchone()[0] or 0

    # Pendientes validación
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE estado_validacion = 'pendiente' OR estado_validacion IS NULL
    """)
    estado['fase2_pendientes_validacion'] = cursor.fetchone()[0] or 0

    # Errores sin resolver
    cursor = conn.execute("SELECT COUNT(*) FROM validation_errors WHERE resuelto = 0")
    estado['fase2_errores_sin_resolver'] = cursor.fetchone()[0] or 0

    # Reglas de negocio
    try:
        rules_path = PROJECT_ROOT / "config" / "matching_rules_business.json"
        if rules_path.exists():
            with open(rules_path) as f:
                rules = json.load(f)
                estado['fase2_reglas_negocio'] = len(rules.get('rules', []))
        else:
            estado['fase2_reglas_negocio'] = 0
    except:
        estado['fase2_reglas_negocio'] = 0

    # Tasa de convergencia y último run
    cursor = conn.execute("""
        SELECT run_id, COUNT(*) as ofertas
        FROM ofertas_esco_matching
        WHERE run_id IS NOT NULL
        GROUP BY run_id
        ORDER BY matching_timestamp DESC
        LIMIT 1
    """)
    last_run = cursor.fetchone()
    if last_run:
        estado['fase2_ultimo_run'] = last_run['run_id']
        # Calcular tasa de errores del último run
        cursor = conn.execute("""
            SELECT COUNT(*) FROM validation_errors
            WHERE resuelto = 0 AND id_oferta IN (
                SELECT id_oferta FROM ofertas_esco_matching WHERE run_id = ?
            )
        """, [last_run['run_id']])
        errores_run = cursor.fetchone()[0] or 0
        total_run = last_run['ofertas'] or 1
        estado['fase2_tasa_convergencia'] = round((1 - errores_run / total_run) * 100, 1)
    else:
        estado['fase2_ultimo_run'] = None
        estado['fase2_tasa_convergencia'] = None

    # === FASE 3: PRESENTACIÓN ===
    # Esto se calcula después del sync a Supabase
    estado['fase3_ofertas_supabase'] = estado['fase2_validadas']  # Aproximación
    estado['fase3_pendientes_sync'] = 0  # Se actualiza después

    # === SUGERENCIA DE FASE ===
    # Determinar qué fase necesita atención
    if estado['fase1_dias_desde_scraping'] > 3:
        estado['fase_sugerida'] = 1
        estado['fase_sugerida_nombre'] = 'Adquisición'
        estado['fase_sugerida_razon'] = f"Último scraping hace {estado['fase1_dias_desde_scraping']} días"
    elif estado['fase2_errores_sin_resolver'] > 10:
        estado['fase_sugerida'] = 2
        estado['fase_sugerida_nombre'] = 'Procesamiento'
        estado['fase_sugerida_razon'] = f"{estado['fase2_errores_sin_resolver']} errores pendientes"
    elif estado['fase2_pendientes_matching'] > 100:
        estado['fase_sugerida'] = 2
        estado['fase_sugerida_nombre'] = 'Procesamiento'
        estado['fase_sugerida_razon'] = f"{estado['fase2_pendientes_matching']} ofertas sin matching"
    else:
        estado['fase_sugerida'] = 3
        estado['fase_sugerida_nombre'] = 'Presentación'
        estado['fase_sugerida_razon'] = 'Sistema saludable, continuar sync'

    return estado


def sync_sistema_estado(client, conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """
    Sincroniza el estado del sistema a Supabase.
    Inserta un nuevo registro con el timestamp actual.
    """
    estado = calcular_estado_sistema(conn)

    if dry_run:
        logger.info("[DRY-RUN] Estado del sistema calculado:")
        for k, v in estado.items():
            logger.info(f"  {k}: {v}")
        return True

    try:
        # Agregar metadata de sync
        estado['sync_source'] = 'sync_to_supabase.py'
        estado['sync_version'] = '2.1'

        # Insertar nuevo registro (no upsert - queremos historial)
        result = client.table(TABLE_SISTEMA_ESTADO).insert(estado).execute()
        logger.info("Estado del sistema sincronizado a Supabase")
        return True
    except Exception as e:
        logger.error(f"Error sincronizando sistema_estado: {e}")
        return False


def sync_scraping_live_stats(client, conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """
    Actualiza scraping_live_stats con datos de la BD local.

    Esta tabla alimenta el panel de portales del dashboard. Se mergea con
    los datos del VPS para que portales que corren local (ej: Indeed) también
    se reflejen correctamente.
    """
    from datetime import timezone

    cursor = conn.execute("""
        SELECT portal,
               COUNT(*) as total,
               MAX(scrapeado_en) as ultimo,
               SUM(CASE WHEN scrapeado_en >= datetime('now', '-7 days') THEN 1 ELSE 0 END) as ultimos_7d,
               SUM(CASE WHEN scrapeado_en >= datetime('now', '-1 day') THEN 1 ELSE 0 END) as hoy
        FROM ofertas
        GROUP BY portal
        ORDER BY total DESC
    """)

    portales = {}
    ultimo_global = None
    for row in cursor.fetchall():
        portal = row['portal'] or 'sin_portal'
        portales[portal] = {
            'total': row['total'],
            'ultimo_scraping': str(row['ultimo'] or ''),
            'ultimos_7d': row['ultimos_7d'] or 0,
            'hoy': row['hoy'] or 0,
        }
        if row['ultimo'] and (not ultimo_global or row['ultimo'] > ultimo_global):
            ultimo_global = row['ultimo']

    total = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]

    if dry_run:
        logger.info(f"[DRY-RUN] scraping_live_stats: {total} ofertas, {len(portales)} portales")
        return True

    try:
        client.table('scraping_live_stats').upsert({
            'id': 'current',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_ofertas': total,
            'portales': portales,
            'ultimo_scraping': ultimo_global,
        }).execute()
        logger.info(f"scraping_live_stats actualizado: {total} ofertas, {len(portales)} portales")
        return True
    except Exception as e:
        logger.error(f"Error actualizando scraping_live_stats: {e}")
        return False


# ============================================================
# TENSIÓN DE DEMANDA (V-16)
# ============================================================

def calcular_tension_ocupaciones(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula indicadores de tensión de demanda por ocupación ISCO.

    Indicadores:
    - Persistencia: % de posiciones con ventana de publicación >45 días
    - Insistencia: % de posiciones que fueron republicadas
    - Cuadrante: CRITICO (alta-alta), URGENTE (alta-baja), PASIVO (baja-alta), FLUIDO (baja-baja)

    Una "posición" = un grupo_republicacion (ofertas agrupadas que son la misma vacante)
    Ofertas sin grupo = cada una es su propia posición.
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT
            o.id_oferta,
            m.isco_code,
            m.isco_label,
            o.dias_publicada,
            COALESCE(o.grupo_republicacion, o.id_oferta) AS posicion_id,
            CASE WHEN o.grupo_republicacion IS NOT NULL THEN 1 ELSE 0 END AS es_republicada
        FROM ofertas o
        INNER JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
    ),
    posiciones AS (
        SELECT
            isco_code,
            isco_label,
            posicion_id,
            MAX(dias_publicada) AS ventana_dias,
            MAX(es_republicada) AS fue_republicada,
            COUNT(*) AS ofertas_en_posicion
        FROM ofertas_validadas
        GROUP BY isco_code, isco_label, posicion_id
    ),
    por_isco AS (
        SELECT
            isco_code,
            MAX(isco_label) AS isco_label,
            COUNT(DISTINCT posicion_id) AS total_posiciones,
            SUM(ofertas_en_posicion) AS total_ofertas,
            ROUND(
                100.0 * SUM(CASE WHEN ventana_dias > 45 THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS persistencia,
            ROUND(
                100.0 * SUM(CASE WHEN fue_republicada = 1 THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS insistencia
        FROM posiciones
        GROUP BY isco_code
        HAVING COUNT(DISTINCT posicion_id) >= 1
    )
    SELECT
        isco_code,
        isco_label,
        total_posiciones,
        total_ofertas,
        persistencia,
        insistencia,
        CASE
            WHEN persistencia >= 50 AND insistencia >= 50 THEN 'CRITICO'
            WHEN persistencia >= 50 AND insistencia < 50 THEN 'URGENTE'
            WHEN persistencia < 50 AND insistencia >= 50 THEN 'PASIVO'
            ELSE 'FLUIDO'
        END AS cuadrante
    FROM por_isco
    ORDER BY total_posiciones DESC
    """

    cursor = conn.execute(query)
    rows = cursor.fetchall()

    resultados = []
    for row in rows:
        resultados.append({
            'isco_code': row['isco_code'],
            'isco_label': row['isco_label'],
            'total_posiciones': row['total_posiciones'],
            'total_ofertas': row['total_ofertas'],
            'persistencia': float(row['persistencia']),
            'insistencia': float(row['insistencia']),
            'cuadrante': row['cuadrante'],
            'calculado_en': datetime.now().isoformat(),
        })

    logger.info(f"Tensión calculada: {len(resultados)} ocupaciones")
    cuadrantes = {}
    for r in resultados:
        cuadrantes[r['cuadrante']] = cuadrantes.get(r['cuadrante'], 0) + 1
    for c, n in sorted(cuadrantes.items()):
        logger.info(f"  {c}: {n}")

    return resultados


def sync_tension_ocupaciones(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """
    Sincroniza tensión de demanda a Supabase.
    Trunca y reinserta (datos calculados, no incrementales).
    """
    resultados = calcular_tension_ocupaciones(conn)

    if not resultados:
        logger.warning("No hay datos de tensión para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} ocupaciones de tensión")
        return len(resultados)

    # Truncar tabla (delete all rows - Supabase workaround)
    try:
        client.table(TABLE_TENSION).delete().neq('isco_code', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando tension_ocupaciones: {e}")

    # Insertar en batches
    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_TENSION).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando tensión batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Tensión sincronizada: {total} ocupaciones")
    return total


# ============================================================
# CONCENTRACIÓN OCUPACIONAL (I-02) — Índice HHI
# ============================================================

def calcular_concentracion_ocupacional(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula el Índice Herfindahl-Hirschman (HHI) de concentración de ofertas por ISCO.
    Retorna 3 tipos de filas: 'global' (HHI total), 'mensual' (HHI por mes),
    'ocupacion' (top 15 con share).
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT o.id_oferta, m.isco_code, m.isco_label,
               strftime('%Y-%m', o.fecha_publicacion_iso) AS mes
        FROM ofertas o
        JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
          AND o.fecha_publicacion_iso IS NOT NULL
    ),
    global_total AS (
        SELECT COUNT(*) AS total FROM ofertas_validadas
    ),
    por_isco AS (
        SELECT isco_code, MAX(isco_label) AS isco_label,
               COUNT(*) AS ofertas,
               ROUND(100.0 * COUNT(*) / (SELECT total FROM global_total), 2) AS share_pct
        FROM ofertas_validadas
        GROUP BY isco_code
    ),
    hhi_global AS (
        SELECT ROUND(SUM(share_pct * share_pct) / 10000.0, 6) AS hhi
        FROM por_isco
    )
    SELECT 'ocupacion' AS tipo, NULL AS mes, isco_code, isco_label, ofertas, share_pct,
           0 AS hhi, NULL AS clasificacion
    FROM por_isco
    ORDER BY share_pct DESC
    LIMIT 15
    """

    cursor = conn.execute(query)
    rows = cursor.fetchall()

    resultados = []
    now = datetime.now().isoformat()

    for row in rows:
        resultados.append({
            'tipo': 'ocupacion',
            'mes': None,
            'isco_code': row['isco_code'],
            'isco_label': row['isco_label'],
            'ofertas': row['ofertas'],
            'share_pct': float(row['share_pct']),
            'hhi': 0,
            'clasificacion': None,
            'calculado_en': now,
        })

    # HHI global
    hhi_query = """
    WITH ofertas_validadas AS (
        SELECT m.isco_code
        FROM ofertas o
        JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
          AND o.fecha_publicacion_iso IS NOT NULL
    ),
    global_total AS (
        SELECT COUNT(*) AS total FROM ofertas_validadas
    ),
    por_isco AS (
        SELECT isco_code, COUNT(*) AS ofertas,
               ROUND(100.0 * COUNT(*) / (SELECT total FROM global_total), 2) AS share_pct
        FROM ofertas_validadas
        GROUP BY isco_code
    )
    SELECT ROUND(SUM(share_pct * share_pct) / 10000.0, 6) AS hhi
    FROM por_isco
    """
    hhi_row = conn.execute(hhi_query).fetchone()
    hhi_val = float(hhi_row['hhi']) if hhi_row and hhi_row['hhi'] else 0

    if hhi_val < 0.15:
        clasificacion = 'diversificado'
    elif hhi_val < 0.25:
        clasificacion = 'moderado'
    else:
        clasificacion = 'concentrado'

    resultados.append({
        'tipo': 'global',
        'mes': None,
        'isco_code': None,
        'isco_label': None,
        'ofertas': 0,
        'share_pct': 0,
        'hhi': hhi_val,
        'clasificacion': clasificacion,
        'calculado_en': now,
    })

    # HHI mensual
    mensual_query = """
    WITH ofertas_validadas AS (
        SELECT m.isco_code,
               strftime('%Y-%m', o.fecha_publicacion_iso) AS mes
        FROM ofertas o
        JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
          AND o.fecha_publicacion_iso IS NOT NULL
    ),
    por_mes AS (
        SELECT mes, COUNT(*) AS total_mes FROM ofertas_validadas GROUP BY mes
    ),
    isco_mes AS (
        SELECT mes, isco_code, COUNT(*) AS ofertas_mes
        FROM ofertas_validadas GROUP BY mes, isco_code
    )
    SELECT im.mes,
           ROUND(SUM( (100.0 * im.ofertas_mes / pm.total_mes) *
                      (100.0 * im.ofertas_mes / pm.total_mes) ) / 10000.0, 6) AS hhi
    FROM isco_mes im
    JOIN por_mes pm ON im.mes = pm.mes
    GROUP BY im.mes
    ORDER BY im.mes
    """
    for row in conn.execute(mensual_query).fetchall():
        resultados.append({
            'tipo': 'mensual',
            'mes': row['mes'],
            'isco_code': None,
            'isco_label': None,
            'ofertas': 0,
            'share_pct': 0,
            'hhi': float(row['hhi']) if row['hhi'] else 0,
            'clasificacion': None,
            'calculado_en': now,
        })

    logger.info(f"Concentración calculada: {len(resultados)} filas (HHI global={hhi_val:.4f} → {clasificacion})")
    return resultados


def sync_concentracion_ocupacional(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza concentración ocupacional a Supabase. Trunca y reinserta."""
    resultados = calcular_concentracion_ocupacional(conn)

    if not resultados:
        logger.warning("No hay datos de concentración para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de concentración")
        return len(resultados)

    try:
        client.table(TABLE_CONCENTRACION).delete().neq('tipo', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_CONCENTRACION}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_CONCENTRACION).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando concentración batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Concentración sincronizada: {total} filas")
    return total


# ============================================================
# BRECHA DE CALIFICACIÓN (I-03)
# ============================================================

def calcular_brecha_calificacion(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula la brecha de calificación: skills promedio por ISCO vs promedio de mercado.
    brecha > 1.0 = sobreexigente, < 1.0 = subexigente.
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT m.id_oferta, m.isco_code, m.isco_label
        FROM ofertas_esco_matching m
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
    ),
    skills_por_oferta AS (
        SELECT ov.id_oferta, ov.isco_code, ov.isco_label,
               COUNT(DISTINCT d.esco_skill_label) AS n_skills
        FROM ofertas_validadas ov
        JOIN ofertas_esco_skills_detalle d ON ov.id_oferta = d.id_oferta
        GROUP BY ov.id_oferta, ov.isco_code, ov.isco_label
    ),
    promedio_mercado AS (
        SELECT ROUND(AVG(n_skills), 2) AS avg_mercado FROM skills_por_oferta
    ),
    por_isco AS (
        SELECT isco_code, MAX(isco_label) AS isco_label,
               COUNT(*) AS total_ofertas,
               ROUND(AVG(n_skills), 2) AS skills_promedio,
               ROUND(AVG(n_skills) / (SELECT avg_mercado FROM promedio_mercado), 2) AS brecha
        FROM skills_por_oferta
        GROUP BY isco_code
        HAVING COUNT(*) >= 5
    )
    SELECT isco_code, isco_label, total_ofertas, skills_promedio, brecha,
           CASE
               WHEN brecha > 1.3 THEN 'sobreexigente'
               WHEN brecha < 0.7 THEN 'subexigente'
               ELSE 'equilibrado'
           END AS categoria
    FROM por_isco
    ORDER BY brecha DESC
    """

    cursor = conn.execute(query)
    rows = cursor.fetchall()

    now = datetime.now().isoformat()
    resultados = []
    for row in rows:
        resultados.append({
            'isco_code': row['isco_code'],
            'isco_label': row['isco_label'],
            'total_ofertas': row['total_ofertas'],
            'skills_promedio': float(row['skills_promedio']),
            'brecha': float(row['brecha']),
            'categoria': row['categoria'],
            'calculado_en': now,
        })

    cats = {}
    for r in resultados:
        cats[r['categoria']] = cats.get(r['categoria'], 0) + 1
    logger.info(f"Brecha calculada: {len(resultados)} ocupaciones — {cats}")
    return resultados


def sync_brecha_calificacion(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza brecha de calificación a Supabase. Trunca y reinserta."""
    resultados = calcular_brecha_calificacion(conn)

    if not resultados:
        logger.warning("No hay datos de brecha para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de brecha")
        return len(resultados)

    try:
        client.table(TABLE_BRECHA).delete().neq('isco_code', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_BRECHA}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_BRECHA).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando brecha batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Brecha sincronizada: {total} ocupaciones")
    return total


# ============================================================
# DIGITALIZACIÓN POR SECTOR (I-05)
# ============================================================

def calcular_digitalizacion_sector(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula el índice de digitalización por sector CLAE:
    % de skills digitales sobre total de skills por sector.
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT m.id_oferta, n.clae_seccion
        FROM ofertas_esco_matching m
        JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND n.clae_seccion IS NOT NULL
    ),
    skills_con_digital AS (
        SELECT ov.id_oferta, ov.clae_seccion,
               json_extract(d.source_classification, '$.es_digital') AS es_digital
        FROM ofertas_validadas ov
        JOIN ofertas_esco_skills_detalle d ON ov.id_oferta = d.id_oferta
        WHERE d.source_classification IS NOT NULL
    ),
    por_sector AS (
        SELECT clae_seccion,
               COUNT(*) AS total_skills,
               SUM(CASE WHEN es_digital = 1 THEN 1 ELSE 0 END) AS skills_digitales,
               COUNT(DISTINCT id_oferta) AS total_ofertas,
               ROUND(100.0 * SUM(CASE WHEN es_digital = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS idx_digital
        FROM skills_con_digital
        GROUP BY clae_seccion
        HAVING COUNT(*) >= 10
    )
    SELECT clae_seccion, total_skills, skills_digitales, total_ofertas, idx_digital,
           CASE
               WHEN idx_digital > 40 THEN 'alto'
               WHEN idx_digital > 20 THEN 'medio'
               ELSE 'bajo'
           END AS nivel_digital
    FROM por_sector
    ORDER BY idx_digital DESC
    """

    cursor = conn.execute(query)
    rows = cursor.fetchall()

    now = datetime.now().isoformat()
    resultados = []
    for row in rows:
        resultados.append({
            'clae_seccion': row['clae_seccion'],
            'total_skills': row['total_skills'],
            'skills_digitales': row['skills_digitales'],
            'total_ofertas': row['total_ofertas'],
            'idx_digital': float(row['idx_digital']),
            'nivel_digital': row['nivel_digital'],
            'calculado_en': now,
        })

    niveles = {}
    for r in resultados:
        niveles[r['nivel_digital']] = niveles.get(r['nivel_digital'], 0) + 1
    logger.info(f"Digitalización calculada: {len(resultados)} sectores — {niveles}")
    return resultados


def sync_digitalizacion_sector(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza digitalización por sector a Supabase. Trunca y reinserta."""
    resultados = calcular_digitalizacion_sector(conn)

    if not resultados:
        logger.warning("No hay datos de digitalización para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de digitalización")
        return len(resultados)

    try:
        client.table(TABLE_DIGITALIZACION).delete().neq('clae_seccion', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_DIGITALIZACION}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_DIGITALIZACION).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando digitalización batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Digitalización sincronizada: {total} sectores")
    return total


# ============================================================
# TRANSICIÓN SKILLS-OCUPACIÓN (I-04)
# ============================================================

def calcular_transicion_skills(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula mapa de transición skills-ocupación usando Jaccard similarity.
    Nodos = top 20 ISCOs por volumen. Enlaces = pares con Jaccard >= 0.10.
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT m.id_oferta, m.isco_code, m.isco_label
        FROM ofertas_esco_matching m
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND m.isco_code IS NOT NULL
    ),
    isco_counts AS (
        SELECT isco_code, MAX(isco_label) AS isco_label, COUNT(*) AS total_ofertas
        FROM ofertas_validadas
        GROUP BY isco_code
        HAVING COUNT(*) >= 5
        ORDER BY total_ofertas DESC
        LIMIT 20
    ),
    skills_por_isco AS (
        SELECT ov.isco_code, d.esco_skill_label AS skill_label
        FROM ofertas_validadas ov
        JOIN ofertas_esco_skills_detalle d ON ov.id_oferta = d.id_oferta
        WHERE ov.isco_code IN (SELECT isco_code FROM isco_counts)
          AND d.esco_skill_label IS NOT NULL
        GROUP BY ov.isco_code, d.esco_skill_label
    )
    SELECT ic.isco_code, ic.isco_label, ic.total_ofertas,
           si.skill_label
    FROM isco_counts ic
    LEFT JOIN skills_por_isco si ON ic.isco_code = si.isco_code
    ORDER BY ic.total_ofertas DESC, ic.isco_code
    """

    rows = conn.execute(query).fetchall()

    # Build skill sets per ISCO
    isco_info: Dict[str, Dict[str, Any]] = {}
    skills_by_isco: Dict[str, set] = {}

    for row in rows:
        code = row['isco_code']
        if code not in isco_info:
            isco_info[code] = {
                'isco_label': row['isco_label'],
                'total_ofertas': row['total_ofertas'],
            }
            skills_by_isco[code] = set()
        if row['skill_label']:
            skills_by_isco[code].add(row['skill_label'])

    now = datetime.now().isoformat()
    resultados = []

    # Nodos
    for code, info in isco_info.items():
        resultados.append({
            'tipo': 'nodo',
            'isco_code': code,
            'isco_label': info['isco_label'],
            'total_ofertas': info['total_ofertas'],
            'total_skills': len(skills_by_isco.get(code, set())),
            'source_isco': None,
            'target_isco': None,
            'jaccard': None,
            'shared_skills': None,
            'union_skills': None,
            'top_shared_labels': None,
            'calculado_en': now,
        })

    # Enlaces — Jaccard para todos los pares
    codes = list(isco_info.keys())
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            a, b = codes[i], codes[j]
            set_a = skills_by_isco.get(a, set())
            set_b = skills_by_isco.get(b, set())
            intersection = set_a & set_b
            union = set_a | set_b

            if not union:
                continue

            jac = len(intersection) / len(union)
            shared = len(intersection)

            if jac >= 0.10 and shared >= 3:
                top_shared = sorted(intersection)[:5]
                resultados.append({
                    'tipo': 'enlace',
                    'isco_code': None,
                    'isco_label': None,
                    'total_ofertas': None,
                    'total_skills': None,
                    'source_isco': a,
                    'target_isco': b,
                    'jaccard': round(jac, 4),
                    'shared_skills': shared,
                    'union_skills': len(union),
                    'top_shared_labels': json.dumps(top_shared, ensure_ascii=False),
                    'calculado_en': now,
                })

    n_nodos = sum(1 for r in resultados if r['tipo'] == 'nodo')
    n_enlaces = sum(1 for r in resultados if r['tipo'] == 'enlace')
    logger.info(f"Transición calculada: {n_nodos} nodos, {n_enlaces} enlaces")
    return resultados


def sync_transicion_skills(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza transición skills-ocupación a Supabase. Trunca y reinserta."""
    resultados = calcular_transicion_skills(conn)

    if not resultados:
        logger.warning("No hay datos de transición para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de transición")
        return len(resultados)

    try:
        client.table(TABLE_TRANSICION).delete().neq('tipo', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_TRANSICION}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_TRANSICION).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando transición batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Transición sincronizada: {total} filas")
    return total


# ============================================================
# VELOCIDAD DE COBERTURA (I-06)
# ============================================================

def calcular_velocidad_cobertura(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula velocidad de cobertura: mediana de días publicada por ISCO.
    Solo ofertas dadas de baja (estado_oferta='baja') con fecha conocida.
    """
    import statistics

    query = """
    SELECT m.isco_code, m.isco_label, o.dias_publicada
    FROM ofertas_esco_matching m
    JOIN ofertas o ON m.id_oferta = o.id_oferta
    WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
      AND m.isco_code IS NOT NULL
      AND o.estado_oferta = 'baja'
      AND o.dias_publicada IS NOT NULL
      AND o.dias_publicada > 0
    """

    rows = conn.execute(query).fetchall()

    # Agrupar días por ISCO
    dias_por_isco: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        code = row['isco_code']
        if code not in dias_por_isco:
            dias_por_isco[code] = {
                'isco_label': row['isco_label'],
                'dias': [],
            }
        dias_por_isco[code]['dias'].append(row['dias_publicada'])

    now = datetime.now().isoformat()
    resultados = []

    for code, info in dias_por_isco.items():
        dias = sorted(info['dias'])
        if len(dias) < 3:
            continue

        mediana = statistics.median(dias)
        q1 = statistics.median(dias[:len(dias) // 2]) if len(dias) >= 4 else dias[0]
        upper_half = dias[(len(dias) + 1) // 2:] if len(dias) >= 4 else dias[-1:]
        q3 = statistics.median(upper_half) if upper_half else mediana

        if mediana < 15:
            categoria = 'rapida'
        elif mediana > 45:
            categoria = 'lenta'
        else:
            categoria = 'normal'

        resultados.append({
            'isco_code': code,
            'isco_label': info['isco_label'],
            'total_ofertas': len(dias),
            'mediana_dias': round(float(mediana), 1),
            'q1_dias': round(float(q1), 1),
            'q3_dias': round(float(q3), 1),
            'min_dias': min(dias),
            'max_dias': max(dias),
            'categoria': categoria,
            'calculado_en': now,
        })

    cats = {}
    for r in resultados:
        cats[r['categoria']] = cats.get(r['categoria'], 0) + 1
    logger.info(f"Velocidad calculada: {len(resultados)} ocupaciones — {cats}")
    return resultados


def sync_velocidad_cobertura(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza velocidad de cobertura a Supabase. Trunca y reinserta."""
    resultados = calcular_velocidad_cobertura(conn)

    if not resultados:
        logger.warning("No hay datos de velocidad para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de velocidad")
        return len(resultados)

    try:
        client.table(TABLE_VELOCIDAD).delete().neq('isco_code', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_VELOCIDAD}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_VELOCIDAD).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando velocidad batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Velocidad sincronizada: {total} ocupaciones")
    return total


# ============================================================
# ÍNDICE DE TRABAJO REMOTO (I-10)
# ============================================================

def calcular_indice_remoto(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calcula índice de trabajo remoto: evolución mensual de modalidades.
    Global (clae_seccion=NULL) + por sector.
    """
    query = """
    WITH ofertas_validadas AS (
        SELECT m.id_oferta,
               strftime('%Y-%m', o.fecha_publicacion_iso) AS mes,
               n.modalidad,
               n.clae_seccion
        FROM ofertas_esco_matching m
        JOIN ofertas o ON m.id_oferta = o.id_oferta
        JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
          AND o.fecha_publicacion_iso IS NOT NULL
          AND n.modalidad IS NOT NULL
    ),
    global_data AS (
        SELECT mes,
               NULL AS clae_seccion,
               COUNT(*) AS total_ofertas,
               SUM(CASE WHEN modalidad = 'presencial' THEN 1 ELSE 0 END) AS presencial,
               SUM(CASE WHEN modalidad = 'remoto' THEN 1 ELSE 0 END) AS remoto,
               SUM(CASE WHEN modalidad = 'hibrido' THEN 1 ELSE 0 END) AS hibrido
        FROM ofertas_validadas
        GROUP BY mes
    ),
    sector_data AS (
        SELECT mes,
               clae_seccion,
               COUNT(*) AS total_ofertas,
               SUM(CASE WHEN modalidad = 'presencial' THEN 1 ELSE 0 END) AS presencial,
               SUM(CASE WHEN modalidad = 'remoto' THEN 1 ELSE 0 END) AS remoto,
               SUM(CASE WHEN modalidad = 'hibrido' THEN 1 ELSE 0 END) AS hibrido
        FROM ofertas_validadas
        WHERE clae_seccion IS NOT NULL
        GROUP BY mes, clae_seccion
        HAVING COUNT(*) >= 5
    )
    SELECT * FROM global_data
    UNION ALL
    SELECT * FROM sector_data
    ORDER BY mes, clae_seccion NULLS FIRST
    """

    rows = conn.execute(query).fetchall()

    now = datetime.now().isoformat()
    resultados = []

    for row in rows:
        total = row['total_ofertas']
        if total == 0:
            continue
        resultados.append({
            'mes': row['mes'],
            'clae_seccion': row['clae_seccion'],
            'total_ofertas': total,
            'presencial': row['presencial'],
            'remoto': row['remoto'],
            'hibrido': row['hibrido'],
            'pct_presencial': round(100.0 * row['presencial'] / total, 2),
            'pct_remoto': round(100.0 * row['remoto'] / total, 2),
            'pct_hibrido': round(100.0 * row['hibrido'] / total, 2),
            'calculado_en': now,
        })

    n_global = sum(1 for r in resultados if r['clae_seccion'] is None)
    n_sector = len(resultados) - n_global
    logger.info(f"Índice remoto calculado: {n_global} meses global, {n_sector} filas por sector")
    return resultados


def sync_indice_remoto(client, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """Sincroniza índice de trabajo remoto a Supabase. Trunca y reinserta."""
    resultados = calcular_indice_remoto(conn)

    if not resultados:
        logger.warning("No hay datos de índice remoto para sincronizar")
        return 0

    if dry_run:
        logger.info(f"[DRY-RUN] Sync {len(resultados)} filas de índice remoto")
        return len(resultados)

    try:
        client.table(TABLE_REMOTO).delete().neq('mes', '__none__').execute()
    except Exception as e:
        logger.warning(f"Error truncando {TABLE_REMOTO}: {e}")

    total = 0
    for i in range(0, len(resultados), BATCH_SIZE):
        batch = resultados[i:i + BATCH_SIZE]
        try:
            client.table(TABLE_REMOTO).insert(batch).execute()
            total += len(batch)
        except Exception as e:
            logger.error(f"Error insertando índice remoto batch {i // BATCH_SIZE + 1}: {e}")
            raise

    logger.info(f"Índice remoto sincronizado: {total} filas")
    return total


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
        WHERE estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
    """)
    row = cursor.fetchone()
    print(f"Ofertas validadas: {row['total']}")
    print(f"Primera validación: {row['primera']}")
    print(f"Última validación: {row['ultima']}")

    # Skills
    cursor = conn.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle d
        JOIN ofertas_esco_matching m ON d.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado', 'validado_claude_subfaseD', 'validado_claude_C1')
    """)
    print(f"Skills detalle: {cursor.fetchone()[0]}")

    print("="*60 + "\n")


# ============================================================
# SYNC LOG (incremental auto-detection)
# ============================================================

SYNC_LOG_PATH = PROJECT_ROOT / "config" / "supabase_sync_log.json"


def load_last_sync_timestamp() -> Optional[str]:
    """Lee last_sync_timestamp del log de sync previo."""
    if SYNC_LOG_PATH.exists():
        try:
            with open(SYNC_LOG_PATH, 'r') as f:
                data = json.load(f)
            return data.get("last_sync_timestamp")
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_sync_log(n_ofertas: int, n_skills: int):
    """Guarda timestamp del sync exitoso para auto-detección incremental."""
    now = datetime.now().isoformat()

    data = {}
    if SYNC_LOG_PATH.exists():
        try:
            with open(SYNC_LOG_PATH, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}

    # Agregar a history (mantener últimos 20)
    history = data.get("history", [])
    history.append({
        "timestamp": now,
        "ofertas": n_ofertas,
        "skills": n_skills
    })
    data["history"] = history[-20:]
    data["last_sync_timestamp"] = now
    data["last_sync_ofertas"] = n_ofertas
    data["last_sync_skills"] = n_skills

    with open(SYNC_LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Sync log guardado: {now}")


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

    # Auto-detección incremental: si no se pasa --full, --ids ni --since,
    # leer último timestamp de sync y usar como --since automático
    if not args.full and not args.ids and not args.since and not args.stats and not args.catalogs_only:
        last_sync = load_last_sync_timestamp()
        if last_sync:
            logger.info(f"Modo INCREMENTAL automático: solo cambios desde {last_sync}")
            args.since = last_sync
        else:
            logger.info("Sin sync previo registrado — ejecutando sync completo")

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

        n_ofertas = n_skills = n_ocup = n_esco = n_issues = 0

        if not ofertas:
            logger.warning("No hay ofertas nuevas para sincronizar (ofertas/skills sin cambios)")
        else:
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

        # Indicadores calculados — siempre se recalculan (usan TODAS las ofertas validadas)
        logger.info("Sincronizando estado del sistema...")
        sync_sistema_estado(client, conn, dry_run=args.dry_run)

        # Actualizar scraping_live_stats con datos locales (Indeed corre local, no VPS)
        logger.info("Actualizando scraping_live_stats desde BD local...")
        sync_scraping_live_stats(client, conn, dry_run=args.dry_run)

        logger.info("Calculando tensión de demanda...")
        n_tension = sync_tension_ocupaciones(client, conn, dry_run=args.dry_run)

        logger.info("Calculando concentración ocupacional...")
        n_concentracion = sync_concentracion_ocupacional(client, conn, dry_run=args.dry_run)

        logger.info("Calculando brecha de calificación...")
        n_brecha = sync_brecha_calificacion(client, conn, dry_run=args.dry_run)

        logger.info("Calculando digitalización por sector...")
        n_digitalizacion = sync_digitalizacion_sector(client, conn, dry_run=args.dry_run)

        logger.info("Calculando transición skills-ocupación...")
        n_transicion = sync_transicion_skills(client, conn, dry_run=args.dry_run)

        logger.info("Calculando velocidad de cobertura...")
        n_velocidad = sync_velocidad_cobertura(client, conn, dry_run=args.dry_run)

        logger.info("Calculando índice de trabajo remoto...")
        n_remoto = sync_indice_remoto(client, conn, dry_run=args.dry_run)

        # Resumen
        print("\n" + "="*60)
        print("RESUMEN" + (" [DRY-RUN]" if args.dry_run else ""))
        print("="*60)
        print(f"Ofertas sincronizadas:    {n_ofertas}")
        print(f"Skills detalle:           {n_skills}")
        print(f"Ocupaciones ESCO:         {n_ocup}")
        print(f"Skills ESCO:              {n_esco}")
        print(f"Issues sincronizados:     {n_issues}")
        print(f"Tensión ocupaciones:      {n_tension}")
        print(f"Concentración ocupacional: {n_concentracion}")
        print(f"Brecha calificación:      {n_brecha}")
        print(f"Digitalización sector:    {n_digitalizacion}")
        print(f"Transición skills:        {n_transicion}")
        print(f"Velocidad cobertura:      {n_velocidad}")
        print(f"Índice remoto:            {n_remoto}")
        print("="*60)

        if not args.dry_run:
            # Guardar timestamp para próximo sync incremental
            save_sync_log(n_ofertas, n_skills)
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

            # PCA-3c: Recalcular emergentes después del sync
            logger.info("\n" + "="*60)
            logger.info("RECALCULANDO EMERGENTES (Bloque 9°)")
            logger.info("="*60)
            try:
                emergentes_result = client.rpc('recalcular_emergentes').execute()
                if emergentes_result.data:
                    r = emergentes_result.data
                    logger.info(f"  Nuevas/actualizadas: {r.get('nuevas_o_actualizadas', 0)}")
                    logger.info(f"  Total pendientes: {r.get('total_pendientes', 0)}")
                    logger.info(f"  Aprobadas: {r.get('total_aprobadas', 0)}")
                    logger.info(f"  Rechazadas: {r.get('total_rechazadas', 0)}")
            except Exception as e:
                logger.warning(f"Error recalculando emergentes (no bloquea): {e}")

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
