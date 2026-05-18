#!/usr/bin/env python3
"""
Backfill pipeline_runs_history.source y description desde la BD local SQLite.

Pre-requisitos:
- migrations/023_pipeline_runs_history_source.sql aplicada en Supabase.

Uso:
    python scripts/backfill_pipeline_runs_source.py [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

from supabase import create_client

REPO = Path(__file__).resolve().parents[1]
DB_PATH = REPO / "database" / "bumeran_scraping.db"
CONFIG = REPO / "config" / "supabase_config.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="No escribe en Supabase")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    client = create_client(config["url"], config["service_role_key"])

    # Leer source + description local
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(
        "SELECT run_id, source, description FROM pipeline_runs WHERE source IS NOT NULL"
    ))
    print(f"Runs locales con source: {len(rows)}")

    if args.dry_run:
        from collections import Counter
        sources = Counter(r["source"] for r in rows)
        print("Distribución por source:")
        for src, n in sources.most_common(20):
            print(f"  {src}: {n}")
        return 0

    t0 = time.time()
    ok = 0
    fail = 0
    for i, r in enumerate(rows):
        try:
            client.table("pipeline_runs_history").update({
                "source": r["source"],
                "description": r["description"] or None,
            }).eq("run_id", r["run_id"]).execute()
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  FALLA {r['run_id']}: {str(e)[:120]}")
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(rows)} ({time.time()-t0:.0f}s) ok={ok} fail={fail}")

    print(f"\nResultado: ok={ok} fail={fail} en {time.time()-t0:.0f}s")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
