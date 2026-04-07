"""
Re-genera embeddings BGE-M3 para skills_embeddings y occupations_embeddings.
Usa el VPS como servidor de embeddings para garantizar compatibilidad.

Uso:
    python3 scripts/exports/regenerate_embeddings.py --skills
    python3 scripts/exports/regenerate_embeddings.py --occupations
    python3 scripts/exports/regenerate_embeddings.py --both
    python3 scripts/exports/regenerate_embeddings.py --both --save-npy
"""

import json
import sys
import time
import requests
import numpy as np
from supabase import create_client

config = json.load(open("config/supabase_config.json"))
client = create_client(config["url"], config["service_role_key"])

VPS_URL = "http://187.124.150.28:8082/embed"
VPS_SECRET = "mol-embed-2026"
BATCH_SIZE = 50  # embeddings per VPS call
UPSERT_BATCH = 20  # rows per Supabase upsert (vectors are large)


def embed_batch(texts):
    """Generate embeddings via VPS BGE-M3 server."""
    res = requests.post(VPS_URL,
        headers={"Content-Type": "application/json", "x-embed-secret": VPS_SECRET},
        json={"texts": texts},
        timeout=60)
    if res.status_code != 200:
        raise Exception(f"VPS error {res.status_code}: {res.text[:200]}")
    return res.json()["embeddings"]


def regenerate_skills():
    """Re-generate skills_embeddings (14K)."""
    print("=== SKILLS EMBEDDINGS ===")

    # Fetch all skills
    print("Fetching skills from Supabase...")
    all_skills = []
    offset = 0
    while True:
        r = client.table("skills_embeddings").select("skill_uri, skill_label").range(offset, offset + 999).execute()
        all_skills.extend(r.data)
        if len(r.data) < 1000:
            break
        offset += 1000
    print(f"  Total: {len(all_skills)} skills")

    # No truncate needed — upsert overwrites by primary key (skill_uri)
    print("Will upsert over existing rows...")

    # Generate embeddings in batches and upsert
    labels = [s["skill_label"] for s in all_skills]
    all_embeddings = []

    print("Generating embeddings via VPS...")
    for i in range(0, len(labels), BATCH_SIZE):
        batch_labels = labels[i:i + BATCH_SIZE]
        embeddings = embed_batch(batch_labels)
        all_embeddings.extend(embeddings)
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  {i + len(batch_labels)}/{len(labels)}")

    print("Upserting to Supabase...")
    for i in range(0, len(all_skills), UPSERT_BATCH):
        batch = []
        for j in range(i, min(i + UPSERT_BATCH, len(all_skills))):
            batch.append({
                "skill_uri": all_skills[j]["skill_uri"],
                "skill_label": all_skills[j]["skill_label"],
                "embedding": all_embeddings[j],
            })
        client.table("skills_embeddings").upsert(batch).execute()
        if (i // UPSERT_BATCH) % 10 == 0:
            print(f"  {min(i + UPSERT_BATCH, len(all_skills))}/{len(all_skills)}")
        time.sleep(0.2)

    print(f"✅ skills_embeddings: {len(all_skills)} rows regenerated")

    # Save npy if requested
    if "--save-npy" in sys.argv:
        npy_path = "database/embeddings/esco_skills_embeddings_full.npy"
        np.save(npy_path, np.array(all_embeddings, dtype=np.float32))
        print(f"  Saved {npy_path}")

    return all_embeddings


def regenerate_occupations():
    """Re-generate occupations_embeddings (3K)."""
    print("\n=== OCCUPATIONS EMBEDDINGS ===")

    # Fetch all occupations
    print("Fetching occupations from Supabase...")
    all_occs = []
    offset = 0
    while True:
        r = client.table("occupations_embeddings").select("occupation_uri, occupation_label").range(offset, offset + 999).execute()
        all_occs.extend(r.data)
        if len(r.data) < 1000:
            break
        offset += 1000
    print(f"  Total: {len(all_occs)} occupations")

    # No truncate — upsert overwrites by primary key (occupation_uri)
    print("Will upsert over existing rows...")

    # Generate embeddings
    labels = [o["occupation_label"] for o in all_occs]
    all_embeddings = []

    print("Generating embeddings via VPS...")
    for i in range(0, len(labels), BATCH_SIZE):
        batch_labels = labels[i:i + BATCH_SIZE]
        embeddings = embed_batch(batch_labels)
        all_embeddings.extend(embeddings)
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  {i + len(batch_labels)}/{len(labels)}")

    print("Upserting to Supabase...")
    for i in range(0, len(all_occs), UPSERT_BATCH):
        batch = []
        for j in range(i, min(i + UPSERT_BATCH, len(all_occs))):
            batch.append({
                "occupation_uri": all_occs[j]["occupation_uri"],
                "occupation_label": all_occs[j]["occupation_label"],
                "embedding": all_embeddings[j],
            })
        client.table("occupations_embeddings").upsert(batch).execute()
        if (i // UPSERT_BATCH) % 10 == 0:
            print(f"  {min(i + UPSERT_BATCH, len(all_occs))}/{len(all_occs)}")
        time.sleep(0.2)

    print(f"✅ occupations_embeddings: {len(all_occs)} rows regenerated")

    if "--save-npy" in sys.argv:
        npy_path = "database/embeddings/esco_occupations_embeddings.npy"
        np.save(npy_path, np.array(all_embeddings, dtype=np.float32))
        print(f"  Saved {npy_path}")


if __name__ == "__main__":
    if "--skills" in sys.argv or "--both" in sys.argv:
        regenerate_skills()
    if "--occupations" in sys.argv or "--both" in sys.argv:
        regenerate_occupations()
    if not any(a in sys.argv for a in ["--skills", "--occupations", "--both"]):
        print("Usage: python3 regenerate_embeddings.py --skills|--occupations|--both [--save-npy]")
