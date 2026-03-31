"""
Backfill retroactivo de similitud_promedio y similitud_minima
para los grupos de equivalencias existentes.

One-time script. Calcula la similitud coseno entre todos los pares
de miembros de cada grupo, usando los embeddings ESCO originales.
"""
import json
import sys
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EMBEDDINGS_PATH = PROJECT_ROOT / "database" / "embeddings" / "esco_skills_embeddings_full.npy"
METADATA_PATH = PROJECT_ROOT / "database" / "embeddings" / "esco_skills_metadata_full.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"


def calculate_group_similarity(embeddings, indices):
    """Calcula similitud promedio y mínima entre miembros del grupo."""
    if len(indices) < 2:
        return 1.0, 1.0
    group_embs = embeddings[indices]
    sim_matrix = cosine_similarity(group_embs)
    n = len(indices)
    pairwise_sims = []
    for i in range(n):
        for j in range(i + 1, n):
            pairwise_sims.append(float(sim_matrix[i][j]))
    return round(float(np.mean(pairwise_sims)), 4), round(float(np.min(pairwise_sims)), 4)


def main():
    from supabase import create_client

    # Cargar embeddings
    print("[BACKFILL] Cargando embeddings ESCO...")
    embeddings = np.load(str(EMBEDDINGS_PATH))
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)

    # Índice URI → posición en embeddings
    uri_to_idx = {}
    for i, m in enumerate(metadata):
        uri = m.get('uri', m.get('id', ''))
        if uri:
            uri_to_idx[uri] = i

    print(f"[BACKFILL] {len(embeddings)} embeddings, {len(uri_to_idx)} URIs indexadas")

    # Cargar grupos desde Supabase
    config = json.load(open(CONFIG_PATH))
    client = create_client(config['url'], config['service_role_key'])

    print("[BACKFILL] Cargando grupos de Supabase...")
    all_groups = []
    offset = 0
    while True:
        batch = client.table('skill_equivalences').select('id,miembros,cantidad_miembros').range(offset, offset + 999).execute()
        if not batch.data:
            break
        all_groups.extend(batch.data)
        offset += 1000
        if len(batch.data) < 1000:
            break

    print(f"[BACKFILL] {len(all_groups)} grupos cargados")

    # Calcular similitud por grupo
    updated = 0
    skipped = 0
    errors = 0

    for group in all_groups:
        group_id = group['id']
        miembros = group.get('miembros', [])

        if not miembros or len(miembros) < 2:
            # Grupo de 1 miembro → similitud perfecta
            try:
                client.table('skill_equivalences').update({
                    'similitud_promedio': 1.0,
                    'similitud_minima': 1.0
                }).eq('id', group_id).execute()
                updated += 1
            except Exception as e:
                errors += 1
            continue

        # Buscar índices de embeddings para cada miembro
        indices = []
        for m in miembros:
            uri = m.get('uri', '')
            if uri in uri_to_idx:
                indices.append(uri_to_idx[uri])

        if len(indices) < 2:
            skipped += 1
            continue

        # Calcular similitud
        sim_avg, sim_min = calculate_group_similarity(embeddings, indices)

        try:
            client.table('skill_equivalences').update({
                'similitud_promedio': sim_avg,
                'similitud_minima': sim_min
            }).eq('id', group_id).execute()
            updated += 1
        except Exception as e:
            errors += 1
            print(f"[BACKFILL] Error en {group_id}: {e}")

        if updated % 100 == 0 and updated > 0:
            print(f"[BACKFILL] {updated}/{len(all_groups)} actualizados...")

    print(f"\n[BACKFILL] Completado: {updated} actualizados, {skipped} sin embeddings, {errors} errores")


if __name__ == '__main__':
    main()
