# -*- coding: utf-8 -*-
"""[CASCADA — laudo 2] Delta contador: re-extraer con v12.5 las vacías con "para+acción".

Lee los ids congelados (exports/cohorts/laudo2_delta_ids.json), corre el pipeline v12.5
(N1→v12.5→N3) y ACTUALIZA la fila del staging. La auto-discriminación del prompt es el
filtro: voltea solo cuando "para" atribuye función real; el resto queda [] (sin daño).
Preserva el valor previo (tareas_json_pre_delta2) y marca delta2_flip (1=volteó, 0=sigue []).
Escribe solo a cascada_staging.db.

Uso:  OLLAMA_HOST=172.17.0.1 python scripts/ops/laudo2_delta_contador.py
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / 'database' / 'cascada_staging.db'
IDS = ROOT / 'exports' / 'cohorts' / 'laudo2_delta_ids.json'
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
os.environ.setdefault('MODEL_TAREAS', 'qwen2.5:14b')
from gate_runner import correr_caso, MODEL   # noqa: E402


def main():
    ids = json.loads(IDS.read_text())['ids']
    con = sqlite3.connect(f'file:{STAGING}', uri=True, timeout=120)
    con.execute('PRAGMA busy_timeout=120000')
    cols = [r[1] for r in con.execute("PRAGMA table_info(ofertas_nlp_tareas_v124)")]
    for c in ('tareas_json_pre_delta2', 'delta2_flip'):
        if c not in cols:
            tipo = 'INTEGER' if c == 'delta2_flip' else 'TEXT'
            con.execute(f"ALTER TABLE ofertas_nlp_tareas_v124 ADD COLUMN {c} {tipo}")
    con.execute(f"ATTACH DATABASE 'file:{ROOT/'database/bumeran_scraping.db'}?mode=ro' AS src")
    con.commit()

    bodies = {}
    B = 900
    for i in range(0, len(ids), B):
        ch = ids[i:i + B]
        q = ("SELECT CAST(id_oferta AS TEXT), portal, COALESCE(descripcion_utf8,descripcion) "
             "FROM src.ofertas WHERE CAST(id_oferta AS TEXT) IN (%s)" % ",".join("?" * len(ch)))
        for oid, portal, d in con.execute(q, ch):
            bodies[oid] = (portal, d)

    t0 = time.time()
    flips = 0
    for n, oid in enumerate(ids, 1):
        portal, d = bodies.get(oid, (None, None))
        if not d:
            continue
        try:
            tareas = correr_caso(d, portal)['v12_final']
        except Exception:
            continue
        flip = 1 if tareas else 0
        flips += flip
        prev = con.execute("SELECT tareas_json FROM ofertas_nlp_tareas_v124 WHERE id_oferta=?", (oid,)).fetchone()
        con.execute("UPDATE ofertas_nlp_tareas_v124 SET tareas_json_pre_delta2=?, tareas_json=?, "
                    "n_tareas=?, delta2_flip=?, tanda='delta_contador' WHERE id_oferta=?",
                    (prev[0] if prev else None, json.dumps(tareas, ensure_ascii=False),
                     len(tareas), flip, oid))
        if n % 50 == 0:
            con.commit()
            print(f'  [{n}/{len(ids)}] {n/(time.time()-t0)*3600:.0f} of/h  flips={flips}', flush=True)
    con.commit()
    print(f'\n[delta contador] {len(ids)} procesados en {(time.time()-t0)/60:.1f} min')
    print(f'  flips (vacío→tarea): {flips}  ({100*flips/max(len(ids),1):.1f}%)  siguen []: {len(ids)-flips}')
    con.close()


if __name__ == '__main__':
    main()
