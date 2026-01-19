#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare Runs v2.0 - Comparar dos corridas del pipeline (BD-centric)
===================================================================

Compara dos runs y muestra:
- Configs que cambiaron
- Diferencia de métricas
- Detalle por oferta (mejoras/regresiones/sin cambio)

**v2.0**: Lee directamente de BD (tabla pipeline_runs), no de archivos JSON.

Uso:
    python scripts/compare_runs.py run_20260113_1550 run_20260112_2023
    python scripts/compare_runs.py --latest  # Compara últimos 2 runs
    python scripts/compare_runs.py --list    # Lista runs disponibles
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Paths
BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"
EXPORTS_DIR = BASE / "exports" / "comparisons"


def get_conn() -> sqlite3.Connection:
    """Obtiene conexión a la BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_run(run_id: str) -> Optional[Dict]:
    """Carga metadata de un run desde BD."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('SELECT * FROM pipeline_runs WHERE run_id = ?', (run_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        result = dict(row)
        # Parsear JSON fields
        if result.get("config_snapshot"):
            result["config_versions"] = json.loads(result["config_snapshot"])
        if result.get("ofertas_ids"):
            result["ofertas_ids"] = json.loads(result["ofertas_ids"])
        if result.get("metricas_detalle"):
            result["errores_por_tipo"] = json.loads(result["metricas_detalle"])
        return result
    return None


