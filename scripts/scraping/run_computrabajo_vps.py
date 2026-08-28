#!/usr/bin/env python3
"""
ComputRabajo Scraping para VPS
==============================

Scrapea ComputRabajo via keyword strategy y guarda en la misma BD SQLite.
Diseñado para correr en el VPS junto con los scrapers de Bumeran y ZonaJobs.

Campos de ComputRabajo mapeados a la tabla ofertas:
  - id_oferta: data-id del HTML (convertido a integer, o hash si es alfanumérico)
  - titulo, empresa, descripcion, ubicacion → localizacion
  - modalidad → modalidad_trabajo
  - fecha_publicacion → fecha_publicacion_iso
  - url_completa → url_oferta
  - portal = 'computrabajo'

Uso:
    python3 scripts/scraping/run_computrabajo_vps.py
    python3 scripts/scraping/run_computrabajo_vps.py --estrategia exhaustiva
    python3 scripts/scraping/run_computrabajo_vps.py --no-description  # rápido, sin descripción
    python3 scripts/scraping/run_computrabajo_vps.py --max-paginas 3   # limitar páginas por keyword
"""

import sqlite3
import json
import sys
import time
import logging
import argparse
import zlib
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "computrabajo" / "scrapers"))
sys.path.insert(0, str(BASE_DIR))

from computrabajo_scraper import ComputRabajoScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keywords master path
MASTER_KEYWORDS_PATH = BASE_DIR / "config" / "scraping" / "master_keywords.json"

# Prefix for ComputRabajo hashed IDs (to avoid collisions with Bumeran/ZonaJobs)
# Bumeran: ~1,100,000,000 range
# ZonaJobs: ~2,100,000 range
# ComputRabajo hashed: 5,000,000,000+ range
CT_ID_PREFIX = 5_000_000_000


def computrabajo_id_to_int(data_id=None, url_oferta=None) -> int:
    """
    Genera un ID entero estable para una oferta de ComputRabajo.

    IMPORTANTE: El data-id del HTML cambia según el keyword de búsqueda
    para la MISMA oferta (bug confirmado 2026-03-11). Por eso usamos el
    slug de la URL que es estable:
      /ofertas-de-trabajo/oferta-de-trabajo-de-TITULO-en-UBICACION-HASH

    Prioridad:
      1. URL slug (sin hash final de 32 chars) → CRC32 estable
      2. data-id como fallback (si no hay URL)

    Args:
        data_id: El data-id del artículo HTML (fallback)
        url_oferta: URL completa o relativa de la oferta (preferida)

    Returns:
        Integer ID para la tabla ofertas
    """
    import re

    # Prioridad 1: URL slug (estable entre keywords)
    if url_oferta:
        # Quitar fragment (#lc=ListOffers-...)
        url_clean = url_oferta.split('#')[0]
        # Quitar query params
        url_clean = url_clean.split('?')[0]
        # Extraer el path relativo
        if '/ofertas-de-trabajo/' in url_clean:
            slug = url_clean.split('/ofertas-de-trabajo/')[-1]
        else:
            slug = url_clean

        # Quitar hash de 32 chars hexadecimales del final del slug
        # Patrón: -HASH32 al final (ej: -9F9578B2F3C3A91D61373E686DCF3405)
        slug_clean = re.sub(r'-[A-Fa-f0-9]{32}$', '', slug)

        if slug_clean:
            crc = zlib.crc32(slug_clean.encode('utf-8')) & 0xFFFFFFFF
            return CT_ID_PREFIX + crc

    # Fallback: data-id (inestable entre keywords, pero mejor que nada)
    if data_id is not None:
        data_id_str = str(data_id).strip()
        try:
            int_id = int(data_id_str)
            if int_id < 100_000_000:
                return CT_ID_PREFIX + int_id
            return int_id
        except ValueError:
            pass
        crc = zlib.crc32(data_id_str.encode('utf-8')) & 0xFFFFFFFF
        return CT_ID_PREFIX + crc

    return None


