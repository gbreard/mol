#!/usr/bin/env python3
"""
Sube embeddings de skills ESCO a Supabase (pgvector).

Lee los embeddings pre-calculados de BGE-M3 (esco_skills_embeddings_full.npy)
y los sube a la tabla skills_embeddings con vectores de 1024 dimensiones.

Prerequisitos:
  1. pgvector habilitado: CREATE EXTENSION vector;
  2. Tabla creada: ejecutar 042_skills_embeddings_pgvector.sql
  3. Archivos de embeddings en database/embeddings/

Uso:
    python scripts/upload_skills_embeddings.py              # Subir todo
    python scripts/upload_skills_embeddings.py --dry-run    # Ver sin subir
    python scripts/upload_skills_embeddings.py --verify     # Verificar después de subir
    python scripts/upload_skills_embeddings.py --batch 500  # Tamaño de batch
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
EMBEDDINGS_PATH = _resolve("database/embeddings/esco_skills_embeddings_full.npy")
METADATA_PATH = _resolve("database/embeddings/esco_skills_metadata_full.json")


def get_supabase_client():
    from supabase import create_client
    config = json.load(open(SUPABASE_CONFIG))
    return create_client(config["url"], config["service_role_key"])


def load_data():
    """Carga embeddings y metadata."""
    print("Cargando embeddings...")
    embeddings = np.load(EMBEDDINGS_PATH)
    print(f"  Shape: {embeddings.shape} ({embeddings.dtype})")

    print("Cargando metadata...")
    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    print(f"  Skills: {len(metadata)}")

    assert len(metadata) == embeddings.shape[0], \
        f"Mismatch: {len(metadata)} metadata vs {embeddings.shape[0]} embeddings"

    return embeddings, metadata


def upload_embeddings(client, embeddings, metadata, batch_size=200, dry_run=False):
    """Sube embeddings a Supabase en batches."""
    total = len(metadata)
    uploaded = 0
    errors = 0
    start_time = time.time()

    print(f"\nSubiendo {total} embeddings en batches de {batch_size}...")
    if dry_run:
        print("[DRY-RUN] No se subirá nada.")

    for i in range(0, total, batch_size):
        batch_meta = metadata[i:i + batch_size]
        batch_emb = embeddings[i:i + batch_size]

        rows = []
        for j, (meta, emb) in enumerate(zip(batch_meta, batch_emb)):
            # pgvector espera el vector como string: "[0.1, 0.2, ...]"
            vec_str = "[" + ",".join(f"{v:.6f}" for v in emb.tolist()) + "]"
            rows.append({
                "skill_uri": meta["uri"],
                "skill_label": meta.get("label", ""),
                "embedding": vec_str,
            })

        if dry_run:
            uploaded += len(rows)
            if i == 0:
                print(f"  Sample row: uri={rows[0]['skill_uri'][:50]}...")
                print(f"  Vector preview: {rows[0]['embedding'][:80]}...")
            continue

        try:
            client.table("skills_embeddings").upsert(rows).execute()
            uploaded += len(rows)
        except Exception as e:
            errors += 1
            print(f"  ERROR batch {i}-{i+len(rows)}: {str(e)[:100]}")
            # Retry one by one
            for row in rows:
                try:
                    client.table("skills_embeddings").upsert([row]).execute()
                    uploaded += 1
                except Exception as e2:
                    errors += 1
                    print(f"    SKIP {row['skill_uri'][:50]}: {str(e2)[:80]}")

        # Progress
        pct = (i + len(rows)) / total * 100
        elapsed = time.time() - start_time
        rate = uploaded / elapsed if elapsed > 0 else 0
        eta = (total - uploaded) / rate if rate > 0 else 0
        print(f"  [{pct:5.1f}%] {uploaded:,}/{total:,} subidos | "
              f"{rate:.0f}/s | ETA: {eta:.0f}s", end="\r")

        # Rate limiting for Supabase free tier
        if not dry_run and i > 0:
            time.sleep(0.3)

    elapsed = time.time() - start_time
    print(f"\n\nCompletado en {elapsed:.1f}s")
    print(f"  Subidos: {uploaded:,}")
    print(f"  Errores: {errors}")

    return uploaded, errors


def verify(client):
    """Verifica los embeddings subidos."""
    print("\nVerificando...")

    # Count
    result = client.table("skills_embeddings").select("skill_uri", count="exact").limit(0).execute()
    print(f"  Total rows: {result.count}")

    # Sample
    sample = client.table("skills_embeddings").select("skill_uri,skill_label").limit(3).execute()
    for s in sample.data:
        print(f"  {s['skill_label'][:50]} | {s['skill_uri'][:50]}")

    # Test similarity query
    print("\n  Probando similitud semántica...")
    try:
        # Get one skill to test
        test_skill = client.table("skills_embeddings") \
            .select("skill_uri") \
            .eq("skill_label", "programación informática") \
            .limit(1).execute()

        if test_skill.data:
            uri = test_skill.data[0]["skill_uri"]
            result = client.rpc("match_skills_semantic", {
                "persona_skill_uris": [uri],
                "similarity_threshold": 0.70,
                "max_results_per_skill": 5
            }).execute()

            if result.data:
                print(f"  Skills similares a 'programación informática':")
                for r in result.data:
                    print(f"    [{r['similarity']:.2f}] {r['matched_skill_label']}")
            else:
                print("  Sin resultados (la función RPC puede no estar creada aún)")
        else:
            print("  Skill 'programación informática' no encontrada, probando con la primera...")
            first = client.table("skills_embeddings").select("skill_uri,skill_label").limit(1).execute()
            if first.data:
                print(f"  Primera skill: {first.data[0]['skill_label']}")
    except Exception as e:
        print(f"  Error en test de similitud: {str(e)[:100]}")
        print("  (Normal si la función RPC aún no fue creada)")

    return result.count if result else 0


def main():
    parser = argparse.ArgumentParser(description="Upload ESCO skill embeddings to Supabase pgvector")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin subir")
    parser.add_argument("--verify", action="store_true", help="Solo verificar")
    parser.add_argument("--batch", type=int, default=200, help="Tamaño de batch (default: 200)")
    args = parser.parse_args()

    client = get_supabase_client()

    if args.verify:
        verify(client)
        return

    embeddings, metadata = load_data()
    uploaded, errors = upload_embeddings(client, embeddings, metadata,
                                         batch_size=args.batch, dry_run=args.dry_run)

    if not args.dry_run and errors == 0:
        verify(client)


if __name__ == "__main__":
    main()
