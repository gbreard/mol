#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick check of v8.1 skills extraction"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=" * 70)
print("ANALISIS NLP v8.1 - SKILLS EXTRAIDOS")
print("=" * 70)

# Stats
c.execute("SELECT nlp_version, COUNT(*) FROM validacion_v7 GROUP BY nlp_version")
print("\nVersiones NLP en validacion_v7:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} ofertas")

# Sample v8.1 skills
c.execute("""
    SELECT v.id_oferta, v.titulo, v.resultado_capa1_verificado
    FROM validacion_v7 v
    WHERE v.nlp_version = '8.1.0'
    ORDER BY v.id DESC
    LIMIT 10
""")

print("\n" + "-" * 70)
print("EJEMPLOS v8.1 (ultimas 10):")
print("-" * 70)

total_skills = 0
ofertas_con_skills = 0

for row in c.fetchall():
    id_oferta, titulo, nlp_json = row
    print(f"\nID: {id_oferta}")
    print(f"Titulo: {str(titulo)[:65]}...")

    if nlp_json:
        try:
            data = json.loads(nlp_json)
            skills = data.get('skills_tecnicas_list', [])
            if isinstance(skills, str):
                skills = json.loads(skills) if skills else []

            if skills:
                ofertas_con_skills += 1
                total_skills += len(skills)

            vals = []
            for s in skills[:6]:
                if isinstance(s, dict):
                    vals.append(s.get('valor', str(s)))
                else:
                    vals.append(str(s))

            print(f"Skills tecnicos ({len(skills)}): {vals}")
        except Exception as e:
            print(f"Error parsing: {e}")

print("\n" + "=" * 70)
print("RESUMEN:")
print(f"  Ofertas v8.1 con skills tecnicos: {ofertas_con_skills}/10")
print(f"  Total skills en muestra: {total_skills}")
print("=" * 70)

conn.close()
