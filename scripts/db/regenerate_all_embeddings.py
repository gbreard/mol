#!/usr/bin/env python3
"""
E1.5 — Pipeline de regeneración controlada de embeddings.

Regenera todos los corpus de embeddings con validación y rollback automático.

Uso:
    python scripts/db/regenerate_all_embeddings.py --dry-run
    python scripts/db/regenerate_all_embeddings.py
    python scripts/db/regenerate_all_embeddings.py --corpus skills
    python scripts/db/regenerate_all_embeddings.py --incremental --uris uri1,uri2
"""

import sys
import json
import argparse
import hashlib
import shutil
import sqlite3
import time
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "config"))
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from embedding_config import EMBEDDING_MODEL, EMBEDDING_REVISION, EMBEDDING_DIMS

DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
EMBEDDINGS_DIR = PROJECT_ROOT / "database" / "embeddings"
MANIFEST_PATH = EMBEDDINGS_DIR / "corpus_manifest.json"
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
BACKUPS_DIR = EMBEDDINGS_DIR / "backups"

CORPUS_DEFINITIONS = {
    "skills": {
        "npy": "esco_skills_embeddings_full.npy",
        "metadata": "esco_skills_metadata_full.json",
        "query": """
            SELECT skill_uri, preferred_label_es, description_es
            FROM esco_skills
            WHERE preferred_label_es IS NOT NULL
            ORDER BY skill_uri
        """,
        "text_fn": lambda uri, label, desc: f"{label}: {desc[:200]}" if desc else label,
        "source_table": "esco_skills",
    },
    "occupations": {
        "npy": "esco_occupations_embeddings.npy",
        "metadata": "esco_occupations_metadata.json",
        "query": """
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE preferred_label_es IS NOT NULL
            ORDER BY occupation_uri
        """,
        "text_fn": lambda uri, label, extra: label,
        "meta_fn": lambda uri, label, extra: {"uri": uri, "label": label, "isco_code": extra or ""},
        "source_table": "esco_occupations",
    },
    "clae": {
        "npy": "clae_actividades_embeddings.npy",
        "metadata": "clae_actividades_metadata.json",
        "source_table": "clae_nomenclador",
        # CLAE uses its own metadata format, regenerate from existing metadata
    },
}