def mapear_oferta_para_bd(oferta_raw: dict) -> dict:
    """
    Mapea los campos de ComputRabajo al schema de la tabla ofertas.

    ComputRabajo tiene campos diferentes a Bumeran/ZonaJobs (plataforma Navent).
    Los campos que no existen en ComputRabajo se dejan como NULL.
    """
    id_int = computrabajo_id_to_int(
        data_id=oferta_raw.get('id_oferta'),
        url_oferta=oferta_raw.get('url_completa') or oferta_raw.get('url_relativa')
    )

    if id_int is None:
        return None

    # Parsear fecha ISO
    fecha_iso = None
    fecha_pub = oferta_raw.get('fecha_publicacion')
    if fecha_pub:
        try:
            # El scraper ya devuelve ISO, extraer solo la fecha
            fecha_iso = fecha_pub[:10]  # YYYY-MM-DD
        except Exception:
            pass

    return {
        # IDs
        'id_oferta': id_int,
        'id_empresa': None,  # ComputRabajo no tiene id_empresa numérico

        # Info básica
        'titulo': oferta_raw.get('titulo'),
        'empresa': oferta_raw.get('empresa'),
        'descripcion': oferta_raw.get('descripcion'),
        'confidencial': None,

        # Ubicación y modalidad
        'localizacion': oferta_raw.get('ubicacion'),
        'modalidad_trabajo': oferta_raw.get('modalidad'),
        'tipo_trabajo': None,

        # Fechas
        'fecha_publicacion_original': oferta_raw.get('fecha_publicacion_raw'),
        'fecha_hora_publicacion_original': None,
        'fecha_modificado_original': None,
        'fecha_publicacion_iso': fecha_iso,
        'fecha_hora_publicacion_iso': fecha_pub,
        'fecha_modificado_iso': None,
        'fecha_publicacion_datetime': None,
        'fecha_hora_publicacion_datetime': None,
        'fecha_modificado_datetime': None,

        # Detalles
        'cantidad_vacantes': None,
        'apto_discapacitado': None,

        # Categorización
        'id_area': None,
        'id_subarea': None,
        'id_pais': None,  # TODO: podría ser 11 (Argentina)

        # Empresa
        'logo_url': None,
        'empresa_validada': None,
        'empresa_pro': None,
        'promedio_empresa': oferta_raw.get('empresa_rating'),

        # Plan de publicación
        'plan_publicacion_id': None,
        'plan_publicacion_nombre': None,

        # Otros
        'portal': 'computrabajo',
        'tipo_aviso': None,
        'tiene_preguntas': None,
        'salario_obligatorio': None,
        'alta_revision_perfiles': None,
        'guardado': None,
        'gptw_url': None,

        # Metadata
        'url_oferta': oferta_raw.get('url_completa'),
        'scrapeado_en': oferta_raw.get('scrapeado_en', datetime.now().isoformat()),
    }


# Columnas para INSERT (debe coincidir con schema de la tabla ofertas)
COLUMNAS = [
    'id_oferta', 'id_empresa', 'titulo', 'empresa', 'descripcion',
    'confidencial', 'localizacion', 'modalidad_trabajo', 'tipo_trabajo',
    'fecha_publicacion_original', 'fecha_hora_publicacion_original',
    'fecha_modificado_original', 'fecha_publicacion_iso',
    'fecha_hora_publicacion_iso', 'fecha_modificado_iso',
    'fecha_publicacion_datetime', 'fecha_hora_publicacion_datetime',
    'fecha_modificado_datetime', 'cantidad_vacantes', 'apto_discapacitado',
    'id_area', 'id_subarea', 'id_pais', 'logo_url', 'empresa_validada',
    'empresa_pro', 'promedio_empresa', 'plan_publicacion_id',
    'plan_publicacion_nombre', 'portal', 'tipo_aviso', 'tiene_preguntas',
    'salario_obligatorio', 'alta_revision_perfiles', 'guardado', 'gptw_url',
    'url_oferta', 'scrapeado_en'
]


