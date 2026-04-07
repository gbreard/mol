"""
Re-genera embeddings BGE-M3 en batches pequeños (genera + upsert por batch).
No guarda todo en memoria — procesa y sube de a poco.
"""

import json, sys, time, requests, numpy as np
from supabase import create_client

config = json.load(open("config/supabase_config.json"))
client = create_client(config["url"], config["service_role_key"])

VPS_URL = "http://187.124.150.28:8082/embed"
VPS_SECRET = "mol-embed-2026"
EMBED_BATCH = 50
UPSERT_BATCH = 10

def embed_batch(texts):
    res = requests.post(VPS_URL,
        headers={"Content-Type": "application/json", "x-embed-secret": VPS_SECRET},
        json={"texts": texts}, timeout=120)
    res.raise_for_status()
    return res.json()["embeddings"]

def do_skills(save_npy=False):
    print("=== SKILLS EMBEDDINGS ===")
    all_rows = []
    offset = 0
    while True:
        r = client.table("skills_embeddings").select("skill_uri, skill_label").range(offset, offset + 999).execute()
        all_rows.extend(r.data)
        if len(r.data) < 1000: break
        offset += 1000
    print(f"Total: {len(all_rows)} skills")

    all_embs = [] if save_npy else None
    errors = 0

    for i in range(0, len(all_rows), EMBED_BATCH):
        batch_rows = all_rows[i:i + EMBED_BATCH]
        labels = [r["skill_label"] for r in batch_rows]

        try:
            embeddings = embed_batch(labels)
        except Exception as e:
            print(f"  VPS error at {i}: {e}")
            errors += 1
            continue

        if save_npy:
            all_embs.extend(embeddings)

        # Upsert in small chunks
        for j in range(0, len(batch_rows), UPSERT_BATCH):
            chunk = []
            for k in range(j, min(j + UPSERT_BATCH, len(batch_rows))):
                chunk.append({
                    "skill_uri": batch_rows[k]["skill_uri"],
                    "skill_label": batch_rows[k]["skill_label"],
                    "embedding": embeddings[k],
                })
            try:
                client.table("skills_embeddings").upsert(chunk).execute()
            except Exception as e:
                print(f"  Upsert error at {i+j}: {e}")
                errors += 1
            time.sleep(0.1)

        if (i // EMBED_BATCH) % 20 == 0:
            print(f"  {min(i + EMBED_BATCH, len(all_rows))}/{len(all_rows)}")

    print(f"✅ skills_embeddings done ({errors} errors)")

    if save_npy and all_embs:
        np.save("database/embeddings/esco_skills_embeddings_full.npy",
                np.array(all_embs, dtype=np.float32))
        print("  Saved .npy")

def do_occupations(save_npy=False):
    print("\n=== OCCUPATIONS EMBEDDINGS ===")
    all_rows = []
    offset = 0
    while True:
        r = client.table("occupations_embeddings").select("occupation_uri, occupation_label, isco_code").range(offset, offset + 999).execute()
        all_rows.extend(r.data)
        if len(r.data) < 1000: break
        offset += 1000
    print(f"Total: {len(all_rows)} occupations")

    all_embs = [] if save_npy else None
    errors = 0

    for i in range(0, len(all_rows), EMBED_BATCH):
        batch_rows = all_rows[i:i + EMBED_BATCH]
        labels = [r["occupation_label"] for r in batch_rows]

        try:
            embeddings = embed_batch(labels)
        except Exception as e:
            print(f"  VPS error at {i}: {e}")
            errors += 1
            continue

        if save_npy:
            all_embs.extend(embeddings)

        for j in range(0, len(batch_rows), UPSERT_BATCH):
            chunk = []
            for k in range(j, min(j + UPSERT_BATCH, len(batch_rows))):
                chunk.append({
                    "occupation_uri": batch_rows[k]["occupation_uri"],
                    "occupation_label": batch_rows[k]["occupation_label"],
                    "isco_code": batch_rows[k].get("isco_code", ""),
                    "embedding": embeddings[k],
                })
            try:
                client.table("occupations_embeddings").upsert(chunk).execute()
            except Exception as e:
                print(f"  Upsert error at {i+j}: {e}")
                errors += 1
            time.sleep(0.1)

        if (i // EMBED_BATCH) % 10 == 0:
            print(f"  {min(i + EMBED_BATCH, len(all_rows))}/{len(all_rows)}")

    print(f"✅ occupations_embeddings done ({errors} errors)")

    if save_npy and all_embs:
        np.save("database/embeddings/esco_occupations_embeddings.npy",
                np.array(all_embs, dtype=np.float32))
        print("  Saved .npy")

if __name__ == "__main__":
    save = "--save-npy" in sys.argv
    if "--skills" in sys.argv or "--both" in sys.argv:
        do_skills(save)
    if "--occupations" in sys.argv or "--both" in sys.argv:
        do_occupations(save)
    if not any(a in sys.argv for a in ["--skills", "--occupations", "--both"]):
        print("Usage: --skills|--occupations|--both [--save-npy]")
