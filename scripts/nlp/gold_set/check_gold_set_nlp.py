# -*- coding: utf-8 -*-
"""Verificar estado NLP del Gold Set"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# IDs del Gold Set (muestra)
gold_ids = [
    '1118026700', '1118026729', '1118027941', '1118028027',
    '1117984105', '1118018714', '1117995368', '1117977340'
]

print("=" * 90)
print("ESTADO NLP GOLD SET - VERIFICACION POSTPROCESSOR")
print("=" * 90)

campos_vacios = {"provincia": 0, "localidad": 0, "modalidad": 0, "nivel_seniority": 0}

for id_oferta in gold_ids:
    cursor.execute('''
        SELECT provincia, localidad, modalidad, nivel_seniority,
               experiencia_min_anios, titulo_limpio, area_funcional
        FROM ofertas_nlp WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cursor.fetchone()

    print(f"\nID {id_oferta}:")
    if row:
        provincia, localidad, modalidad, seniority, exp_min, titulo_limpio, area = row

        # Contar vacios
        if not provincia: campos_vacios["provincia"] += 1
        if not localidad: campos_vacios["localidad"] += 1
        if not modalidad: campos_vacios["modalidad"] += 1
        if not seniority: campos_vacios["nivel_seniority"] += 1

        print(f"  provincia: {provincia or 'NULL'}")
        print(f"  localidad: {localidad or 'NULL'}")
        print(f"  modalidad: {modalidad or 'NULL'}")
        print(f"  nivel_seniority: {seniority or 'NULL'}")
        print(f"  experiencia_min: {exp_min}")
        print(f"  area_funcional: {area or 'NULL'}")
        print(f"  titulo_limpio: {(titulo_limpio[:40] + '...') if titulo_limpio else 'NULL'}")
    else:
        print("  NO ENCONTRADO en ofertas_nlp")

print("\n" + "=" * 90)
print("RESUMEN CAMPOS VACIOS:")
for campo, count in campos_vacios.items():
    pct = count / len(gold_ids) * 100
    estado = "OK" if pct < 20 else "REVISAR"
    print(f"  {campo}: {count}/{len(gold_ids)} vacios ({pct:.0f}%) - {estado}")

conn.close()
