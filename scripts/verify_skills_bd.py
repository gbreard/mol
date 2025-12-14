#!/usr/bin/env python3
"""Verificar skills guardadas en BD para caso Angular Senior"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("CASO ANGULAR SENIOR DESPUES DEL FIX")
print("=" * 60)

cursor.execute("""
    SELECT skills_tecnicas_list, soft_skills_list, tecnologias_list
    FROM ofertas_nlp
    WHERE id_oferta = '1117982053'
""")
row = cursor.fetchone()

if row:
    print("\n[skills_tecnicas_list]:")
    if row[0]:
        try:
            skills = json.loads(row[0])
            for s in skills:
                if isinstance(s, dict):
                    marca = "[regex]" if "[regex]" in s.get("texto_original", "") else ""
                    print(f"  - {s.get('valor', s)} {marca}")
                else:
                    print(f"  - {s}")
            print(f"\nTotal: {len(skills)} skills tecnicas")
        except Exception as e:
            print(f"  Error: {e}")
            print(f"  Raw: {row[0]}")
    else:
        print("  (vacio)")

    print("\n[soft_skills_list]:")
    if row[1]:
        try:
            soft = json.loads(row[1])
            for s in soft:
                if isinstance(s, dict):
                    marca = "[regex]" if "[regex]" in s.get("texto_original", "") else ""
                    print(f"  - {s.get('valor', s)} {marca}")
                else:
                    print(f"  - {s}")
            print(f"\nTotal: {len(soft)} soft skills")
        except Exception as e:
            print(f"  Error: {e}")
            print(f"  Raw: {row[1]}")
    else:
        print("  (vacio)")

    print("\n[tecnologias_list]:")
    if row[2]:
        try:
            tech = json.loads(row[2])
            for t in tech:
                if isinstance(t, dict):
                    print(f"  - {t.get('valor', t)}")
                else:
                    print(f"  - {t}")
        except Exception as e:
            print(f"  Error: {e}")
            print(f"  Raw: {row[2]}")
    else:
        print("  (vacio)")

print("\n" + "=" * 60)
print("COMPARATIVA ANTES/DESPUES")
print("=" * 60)
print("""
ANTES (solo LLM):
  skills_tecnicas_list: ["Angular", "Webpack"]  (2)
  soft_skills_list: None                        (0)

ESPERADO (LLM + regex):
  skills_tecnicas: Angular, Webpack + typescript, react, vue, svelte, seleccion  (7+)
  soft_skills: comunicacion, liderazgo, proactividad, flexibilidad, autonomia    (5+)
""")

conn.close()
