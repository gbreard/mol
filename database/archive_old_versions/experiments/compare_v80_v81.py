#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comparar matching v8.0 vs v8.1"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# IDs de v8.1
c.execute("SELECT CAST(id_oferta AS TEXT) FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [row[0] for row in c.fetchall()]

print('='*70)
print('COMPARACION MATCHING: NLP v8.0 vs v8.1')
print('='*70)
print(f'\nOfertas con NLP v8.1.0: {len(ids_v81)}')

# Stats para v8.1
if ids_v81:
    placeholders = ','.join(['?'] * len(ids_v81))
    c.execute(f'''
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
    ''', ids_v81)

    row = c.fetchone()
    total, avg_score, avg_titulo, avg_skills, avg_desc, confirmados, revision, rechazados = row

    print(f'\n[RESULTADOS MATCHING v8.1 ({total} ofertas con matching)]')
    print('-'*50)
    if avg_score:
        print(f'  Score FINAL promedio:    {avg_score:.3f}')
        print(f'  Score Titulo promedio:   {avg_titulo:.3f}')
        print(f'  Score Skills promedio:   {avg_skills:.3f}')
        print(f'  Score Descripcion prom:  {avg_desc:.3f}')

        print(f'\n  Distribucion:')
        print(f'    CONFIRMADOS (>75%):  {confirmados} ({confirmados/total*100:.1f}%)')
        print(f'    REVISION (50-75%):   {revision} ({revision/total*100:.1f}%)')
        print(f'    RECHAZADOS (<50%):   {rechazados} ({rechazados/total*100:.1f}%)')

        # Comparacion
        print('\n' + '='*70)
        print('TABLA COMPARATIVA v8.0 vs v8.1')
        print('='*70)

        diff_score = avg_score - 0.513
        pct_conf = confirmados/total*100 if total else 0
        pct_rev = revision/total*100 if total else 0
        pct_rech = rechazados/total*100 if total else 0

        print(f'''
| Metrica              | v8.0 (121) | v8.1 ({total})  | Diff     |
|----------------------|------------|------------|----------|
| Score promedio       | 0.513      | {avg_score:.3f}      | {diff_score:+.3f}    |
| Score Titulo         | 0.616      | {avg_titulo:.3f}      | {avg_titulo-0.616:+.3f}    |
| Score Skills         | 0.472      | {avg_skills:.3f}      | {avg_skills-0.472:+.3f}    |
| Score Descripcion    | 0.269      | {avg_desc:.3f}      | {avg_desc-0.269:+.3f}    |
|----------------------|------------|------------|----------|
| Confirmados (>75%)   | 0.8%       | {pct_conf:.1f}%      | {pct_conf-0.8:+.1f}pp    |
| Revision (50-75%)    | 60.3%      | {pct_rev:.1f}%     | {pct_rev-60.3:+.1f}pp   |
| Rechazados (<50%)    | 38.8%      | {pct_rech:.1f}%     | {pct_rech-38.8:+.1f}pp   |
''')

        # Conclusion
        if diff_score > 0:
            print(f'CONCLUSION: v8.1 MEJORA el score promedio en {diff_score*100:.1f}%')
        else:
            print(f'CONCLUSION: v8.1 tiene score similar a v8.0 ({diff_score*100:.1f}%)')
    else:
        print('  Sin datos de matching para ofertas v8.1')

conn.close()
