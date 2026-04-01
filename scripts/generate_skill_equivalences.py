#!/usr/bin/env python3
"""
Genera tabla de equivalencias de skills ESCO.
Agrupa variaciones lingüísticas del mismo concepto usando clustering por embedding.
Calcula frecuencia de cada skill en las ofertas reales del mercado argentino.

Uso:
    python scripts/generate_skill_equivalences.py              # Generar y subir a Supabase
    python scripts/generate_skill_equivalences.py --dry-run    # Solo mostrar, no subir
    python scripts/generate_skill_equivalences.py --threshold 0.85  # Ajustar similitud
"""

import json
import sys
import sqlite3
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

PROJECT = Path(__file__).parent.parent
DB_PATH = PROJECT / "database" / "bumeran_scraping.db"
EMBEDDINGS_PATH = PROJECT / "database" / "embeddings" / "esco_skills_embeddings_full.npy"
METADATA_PATH = PROJECT / "database" / "embeddings" / "esco_skills_metadata_full.json"
CONFIG_PATH = PROJECT / "config" / "supabase_config.json"


def load_esco_skills():
    embeddings = np.load(str(EMBEDDINGS_PATH))
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    return embeddings, metadata


def cluster_skills(embeddings, threshold=0.85):
    """Clustering jerárquico por cosine similarity."""
    print(f"[EQUIV] Clustering {len(embeddings)} skills con similitud >= {threshold}...")
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - threshold,
        metric='cosine',
        linkage='average',
    )
    labels = clustering.fit_predict(embeddings)
    return labels


def calculate_frequencies(metadata):
    """Cuenta frecuencia de cada skill URI en las ofertas reales."""
    print(f"[EQUIV] Calculando frecuencias desde BD local...")
    conn = sqlite3.connect(str(DB_PATH))

    # Get all skills from ofertas
    rows = conn.execute("""
        SELECT skills_tecnicas_list FROM ofertas_nlp
        WHERE skills_tecnicas_list IS NOT NULL
          AND skills_tecnicas_list != ''
          AND skills_tecnicas_list != '[]'
    """).fetchall()
    conn.close()

    freq = Counter()
    for row in rows:
        try:
            skills = json.loads(row[0]) if row[0].startswith('[') else row[0].split(',')
            for s in skills:
                label = s.strip().strip('"').strip("'") if isinstance(s, str) else s.get('skill_esco', s.get('label', ''))
                if label:
                    freq[label.lower()] += 1
        except:
            pass

    print(f"[EQUIV] {len(freq)} skills únicas en {len(rows)} ofertas")
    return freq


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


def build_equivalence_table(metadata, cluster_labels, frequencies, embeddings=None):
    """Construye la tabla de equivalencias."""
    groups = defaultdict(list)
    for i, cl in enumerate(cluster_labels):
        groups[cl].append(i)

    equiv_table = []
    lookup_table = []

    for group_id, indices in groups.items():
        if len(indices) < 2:
            # Skill sin equivalentes — igual va al lookup
            i = indices[0]
            uri = metadata[i].get('uri', metadata[i].get('id', ''))
            label = metadata[i].get('label', metadata[i].get('preferred_label', ''))
            if uri and label:
                lookup_table.append({
                    'skill_uri': uri,
                    'equivalence_id': None,  # sin grupo
                    'skill_label': label,
                })
            continue

        # Grupo con 2+ miembros
        members = []
        for i in indices:
            uri = metadata[i].get('uri', metadata[i].get('id', ''))
            label = metadata[i].get('label', metadata[i].get('preferred_label', ''))
            freq = frequencies.get(label.lower(), 0)
            members.append({
                'uri': uri,
                'label': label,
                'frecuencia': freq,
            })

        # Label representante: el de mayor frecuencia, si empatan el más corto
        members.sort(key=lambda m: (-m['frecuencia'], len(m['label'])))
        representative = members[0]['label']

        freq_total = sum(m['frecuencia'] for m in members)
        eq_id = f"EQ-{group_id:05d}"

        # Score de confianza del clustering
        sim_avg, sim_min = (0.0, 0.0)
        if embeddings is not None:
            sim_avg, sim_min = calculate_group_similarity(embeddings, indices)

        equiv_table.append({
            'id': eq_id,
            'label_representante': representative,
            'label_argentino': None,
            'miembros': members,
            'cantidad_miembros': len(members),
            'frecuencia_total': freq_total,
            'estado': 'auto',
            'similitud_promedio': sim_avg,
            'similitud_minima': sim_min,
        })

        for m in members:
            lookup_table.append({
                'skill_uri': m['uri'],
                'equivalence_id': eq_id,
                'skill_label': m['label'],
            })

    equiv_table.sort(key=lambda x: -x['frecuencia_total'])
    return equiv_table, lookup_table


