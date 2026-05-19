#!/usr/bin/env python3
"""
Ingesta de gold set desde 3 fuentes a tabla Supabase `gold_set`:
1. Excel Cyn 2026-05-08 (SPEC W, sub-ocupaciones bizarras): 30 ofertas
2. ofertas_dashboard.validacion_humana (ok/error): 9 ofertas
3. ofertas_esco_matching.validado_por humano explícito: 25 ofertas

Total esperado: 63 nuevos → gold_set pasa de 49 a 112.

Uso:
    python scripts/ingest_gold_set.py [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
from supabase import create_client

REPO = Path(__file__).resolve().parents[1]
DB_PATH = REPO / "database" / "bumeran_scraping.db"
CONFIG = REPO / "config" / "supabase_config.json"
EXCEL_CYN = REPO / "data" / "spec_u1" / "validacion_humana_B2_completado_Cyn_20260508.xlsx"

# Versión actual del matcher (lee del archivo de versión)
MATCHER_VERSION = (REPO / "database" / "MATCHER_VERSION").read_text().strip()


def load_excel_cyn():
    """30 ofertas del Excel SPEC W validado por Cyn."""
    wb = openpyxl.load_workbook(EXCEL_CYN, read_only=True)
    ws = wb["Validacion B2"]

    rows = []
    header = None
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header = list(row)
            continue
        if not row[0]:
            continue
        rec = dict(zip(header, row))
        evaluacion = (rec.get("evaluacion") or "").lower().strip()
        esco_ok = evaluacion == "ok"
        comentario_partes = [
            rec.get("comentario") or "",
            rec.get("clasificacion_correcta_libre") or "",
        ]
        comentario = " | ".join(p for p in comentario_partes if p).strip()
        isco_esperado = rec.get("sub_codigo_esco_sugerido_cyn") if not esco_ok else None
        esco_esperado = rec.get("label_canonico_segun_cyn") if not esco_ok else None
        fecha_rev = rec.get("fecha_revision")
        if fecha_rev and not isinstance(fecha_rev, str):
            fecha_rev = fecha_rev.isoformat()
        rows.append({
            "id_oferta": str(rec["id_oferta"]),
            "esco_ok": esco_ok,
            "isco_esperado": str(isco_esperado) if isco_esperado else None,
            "esco_esperado": esco_esperado,
            # tipo_error solo si encaja en el check constraint: dominio_incorrecto, homonimia, nivel_jerarquico, rol_primario
            "tipo_error": None,
            "comentario": comentario or f"Excel SPEC W Cyn — evaluacion={evaluacion}",
            "agregado_por": rec.get("revisado_por") or "cinvazquez4@gmail.com",
            "agregado_at": fecha_rev or "2026-05-08T00:00:00+00:00",
            "version_reglas": MATCHER_VERSION,
            "activo": True,
        })
    return rows


def load_validacion_humana(client):
    """9 ofertas con ofertas_dashboard.validacion_humana ok/error."""
    r = client.table("ofertas_dashboard").select(
        "id_oferta,validacion_humana,validacion_humana_por,validacion_humana_at"
    ).in_("validacion_humana", ["ok", "error"]).execute()

    rows = []
    for v in r.data:
        esco_ok = v["validacion_humana"] == "ok"
        rows.append({
            "id_oferta": str(v["id_oferta"]),
            "esco_ok": esco_ok,
            "isco_esperado": None,
            "esco_esperado": None,
            "tipo_error": None,  # no clasificable con los valores del check constraint
            "comentario": f"validacion_humana={v['validacion_humana']} (ofertas_dashboard)",
            "agregado_por": v.get("validacion_humana_por") or "unknown",
            "agregado_at": v.get("validacion_humana_at") or datetime.now(timezone.utc).isoformat(),
            "version_reglas": MATCHER_VERSION,
            "activo": True,
        })
    return rows


def load_validado_humano_local():
    """25 ofertas validadas por humano explícito en local."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT id_oferta, validado_por, estado_validacion
        FROM ofertas_esco_matching
        WHERE validado_por IN ('manual', 'claude_issues_cynthia_r2',
                               'claude_issues_diego_gerardo', 'claude_revision_manual')
    """)

    rows = []
    for r in cursor:
        rows.append({
            "id_oferta": str(r["id_oferta"]),
            "esco_ok": True,  # "validado" = OK confirmado por humano
            "isco_esperado": None,
            "esco_esperado": None,
            "tipo_error": None,
            "comentario": f"validado_por={r['validado_por']} (BD local)",
            "agregado_por": r["validado_por"],
            "agregado_at": "2026-05-01T00:00:00+00:00",  # fecha aproximada
            "version_reglas": MATCHER_VERSION,
            "activo": True,
        })
    conn.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    client = create_client(config["url"], config["service_role_key"])

    # Existing ids en gold_set
    existing = client.table("gold_set").select("id_oferta").execute()
    existing_ids = {str(r["id_oferta"]) for r in existing.data}
    print(f"gold_set actual: {len(existing_ids)} ids")

    # Cargar de 3 fuentes
    fuentes = [
        ("Excel Cyn SPEC W", load_excel_cyn()),
        ("ofertas_dashboard.validacion_humana", load_validacion_humana(client)),
        ("validado_por humano local", load_validado_humano_local()),
    ]

    # Dedupe contra existing + entre fuentes (prioridad: Excel > validacion_humana > local)
    todos = {}  # id_oferta → record
    for nombre, registros in fuentes:
        nuevos = [r for r in registros if r["id_oferta"] not in existing_ids]
        antes = len(todos)
        for r in nuevos:
            if r["id_oferta"] not in todos:
                todos[r["id_oferta"]] = r
        print(f"  {nombre}: {len(registros)} total, {len(nuevos)} no en gold_set, {len(todos) - antes} sumados (sin colisión interna)")

    print(f"\nTotal nuevos únicos a insertar: {len(todos)}")

    if args.dry_run:
        print("\n--- DRY RUN ---")
        for r in list(todos.values())[:3]:
            print(f"  {r}")
        return 0

    # Insertar en batches
    to_insert = list(todos.values())
    batch_size = 50
    inserted = 0
    errors = []
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i:i + batch_size]
        try:
            client.table("gold_set").insert(batch).execute()
            inserted += len(batch)
            print(f"  Batch {i // batch_size + 1}: +{len(batch)}")
        except Exception as e:
            errors.append(str(e)[:200])
            print(f"  Batch {i // batch_size + 1} FALLA: {e}")

    print(f"\nResultado: insertados {inserted}/{len(to_insert)}")
    final = client.table("gold_set").select("id_oferta", count="exact", head=True).execute()
    print(f"gold_set total ahora: {final.count}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