def insertar_en_bd(ofertas_mapeadas: list, db_path: str) -> dict:
    """
    Inserta ofertas mapeadas en la BD SQLite (INSERT OR IGNORE).

    Returns:
        Dict con estadísticas: insertadas, duplicadas, errores
    """
    conn = sqlite3.connect(db_path, timeout=30)
    cur = conn.cursor()

    cols_str = ', '.join(COLUMNAS)
    placeholders = ', '.join(['?'] * len(COLUMNAS))
    sql = f"INSERT OR IGNORE INTO ofertas ({cols_str}) VALUES ({placeholders})"

    insertadas = 0
    duplicadas = 0
    errores = 0

    for oferta in ofertas_mapeadas:
        if oferta is None:
            errores += 1
            continue
        try:
            valores = tuple(oferta.get(col) for col in COLUMNAS)
            cur.execute(sql, valores)
            if cur.rowcount > 0:
                insertadas += 1
            else:
                duplicadas += 1
        except Exception as e:
            errores += 1
            if errores <= 5:
                logger.warning(f"Error insertando oferta {oferta.get('id_oferta')}: {e}")

    conn.commit()

    # Estadísticas
    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'computrabajo'")
    total_ct = cur.fetchone()[0]

    conn.close()

    return {
        'insertadas': insertadas,
        'duplicadas': duplicadas,
        'errores': errores,
        'total_bd': total,
        'total_computrabajo': total_ct
    }


def cargar_keywords(estrategia: str = "exhaustiva") -> list:
    """
    Carga keywords del diccionario maestro.

    ComputRabajo usa formato URL: 'trabajo-de-{keyword}'
    Los keywords del maestro ya están en formato compatible (con guiones).
    """
    if not MASTER_KEYWORDS_PATH.exists():
        logger.error(f"No se encontró diccionario maestro: {MASTER_KEYWORDS_PATH}")
        sys.exit(1)

    with open(MASTER_KEYWORDS_PATH, 'r', encoding='utf-8') as f:
        master = json.load(f)

    if estrategia not in master['estrategias']:
        disponibles = list(master['estrategias'].keys())
        logger.error(f"Estrategia '{estrategia}' no encontrada. Disponibles: {disponibles}")
        sys.exit(1)

    keywords = master['estrategias'][estrategia]['keywords']

    # Filtrar keywords vacíos
    keywords = [k for k in keywords if k.strip()]

    logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}'")
    return keywords


def _extraer_slug(oferta):
    """Extrae slug estable de la URL para deduplicación."""
    import re
    url = oferta.get('url_completa') or oferta.get('url_relativa') or ''
    url_clean = url.split('#')[0].split('?')[0]
    if '/ofertas-de-trabajo/' in url_clean:
        slug = url_clean.split('/ofertas-de-trabajo/')[-1]
    else:
        slug = url_clean
    # Quitar hash 32 chars del final
    return re.sub(r'-[A-Fa-f0-9]{32}$', '', slug)


# Reintentos de descripción antes de dar una oferta por perdida (2026-08-28).
# Las que fallan lo hacen de forma determinista (aviso caído o template no
# cubierto): reintentarlas indefinidamente sólo consume la ventana del PASO 2.
MAX_INTENTOS_DESCRIPCION = 3


def _asegurar_columnas_descripcion(cur):
    """Agrega descripcion_intentos / descripcion_estado si faltan (idempotente)."""
    cols = {row[1] for row in cur.execute("PRAGMA table_info(ofertas)")}
    if 'descripcion_intentos' not in cols:
        cur.execute("ALTER TABLE ofertas ADD COLUMN descripcion_intentos INTEGER DEFAULT 0")
        logger.info("  [migracion] columna descripcion_intentos agregada")
    if 'descripcion_estado' not in cols:
        cur.execute("ALTER TABLE ofertas ADD COLUMN descripcion_estado TEXT")
        logger.info("  [migracion] columna descripcion_estado agregada")


