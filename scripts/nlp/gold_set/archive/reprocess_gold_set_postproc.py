#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Re-procesa Gold Set 100 con postprocessor actualizado.
Mide mejora en cobertura de tareas_explicitas y sector_empresa.
"""

import sys
import json
import sqlite3
from pathlib import Path

base = Path(__file__).parent.parent
sys.path.insert(0, str(base / "database"))

from nlp_postprocessor import NLPPostprocessor

def main():
    # Cargar IDs Gold Set
    gold_set_file = base / "database" / "gold_set_nlp_100_ids.json"
    if not gold_set_file.exists():
        gold_set_file = base / "database" / "gold_set_manual_v2.json"
        with open(gold_set_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ids = [str(x['id_oferta']) for x in data]
    else:
        with open(gold_set_file, 'r', encoding='utf-8') as f:
            ids = json.load(f)

    print(f"Gold Set: {len(ids)} ofertas")
    print("=" * 60)

    # Conectar BD
    conn = sqlite3.connect(base / "database" / "bumeran_scraping.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Medir cobertura ANTES
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN tareas_explicitas IS NOT NULL AND tareas_explicitas != '' THEN 1 ELSE 0 END) as con_tareas,
            SUM(CASE WHEN sector_empresa IS NOT NULL AND sector_empresa != '' THEN 1 ELSE 0 END) as con_sector
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    row = c.fetchone()
    total = row['total']
    tareas_antes = row['con_tareas']
    sector_antes = row['con_sector']

    print(f"\n[ANTES]")
    print(f"  tareas_explicitas: {tareas_antes}/{total} ({100*tareas_antes/total:.0f}%)")
    print(f"  sector_empresa: {sector_antes}/{total} ({100*sector_antes/total:.0f}%)")

    # Inicializar postprocessor
    pp = NLPPostprocessor(verbose=False)

    # Obtener ofertas sin tareas o sin sector
    c.execute(f"""
        SELECT n.id_oferta, n.tareas_explicitas, n.sector_empresa, o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
          AND (n.tareas_explicitas IS NULL OR n.tareas_explicitas = ''
               OR n.sector_empresa IS NULL OR n.sector_empresa = '')
    """, ids)

    ofertas_procesar = c.fetchall()
    print(f"\n[PROCESANDO] {len(ofertas_procesar)} ofertas sin tareas o sector...")

    tareas_nuevas = 0
    sector_nuevos = 0
    updates = []

    for oferta in ofertas_procesar:
        id_oferta = oferta['id_oferta']
        descripcion = oferta['descripcion'] or ""

        # Construir data actual
        data = {
            "tareas_explicitas": oferta['tareas_explicitas'],
            "sector_empresa": oferta['sector_empresa']
        }

        # Aplicar extraccion
        data = pp._extract_tareas(descripcion, data)
        data = pp._extract_sector(descripcion, data)

        # Verificar cambios
        new_tareas = data.get('tareas_explicitas')
        new_sector = data.get('sector_empresa')

        if new_tareas and new_tareas != oferta['tareas_explicitas']:
            tareas_nuevas += 1
        if new_sector and new_sector != oferta['sector_empresa']:
            sector_nuevos += 1

        updates.append((new_tareas, new_sector, str(id_oferta)))

    # Actualizar BD
    print(f"\n[ACTUALIZANDO] {len(updates)} registros...")
    c.executemany("""
        UPDATE ofertas_nlp
        SET tareas_explicitas = COALESCE(?, tareas_explicitas),
            sector_empresa = COALESCE(?, sector_empresa)
        WHERE id_oferta = ?
    """, updates)
    conn.commit()

    # Medir cobertura DESPUES
    c.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN tareas_explicitas IS NOT NULL AND tareas_explicitas != '' THEN 1 ELSE 0 END) as con_tareas,
            SUM(CASE WHEN sector_empresa IS NOT NULL AND sector_empresa != '' THEN 1 ELSE 0 END) as con_sector
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    row = c.fetchone()
    tareas_despues = row['con_tareas']
    sector_despues = row['con_sector']

    print(f"\n[DESPUES]")
    print(f"  tareas_explicitas: {tareas_despues}/{total} ({100*tareas_despues/total:.0f}%)")
    print(f"  sector_empresa: {sector_despues}/{total} ({100*sector_despues/total:.0f}%)")

    print(f"\n[MEJORA]")
    print(f"  tareas: +{tareas_nuevas} ({tareas_antes} -> {tareas_despues})")
    print(f"  sector: +{sector_nuevos} ({sector_antes} -> {sector_despues})")

    print(f"\n[STATS POSTPROC]")
    print(f"  {pp.stats}")

    conn.close()
    print("\n[OK] Reprocesamiento completado")

if __name__ == '__main__':
    main()