def upload_to_supabase(equiv_table, lookup_table):
    """Sube a Supabase."""
    config = json.loads(CONFIG_PATH.read_text())
    from supabase import create_client
    client = create_client(config['url'], config['service_role_key'])

    # Clear existing
    client.table('skill_equivalence_lookup').delete().neq('skill_uri', '').execute()
    client.table('skill_equivalences').delete().neq('id', '').execute()

    # Upload equivalences in batches
    print(f"[EQUIV] Subiendo {len(equiv_table)} grupos de equivalencia...")
    for i in range(0, len(equiv_table), 100):
        batch = equiv_table[i:i+100]
        rows = [{
            'id': eq['id'],
            'label_representante': eq['label_representante'],
            'label_argentino': eq['label_argentino'],
            'miembros': eq['miembros'],
            'cantidad_miembros': eq['cantidad_miembros'],
            'frecuencia_total': eq['frecuencia_total'],
            'estado': eq['estado'],
        } for eq in batch]
        client.table('skill_equivalences').upsert(rows).execute()

    # Upload lookup in batches
    print(f"[EQUIV] Subiendo {len(lookup_table)} lookups...")
    for i in range(0, len(lookup_table), 500):
        batch = lookup_table[i:i+500]
        # Only those with equivalence_id (in a group)
        rows = [l for l in batch if l['equivalence_id']]
        if rows:
            client.table('skill_equivalence_lookup').upsert(rows).execute()

    print(f"[EQUIV] OK")


def load_frozen_groups():
    """M-08b: Carga grupos protegidos (aprobado/revisado) de Supabase."""
    try:
        config = json.loads(CONFIG_PATH.read_text())
        from supabase import create_client
        client = create_client(config['url'], config['service_role_key'])

        frozen = []
        offset = 0
        while True:
            batch = client.table('skill_equivalences').select('id,miembros,estado,label_argentino,label_representante').in_('estado', ['aprobado', 'revisado']).range(offset, offset + 999).execute()
            if not batch.data:
                break
            frozen.extend(batch.data)
            offset += 1000
            if len(batch.data) < 1000:
                break

        # URIs de skills en grupos protegidos
        frozen_uris = set()
        for g in frozen:
            for m in (g.get('miembros') or []):
                frozen_uris.add(m.get('uri', ''))

        return frozen, frozen_uris
    except Exception as e:
        print(f"[EQUIV] WARN: No se pudieron cargar grupos protegidos: {e}")
        return [], set()


