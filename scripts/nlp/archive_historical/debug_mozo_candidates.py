#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug: Check if Camarero is in top-10 candidates for Mozo"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

base = Path(__file__).parent
conn = sqlite3.connect(base / 'bumeran_scraping.db')
conn.row_factory = sqlite3.Row

# Get Mozo offer
c = conn.cursor()
c.execute("""
    SELECT o.titulo, o.descripcion
    FROM ofertas o
    WHERE o.id_oferta = '2164100'
""")
row = c.fetchone()

titulo = row['titulo']
descripcion = row['descripcion'] or ''

print("=" * 70)
print("CASO MOZO (id: 2164100)")
print("=" * 70)
print(f"Titulo: {titulo}")
print(f"Descripcion (primeras 200 palabras):")
print(f"  {' '.join(descripcion.split()[:200])[:500]}...")

# Load embeddings
print("\n[1] Cargando modelos y embeddings...")
model = SentenceTransformer('BAAI/bge-m3')
embeddings_dir = base / 'embeddings'
esco_embeddings = np.load(embeddings_dir / 'esco_occupations_embeddings.npy')
with open(embeddings_dir / 'esco_occupations_metadata.json', 'r', encoding='utf-8') as f:
    esco_metadata = json.load(f)

print(f"   {len(esco_embeddings):,} ocupaciones ESCO cargadas")

# SCENARIO 1: Current method (titulo + descripcion)
print("\n" + "-" * 70)
print("ESCENARIO 1: Titulo + Descripcion (metodo actual)")
print("-" * 70)

texto_actual = f"{titulo}. {' '.join(descripcion.split()[:200])}"
emb = model.encode([texto_actual])[0]
emb = emb / np.linalg.norm(emb)

similarities = np.dot(esco_embeddings, emb)
top_indices = np.argsort(similarities)[-10:][::-1]

print("Top 10 candidatos:")
has_camarero = False
for i, idx in enumerate(top_indices):
    label = esco_metadata[idx]['label']
    isco = esco_metadata[idx].get('isco_code', 'N/A')
    sim = similarities[idx]
    marker = "<<<< CAMARERO" if '5131' in isco else ""
    if '5131' in isco:
        has_camarero = True
    print(f"  {i+1}. [{isco}] {label[:45]}: {sim:.3f} {marker}")

if not has_camarero:
    print("\n  *** CAMARERO (5131) NO ESTA EN TOP-10 ***")

# Find camarero's position
for idx, m in enumerate(esco_metadata):
    if m.get('isco_code') == '5131':
        sim = similarities[idx]
        rank = np.sum(similarities > sim) + 1
        print(f"\n  Camarero esta en posicion #{rank} con score {sim:.3f}")
        break

# SCENARIO 2: Only titulo (proposed)
print("\n" + "-" * 70)
print("ESCENARIO 2: Solo Titulo (propuesto)")
print("-" * 70)

texto_solo_titulo = titulo
emb = model.encode([texto_solo_titulo])[0]
emb = emb / np.linalg.norm(emb)

similarities = np.dot(esco_embeddings, emb)
top_indices = np.argsort(similarities)[-10:][::-1]

print("Top 10 candidatos:")
has_camarero = False
for i, idx in enumerate(top_indices):
    label = esco_metadata[idx]['label']
    isco = esco_metadata[idx].get('isco_code', 'N/A')
    sim = similarities[idx]
    marker = "<<<< CAMARERO" if '5131' in isco else ""
    if '5131' in isco:
        has_camarero = True
    print(f"  {i+1}. [{isco}] {label[:45]}: {sim:.3f} {marker}")

if has_camarero:
    print("\n  *** OK: CAMARERO ESTA EN TOP-10 CON SOLO TITULO ***")
else:
    # Find camarero's position
    for idx, m in enumerate(esco_metadata):
        if m.get('isco_code') == '5131':
            sim = similarities[idx]
            rank = np.sum(similarities > sim) + 1
            print(f"\n  Camarero esta en posicion #{rank} con score {sim:.3f}")
            break

conn.close()
