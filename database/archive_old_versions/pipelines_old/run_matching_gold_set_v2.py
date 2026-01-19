#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run matching v8.4 for Gold Set v2 (50 cases) and measure precision"""

import subprocess
import json
from pathlib import Path

base = Path(__file__).parent

# Load Gold Set v2 IDs
with open(base / 'gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)

ids = [str(c['id_oferta']) for c in gold_set]
print(f"Gold Set v2: {len(ids)} casos")

# Create IDs file for matching
ids_file = base / 'gold_set_ids.txt'
with open(ids_file, 'w') as f:
    for id_oferta in ids:
        f.write(f"{id_oferta}\n")
print(f"IDs guardados en: {ids_file}")

# Run matching for these specific IDs
print("\nEjecutando matching v8.2 con normalizacion argentina...")
cmd = [
    'python', str(base / 'match_ofertas_multicriteria.py'),
    '--ids-file', str(ids_file)
]

print(f"CMD: {' '.join(cmd[:3])} --ids-file <{len(ids)} IDs>")

result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(base))
print("\nSTDOUT:")
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)

print(f"\nReturn code: {result.returncode}")
