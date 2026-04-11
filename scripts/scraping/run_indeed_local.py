#!/usr/bin/env python3
"""
Indeed Argentina - Scraping LOCAL con keyword cycling
=====================================================

Corre Indeed desde la máquina local (no VPS) porque la IP del VPS
está bloqueada por Cloudflare desde 2026-03-21.

Diferencias con run_indeed_vps.py:
  - Keyword cycling: solo procesa 1/4 de las keywords por semana
  - Delays más altos (4s listado, 4s detalle) para proteger IP residencial
  - Guarda en la BD local directamente

Uso:
    python3 scripts/scraping/run_indeed_local.py
    python3 scripts/scraping/run_indeed_local.py --chunks 4        # ciclo de 4 semanas
    python3 scripts/scraping/run_indeed_local.py --force-chunk 0   # forzar chunk específico
    python3 scripts/scraping/run_indeed_local.py --all-keywords    # sin cycling (cuidado!)
    python3 scripts/scraping/run_indeed_local.py --dry-run
"""

import sqlite3
import json
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "indeed" / "scrapers"))
sys.path.insert(0, str(BASE_DIR / "config" / "scraping"))

from indeed_scraper import IndeedScraper
from keyword_cycling import load_keywords_with_cycling, get_cycling_info

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INDEED_ID_PREFIX = 8_000_000_000


def jk_to_int(job_key: str) -> int:
    """Convierte job_key hex a entero estable."""
    try:
        raw_int = int(job_key, 16)
        return INDEED_ID_PREFIX + (raw_int % 1_000_000_000)
    except (ValueError, TypeError):
        import hashlib
        h = int(hashlib.md5(job_key.encode()).hexdigest()[:8], 16)
        return INDEED_ID_PREFIX + h


def _map_employment_type(types: list) -> str:
    if not types:
        return None
    type_map = {
        'FULL_TIME': 'full-time', 'PART_TIME': 'part-time',
        'CONTRACT': 'contrato', 'TEMPORARY': 'temporal',
        'INTERN': 'pasantia', 'VOLUNTEER': 'voluntario', 'OTHER': None,
    }
    for t in types:
        mapped = type_map.get(t)
        if mapped:
            return mapped
    return types[0] if types else None


def _build_descripcion(oferta: dict) -> str:
    parts = []
    desc = oferta.get('descripcion')
    if desc:
        parts.append(desc)

    metadata = []
    sal_min = oferta.get('salario_min')
    sal_max = oferta.get('salario_max')
    sal_moneda = oferta.get('salario_moneda', '')
    if sal_min or sal_max:
        sal_str = f"Salario: {sal_moneda} "
        if sal_min and sal_max:
            sal_str += f"{sal_min} - {sal_max}"
        elif sal_min:
            sal_str += f"{sal_min}+"
        else:
            sal_str += f"hasta {sal_max}"
        periodo = oferta.get('salario_periodo', '')
        if periodo:
            sal_str += f" ({periodo})"
        metadata.append(sal_str)

    tipos = oferta.get('tipo_empleo', [])
    if tipos:
        metadata.append(f"Tipo: {', '.join(tipos)}")

    if metadata:
        parts.append("\n---\n" + "\n".join(metadata))

    return "\n".join(parts) if parts else None


def _build_modalidad(oferta: dict) -> str:
    ubicacion = oferta.get('ubicacion', '') or ''
    if 'remoto' in ubicacion.lower() or 'remote' in ubicacion.lower():
        return 'remoto'
    if 'híbrido' in ubicacion.lower() or 'hybrid' in ubicacion.lower():
        return 'híbrido'
    return None


def mapear_oferta_para_bd(oferta: dict) -> dict:
    id_int = jk_to_int(oferta['job_key'])
    ubicacion = oferta.get('ubicacion', '')

    fecha_iso = None
    fecha_pub = oferta.get('fecha_publicacion')
    if fecha_pub:
        try:
            dt = datetime.fromisoformat(fecha_pub.replace('Z', '+00:00'))
            fecha_iso = dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            fecha_iso = fecha_pub[:10] if len(str(fecha_pub)) >= 10 else None

    return {
        'id_oferta': id_int,
        'id_empresa': None,
        'titulo': oferta.get('titulo'),
        'empresa': oferta.get('empresa_jsonld') or oferta.get('empresa'),
        'descripcion': _build_descripcion(oferta),
        'confidencial': None,
        'localizacion': ubicacion,
        'modalidad_trabajo': _build_modalidad(oferta),
        'tipo_trabajo': _map_employment_type(oferta.get('tipo_empleo')),
        'fecha_publicacion_original': oferta.get('fecha_publicacion'),
        'fecha_hora_publicacion_original': None,
        'fecha_modificado_original': None,
        'fecha_publicacion_iso': fecha_iso,
        'fecha_hora_publicacion_iso': None,
        'fecha_modificado_iso': None,
        'fecha_publicacion_datetime': None,
        'fecha_hora_publicacion_datetime': None,
        'fecha_modificado_datetime': None,
        'cantidad_vacantes': None,
        'apto_discapacitado': None,
        'id_area': None,
        'id_subarea': None,
        'id_pais': None,
        'logo_url': None,
        'empresa_validada': None,
        'empresa_pro': None,
        'promedio_empresa': None,
        'plan_publicacion_id': None,
        'plan_publicacion_nombre': None,
        'portal': 'indeed',
        'tipo_aviso': None,
        'tiene_preguntas': None,
        'salario_obligatorio': None,
        'alta_revision_perfiles': None,
        'guardado': None,
        'gptw_url': None,
        'url_oferta': oferta.get('url'),
        'scrapeado_en': oferta.get('scrapeado_en', datetime.now().isoformat()),
    }


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

    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'indeed'")
    total_indeed = cur.fetchone()[0]

    conn.close()

    return {
        'insertadas': insertadas,
        'duplicadas': duplicadas,
        'errores': errores,
        'total_bd': total,
        'total_indeed': total_indeed,
    }


