#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check improvements from v8.4 rules"""

import sqlite3
import json
from pathlib import Path

base = Path(__file__).parent

# Load Gold Set v2
with open(base / 'gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)

# Get cases that were marked as errors
error_cases = [c for c in gold_set if not c.get('esco_ok', True)]

print("="*80)
print("CASOS MARCADOS COMO ERROR - VERIFICAR SI v8.4 LOS CORRIGIO")
print("="*80)

conn = sqlite3.connect(base / 'bumeran_scraping.db')
c = conn.cursor()

improved = []
still_wrong = []

for case in error_cases:
    id_o = case['id_oferta']
    tipo = case.get('tipo_error', 'N/A')
    comentario = case.get('comentario', '')

    c.execute("""
        SELECT o.titulo, m.esco_occupation_label, m.matching_version
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta = ?
    """, (id_o,))
    row = c.fetchone()

    if row:
        titulo, esco_label, version = row
        esco_lower = esco_label.lower() if esco_label else ''

        # Check if the error was fixed based on tipo_error
        is_fixed = False

        if tipo == 'tipo_funcion':
            # Repositor -> Reponedor (FIXED if contains 'reponedor')
            if 'repositor' in titulo.lower() and 'reponedor' in esco_lower:
                is_fixed = True
            # Picking -> deberia ser almacen/logistica
            if 'picking' in titulo.lower() and ('almacen' in esco_lower or 'logistica' in esco_lower):
                is_fixed = True

        if tipo == 'sector_funcion':
            # Mozo -> deberia ser camarero/mesero
            if 'mozo' in titulo.lower() and ('camarero' in esco_lower or 'mesero' in esco_lower):
                is_fixed = True

        if tipo == 'nivel_profesional':
            # Medica -> deberia ser medico
            if ('medic' in titulo.lower() or 'dermat' in titulo.lower()) and 'medic' in esco_lower:
                is_fixed = True

        status = "FIXED" if is_fixed else "STILL_WRONG"
        if is_fixed:
            improved.append((id_o, titulo, esco_label))
        else:
            still_wrong.append((id_o, titulo, esco_label, tipo))

        print(f"[{status}] {id_o}")
        print(f"    Titulo: {titulo[:50]}")
        print(f"    ESCO:   {esco_label[:50] if esco_label else 'N/A'}")
        print(f"    Tipo error original: {tipo}")
        print()

conn.close()

print("="*80)
print("RESUMEN")
print("="*80)
print(f"Total errores en Gold Set:  {len(error_cases)}")
print(f"Corregidos por v8.4:        {len(improved)}")
print(f"Aun incorrectos:            {len(still_wrong)}")
print()

if improved:
    print("CASOS CORREGIDOS:")
    for id_o, titulo, esco in improved:
        print(f"  {id_o}: {titulo[:30]} -> {esco[:30]}")

print()
print("Precision teorica con correcciones:")
correct_base = 35  # Original
new_precision = (correct_base + len(improved)) / 50
print(f"  ({correct_base} + {len(improved)}) / 50 = {new_precision*100:.1f}%")
