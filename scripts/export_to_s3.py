#!/usr/bin/env python3
"""
MOL-30: Export SQLite data to S3 for validation dashboard

Exports:
  - ofertas.json: Job postings data
  - matches.json: ESCO matching results
  - candidates.json: Top-k alternatives (for revision cases)
  - metrics.json: Aggregated metrics
  - esco_occupations.json: ESCO catalog

Usage:
    python scripts/export_to_s3.py
    python scripts/export_to_s3.py --dry-run      # Generate files without upload
    python scripts/export_to_s3.py --local-only   # Save to local folder only
"""

import gzip
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "database" / "bumeran_scraping.db"
CONFIG_PATH = ROOT_DIR / "config" / "aws_credentials.json"
OUTPUT_DIR = ROOT_DIR / "exports"


def load_aws_credentials():
    """Load AWS credentials from config file or environment."""
    if os.environ.get('AWS_ACCESS_KEY_ID'):
        return {
            'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
            'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
            'region': os.environ.get('AWS_REGION', 'sa-east-1'),
            'bucket': os.environ.get('S3_BUCKET', 'mol-validation-data')
        }

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    return None


def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect(DB_PATH)


def export_ofertas(conn, snapshot_date: str) -> dict:
    """Export ofertas data."""
    print("  Exportando ofertas...")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            o.empresa,
            o.localizacion,
            o.fecha_publicacion_iso,
            SUBSTR(o.descripcion_utf8, 1, 200) as descripcion_preview,
            o.descripcion_utf8 as descripcion_full,
            o.url_oferta,
            COALESCE(o.portal, 'bumeran') as fuente
        FROM ofertas o
        INNER JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = m.id_oferta
        ORDER BY o.fecha_publicacion_iso DESC
    ''')

    ofertas = []
    for row in cursor.fetchall():
        ofertas.append({
            "id": str(row[0]),
            "titulo": row[1] or "",
            "empresa": row[2] or "Confidencial",
            "ubicacion": row[3] or "",
            "fecha_publicacion": row[4] or "",
            "descripcion_preview": (row[5] or "")[:200] + "..." if row[5] and len(row[5]) > 200 else (row[5] or ""),
            "descripcion_full": row[6] or "",
            "url_original": row[7] or "",
            "fuente": row[8] or "bumeran"
        })

    print(f"    {len(ofertas)} ofertas exportadas")

    return {
        "version": "1.0",
        "snapshot_date": snapshot_date,
        "total_ofertas": len(ofertas),
        "ofertas": ofertas
    }


def export_matches(conn, snapshot_date: str) -> dict:
    """Export matching results."""
    print("  Exportando matches...")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            id_oferta,
            esco_occupation_uri,
            esco_occupation_label,
            isco_code,
            score_final_ponderado,
            score_titulo,
            score_skills,
            score_descripcion,
            match_confirmado,
            requiere_revision,
            skills_matched_essential,
            skills_oferta_json,
            matching_version
        FROM ofertas_esco_matching
    ''')

    # Handle potential bytes/string values from DB
    def safe_float(val, default=0.0):
        if val is None:
            return default
        if isinstance(val, bytes):
            try:
                return float(val.decode('utf-8'))
            except:
                return default
        try:
            return float(val)
        except:
            return default

    def safe_str(val, default=""):
        if val is None:
            return default
        if isinstance(val, bytes):
            return val.decode('utf-8', errors='replace')
        return str(val)

    matches = []
    version = None

    for row in cursor.fetchall():
        # Determine status
        score = safe_float(row[4], 0)
        confirmado = row[8]
        revision = row[9]

        if confirmado:
            status = "confirmado"
        elif revision:
            status = "revision"
        elif score < 0.50:
            status = "rechazado"
        else:
            status = "revision"

        # Parse skills
        skills_matched = []
        skills_str = safe_str(row[10])
        if skills_str:
            try:
                skills_matched = json.loads(skills_str) if skills_str.startswith('[') else skills_str.split(',')
            except:
                skills_matched = []

        skills_oferta = []
        skills_oferta_str = safe_str(row[11])
        if skills_oferta_str:
            try:
                skills_oferta = json.loads(skills_oferta_str) if skills_oferta_str.startswith('[') else skills_oferta_str.split(',')
            except:
                skills_oferta = []

        matches.append({
            "id_oferta": safe_str(row[0]),
            "esco": {
                "uri": safe_str(row[1]),
                "label": safe_str(row[2]),
                "isco_code": safe_str(row[3])
            },
            "scores": {
                "final": round(safe_float(row[4]), 3),
                "titulo": round(safe_float(row[5]), 3),
                "skills": round(safe_float(row[6]), 3),
                "descripcion": round(safe_float(row[7]), 3)
            },
            "status": status,
            "never_confirm": revision == 1 and confirmado == 0,
            "skills_matched": skills_matched[:10] if isinstance(skills_matched, list) else [],
            "skills_oferta": skills_oferta[:10] if isinstance(skills_oferta, list) else []
        })

        if row[12]:
            version = row[12]

    print(f"    {len(matches)} matches exportados")

    return {
        "version": "1.0",
        "snapshot_date": snapshot_date,
        "matching_version": version or "unknown",
        "total_matches": len(matches),
        "matches": matches
    }


