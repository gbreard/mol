#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplica limpieza de skills a Gold Set 100 usando el postprocessor.
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
    pp = NLPPostprocessor(verbose=False)

    # Obtener skills actuales
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''
        SELECT id_oferta, skills_tecnicas_list, soft_skills_list
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    ''', ids)

    rows = c.fetchall()
    print(f"Ofertas a procesar: {len(rows)}")

    updates = []
    tecnicas_limpiadas = 0
    soft_limpiadas = 0

    for row in rows:
        id_oferta = row['id_oferta']
        tecnicas_antes = row['skills_tecnicas_list'] or ''
        soft_antes = row['soft_skills_list'] or ''

        # Aplicar limpieza
        data = {
            "skills_tecnicas_list": tecnicas_antes,
            "soft_skills_list": soft_antes
        }
        data = pp._limpiar_skills(data)

        tecnicas_despues = data.get("skills_tecnicas_list", "")
        soft_despues = data.get("soft_skills_list", "")

        cambio = False
        if tecnicas_despues != tecnicas_antes:
            tecnicas_limpiadas += 1
            cambio = True
        if soft_despues != soft_antes:
            soft_limpiadas += 1
            cambio = True

        if cambio:
            updates.append((tecnicas_despues, soft_despues, str(id_oferta)))

    print(f"\n[RESUMEN]")
    print(f"  skills_tecnicas_list modificadas: {tecnicas_limpiadas}")
    print(f"  soft_skills_list modificadas: {soft_limpiadas}")
    print(f"  Total registros a actualizar: {len(updates)}")

    if updates:
        print(f"\nActualizando BD...")
        c.executemany('''
            UPDATE ofertas_nlp
            SET skills_tecnicas_list = ?,
                soft_skills_list = ?
            WHERE id_oferta = ?
        ''', updates)
        conn.commit()
        print(f"  [OK] {len(updates)} registros actualizados")

    # Mostrar ejemplos
    print("\n" + "=" * 60)
    print("EJEMPLOS DE SKILLS LIMPIAS:")
    c.execute(f'''
        SELECT id_oferta, skills_tecnicas_list, soft_skills_list
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
          AND (skills_tecnicas_list IS NOT NULL OR soft_skills_list IS NOT NULL)
        LIMIT 5
    ''', ids)

    for row in c.fetchall():
        print(f"\n[{row['id_oferta']}]")
        if row['skills_tecnicas_list']:
            print(f"  TEC: {row['skills_tecnicas_list'][:80]}...")
        if row['soft_skills_list']:
            print(f"  SOFT: {row['soft_skills_list'][:80]}...")

    conn.close()

if __name__ == '__main__':
    main()
