# -*- coding: utf-8 -*-
"""[CASCADA v12.4 — P1] Re-extracción de TAREAS con el pipeline del frente N.

N1 (limpiar_chrome) → prompt v12.4 → N3 (postfiltro), modelo qwen2.5:14b.
Escribe a una tabla de STAGING (ofertas_nlp_tareas_v124), NO a la tabla viva:
el reemplazo de tareas_explicitas es un paso posterior con el OK de Gerardo
(punto de control P1). Tandas con checkpoint, log y medición de throughput.

Uso:
  # checkpoint (medir throughput con GPU libre, no toca tareas vivas):
  OLLAMA_HOST=172.17.0.1 python scripts/ops/reextraccion_tareas_v124.py --limit 40
  # tanda nombrada (para el run completo, tras OK):
  OLLAMA_HOST=172.17.0.1 python scripts/ops/reextraccion_tareas_v124.py --limit 2000 --tanda t01
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'database' / 'bumeran_scraping.db'
# STAGING en DB PROPIA: el main DB tiene escritores continuos (sync_scraping_dinamica,
# pipeline_command_poller cada minuto, scraping crons) → 'database is locked'. El runner
# LEE el main en modo RO (los lectores WAL nunca bloquean) y ESCRIBE solo a este archivo.
STAGING_DB = ROOT / 'database' / 'cascada_staging.db'
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
os.environ.setdefault('MODEL_TAREAS', 'qwen2.5:14b')
from gate_runner import correr_caso, MODEL   # noqa: E402

STAGING_DDL = """
CREATE TABLE IF NOT EXISTS ofertas_nlp_tareas_v124 (
  id_oferta TEXT PRIMARY KEY,
  tareas_json TEXT,
  n_tareas INTEGER,
  postfiltradas_json TEXT,
  modelo TEXT,
  dur_ms INTEGER,
  tanda TEXT,
  ts TEXT
)"""


def _conectar():
    """Conexión de ESCRITURA al staging propio + ATTACH del main DB como RO (src)."""
    con = sqlite3.connect(f'file:{STAGING_DB}', uri=True, timeout=120)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=120000')
    con.execute(STAGING_DDL)
    con.execute(f"ATTACH DATABASE 'file:{DB}?mode=ro' AS src")
    con.commit()
    return con


def _candidatos(con, limit):
    """Ofertas a re-extraer: primarias con descripción procesable, no hechas aún.
    Orden: más recientes primero. Lee de src (main RO), excluye el staging local."""
    cols = [r[1] for r in con.execute("PRAGMA src.table_info(ofertas)")]
    fecha = next((c for c in ('fecha_publicacion', 'scrapeado_en', 'fecha_scraping', 'created_at')
                  if c in cols), 'id_oferta')
    q = f"""
      SELECT n.id_oferta, o.portal, COALESCE(o.descripcion_utf8, o.descripcion) AS desc
      FROM src.ofertas_nlp n
      JOIN src.ofertas o ON CAST(o.id_oferta AS TEXT) = n.id_oferta
      WHERE (n.es_suboferta IS NULL OR n.es_suboferta = 0)
        AND length(COALESCE(o.descripcion_utf8, o.descripcion, '')) > 80
        AND n.id_oferta NOT IN (SELECT id_oferta FROM ofertas_nlp_tareas_v124)
      ORDER BY o.{fecha} DESC
      LIMIT ?"""
    return con.execute(q, (limit,)).fetchall(), fecha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=40)
    ap.add_argument('--tanda', default='checkpoint')
    args = ap.parse_args()
    con = _conectar()
    cands, fecha_col = _candidatos(con, args.limit)
    print(f'[tanda {args.tanda}] modelo={MODEL} orden=por {fecha_col} DESC  candidatos={len(cands)}', flush=True)
    t0 = time.time()
    n_vac = n_err = 0
    dists = []
    for i, (oid, portal, desc) in enumerate(cands, 1):
        tc = time.time()
        try:
            run = correr_caso(desc, portal)
            tareas = run['v12_final']
        except Exception as e:
            n_err += 1
            print(f'  [{i}/{len(cands)}] {oid} ERR {e}', flush=True)
            continue
        dur = int((time.time() - tc) * 1000)
        if not tareas:
            n_vac += 1
        dists.append(len(tareas))
        con.execute("INSERT OR REPLACE INTO ofertas_nlp_tareas_v124 VALUES (?,?,?,?,?,?,?,?)",
                    (oid, json.dumps(tareas, ensure_ascii=False), len(tareas),
                     json.dumps(run['postfiltradas'], ensure_ascii=False), MODEL, dur,
                     args.tanda, time.strftime('%Y-%m-%dT%H:%M:%S')))
        if i % 10 == 0:
            con.commit()
            rate = i / (time.time() - t0) * 3600
            print(f'  [{i}/{len(cands)}] {rate:.0f} of/h  n_tareas_avg={sum(dists)/len(dists):.1f}', flush=True)
    con.commit()
    el = time.time() - t0
    rate = len(cands) / el * 3600 if el else 0
    print(f'\n[tanda {args.tanda}] {len(cands)} en {el/60:.1f} min = {rate:.0f} of/h')
    print(f'  vacías={n_vac} ({100*n_vac/max(len(cands),1):.1f}%) errores={n_err}')
    if dists:
        nz = [d for d in dists if d]
        print(f'  n_tareas: media_global={sum(dists)/len(dists):.2f} media_no_vacio={sum(nz)/len(nz):.2f}'
              f' max={max(dists)}')
    con.close()


if __name__ == '__main__':
    main()
