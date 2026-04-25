#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill del campo `titulo_esco_code` en `ofertas_esco_matching`.

Hasta hoy el campo estaba vacío en las 52,571 ofertas. El esco_code específico
(ej. "7214.3.1") se podía derivar consultando metadata desde `esco_occupation_uri`,
pero no estaba persistido en la BD. Con SPEC H + SPEC E corregidos, ahora cada
oferta tiene la URI correcta. Llenamos el campo derivando desde URI.

Uso:
    python3 scripts/embeddings/backfill_titulo_esco_code.py
    python3 scripts/embeddings/backfill_titulo_esco_code.py --dry-run
"""
import argparse
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    # Mapa URI → esco_code desde metadata
    print('[backfill] Cargando metadata ocupaciones...')
    meta = json.load(open(ROOT / 'database/embeddings/esco_occupations_metadata.json'))
    uri_to_code = {m['uri']: m.get('esco_code') for m in meta if m.get('esco_code')}
    print(f'[backfill] Ocupaciones con esco_code: {len(uri_to_code):,}')

    conn = sqlite3.connect(args.db)
    c = conn.cursor()

    # Total ofertas con esco_occupation_uri no vacío
    c.execute('''SELECT COUNT(*) FROM ofertas_esco_matching
                 WHERE esco_occupation_uri IS NOT NULL AND esco_occupation_uri != "" ''')
    total = c.fetchone()[0]
    print(f'[backfill] Ofertas con esco_occupation_uri: {total:,}')

    # Procesar
    c.execute('''SELECT id_oferta, esco_occupation_uri FROM ofertas_esco_matching
                 WHERE esco_occupation_uri IS NOT NULL AND esco_occupation_uri != "" ''')
    rows = c.fetchall()

    actualizadas = 0
    sin_match = 0
    no_match_sample = []
    t0 = time.time()
    for i, (oid, uri) in enumerate(rows, 1):
        code = uri_to_code.get(uri)
        if not code:
            sin_match += 1
            if len(no_match_sample) < 5:
                no_match_sample.append((oid, uri))
            continue
        if not args.dry_run:
            c.execute('UPDATE ofertas_esco_matching SET titulo_esco_code = ? WHERE id_oferta = ?',
                      (code, str(oid)))
        actualizadas += 1
        if i % 5000 == 0:
            if not args.dry_run:
                conn.commit()
            print(f'  [{i}/{total}] actualizadas={actualizadas} sin_match={sin_match}')

    if not args.dry_run:
        conn.commit()

    el = time.time() - t0
    print(f'\n[backfill] Terminado en {el:.0f}s')
    print(f'  Actualizadas: {actualizadas:,}')
    print(f'  Sin match en metadata: {sin_match:,}')
    if no_match_sample:
        print(f'  Sample sin match:')
        for oid, uri in no_match_sample:
            print(f'    {oid}: {uri[:80]}')

    # Verificación
    c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE titulo_esco_code IS NOT NULL AND titulo_esco_code != ""')
    print(f'\n[backfill] Total con titulo_esco_code post-update: {c.fetchone()[0]:,}')
    conn.close()


if __name__ == '__main__':
    main()
