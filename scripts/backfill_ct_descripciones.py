#!/usr/bin/env python3
"""
Backfill de descripciones faltantes de ComputRabajo.

Lee ofertas con descripcion=NULL que tienen url_oferta,
visita cada URL y extrae la descripción.

Uso:
    python scripts/backfill_ct_descripciones.py
    python scripts/backfill_ct_descripciones.py --limit 100 --dry-run
"""

import sqlite3
import time
import argparse
import requests
from pathlib import Path
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-AR,es;q=0.9',
}
DELAY = 2  # seconds between requests


def extract_description(html: str) -> str | None:
    """Extract description from ComputRabajo offer page."""
    soup = BeautifulSoup(html, 'html.parser')

    # Method 1: p.mbB (primary)
    desc = soup.find('p', class_='mbB')
    if desc:
        text = desc.get_text(strip=True)
        if len(text) > 30:
            return text

    # Method 2: div with substantive content
    for div in soup.find_all('div', class_='fs16'):
        text = div.get_text(strip=True)
        if len(text) > 80:
            return text

    # Method 3: any div with >100 chars leaf content
    for div in soup.find_all('div'):
        if div.find('div'):
            continue
        text = div.get_text(strip=True)
        if len(text) > 100:
            return text

    return None


def main():
    parser = argparse.ArgumentParser(description="Backfill ComputRabajo descriptions")
    parser.add_argument("--limit", type=int, default=0, help="Limit offers (0=all)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")

    # Get offers without description
    query = """
        SELECT id_oferta, url_oferta FROM ofertas
        WHERE (descripcion IS NULL OR LENGTH(descripcion) <= 50)
        AND url_oferta IS NOT NULL AND url_oferta != ''
        AND CAST(id_oferta AS INTEGER) >= 5000000000
        AND CAST(id_oferta AS INTEGER) < 9000000000
        ORDER BY fecha_publicacion_iso DESC
    """
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    offers = conn.execute(query).fetchall()
    print(f"Ofertas sin descripción: {len(offers)}")

    if args.dry_run:
        print("[DRY-RUN] No se descarga nada.")
        return

    fetched = 0
    failed = 0
    expired = 0
    session = requests.Session()
    session.headers.update(HEADERS)

    for i, (oid, url) in enumerate(offers):
        # Clean URL (remove fragment)
        clean_url = url.split('#')[0]

        try:
            r = session.get(clean_url, timeout=15)

            if r.status_code == 404 or r.status_code == 410:
                expired += 1
                if expired <= 3:
                    print(f"  [{i+1}/{len(offers)}] {oid}: EXPIRADA (404/410)")
                continue

            if r.status_code != 200:
                failed += 1
                if failed <= 3:
                    print(f"  [{i+1}/{len(offers)}] {oid}: HTTP {r.status_code}")
                continue

            desc = extract_description(r.text)
            if desc:
                conn.execute(
                    "UPDATE ofertas SET descripcion = ? WHERE id_oferta = ?",
                    (desc[:5000], str(oid))
                )
                fetched += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"  [{i+1}/{len(offers)}] {oid}: sin descripción en HTML")

        except requests.RequestException as e:
            failed += 1
            if failed <= 3:
                print(f"  [{i+1}/{len(offers)}] {oid}: {e}")

        # Progress + commit every 50
        if (i + 1) % 50 == 0:
            conn.commit()
            print(f"  [{i+1}/{len(offers)}] fetched={fetched} failed={failed} expired={expired}")

        time.sleep(DELAY)

    conn.commit()
    conn.close()

    print(f"\nResultado:")
    print(f"  Fetched: {fetched}")
    print(f"  Failed: {failed}")
    print(f"  Expired: {expired}")
    print(f"  Total: {fetched + failed + expired}/{len(offers)}")


if __name__ == "__main__":
    main()
