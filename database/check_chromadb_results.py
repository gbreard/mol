#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar resultados de ChromaDB re-matching"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Ver columnas disponibles
cursor.execute('PRAGMA table_info(ofertas_esco_skills_detalle)')
print('=== COLUMNAS EN ofertas_esco_skills_detalle ===')
for col in cursor.fetchall():
    print(f'  {col[1]:30s} {col[2]}')

# Estadisticas por match_method
print('\n=== ESTADISTICAS POR METODO DE MATCHING ===')
cursor.execute('''
    SELECT match_method, COUNT(*) as cnt
    FROM ofertas_esco_skills_detalle
    GROUP BY match_method
''')
for row in cursor.fetchall():
    print(f'  {row["match_method"] or "NULL":30s}: {row["cnt"]}')

# Ejemplos de matchs CORREGIDOS (donde original != global)
print('\n=== EJEMPLOS DE MATCHS CORREGIDOS CON CHROMADB ===')
cursor.execute('''
    SELECT DISTINCT
        skill_mencionado,
        esco_skill_label AS match_original,
        esco_skill_label_global AS match_global,
        match_score_global
    FROM ofertas_esco_skills_detalle
    WHERE match_method = 'chromadb_global'
      AND esco_skill_label_global IS NOT NULL
      AND esco_skill_label != esco_skill_label_global
    ORDER BY match_score_global DESC
    LIMIT 20
''')
print(f"{'SKILL OFERTA':25s} | {'ORIGINAL (incorrecto)':35s} | {'CHROMADB (corregido)':35s} | SCORE")
print('-' * 115)
for row in cursor.fetchall():
    orig = (row['match_original'] or 'NULL')[:35]
    glob = (row['match_global'] or 'sin match')[:35]
    score = row['match_score_global'] or 0
    print(f"{row['skill_mencionado'][:25]:25s} | {orig:35s} | {glob:35s} | {score:.2f}")

# Ejemplos sin match en ChromaDB (correctamente rechazados)
print('\n=== SKILLS RECHAZADOS POR CHROMADB (umbral 0.70) ===')
cursor.execute('''
    SELECT DISTINCT
        skill_mencionado,
        esco_skill_label AS match_original,
        match_score_global
    FROM ofertas_esco_skills_detalle
    WHERE match_method = 'chromadb_no_match'
    ORDER BY match_score_global DESC
    LIMIT 15
''')
print(f"{'SKILL OFERTA':25s} | {'MATCH ORIGINAL (era incorrecto)':40s} | SCORE GLOBAL")
print('-' * 90)
for row in cursor.fetchall():
    orig = (row['match_original'] or 'NULL')[:40]
    score = row['match_score_global'] or 0
    print(f"{row['skill_mencionado'][:25]:25s} | {orig:40s} | {score:.2f}")

conn.close()