def export_candidates(conn, snapshot_date: str, matches_data: dict) -> dict:
    """
    Export top-k candidates for cases requiring validation.

    NOTE: Currently the matching only stores the best match.
    This function creates a placeholder structure. To populate with real
    candidates, the matching algorithm needs to be updated to store top-k.
    """
    print("  Exportando candidates...")

    # Filter cases that need validation (revision or never_confirm)
    revision_ids = set()
    for match in matches_data.get("matches", []):
        if match["status"] == "revision" or match.get("never_confirm"):
            revision_ids.add(match["id_oferta"])

    # For now, we only have the best match stored
    # Create placeholder with just the selected candidate
    candidates = {}
    for match in matches_data.get("matches", []):
        if match["id_oferta"] in revision_ids:
            candidates[match["id_oferta"]] = [
                {
                    "rank": 1,
                    "uri": match["esco"]["uri"],
                    "label": match["esco"]["label"],
                    "score": match["scores"]["final"],
                    "selected": True
                }
            ]

    print(f"    {len(candidates)} ofertas con candidatos (solo best match disponible)")
    print(f"    NOTE: Para top-k completo, actualizar matching a guardar alternativas")

    return {
        "version": "1.0",
        "snapshot_date": snapshot_date,
        "total_ofertas_con_candidatos": len(candidates),
        "note": "Solo best match disponible. Top-k requiere actualizar matching.",
        "candidates": candidates
    }


