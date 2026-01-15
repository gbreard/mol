#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix sector_empresa usando reglas de correccion del postprocessor.
"""

import sqlite3
import json
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from nlp_postprocessor import NLPPostprocessor

def main():
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Cargar Gold Set
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    ids = [str(x['id_oferta']) for x in gold_set]

    print(f"Corrigiendo sector_empresa de {len(ids)} ofertas...")
    print("-" * 70)

    pp = NLPPostprocessor(verbose=False)
    cur = conn.cursor()
    cambios = 0

    for id_oferta in ids:
        # Obtener datos actuales
        cur.execute('''
            SELECT n.titulo_limpio, n.sector_empresa, o.descripcion
            FROM ofertas_nlp n
            JOIN ofertas o ON n.id_oferta = o.id_oferta
            WHERE n.id_oferta = ?
        ''', (id_oferta,))
        row = cur.fetchone()
        if not row:
            continue

        titulo_limpio = row['titulo_limpio'] or ''
        sector_actual = row['sector_empresa']
        descripcion = row['descripcion'] or ''

        if not sector_actual:
            continue

        # Aplicar correccion
        data = {'titulo_limpio': titulo_limpio, 'sector_empresa': sector_actual}
        data_corregido = pp._corregir_sector(data, descripcion)

        sector_nuevo = data_corregido.get('sector_empresa')

        if sector_nuevo != sector_actual:
            cur.execute('''
                UPDATE ofertas_nlp
                SET sector_empresa = ?
                WHERE id_oferta = ?
            ''', (sector_nuevo, id_oferta))
            cambios += 1
            print(f"  {id_oferta}: {sector_actual} -> {sector_nuevo}")
            print(f"    titulo: {titulo_limpio[:50]}")

    conn.commit()
    conn.close()

    print()
    print(f"[OK] {cambios} ofertas corregidas")

if __name__ == "__main__":
    main()
