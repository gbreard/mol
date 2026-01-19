#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix localidad/provincia usando datos del scraping (prioridad sobre LLM).
"""

import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Cargar Gold Set
    gold_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    ids = [str(x['id_oferta']) for x in gold_set]

    print(f"Actualizando localidad/provincia de {len(ids)} ofertas desde scraping...")
    print("-" * 70)

    cur = conn.cursor()
    cambios = 0

    for id_oferta in ids:
        # Obtener localizacion del scraping
        cur.execute('SELECT localizacion FROM ofertas WHERE id_oferta = ?', (id_oferta,))
        row = cur.fetchone()
        if not row or not row['localizacion']:
            continue

        localizacion = row['localizacion']
        partes = [p.strip() for p in localizacion.split(',')]

        if len(partes) >= 2:
            localidad_scraping = partes[0]
            provincia_scraping = partes[1]

            # Obtener valores actuales
            cur.execute('SELECT localidad, provincia FROM ofertas_nlp WHERE id_oferta = ?', (id_oferta,))
            nlp_row = cur.fetchone()
            if not nlp_row:
                continue

            localidad_actual = nlp_row['localidad']
            provincia_actual = nlp_row['provincia']

            # Solo actualizar si hay diferencia
            if localidad_actual != localidad_scraping or provincia_actual != provincia_scraping:
                cur.execute('''
                    UPDATE ofertas_nlp
                    SET localidad = ?, provincia = ?
                    WHERE id_oferta = ?
                ''', (localidad_scraping, provincia_scraping, id_oferta))
                cambios += 1
                if cambios <= 10:
                    print(f"  {id_oferta}:")
                    print(f"    localidad: {localidad_actual} -> {localidad_scraping}")
                    print(f"    provincia: {provincia_actual} -> {provincia_scraping}")

    conn.commit()
    conn.close()

    print()
    print(f"[OK] {cambios} ofertas actualizadas")

if __name__ == "__main__":
    main()
