#!/usr/bin/env python3
"""
Calcula métricas de dinámica del mercado desde SQLite y sube a Supabase.

Usa fecha_ultimo_visto como proxy de "día de scraping" y fecha_baja para bajas.
Republicaciones desde la columna es_republicacion de la tabla ofertas.
Vida media desde fecha_publicacion hasta fecha_baja (vida real de la oferta).

Uso:
    python3 scripts/sync_scraping_dinamica.py          # últimos 90 días
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
    conn = sqlite3.connect(str(db_path))

    since_clause = ""
    if days:
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        since_clause = f"AND DATE(fecha_ultimo_visto) >= '{since}'"

    # Nuevas por día (agrupadas por fecha_ultimo_visto = día del scraping)
    nuevas_query = f"""
        SELECT DATE(fecha_ultimo_visto) as fecha, COUNT(*) as cnt
        FROM ofertas
        WHERE fecha_ultimo_visto IS NOT NULL {since_clause}
        GROUP BY fecha
        ORDER BY fecha
    """
    nuevas_por_dia = dict(conn.execute(nuevas_query).fetchall())

    # Bajas por día
    bajas_query = f"""
        SELECT DATE(fecha_baja) as fecha, COUNT(*) as cnt
        FROM ofertas
        WHERE fecha_baja IS NOT NULL
        {'AND DATE(fecha_baja) >= ' + repr(since) if days else ''}
        GROUP BY fecha
        ORDER BY fecha
    """
    bajas_por_dia = dict(conn.execute(bajas_query).fetchall())

    # Republicaciones por día (desde tabla ofertas, campo es_republicacion)
    repub_query = f"""
        SELECT DATE(fecha_ultimo_visto) as fecha, COUNT(*) as cnt
        FROM ofertas
        WHERE es_republicacion = 1 AND fecha_ultimo_visto IS NOT NULL {since_clause}
        GROUP BY fecha
        ORDER BY fecha
    """
    repub_por_dia = dict(conn.execute(repub_query).fetchall())

    # Vida media: usar fecha_publicacion_iso → fecha_baja (vida real de la oferta en el mercado)
    vida_query = f"""
        SELECT
            DATE(fecha_baja) as fecha,
            CAST(julianday(DATE(fecha_baja)) - julianday(DATE(fecha_publicacion_iso)) AS INTEGER) as vida_dias
        FROM ofertas
        WHERE fecha_baja IS NOT NULL
          AND fecha_publicacion_iso IS NOT NULL
          AND julianday(DATE(fecha_baja)) > julianday(DATE(fecha_publicacion_iso))
        {'AND DATE(fecha_baja) >= ' + repr(since) if days else ''}
    """
    vida_por_dia = defaultdict(list)
    for fecha, vida in conn.execute(vida_query).fetchall():
        if fecha and vida and 0 < vida < 365:  # filtrar outliers
            vida_por_dia[fecha].append(vida)

    # Total activas al día (acumulado)
    total_activas_query = """
        SELECT COUNT(*) FROM ofertas
        WHERE estado_oferta = 'activa' OR (fecha_baja IS NULL AND fecha_ultimo_visto IS NOT NULL)
    """
    activas_actual = conn.execute(total_activas_query).fetchone()[0]

    conn.close()

    # Unir todas las fechas
    todas_fechas = sorted(set(list(nuevas_por_dia.keys()) + list(bajas_por_dia.keys())))

    UMBRAL_MASIVO = 10000

    dinamica = []

    for fecha in todas_fechas:
        nuevas = nuevas_por_dia.get(fecha, 0)
        bajas = bajas_por_dia.get(fecha, 0)
        repubs = repub_por_dia.get(fecha, 0)

        # Vida media (mediana)
        vidas = vida_por_dia.get(fecha, [])
        vida_media = None
        if vidas:
            vidas_sorted = sorted(vidas)
            vida_media = vidas_sorted[len(vidas_sorted) // 2]

        es_masivo = nuevas > UMBRAL_MASIVO or bajas > UMBRAL_MASIVO
        es_solo_bajas = nuevas == 0 and bajas > 0  # día sin scraping, solo detección de bajas

        # Tasas: solo para días normales con datos suficientes
        tasa_rot = None
        tasa_repub = None
        if not es_masivo and not es_solo_bajas and nuevas > 0:
            tasa_repub = round(repubs / nuevas, 4)
            if activas_actual > 0:
                tasa_rot = round(bajas / activas_actual, 4)

        dinamica.append({
            'fecha': fecha,
            'ofertas_nuevas': nuevas,
            'ofertas_bajas': bajas,
            'ofertas_republicadas': repubs,
            'ofertas_activas': activas_actual,
            'grupos_republicados': 0,
            'vida_media_dias': vida_media,
            'tasa_rotacion': tasa_rot,
            'tasa_republicacion': tasa_repub,
            'flujo_neto': nuevas - bajas,
        })

    return dinamica


def sync_to_supabase(data):
    client = get_supabase_client()
    # Limpiar tabla y re-insertar (más simple que upsert con nulls)
    client.table('scraping_dinamica').delete().neq('fecha', '1900-01-01').execute()
    batch_size = 500
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        client.table('scraping_dinamica').insert(batch).execute()
        total += len(batch)
        print(f"  Insert {total}/{len(data)}")
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=90)
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

    # Resumen (excluyendo días masivos)
    normales = [d for d in data if d['ofertas_nuevas'] <= 10000 and d['ofertas_bajas'] <= 10000]
    total_nuevas = sum(d['ofertas_nuevas'] for d in normales)
    total_bajas = sum(d['ofertas_bajas'] for d in normales)
    total_repubs = sum(d['ofertas_republicadas'] for d in normales)
    masivos = len(data) - len(normales)
    print(f"  Días normales: {len(normales)} | Días masivos (excluidos de promedios): {masivos}")
    print(f"  Nuevas: {total_nuevas:,} | Bajas: {total_bajas:,} | Repubs: {total_repubs:,}")

    total = sync_to_supabase(data)
    print(f"  Sincronizados: {total}")
    print(f"=== Completado ===")


if __name__ == '__main__':
    main()