def main():
    parser = argparse.ArgumentParser(description='Generate skill equivalences')
    parser.add_argument('--threshold', type=float, default=0.85, help='Cosine similarity threshold')
    parser.add_argument('--dry-run', action='store_true', help='Only show, do not upload')
    parser.add_argument('--partial', action='store_true', help='Solo re-clusterizar grupos auto (protege aprobados/revisados)')
    parser.add_argument('--preview', action='store_true', help='Mostrar diff sin aplicar cambios (implica --partial)')
    args = parser.parse_args()

    if args.preview:
        args.partial = True

    # Load
    embeddings, metadata = load_esco_skills()
    print(f"[EQUIV] {len(metadata)} skills ESCO cargadas")

    # M-08b: Si --partial, filtrar skills de grupos protegidos
    frozen_groups = []
    if args.partial:
        frozen_groups, frozen_uris = load_frozen_groups()
        print(f"[EQUIV] Grupos protegidos: {len(frozen_groups)} (aprobado/revisado)")
        print(f"[EQUIV] Skills protegidas: {len(frozen_uris)} URIs")

        # Filtrar: solo clusterizar skills NO protegidas
        uri_to_idx = {m.get('uri', m.get('id', '')): i for i, m in enumerate(metadata)}
        free_indices = [i for i, m in enumerate(metadata) if m.get('uri', m.get('id', '')) not in frozen_uris]

        print(f"[EQUIV] Skills libres para clustering: {len(free_indices)}")

        # Subconjunto de embeddings
        embeddings_free = embeddings[free_indices]
        metadata_free = [metadata[i] for i in free_indices]
    else:
        embeddings_free = embeddings
        metadata_free = metadata

    # Cluster
    cluster_labels = cluster_skills(embeddings_free, args.threshold)

    # Frequencies
    frequencies = calculate_frequencies(metadata_free)

    # Build table
    equiv_table, lookup_table = build_equivalence_table(metadata_free, cluster_labels, frequencies, embeddings=embeddings_free)

    # M-08b: Si --partial, ajustar IDs para no colisionar con protegidos
    if args.partial and frozen_groups:
        max_frozen_id = max(int(g['id'].replace('EQ-', '')) for g in frozen_groups) if frozen_groups else 0
        for eq in equiv_table:
            old_num = int(eq['id'].replace('EQ-', ''))
            eq['id'] = f"EQ-{old_num + max_frozen_id + 1:05d}"
        for lk in lookup_table:
            if lk.get('equivalence_id'):
                old_num = int(lk['equivalence_id'].replace('EQ-', ''))
                lk['equivalence_id'] = f"EQ-{old_num + max_frozen_id + 1:05d}"

    groups_with_members = [eq for eq in equiv_table if eq['cantidad_miembros'] >= 2]
    total_skills_grouped = sum(eq['cantidad_miembros'] for eq in groups_with_members)

    print(f"\n[EQUIV] RESULTADO:")
    print(f"  Grupos de equivalencia: {len(groups_with_members)}")
    print(f"  Skills en grupos: {total_skills_grouped}")
    print(f"  Skills sin grupo: {len(metadata) - total_skills_grouped}")
    print(f"  Lookups: {len([l for l in lookup_table if l['equivalence_id']])}")

    # Top groups
    print(f"\n  TOP 10 por frecuencia en mercado:")
    for eq in groups_with_members[:10]:
        print(f"    {eq['id']} | freq={eq['frecuencia_total']:>5} | {eq['label_representante'][:50]} ({eq['cantidad_miembros']} equiv)")

    if args.preview:
        # M-08c: Output JSON estructurado para el poller
        labels_argentinos = sum(1 for g in frozen_groups if g.get('label_argentino'))
        preview_json = {
            "tipo": "recluster_preview",
            "timestamp": datetime.now().isoformat() if 'datetime' in dir() else "",
            "threshold_usado": args.threshold,
            "grupos_analizados": len(groups_with_members) + (len(frozen_groups) if args.partial else 0),
            "grupos_protegidos": len(frozen_groups) if args.partial else 0,
            "labels_argentinos_protegidos": labels_argentinos,
            "cambios": {
                "total": len(groups_with_members),
                "divididos": 0,
                "fusionados": 0,
                "sin_cambio": len(groups_with_members),
            },
            "detalle_divididos": [],
            "detalle_fusionados": [],
        }

        print(f"\n  PREVIEW (--partial) — cambios propuestos:")
        print(f"    Grupos auto nuevos/modificados: {len(groups_with_members)}")
        print(f"    Protegidos (intactos): {len(frozen_groups) if args.partial else 0}")
        print(f"    Labels argentinos (intactos): {labels_argentinos}")
        print(f"\n  No se aplicaron cambios. Usar --partial sin --preview para aplicar.")
        # Última línea: JSON para que el poller lo parsee
        print(json.dumps(preview_json, ensure_ascii=False))

    elif args.dry_run:
        print(f"\n  DRY RUN — no se subió a Supabase")
        with open('/tmp/skill_equivalences_full.json', 'w') as f:
            json.dump(equiv_table, f, ensure_ascii=False, indent=2)
        print(f"  Guardado en /tmp/skill_equivalences_full.json")
    else:
        upload_to_supabase(equiv_table, lookup_table)
        # M-08c: Si --partial apply, imprimir JSON de stats
        if args.partial:
            from datetime import datetime as dt
            apply_json = {
                "tipo": "recluster_apply",
                "timestamp": dt.now().isoformat(),
                "threshold_usado": args.threshold,
                "grupos_procesados": len(groups_with_members),
                "grupos_protegidos": len(frozen_groups) if frozen_groups else 0,
                "grupos_nuevos": len(groups_with_members),
                "updated_at_actualizado": True,
                "duracion_seg": 0,
            }
            print(json.dumps(apply_json, ensure_ascii=False))
        else:
            print(f"\n  Subido a Supabase")


if __name__ == '__main__':
    main()
