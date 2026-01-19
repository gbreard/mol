# -*- coding: utf-8 -*-
"""Verificar que tareas estan limpias."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

print("VERIFICACION DE TAREAS LIMPIAS")
print("=" * 60)

# Contar tareas con formato JSON vs texto
c.execute("""
    SELECT
        SUM(CASE WHEN tareas_explicitas LIKE '[{%' THEN 1 ELSE 0 END) as json_format,
        SUM(CASE WHEN tareas_explicitas NOT LIKE '[{%' AND tareas_explicitas IS NOT NULL THEN 1 ELSE 0 END) as text_format,
        SUM(CASE WHEN tareas_explicitas IS NULL OR tareas_explicitas = '' THEN 1 ELSE 0 END) as empty
    FROM ofertas_nlp
    WHERE nlp_version = '10.0.0'
""")
row = c.fetchone()
print(f"\nFormato JSON (sin limpiar): {row[0]}")
print(f"Formato texto (limpio): {row[1]}")
print(f"Sin tareas: {row[2]}")

# Mostrar ejemplos
print("\n" + "-" * 60)
print("EJEMPLOS DE TAREAS LIMPIAS:")
print("-" * 60)

c.execute("""
    SELECT id_oferta, tareas_explicitas
    FROM ofertas_nlp
    WHERE nlp_version = '10.0.0'
    AND tareas_explicitas IS NOT NULL
    AND tareas_explicitas != ''
    LIMIT 5
""")
for row in c.fetchall():
    tareas = row[1][:150] + "..." if len(row[1]) > 150 else row[1]
    print(f"\nID {row[0]}:")
    print(f"  {tareas}")

conn.close()
