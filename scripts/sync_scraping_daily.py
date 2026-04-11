#!/usr/bin/env python3
"""
Sincroniza conteos diarios de scraping (BD local SQLite → Supabase scraping_daily).

Lee la tabla 'ofertas' local y calcula ofertas por día y portal,
luego hace upsert en scraping_daily de Supabase.

Uso:
    python3 scripts/sync_scraping_daily.py          # últimos 30 días
    python3 scripts/sync_scraping_daily.py --days 90 # últimos 90 días
    python3 scripts/sync_scraping_daily.py --all     # todo el historial
"""

import json
import sqlite3
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'bumeran_scraping.db'


def get_supabase_client():
    config_path = BASE_DIR / 'config' / 'supabase_config.json'
    config = json.loads(config_path.read_text())
    from supabase import create_client
    return create_client(config['url'], config['service_role_key'])


def get_daily_counts(db_path, days=None):
    """Lee conteos diarios por portal desde SQLite local (ambos tipos de fecha)"""
    conn = sqlite3.connect(str(db_path))

    since_clause = ""
    if days:
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        since_clause = f"AND fecha >= '{since}'"

    daily = []

    # Tipo 1: por fecha de scraping (scrapeado_en, compatible con VPS y local)
    query = f"""
        SELECT DATE(scrapeado_en) as fecha, COALESCE(portal, 'desconocido') as portal, COUNT(*) as cnt
        FROM ofertas
        WHERE scrapeado_en IS NOT NULL {since_clause.replace('fecha', 'DATE(scrapeado_en)')}
        GROUP BY fecha, portal
        HAVING fecha IS NOT NULL
        ORDER BY fecha, portal
    """
    acum = {}
    for fecha, portal, count in conn.execute(query).fetchall():
        acum[portal] = acum.get(portal, 0) + count
        daily.append({
            'fecha': fecha, 'portal': portal, 'fecha_tipo': 'scraping',
            'ofertas_nuevas': count, 'ofertas_acumuladas': acum[portal],
        })

    # Tipo 2: por fecha de publicación
    query = f"""
        SELECT DATE(fecha_publicacion_iso) as fecha, COALESCE(portal, 'desconocido') as portal, COUNT(*) as cnt
        FROM ofertas
        WHERE fecha_publicacion_iso IS NOT NULL {since_clause.replace('fecha', 'DATE(fecha_publicacion_iso)')}
        GROUP BY fecha, portal
        HAVING fecha IS NOT NULL
        ORDER BY fecha, portal
    """
    acum = {}
    for fecha, portal, count in conn.execute(query).fetchall():
        acum[portal] = acum.get(portal, 0) + count
        daily.append({
            'fecha': fecha, 'portal': portal, 'fecha_tipo': 'publicacion',
            'ofertas_nuevas': count, 'ofertas_acumuladas': acum[portal],
        })

    conn.close()
    return daily


def sync_to_supabase(daily_data):
    """Upsert conteos diarios a Supabase"""
    client = get_supabase_client()

    # Upsert en batches de 500
    batch_size = 500
    total = 0
    for i in range(0, len(daily_data), batch_size):
        batch = daily_data[i:i + batch_size]
        client.table('scraping_daily').upsert(batch, on_conflict='fecha,portal,fecha_tipo').execute()
        total += len(batch)
        print(f"  Upsert {total}/{len(daily_data)}")

    return total


def main():
    parser = argparse.ArgumentParser(description='Sync scraping daily counts to Supabase')
    parser.add_argument('--days', type=int, default=30, help='Últimos N días (default: 30)')
    parser.add_argument('--all', action='store_true', help='Todo el historial')
    args = parser.parse_args()

    days = None if args.all else args.days

    print(f"=== Sync Scraping Daily ===")
    print(f"  BD: {DB_PATH}")
    print(f"  Periodo: {'todo' if days is None else f'últimos {days} días'}")

    daily = get_daily_counts(DB_PATH, days)
    print(f"  Registros: {len(daily)}")

    if not daily:
        print("  Sin datos para sincronizar")
        return

    total = sync_to_supabase(daily)
    print(f"  Sincronizados: {total}")
    print(f"=== Completado ===")


if __name__ == '__main__':
    main()
