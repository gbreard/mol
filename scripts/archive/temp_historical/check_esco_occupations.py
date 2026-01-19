#!/usr/bin/env python3
"""Buscar ocupaciones ESCO para casos problemáticos del matching."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))

print("=" * 60)
print("OCUPACIONES ESCO: Ventas vehículos/autos")
print("=" * 60)
cur = conn.execute('''
    SELECT esco_code, preferred_label_es, isco_code
    FROM esco_occupations
    WHERE preferred_label_es LIKE '%veh%'
       OR preferred_label_es LIKE '%auto%'
       OR preferred_label_es LIKE '%coche%'
       OR preferred_label_es LIKE '%concesion%'
    ORDER BY esco_code
''')
for row in cur:
    print(f"{row[0]} | {row[1]} | ISCO: {row[2]}")

print("\n" + "=" * 60)
print("OCUPACIONES ESCO: Vendedor")
print("=" * 60)
cur = conn.execute('''
    SELECT esco_code, preferred_label_es, isco_code
    FROM esco_occupations
    WHERE preferred_label_es LIKE '%vendedor%'
    ORDER BY esco_code
''')
for row in cur:
    print(f"{row[0]} | {row[1]} | ISCO: {row[2]}")

print("\n" + "=" * 60)
print("OCUPACIONES ESCO: Mantenimiento")
print("=" * 60)
cur = conn.execute('''
    SELECT esco_code, preferred_label_es, isco_code
    FROM esco_occupations
    WHERE preferred_label_es LIKE '%manten%'
       OR preferred_label_es LIKE '%manteni%'
    LIMIT 20
''')
for row in cur:
    print(f"{row[0]} | {row[1]} | ISCO: {row[2]}")

print("\n" + "=" * 60)
print("OFERTAS PROBLEMÁTICAS - Datos NLP")
print("=" * 60)
cur = conn.execute('''
    SELECT id, titulo_limpio, area_funcional, nivel_seniority, skills_tecnicas_list
    FROM ofertas_nlp
    WHERE titulo_limpio LIKE '%Vendedor%Auto%'
       OR titulo_limpio LIKE '%Operario%Manten%'
       OR titulo_limpio LIKE '%vendedor%auto%'
    LIMIT 10
''')
for row in cur:
    print(f"ID: {row[0]}")
    print(f"  Título: {row[1]}")
    print(f"  Área: {row[2]}")
    print(f"  Seniority: {row[3]}")
    print(f"  Skills: {row[4][:100] if row[4] else 'NULL'}...")
    print()

conn.close()
