# -*- coding: utf-8 -*-
"""[CASCADA — laudo 1] Netear HSE/compliance pasivo del staging completo.

Cyn laudó (hoja "1-seguridad e higiene"): "cumplir norma/procedimiento/estándar de
seguridad, higiene o ambiente" NUNCA es tarea, independiente del oficio. v12.4 las
dejaba pasar a propósito (contradicción caso-4). Ahora hay laudo → se netean sobre
las 119K ya extraídas (las 118K NO se re-corren; se corrigen por delta determinístico).

Aplica el N3 ampliado (postfiltro v12.5) sobre las tareas de cada fila del staging;
preserva el original (tareas_json_pre_laudo1) y registra lo removido (log + conteo).
Reversible. Escribe solo a cascada_staging.db (DB propia, sin contención).

Uso:  python scripts/ops/laudo1_netear_hse.py [--dry-run]
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING_DB = ROOT / 'database' / 'cascada_staging.db'
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from postfiltro_tareas import postfiltrar   # noqa: E402  (incluye _HSE_RE ampliado v12.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    con = sqlite3.connect(f'file:{STAGING_DB}', uri=True, timeout=120)
    con.execute('PRAGMA busy_timeout=120000')
    cols = [r[1] for r in con.execute("PRAGMA table_info(ofertas_nlp_tareas_v124)")]
    if not args.dry_run:
        if 'tareas_json_pre_laudo1' not in cols:
            con.execute("ALTER TABLE ofertas_nlp_tareas_v124 ADD COLUMN tareas_json_pre_laudo1 TEXT")
        if 'laudo1_removidas_json' not in cols:
            con.execute("ALTER TABLE ofertas_nlp_tareas_v124 ADD COLUMN laudo1_removidas_json TEXT")
        con.commit()

    rows = con.execute("SELECT id_oferta, tareas_json FROM ofertas_nlp_tareas_v124").fetchall()
    n_filas_tocadas = 0
    n_items_removidos = 0
    motivos = {}
    ejemplos = []
    bw = con.cursor()
    for oid, tj in rows:
        tareas = json.loads(tj) if tj else []
        if not tareas:
            continue
        ok, removidas = postfiltrar(tareas)
        # SOLO nos interesa lo que removió el laudo 1 (HSE); el resto ya estaba filtrado al extraer
        hse = [d for d in removidas if d['motivo'] == 'compliance_hse_pasivo']
        if not hse:
            continue
        # recomputar ok considerando únicamente la red HSE (no re-filtrar por otras redes
        # para no tocar nada que el laudo 1 no cubre): quitar de `tareas` solo las HSE.
        quitar = {d['tarea'] for d in hse}
        ok_final = [t for t in tareas if t not in quitar]
        n_filas_tocadas += 1
        n_items_removidos += len(hse)
        for d in hse:
            motivos[d['motivo']] = motivos.get(d['motivo'], 0) + 1
        if len(ejemplos) < 15:
            ejemplos.append({'id': oid, 'removidas': [d['tarea'] for d in hse]})
        if not args.dry_run:
            bw.execute("UPDATE ofertas_nlp_tareas_v124 SET tareas_json_pre_laudo1=?, "
                       "tareas_json=?, n_tareas=?, laudo1_removidas_json=? WHERE id_oferta=?",
                       (tj, json.dumps(ok_final, ensure_ascii=False), len(ok_final),
                        json.dumps([d['tarea'] for d in hse], ensure_ascii=False), oid))
    if not args.dry_run:
        con.commit()
    modo = 'DRY-RUN' if args.dry_run else 'APLICADO'
    print(f'[laudo 1 — {modo}] filas analizadas: {len(rows)}')
    print(f'  filas con HSE neteado: {n_filas_tocadas}')
    print(f'  ítems HSE removidos: {n_items_removidos}')
    print(f'  motivos: {motivos}')
    print(f'  ejemplos (hasta 15):')
    for e in ejemplos:
        print(f'    {e["id"]}: {e["removidas"]}')
    con.close()


if __name__ == '__main__':
    main()
