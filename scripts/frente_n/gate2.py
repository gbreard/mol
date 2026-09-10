# -*- coding: utf-8 -*-
"""
[FRENTE N — N4] Gate 2: muestra fresca de 200 (estratificada por portal, CT
sobre-muestreado) + población anti-alucinación (genuinamente-sin-tareas). v11 (de
BD) vs v12 (14b, fresh). Vara del anexo: mejora medible en la población ciega,
y CERO tareas en la población sin-tareas (requisito DURO).
"""
import argparse
import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path

random.seed(42)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from limpiar_chrome import limpiar_chrome, parece_solo_titulo  # noqa: E402
from postfiltro_tareas import postfiltrar        # noqa: E402
from prompt_tareas_v12 import build_prompt_v12    # noqa: E402
import requests                                   # noqa: E402

DB = ROOT / 'database/bumeran_scraping.db'
MODEL = os.environ.get('MODEL_TAREAS', 'qwen2.5:14b')
URL = f"http://{os.environ.get('OLLAMA_HOST','172.17.0.1')}:11434/api/generate"
CUOTAS = {'computrabajo': 70, 'bumeran': 40, 'zonajobs': 40, 'indeed': 30, 'portalempleo': 15, 'caba': 5}


def n_tareas_v11(t):
    return 0 if not t or not t.strip() else len([x for x in t.split(';') if x.strip()])


def run_v12(cuerpo, portal):
    limpio = limpiar_chrome(cuerpo, portal)
    if not limpio or parece_solo_titulo(limpio):
        return [], len(limpio)   # guard anti-alucinación título-only
    payload = {'model': MODEL, 'prompt': build_prompt_v12(limpio), 'stream': False,
               'format': 'json', 'options': {'temperature': 0.0, 'top_p': 0.1,
                                             'num_predict': 1024, 'num_ctx': 8192}}
    try:
        r = requests.post(URL, json=payload, timeout=180)
        tareas = json.loads(r.json().get('response', '{}')).get('tareas', [])
        crudas = [str(t).strip() for t in tareas if str(t).strip()]
    except Exception:
        crudas = []
    ok, desc = postfiltrar(crudas)
    return ok, len(limpio)


def muestrear(con):
    ids = []
    for portal, cuota in CUOTAS.items():
        rows = con.execute(
            "SELECT o.id_oferta, COALESCE(o.descripcion_utf8,o.descripcion), n.tareas_explicitas "
            "FROM ofertas o JOIN ofertas_nlp n ON CAST(o.id_oferta AS TEXT)=n.id_oferta "
            "WHERE o.portal=? AND LENGTH(COALESCE(o.descripcion_utf8,o.descripcion))>200 LIMIT 4000",
            (portal,)).fetchall()
        random.shuffle(rows)
        for oid, desc, tar in rows[:cuota]:
            ids.append({'id': str(oid), 'portal': portal, 'cuerpo': desc, 'v11': tar})
    # población anti-alucinación: cuerpos cortos (genuinamente sin tareas / boilerplate)
    anti = con.execute(
        "SELECT o.id_oferta, COALESCE(o.descripcion_utf8,o.descripcion), n.tareas_explicitas, o.portal "
        "FROM ofertas o JOIN ofertas_nlp n ON CAST(o.id_oferta AS TEXT)=n.id_oferta "
        "WHERE LENGTH(COALESCE(o.descripcion_utf8,o.descripcion)) BETWEEN 40 AND 160 LIMIT 2000").fetchall()
    random.shuffle(anti)
    anti_pop = [{'id': str(r[0]), 'portal': r[3], 'cuerpo': r[1], 'v11': r[2], 'anti': True}
                for r in anti[:30]]
    return ids, anti_pop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'exports/reportes/N_gate2_raw.json'))
    args = ap.parse_args()
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    muestra, anti = muestrear(con)
    print(f'muestra={len(muestra)}  anti-alucinacion={len(anti)}  modelo={MODEL}', flush=True)
    res = []
    t0 = time.time()
    for i, r in enumerate(muestra + anti):
        v12, limpio_len = run_v12(r['cuerpo'], r['portal'])
        res.append({'id': r['id'], 'portal': r['portal'], 'anti': r.get('anti', False),
                    'cuerpo_len': len(r['cuerpo'] or ''), 'limpio_len': limpio_len,
                    'n_v11': n_tareas_v11(r['v11']), 'n_v12': len(v12),
                    'v11': r['v11'], 'v12': v12})
        if i % 20 == 0:
            print(f'  {i}/{len(muestra)+len(anti)}  ({time.time()-t0:.0f}s)', flush=True)
    Path(args.out).write_text(json.dumps({'model': MODEL, 'n': len(res), 'resultados': res},
                                         ensure_ascii=False, indent=2))
    print(f'-> {args.out}  ({time.time()-t0:.0f}s)')


if __name__ == '__main__':
    main()
