#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check ESCO tables structure"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Ver skill_reusability_level
print('=== SKILL_REUSABILITY_LEVEL ===')
cursor.execute('SELECT DISTINCT skill_reusability_level, COUNT(*) FROM esco_skills GROUP BY skill_reusability_level')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]:,}')

# Ver skill_type_in_relation en associations
print('\n=== SKILL_TYPE_IN_RELATION (associations) ===')
cursor.execute('SELECT DISTINCT skill_type_in_relation, COUNT(*) FROM esco_associations GROUP BY skill_type_in_relation')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]:,}')

# Buscar skills que parezcan knowledge
print('\n=== SKILLS URI con /knowledge/ ===')
cursor.execute("SELECT skill_uri, preferred_label_es FROM esco_skills WHERE skill_uri LIKE '%/knowledge/%' LIMIT 5")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f'  {row}')
else:
    print('  No encontrados')

# Buscar por concept_type
print('\n=== BUSCAR PATRON EN URI ===')
cursor.execute("SELECT DISTINCT SUBSTR(skill_uri, 1, 50) FROM esco_skills LIMIT 10")
for row in cursor.fetchall():
    print(f'  {row[0]}')

# Ejemplo de una ocupacion con sus skills
print('\n=== EJEMPLO: Skills de una ocupacion ===')
cursor.execute("""
    SELECT o.preferred_label_es, s.preferred_label_es, a.relation_type, a.skill_type_in_relation
    FROM esco_occupations o
    JOIN esco_associations a ON o.occupation_uri = a.occupation_uri
    JOIN esco_skills s ON a.skill_uri = s.skill_uri
    WHERE o.preferred_label_es LIKE '%vendedor%'
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f'  {row[0][:30]} | {row[1][:40]} | {row[2]} | {row[3]}')

conn.close()
