#!/usr/bin/env python3
"""
M-10: Sincronizar Gold Set desde Supabase a JSON local.

Lee tabla gold_set de Supabase y genera database/gold_set_manual_v2.json
en formato compatible con test_gold_set_manual.py.

Uso:
    python scripts/sync_gold_set.py
    python scripts/sync_gold_set.py --dry-run
"""

import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"


def main():
    parser = argparse.ArgumentParser(description="M-10: Sync Gold Set from Supabase")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-10: Sincronizando Gold Set desde Supabase")
    print("=" * 50)

    config_path = PROJECT_ROOT / "config" / "supabase_config.json"
    config = json.loads(config_path.read_text())
    from supabase import create_client
    client = create_client(config['url'], config['service_role_key'])

    result = client.table('gold_set').select(
        'id_oferta,esco_ok,isco_esperado,esco_esperado,tipo_error,comentario'
    ).eq('activo', True).order('id').execute()

    # Convert to legacy format (compatible with test_gold_set_manual.py)
    gold_set = []
    for row in (result.data or []):
        entry = {
            "id_oferta": row['id_oferta'],
            "esco_ok": row['esco_ok'],
        }
        if row.get('tipo_error'):
            entry["tipo_error"] = row['tipo_error']
        if row.get('comentario'):
            entry["comentario"] = row['comentario']
        if row.get('esco_esperado'):
            entry["esco_esperado"] = row['esco_esperado']
        if row.get('isco_esperado'):
            entry["isco_esperado"] = row['isco_esperado']
        gold_set.append(entry)

    print(f"Supabase: {len(gold_set)} casos activos")
    ok = sum(1 for g in gold_set if g['esco_ok'])
    err = sum(1 for g in gold_set if not g['esco_ok'])
    print(f"  Correctos: {ok}, Errores: {err}")

    # Diff with existing
    if OUTPUT_PATH.exists():
        existing = json.loads(OUTPUT_PATH.read_text(encoding='utf-8'))
        existing_ids = set(g['id_oferta'] for g in existing)
        new_ids = set(g['id_oferta'] for g in gold_set)
        added = new_ids - existing_ids
        removed = existing_ids - new_ids
        if added:
            print(f"  Nuevos: {len(added)} ({', '.join(list(added)[:5])}...)")
        if removed:
            print(f"  Removidos: {len(removed)} ({', '.join(list(removed)[:5])}...)")
        if not added and not removed:
            print(f"  Sin cambios en IDs (mismos {len(existing_ids)} casos)")
    else:
        print(f"  Archivo local no existe, se creará nuevo")

    # M-10 P2: Fetch skills per oferta
    skills_result = client.table('gold_set_skills').select(
        'id_oferta,skill_label'
    ).order('id_oferta').execute()

    skills_by_oferta = {}
    for row in (skills_result.data or []):
        oid = row['id_oferta']
        skills_by_oferta.setdefault(oid, [])
        skills_by_oferta[oid].append(row['skill_label'])

    ofertas_with_skills = sum(1 for g in gold_set if g['id_oferta'] in skills_by_oferta)
    total_skills = sum(len(v) for v in skills_by_oferta.values())
    print(f"  Skills: {total_skills} en {ofertas_with_skills} ofertas")

    # Add skills_esperadas to each entry
    for entry in gold_set:
        oid = entry['id_oferta']
        if oid in skills_by_oferta:
            entry['skills_esperadas'] = skills_by_oferta[oid]

    if args.dry_run:
        print("[DRY-RUN] No se escribe archivo.")
        return

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(gold_set, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