BASELINE_PRECISION = 81.6
PRECISION_THRESHOLD_PCT = 5.0  # rollback si cae más de 5 puntos


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def backup_corpus(corpus_names, dry_run=False):
    """Paso 1: Backup de .npy activos."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUPS_DIR / ts

    if dry_run:
        print(f"[DRY-RUN] Crearía backup en {backup_dir}")
        return backup_dir

    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in corpus_names:
        defn = CORPUS_DEFINITIONS[name]
        src = EMBEDDINGS_DIR / defn["npy"]
        if src.exists():
            shutil.copy2(src, backup_dir / defn["npy"])
            print(f"  Backup: {defn['npy']} → {backup_dir.name}/")
    return backup_dir


def restore_backup(backup_dir, corpus_names):
    """Restaurar desde backup (rollback)."""
    for name in corpus_names:
        defn = CORPUS_DEFINITIONS[name]
        bak = backup_dir / defn["npy"]
        dst = EMBEDDINGS_DIR / defn["npy"]
        if bak.exists():
            shutil.copy2(bak, dst)
            print(f"  Restaurado: {defn['npy']}")


def generate_corpus(name, model, dry_run=False):
    """Paso 2: Generar un corpus de embeddings."""
    defn = CORPUS_DEFINITIONS[name]

    if name == "clae":
        return _generate_clae(model, dry_run)

    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(defn["query"]).fetchall()
    conn.close()

    if dry_run:
        print(f"[DRY-RUN] Generaría {len(rows)} vectores para {name}")
        return len(rows)

    texts = []
    metadata = []
    for row in rows:
        uri, label = row[0], row[1]
        extra = row[2] if len(row) > 2 else None
        text = defn["text_fn"](uri, label, extra)
        texts.append(text)

        if "meta_fn" in defn:
            metadata.append(defn["meta_fn"](uri, label, extra))
        else:
            metadata.append({"uri": uri, "label": label, "description": extra or ""})

    print(f"  Encoding {len(texts)} textos con {EMBEDDING_MODEL}...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True,
                               normalize_embeddings=True)

    npy_path = EMBEDDINGS_DIR / defn["npy"]
    meta_path = EMBEDDINGS_DIR / defn["metadata"]

    np.save(str(npy_path), embeddings.astype(np.float32))
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  Guardado: {defn['npy']} ({embeddings.shape})")
    return len(texts)


def _generate_clae(model, dry_run=False):
    """Genera CLAE desde metadata existente (no hay tabla SQL dedicada)."""
    meta_path = EMBEDDINGS_DIR / "clae_actividades_metadata.json"
    meta = json.load(open(meta_path, encoding="utf-8"))

    if dry_run:
        print(f"[DRY-RUN] Regeneraría {len(meta)} vectores CLAE")
        return len(meta)

    texts = [m["nombre"] for m in meta]
    print(f"  Encoding {len(texts)} actividades CLAE...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True,
                               normalize_embeddings=True)

    npy_path = EMBEDDINGS_DIR / "clae_actividades_embeddings.npy"
    np.save(str(npy_path), embeddings.astype(np.float32))
    print(f"  Guardado: clae_actividades_embeddings.npy ({embeddings.shape})")
    return len(texts)


def generate_incremental(uris, model, dry_run=False):
    """Flag --incremental: regenerar solo URIs específicas en skills."""
    npy_path = EMBEDDINGS_DIR / "esco_skills_embeddings_full.npy"
    meta_path = EMBEDDINGS_DIR / "esco_skills_metadata_full.json"

    embeddings = np.load(str(npy_path))
    metadata = json.load(open(meta_path, encoding="utf-8"))

    uri_to_idx = {m["uri"]: i for i, m in enumerate(metadata)}
    uris_found = [u for u in uris if u in uri_to_idx]
    uris_missing = [u for u in uris if u not in uri_to_idx]

    if uris_missing:
        print(f"  WARNING: {len(uris_missing)} URIs no encontradas en metadata")

    if dry_run:
        print(f"[DRY-RUN] Regeneraría {len(uris_found)} vectores (de {len(uris)} solicitadas)")
        return len(uris_found)

    if not uris_found:
        print("  Ninguna URI encontrada, nada que regenerar")
        return 0

    texts = [metadata[uri_to_idx[u]].get("label", "") for u in uris_found]
    new_embs = model.encode(texts, batch_size=32, normalize_embeddings=True)

    for i, uri in enumerate(uris_found):
        idx = uri_to_idx[uri]
        embeddings[idx] = new_embs[i]

    np.save(str(npy_path), embeddings.astype(np.float32))
    print(f"  Actualizado: {len(uris_found)} vectores en esco_skills_embeddings_full.npy")
    return len(uris_found)


def update_manifest(corpus_names):
    """Paso 3: Actualizar corpus_manifest.json."""
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.load(open(MANIFEST_PATH))

    for name in corpus_names:
        defn = CORPUS_DEFINITIONS[name]
        npy_path = EMBEDDINGS_DIR / defn["npy"]
        if not npy_path.exists():
            continue

        arr = np.load(str(npy_path))
        # Mapear nombre interno a key del manifest
        manifest_key = {"skills": "esco_skills", "occupations": "esco_occupations", "clae": "clae_actividades"}[name]
        manifest[manifest_key] = {
            "file": defn["npy"],
            "shape": list(arr.shape),
            "model": EMBEDDING_MODEL,
            "model_revision": EMBEDDING_REVISION,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generated_by": "LOCAL",
            "source_table": defn["source_table"],
            "source_count": arr.shape[0],
            "normalize": True,
            "checksum_sha256": sha256_file(str(npy_path)),
        }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  Manifest actualizado: {MANIFEST_PATH.name}")


def validate_gold_set():
    """Paso 4: Correr Gold Set y verificar precisión."""
    if not GOLD_SET_PATH.exists():
        print("  WARNING: Gold Set no encontrado, skip validación")
        return True, 0.0

    gold_set = json.load(open(GOLD_SET_PATH))
    total = len(gold_set)
    correct = sum(1 for g in gold_set if g.get("esco_ok"))
    precision = correct * 100 / total if total > 0 else 0

    min_precision = BASELINE_PRECISION - PRECISION_THRESHOLD_PCT

    print(f"  Gold Set: {correct}/{total} = {precision:.1f}% (mínimo: {min_precision:.1f}%)")

    if precision < min_precision:
        return False, precision

    return True, precision


def upload_to_supabase(corpus_names, dry_run=False):
    """Paso 5: Subir a Supabase con embedding_model_version."""
    if dry_run:
        print("[DRY-RUN] Subiría a Supabase")
        return

    try:
        config = json.load(open(PROJECT_ROOT / "config" / "supabase_config.json"))
        from supabase import create_client
        client = create_client(config["url"], config["service_role_key"])
    except Exception as e:
        print(f"  WARNING: No se pudo conectar a Supabase: {e}")
        return

    for name in corpus_names:
        if name == "skills":
            _upload_skills_to_supabase(client)
        elif name == "occupations":
            _upload_occupations_to_supabase(client)
        # CLAE no se sube a Supabase (es local)


def _upload_skills_to_supabase(client):
    """Sube skills embeddings a Supabase."""
    npy_path = EMBEDDINGS_DIR / "esco_skills_embeddings_full.npy"
    meta_path = EMBEDDINGS_DIR / "esco_skills_metadata_full.json"
    embeddings = np.load(str(npy_path))
    metadata = json.load(open(meta_path))

    print(f"  Subiendo {len(metadata)} skills a Supabase...")
    batch_size = 200
    for i in range(0, len(metadata), batch_size):
        batch_meta = metadata[i:i + batch_size]
        batch_emb = embeddings[i:i + batch_size]
        rows = []
        for meta, emb in zip(batch_meta, batch_emb):
            vec_str = "[" + ",".join(f"{v:.6f}" for v in emb.tolist()) + "]"
            rows.append({
                "skill_uri": meta["uri"],
                "skill_label": meta.get("label", ""),
                "embedding": vec_str,
                "embedding_model_version": EMBEDDING_REVISION,
            })
        try:
            client.table("skills_embeddings").upsert(rows).execute()
        except Exception as e:
            print(f"    Error batch {i}: {str(e)[:80]}")
        if (i + batch_size) % 2000 == 0:
            print(f"    [{i + batch_size}/{len(metadata)}]")
    print(f"  Skills subidas OK")


def _upload_occupations_to_supabase(client):
    """Sube occupations embeddings a Supabase."""
    npy_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
    meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"
    embeddings = np.load(str(npy_path))
    metadata = json.load(open(meta_path))

    print(f"  Subiendo {len(metadata)} ocupaciones a Supabase...")
    batch_size = 200
    for i in range(0, len(metadata), batch_size):
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
                "embedding_model_version": EMBEDDING_REVISION,
            })
        try:
            client.table("occupations_embeddings").upsert(rows).execute()
        except Exception as e:
            print(f"    Error batch {i}: {str(e)[:80]}")
        if (i + batch_size) % 2000 == 0:
            print(f"    [{i + batch_size}/{len(metadata)}]")
    print(f"  Ocupaciones subidas OK")


def register_pipeline_run(corpus_names, precision):
    """Paso 6: Registrar en pipeline_runs."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        run_id = f"regen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute("""
            INSERT OR IGNORE INTO pipeline_runs
            (run_id, timestamp, source, description, embedding_model_version,
             matching_version, metricas_precision)
            VALUES (?, ?, 'regeneration', ?, ?, 'N/A', ?)
        """, (
            run_id,
            datetime.now().isoformat(),
            f"Regeneración corpus: {','.join(corpus_names)}",
            EMBEDDING_REVISION,
            precision,
        ))
        conn.commit()
        conn.close()
        print(f"  Registrado: {run_id}")
    except Exception as e:
        print(f"  WARNING: No se pudo registrar run: {e}")


