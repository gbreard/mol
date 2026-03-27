"""
Backfill equivalence_id + canonical_label en ofertas_skills de Supabase.
One-time script — run after executing 037_skill_equiv_in_ofertas_skills.sql.

Para cada skill_uri que tiene grupo de equivalencia, actualiza:
  - equivalence_id: ID del grupo (EQ-00001, etc.)
  - canonical_label: label representante del grupo
  - preferred_label: reemplaza con canonical (para consistencia)

Luego limpia duplicados: si una oferta tiene 2 skills del mismo grupo,
queda solo el de mayor score.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"
BATCH_SIZE = 200  # URIs por UPDATE batch


def main():
    from supabase import create_client

    config = json.load(open(CONFIG_PATH))
    client = create_client(config['url'], config['service_role_key'])

    # 1. Load equivalence lookup
    print("Cargando equivalencias...", flush=True)
    uri_to_equiv = {}
    offset = 0
    while True:
        batch = client.table('skill_equivalence_lookup').select(
            'skill_uri,equivalence_id'
        ).range(offset, offset + 999).execute()
        if not batch.data:
            break
        for row in batch.data:
            uri_to_equiv[row['skill_uri']] = row['equivalence_id']
        offset += len(batch.data)
        if len(batch.data) < 1000:
            break

    # Load equivalence labels
    equiv_labels = {}
    offset = 0
    while True:
        batch = client.table('skill_equivalences').select(
            'id,label_representante,label_argentino'
        ).range(offset, offset + 999).execute()
        if not batch.data:
            break
        for row in batch.data:
            equiv_labels[row['id']] = row.get('label_argentino') or row['label_representante']
        offset += len(batch.data)
        if len(batch.data) < 1000:
            break

    print(f"  {len(uri_to_equiv)} URIs → {len(equiv_labels)} grupos", flush=True)

    # 2. Build RPC payloads grouped by equivalence_id
    # We'll update all skills matching each URI group at once
    # Group URIs by their equivalence_id
    eq_to_uris = {}
    for uri, eq_id in uri_to_equiv.items():
        if eq_id not in eq_to_uris:
            eq_to_uris[eq_id] = []
        eq_to_uris[eq_id].append(uri)

    print(f"\n--- PASO 1: Actualizar equivalence_id + canonical_label ---", flush=True)
    total_updated = 0
    total_groups = len(eq_to_uris)

    for i, (eq_id, uris) in enumerate(eq_to_uris.items()):
        canonical = equiv_labels.get(eq_id, '')
        if not canonical:
            continue

        # Update in batches of URIs
        for j in range(0, len(uris), BATCH_SIZE):
            uri_batch = uris[j:j + BATCH_SIZE]
            try:
                result = client.table('ofertas_skills').update({
                    'equivalence_id': eq_id,
                    'canonical_label': canonical,
                }).in_('skill_uri', uri_batch).execute()
                # Count updated rows (approximate)
                if result.data:
                    total_updated += len(result.data)
            except Exception as e:
                print(f"  Error updating {eq_id} batch {j}: {e}", flush=True)

        if (i + 1) % 50 == 0:
            print(f"  Progreso: {i+1}/{total_groups} grupos, {total_updated} filas actualizadas", flush=True)
            time.sleep(1)  # Rate limit

    print(f"  Total filas actualizadas: {total_updated}", flush=True)

    # 3. Clean duplicates: if an offer has 2 skills from same equivalence group
    print(f"\n--- PASO 2: Limpiar duplicados por grupo de equivalencia ---", flush=True)

    # Find duplicates via RPC or paginated query
    # Strategy: query all skills with equivalence_id, group client-side
    print("  Buscando duplicados...", flush=True)
    dupes_found = 0
    dupes_deleted = 0
    offset = 0

    # We'll scan in pages and track (id_oferta, equivalence_id) -> [rows]
    from collections import defaultdict
    groups = defaultdict(list)

    while True:
        batch = client.table('ofertas_skills').select(
            'id,id_oferta,equivalence_id,score'
        ).not_.is_('equivalence_id', 'null').order(
            'id_oferta'
        ).range(offset, offset + 4999).execute()

        if not batch.data:
            break

        for row in batch.data:
            key = (row['id_oferta'], row['equivalence_id'])
            groups[key].append(row)

        offset += len(batch.data)
        if len(batch.data) < 5000:
            break
        print(f"    Escaneados: {offset} filas...", flush=True)

    # Find groups with > 1 entry
    ids_to_delete = []
    for key, rows in groups.items():
        if len(rows) > 1:
            dupes_found += len(rows) - 1
            # Sort by score DESC, keep first
            rows.sort(key=lambda r: r.get('score') or 0, reverse=True)
            for r in rows[1:]:
                ids_to_delete.append(r['id'])

    print(f"  Duplicados encontrados: {dupes_found}", flush=True)

    if ids_to_delete:
        # Delete in batches
        for k in range(0, len(ids_to_delete), 100):
            chunk = ids_to_delete[k:k + 100]
            try:
                client.table('ofertas_skills').delete().in_('id', chunk).execute()
                dupes_deleted += len(chunk)
            except Exception as e:
                print(f"  Error eliminando duplicados batch {k}: {e}", flush=True)
            time.sleep(0.5)

        print(f"  Duplicados eliminados: {dupes_deleted}", flush=True)
    else:
        print("  Sin duplicados.", flush=True)

    # 4. Verify
    print(f"\n--- VERIFICACION ---", flush=True)
    result = client.table('ofertas_skills').select('id', count='exact', head=True).execute()
    total = result.count
    result_eq = client.table('ofertas_skills').select(
        'id', count='exact', head=True
    ).not_.is_('equivalence_id', 'null').execute()
    with_equiv = result_eq.count

    print(f"  Total skills: {total}", flush=True)
    print(f"  Con equivalencia: {with_equiv} ({with_equiv*100//max(total,1)}%)", flush=True)
    print(f"  Sin equivalencia: {total - with_equiv}", flush=True)
    print(f"\nBackfill completado.", flush=True)


if __name__ == '__main__':
    main()
