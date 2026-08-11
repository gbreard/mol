#!/usr/bin/env python3
"""Sube stats de scraping a Supabase para que el dashboard las muestre.

Lee la BD LOCAL, que concentra todos los portales (los del VPS llegan por
sync_from_vps.py). Por eso no hace falta excluir ninguno: si un portal tiene
filas en esta BD, sus stats salen de aca.

Historico: hasta 2026-08-11 Indeed se excluia porque corria en la maquina local
y lo escribia el poller — la exclusion preservaba ese valor para que el sync no
lo pisara con datos que la BD no tenia. Al volver Indeed al VPS (lo que lo
bloqueaba no era la IP sino el fingerprint TLS chrome, ver indeed_scraper.py),
esa exclusion congelaba la fecha de Indeed en el dashboard.
"""
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DB_PATH = PROJECT / "database" / "bumeran_scraping.db"
CONFIG_PATH = PROJECT / "config" / "supabase_config.json"

# Portales cuyas stats NO se recalculan desde esta BD (se preserva lo que haya
# en Supabase). Vacio: hoy todos los portales tienen sus filas en la BD local.
PORTALES_LOCALES = set()

def sync():
    if not CONFIG_PATH.exists():
        print("[SYNC-STATS] No supabase config")
        return

    config = json.loads(CONFIG_PATH.read_text())
    from supabase import create_client
    client = create_client(config["url"], config["service_role_key"])

    conn = sqlite3.connect(str(DB_PATH))

    rows = conn.execute("""
        SELECT portal,
               COUNT(*) as total,
               MAX(scrapeado_en) as ultimo,
               SUM(CASE WHEN scrapeado_en >= datetime('now', '-7 days') THEN 1 ELSE 0 END) as ultimos_7d,
               SUM(CASE WHEN scrapeado_en >= datetime('now', '-1 day') THEN 1 ELSE 0 END) as hoy
        FROM ofertas
        GROUP BY portal
        ORDER BY total DESC
    """).fetchall()

    vps_portales = {}
    for r in rows:
        portal = r[0] or "sin_portal"
        if portal in PORTALES_LOCALES:
            continue  # No tocar portales que corren local
        vps_portales[portal] = {
            "total": r[1],
            "ultimo_scraping": str(r[2] or ""),
            "ultimos_7d": r[3] or 0,
            "hoy": r[4] or 0,
        }

    total_vps = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
    conn.close()

    # Leer datos existentes para preservar portales locales
    existing = client.table("scraping_live_stats").select("portales").eq("id", "current").execute()
    existing_portales = {}
    if existing.data and existing.data[0].get("portales"):
        existing_portales = existing.data[0]["portales"]

    # Merge: VPS portales + preservar locales existentes
    merged = dict(vps_portales)
    for portal in PORTALES_LOCALES:
        if portal in existing_portales:
            merged[portal] = existing_portales[portal]

    total = sum(p.get("total", 0) for p in merged.values())
    ultimo_global = max(
        (p["ultimo_scraping"] for p in merged.values() if p.get("ultimo_scraping")),
        default=None
    )

    client.table("scraping_live_stats").upsert({
        "id": "current",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_ofertas": total,
        "portales": merged,
        "ultimo_scraping": ultimo_global,
    }).execute()

    total_7d = sum(p.get("ultimos_7d", 0) for p in merged.values())
    print(f"[SYNC-STATS] OK: {total} ofertas ({total_7d} ultimos 7d), {len(merged)} portales (local: {list(PORTALES_LOCALES & set(merged))})")

if __name__ == "__main__":
    sync()
