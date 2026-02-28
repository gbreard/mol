"""
Backfill ofertas_skills to Supabase for all validated offers.
Extracts from SQLite ofertas_esco_skills_detalle, transforms, and upserts.
"""
import sqlite3
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


def main():
    # Import sync functions from the main module
    from scripts.exports.sync_to_supabase import (
        extraer_skills_detalle,
        upsert_skills,
        get_supabase_client,
    )

    client = get_supabase_client()

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    # Get all validated offer IDs
    rows = db.execute("""
        SELECT id_oferta FROM ofertas_esco_matching
        WHERE estado_validacion IN ('validado_claude','validado_humano','validado')
    """).fetchall()
    all_ids = [str(r['id_oferta']) for r in rows]
    print(f"Ofertas validadas: {len(all_ids)}", flush=True)

    # Process in chunks — smaller + sleep to avoid rate-limiting Supabase
    CHUNK = 200
    total_skills = 0
    t0 = time.time()

    for i in range(0, len(all_ids), CHUNK):
        chunk_ids = all_ids[i:i + CHUNK]
        skills = extraer_skills_detalle(db, chunk_ids)

        if skills:
            uploaded = upsert_skills(client, skills)
            total_skills += uploaded

        elapsed = time.time() - t0
        rate = (i + len(chunk_ids)) / elapsed if elapsed > 0 else 0
        eta = (len(all_ids) - i - len(chunk_ids)) / rate if rate > 0 else 0
        print(
            f"  [{i + len(chunk_ids)}/{len(all_ids)}] "
            f"skills: {total_skills} | {elapsed:.0f}s | ETA {eta / 60:.1f}min",
            flush=True,
        )

        # Throttle to avoid killing Supabase free tier
        time.sleep(1)

    elapsed = time.time() - t0
    print(f"\nDone: {total_skills} skills uploaded in {elapsed / 60:.1f}min", flush=True)
    db.close()


if __name__ == "__main__":
    main()
