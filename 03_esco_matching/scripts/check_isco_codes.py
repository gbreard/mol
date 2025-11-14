# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from pathlib import Path

# Cargar datos consolidados
esco_path = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_consolidado_con_isco.json")

with open(esco_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Checking ISCO code coverage...")
print(f"Total occupations: {len(data)}")

with_4d = sum(1 for v in data.values() if v.get('codigo_isco_4d'))
with_2d = sum(1 for v in data.values() if v.get('codigo_isco_2d'))
without_isco = sum(1 for v in data.values() if not v.get('codigo_isco_4d'))

print(f"With ISCO 4D: {with_4d}")
print(f"With ISCO 2D: {with_2d}")
print(f"Without ISCO: {without_isco}")

print("\nSample with ISCO 4D codes:")
items_with_isco = [(k,v) for k,v in data.items() if v.get('codigo_isco_4d')]
for k,v in items_with_isco[:5]:
    print(f"  {v.get('label_es')}: {v.get('codigo_isco_4d')}")

print("\nSample WITHOUT ISCO codes:")
items_without = [(k,v) for k,v in data.items() if not v.get('codigo_isco_4d')]
for k,v in items_without[:5]:
    print(f"  {v.get('label_es')}: {v.get('codigo_isco')}")