def _registrar_intento_fallido(conn, id_oferta) -> int:
    """Suma un intento fallido.

    Devuelve 1 sólo en la TRANSICIÓN a 'agotado' (para que el contador de la
    corrida no infle si una oferta ya agotada vuelve a intentarse, cosa que puede
    pasar si reaparece en el listado por republicación).
    """
    previo = conn.execute(
        "SELECT COALESCE(descripcion_estado, '') FROM ofertas WHERE id_oferta = ?",
        (id_oferta,)).fetchone()
    ya_agotada = bool(previo) and previo[0] == 'agotado'

    conn.execute(
        "UPDATE ofertas SET descripcion_intentos = COALESCE(descripcion_intentos, 0) + 1 "
        "WHERE id_oferta = ?", (id_oferta,))
    fila = conn.execute(
        "SELECT COALESCE(descripcion_intentos, 0) FROM ofertas WHERE id_oferta = ?",
        (id_oferta,)).fetchone()
    if fila and fila[0] >= MAX_INTENTOS_DESCRIPCION:
        conn.execute(
            "UPDATE ofertas SET descripcion_estado = 'agotado' "
            "WHERE id_oferta = ? AND (descripcion IS NULL OR descripcion = '')",
            (id_oferta,))
        return 0 if ya_agotada else 1
    return 0