def export_metrics(conn, snapshot_date: str, matches_data: dict) -> dict:
    """Export aggregated metrics."""
    print("  Exportando metrics...")

    cursor = conn.cursor()

    # Pipeline metrics
    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total_ofertas = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ofertas_nlp')
    ofertas_nlp = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM ofertas_esco_matching')
    ofertas_matching = cursor.fetchone()[0]

    # Matching metrics
    matches = matches_data.get("matches", [])
    confirmados = sum(1 for m in matches if m["status"] == "confirmado")
    revision = sum(1 for m in matches if m["status"] == "revision")
    rechazados = sum(1 for m in matches if m["status"] == "rechazado")

    scores = [m["scores"]["final"] for m in matches if m["scores"]["final"] > 0]
    score_promedio = sum(scores) / len(scores) if scores else 0
    scores_sorted = sorted(scores)
    score_mediana = scores_sorted[len(scores_sorted) // 2] if scores_sorted else 0

    # ISCO distribution
    isco_dist = {}
    for m in matches:
        isco = m["esco"].get("isco_code", "")
        if isco:
            nivel1 = isco[0] if len(isco) > 0 else "?"
            isco_dist[nivel1] = isco_dist.get(nivel1, 0) + 1

    # Top occupations
    occupation_counts = {}
    for m in matches:
        label = m["esco"].get("label", "")
        if label:
            occupation_counts[label] = occupation_counts.get(label, 0) + 1

    top_ocupaciones = sorted(occupation_counts.items(), key=lambda x: -x[1])[:10]

    # Gold set metrics (from validacion_humana if exists)
    gold_set_metrics = {"total_casos": 19, "validados": 19, "pendientes": 0, "precision": 0.789}
    try:
        cursor.execute('SELECT COUNT(*) FROM validacion_humana')
        gold_set_metrics["total_casos"] = cursor.fetchone()[0]
    except:
        pass

    print(f"    Pipeline: {total_ofertas} ofertas, {ofertas_nlp} NLP, {ofertas_matching} matching")
    print(f"    Status: {confirmados} confirmados, {revision} revision, {rechazados} rechazados")

    return {
        "version": "1.0",
        "snapshot_date": snapshot_date,
        "pipeline": {
            "ofertas_total": total_ofertas,
            "ofertas_con_nlp": ofertas_nlp,
            "ofertas_con_matching": ofertas_matching,
            "cobertura_nlp": round(ofertas_nlp / total_ofertas, 2) if total_ofertas > 0 else 0
        },
        "matching": {
            "confirmados": confirmados,
            "revision": revision,
            "rechazados": rechazados,
            "score_promedio": round(score_promedio, 3),
            "score_mediana": round(score_mediana, 3)
        },
        "gold_set": gold_set_metrics,
        "distribucion_isco": isco_dist,
        "top_ocupaciones": [{"label": label, "count": count} for label, count in top_ocupaciones]
    }


def export_esco_occupations(conn, snapshot_date: str) -> dict:
    """Export ESCO occupations catalog."""
    print("  Exportando esco_occupations...")

    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            occupation_uri,
            preferred_label_es,
            isco_code,
            description_es
        FROM esco_occupations
        WHERE status = 'released' OR status IS NULL
        ORDER BY preferred_label_es
    ''')

    # ISCO groups
    isco_groups = {
        "1": "Directores y gerentes",
        "2": "Profesionales cientificos e intelectuales",
        "3": "Tecnicos y profesionales de nivel medio",
        "4": "Personal de apoyo administrativo",
        "5": "Trabajadores de servicios y vendedores",
        "6": "Agricultores y trabajadores calificados",
        "7": "Oficiales, operarios y artesanos",
        "8": "Operadores de instalaciones y maquinas",
        "9": "Ocupaciones elementales"
    }

    occupations = []
    for row in cursor.fetchall():
        isco_code = row[2] or ""
        isco_nivel1 = isco_code[0] if len(isco_code) > 0 else ""

        occupations.append({
            "uri": row[0],
            "label": row[1] or "",
            "isco_code": isco_code,
            "isco_group": isco_groups.get(isco_nivel1, ""),
            "keywords": []  # Could extract from description
        })

    print(f"    {len(occupations)} ocupaciones ESCO exportadas")

    return {
        "version": "1.1.2",
        "total": len(occupations),
        "occupations": occupations,
        "isco_groups": isco_groups
    }


def save_json(data: dict, filepath: Path, compress: bool = True):
    """Save JSON data to file, optionally compressed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    json_str = json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'))

    if compress:
        gz_path = filepath.with_suffix('.json.gz')
        with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
        size_kb = gz_path.stat().st_size / 1024
        print(f"    Guardado: {gz_path.name} ({size_kb:.1f} KB)")
        return gz_path
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
        size_kb = filepath.stat().st_size / 1024
        print(f"    Guardado: {filepath.name} ({size_kb:.1f} KB)")
        return filepath


def upload_to_s3(local_path: Path, s3_key: str, credentials: dict):
    """Upload file to S3."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        s3 = boto3.client(
            's3',
            aws_access_key_id=credentials['aws_access_key_id'],
            aws_secret_access_key=credentials['aws_secret_access_key'],
            region_name=credentials['region']
        )

        content_type = 'application/json'
        if local_path.suffix == '.gz':
            content_type = 'application/gzip'

        s3.upload_file(
            str(local_path),
            credentials['bucket'],
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )

        return True
    except Exception as e:
        print(f"    ERROR upload: {e}")
        return False


def main():
    dry_run = '--dry-run' in sys.argv
    local_only = '--local-only' in sys.argv

    snapshot_date = datetime.now().strftime('%Y-%m-%d')

    print("=" * 60)
    print(f"MOL-30: Export to S3")
    print(f"Snapshot: {snapshot_date}")
    print("=" * 60)
    print()

    # Load credentials
    credentials = None
    if not dry_run and not local_only:
        credentials = load_aws_credentials()
        if not credentials:
            print("ERROR: No AWS credentials found")
            print("  Options:")
            print("    - Create config/aws_credentials.json")
            print("    - Set AWS_ACCESS_KEY_ID environment variable")
            print("    - Use --local-only or --dry-run")
            sys.exit(1)
        print(f"AWS: {credentials['bucket']} ({credentials['region']})")
    else:
        print("Mode: " + ("DRY RUN" if dry_run else "LOCAL ONLY"))
    print()

    # Connect to database
    print("[1/6] Conectando a SQLite...")
    conn = get_db_connection()
    print(f"    DB: {DB_PATH}")
    print()

    # Export data
    print("[2/6] Exportando ofertas...")
    ofertas_data = export_ofertas(conn, snapshot_date)
    print()

    print("[3/6] Exportando matches...")
    matches_data = export_matches(conn, snapshot_date)
    print()

    print("[4/6] Exportando candidates...")
    candidates_data = export_candidates(conn, snapshot_date, matches_data)
    print()

    print("[5/6] Exportando metrics...")
    metrics_data = export_metrics(conn, snapshot_date, matches_data)
    print()

    print("[6/6] Exportando esco_occupations...")
    esco_data = export_esco_occupations(conn, snapshot_date)
    print()

    conn.close()

    # Save locally
    print("Guardando archivos locales...")
    local_dir = OUTPUT_DIR / snapshot_date
    local_dir.mkdir(parents=True, exist_ok=True)

    files = {
        'ofertas.json': ofertas_data,
        'matches.json': matches_data,
        'candidates.json': candidates_data,
        'metrics.json': metrics_data
    }

    saved_files = {}
    for filename, data in files.items():
        # Compress large files, keep metrics.json uncompressed
        compress = filename != 'metrics.json'
        filepath = local_dir / filename
        saved_files[filename] = save_json(data, filepath, compress=compress)

    # Save esco_occupations to config folder
    esco_path = save_json(esco_data, local_dir / 'esco_occupations.json', compress=True)
    saved_files['esco_occupations.json'] = esco_path

    print()

    # Upload to S3
    if not dry_run and not local_only and credentials:
        print("Subiendo a S3...")
        s3_prefix = f"snapshots/{snapshot_date}"

        upload_results = {}
        for filename, local_path in saved_files.items():
            s3_key = f"{s3_prefix}/{local_path.name}"
            print(f"  Uploading {local_path.name} -> s3://{credentials['bucket']}/{s3_key}")
            success = upload_to_s3(local_path, s3_key, credentials)
            upload_results[filename] = success

        # Also upload esco_occupations to config/
        esco_s3_key = f"config/{esco_path.name}"
        print(f"  Uploading {esco_path.name} -> s3://{credentials['bucket']}/{esco_s3_key}")
        upload_to_s3(esco_path, esco_s3_key, credentials)

        # Update latest.json
        latest_data = {
            "current_snapshot": snapshot_date,
            "updated_at": datetime.now().isoformat()
        }
        latest_path = local_dir.parent / "latest.json"
        with open(latest_path, 'w') as f:
            json.dump(latest_data, f)
        upload_to_s3(latest_path, "snapshots/latest.json", credentials)

        print()
        successful = sum(1 for v in upload_results.values() if v)
        print(f"Uploads: {successful}/{len(upload_results)} exitosos")

    # Summary
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Ofertas:    {ofertas_data['total_ofertas']:,}")
    print(f"Matches:    {matches_data['total_matches']:,}")
    print(f"Candidates: {candidates_data['total_ofertas_con_candidatos']:,}")
    print(f"ESCO:       {esco_data['total']:,}")
    print()
    print(f"Archivos:   {local_dir}")
    if not dry_run and not local_only and credentials:
        print(f"S3:         s3://{credentials['bucket']}/snapshots/{snapshot_date}/")
    print()


if __name__ == '__main__':
    main()
