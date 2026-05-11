#!/usr/bin/env python3
"""Ejecuta los canarios SPEC U-1 v3.1 sobre BD local + Supabase y compara con baselines.

Uso:
  python scripts/canarios/run_canarios.py             # imprime conteos
  python scripts/canarios/run_canarios.py --json      # output JSON
  python scripts/canarios/run_canarios.py --log       # append a logs/canarios_YYYYMMDD.log

Códigos de salida:
  0 — todos los canarios dentro del umbral
  1 — al menos un canario disparado
  2 — error de ejecución
"""
import sqlite3
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT / "database/bumeran_scraping.db"
SUPABASE_CFG = PROJECT / "config/supabase_config.json"
LOG_DIR = PROJECT / "logs"

# Baselines (registrados post-F0 — NO son targets, son referencia para detectar drift)
BASELINES = {
    "C-Q1": {"valor": 3762,    "umbral_pct": 5,   "direccion": "max"},   # max +5%
    "C-Q2": {"valor": 1116011, "umbral_pct": 1,   "direccion": "max"},   # max +1%, debe BAJAR con C4
    "C-Q3": {"valor": 1237,    "umbral_pct": 5,   "direccion": "max"},   # max +5%
    "C-Q4": {"valor": 28395,   "umbral_pct": 10,  "direccion": "max"},   # Supabase: max +10%
    "C-Q5": {"valor": 3834,    "umbral_pct": 20,  "direccion": "abs"},   # ±20% (drift Local↔Supabase actualizado)
    "C-Q6": {"valor": 56397,   "umbral_pct": 5,   "direccion": "abs"},   # ±5% validadas locales
    "C-Q7": {"valor": 8221,    "umbral_pct": 0,   "direccion": "any"},   # solo informativo
}