def get_latest_runs(n: int = 2) -> List[str]:
    """Obtiene los últimos N run_ids desde BD."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT run_id FROM pipeline_runs
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (n,))

    runs = [row['run_id'] for row in cur.fetchall()]
    conn.close()
    return runs


def compare_configs(run_a: str, run_b: str) -> Dict[str, Dict]:
    """
    Compara configs entre dos runs.

    Returns:
        Dict con configs que cambiaron y sus diferencias
    """
    meta_a = load_run(run_a)
    meta_b = load_run(run_b)

    if not meta_a or not meta_b:
        return {}

    versions_a = meta_a.get("config_versions", {})
    versions_b = meta_b.get("config_versions", {})

    changes = {}

    # Configs en ambos
    all_configs = set(versions_a.keys()) | set(versions_b.keys())

    for config in all_configs:
        v_a = versions_a.get(config, "N/A")
        v_b = versions_b.get(config, "N/A")

        if v_a != v_b:
            changes[config] = {
                "version_anterior": v_a,
                "version_nueva": v_b
            }

    return changes


def compare_metrics(run_a: str, run_b: str) -> Dict:
    """
    Compara métricas entre dos runs.

    Returns:
        Dict con diferencias de métricas
    """
    meta_a = load_run(run_a)
    meta_b = load_run(run_b)

    if not meta_a or not meta_b:
        return {"error": "No se encontraron datos para uno o ambos runs"}

    comparison = {}

    # Métricas numéricas a comparar
    metric_keys = [
        ("metricas_total", "total"),
        ("metricas_correctos", "correctos"),
        ("metricas_parciales", "parciales"),
        ("metricas_errores", "errores"),
        ("metricas_precision", "precision"),
    ]

    for db_key, display_key in metric_keys:
        val_a = meta_a.get(db_key)
        val_b = meta_b.get(db_key)

        if val_a is not None or val_b is not None:
            val_a = val_a or 0
            val_b = val_b or 0
            diff = val_b - val_a

            if isinstance(val_a, float) or isinstance(val_b, float):
                comparison[display_key] = {
                    "anterior": round(val_a, 4),
                    "nuevo": round(val_b, 4),
                    "diferencia": round(diff, 4),
                    "cambio": f"+{diff:.2%}" if diff > 0 else f"{diff:.2%}"
                }
            else:
                comparison[display_key] = {
                    "anterior": val_a,
                    "nuevo": val_b,
                    "diferencia": diff,
                    "cambio": f"+{diff}" if diff > 0 else str(diff)
                }

    return comparison


def compare_offers(run_a: str, run_b: str) -> Dict:
    """
    Compara resultados por oferta entre dos runs.

    Returns:
        Dict con mejoras, regresiones, sin cambio
    """
    meta_a = load_run(run_a)
    meta_b = load_run(run_b)

    if not meta_a or not meta_b:
        return {"error": "No se encontraron metadata para uno o ambos runs"}

    ids_a = set(meta_a.get("ofertas_ids", []))
    ids_b = set(meta_b.get("ofertas_ids", []))

    common_ids = ids_a & ids_b
    only_a = ids_a - ids_b
    only_b = ids_b - ids_a

    return {
        "ofertas_en_ambos": len(common_ids),
        "solo_en_anterior": len(only_a),
        "solo_en_nuevo": len(only_b),
        "ids_comunes": list(common_ids)[:10],  # Primeros 10
        "ids_solo_anterior": list(only_a)[:5],
        "ids_solo_nuevo": list(only_b)[:5]
    }


def compare_isco_changes(run_a: str, run_b: str) -> Dict:
    """
    Compara cambios de ISCO entre dos runs usando la BD.

    Requiere que las ofertas tengan run_id guardado.
    """
    conn = get_conn()
    cur = conn.cursor()

    # Verificar si existe columna run_id
    cur.execute("PRAGMA table_info(ofertas_esco_matching)")
    columns = [row[1] for row in cur.fetchall()]

    if "run_id" not in columns:
        conn.close()
        return {"nota": "Columna run_id no existe aún - comparación limitada"}

    # Obtener ISCO por oferta para cada run
    cur.execute('''
        SELECT id_oferta, isco_code
        FROM ofertas_esco_matching
        WHERE run_id = ?
    ''', (run_a,))
    isco_a = {str(row[0]): row[1] for row in cur.fetchall()}

    cur.execute('''
        SELECT id_oferta, isco_code
        FROM ofertas_esco_matching
        WHERE run_id = ?
    ''', (run_b,))
    isco_b = {str(row[0]): row[1] for row in cur.fetchall()}

    conn.close()

    # Comparar
    cambios = 0
    cambios_detalle = []

    for oferta_id in set(isco_a.keys()) & set(isco_b.keys()):
        if isco_a[oferta_id] != isco_b[oferta_id]:
            cambios += 1
            cambios_detalle.append({
                "id": oferta_id,
                "isco_anterior": isco_a[oferta_id],
                "isco_nuevo": isco_b[oferta_id]
            })

    return {
        "cambios_isco": cambios,
        "ofertas_comparadas": len(set(isco_a.keys()) & set(isco_b.keys())),
        "detalle": cambios_detalle[:10]  # Primeros 10 cambios
    }


def print_comparison(run_a: str, run_b: str):
    """Imprime comparación formateada."""
    print("=" * 70)
    print(f"COMPARACIÓN DE RUNS")
    print(f"  Anterior: {run_a}")
    print(f"  Nuevo:    {run_b}")
    print("=" * 70)

    # Cargar metadata
    meta_a = load_run(run_a)
    meta_b = load_run(run_b)

    if not meta_a:
        print(f"\n[ERROR] Run no encontrado: {run_a}")
        return
    if not meta_b:
        print(f"\n[ERROR] Run no encontrado: {run_b}")
        return

    # Info básica
    print(f"\n--- INFO BÁSICA ---")
    print(f"  Run A: {meta_a.get('timestamp', 'N/A')[:19]}")
    print(f"    Branch: {meta_a.get('git_branch', 'N/A')}")
    print(f"    Ofertas: {meta_a.get('ofertas_count', 0)}")
    print(f"    Matching: {meta_a.get('matching_version', 'N/A')}")
    print(f"  Run B: {meta_b.get('timestamp', 'N/A')[:19]}")
    print(f"    Branch: {meta_b.get('git_branch', 'N/A')}")
    print(f"    Ofertas: {meta_b.get('ofertas_count', 0)}")
    print(f"    Matching: {meta_b.get('matching_version', 'N/A')}")

    # Configs cambiadas
    print(f"\n--- CONFIGS CAMBIADAS ---")
    config_changes = compare_configs(run_a, run_b)
    if config_changes:
        for config, change in config_changes.items():
            print(f"  {config}: {change['version_anterior']} → {change['version_nueva']}")
    else:
        print("  (Sin cambios de versión)")

    # Métricas
    print(f"\n--- MÉTRICAS ---")
    metric_comparison = compare_metrics(run_a, run_b)
    if "error" in metric_comparison:
        print(f"  {metric_comparison['error']}")
    else:
        for metric, data in metric_comparison.items():
            if data.get('anterior') is not None:
                print(f"  {metric}: {data['anterior']} → {data['nuevo']} ({data['cambio']})")

    # Ofertas
    print(f"\n--- OFERTAS ---")
    offer_comparison = compare_offers(run_a, run_b)
    if "error" in offer_comparison:
        print(f"  {offer_comparison['error']}")
    else:
        print(f"  En ambos runs: {offer_comparison['ofertas_en_ambos']}")
        print(f"  Solo en anterior: {offer_comparison['solo_en_anterior']}")
        print(f"  Solo en nuevo: {offer_comparison['solo_en_nuevo']}")

    # Cambios ISCO
    print(f"\n--- CAMBIOS ISCO ---")
    isco_comparison = compare_isco_changes(run_a, run_b)
    if "error" in isco_comparison:
        print(f"  Error: {isco_comparison['error']}")
    elif "nota" in isco_comparison:
        print(f"  {isco_comparison['nota']}")
    else:
        print(f"  Ofertas con cambio de ISCO: {isco_comparison.get('cambios_isco', 0)}")
        if isco_comparison.get('detalle'):
            print("  Ejemplos:")
            for cambio in isco_comparison['detalle'][:5]:
                print(f"    {cambio['id']}: {cambio['isco_anterior']} → {cambio['isco_nuevo']}")

    print("\n" + "=" * 70)


def export_comparison(run_a: str, run_b: str) -> Path:
    """Exporta comparación a JSON."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    comparison = {
        "run_anterior": run_a,
        "run_nuevo": run_b,
        "timestamp": datetime.now().isoformat(),
        "configs_cambiadas": compare_configs(run_a, run_b),
        "metricas": compare_metrics(run_a, run_b),
        "ofertas": compare_offers(run_a, run_b),
        "isco_changes": compare_isco_changes(run_a, run_b)
    }

    filename = f"comparison_{run_a}_vs_{run_b}.json"
    path = EXPORTS_DIR / filename

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print(f"\n[EXPORT] Comparación guardada: {path}")
    return path


