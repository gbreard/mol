#!/usr/bin/env python3
"""SPEC S1C-F0.5-build · Capa 3 — Runner read-only del matcher sobre el Gold Set.

Para cada caso con fila en ofertas_nlp: carga la fila como dict, ejecuta
matcher.match(dict) y captura el MatchResult completo. NUNCA llama
match_and_persist; NUNCA escribe en tablas de producción.

Patrón de carga del matcher reutilizado tal cual de exp_raiz_skills/ (diseño §3.1):
MatcherV3(db_conn=conn, verbose=False), matcher en memoria, BD compartida, sin
persistir. La entrada de match() es la fila ofertas_nlp como dict.
"""

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"

# Tablas de producción que el harness JAMÁS debe modificar. El runner verifica
# que sus conteos no cambian entre antes y después de correr (garantía read-only).
PRODUCTION_TABLES = ["ofertas_esco_matching", "ofertas_esco_skills_detalle", "ofertas_nlp"]


@dataclass
class RunRecord:
    id_oferta: str
    titulo: Optional[str]
    status: Optional[str]
    esco_uri: Optional[str]
    esco_label: Optional[str]
    isco_code: Optional[str]
    isco4: Optional[str]
    score: Optional[float]
    metodo: Optional[str]
    decision_metodo: Optional[str]
    regla_aplicada: Optional[str]


def _isco4(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    c = str(code).lstrip("C")
    return c[:4] if len(c) >= 4 else (c or None)


def _table_counts(conn: sqlite3.Connection) -> Dict[str, int]:
    out = {}
    for t in PRODUCTION_TABLES:
        try:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except sqlite3.Error:
            out[t] = -1
    return out


def run_matcher_over_ids(
    ids: List[str], conn: sqlite3.Connection, verify_readonly: bool = True
) -> List[RunRecord]:
    """Corre matcher.match() read-only sobre una lista de id_oferta.

    Si verify_readonly: snapshota conteos de tablas de producción antes/después
    y lanza RuntimeError si alguno cambió (red de seguridad del contrato read-only).
    """
    sys.path.insert(0, str(PROJECT_ROOT / "database"))
    from match_ofertas_v3 import MatcherV3  # noqa: E402

    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ofertas_nlp)")]

    counts_before = _table_counts(conn) if verify_readonly else {}

    matcher = MatcherV3(db_conn=conn, verbose=False)

    records: List[RunRecord] = []
    for oid in ids:
        row = conn.execute(
            "SELECT * FROM ofertas_nlp WHERE id_oferta=?", (oid,)
        ).fetchone()
        if row is None:
            continue
        nlp = {k: row[k] for k in cols}
        res = matcher.match(nlp)  # read-only: NUNCA match_and_persist
        meta = res.metadata or {}
        records.append(
            RunRecord(
                id_oferta=oid,
                titulo=nlp.get("titulo_limpio") or nlp.get("titulo"),
                status=res.status,
                esco_uri=res.esco_uri,
                esco_label=res.esco_label,
                isco_code=res.isco_code,
                isco4=_isco4(res.isco_code),
                score=round(res.score, 4) if res.score is not None else None,
                metodo=res.metodo,
                decision_metodo=meta.get("decision_metodo"),
                regla_aplicada=meta.get("regla_aplicada"),
            )
        )

    if verify_readonly:
        counts_after = _table_counts(conn)
        if counts_before != counts_after:
            raise RuntimeError(
                f"VIOLACIÓN READ-ONLY: conteos de producción cambiaron.\n"
                f"  antes:  {counts_before}\n  después: {counts_after}"
            )

    return records


if __name__ == "__main__":
    import argparse

    from ground_truth import load_ground_truth_default

    p = argparse.ArgumentParser(description="Runner read-only (capa 3)")
    p.add_argument("--fecha", required=True)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    casos, conn = load_ground_truth_default(args.fecha)
    ids = [c.id_oferta for c in casos]
    if args.limit:
        ids = ids[: args.limit]
    recs = run_matcher_over_ids(ids, conn, verify_readonly=True)
    print(f"Corridos {len(recs)} casos read-only (sin tocar producción).")
    for r in recs[:5]:
        print(f"  {r.id_oferta} -> isco4={r.isco4} esco={r.esco_label!r} metodo={r.decision_metodo}")
    conn.close()