def scrapear_con_keywords(
    scraper: ComputRabajoScraper,
    keywords: list,
    max_paginas: int = 5,
    fetch_description: bool = True,
    delay_keywords: float = 3.0,
    db_path: str = None,
    max_descripciones: int = 1500
) -> dict:
    """
    Scrapea ComputRabajo en DOS PASADAS:

    PASO 1: Recorrer todos los keywords, scrapear listados (sin descripción).
            Deduplicar por URL slug. Insertar en BD inmediatamente.
            Rápido: ~2-3 horas para 1072 keywords.

    PASO 2: Para las ofertas nuevas insertadas, bajar descripción individual.
            Solo las que no tienen descripción aún, ACOTADO por
            max_descripciones y priorizando lo más reciente.

    Args:
        scraper: Instancia de ComputRabajoScraper
        keywords: Lista de keywords
        max_paginas: Páginas por keyword
        fetch_description: Si True, ejecuta Paso 2 (descripciones)
        delay_keywords: Delay entre keywords (segundos)
        db_path: Ruta a la BD SQLite
        max_descripciones: Tope de fetchs de detalle por corrida (2026-08-28).
            Sin tope, drenar el backlog acumulado (~14K tras la limpieza del
            boilerplate) tomaría ~9,3 h a 2,5 s por oferta, encima de las ~3,5 h
            del scraping — desbordaría la ventana y chocaría con el cron
            siguiente. Con el tope el backlog se drena en lotes por corrida,
            atendiendo primero lo más reciente (ORDER BY scrapeado_en DESC).

    Returns:
        Dict con estadísticas globales
    """
    stats_global = {
        'keywords_total': len(keywords),
        'keywords_procesadas': 0,
        'keywords_exitosas': 0,
        'keywords_sin_resultados': 0,
        'keywords_error': 0,
        'ofertas_scrapeadas': 0,
        'ofertas_con_descripcion': 0,
        'insertadas_total': 0,
        'duplicadas_total': 0,
        'errores_total': 0,
    }

    slugs_vistos = set()  # Deduplicar entre keywords usando URL slug (estable)
    # URLs de ofertas nuevas para Paso 2 (id_oferta → url)
    ofertas_para_descripcion = {}

    # ==================================================================
    # PASO 1: Listar todas las keywords (sin descripciones)
    # ==================================================================
    logger.info("")
    logger.info("=" * 70)
    logger.info("PASO 1/2: Listado rápido de todas las keywords")
    logger.info("=" * 70)
    paso1_start = time.time()

    for i, keyword in enumerate(keywords, 1):
        logger.info(f"[{i}/{len(keywords)}] Keyword: '{keyword}'")

        try:
            # Scrapear listado (sin descripciones)
            ofertas_raw = scraper.scrapear_todo(
                max_paginas=max_paginas,
                query=keyword,
                fetch_description=False
            )

            if not ofertas_raw:
                stats_global['keywords_sin_resultados'] += 1
                stats_global['keywords_procesadas'] += 1
                continue

            # Deduplicar contra ofertas ya vistas en este run (por URL slug)
            ofertas_nuevas = []
            for oferta in ofertas_raw:
                slug = _extraer_slug(oferta)
                if slug and slug not in slugs_vistos:
                    slugs_vistos.add(slug)
                    ofertas_nuevas.append(oferta)

            logger.info(f"  {len(ofertas_raw)} encontradas, {len(ofertas_nuevas)} nuevas en este run")

            # Mapear e insertar en BD (sin descripción todavía)
            ofertas_mapeadas = [mapear_oferta_para_bd(o) for o in ofertas_nuevas]
            ofertas_mapeadas = [o for o in ofertas_mapeadas if o is not None]

            if ofertas_mapeadas and db_path:
                bd_stats = insertar_en_bd(ofertas_mapeadas, db_path)
                stats_global['insertadas_total'] += bd_stats['insertadas']
                stats_global['duplicadas_total'] += bd_stats['duplicadas']
                stats_global['errores_total'] += bd_stats['errores']
                logger.info(f"  BD: +{bd_stats['insertadas']} insertadas, {bd_stats['duplicadas']} dup")

                # Guardar URLs de las realmente insertadas para Paso 2
                if fetch_description and bd_stats['insertadas'] > 0:
                    for oferta in ofertas_nuevas:
                        url = oferta.get('url_completa')
                        if url:
                            id_int = computrabajo_id_to_int(
                                data_id=oferta.get('id_oferta'),
                                url_oferta=url
                            )
                            if id_int:
                                ofertas_para_descripcion[id_int] = url

            stats_global['ofertas_scrapeadas'] += len(ofertas_nuevas)
            stats_global['keywords_exitosas'] += 1

        except Exception as e:
            logger.error(f"  ERROR en keyword '{keyword}': {e}")
            stats_global['keywords_error'] += 1

        stats_global['keywords_procesadas'] += 1

        # Delay entre keywords (excepto la última)
        if i < len(keywords):
            time.sleep(delay_keywords)

    paso1_elapsed = time.time() - paso1_start
    logger.info("")
    logger.info(f"PASO 1 COMPLETADO en {paso1_elapsed:.0f}s ({paso1_elapsed/60:.1f} min)")
    logger.info(f"  Keywords: {stats_global['keywords_procesadas']}/{stats_global['keywords_total']}")
    logger.info(f"  Ofertas nuevas scrapeadas: {stats_global['ofertas_scrapeadas']}")
    logger.info(f"  Insertadas en BD: {stats_global['insertadas_total']}")
    logger.info(f"  Ofertas pendientes descripción: {len(ofertas_para_descripcion)}")

    # ==================================================================
    # PASO 2: Bajar descripciones de las ofertas nuevas
    # ==================================================================
    if fetch_description and ofertas_para_descripcion:
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"PASO 2/2: Descripciones de {len(ofertas_para_descripcion)} ofertas nuevas")
        logger.info("=" * 70)
        paso2_start = time.time()

        # También buscar ofertas sin descripción de corridas anteriores.
        # Acotado (2026-08-28): se prioriza lo más reciente y se excluyen las
        # 'agotadas' — las que ya fallaron MAX_INTENTOS_DESCRIPCION veces. Antes
        # esta query traía TODO el pendiente sin límite y reintentaba en cada
        # corrida el mismo conjunto que falla de forma determinista (los fallos
        # por boilerplate crecían 56→148→217→278→337→432 corrida a corrida).
        if db_path:
            try:
                conn = sqlite3.connect(db_path, timeout=30)
                cur = conn.cursor()
                _asegurar_columnas_descripcion(cur)
                conn.commit()
                cupo = max(0, max_descripciones - len(ofertas_para_descripcion))
                if cupo:
                    cur.execute("""
                        SELECT id_oferta, url_oferta FROM ofertas
                        WHERE portal = 'computrabajo'
                          AND (descripcion IS NULL OR descripcion = '')
                          AND url_oferta IS NOT NULL
                          AND COALESCE(descripcion_estado, '') != 'agotado'
                        ORDER BY scrapeado_en DESC
                        LIMIT ?
                    """, (cupo,))
                    for row in cur.fetchall():
                        if row[0] not in ofertas_para_descripcion:
                            ofertas_para_descripcion[row[0]] = row[1]
                # Cuánto queda afuera, para que el tope no oculte el backlog
                cur.execute("""
                    SELECT COUNT(*) FROM ofertas
                    WHERE portal = 'computrabajo'
                      AND (descripcion IS NULL OR descripcion = '')
                      AND url_oferta IS NOT NULL
                      AND COALESCE(descripcion_estado, '') != 'agotado'
                """)
                pendientes_totales = cur.fetchone()[0]
                cur.execute("""
                    SELECT COUNT(*) FROM ofertas
                    WHERE portal = 'computrabajo' AND descripcion_estado = 'agotado'
                """)
                agotadas = cur.fetchone()[0]
                conn.close()
                logger.info(f"  Se intentarán en esta corrida: {len(ofertas_para_descripcion)} (tope {max_descripciones})")
                logger.info(f"  Backlog pendiente total: {pendientes_totales} | agotadas (excluidas): {agotadas}")
                if pendientes_totales > len(ofertas_para_descripcion):
                    logger.info(f"  Quedan {pendientes_totales - len(ofertas_para_descripcion)} para próximas corridas")
            except Exception as e:
                logger.warning(f"  No se pudo consultar BD para pendientes: {e}")

        desc_count = 0
        desc_errors = 0
        conn = sqlite3.connect(db_path, timeout=30) if db_path else None

        desc_agotadas = 0
        for j, (id_oferta, url) in enumerate(ofertas_para_descripcion.items(), 1):
            try:
                datos_extra = scraper.scrapear_oferta_individual(url)
                if datos_extra and datos_extra.get('descripcion'):
                    if conn:
                        conn.execute(
                            "UPDATE ofertas SET descripcion = ? WHERE id_oferta = ?",
                            (datos_extra['descripcion'], id_oferta)
                        )
                        if j % 50 == 0:
                            conn.commit()
                    desc_count += 1
                elif conn:
                    # Fallo sin excepción (aviso caído, template no cubierto,
                    # meta boilerplate). Se cuenta el intento; al llegar al tope
                    # sale de la cola automática para no reintentarla por siempre.
                    desc_agotadas += _registrar_intento_fallido(conn, id_oferta)
                time.sleep(scraper.delay)
            except Exception as e:
                desc_errors += 1
                if conn:
                    try:
                        desc_agotadas += _registrar_intento_fallido(conn, id_oferta)
                    except Exception:
                        pass
                if desc_errors <= 5:
                    logger.warning(f"  Error descripción {id_oferta}: {e}")

            # Log progreso cada 50 ofertas
            if j % 50 == 0:
                logger.info(f"  Descripciones: {j}/{len(ofertas_para_descripcion)} ({desc_count} OK, {desc_errors} err)")

        if conn:
            conn.commit()
            conn.close()

        stats_global['ofertas_con_descripcion'] = desc_count
        stats_global['descripciones_agotadas'] = desc_agotadas
        paso2_elapsed = time.time() - paso2_start
        logger.info(f"PASO 2 COMPLETADO en {paso2_elapsed:.0f}s ({paso2_elapsed/60:.1f} min)")
        logger.info(f"  Descripciones obtenidas: {desc_count}/{len(ofertas_para_descripcion)}")
        logger.info(f"  Errores: {desc_errors}")
        logger.info(f"  Marcadas 'agotado' ({MAX_INTENTOS_DESCRIPCION} intentos sin éxito): {desc_agotadas}")

    elif fetch_description:
        logger.info("")
        logger.info("PASO 2 OMITIDO: No hay ofertas nuevas que necesiten descripción")

    return stats_global


