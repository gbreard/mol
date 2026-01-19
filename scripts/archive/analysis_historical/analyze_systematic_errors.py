#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analyze systematic errors in Gold Set v2"""

import sqlite3
import json
from pathlib import Path

base = Path(__file__).parent

# Connect to DB
conn = sqlite3.connect(base / 'bumeran_scraping.db')
c = conn.cursor()

# Key error cases to analyze
ERROR_CASES = [
    '2164100',    # Mozo -> Supervisor vinedos
    '1118017586', # Medica -> Esteticista
    '1118022146', # Community Manager -> Responsable marketing
    '1117984105', # Gerente Ventas -> Representante
    '1117990944', # Repositor -> Mantenedor
    '1118023904', # Picking -> Embalaje
]

print("="*100)
print("ANALISIS DE ERRORES SISTEMATICOS")
print("="*100)

for id_oferta in ERROR_CASES:
    print(f"\n{'='*100}")
    print(f"CASO: {id_oferta}")
    print("="*100)

    # Get offer details
    c.execute("""
        SELECT titulo, descripcion_utf8
        FROM ofertas
        WHERE CAST(id_oferta AS TEXT) = ?
    """, (id_oferta,))
    row = c.fetchone()
    if row:
        titulo, desc = row
        print(f"TITULO: {titulo}")
        print(f"DESCRIPCION (primeros 500 chars):")
        print(f"  {(desc or '')[:500]}...")
    else:
        print("NO DATA IN ofertas table")
        continue

    # Get NLP extraction
    c.execute("""
        SELECT titulo_normalizado, skills_detectados, nivel_educativo,
               experiencia_anios, sector_actividad
        FROM ofertas_nlp
        WHERE id_oferta = ?
    """, (id_oferta,))
    nlp = c.fetchone()
    if nlp:
        print(f"\nNLP EXTRACTION:")
        print(f"  titulo_normalizado: {nlp[0]}")
        print(f"  skills_detectados: {nlp[1][:200] if nlp[1] else 'None'}...")
        print(f"  nivel_educativo: {nlp[2]}")
        print(f"  experiencia_anios: {nlp[3]}")
        print(f"  sector_actividad: {nlp[4]}")
    else:
        print("\nNO NLP DATA")

    # Get matching result
    c.execute("""
        SELECT esco_occupation_label, esco_occupation_uri, isco_code, isco_label,
               score_final_ponderado, score_titulo, score_skills, score_descripcion,
               matching_version
        FROM ofertas_esco_matching
        WHERE id_oferta = ?
    """, (id_oferta,))
    match = c.fetchone()
    if match:
        print(f"\nMATCHING RESULT:")
        print(f"  ESCO label: {match[0]}")
        print(f"  ESCO URI:   {match[1]}")
        print(f"  ISCO code:  {match[2]} - {match[3]}")
        print(f"  SCORES:")
        print(f"    - Final ponderado: {match[4]:.3f}")
        print(f"    - Titulo:          {match[5]:.3f}" if match[5] else "    - Titulo:          N/A")
        print(f"    - Skills:          {match[6]:.3f}" if match[6] else "    - Skills:          N/A")
        print(f"    - Descripcion:     {match[7]:.3f}" if match[7] else "    - Descripcion:     N/A")
        print(f"  Matching version: {match[8]}")
    else:
        print("\nNO MATCHING DATA")

conn.close()

print("\n" + "="*100)
print("DIAGNOSTICO")
print("="*100)
print("""
CASO Mozo -> Supervisor vinedos (2164100):
  PROBLEMA: "Mozo" en Argentina = camarero/mesero. El embedding confunde con
  "mozo de labranza" (trabajador agricola) que tiene similitud con vinedos.
  FIX PROPUESTO:
  - Agregar regla de sinonimos: mozo = camarero, mesero
  - Pre-filtrar por sector antes del embedding match

CASO Medica -> Esteticista (1118017586):
  PROBLEMA: El titulo menciona "tratamientos esteticos" y el embedding
  prioriza la palabra "estetico" sobre "medica/dermatologa".
  FIX PROPUESTO:
  - Dar mas peso a palabras de nivel profesional (medico, doctor, ingeniero)
  - Excluir ocupaciones ESCO nivel 5xxx para titulos con "medico/a"

PATRON COMUN:
  - Los embeddings no capturan bien la JERARQUIA ni el NIVEL PROFESIONAL
  - El matching por similitud semantica ignora restricciones de dominio

SOLUCION GENERAL:
  1. Pre-filtro por ISCO nivel 1: Restringir candidatos ESCO al ISCO apropiado
  2. Blacklist de combinaciones: Si titulo contiene X, no puede ser Y
  3. Sinonimos argentinos: mozo->camarero, repositor->reponedor
""")
