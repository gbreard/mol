#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplica limpieza de tareas a Gold Set 100 usando el postprocessor.
"""

import sys
import json
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(__file__).parent.parent
sys.path.insert(0, str(base / "database"))

from nlp_postprocessor import NLPPostprocessor

def main():
    # Cargar IDs Gold Set
    with open(base / 'database/gold_set_nlp_100_ids.json', 'r', encoding='utf-8') as f:
        ids = json.load(f)

    print(f"Gold Set: {len(ids)} ofertas")
    print("=" * 60)

    # Conectar BD
    conn = sqlite3.connect(base / "database" / "bumeran_scraping.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Inicializar postprocessor
    pp = NLPPostprocessor(verbose=True)

    # Obtener tareas actuales
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''
        SELECT id_oferta, tareas_explicitas
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
          AND tareas_explicitas IS NOT NULL
          AND tareas_explicitas != ''
    ''', ids)

    rows = c.fetchall()
    print(f"Ofertas con tareas: {len(rows)}")

    updates = []
    limpiadas = 0

    for row in rows:
        id_oferta = row['id_oferta']
        tareas_antes = row['tareas_explicitas']

        # Aplicar limpieza
        data = {"tareas_explicitas": tareas_antes}
        data = pp._limpiar_tareas(data)
        tareas_despues = data.get("tareas_explicitas", "")

        if tareas_despues != tareas_antes:
            limpiadas += 1
            updates.append((tareas_despues, str(id_oferta)))

    print(f"\n[RESUMEN]")
    print(f"  Tareas modificadas: {limpiadas}/{len(rows)}")

    if updates:
        print(f"\nActualizando BD...")
        c.executemany('''
            UPDATE ofertas_nlp
            SET tareas_explicitas = ?
            WHERE id_oferta = ?
        ''', updates)
        conn.commit()
        print(f"  [OK] {len(updates)} registros actualizados")

    conn.close()

if __name__ == '__main__':
    main()
