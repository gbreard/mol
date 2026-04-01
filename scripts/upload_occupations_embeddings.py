#!/usr/bin/env python3
"""
Sube embeddings de ocupaciones ESCO a Supabase (pgvector).

Lee esco_occupations_embeddings.npy + esco_occupations_metadata.json
y los sube a la tabla occupations_embeddings (3,045 rows × 1024 dims).

Prerequisitos:
  1. pgvector habilitado
  2. Tabla creada: ejecutar 047_occupations_embeddings.sql

Uso:
    python scripts/upload_occupations_embeddings.py
    python scripts/upload_occupations_embeddings.py --dry-run
    python scripts/upload_occupations_embeddings.py --verify
"""

import json
import sys
import os
import argparse
import time
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_REPO = "/mnt/d/OEDE/Webscrapping"


def _resolve(path):
    full = os.path.join(BASE_DIR, path)
    if os.path.exists(full):
        return full
    alt = os.path.join(MAIN_REPO, path)
    if os.path.exists(alt):
        return alt
    return full


SUPABASE_CONFIG = _resolve("config/supabase_config.json")
EMBEDDINGS_PATH = _resolve("database/embeddings/esco_occupations_embeddings.npy")
METADATA_PATH = _resolve("database/embeddings/esco_occupations_metadata.json")


def get_supabase_client():
    from supabase import create_client
    config = json.load(open(SUPABASE_CONFIG))
    return create_client(config["url"], config["service_role_key"])


def load_data():
    print("Cargando embeddings de ocupaciones...")
    embeddings = np.load(EMBEDDINGS_PATH)
    print(f"  Shape: {embeddings.shape} ({embeddings.dtype})")

    print("Cargando metadata...")
    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    print(f"  Ocupaciones: {len(metadata)}")

    assert len(metadata) == embeddings.shape[0], \
        f"Mismatch: {len(metadata)} metadata vs {embeddings.shape[0]} embeddings"

    return embeddings, metadata


def upload(client, embeddings, metadata, batch_size=200, dry_run=False):
    total = len(metadata)
    uploaded = 0
    errors = 0
    start_time = time.time()

    print(f"\nSubiendo {total} embeddings en batches de {batch_size}...")
    if dry_run:
        print("[DRY-RUN]")

    for i in range(0, total, batch_size):
        batch_meta = metadata[i:i + batch_size]
        batch_emb = embeddings[i:i + batch_size]

        rows = []
        for meta, emb in zip(batch_meta, batch_emb):
            vec_str = "[" + ",".join(f"{v:.6f}" for v in emb.tolist()) + "]"
            rows.append({
                "occupation_uri": meta["uri"],
                "occupation_label": meta.get("label", ""),
                "isco_code": meta.get("isco_code", "").replace("C", ""),
                "embedding": vec_str,
            })

        if dry_run:
            uploaded += len(rows)
            if i == 0:
                print(f"  Sample: uri={rows[0]['occupation_uri'][:50]}")
                print(f"  isco_code={rows[0]['isco_code']}, label={rows[0]['occupation_label'][:40]}")
            continue

        try:
            client.table("occupations_embeddings").upsert(rows).execute()
            uploaded += len(rows)
        except Exception as e:
            errors += 1
            print(f"  ERROR batch {i}: {str(e)[:100]}")
            for row in rows:
                try:
                    client.table("occupations_embeddings").upsert([row]).execute()
                    uploaded += 1
                except:
                    errors += 1

        pct = (i + len(rows)) / total * 100
        elapsed = time.time() - start_time
        rate = uploaded / elapsed if elapsed > 0 else 0
        print(f"  [{pct:5.1f}%] {uploaded:,}/{total:,} | {rate:.0f}/s", end="\r")

        if not dry_run and i > 0:
            time.sleep(0.2)

    elapsed = time.time() - start_time
    print(f"\n\nCompletado en {elapsed:.1f}s — {uploaded:,} subidos, {errors} errores")
    return uploaded, errors


def verify(client):
    print("\nVerificando...")
    result = client.table("occupations_embeddings").select("occupation_uri", count="exact").limit(0).execute()
    print(f"  Total rows: {result.count}")

    sample = client.table("occupations_embeddings").select("occupation_uri,occupation_label,isco_code").limit(3).execute()
    for s in sample.data:
        print(f"  {s['isco_code']:6s} | {s['occupation_label'][:50]}")

    return result.count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    client = get_supabase_client()

    if args.verify:
        verify(client)
        return

    embeddings, metadata = load_data()
    upload(client, embeddings, metadata, dry_run=args.dry_run)

    if not args.dry_run:
        verify(client)


if __name__ == "__main__":
    main()
