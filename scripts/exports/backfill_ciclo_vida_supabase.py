#!/usr/bin/env python3
"""B.4 — HERRAMIENTA DE VERIFICACION. **NO APTO PARA ESCRIBIR.**

Su modo --dry-run sirve: cruza ofertas_dashboard contra local y reporta cuantas
filas tienen estado_ciclo para poblar y su distribucion.

Sus modos de ESCRITURA no funcionan y se dejan solo como registro del intento:
PostgREST traduce upsert a INSERT ... ON CONFLICT DO UPDATE, asi que el payload
debe satisfacer los NOT NULL aunque la fila exista. Con id_oferta + 6 columnas
falla con 23502 (null value in column "titulo"). Verificado 2026-09-10 con
--checkpoint: 0 filas escritas.

El backfill real se hace agregando las columnas al transform del sync
(transform_oferta_for_supabase) y corriendo un sync: manda la fila completa.

Backfill de las columnas de ciclo de vida en ofertas_dashboard.

Puebla en Supabase las 6 columnas que agrego la migracion 067, para las filas
que YA existen alli. No usa --full del sync (2,8M skills, horas): va dirigido,
por lotes, solo con id_oferta + las 6 columnas.

Requiere que 067 este ejecutado (SQL Editor). Verifica que las columnas existan
antes de escribir nada.

Uso:
    python3 scripts/exports/backfill_ciclo_vida_supabase.py --dry-run
    python3 scripts/exports/backfill_ciclo_vida_supabase.py --checkpoint   # 1 lote
    python3 scripts/exports/backfill_ciclo_vida_supabase.py
"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
DB = PROJECT / 'database' / 'bumeran_scraping.db'
CFG = PROJECT / 'config' / 'supabase_config.json'
LOTE = 500

COLUMNAS = ['estado_ciclo', 'fecha_baja_estimada', 'fecha_baja_intervalo_desde',
            'fecha_baja_intervalo_hasta', 'fecha_baja_incertidumbre_dias',
            'grupo_oferta_id']


def cliente():
    from supabase import create_client
    cfg = json.loads(CFG.read_text())
    return create_client(cfg['url'], cfg['service_role_key'])


def verificar_columnas(client):
    """Sin las columnas de 067 el upsert falla a mitad de camino; mejor abortar antes."""
    r = client.table('ofertas_dashboard').select('*').limit(1).execute()
    if not r.data:
        print('ofertas_dashboard vacia: nada que backfillear')
        return False
    faltan = [c for c in COLUMNAS if c not in r.data[0]]
    if faltan:
        print('FALTAN columnas en ofertas_dashboard: %s' % faltan)
        print('  -> ejecutar fase3_dashboard/sql/067_ciclo_vida_ofertas.sql en el SQL Editor')
        return False
    print('columnas de 067 verificadas: OK')
    return True


def ids_en_supabase(client):
    """Solo se backfillea lo que YA esta en Supabase: esto es un UPDATE, no una carga."""
    ids, off = set(), 0
    while True:
        r = client.table('ofertas_dashboard').select('id_oferta').range(off, off + 999).execute()
        if not r.data:
            break
        ids.update(str(x['id_oferta']) for x in r.data)
        off += 1000
    return ids


def filas_locales(ids):
    conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    out = []
    q = 'SELECT id_oferta, %s FROM ofertas WHERE estado_ciclo IS NOT NULL' % ', '.join(COLUMNAS)
    for row in conn.execute(q):
        sid = str(row['id_oferta'])
        if sid not in ids:
            continue                      # no esta en Supabase: no se inserta, se ignora
        d = {'id_oferta': row['id_oferta']}
        for c in COLUMNAS:
            d[c] = row[c]
        out.append(d)
    conn.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--checkpoint', action='store_true',
                    help='escribe UN solo lote y verifica en Supabase antes de seguir')
    args = ap.parse_args()

    client = cliente()
    if not verificar_columnas(client):
        sys.exit(1)

    print('leyendo ids de Supabase...')
    ids = ids_en_supabase(client)
    print('  %d filas en ofertas_dashboard' % len(ids))

    print('cruzando con local...')
    filas = filas_locales(ids)
    print('  %d filas a backfillear' % len(filas))

    from collections import Counter
    print('  por estado_ciclo: %s' % dict(Counter(f['estado_ciclo'] for f in filas)))

    if args.dry_run:
        print('[DRY-RUN] no se escribe nada')
        print('  ejemplo: %s' % filas[0] if filas else '  (sin filas)')
        return

    lotes = [filas[i:i + LOTE] for i in range(0, len(filas), LOTE)]
    if args.checkpoint:
        lotes = lotes[:1]
        print('CHECKPOINT: solo el primer lote (%d filas)' % len(lotes[0]))

    t0, escritas, errores = time.time(), 0, 0
    for i, lote in enumerate(lotes, 1):
        try:
            client.table('ofertas_dashboard').upsert(lote, on_conflict='id_oferta').execute()
            escritas += len(lote)
        except Exception as e:
            errores += 1
            print('  ERROR lote %d: %s' % (i, str(e)[:160]))
            if errores > max(3, len(lotes) * 0.02):     # mismo criterio del sync: 2%
                print('FRENADO: demasiados errores')
                sys.exit(2)
        if i % 10 == 0 or i == len(lotes):
            print('  lote %d/%d — %d filas — %.0fs' % (i, len(lotes), escritas, time.time() - t0))

    print('backfill terminado: %d filas, %d errores, %.0fs' % (escritas, errores, time.time() - t0))
    if args.checkpoint:
        print('\nVERIFICAR en Supabase antes de correr el backfill completo:')
        print("  select estado_ciclo, count(*) from ofertas_dashboard "
              "where estado_ciclo is not null group by 1;")


if __name__ == '__main__':
    main()
