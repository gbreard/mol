#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Execute matching for v8.1 offers specifically - Imports from main module"""

import sqlite3
import json
from pathlib import Path
from tqdm import tqdm

# Import from main matching module
import sys
sys.path.insert(0, str(Path(__file__).parent))

from match_ofertas_multicriteria import MultiCriteriaMatcher

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

print("="*70)
print("MATCHING PARA OFERTAS v8.1 (67 ofertas)")
print("="*70)

# Get v8.1 IDs
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [str(r[0]) for r in c.fetchall()]
print(f"IDs v8.1 a procesar: {len(ids_v81)}")

# Check how many already have matching
placeholders = ','.join(['?'] * len(ids_v81))
c.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
existing = c.fetchone()[0]
print(f"Ya tienen matching: {existing}")

if existing > 0:
    print("Borrando matching existente...")
    c.execute(f"DELETE FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
    conn.commit()
    print(f"Eliminados: {c.rowcount}")

conn.close()

# Now run full matcher (it will process all but we only care about v8.1)
print("\nEjecutando matcher completo...")
matcher = MultiCriteriaMatcher()
matcher.ejecutar()

# Check results for v8.1 specifically
print("\n" + "="*70)
print("RESULTADOS v8.1")
print("="*70)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(f"""
    SELECT
        COUNT(*) as total,
        AVG(score_final_ponderado) as avg_score,
        AVG(score_titulo) as avg_titulo,
        AVG(score_skills) as avg_skills,
        AVG(score_descripcion) as avg_desc,
        SUM(CASE WHEN score_final_ponderado >= 0.75 THEN 1 ELSE 0 END) as confirmados,
        SUM(CASE WHEN score_final_ponderado >= 0.50 AND score_final_ponderado < 0.75 THEN 1 ELSE 0 END) as revision,
        SUM(CASE WHEN score_final_ponderado < 0.50 THEN 1 ELSE 0 END) as rechazados
    FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders})
""", ids_v81)

row = c.fetchone()
if row and row[0] > 0:
    total, avg_score, avg_titulo, avg_skills, avg_desc, confirmados, revision, rechazados = row
    print(f"\nTotal v8.1 con matching: {total}")
    print(f"Score promedio: {avg_score:.3f}")
    print(f"Score titulo: {avg_titulo:.3f}")
    print(f"Score skills: {avg_skills:.3f}")
    print(f"Score descripcion: {avg_desc:.3f}")
    print(f"\nDistribucion:")
    print(f"  CONFIRMADOS: {confirmados} ({confirmados/total*100:.1f}%)")
    print(f"  REVISION: {revision} ({revision/total*100:.1f}%)")
    print(f"  RECHAZADOS: {rechazados} ({rechazados/total*100:.1f}%)")
else:
    print("No se encontraron resultados para v8.1")

conn.close()
