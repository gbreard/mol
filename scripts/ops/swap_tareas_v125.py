# -*- coding: utf-8 -*-
"""[CASCADA — swap P3→P4] Migra las tareas v12.5 del staging a la tabla viva ofertas_nlp.
ESCRIBE el main DB → EXIGE ventana muerta de escritores (ver CASCADA_DISEÑO_swap_P3.md).
Candado F0.4b: el swap toca SOLO tareas_explicitas (input), NO decisiones de matching → las
6.326 validadas-humanas reciben sus tareas v12.5, su matching queda intacto (eso es P4).

Uso:
  python scripts/ops/swap_tareas_v125.py --check     # precondiciones (escritores, snapshot)
  python scripts/ops/swap_tareas_v125.py --dry-run   # cuántas y muestra, sin tocar
  python scripts/ops/swap_tareas_v125.py --execute    # aplica (SOLO en ventana muerta, con OK)
"""
import argparse
import hashlib
import json
import subprocess
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
STAGING = ROOT / 'database' / 'cascada_staging.db'
SNAP = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz'
MANIF = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_MANIFIESTO.json'


def check_preconditions():
    ok = True
    # 1) escritores activos del main
    try:
        ps = subprocess.check_output(['pgrep', '-af', 'python'], text=True)
    except subprocess.CalledProcessError:
        ps = ''
    writers = [l for l in ps.splitlines()
               if any(w in l for w in ('sync_scraping_dinamica', 'sync_from_vps',
                                       'pipeline_command_poller', 'run_validated_pipeline',
                                       'process_nlp_from_db')) and 'swap_tareas' not in l]
    if writers:
        ok = False
        print('  ❌ ESCRITORES ACTIVOS (pausar antes del swap):')
        for w in writers:
            print(f'     {w[:100]}')
    else:
        print('  ✅ sin escritores de main activos')
    # 2) snapshot de rollback presente + sha256
    try:
        man = json.load(open(MANIF))
        rec = man['archivos'].get('exports/cohorts/snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz', {})
        h = hashlib.sha256()
        with open(SNAP, 'rb') as f:
            for ch in iter(lambda: f.read(1 << 20), b''):
                h.update(ch)
        if h.hexdigest() == rec.get('sha256'):
            print('  ✅ snapshot rollback tareas_v11 íntegro (sha256 OK)')
        else:
            ok = False; print('  ❌ snapshot tareas_v11 sha256 NO coincide')
    except Exception as e:
        ok = False; print(f'  ❌ no se pudo verificar snapshot: {e}')
    # 3) recordatorio crons
    print('  ℹ ventana: evitar :00 (auto_sync), 0/3h (indeed), 6:15 (portalempleo), 7:00 (verificador)')
    print('  ℹ pausar el cron del poller:  crontab -l > /tmp/ct.bak && crontab -l | grep -v pipeline_command_poller | crontab -')
    return ok


def _rows():
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    return stg.execute("SELECT id_oferta, tareas_json, n_tareas, primera_extraccion "
                       "FROM ofertas_nlp_tareas_v124").fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()

    if args.check:
        ok = check_preconditions()
        print('PRECONDICIONES:', 'OK para swap' if ok else 'NO — resolver antes')
        return

    rows = _rows()
    # formato tareas_explicitas vivo = ';'-separado (compat v11 que lee el matcher/traductor)
    def joined(tj):
        return '; '.join(json.loads(tj)) if tj else ''

    if args.dry_run:
        n_update = sum(1 for _, tj, nt, _ in rows if True)
        vac = sum(1 for _, tj, nt, _ in rows if not nt)
        print(f'[DRY-RUN] filas en staging: {len(rows)}')
        print(f'  se actualizarían tareas_explicitas de {n_update} ofertas ({vac} a vacío)')
        print('  nlp_version -> "12.5-tareas" ; se preserva matching (candado = P4)')
        for oid, tj, nt, prim in rows[:5]:
            print(f'    {oid} (prim={prim}) n={nt}: {joined(tj)[:90]}')
        print('  NO se escribió nada. Para aplicar: --execute (en ventana muerta, con OK de Gerardo).')
        return

    if args.execute:
        if not check_preconditions():
            print('ABORTADO: precondiciones no OK.')
            sys.exit(1)
        con = sqlite3.connect(MAIN, timeout=120)
        con.execute('PRAGMA busy_timeout=120000')
        cols = [r[1] for r in con.execute("PRAGMA table_info(ofertas_nlp)")]
        if 'tareas_epoca' not in cols:
            con.execute("ALTER TABLE ofertas_nlp ADD COLUMN tareas_epoca TEXT")
        con.commit()
        t0 = time.time(); n = 0
        for oid, tj, nt, prim in rows:
            con.execute("UPDATE ofertas_nlp SET tareas_explicitas=?, nlp_version='12.5-tareas', "
                        "tareas_epoca='v12.5' WHERE id_oferta=?", (joined(tj), oid))
            n += 1
            if n % 2000 == 0:
                con.commit(); print(f'  {n}/{len(rows)}', flush=True)
        con.commit()
        print(f'[SWAP APLICADO] {n} ofertas en {(time.time()-t0)/60:.1f} min. '
              f'Reactivar crons. Siguiente: P4 (re-matching con candado).')
        con.close()
        return
    print('Indicá --check | --dry-run | --execute')


if __name__ == '__main__':
    main()
