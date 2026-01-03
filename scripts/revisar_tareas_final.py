#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Revision FINAL de tareas_explicitas del Gold Set 100"""

import sqlite3
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(__file__).parent.parent

with open(base / 'database/gold_set_nlp_100_ids.json', 'r', encoding='utf-8') as f:
    ids = json.load(f)

conn = sqlite3.connect(base / 'database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
placeholders = ','.join(['?' for _ in ids])

# =====================================================
# 1. Ofertas CON tareas
# =====================================================
print('=' * 80)
print('OFERTAS CON TAREAS EXPLICITAS (83/100)')
print('=' * 80)

c.execute(f'''
    SELECT n.id_oferta, o.titulo, n.tareas_explicitas
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
      AND n.tareas_explicitas IS NOT NULL
      AND n.tareas_explicitas != ''
    ORDER BY n.id_oferta
''', ids)

con_tareas = c.fetchall()
for i, row in enumerate(con_tareas, 1):
    titulo = (row['titulo'] or '')[:45]
    tareas = (row['tareas_explicitas'] or '')[:120]
    # Limpiar para display
    tareas = tareas.replace('\n', ' ').replace('\r', '')
    print(f"{i:2}. [{row['id_oferta']}] {titulo}")
    print(f"    -> {tareas}...")
    print()

# =====================================================
# 2. Ofertas SIN tareas
# =====================================================
print('\n' + '=' * 80)
print('OFERTAS SIN TAREAS EXPLICITAS (17/100)')
print('=' * 80)

c.execute(f'''
    SELECT n.id_oferta, o.titulo, substr(o.descripcion, 1, 400) as desc
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
      AND (n.tareas_explicitas IS NULL OR n.tareas_explicitas = '')
    ORDER BY n.id_oferta
''', ids)

sin_tareas = c.fetchall()
for i, row in enumerate(sin_tareas, 1):
    titulo = (row['titulo'] or '')[:50]
    desc = (row['desc'] or '').replace('\n', ' ').replace('\r', '')
    desc = ''.join(c if ord(c) < 128 else ' ' for c in desc)[:200]
    print(f"\n{i:2}. [{row['id_oferta']}] {titulo}")
    print(f"    DESC: {desc}...")

# =====================================================
# 3. Resumen
# =====================================================
print('\n' + '=' * 80)
print('RESUMEN COBERTURA TAREAS')
print('=' * 80)
print(f"  CON TAREAS: {len(con_tareas)}/100 ({len(con_tareas)}%)")
print(f"  SIN TAREAS: {len(sin_tareas)}/100 ({len(sin_tareas)}%)")

# Analizar los sin tareas
print("\nANALISIS OFERTAS SIN TAREAS:")
print("  - Vendedor/Comercial (sin tareas explicitas): ~5")
print("  - Operarios/Produccion (descripcion general): ~4")
print("  - Otros (requisitos > tareas): ~8")
print("\n  NOTA: Estas ofertas tienen descripciones genericas")
print("  sin frases como 'sera responsable de' o 'funciones:'")

conn.close()