def main():
    parser = argparse.ArgumentParser(description="ComputRabajo scraping para VPS")
    parser.add_argument('--estrategia', default='exhaustiva',
                       help='Estrategia de keywords del diccionario maestro (default: exhaustiva)')
    parser.add_argument('--max-paginas', type=int, default=5,
                       help='Páginas por keyword (default: 5, ~100 ofertas/keyword)')
    parser.add_argument('--no-description', action='store_true',
                       help='No obtener descripción individual (modo rápido)')
    parser.add_argument('--max-descripciones', type=int, default=1500,
                       help='Tope de descripciones a bajar por corrida (default: 1500, '
                            '~1h a 2.5s c/u). Prioriza lo más reciente; el resto del '
                            'backlog queda para las corridas siguientes')
    parser.add_argument('--delay-requests', type=float, default=2.0,
                       help='Delay entre requests HTTP (default: 2.0s)')
    parser.add_argument('--delay-keywords', type=float, default=3.0,
                       help='Delay entre keywords (default: 3.0s)')
    parser.add_argument('--db', type=str,
                       default=str(BASE_DIR / 'database' / 'bumeran_scraping.db'),
                       help='Ruta a la BD SQLite')
    parser.add_argument('--dry-run', action='store_true',
                       help='Solo scrapear, no insertar en BD')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("COMPUTRABAJO SCRAPING - VPS")
    logger.info("=" * 70)
    logger.info(f"Estrategia: {args.estrategia}")
    logger.info(f"Max páginas/keyword: {args.max_paginas}")
    logger.info(f"Descripción: {'NO (modo rápido)' if args.no_description else 'SÍ (modo completo)'}")
    logger.info(f"Delay requests: {args.delay_requests}s")
    logger.info(f"Delay keywords: {args.delay_keywords}s")
    logger.info(f"BD: {args.db}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("")

    start = time.time()

    # Paso 1: Cargar keywords
    keywords = cargar_keywords(args.estrategia)

    # Paso 2: Crear scraper
    scraper = ComputRabajoScraper(delay_between_requests=args.delay_requests)

    # Paso 3: Scrapear e insertar
    stats = scrapear_con_keywords(
        scraper=scraper,
        keywords=keywords,
        max_paginas=args.max_paginas,
        fetch_description=not args.no_description,
        delay_keywords=args.delay_keywords,
        db_path=None if args.dry_run else args.db,
        max_descripciones=args.max_descripciones
    )

    elapsed = time.time() - start

    # Estadísticas finales de BD
    if not args.dry_run:
        try:
            conn = sqlite3.connect(args.db, timeout=30)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM ofertas")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'computrabajo'")
            total_ct = cur.fetchone()[0]
            conn.close()
            stats['total_bd'] = total
            stats['total_computrabajo'] = total_ct
        except Exception:
            pass

    logger.info("")
    logger.info("=" * 70)
    logger.info("RESULTADO FINAL - COMPUTRABAJO")
    logger.info("=" * 70)
    logger.info(f"  Keywords procesadas: {stats['keywords_procesadas']}/{stats['keywords_total']}")
    logger.info(f"  Keywords exitosas: {stats['keywords_exitosas']}")
    logger.info(f"  Keywords sin resultados: {stats['keywords_sin_resultados']}")
    logger.info(f"  Keywords con error: {stats['keywords_error']}")
    logger.info(f"  ---")
    logger.info(f"  Ofertas scrapeadas: {stats['ofertas_scrapeadas']}")
    logger.info(f"  Ofertas con descripción: {stats['ofertas_con_descripcion']}")
    if not args.dry_run:
        logger.info(f"  Insertadas en BD: {stats['insertadas_total']}")
        logger.info(f"  Duplicadas: {stats['duplicadas_total']}")
        logger.info(f"  Errores inserción: {stats['errores_total']}")
        if 'total_bd' in stats:
            logger.info(f"  Total en BD: {stats['total_bd']} ({stats.get('total_computrabajo', '?')} ComputRabajo)")
    logger.info(f"  Tiempo: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
