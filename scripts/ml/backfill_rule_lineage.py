#!/usr/bin/env python3
"""
M-09 + M-11: Backfill rule lineage.

For each rule in matching_rules_business.json:
1. Search training_pairs.json for pairs that reference the rule → training_pair_ids
2. Search _cambios_vXX keys for mentions of the rule → approximate date
3. Mark requiere_revision: true if no meaningful data found

Uso:
    python scripts/ml/backfill_rule_lineage.py
    python scripts/ml/backfill_rule_lineage.py --dry-run
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RULES_PATH = PROJECT_ROOT / "config" / "matching_rules_business.json"
TP_PATH = PROJECT_ROOT / "config" / "training_pairs.json"


def extract_cambios_info(rules: dict, rid: str) -> dict:
    """Search _cambios_vXX keys for mentions of a rule ID."""
    r_num = rid.split('_')[0] if '_' in rid else rid
    info = {}

    for key, value in rules.items():
        if not key.startswith('_cambios_') and not key.startswith('_changelog_'):
            continue
        text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        if r_num in text or rid in text:
            # Extract version number from key
            version_match = re.search(r'v?(\d+)', key)
            version = version_match.group(1) if version_match else key
            info['version_origen'] = f"v{version}"
            # Try to extract a snippet
            idx = text.find(r_num)
            if idx >= 0:
                snippet = text[max(0, idx-20):idx+60].strip()
                info['contexto'] = snippet[:100]
            break

    return info


def main():
    parser = argparse.ArgumentParser(description="M-09+M-11: Backfill rule lineage")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-09: Backfilling rule lineage (training pairs + cambios + requiere_revision)")
    print("=" * 70)

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

    total_rules = sum(1 for k, v in reglas.items() if isinstance(v, dict))
    had_linaje = sum(1 for k, v in reglas.items() if isinstance(v, dict) and v.get('_linaje'))
    updated_tp = 0
    updated_cambios = 0
    marked_revision = 0

    for rid, r in reglas.items():
        if not isinstance(r, dict):
            continue

        r_num = rid.split('_')[0] if '_' in rid else rid

        # Ensure _linaje exists
        if '_linaje' not in r:
            r['_linaje'] = {}

        linaje = r['_linaje']

        # 1. Training pair IDs
        tp_ids = rule_to_pairs.get(r_num, [])
        if tp_ids:
            linaje['training_pair_ids'] = tp_ids
            updated_tp += 1

        # 2. Extract from _cambios_vXX
        if not linaje.get('version_origen') and not linaje.get('reporte'):
            cambios_info = extract_cambios_info(rules, rid)
            if cambios_info:
                linaje.update(cambios_info)
                updated_cambios += 1

        # 3. Mark requiere_revision if still sparse
        has_meaningful = (
            linaje.get('nota') or
            linaje.get('justificacion') or
            linaje.get('issue_ids') or
            linaje.get('training_pair_ids') or
            linaje.get('reporte') or
            linaje.get('created_by')
        )
        if not has_meaningful:
            linaje['requiere_revision'] = True
            marked_revision += 1
        elif linaje.get('requiere_revision') and has_meaningful:
            del linaje['requiere_revision']

    now_has_linaje = sum(1 for k, v in reglas.items() if isinstance(v, dict) and v.get('_linaje'))

    print(f"Total reglas: {total_rules}")
    print(f"Ya tenían _linaje: {had_linaje}")
    print(f"Actualizadas con training_pair_ids: {updated_tp}")
    print(f"Actualizadas con info de _cambios: {updated_cambios}")
    print(f"Marcadas requiere_revision: {marked_revision}")
    print(f"Con _linaje después: {now_has_linaje}")

    if args.dry_run:
        print("\n[DRY-RUN] No se guarda.")
        return

    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {RULES_PATH}")


if __name__ == "__main__":
    main()
