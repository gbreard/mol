#!/usr/bin/env python3
"""
Indeed Argentina - Scraping LOCAL con keyword cycling
=====================================================

Wrapper sobre run_indeed_vps.py para ejecución local.
Usa keyword cycling: 1/4 de keywords por semana para no quemar la IP.
Delays conservadores (4s) para evitar bloqueo de Cloudflare.

Invocado por pipeline_command_poller.py cuando el admin lanza 'scrape_indeed'.

Uso directo:
    python3 scripts/scraping/run_indeed_local.py
    python3 scripts/scraping/run_indeed_local.py --all-keywords     # sin cycling
    python3 scripts/scraping/run_indeed_local.py --force-chunk 0    # chunk específico
    python3 scripts/scraping/run_indeed_local.py --chunks 4         # N chunks (default 4)
    python3 scripts/scraping/run_indeed_local.py --dry-run
"""

import sys
import json
import logging
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "indeed" / "scrapers"))
sys.path.insert(0, str(BASE_DIR / "config" / "scraping"))

from indeed_scraper import IndeedScraper
from keyword_cycling import get_weekly_chunk

# Reuse mapping/insert logic from VPS script
sys.path.insert(0, str(BASE_DIR / "scripts" / "scraping"))
from run_indeed_vps import mapear_oferta_para_bd, insertar_en_bd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_all_keywords(keywords_path: str) -> list:
    """Load all keywords from master_keywords.json (categorias format)."""
    with open(keywords_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # master_keywords.json has categorias dict with lists
    categorias = data.get('categorias', {})
    all_kw = []
    for cat_keywords in categorias.values():
        if isinstance(cat_keywords, list):
            all_kw.extend(cat_keywords)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for kw in all_kw:
        kw_lower = kw.strip().lower()
        if kw_lower and kw_lower not in seen:
            seen.add(kw_lower)
            unique.append(kw.strip())

    return unique


def main():
    parser = argparse.ArgumentParser(description='Indeed Argentina Scraper (local con cycling)')
    parser.add_argument('--chunks', type=int, default=4,
                        help='Chunks de cycling (default: 4 = ciclo mensual)')
    parser.add_argument('--force-chunk', type=int, default=None,
                        help='Forzar chunk específico (0-based)')
    parser.add_argument('--all-keywords', action='store_true',
                        help='Sin cycling — TODAS las keywords (riesgo de bloqueo)')
    parser.add_argument('--fromage', type=int, default=14,
                        help='Días de antigüedad máxima (default: 14)')
    parser.add_argument('--delay', type=float, default=4.0,
                        help='Delay entre requests de listado (default: 4.0)')
    parser.add_argument('--detail-delay', type=float, default=4.0,
                        help='Delay entre requests de detalle (default: 4.0)')
    parser.add_argument('--no-details', action='store_true',
                        help='Solo listado, sin fetch de detalles')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo scrapear, no insertar en BD')
    parser.add_argument('--max-keywords', type=int, default=None,
                        help='Límite de keywords (override cycling)')
    args = parser.parse_args()

    db_path = str(BASE_DIR / "database" / "bumeran_scraping.db")
    keywords_path = str(BASE_DIR / "config" / "scraping" / "master_keywords.json")

    logger.info("=" * 60)
    logger.info("Indeed Argentina - Scraping LOCAL")
    logger.info("=" * 60)

    # Load keywords
    all_keywords = load_all_keywords(keywords_path)
    logger.info(f"Total keywords disponibles: {len(all_keywords)}")

    if args.max_keywords:
        keywords = all_keywords[:args.max_keywords]
        logger.info(f"Limitado a {args.max_keywords} keywords (override)")
    elif args.all_keywords:
        keywords = all_keywords
        logger.warning(f"MODO SIN CYCLING — {len(keywords)} keywords (riesgo de bloqueo)")
    else:
        keywords = get_weekly_chunk(all_keywords, args.chunks, args.force_chunk)

    if not keywords:
        logger.error("No se obtuvieron keywords")
        return

    logger.info(f"Keywords a procesar: {len(keywords)}")
    logger.info(f"Delay: listado={args.delay}s, detalle={args.detail_delay}s")

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
    logger.info(f"  Con descripción: {con_desc}")

    ofertas_mapeadas = [mapear_oferta_para_bd(o) for o in ofertas if o]
    ofertas_mapeadas = [o for o in ofertas_mapeadas if o]
    logger.info(f"Ofertas mapeadas: {len(ofertas_mapeadas)}")

    if args.dry_run:
        logger.info("DRY RUN — no se inserta en BD")
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