def main():
    parser = argparse.ArgumentParser(description='Indeed Argentina Scraper (LOCAL + cycling)')
    parser.add_argument('--db', type=str, default=None,
                        help='Ruta a la BD SQLite')
    parser.add_argument('--estrategia', type=str, default='exhaustiva',
                        help='Estrategia de keywords (default: exhaustiva)')
    parser.add_argument('--chunks', type=int, default=4,
                        help='Cantidad de chunks para cycling (default: 4 = ciclo mensual)')
    parser.add_argument('--force-chunk', type=int, default=None,
                        help='Forzar chunk específico (0-based)')
    parser.add_argument('--all-keywords', action='store_true',
                        help='Usar TODAS las keywords sin cycling (cuidado con bloqueos)')
    parser.add_argument('--fromage', type=int, default=14,
                        help='Dias de antiguedad maxima (default: 14)')
    parser.add_argument('--delay', type=float, default=4.0,
                        help='Delay entre requests de listado (default: 4.0)')
    parser.add_argument('--detail-delay', type=float, default=4.0,
                        help='Delay entre requests de detalle (default: 4.0)')
    parser.add_argument('--no-details', action='store_true',
                        help='Solo listado, sin fetch de detalles')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo scrapear, no insertar en BD')
    args = parser.parse_args()

    db_path = args.db or str(BASE_DIR / "database" / "bumeran_scraping.db")
    keywords_path = str(BASE_DIR / "config" / "scraping" / "master_keywords.json")

    logger.info("=" * 60)
    logger.info("Indeed Argentina - Scraping LOCAL")
    logger.info("=" * 60)
    logger.info(f"BD: {db_path}")
    logger.info(f"Delay listado: {args.delay}s, detalle: {args.detail_delay}s")
    logger.info(f"Fromage: {args.fromage} dias")
    logger.info(f"Fetch details: {not args.no_details}")

    # Cargar keywords con cycling
    if args.all_keywords:
        logger.warning("MODO SIN CYCLING — usando TODAS las keywords")
        with open(keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        keywords = data['estrategias'][args.estrategia]['keywords']
        keywords = [k for k in keywords if k.strip()]
    else:
        keywords = load_keywords_with_cycling(
            keywords_path,
            estrategia=args.estrategia,
            num_chunks=args.chunks,
            force_chunk=args.force_chunk,
        )

    if not keywords:
        logger.error("No se obtuvieron keywords")
        return

    logger.info(f"Keywords a procesar: {len(keywords)}")

    scraper = IndeedScraper(
        delay=args.delay,
        detail_delay=args.detail_delay,
        fetch_details=not args.no_details,
    )

    ofertas = scraper.scrape_with_keywords(keywords, fromage=args.fromage)

    if not ofertas:
        logger.warning("No se obtuvieron ofertas")
        return

    logger.info(f"\nOfertas scrapeadas: {len(ofertas)}")
    con_desc = sum(1 for o in ofertas if o.get('descripcion'))
    con_fecha = sum(1 for o in ofertas if o.get('fecha_publicacion'))
    logger.info(f"  Con descripcion: {con_desc}")
    logger.info(f"  Con fecha: {con_fecha}")

    ofertas_mapeadas = [mapear_oferta_para_bd(o) for o in ofertas if o]
    logger.info(f"Ofertas mapeadas: {len(ofertas_mapeadas)}")

    if args.dry_run:
        logger.info("DRY RUN - no se inserta en BD")
        return

    stats = insertar_en_bd(ofertas_mapeadas, db_path)

    logger.info("\n" + "=" * 60)
    logger.info("RESULTADO INDEED SCRAPING (LOCAL)")
    logger.info("=" * 60)
    logger.info(f"  Nuevas insertadas: {stats['insertadas']}")
    logger.info(f"  Duplicadas: {stats['duplicadas']}")
    logger.info(f"  Errores: {stats['errores']}")
    logger.info(f"  Total Indeed en BD: {stats['total_indeed']}")
    logger.info(f"  Total ofertas en BD: {stats['total_bd']}")


if __name__ == '__main__':
    main()
