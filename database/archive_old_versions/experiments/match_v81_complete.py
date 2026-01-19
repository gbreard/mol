#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Complete matching for v8.1 offers - Create records and run matching"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

print("="*70)
print("MATCHING COMPLETO PARA OFERTAS v8.1")
print("="*70)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get v8.1 IDs
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [str(r[0]) for r in c.fetchall()]
print(f"\n[1] IDs v8.1 encontrados: {len(ids_v81)}")

# Check existing matching records
placeholders = ','.join(['?'] * len(ids_v81))
c.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
existing = c.fetchone()[0]
print(f"    Ya tienen matching: {existing}")

# Step 1: Create records for those that don't exist
print(f"\n[2] Creando registros en ofertas_esco_matching...")
inserted = 0
for id_oferta in ids_v81:
    try:
        c.execute("""
            INSERT OR IGNORE INTO ofertas_esco_matching (
                id_oferta, match_method
            ) VALUES (?, 'v8.1_pending')
        """, (id_oferta,))
        if c.rowcount > 0:
            inserted += 1
    except Exception as e:
        print(f"    Error inserting {id_oferta}: {e}")

conn.commit()
print(f"    Registros creados: {inserted}")

# Check total now
c.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
total_now = c.fetchone()[0]
print(f"    Total en matching: {total_now}")

conn.close()

# Step 2: Run matching
print(f"\n[3] Ejecutando matching multicriteria...")
from match_ofertas_multicriteria import MultiCriteriaMatcher
matcher = MultiCriteriaMatcher()
matcher.ejecutar()

# Step 3: Show v8.1 results
print("\n" + "="*70)
print("RESULTADOS v8.1 POST-MATCHING")
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
    WHERE id_oferta IN ({placeholders}) AND score_final_ponderado IS NOT NULL
""", ids_v81)

row = c.fetchone()
if row and row[0] > 0:
    total, avg_score, avg_titulo, avg_skills, avg_desc, confirmados, revision, rechazados = row

    print(f"\nTotal v8.1 procesadas: {total}/{len(ids_v81)}")
    print(f"\n  Scores promedio:")
    print(f"    Score FINAL:       {avg_score:.3f}")
    print(f"    Score Titulo:      {avg_titulo:.3f}")
    print(f"    Score Skills:      {avg_skills:.3f}")
    print(f"    Score Descripcion: {avg_desc:.3f}")

    print(f"\n  Distribucion:")
    print(f"    CONFIRMADOS (>75%): {confirmados} ({confirmados/total*100:.1f}%)")
    print(f"    REVISION (50-75%):  {revision} ({revision/total*100:.1f}%)")
    print(f"    RECHAZADOS (<50%):  {rechazados} ({rechazados/total*100:.1f}%)")

    # Comparison table with v8.0 baseline
    print("\n" + "="*70)
    print("COMPARACION v8.0 vs v8.1 (después del fix descripcion_utf8)")
    print("="*70)
    print(f"""
| Métrica              | v8.0 (121) | v8.1 ({total})   | Diff     |
|----------------------|------------|-------------|----------|
| Score promedio       | 0.513      | {avg_score:.3f}       | {avg_score-0.513:+.3f}    |
| Score Titulo         | 0.616      | {avg_titulo:.3f}       | {avg_titulo-0.616:+.3f}    |
| Score Skills         | 0.472      | {avg_skills:.3f}       | {avg_skills-0.472:+.3f}    |
| Score Descripcion    | 0.269      | {avg_desc:.3f}       | {avg_desc-0.269:+.3f}    |
|----------------------|------------|-------------|----------|
| CONFIRMADOS (>75%)   | 0.8%       | {confirmados/total*100:.1f}%       | {confirmados/total*100-0.8:+.1f}pp    |
| REVISION (50-75%)    | 60.3%      | {revision/total*100:.1f}%      | {revision/total*100-60.3:+.1f}pp   |
| RECHAZADOS (<50%)    | 38.8%      | {rechazados/total*100:.1f}%      | {rechazados/total*100-38.8:+.1f}pp   |
""")
else:
    print(f"No se encontraron resultados para v8.1")
    # Debug
    c.execute(f"SELECT id_oferta, score_final_ponderado FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders}) LIMIT 5", ids_v81)
    print("Debug - primeros 5 registros:")
    for r in c.fetchall():
        print(f"  {r}")

conn.close()
print("="*70)
