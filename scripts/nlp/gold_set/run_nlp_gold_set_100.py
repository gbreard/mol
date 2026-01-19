# -*- coding: utf-8 -*-
"""Ejecuta NLP v11 sobre los 100 IDs del Gold Set."""
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Cargar IDs
ids_path = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
with open(ids_path) as f:
    ids = json.load(f)

print(f"IDs a procesar: {len(ids)}")

# Ejecutar NLP v11
cmd = [
    sys.executable,
    str(BASE_DIR / "database" / "process_nlp_from_db_v11.py"),
    "--ids", ",".join(ids),
    "--verbose"
]

print(f"Ejecutando: {' '.join(cmd[:3])} --ids <{len(ids)} IDs> --verbose")
subprocess.run(cmd)
