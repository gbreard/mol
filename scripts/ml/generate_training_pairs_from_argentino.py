#!/usr/bin/env python3
"""
E4.2 — Generar pares contrastivos desde esco_argentino.

Lee las 291 asignaciones de esco_argentino (44 ocupaciones × skills curadas)
y genera pares contrastivos con hard negatives via pgvector.

Para cada asignación (ocupación, skill):
  - query   = label de la skill en español
  - positive = uri + label de la skill curada
  - negatives = top 5 skills semánticamente similares que NO están en el perfil

Output: data/fine_tuning/train_argentino.json

Uso:
    python scripts/ml/generate_training_pairs_from_argentino.py
    python scripts/ml/generate_training_pairs_from_argentino.py --dry-run
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "fine_tuning"
OUTPUT_PATH = OUTPUT_DIR / "train_argentino.json"


def get_supabase_client():
    config_path = PROJECT_ROOT / "config" / "supabase_config.json"
    if not config_path.exists():
        # Try main repo fallback
        alt = Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json")
        if alt.exists():
            config_path = alt
        else:
            raise FileNotFoundError("supabase_config.json not found")
    config = json.loads(config_path.read_text())
    from supabase import create_client
    return create_client(config['url'], config['service_role_key'])


def load_argentino_assignments(client):
    """Load all occupation-skill assignments from esco_argentino."""
    result = client.table('esco_argentino').select(
        'esco_occupation_uri,esco_occupation_label,isco_code,skills_consolidadas'
    ).execute()

    assignments = []
    for row in (result.data or []):
        occ_uri = row['esco_occupation_uri']
        occ_label = row['esco_occupation_label']
        skills = row.get('skills_consolidadas') or []

        # Collect all skill URIs for this occupation (to exclude from negatives)
        occ_skill_uris = set()
        for s in skills:
            uri = s.get('esco_uri') or s.get('uri')
            if uri:
                occ_skill_uris.add(uri)

        for s in skills:
            uri = s.get('esco_uri') or s.get('uri')
            label = s.get('label_normalized') or s.get('label_original') or s.get('label', '')
            if not uri or not label:
                continue  # Skip 3 skills without URI

            assignments.append({
                'occupation_uri': occ_uri,
                'occupation_label': occ_label,
                'skill_uri': uri,
                'skill_label': label,
                'source': s.get('source', 'unknown'),
                'occ_skill_uris': occ_skill_uris,
            })

    return assignments


def get_hard_negatives(client, skill_uri, occupation_uri, occ_skill_uris, max_negatives=5):
    """Get hard negatives via expand_skills_semantic RPC.

    Filters out skills in the occupation's argentino profile client-side,
    since the RPC only checks esco_uri but some skills use the uri field.
    """
    try:
        # Fetch extra to compensate for filtering
        result = client.rpc('expand_skills_semantic', {
            'input_skill_uri': skill_uri,
            'match_threshold': 0.40,
            'match_count': max_negatives + 10,
            'occupation_uri': occupation_uri,
        }).execute()

        negatives = []
        for row in (result.data or []):
            # Double filter: RPC is_argentino + client-side occ_skill_uris
            if row.get('is_argentino', False):
                continue
            if row['skill_uri'] in occ_skill_uris:
                continue
            negatives.append({
                'uri': row['skill_uri'],
                'label': row['skill_label'],
                'similarity': round(row['similarity'], 4),
            })
            if len(negatives) >= max_negatives:
                break

        return negatives
    except Exception as e:
        print(f"  WARN: Error getting negatives for {skill_uri[:50]}: {e}", file=sys.stderr)
        return []


def build_contrastive_pair(assignment, negatives):
    """Build a single contrastive training pair."""
    return {
        "query": assignment['skill_label'],
        "positive": f"{assignment['skill_uri']} {assignment['skill_label']}",
        "negatives": [f"{n['uri']} {n['label']}" for n in negatives],
        "occupation_context": assignment['occupation_uri'],
        "occupation_label": assignment['occupation_label'],
        "source": "esco_argentino_v1.0",
        "confianza": "alta",
        "split": "train",
    }


def main():
    parser = argparse.ArgumentParser(description="E4.2: Generate training pairs from esco_argentino")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output file")
    parser.add_argument("--max-negatives", type=int, default=5, help="Max hard negatives per pair")
    args = parser.parse_args()

    print("E4.2: Generando pares contrastivos desde esco_argentino")
    print("=" * 60)

    client = get_supabase_client()

    # 1. Load assignments
    assignments = load_argentino_assignments(client)
    print(f"Asignaciones cargadas: {len(assignments)}")

    # 2. Generate contrastive pairs
    pairs = []
    errors = 0
    for i, a in enumerate(assignments):
        negatives = get_hard_negatives(client, a['skill_uri'], a['occupation_uri'], a['occ_skill_uris'], args.max_negatives)
        pair = build_contrastive_pair(a, negatives)
        pairs.append(pair)

        if not negatives:
            errors += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(assignments)}] {len(pairs)} pares generados")

    print(f"\nTotal pares: {len(pairs)}")
    print(f"Sin negatives: {errors}")

    # Stats
    with_negs = sum(1 for p in pairs if p['negatives'])
    avg_negs = sum(len(p['negatives']) for p in pairs) / len(pairs) if pairs else 0
    print(f"Con negatives: {with_negs} ({with_negs/len(pairs)*100:.1f}%)")
    print(f"Negatives promedio: {avg_negs:.1f}")

    if args.dry_run:
        print("\n[DRY-RUN] No se guarda archivo.")
        if pairs:
            print(f"\nSample:")
            print(json.dumps(pairs[0], ensure_ascii=False, indent=2)[:400])
        return

    # 3. Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {OUTPUT_PATH} ({len(pairs)} pares)")


if __name__ == "__main__":
    main()