def list_runs():
    """Lista runs disponibles en BD."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT run_id, timestamp, source, ofertas_count, metricas_precision,
               matching_version, git_branch
        FROM pipeline_runs
        ORDER BY timestamp DESC
        LIMIT 20
    ''')

    print("\n" + "=" * 80)
    print("RUNS DISPONIBLES")
    print("=" * 80)
    print(f"{'Run ID':<25} {'Fecha':<20} {'Ofertas':>8} {'Prec':>6} {'Version':>8} {'Source':<15}")
    print("-" * 80)

    for row in cur.fetchall():
        run_id = row['run_id']
        ts = row['timestamp'][:16] if row['timestamp'] else 'N/A'
        ofertas = row['ofertas_count'] or 0
        prec = f"{row['metricas_precision']:.2f}" if row['metricas_precision'] else 'N/A'
        version = row['matching_version'] or 'N/A'
        source = row['source'] or 'N/A'
        print(f"{run_id:<25} {ts:<20} {ofertas:>8} {prec:>6} {version:>8} {source:<15}")

    conn.close()
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Comparar dos runs del pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/compare_runs.py run_20260113_1550 run_20260112_2023
  python scripts/compare_runs.py --latest
  python scripts/compare_runs.py --list
  python scripts/compare_runs.py run_a run_b --export
        """
    )
    parser.add_argument("run_a", nargs="?", help="Run ID anterior")
    parser.add_argument("run_b", nargs="?", help="Run ID nuevo")
    parser.add_argument("--latest", action="store_true", help="Comparar últimos 2 runs")
    parser.add_argument("--export", action="store_true", help="Exportar a JSON")
    parser.add_argument("--list", action="store_true", help="Listar runs disponibles")

    args = parser.parse_args()

    if args.list:
        list_runs()
        return

    if args.latest:
        runs = get_latest_runs(2)
        if len(runs) < 2:
            print("No hay suficientes runs para comparar")
            return
        run_a, run_b = runs[1], runs[0]  # Antiguo, Nuevo
    else:
        if not args.run_a or not args.run_b:
            parser.print_help()
            return
        run_a, run_b = args.run_a, args.run_b

    print_comparison(run_a, run_b)

    if args.export:
        export_comparison(run_a, run_b)


if __name__ == "__main__":
    main()
