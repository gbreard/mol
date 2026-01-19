#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check matching status for NLP v8.0 offers"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Total NLP v8.0
c.execute("SELECT COUNT(*) FROM validacion_v7 WHERE nlp_version = '8.0.0'")
print(f"Total NLP v8.0: {c.fetchone()[0]}")

# Con matching (JOIN)
c.execute('''
    SELECT COUNT(*)
    FROM validacion_v7 v
    JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.0.0' AND m.esco_occupation_uri IS NOT NULL
''')
print(f"NLP v8.0 con matching URI: {c.fetchone()[0]}")

# Con score no nulo
c.execute('''
    SELECT COUNT(*)
    FROM validacion_v7 v
    JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.0.0' AND m.score_final_ponderado IS NOT NULL
''')
print(f"NLP v8.0 con score: {c.fetchone()[0]}")

# Distribucion de scores
c.execute('''
    SELECT
        CASE
            WHEN m.score_final_ponderado >= 0.60 THEN 'confirmados (>=0.60)'
            WHEN m.score_final_ponderado >= 0.50 THEN 'revision (0.50-0.60)'
            ELSE 'rechazados (<0.50)'
        END as categoria,
        COUNT(*) as cantidad
    FROM validacion_v7 v
    JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.0.0' AND m.score_final_ponderado IS NOT NULL
    GROUP BY categoria
    ORDER BY categoria
''')
print("\nDistribucion scores NLP v8.0:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Estadisticas de scores
c.execute('''
    SELECT
        AVG(m.score_final_ponderado) as avg_score,
        MIN(m.score_final_ponderado) as min_score,
        MAX(m.score_final_ponderado) as max_score
    FROM validacion_v7 v
    JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.0.0' AND m.score_final_ponderado IS NOT NULL
''')
row = c.fetchone()
if row and row[0]:
    print(f"\nEstadisticas scores:")
    print(f"  Promedio: {row[0]:.3f}")
    print(f"  Minimo: {row[1]:.3f}")
    print(f"  Maximo: {row[2]:.3f}")

# Verificar si hay registros sin esco_uri
c.execute('''
    SELECT COUNT(*)
    FROM validacion_v7 v
    JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.0.0' AND m.esco_occupation_uri IS NULL
''')
sin_uri = c.fetchone()[0]
print(f"\nNLP v8.0 con matching pero sin URI: {sin_uri}")

conn.close()
