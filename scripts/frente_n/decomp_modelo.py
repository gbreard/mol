# -*- coding: utf-8 -*-
"""[FRENTE N] Descomposición prompt-solo (v12+7b) vs prompt+modelo (v12+14b) sobre
la MISMA submuestra del gate 2, con of/h medida de cada modelo. Atribución del
hallazgo 14b antes de decidir el bundle."""
import json, os, sys, time, sqlite3, random
from pathlib import Path
from statistics import median
random.seed(11)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from limpiar_chrome import limpiar_chrome, parece_solo_titulo
from prompt_tareas_v12 import build_prompt_v12
from postfiltro_tareas import postfiltrar, _REQ_RE, _BENEF_RE
import requests
URL = f"http://{os.environ.get('OLLAMA_HOST','172.17.0.1')}:11434/api/generate"


def run(model, cuerpo, portal):
    limpio = limpiar_chrome(cuerpo, portal)
    if not limpio or parece_solo_titulo(limpio):
        return [], 0.0
    t0 = time.time()
    try:
        r = requests.post(URL, json={'model': model, 'prompt': build_prompt_v12(limpio),
                          'stream': False, 'format': 'json',
                          'options': {'temperature': 0.0, 'top_p': 0.1, 'num_predict': 1024, 'num_ctx': 8192}},
                          timeout=200)
        crudas = [str(t).strip() for t in json.loads(r.json().get('response', '{}')).get('tareas', []) if str(t).strip()]
    except Exception:
        crudas = []
    dt = time.time() - t0
    ok, _ = postfiltrar(crudas)
    return ok, dt


def req_rate(listas):
    c = tot = 0
    for L in listas:
        for it in L:
            tot += 1
            if _REQ_RE.match(it) or _BENEF_RE.match(it):
                c += 1
    return c, tot


def main():
    g2 = json.loads((ROOT / 'exports/reportes/N_gate2_raw.json').read_text())['resultados']
    muestra = [r for r in g2 if not r['anti']]
    sub = random.sample(muestra, 70)
    con = sqlite3.connect(f"file:{ROOT/'database/bumeran_scraping.db'}?mode=ro", uri=True)
    ids = [int(r['id']) for r in sub]
    ph = ','.join('?' * len(ids))
    cuerpos = {str(r[0]): (r[1], r[2]) for r in con.execute(
        f"SELECT id_oferta, COALESCE(descripcion_utf8,descripcion), portal FROM ofertas WHERE id_oferta IN ({ph})", ids)}
    out = {'7b': {'n': [], 'dt': [], 'listas': []}, '14b': {'n': [], 'dt': [], 'listas': []}}
    modelos = {'7b': 'qwen2.5:7b', '14b': 'qwen2.5:14b'}
    for k, model in modelos.items():
        t0 = time.time()
        for r in sub:
            cuerpo, portal = cuerpos.get(r['id'], (None, r['portal']))
            tareas, dt = run(model, cuerpo, portal)
            out[k]['n'].append(len(tareas)); out[k]['dt'].append(dt); out[k]['listas'].append(tareas)
        wall = time.time() - t0
        ns = out[k]['n']; dts = [d for d in out[k]['dt'] if d > 0]
        rq, tot = req_rate(out[k]['listas'])
        ofh = 3600 / (sum(dts)/len(dts)) if dts else 0
        print(f"\n=== v12 + {model} (n=70) ===")
        print(f"  n_tareas media={sum(ns)/len(ns):.2f} mediana={median(ns)}  %vacías={100*sum(1 for x in ns if x==0)/len(ns):.0f}%")
        print(f"  requisito-como-tarea: {rq}/{tot} ({100*rq/max(tot,1):.1f}%)")
        print(f"  latencia media={sum(dts)/len(dts):.1f}s  → of/h efectiva ≈ {ofh:.0f}  (wall {wall:.0f}s los 70)")
        out[k]['ofh'] = round(ofh); out[k]['lat_media'] = round(sum(dts)/len(dts), 1)
    # comparación directa
    dif = sum(1 for a, b in zip(out['7b']['n'], out['14b']['n']) if a != b)
    print(f"\n=== 7b vs 14b (misma muestra, mismo prompt v12) ===")
    print(f"  ofertas con distinto n_tareas: {dif}/70")
    print(f"  n_tareas total: 7b={sum(out['7b']['n'])}  14b={sum(out['14b']['n'])}")
    (ROOT / 'exports/reportes/N_decomp_modelo.json').write_text(json.dumps(
        {k: {kk: v[kk] for kk in ('n', 'dt', 'ofh', 'lat_media')} for k, v in out.items()}, ensure_ascii=False))
    print("\n-> exports/reportes/N_decomp_modelo.json")


if __name__ == '__main__':
    main()
