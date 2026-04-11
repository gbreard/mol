#!/usr/bin/env python3
"""
M-11: Tag training pairs with generated rules.

Parses correccion.solucion_aplicada for rule IDs (R\d+) and adds
reglas_generadas field to each training pair.

Uso:
    python scripts/ml/tag_training_pairs_rules.py
    python scripts/ml/tag_training_pairs_rules.py --dry-run
"""

import json
import re
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TP_PATH = PROJECT_ROOT / "config" / "training_pairs.json"

RULE_PATTERN = re.compile(r'R(\d+)')
RULE_RANGE_PATTERN = re.compile(r'R(\d+)\s*[-–]\s*R(\d+)')


def extract_rules(text: str) -> list:
    """Extract rule IDs from text like 'Reglas R247-R259 + fix R57'."""
    if not text:
        return []

    rules = set()

    # First extract ranges (R247-R259)
    for m in RULE_RANGE_PATTERN.finditer(text):
        start, end = int(m.group(1)), int(m.group(2))
        for i in range(start, end + 1):
            rules.add(f"R{i}")

    # Then extract individual rules
    for m in RULE_PATTERN.finditer(text):
        rules.add(f"R{m.group(1)}")

    return sorted(rules, key=lambda r: int(r[1:]))


def main():
    parser = argparse.ArgumentParser(description="M-11: Tag training pairs with rules")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-11: Tagging training pairs with generated rules")
    print("=" * 55)

    tp = json.loads(TP_PATH.read_text(encoding='utf-8'))
    pares = tp.get('pares', [])
    print(f"Total pares: {len(pares)}")

    tagged = 0
    total_rules = set()

    for p in pares:
        correccion = p.get('correccion', {})
        sol = correccion.get('solucion_aplicada', '') if isinstance(correccion, dict) else ''
        rules = extract_rules(sol)

        if rules:
            p['reglas_generadas'] = rules
            tagged += 1
            total_rules.update(rules)
        else:
            p['reglas_generadas'] = []

    print(f"Pares con reglas: {tagged}")
    print(f"Reglas únicas referenciadas: {len(total_rules)}")
    if total_rules:
        sample = sorted(total_rules, key=lambda r: int(r[1:]))[:10]
        print(f"  Muestra: {sample}")

    if args.dry_run:
        print("[DRY-RUN] No se guarda.")
        return

    with open(TP_PATH, 'w', encoding='utf-8') as f:
        json.dump(tp, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {TP_PATH}")


if __name__ == "__main__":
    main()
