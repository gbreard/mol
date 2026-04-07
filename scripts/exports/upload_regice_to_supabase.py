"""
Carga tablas REGICE desde Voucher PostgreSQL local a Supabase.
Prerequisito: ejecutar 053_regice_tables_supabase.sql en Supabase primero.

Uso:
    python scripts/exports/upload_regice_to_supabase.py
    python scripts/exports/upload_regice_to_supabase.py --dry-run
"""

import json
import sys
import time
import psycopg2
from supabase import create_client

# Voucher PG local
VOUCHER_DSN = "host=localhost port=5433 dbname=voucher user=voucher password=voucher_dev"

# Supabase
config = json.load(open("config/supabase_config.json"))
supabase = create_client(config["url"], config["service_role_key"])

BATCH_SIZE = 500
DRY_RUN = "--dry-run" in sys.argv


def fetch_all(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows


def upsert_batch(table, rows, batch_size=BATCH_SIZE):
    if DRY_RUN:
        print(f"  [dry-run] Would upsert {len(rows)} rows to {table}")
        return
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        supabase.table(table).upsert(batch).execute()
        print(f"  {table}: {min(i + batch_size, len(rows))}/{len(rows)}")
        time.sleep(0.3)


def main():
    conn = psycopg2.connect(VOUCHER_DSN)
    print("Connected to Voucher PG")

    # 1. regice_sedes
    print("\n=== regice_sedes ===")
    rows = fetch_all(conn, "SELECT sede_code, descripcion, tipo_efector, provincia, municipio, lat, lon FROM regice_sedes")
    print(f"  Fetched {len(rows)} rows")
    upsert_batch("regice_sedes", rows)

    # 2. regice_cursos
    print("\n=== regice_cursos ===")
    rows = fetch_all(conn, "SELECT id, denominacion, denominacion_orig, grupo, carga_horaria_modal FROM regice_cursos")
    print(f"  Fetched {len(rows)} rows")
    upsert_batch("regice_cursos", rows)

    # 3. regice_cursos_sedes
    print("\n=== regice_cursos_sedes ===")
    rows = fetch_all(conn, """
        SELECT id, clave_curso, sede_code, curso_id, modalidad,
               anio_inicio, mes_inicio, anio_fin, carga_horaria, contraparte,
               matricula, mat_femenina, mat_18_24, mat_fomentar, mat_vat
        FROM regice_cursos_sedes
    """)
    print(f"  Fetched {len(rows)} rows")
    upsert_batch("regice_cursos_sedes", rows)

    # 4. regice_cursos_esco
    print("\n=== regice_cursos_esco ===")
    rows = fetch_all(conn, """
        SELECT id, curso_id, occupation_uri, classification_method,
               classification_score, role, status, notes
        FROM regice_cursos_esco
    """)
    print(f"  Fetched {len(rows)} rows")
    upsert_batch("regice_cursos_esco", rows)

    # 5. regice_cursos_skills
    print("\n=== regice_cursos_skills ===")
    rows = fetch_all(conn, "SELECT id, curso_id, skill_uri, skill_label, source FROM regice_cursos_skills")
    print(f"  Fetched {len(rows)} rows")
    upsert_batch("regice_cursos_skills", rows)

    conn.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
