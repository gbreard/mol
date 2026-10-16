# -*- coding: utf-8 -*-
"""[CASCADA — P1-total] Censo del punto de control: por capa + distribución antes/después
(staging v12.5 neteado vs snapshot v11) + muestra de 15 + verificación sub-ofertas (541).
Read-only. Emite exports/reportes/CASCADA_P1_total_censo_<fecha>.json para el reporte.
"""
import gzip
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / 'database' / 'cascada_staging.db'
SNAP_V11 = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P1_total_censo_2026-10-16.json'


def _n_v11(tareas_explicitas):
    if not tareas_explicitas or not str(tareas_explicitas).strip():
        return 0, []
    parts = [t.strip() for t in str(tareas_explicitas).split(';') if t.strip()]
    return len(parts), parts


def main():
    # ── snapshot v11: n_tareas por id + sub-ofertas ──
    v11 = {}          # id -> (n, lista)
    v11_sub = {}      # parent_id -> [ids sub]
    with gzip.open(SNAP_V11, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            n, lst = _n_v11(r.get('tareas_explicitas'))
            v11[r['id_oferta']] = (n, lst)
            if r.get('es_suboferta') == 1 and r.get('parent_id_oferta'):
                v11_sub.setdefault(str(r['parent_id_oferta']), []).append(r['id_oferta'])

    con = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    rows = con.execute("SELECT id_oferta, n_tareas, tareas_json, primera_extraccion, tanda, "
                       "multipuesto_inline_pendiente, delta2_flip FROM ofertas_nlp_tareas_v124").fetchall()

    # ── censo por capa ──
    capas = {}
    for oid, n, tj, prim, tanda, mpi, d2 in rows:
        capa = 'delta_contador' if tanda == 'delta_contador' else ('primera' if prim else 're-extraccion')
        d = capas.setdefault(capa, {'n': 0, 'vac': 0, 'sum': 0, 'sum_nz': 0, 'nz': 0})
        d['n'] += 1
        if n == 0:
            d['vac'] += 1
        else:
            d['sum_nz'] += n; d['nz'] += 1
        d['sum'] += n
    for k, d in capas.items():
        d['media_global'] = round(d['sum'] / d['n'], 2) if d['n'] else 0
        d['media_no_vacio'] = round(d['sum_nz'] / d['nz'], 2) if d['nz'] else 0
        d['pct_vacio'] = round(100 * d['vac'] / d['n'], 1) if d['n'] else 0

    # ── distribución antes/después (solo re-ext: tienen v11 comparable) ──
    pares = []
    for oid, n, tj, prim, tanda, mpi, d2 in rows:
        if prim:
            continue
        if oid in v11:
            pares.append((v11[oid][0], n))
    n_v11 = sum(a for a, _ in pares)
    n_v125 = sum(b for _, b in pares)
    subio = sum(1 for a, b in pares if b > a)
    bajo = sum(1 for a, b in pares if b < a)
    igual = sum(1 for a, b in pares if b == a)
    antes_vac = sum(1 for a, b in pares if a == 0)
    desp_vac = sum(1 for a, b in pares if b == 0)

    # ── muestra de 15 (variada por capa) ──
    muestra = []
    seen = set()
    for oid, n, tj, prim, tanda, mpi, d2 in rows:
        capa = 'delta' if tanda == 'delta_contador' else ('primera' if prim else 're-ext')
        if capa in seen and len([m for m in muestra if m['capa'] == capa]) >= 5:
            continue
        seen.add(capa)
        muestra.append({'id': oid, 'capa': capa, 'n': n,
                        'tareas': json.loads(tj)[:6] if tj else [],
                        'v11_n': v11.get(oid, (None,))[0]})
        if len(muestra) >= 15:
            break

    # ── sub-ofertas: 10 familias, ¿el padre v12.5 cubre lo que el split v11 repartía? ──
    stg_ids = {r[0] for r in rows}
    stg_tareas = {oid: (json.loads(tj) if tj else []) for oid, n, tj, *_ in rows}
    familias = [p for p in v11_sub if p in stg_ids][:10]
    sub_check = []
    import re as _re

    def toks(s):
        return set(_re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower()).split())
    for p in familias:
        v11_union = set()
        v11_union |= toks(' '.join(v11.get(p, (0, []))[1]))
        for s in v11_sub[p]:
            v11_union |= toks(' '.join(v11.get(s, (0, []))[1]))
        v125 = toks(' '.join(stg_tareas.get(p, [])))
        content = {w for w in v11_union if len(w) > 3}
        cov = len(content & v125) / len(content) if content else 1.0
        sub_check.append({'parent': p, 'n_sub': len(v11_sub[p]),
                          'v11_tokens': len(content), 'cubre_pct': round(100 * cov, 0),
                          'v125_n': len(stg_tareas.get(p, []))})

    doc = {
        'fecha': '2026-10-16',
        'staging_total': len(rows),
        'capas': capas,
        'distribucion_reext': {
            'pares_comparados': len(pares),
            'n_tareas_v11_total': n_v11, 'n_tareas_v125_total': n_v125,
            'media_v11': round(n_v11 / len(pares), 2) if pares else 0,
            'media_v125': round(n_v125 / len(pares), 2) if pares else 0,
            'subio': subio, 'bajo': bajo, 'igual': igual,
            'vacias_antes': antes_vac, 'vacias_despues': desp_vac,
        },
        'multipuesto_inline_flag': sum(1 for r in rows if r[5] == 1),
        'sub_ofertas_check': sub_check,
        'muestra_15': muestra,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f'-> {OUT}')
    print('CAPAS:')
    for k, d in capas.items():
        print(f'  {k:16} n={d["n"]:>6} vacías={d["pct_vacio"]}% media_no_vacío={d["media_no_vacio"]}')
    dd = doc['distribucion_reext']
    print(f'DISTRIB re-ext ({dd["pares_comparados"]} pares): media v11={dd["media_v11"]} → v12.5={dd["media_v125"]}  '
          f'subió={dd["subio"]} bajó={dd["bajo"]} igual={dd["igual"]}  vacías {dd["vacias_antes"]}→{dd["vacias_despues"]}')
    print(f'SUB-OFERTAS (10 familias): cobertura v12.5 de contenido v11:')
    for s in sub_check:
        print(f'  parent {s["parent"]} ({s["n_sub"]} sub): cubre {s["cubre_pct"]}% de {s["v11_tokens"]} tokens  v12.5_n={s["v125_n"]}')


if __name__ == '__main__':
    main()
