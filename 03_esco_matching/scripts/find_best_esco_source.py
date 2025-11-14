# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from pathlib import Path

esco_dir = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data")

# Archivos a revisar
archivos = [
    "esco_con_isco.json",
    "esco_consolidado_con_isco.json",
    "esco_isco_completo.json",
    "esco_ocupaciones_completo.json"
]

print("=" * 80)
print("BUSCANDO MEJOR FUENTE DE DATOS ESCO CON CÓDIGOS ISCO")
print("=" * 80)

for archivo in archivos:
    path = esco_dir / archivo

    if not path.exists():
        print(f"\n❌ {archivo}: No existe")
        continue

    print(f"\n📄 {archivo}:")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"   Total entries: {len(data)}")

    if isinstance(data, dict):
        # Buscar campos ISCO
        sample_key = list(data.keys())[0] if data else None
        if sample_key:
            sample = data[sample_key]
            print(f"   Campos disponibles: {list(sample.keys())[:10]}")

            # Contar ocupaciones con ISCO
            isco_fields = ['isco_4d', 'codigo_isco_4d', 'isco', 'codigo_isco']
            for field in isco_fields:
                count = sum(1 for v in data.values() if v.get(field))
                if count > 0:
                    print(f"   ✅ Con '{field}': {count}")

            # Muestra
            items_with_isco = []
            for k, v in list(data.items())[:50]:
                for field in isco_fields:
                    if v.get(field):
                        items_with_isco.append((k, v, field))
                        break

            if items_with_isco:
                print(f"\n   📋 Muestra (primeras 3):")
                for k, v, field in items_with_isco[:3]:
                    label = v.get('label_es', v.get('label', 'N/A'))
                    isco_val = v.get(field)
                    print(f"      {label}: {field}={isco_val}")

print("\n" + "=" * 80)
