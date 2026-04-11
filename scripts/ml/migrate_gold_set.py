#!/usr/bin/env python3
"""
M-10: Migrar Gold Set de JSON local a tabla Supabase.

Lee database/gold_set_manual_v2.json (49 casos) e inserta
en la tabla gold_set de Supabase via RPC agregar_a_gold_set().

Uso:
    python scripts/ml/migrate_gold_set.py
    python scripts/ml/migrate_gold_set.py --dry-run
"""

import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"


def main():
    parser = argparse.ArgumentParser(description="M-10: Migrate Gold Set to Supabase")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-10: Migrando Gold Set a Supabase")
    print("=" * 50)

    # Load JSON
    gold_set = json.loads(GOLD_SET_PATH.read_text(encoding='utf-8'))
    print(f"Casos en JSON: {len(gold_set)}")

    if args.dry_run:
        ok = sum(1 for g in gold_set if g.get('esco_ok'))
        err = sum(1 for g in gold_set if not g.get('esco_ok'))
        print(f"  Correctos: {ok}, Errores: {err}")
        print("[DRY-RUN] No se insertan.")
        return

    # Connect
    config_path = PROJECT_ROOT / "config" / "supabase_config.json"
    config = json.loads(config_path.read_text())
    from supabase import create_client
    client = create_client(config['url'], config['service_role_key'])

    inserted = 0
    updated = 0
    errors = 0

    for g in gold_set:
        try:
            result = client.rpc('agregar_a_gold_set', {
                'p_id_oferta': str(g['id_oferta']),
                'p_esco_ok': g['esco_ok'],
                'p_isco_esperado': g.get('isco_esperado'),
                'p_esco_esperado': g.get('esco_esperado'),
                'p_tipo_error': g.get('tipo_error'),
                'p_comentario': g.get('comentario'),
                'p_agregado_por': 'migracion_inicial',
                'p_version_reglas': 'v5.16',
            }).execute()

            data = result.data
            if data and data.get('is_update'):
                updated += 1
            else:
                inserted += 1
        except Exception as e:
            errors += 1
            print(f"  ERROR {g['id_oferta']}: {e}")

    print(f"\nResultado: {inserted} insertados, {updated} actualizados, {errors} errores")

    # Verify
    stats = client.rpc('get_gold_set_stats').execute()
    print(f"Stats post-migración: {json.dumps(stats.data, indent=2)}")


if __name__ == "__main__":
    main()
