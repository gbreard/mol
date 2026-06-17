#!/usr/bin/env python3
"""SPEC S1C-F0.5-build · Capa 1 — Bajada del Gold Set a snapshot local fechado.

Script hermano de scripts/sync_gold_set.py. La diferencia crítica es el DESTINO:
sync_gold_set.py escribe en database/gold_set_manual_v2.json (el archivo que
consume la regresión vieja de 49 casos). Este script escribe SOLO en
tests/harness/gold_set_snapshot_<fecha>.json y NUNCA toca el archivo de la
regresión — ese aislamiento es el blindaje del diseño (sección 4 del diseño).

El snapshot es un acto deliberado y versionado (su propio commit), NO un espejo
vivo: el ground truth no se mueve entre la medición de la config A y la B.

Read-only sobre Supabase; escritura local exclusiva en tests/harness/.

Uso:
    python3 tests/harness/download_snapshot.py --fecha 2026-06-17
    python3 tests/harness/download_snapshot.py --dry-run
"""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_DIR = Path(__file__).resolve().parent

# Blindaje: este script JAMÁS escribe acá. Solo lo nombramos para que el guard
# de abajo verifique que no estamos por pisarlo.
REGRESSION_FILE = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"


def snapshot_path(fecha: str) -> Path:
    return HARNESS_DIR / f"gold_set_snapshot_{fecha}.json"


def download_snapshot(fecha: str, dry_run: bool = False) -> dict:
    """Baja gold_set (activo=True) de Supabase y arma el snapshot del harness.

    Devuelve el dict del snapshot (también lo escribe a disco salvo dry_run).
    """
    config_path = PROJECT_ROOT / "config" / "supabase_config.json"
    config = json.loads(config_path.read_text())
    from supabase import create_client

    client = create_client(config["url"], config["service_role_key"])

    result = (
        client.table("gold_set")
        .select("id_oferta,esco_ok,isco_esperado,esco_esperado,tipo_error,comentario")
        .eq("activo", True)
        .order("id")
        .execute()
    )
    rows = result.data or []

    casos = []
    for row in rows:
        isco_esp = row.get("isco_esperado") or None
        esco_esp = row.get("esco_esperado") or None
        esco_ok = bool(row.get("esco_ok"))
        # Un caso es "true sin esperado explícito" cuando esco_ok=True y no trae
        # ni isco_esperado ni esco_esperado. Su target implícito (el output del
        # baseline) se captura en la capa 4 (criterio de aceptación 2).
        es_true_sin_esperado = esco_ok and not isco_esp and not esco_esp
        casos.append(
            {
                "id_oferta": row["id_oferta"],
                "esco_ok": esco_ok,
                "isco_esperado": isco_esp,
                "esco_esperado": esco_esp,
                "tipo_error": row.get("tipo_error") or None,
                "comentario": row.get("comentario") or None,
                "es_true_sin_esperado": es_true_sin_esperado,
            }
        )

    n_ok = sum(1 for c in casos if c["esco_ok"])
    snapshot = {
        "spec": "S1C-F0.5-build",
        "fecha_snapshot": fecha,
        "fuente": "supabase.gold_set (activo=True)",
        "nota": (
            "Snapshot fechado del ground truth para el harness de ocupación. "
            "NO sustituye database/gold_set_manual_v2.json (regresión vieja de 49)."
        ),
        "totales": {
            "n_casos": len(casos),
            "n_esco_ok_true": n_ok,
            "n_esco_ok_false": len(casos) - n_ok,
            "n_con_isco_esperado": sum(1 for c in casos if c["isco_esperado"]),
            "n_con_esco_esperado": sum(1 for c in casos if c["esco_esperado"]),
            "n_true_sin_esperado": sum(1 for c in casos if c["es_true_sin_esperado"]),
        },
        "casos": casos,
    }

    out = snapshot_path(fecha)
    # Guard de blindaje: jamás escribir sobre el archivo de la regresión vieja.
    if out.resolve() == REGRESSION_FILE.resolve():
        raise RuntimeError(
            "BLINDAJE: el snapshot intentó escribir sobre gold_set_manual_v2.json"
        )

    print(f"Supabase gold_set (activo=True): {len(casos)} casos")
    for k, v in snapshot["totales"].items():
        print(f"  {k}: {v}")

    if dry_run:
        print("[DRY-RUN] No se escribe archivo.")
        return snapshot

    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSnapshot guardado: {out.relative_to(PROJECT_ROOT)}")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description="Bajada del Gold Set a snapshot del harness")
    parser.add_argument(
        "--fecha",
        required=True,
        help="Fecha del snapshot (YYYY-MM-DD), va en el nombre del archivo",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    download_snapshot(args.fecha, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
