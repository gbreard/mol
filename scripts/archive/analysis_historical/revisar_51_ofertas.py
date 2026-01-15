# -*- coding: utf-8 -*-
"""Revisión rápida de las 51 ofertas nuevas - detectar problemas obvios."""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
GOLD_SET_100_PATH = Path(__file__).parent.parent / "database" / "gold_set_nlp_100_ids.json"

with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
    gold_set_orig = json.load(f)
ids_originales = set(str(item['id_oferta']) for item in gold_set_orig)

with open(GOLD_SET_100_PATH, 'r', encoding='utf-8') as f:
    ids_total = json.load(f)

# Convertir a string para comparación correcta
ids_total_str = [str(x) for x in ids_total]
ids_nuevos = [id for id in ids_total_str if id not in ids_originales]
print(f"IDs originales: {len(ids_originales)}, Total: {len(ids_total)}, Nuevos: {len(ids_nuevos)}")

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

print("=" * 80)
print("REVISION DE 51 OFERTAS NUEVAS - DETECTANDO PROBLEMAS")
print("=" * 80)

# Get all 51 with key fields
placeholders = ','.join(['?' for _ in ids_nuevos])
cur.execute(f'''
    SELECT n.id_oferta, n.titulo_limpio, n.area_funcional, n.localidad,
           o.localizacion, n.nivel_seniority, n.tareas_explicitas
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
''', ids_nuevos)

issues = []
all_rows = cur.fetchall()

for row in all_rows:
    id_o, titulo, area, localidad, loc_orig, seniority, tareas = row
    titulo = titulo or ''
    area = area or ''
    titulo_lower = titulo.lower()
    area_lower = area.lower()

    # 1. Técnico/Mecánico/Electro/Ingeniero -> no debería ser RRHH
    if any(x in titulo_lower for x in ['tecnic', 'mecan', 'electro', 'ingenier']) and 'recursos' in area_lower:
        issues.append(('AREA_MAL', id_o, titulo[:45], f"area={area}"))

    # 2. Contador/Contable -> no debería ser Ventas
    if any(x in titulo_lower for x in ['contab', 'contador']) and 'venta' in area_lower:
        issues.append(('AREA_MAL', id_o, titulo[:45], f"area={area}"))

    # 3. Localidad como array JSON
    if localidad and localidad.startswith('['):
        issues.append(('LOC_ARRAY', id_o, titulo[:45], localidad[:60]))

    # 4. Localidad vacía cuando hay localizacion de scraping
    if (not localidad or localidad == '') and loc_orig:
        issues.append(('LOC_VACIA', id_o, titulo[:45], f"scraping: {loc_orig}"))

# Print issues
if issues:
    print(f"\n[!] PROBLEMAS DETECTADOS: {len(issues)}")
    print("-" * 80)
    for tipo, id_o, titulo, detalle in issues:
        print(f"[{tipo}] {id_o} | {titulo}")
        print(f"         -> {detalle}")
        print()
else:
    print("\n[OK] No se detectaron problemas obvios.")

# Summary by area
print("\n" + "=" * 80)
print("DISTRIBUCION POR AREA FUNCIONAL:")
print("-" * 80)
areas = {}
for row in all_rows:
    area = row[2] or 'Sin area'
    areas[area] = areas.get(area, 0) + 1

for area, count in sorted(areas.items(), key=lambda x: -x[1]):
    print(f"  {count:2d} - {area}")

# Summary by seniority
print("\n" + "=" * 80)
print("DISTRIBUCION POR SENIORITY:")
print("-" * 80)
seniorities = {}
for row in all_rows:
    sen = row[5] or 'Sin seniority'
    seniorities[sen] = seniorities.get(sen, 0) + 1

for sen, count in sorted(seniorities.items(), key=lambda x: -x[1]):
    print(f"  {count:2d} - {sen}")

# Tareas coverage
tareas_count = sum(1 for row in all_rows if row[6] and len(row[6]) > 10)
print(f"\nTareas explicitas con contenido: {tareas_count}/{len(all_rows)} ({100*tareas_count/len(all_rows):.0f}%)")

conn.close()