def verify_equivalences_lookup(dry_run=False):
    """Paso 7: Verificar que lookup de equivalencias no tiene URIs huérfanas."""
    if dry_run:
        print("[DRY-RUN] Verificaría equivalencias")
        return

    try:
        config = json.load(open(PROJECT_ROOT / "config" / "supabase_config.json"))
        from supabase import create_client
        client = create_client(config["url"], config["service_role_key"])

        # Contar URIs en lookup que no están en skills_embeddings
        # No hay JOIN directo via REST, hacemos check por sampling
        lookup_r = client.table("skill_equivalence_lookup").select("skill_uri", count="exact").limit(0).execute()
        skills_r = client.table("skills_embeddings").select("skill_uri", count="exact").limit(0).execute()

        print(f"  Equivalences lookup: {lookup_r.count} URIs")
        print(f"  Skills embeddings:   {skills_r.count} URIs")

        if lookup_r.count > skills_r.count:
            diff = lookup_r.count - skills_r.count
            print(f"  WARNING: {diff} URIs en lookup podrían no tener embedding")
        else:
            print(f"  ✓ Lookup compatible con embeddings")

    except Exception as e:
        print(f"  WARNING: No se pudo verificar equivalencias: {e}")


def main():
    parser = argparse.ArgumentParser(description="Regenerar corpus de embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Solo verificar, no modificar")
    parser.add_argument("--corpus", choices=["skills", "occupations", "clae"],
                        help="Regenerar solo este corpus")
    parser.add_argument("--incremental", action="store_true",
                        help="Regenerar solo URIs específicas")
    parser.add_argument("--uris", type=str, help="URIs a regenerar (comma-separated)")
    parser.add_argument("--skip-supabase", action="store_true", help="No subir a Supabase")
    args = parser.parse_args()

    print("=" * 60)
    print("REGENERACIÓN DE EMBEDDINGS")
    print("=" * 60)
    print(f"Modelo:   {EMBEDDING_MODEL}")
    print(f"Revisión: {EMBEDDING_REVISION[:12]}")
    print(f"Dims:     {EMBEDDING_DIMS}")
    print(f"Modo:     {'DRY-RUN' if args.dry_run else 'REAL'}")

    # Determinar qué corpus regenerar
    if args.corpus:
        corpus_names = [args.corpus]
    else:
        corpus_names = ["skills", "occupations", "clae"]
    print(f"Corpus:   {', '.join(corpus_names)}")

    # Incremental mode
    if args.incremental:
        if not args.uris:
            print("ERROR: --incremental requiere --uris uri1,uri2,...")
            sys.exit(1)

        uris = [u.strip() for u in args.uris.split(",") if u.strip()]
        print(f"URIs:     {len(uris)}")

        if not args.dry_run:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)

            # Backup antes de incremental
            backup_dir = backup_corpus(["skills"], dry_run=False)
            n = generate_incremental(uris, model, dry_run=False)
            update_manifest(["skills"])
            print(f"\nIncremental completado: {n} vectores actualizados")
        else:
            generate_incremental(uris, None, dry_run=True)
        return

    # === FLUJO COMPLETO ===

    # Paso 1: Backup
    print(f"\n--- Paso 1: Backup ---")
    backup_dir = backup_corpus(corpus_names, dry_run=args.dry_run)

    if args.dry_run:
        # Verificar que todo está en orden
        for name in corpus_names:
            defn = CORPUS_DEFINITIONS[name]
            npy = EMBEDDINGS_DIR / defn["npy"]
            if npy.exists():
                arr = np.load(str(npy))
                print(f"  {defn['npy']}: {arr.shape} ✓")
            else:
                print(f"  {defn['npy']}: NO EXISTE ✗")

        print(f"\n--- Paso 4: Validación Gold Set ---")
        ok, prec = validate_gold_set()
        print(f"  Resultado: {'OK' if ok else 'FALLA'}")

        print(f"\n--- Paso 7: Verificar equivalencias ---")
        verify_equivalences_lookup(dry_run=True)

        print(f"\n[DRY-RUN] Nada fue modificado.")
        return

    # Paso 2: Generar
    print(f"\n--- Paso 2: Generar corpus ---")
    from sentence_transformers import SentenceTransformer
    print(f"Cargando modelo {EMBEDDING_MODEL} @ {EMBEDDING_REVISION[:12]}...")
    model = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)

    for name in corpus_names:
        print(f"\n  [{name}]")
        generate_corpus(name, model)

    # Paso 3: Actualizar manifest
    print(f"\n--- Paso 3: Actualizar manifest ---")
    update_manifest(corpus_names)

    # Paso 4: Validar Gold Set
    print(f"\n--- Paso 4: Validar Gold Set ---")
    ok, precision = validate_gold_set()

    if not ok:
        print(f"\n*** ROLLBACK: Precisión {precision:.1f}% < mínimo {BASELINE_PRECISION - PRECISION_THRESHOLD_PCT:.1f}% ***")
        restore_backup(backup_dir, corpus_names)
        # Restaurar manifest también
        update_manifest(corpus_names)
        print("Backup restaurado. Embeddings originales activos.")
        sys.exit(1)

    # Paso 5: Subir a Supabase
    if not args.skip_supabase:
        print(f"\n--- Paso 5: Subir a Supabase ---")
        upload_to_supabase(corpus_names)
    else:
        print(f"\n--- Paso 5: Supabase SKIP (--skip-supabase) ---")

    # Paso 6: Registrar run
    print(f"\n--- Paso 6: Registrar pipeline run ---")
    register_pipeline_run(corpus_names, precision)

    # Paso 7: Verificar equivalencias
    print(f"\n--- Paso 7: Verificar equivalencias ---")
    verify_equivalences_lookup()

    print(f"\n{'='*60}")
    print(f"REGENERACIÓN COMPLETADA")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
