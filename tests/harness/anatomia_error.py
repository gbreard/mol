#!/usr/bin/env python3
"""SPEC S1C-F0.6 — Discovery de anatomía del error (read-only).

Re-corre el universo consolidado de correcciones de Cyn (312 ofertas) por el
matcher de HOY, sin persistir (patrón runner.py / F0.5), y captura por oferta:
canal de decisión, regla aplicada, ISCO/ESCO resultante. Cruza con el snapshot
de mayo (cambio de canal = información) y con el origen de reglas (_linaje) para
la clasificación de regla-parche.

NO escribe en producción. Guard de conteos read-only heredado de runner.py.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
UNIVERSO = PROJECT_ROOT / "tests" / "harness" / "universo_errores_cyn_2026-06-18.json"
RULES = PROJECT_ROOT / "config" / "matching_rules_business.json"
PRODUCTION_TABLES = ["ofertas_esco_matching", "ofertas_esco_skills_detalle", "ofertas_nlp"]


def isco4(code):
    if not code:
        return None
    c = str(code).lstrip("C")
    return c[:4] if len(c) >= 4 else (c or None)


def canal_familia(metodo_decision, regla_aplicada, metodo):
    """Normaliza el canal a {regla, diccionario, semantico} para los cortes."""
    md = (metodo_decision or "")
    m = (metodo or "")
    if md.startswith("regla") or regla_aplicada:
        return "regla"
    if m.startswith("diccionario_argentino") or md == "diccionario_argentino":
        return "diccionario"
    if md in ("semantico_unico", "dual_coinciden") or m.startswith("skills_first") or m.startswith("semantic"):
        # dual_coinciden = regla y semantico coinciden -> lo decide la regla pero confirma semantico
        if md == "dual_coinciden":
            return "regla"  # hubo regla que coincidio
        return "semantico"
    return "otro"


def _counts(conn):
    out = {}
    for t in PRODUCTION_TABLES:
        try:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except sqlite3.Error:
            out[t] = -1
    return out


def load_rule_origins():
    """_linaje por regla: marcadores de origen humano (Cyn) por-regla.

    Devuelve: rule_id -> dict(autor, oferta_ejemplo, issue_ids, tiene_origen).
    """
    rules = json.load(open(RULES))
    rfi = {k: v for k, v in rules["reglas_forzar_isco"].items() if isinstance(v, dict)}
    origins = {}
    for rid, r in rfi.items():
        lin = r.get("_linaje", {})
        oe = lin.get("oferta_ejemplo")
        # oferta_ejemplo puede traer texto extra: "5924126529 - Tecnico..."
        oe_id = None
        if oe:
            mo = re.match(r"\s*(\w+)", str(oe))
            oe_id = mo.group(1) if mo else None
        iids = lin.get("issue_ids") or ([lin["issue_id"]] if lin.get("issue_id") else [])
        autor = lin.get("autor_correccion")
        tp = lin.get("training_pair_ids")
        marcadores = [f for f in ("issue_ids", "issue_id", "oferta_ejemplo",
                                  "autor_correccion", "training_pair_ids", "spec", "reporte")
                      if lin.get(f)]
        origins[rid] = {
            "autor": autor,
            "oferta_ejemplo_id": oe_id,
            "issue_ids": iids,
            "training_pair_ids": tp,
            "tiene_origen": bool(marcadores),
            "marcadores": marcadores,
            "es_humano_cyn": bool(autor and "Cyn" in str(autor)),
        }
    return origins


def main():
    uni = json.load(open(UNIVERSO))
    casos = uni["casos"]
    ids = list(casos.keys())
    origins = load_rule_origins()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ofertas_nlp)")]
    counts_before = _counts(conn)

    sys.path.insert(0, str(PROJECT_ROOT / "database"))
    from match_ofertas_v3 import MatcherV3
    matcher = MatcherV3(db_conn=conn, verbose=False)

    out = {}
    for oid in ids:
        row = conn.execute("SELECT * FROM ofertas_nlp WHERE id_oferta=?", (oid,)).fetchone()
        if row is None:
            continue
        nlp = {k: row[k] for k in cols}
        res = matcher.match(nlp)
        meta = res.metadata or {}
        md = meta.get("decision_metodo")
        ra = meta.get("regla_aplicada")
        fam = canal_familia(md, ra, res.metodo)
        # regla que decide hoy: extraer id Rxxx
        rid_hoy = None
        if ra:
            rid_hoy = ra
        elif res.metodo and res.metodo.startswith("regla_negocio_"):
            rid_hoy = res.metodo.replace("regla_negocio_", "")
        out[oid] = {
            "isco_hoy": res.isco_code,
            "isco4_hoy": isco4(res.isco_code),
            "esco_label_hoy": res.esco_label,
            "esco_uri_hoy": res.esco_uri,
            "score_hoy": round(res.score, 4) if res.score is not None else None,
            "metodo_hoy": res.metodo,
            "decision_metodo_hoy": md,
            "regla_aplicada_hoy": ra,
            "rid_hoy": rid_hoy,
            "canal_familia_hoy": fam,
        }

    counts_after = _counts(conn)
    if counts_before != counts_after:
        raise RuntimeError(f"VIOLACION READ-ONLY: {counts_before} != {counts_after}")
    conn.close()

    result = {
        "spec": "SPEC_S1C_F06_ANATOMIA_ERROR",
        "fecha_recorrida": "2026-06-18",
        "n_recorridas": len(out),
        "resultado_hoy": out,
        "rule_origins": origins,
    }
    dest = PROJECT_ROOT / "tests" / "harness" / "anatomia_recorrida_2026-06-18.json"
    json.dump(result, open(dest, "w"), ensure_ascii=False, indent=2)
    print(f"Re-corridas {len(out)} ofertas read-only (conteos producción intactos).")
    print(f"Guardado: {dest}")


if __name__ == "__main__":
    main()