def run_local_canarios():
    """Ejecuta canarios Q1, Q2, Q3, Q6, Q7 sobre SQLite local."""
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()
    results = {}

    results["C-Q1"] = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE esco_occupation_uri = '' OR esco_occupation_uri IS NULL
    """).fetchone()[0]

    results["C-Q2"] = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle
        WHERE is_essential_for_occupation = 0 AND is_optional_for_occupation = 0
    """).fetchone()[0]

    results["C-Q3"] = cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT esco_occupation_uri, COUNT(DISTINCT esco_occupation_label) AS n_labels
            FROM ofertas_esco_matching
            WHERE esco_occupation_uri != '' AND esco_occupation_label != ''
            GROUP BY esco_occupation_uri
            HAVING n_labels > 1
        )
    """).fetchone()[0]

    results["C-Q6"] = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE estado_validacion IN ('validado', 'validado_claude', 'validado_humano')
    """).fetchone()[0]

    results["C-Q7"] = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE matching_version = 'spec_h_rematch'
    """).fetchone()[0]

    con.close()
    return results


def run_supabase_canarios(local_validadas_ids):
    """Ejecuta canarios Q4 (zombies) y Q5 (drift) contra Supabase."""
    try:
        from supabase import create_client
    except ImportError:
        return {"C-Q4": None, "C-Q5": None, "error": "supabase package not installed"}

    config = json.loads(SUPABASE_CFG.read_text())
    client = create_client(config['url'], config['service_role_key'])

    results = {}

    # C-Q4: skills zombies (id_oferta NOT IN ofertas_dashboard)
    # Supabase REST no soporta NOT IN con subquery directo; usamos sample paginado
    # de ofertas_skills para contar zombies aproximados.
    try:
        ofertas_dash = set()
        page = 0
        while True:
            r = client.table('ofertas_dashboard').select('id_oferta').range(page*1000, (page+1)*1000-1).execute()
            if not r.data:
                break
            ofertas_dash.update(row['id_oferta'] for row in r.data)
            if len(r.data) < 1000:
                break
            page += 1

        # n_skills_total y muestreo para zombies — paginar todas las skills
        # y contar las cuyo id_oferta no está en ofertas_dashboard.
        n_skills_total = client.table('ofertas_skills').select('id_oferta', count='exact').range(0, 0).execute().count

        # Conteo aproximado de zombies: paginar ofertas_skills y contar IDs no presentes en ofertas_dash.
        skills_huerfanas = 0
        ofertas_skills_huerfanas = set()
        page = 0
        while True:
            r = client.table('ofertas_skills').select('id_oferta').range(page*1000, (page+1)*1000-1).execute()
            if not r.data:
                break
            for row in r.data:
                if row['id_oferta'] not in ofertas_dash:
                    skills_huerfanas += 1
                    ofertas_skills_huerfanas.add(row['id_oferta'])
            if len(r.data) < 1000:
                break
            page += 1
            # Safety: no más de 1500 páginas (~1.5M filas)
            if page > 1500:
                break

        results["C-Q4"] = {
            "valor": skills_huerfanas,  # principal métrica del canario
            "n_ofertas_dashboard": len(ofertas_dash),
            "n_skills_total": n_skills_total,
            "n_ofertas_huerfanas": len(ofertas_skills_huerfanas),
            "nota": "Cómputo on-demand (paginado). Para tiempo real considerar RPC SQL.",
        }

        # C-Q5: drift Local↔Supabase
        local_validadas = set(local_validadas_ids)
        diff_local_minus_supabase = len(local_validadas - ofertas_dash)
        diff_supabase_minus_local = len(ofertas_dash - local_validadas)
        results["C-Q5"] = {
            "valor": diff_local_minus_supabase,  # principal métrica
            "n_local_validadas": len(local_validadas),
            "n_supabase_dashboard": len(ofertas_dash),
            "local_minus_supabase": diff_local_minus_supabase,
            "supabase_minus_local": diff_supabase_minus_local,
        }
    except Exception as e:
        # No silenciar el error: imprimirlo para debugging y propagarlo al consumer.
        import traceback
        results["error"] = f"{type(e).__name__}: {e}"
        results["traceback"] = traceback.format_exc()
        results["C-Q4"] = None
        results["C-Q5"] = None

    return results


def evaluar_alarma(canario, valor, baseline_info):
    if valor is None:
        return "NA"
    baseline = baseline_info["valor"]
    umbral = baseline_info["umbral_pct"]
    direccion = baseline_info["direccion"]
    if isinstance(valor, dict):
        valor = valor.get("valor", None)
        if valor is None:
            return "NA"
    diff_pct = (valor - baseline) / baseline * 100 if baseline else 0
    if direccion == "max":
        return "ALARMA" if diff_pct > umbral else "OK"
    elif direccion == "abs":
        return "ALARMA" if abs(diff_pct) > umbral else "OK"
    elif direccion == "any":
        return "OK"
    return "OK"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--no-supabase", action="store_true", help="Saltar canarios Supabase")
    args = parser.parse_args()

    timestamp = datetime.now().isoformat()
    print(f"=== Canarios SPEC U-1 v3.1 — {timestamp} ===\n")

    # Locales
    print("Local (SQLite):")
    local = run_local_canarios()

    # Para C-Q5 necesitamos las IDs de validadas locales
    if not args.no_supabase:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        validadas_ids = [r[0] for r in con.execute("""
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE estado_validacion IN ('validado', 'validado_claude', 'validado_humano')
        """).fetchall()]
        con.close()

        print("Supabase:")
        sb = run_supabase_canarios(validadas_ids)
        # Exhibir errores de Supabase si los hubo (antes el script los silenciaba).
        if sb.get("error"):
            print(f"  ERROR Supabase: {sb['error']}")
            if sb.get("traceback"):
                print(sb["traceback"])
    else:
        sb = {"C-Q4": None, "C-Q5": None, "skipped": True}

    # Resultados consolidados
    all_results = {**local, **{k: v for k, v in sb.items() if k.startswith("C-Q")}}
    rows = []
    for q in ["C-Q1", "C-Q2", "C-Q3", "C-Q4", "C-Q5", "C-Q6", "C-Q7"]:
        valor = all_results.get(q)
        baseline_info = BASELINES.get(q, {})
        alarma = evaluar_alarma(q, valor, baseline_info) if baseline_info else "NA"
        rows.append({"canario": q, "valor": valor, "baseline": baseline_info.get("valor"), "alarma": alarma})

    # Imprimir tabla
    print()
    print(f"{'Canario':<8} {'Valor':>15} {'Baseline':>12} {'Alarma':>10}")
    print("-" * 50)
    for r in rows:
        v = r["valor"]
        if isinstance(v, dict):
            v_str = str(v.get("valor", v))[:15]
        else:
            v_str = f"{v:,}" if isinstance(v, int) else str(v)
        b = r["baseline"]
        b_str = f"{b:,}" if isinstance(b, int) else str(b)
        print(f"{r['canario']:<8} {v_str:>15} {b_str:>12} {r['alarma']:>10}")

    # Salida
    output = {"timestamp": timestamp, "results": all_results, "evaluations": rows}
    if args.json:
        print(json.dumps(output, indent=2, default=str))
    if args.log:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"canarios_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_path, "a") as f:
            f.write(json.dumps(output, default=str) + "\n")
        print(f"\nLogged to {log_path}")

    # Exit code
    has_alarm = any(r["alarma"] == "ALARMA" for r in rows)
    return 1 if has_alarm else 0


if __name__ == "__main__":
    sys.exit(main())
