# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from pathlib import Path

path = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_isco_completo.json")

print("Checking esco_isco_completo.json...")

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Type: {type(data)}")
print(f"Total entries: {len(data)}")

if isinstance(data, dict):
    key = list(data.keys())[0]
    sample = data[key]
    print(f"\nSample entry type: {type(sample)}")
    print(f"Sample key: {key}")

    if isinstance(sample, dict):
        print(f"Sample keys: {list(sample.keys())}")
        print(f"\nSample data:")
        print(json.dumps({key: sample}, indent=2, ensure_ascii=False)[:500])

        # Count with ISCO
        with_isco = 0
        for k, v in data.items():
            if isinstance(v, dict):
                if v.get('isco_4d') or v.get('codigo_isco_4d') or v.get('isco') or v.get('codigo_isco'):
                    with_isco += 1

        print(f"\n\nEntries with some ISCO code: {with_isco}")
    elif isinstance(sample, str):
        print(f"Sample value: {sample}")
        print("\nThis appears to be a mapping, not occupation data")
