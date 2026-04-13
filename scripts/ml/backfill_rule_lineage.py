#!/usr/bin/env python3
"""
M-11: Backfill rule lineage with training pair IDs.

For each rule in matching_rules_business.json, search training_pairs.json
for pairs that reference that rule → add training_pair_id to _linaje.

Uso:
    python scripts/ml/backfill_rule_lineage.py
    python scripts/ml/backfill_rule_lineage.py --dry-run
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RULES_PATH = PROJECT_ROOT / "config" / "matching_rules_business.json"
TP_PATH = PROJECT_ROOT / "config" / "training_pairs.json"


def main():
    parser = argparse.ArgumentParser(description="M-11: Backfill rule lineage")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-11: Backfilling rule lineage with training pair IDs")
    print("=" * 55)

    rules = json.loads(RULES_PATH.read_text(encoding='utf-8'))
    reglas = rules.get('reglas_forzar_isco', {})
    tp = json.loads(TP_PATH.read_text(encoding='utf-8'))
    pares = tp.get('pares', [])

    # Build index: rule_id → list of training pair indices
    rule_to_pairs = defaultdict(list)
    for i, p in enumerate(pares):
        for r in p.get('reglas_generadas', []):
            tp_id = f"TP-{i:03d}"
            rule_to_pairs[r].append(tp_id)

    print(f"Reglas en config: {len(reglas)}")
    print(f"Reglas referenciadas en training pairs: {len(rule_to_pairs)}")

    updated = 0
    for rid, r in reglas.items():
        if not isinstance(r, dict):
            continue

        # Extract the R-number from rule ID (e.g., R23_responsable_deposito → R23)
        r_num = rid.split('_')[0] if '_' in rid else rid

        tp_ids = rule_to_pairs.get(r_num, [])
        if not tp_ids:
            continue

        # Ensure _linaje exists
        if '_linaje' not in r:
            r['_linaje'] = {}

        r['_linaje']['training_pair_ids'] = tp_ids
        updated += 1

    print(f"Reglas actualizadas con training_pair_ids: {updated}")

    if args.dry_run:
        print("[DRY-RUN] No se guarda.")
        # Show samples
        for rid, r in reglas.items():
            if not isinstance(r, dict):
                continue
            tp_ids = r.get('_linaje', {}).get('training_pair_ids')
            if tp_ids:
                print(f"  {rid}: {tp_ids}")
                if updated > 5:
                    break
        return

    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {RULES_PATH}")


if __name__ == "__main__":
    main()
