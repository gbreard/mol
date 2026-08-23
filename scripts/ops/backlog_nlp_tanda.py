#!/usr/bin/env python3
"""
backlog_nlp_tanda.py — UNA tanda del backlog historico de NLP.

Se ejecuta SIEMPRE dentro de scripts/ops/run_con_tmpfs.sh: asume que
database/bumeran_scraping.db es el symlink a /dev/shm (por eso las queries de
seleccion, que sobre 9p tardan minutos, aca tardan segundos).

Hace: cuenta el remanente -> selecciona las N mas recientes sin NLP (excluye
validadas, misma guarda que get_ids_without_nlp) -> llama al entry point
canonico run_validated_pipeline.py --ids (NLP + gate + multi-position +
matching v3.6.0 + validacion) -> vuelve a contar -> escribe el checkpoint.

El checkpoint es la BD misma: una oferta con NLP deja de aparecer en la
seleccion. El JSONL solo registra el progreso para el reporte.

Uso: python3 scripts/ops/backlog_nlp_tanda.py --size 3000 --tanda 1 --rundir <dir>
"""
import argparse
import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "database" / "bumeran_scraping.db"

# Misma guarda que run_validated_pipeline.get_ids_without_nlp: nunca tocar
# ofertas validadas. Orden: mas recientes primero (encargo de la operacion).
#
# El CAST no es cosmetico: ofertas.id_oferta es INTEGER pero ofertas_nlp y
# ofertas_esco_matching lo tienen como TEXT. Sin el CAST la comparacion cruza
# afinidades, ningun indice sirve para seek y el LEFT JOIN degenera en un
# nested loop de 111K x 83K (~9.200 millones de comparaciones): medido, >15 min
# sin terminar. Con el CAST son index seeks: la misma seleccion tarda 0,1 s y
# devuelve exactamente el mismo conjunto (26.647 verificado contra el join).
# El filtro de descripcion NO es un criterio propio: replica exactamente el que
# aplica el extractor (process_nlp_from_db_v11.py:622 —
# `descripcion IS NOT NULL AND LENGTH(descripcion) > 100`). Sin el, cada tanda
# gasta cupo seleccionando ofertas que el pipeline descarta en silencio y que
# nunca salen del backlog: al 2026-08-20 son 14.940 de 23.672 (63%), casi todas
# de computrabajo (walls de Cloudflare sin descripcion). Con el filtro la
# corrida termina; sin el, las ultimas tandas seleccionarian siempre las mismas
# inertes y no procesarian nada.
SQL_BACKLOG = """
    SELECT o.id_oferta
    FROM ofertas o
    WHERE NOT EXISTS (
            SELECT 1 FROM ofertas_nlp n
            WHERE n.id_oferta = CAST(o.id_oferta AS TEXT))
      AND CAST(o.id_oferta AS TEXT) NOT IN (
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE estado_validacion = 'validado')
      AND o.descripcion IS NOT NULL
      AND LENGTH(o.descripcion) > 100
    ORDER BY COALESCE(o.fecha_publicacion_iso, o.scrapeado_en) DESC
"""

# Cierre de la tanda: cuantas de las seleccionadas quedaron con NLP. Los ids
# van entre comillas porque en ofertas_nlp la columna es TEXT (ver SQL_BACKLOG).
SQL_YA_TIENEN_NLP = """
    SELECT COUNT(*) FROM ofertas_nlp WHERE id_oferta IN (%s)
"""


def conectar(readonly=True):
    uri = f"file:{DB}?mode=ro" if readonly else str(DB)
    return sqlite3.connect(uri, uri=readonly, timeout=300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--tanda", type=int, required=True)
    ap.add_argument("--rundir", required=True)
    args = ap.parse_args()

    rundir = Path(args.rundir)
    rundir.mkdir(parents=True, exist_ok=True)
    ckpt = rundir / "checkpoint.jsonl"
    t0 = time.time()

    if not DB.is_symlink():
        print("[tanda] ABORT: la BD no es symlink — esta tanda debe correr "
              "dentro de run_con_tmpfs.sh", file=sys.stderr)
        return 2

    con = conectar()
    t_sel = time.time()
    backlog = [str(r[0]) for r in con.execute(SQL_BACKLOG)]   # unica pasada cara
    antes = len(backlog)
    ids = backlog[:args.size]
    print(f"[tanda {args.tanda}] seleccion: {time.time() - t_sel:.0f}s", flush=True)
    # Rango de fechas de la tanda: sirve para verificar el orden por frescura.
    rango = con.execute(
        "SELECT MIN(f), MAX(f) FROM (SELECT COALESCE(fecha_publicacion_iso, scrapeado_en) f "
        "FROM ofertas WHERE id_oferta IN (%s))" % ",".join(ids or ["NULL"])
    ).fetchone() if ids else (None, None)
    con.close()

    print(f"[tanda {args.tanda}] remanente={antes} seleccionadas={len(ids)} "
          f"fechas={rango[1]} .. {rango[0]}", flush=True)

    if not ids:
        print("[tanda] backlog vacio — nada que procesar", flush=True)
        (rundir / "BACKLOG_VACIO").write_text(datetime.now().isoformat())
        return 0

    log_tanda = rundir / f"tanda_{args.tanda:02d}.log"
    cmd = [sys.executable, "scripts/run_validated_pipeline.py", "--ids", ",".join(ids)]
    print(f"[tanda {args.tanda}] -> {' '.join(cmd[:3])} (--ids x{len(ids)})", flush=True)

    with open(log_tanda, "w") as fh:
        rc = subprocess.run(cmd, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT).returncode

    # Cierre barato: cuantas de las seleccionadas quedaron con NLP (lookup por PK).
    con = conectar()
    procesadas = con.execute(
        SQL_YA_TIENEN_NLP % ",".join(f"'{i}'" for i in ids)).fetchone()[0]
    con.close()
    despues = antes - procesadas
    dur = time.time() - t0
    registro = {
        "tanda": args.tanda,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "rc_pipeline": rc,
        "seleccionadas": len(ids),
        "procesadas": procesadas,
        "remanente_antes": antes,
        "remanente_despues": despues,
        "fecha_mas_nueva": rango[1],
        "fecha_mas_vieja": rango[0],
        "duracion_seg": round(dur),
        "ofertas_por_hora": round(procesadas / dur * 3600, 1) if dur > 0 else None,
        "log": str(log_tanda),
    }
    with open(ckpt, "a") as fh:
        fh.write(json.dumps(registro, ensure_ascii=False) + "\n")

    print(f"[tanda {args.tanda}] rc={rc} procesadas={procesadas}/{len(ids)} "
          f"remanente={despues} en {dur/60:.0f} min "
          f"({registro['ofertas_por_hora']}/h)", flush=True)

    # rc del pipeline != 0 puede ser solo "hay patrones para Claude"; lo que
    # decide si la tanda sirvio es cuantas salieron del backlog.
    return 0 if procesadas > 0 else (rc or 1)


if __name__ == "__main__":
    sys.exit(main())
