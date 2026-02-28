"""
Backfill 5 new columns to ofertas_dashboard in Supabase.
One-time script — run after executing 015_add_validation_columns.sql.

Columns: descripcion, tareas_explicitas, mision_rol, decision_metodo, regla_aplicada
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
    from supabase import create_client

    config = json.load(open(CONFIG_PATH))
    client = create_client(config['url'], config['service_role_key'])

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    rows = db.execute('''
        SELECT n.id_oferta, o.descripcion, n.tareas_explicitas, n.mision_rol,
               m.decision_metodo, m.regla_aplicada
        FROM ofertas_esco_matching m
        JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        JOIN ofertas o ON o.id_oferta = CASE
            WHEN n.es_suboferta = 1 THEN CAST(n.parent_id_oferta AS INTEGER)
            ELSE n.id_oferta END
        WHERE m.estado_validacion IN ('validado_claude','validado_humano','validado')
    ''').fetchall()

    total = len(rows)
    print(f"Total ofertas a actualizar: {total}", flush=True)

    ok = 0
    errors = 0
    skipped = 0
    t0 = time.time()

    for i, r in enumerate(rows):
        payload = {}
        if r['descripcion']:
            payload['descripcion'] = r['descripcion']
        if r['tareas_explicitas']:
            payload['tareas_explicitas'] = r['tareas_explicitas']
        if r['mision_rol']:
            payload['mision_rol'] = r['mision_rol']
        if r['decision_metodo']:
            payload['decision_metodo'] = r['decision_metodo']
        if r['regla_aplicada']:
            payload['regla_aplicada'] = r['regla_aplicada']

        if not payload:
            skipped += 1
            continue

        try:
            client.table('ofertas_dashboard').update(payload).eq(
                'id_oferta', str(r['id_oferta'])
            ).execute()
            ok += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error #{errors} id={r['id_oferta']}: {e}", flush=True)

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{i+1}/{total}] {ok} ok, {errors} err, {skipped} skip "
                f"| {rate:.0f}/s | ETA {eta/60:.1f}min",
                flush=True,
            )

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed/60:.1f}min: {ok} updated, {errors} errors, {skipped} skipped", flush=True)
    db.close()


if __name__ == "__main__":
    main()
