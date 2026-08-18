#!/usr/bin/env python3
"""
Backfill de descripciones faltantes de Indeed.

Contexto: entre 2026-07-02 y 2026-08-03 Cloudflare bloqueo la familia de
fingerprints TLS chrome/edge que usaba el scraper. El LISTADO seguia
funcionando (los titulos entraron) pero el fetch de DETALLE devolvia 403,
asi que ~2.700 ofertas quedaron guardadas sin descripcion. Con el
fingerprint corregido (firefox135) esas paginas vuelven a responder.

Reutiliza IndeedScraper.fetch_detail (mismo parser, misma rotacion de
fingerprints ante bloqueo) y solo actualiza `descripcion`.

Uso:
    python3 scripts/backfill_indeed_descripciones.py --dry-run
    python3 scripts/backfill_indeed_descripciones.py --limit 200
    python3 scripts/backfill_indeed_descripciones.py            # todas
"""

import re
import sys
import time
import sqlite3
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"

sys.path.insert(0, str(PROJECT_ROOT / "01_sources" / "indeed" / "scrapers"))
from indeed_scraper import IndeedScraper  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

JK_RE = re.compile(r'[?&]jk=([0-9a-f]+)', re.IGNORECASE)


def extract_jk(url: str) -> str | None:
    """Saca el job_key de la url_oferta (https://ar.indeed.com/viewjob?jk=XXX)."""
    if not url:
        return None
    m = JK_RE.search(url)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description="Backfill descripciones Indeed")
    parser.add_argument("--limit", type=int, default=0, help="Limite de ofertas (0=todas)")
    parser.add_argument("--desde", default="2026-07-01",
                        help="Solo ofertas scrapeadas desde esta fecha (default: 2026-07-01)")
    parser.add_argument("--delay", type=float, default=2.5,
                        help="Segundos entre requests (default: 2.5)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    query = """
        SELECT id_oferta, url_oferta FROM ofertas
        WHERE portal = 'indeed'
          AND (descripcion IS NULL OR LENGTH(descripcion) <= 50)
          AND url_oferta IS NOT NULL AND url_oferta != ''
          AND scrapeado_en >= ?
        ORDER BY scrapeado_en DESC
    """
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    ofertas = conn.execute(query, (args.desde,)).fetchall()
    logger.info(f"Ofertas Indeed sin descripcion desde {args.desde}: {len(ofertas)}")

    if args.dry_run:
        logger.info("[DRY-RUN] No se descarga ni actualiza nada.")
        conn.close()
        return

    # fetch_details=False: el scraper no se usa para scrapear, solo su fetch_detail
    scraper = IndeedScraper(delay=args.delay, detail_delay=args.delay,
                            fetch_details=False)

    ok = expiradas = sin_jk = 0

    for i, (oid, url) in enumerate(ofertas, 1):
        jk = extract_jk(url)
        if not jk:
            sin_jk += 1
            continue

        # fetch_detail no rota por su cuenta (la rotacion vive en los loops del
        # scraper). Aca replicamos el criterio: 5 bloqueos seguidos -> siguiente
        # fingerprint; si se agotan, cortar en vez de quemar requests contra un 403.
        if scraper._consecutive_blocks >= scraper._max_consecutive_blocks:
            if not scraper._rotate_fingerprint():
                logger.error("  Fingerprints agotados — corto el backfill "
                              f"en {i}/{len(ofertas)}. Reintentar mas tarde.")
                break

        detail = scraper.fetch_detail(jk)
        desc = (detail or {}).get('descripcion')

        if desc and len(desc) > 50:
            scraper._consecutive_blocks = 0
            conn.execute("UPDATE ofertas SET descripcion = ? WHERE id_oferta = ?",
                          (desc[:20000], oid))
            ok += 1
        else:
            expiradas += 1

        if i % 50 == 0:
            conn.commit()
            logger.info(f"  [{i}/{len(ofertas)}] recuperadas={ok} "
                         f"sin_detalle={expiradas} sin_jk={sin_jk}")

        time.sleep(args.delay)

    conn.commit()
    conn.close()

    logger.info("")
    logger.info("RESULTADO BACKFILL INDEED")
    logger.info(f"  Recuperadas:  {ok}")
    logger.info(f"  Sin detalle:  {expiradas} (404/expiradas o bloqueo)")
    logger.info(f"  Sin job_key:  {sin_jk}")
    logger.info(f"  Total:        {len(ofertas)}")


if __name__ == "__main__":
    main()
