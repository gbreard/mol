#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Match only Gold Set 19 IDs - lightweight version"""

import sqlite3
import json
import sys
from pathlib import Path
import numpy as np

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
EMBEDDINGS_DIR = Path(__file__).parent / 'embeddings'

print("=" * 70)
print("MATCHING SOLO GOLD SET - 19 casos")
print("=" * 70)

# Load Gold Set IDs
with open(Path(__file__).parent / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
gold_ids = [str(case['id_oferta']) for case in gold_set]
print(f"Gold Set IDs: {len(gold_ids)}")

# Load models
print("\n[1] Cargando modelos...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
print("  -> BGE-M3 cargado")

# Load ESCO embeddings
print("\n[2] Cargando embeddings ESCO...")
occ_emb = np.load(EMBEDDINGS_DIR / 'occupation_embeddings_bge-m3.npy')
with open(EMBEDDINGS_DIR / 'occupation_embeddings_bge-m3.json', 'r') as f:
    occ_meta = json.load(f)
print(f"  -> {len(occ_emb)} ocupaciones ESCO")

# Load offers
print("\n[3] Cargando ofertas Gold Set...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

placeholders = ','.join(['?'] * len(gold_ids))
c.execute(f'''
    SELECT
        o.id_oferta, o.titulo,
        COALESCE(o.descripcion_utf8, o.descripcion) as descripcion
    FROM ofertas o
    WHERE o.id_oferta IN ({placeholders})
''', gold_ids)
ofertas = [dict(row) for row in c.fetchall()]
print(f"  -> {len(ofertas)} ofertas cargadas")

# Process matching
print("\n[4] Procesando matching...")
from tqdm import tqdm

for oferta in tqdm(ofertas, desc="Matching Gold Set"):
    id_oferta = str(oferta['id_oferta'])
    titulo = oferta['titulo'] or ''
    descripcion = oferta['descripcion'] or ''

    # Generate title embedding
    titulo_emb = model.encode([titulo])[0]

    # Calculate cosine similarity with all ESCO occupations
    similarities = np.dot(occ_emb, titulo_emb) / (
        np.linalg.norm(occ_emb, axis=1) * np.linalg.norm(titulo_emb) + 1e-8
    )

    # Get best match
    best_idx = np.argmax(similarities)
    best_score = float(similarities[best_idx])
    best_uri = occ_meta[best_idx]['uri']
    best_label = occ_meta[best_idx]['label']

    # Description score (simple similarity)
    if descripcion:
        desc_emb = model.encode([descripcion[:1000]])[0]  # Limit description
        desc_sims = np.dot(occ_emb, desc_emb) / (
            np.linalg.norm(occ_emb, axis=1) * np.linalg.norm(desc_emb) + 1e-8
        )
        desc_score = float(desc_sims[best_idx])
    else:
        desc_score = 0.0

    # Final score: 60% title + 40% description (simplified, no skills)
    score_final = 0.6 * best_score + 0.4 * desc_score

    # Update database
    c.execute('''
        UPDATE ofertas_esco_matching SET
            esco_occupation_uri = ?,
            esco_occupation_label = ?,
            score_titulo = ?,
            score_descripcion = ?,
            score_final_ponderado = ?,
            match_method = 'gold_set_v81'
        WHERE id_oferta = ?
    ''', (best_uri, best_label, best_score, desc_score, score_final, id_oferta))

conn.commit()
print(f"\n  -> {len(ofertas)} registros actualizados")

# Show results
print("\n" + "=" * 70)
print("RESULTADOS")
print("=" * 70)

c.execute(f'''
    SELECT id_oferta, esco_occupation_label, score_final_ponderado
    FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders})
    ORDER BY id_oferta
''', gold_ids)

print("\n| ID Oferta    | ESCO Match                       | Score |")
print("|--------------|----------------------------------|-------|")
for row in c.fetchall():
    label = (row[1] or 'N/A')[:32]
    score = row[2] or 0
    print(f"| {row[0]} | {label:32} | {score:.3f} |")

conn.close()
print("\nListo!")
