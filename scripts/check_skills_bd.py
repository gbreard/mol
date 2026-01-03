#!/usr/bin/env python3
"""
Verificar si skills via diccionario se guardaron en BD
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("VERIFICACION SKILLS EN BD")
print("=" * 60)

# Parte 1: Columnas de skills
print("\n[1] COLUMNAS DE SKILLS EN ofertas_nlp:")
cursor.execute("PRAGMA table_info(ofertas_nlp)")
cols = cursor.fetchall()
skill_cols = [c for c in cols if 'skill' in c[1].lower()]
for c in skill_cols:
    print(f"    {c[0]:3d} | {c[1]:35s} | {c[2]}")

# Parte 2: Columnas regex
print("\n[2] COLUMNAS CON 'regex' EN NOMBRE:")
regex_cols = [c for c in cols if 'regex' in c[1].lower()]
if regex_cols:
    for c in regex_cols:
        print(f"    {c[0]:3d} | {c[1]:35s} | {c[2]}")
else:
    print("    [NO HAY COLUMNAS _regex - Skills diccionario NO se guardan]")

# Parte 3: Caso Angular Senior
print("\n[3] CASO ANGULAR SENIOR (ID 1117982053):")
cursor.execute("""
    SELECT skills_tecnicas_list, soft_skills_list, tecnologias_list
    FROM ofertas_nlp
    WHERE id_oferta = '1117982053'
""")
row = cursor.fetchone()
if row:
    print(f"    skills_tecnicas_list: {row[0]}")
    print(f"    soft_skills_list:     {row[1]}")
    print(f"    tecnologias_list:     {row[2]}")

# Parte 4: Conteo Gold Set (usando JSON)
import json
gold_set_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"
with open(gold_set_path, 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
gold_ids = [item['id_oferta'] for item in gold_set]
placeholders = ','.join(['?' for _ in gold_ids])

print("\n[4] CONTEO SKILLS EN GOLD SET (49 ofertas):")
cursor.execute(f"""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN skills_tecnicas_list IS NOT NULL
                  AND skills_tecnicas_list != '[]'
                  AND skills_tecnicas_list != 'null' THEN 1 ELSE 0 END) as con_skills_tecnicas,
        SUM(CASE WHEN soft_skills_list IS NOT NULL
                  AND soft_skills_list != '[]'
                  AND soft_skills_list != 'null' THEN 1 ELSE 0 END) as con_soft_skills,
        SUM(CASE WHEN tecnologias_list IS NOT NULL
                  AND tecnologias_list != '[]'
                  AND tecnologias_list != 'null' THEN 1 ELSE 0 END) as con_tecnologias
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
""", gold_ids)
row = cursor.fetchone()
total = row[0]
print(f"    Total ofertas Gold Set: {total}")
print(f"    Con skills_tecnicas:    {row[1]} ({100*row[1]/total:.1f}%)")
print(f"    Con soft_skills:        {row[2]} ({100*row[2]/total:.1f}%)")
print(f"    Con tecnologias:        {row[3]} ({100*row[3]/total:.1f}%)")

# Parte 5: Resumen
print("\n" + "=" * 60)
print("DIAGNOSTICO")
print("=" * 60)
print("""
La tabla ofertas_nlp NO tiene columnas para skills_regex:
- skills_tecnicas_list  -> Viene del LLM (Qwen)
- soft_skills_list      -> Viene del LLM (Qwen)

Las skills extraidas via diccionario (regex_patterns_v4.py):
- skills_tecnicas_regex -> NO SE GUARDAN EN BD
- soft_skills_regex     -> NO SE GUARDAN EN BD

SOLUCION REQUERIDA:
1. Agregar columnas skills_tecnicas_regex y soft_skills_regex
2. O fusionar regex+LLM en las columnas existentes
""")

conn.close()
