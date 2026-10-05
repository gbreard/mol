# -*- coding: utf-8 -*-
"""[CASCADA v12.4 — P0] Snapshot pre-cascada: el camino de vuelta + la fuente del linaje viejo.

Congela las TRES capas del universo antes de re-extraer tareas:
  - tareas_v11   : ofertas_nlp (tareas_explicitas/inferidas + nlp_version + multi-pos)
  - skills       : ofertas_esco_skills_detalle (v11-derivadas; NO se re-derivan en esta cascada)
  - matching     : ofertas_esco_matching (pre-re-matching; candado F0.4b lo preserva)
Dump .jsonl.gz por capa (quedan EN DISCO, no viajan a git) + MANIFIESTO con sha256.
Patrón del frente L (exports/cohorts/snapshot_pre_rematching_2026-08-19_*).

Uso:  python scripts/ops/snapshot_cascada.py --fecha 2026-10-05
"""
import argparse
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'database' / 'bumeran_scraping.db'
OUTDIR = ROOT / 'exports' / 'cohorts'

CAPAS = {
    'tareas_v11': "SELECT id_oferta, nlp_version, tareas_explicitas, tareas_inferidas, "
                  "es_suboferta, numero_suboferta, parent_id_oferta, multi_position_status, "
                  "nlp_gate_status FROM ofertas_nlp",
    'matching': "SELECT id_oferta, esco_occupation_uri, esco_occupation_label, "
                "occupation_match_score, occupation_match_method, titulo_esco_code, "
                "matching_version, estado_validacion, decision_metodo, confidence_score, "
                "rerank_score, score_titulo, score_skills FROM ofertas_esco_matching",
    'skills': "SELECT id, id_oferta, skill_mencionado, esco_skill_uri, esco_skill_label, "
              "match_score, match_method, origen_tipo, source_classification "
              "FROM ofertas_esco_skills_detalle",
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fecha', required=True)
    args = ap.parse_args()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    archivos = {}
    for capa, q in CAPAS.items():
        out = OUTDIR / f'snapshot_pre_cascada_{args.fecha}_{capa}.jsonl.gz'
        n = 0
        with gzip.open(out, 'wt', encoding='utf-8') as gz:
            for row in con.execute(q):
                gz.write(json.dumps({k: row[k] for k in row.keys()}, ensure_ascii=False) + '\n')
                n += 1
        sz = out.stat().st_size
        archivos[str(out.relative_to(ROOT))] = {'sha256': _sha256(out), 'bytes': sz, 'filas': n}
        print(f'  {capa:12} {n:>9} filas  {sz/1e6:.1f} MB  -> {out.name}', flush=True)

    # censo del candado
    cand = {k: con.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE {c}").fetchone()[0]
            for k, c in {'validado': "estado_validacion='validado'",
                         'en_revision': "estado_validacion='en_revision'",
                         'rule_manual_fix': "occupation_match_method='rule_manual_fix'"}.items()}
    manifiesto = {
        '_meta': {
            'proposito': '[CASCADA v12.4] Snapshot PRE-cascada (reversibilidad + linaje viejo). '
                         'Los .gz quedan EN DISCO; este manifiesto los registra con sha256.',
            'generado': args.fecha,
            'extractor_destino': 'tareas v12.4 (frente N: 16 RG-TAR, qwen2.5:14b)',
            'capas_congeladas': 'tareas_v11 (se reemplazan) + skills (v11, NO se re-derivan acá) '
                                '+ matching (pre-re-matching, candado F0.4b)',
            'candado_F0.4b': cand,
            'candado_total': sum(cand.values()),
            'nota_candado': 'El candado protege DECISIONES de matching; las TAREAS de estas filas '
                            'SÍ se re-extraen (laudo). Skills: ventana abierta hasta el frente O.',
        },
        'archivos': archivos,
    }
    man = OUTDIR / f'snapshot_pre_cascada_{args.fecha}_MANIFIESTO.json'
    man.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1))
    print(f'\nMANIFIESTO -> {man}')
    print(f'candado total: {sum(cand.values())}  {cand}')


if __name__ == '__main__':
    main()
