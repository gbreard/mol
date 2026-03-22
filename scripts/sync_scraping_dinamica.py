#!/usr/bin/env python3
"""
Calcula métricas de dinámica del mercado desde SQLite y sube a Supabase.

Métricas por día:
  - ofertas_nuevas: ofertas vistas por primera vez ese día
  - ofertas_bajas: ofertas que dejaron de aparecer ese día
  - ofertas_republicadas: ofertas detectadas como republicación
  - ofertas_activas: total activas al cierre del día
  - vida_media_dias: mediana de días que una oferta permanece activa
  - tasa_rotacion: bajas / activas
  - tasa_republicacion: republicadas / total
  - flujo_neto: nuevas - bajas

Uso:
    python3 scripts/sync_scraping_dinamica.py          # últimos 30 días
    python3 scripts/sync_scraping_dinamica.py --all    # todo
"""

import json
import sqlite3
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'bumeran_scraping.db'


def get_supabase_client():
    config = json.loads((BASE_DIR / 'config' / 'supabase_config.json').read_text())
    from supabase import create_client
    return create_client(config['url'], config['service_role_key'])


def calculate_dinamica(db_path, days=None):
    """Calcula métricas de dinámica desde SQLite"""
    conn = sqlite3.connect(str(db_path))

    # Obtener todas las ofertas con sus fechas relevantes
    since = ''
    if days:
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        since = f"AND (DATE(fecha_ultimo_visto) >= '{since_date}' OR DATE(fecha_baja) >= '{since_date}')"

    query = f"""
        SELECT
            id,
            DATE(fecha_ultimo_visto) as fecha_visto,
            DATE(fecha_baja) as fecha_baja,
            DATE(fecha_publicacion_iso) as fecha_pub,
            estado,
            COALESCE(portal, 'desconocido') as portal
        FROM ofertas
        WHERE 1=1 {since}
    """
    rows = conn.execute(query).fetchall()

    # Republicaciones
    query_repub = """
        SELECT DATE(fecha_ultimo_visto) as fecha, COUNT(*) as cnt
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id = n.id_oferta
        WHERE n.es_republicacion = 1 AND fecha_ultimo_visto IS NOT NULL
        GROUP BY fecha
    """
    try:
        repub_por_dia = dict(conn.execute(query_repub).fetchall())
    except:
        repub_por_dia = {}

    # Permanencia media
    query_perm = """
        SELECT
            DATE(fecha_baja) as fecha,
            CAST(julianday(fecha_baja) - julianday(fecha_publicacion_iso) AS INTEGER) as dias_activa
        FROM ofertas
        WHERE fecha_baja IS NOT NULL AND fecha_publicacion_iso IS NOT NULL
    """
    try:
        perm_data = conn.execute(query_perm).fetchall()
    except:
        perm_data = []

    perm_por_dia = defaultdict(list)
    for fecha, dias in perm_data:
        if fecha and dias and dias >= 0:
            perm_por_dia[fecha].append(dias)

    conn.close()

    # Agrupar por día
    nuevas_por_dia = defaultdict(int)
    bajas_por_dia = defaultdict(int)
    activas_acum = 0
    activas_por_dia = {}
    todas_fechas = set()

    for _, fecha_visto, fecha_baja, fecha_pub, estado, portal in rows:
        if fecha_visto:
            nuevas_por_dia[fecha_visto] += 1
            todas_fechas.add(fecha_visto)
        if fecha_baja:
            bajas_por_dia[fecha_baja] += 1
            todas_fechas.add(fecha_baja)

    # Calcular activas acumuladas por día
    fechas_ordenadas = sorted(todas_fechas)
    activas = 0
    for fecha in fechas_ordenadas:
        activas += nuevas_por_dia.get(fecha, 0) - bajas_por_dia.get(fecha, 0)
        activas_por_dia[fecha] = max(activas, 0)

    # Construir registros
    dinamica = []
    for fecha in fechas_ordenadas:
        nuevas = nuevas_por_dia.get(fecha, 0)
        bajas = bajas_por_dia.get(fecha, 0)
        activas = activas_por_dia.get(fecha, 0)
        repubs = repub_por_dia.get(fecha, 0)
        perm_list = perm_por_dia.get(fecha, [])
        vida_media = sorted(perm_list)[len(perm_list) // 2] if perm_list else None

        dinamica.append({
            'fecha': fecha,
            'ofertas_nuevas': nuevas,
            'ofertas_bajas': bajas,
            'ofertas_republicadas': repubs,
            'ofertas_activas': activas,
            'grupos_republicados': 0,
            'vida_media_dias': vida_media,
            'tasa_rotacion': round(bajas / max(activas, 1), 4),
            'tasa_republicacion': round(repubs / max(nuevas, 1), 4),
            'flujo_neto': nuevas - bajas,
        })

    return dinamica


def sync_to_supabase(data):
    client = get_supabase_client()
    batch_size = 500
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        client.table('scraping_dinamica').upsert(batch, on_conflict='fecha').execute()
        total += len(batch)
        print(f"  Upsert {total}/{len(data)}")
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    days = None if args.all else args.days

    print(f"=== Sync Scraping Dinámica ===")
    print(f"  BD: {DB_PATH}")
    print(f"  Periodo: {'todo' if days is None else f'{days} días'}")

    data = calculate_dinamica(DB_PATH, days)
    print(f"  Registros: {len(data)}")

    if not data:
        print("  Sin datos")
        return

    # Mostrar resumen
    total_nuevas = sum(d['ofertas_nuevas'] for d in data)
    total_bajas = sum(d['ofertas_bajas'] for d in data)
    total_repubs = sum(d['ofertas_republicadas'] for d in data)
    print(f"  Nuevas: {total_nuevas:,} | Bajas: {total_bajas:,} | Repubs: {total_repubs:,}")

    total = sync_to_supabase(data)
    print(f"  Sincronizados: {total}")
    print(f"=== Completado ===")


if __name__ == '__main__':
    main()
