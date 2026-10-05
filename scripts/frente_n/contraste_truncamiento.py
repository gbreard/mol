# -*- coding: utf-8 -*-
"""[FRENTE N — v12.4] Contraste v12.3 vs v12.4 sobre avisos frescos.

Pregunta: ¿el endurecimiento de v12.4 (flip chofer + redes N3 + pitch acotado)
re-abrió el truncamiento del frente M, es decir, colapsó el recall? Se corre el
MISMO N1+N3 (v12.4) con ambos prompts para aislar el efecto del PROMPT; se compara
la media de n_tareas y el % de vacío. El prompt v12.3 baseline se lee de git
(rama spec/n-v123-regate). Resultado esperado: media levemente menor por precisión,
%vacío NO mayor (no se vacían avisos con tareas reales).

Uso:  OLLAMA_HOST=172.17.0.1 python scripts/frente_n/contraste_truncamiento.py --n 72
"""
import argparse
import importlib.util
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from limpiar_chrome import limpiar_chrome, parece_solo_titulo   # noqa: E402
from postfiltro_tareas import postfiltrar                       # noqa: E402
from prompt_tareas_v12 import build_prompt_v12 as build_v124    # noqa: E402

OLLAMA_URL = f"http://{__import__('os').environ.get('OLLAMA_HOST', '172.17.0.1')}:11434/api/generate"
MODEL = 'qwen2.5:14b'


def _load_v123():
    """Carga build_prompt_v12 de la rama spec/n-v123-regate (baseline)."""
    txt = subprocess.check_output(
        ['git', 'show', 'spec/n-v123-regate:scripts/frente_n/prompt_tareas_v12.py'], cwd=ROOT)
    f = tempfile.NamedTemporaryFile('wb', suffix='.py', delete=False)
    f.write(txt); f.close()
    spec = importlib.util.spec_from_file_location('p123', f.name)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.build_prompt_v12


def _llamar(prompt):
    r = requests.post(OLLAMA_URL, json={'model': MODEL, 'prompt': prompt, 'stream': False,
        'format': 'json', 'options': {'temperature': 0.0, 'top_p': 0.1,
        'num_predict': 1024, 'num_ctx': 8192}}, timeout=120)
    try:
        t = json.loads(r.json().get('response', '')).get('tareas', [])
        if isinstance(t, str):
            t = [x.strip() for x in re.split(r'[;\n]', t) if x.strip()]
        return [str(x).strip() for x in t if str(x).strip()]
    except Exception:
        return []


def _corr(desc, portal, builder):
    limpio = limpiar_chrome(desc, portal)
    if not limpio or parece_solo_titulo(limpio):
        return []
    ok, _ = postfiltrar(_llamar(builder(limpio)))
    return ok


def _sample(n):
    con = sqlite3.connect(f"file:{ROOT/'database/bumeran_scraping.db'}?mode=ro", uri=True)
    gold = {c['id_oferta'] for c in json.loads((ROOT / 'metrics/gold_set_tareas.json').read_text())['casos']}
    por = max(1, n // 6)
    out = []
    for portal in ['bumeran', 'zonajobs', 'computrabajo', 'indeed', 'portalempleo', 'caba']:
        for oid, p, d in con.execute(
                "SELECT id_oferta, portal, COALESCE(descripcion_utf8,descripcion) FROM ofertas "
                "WHERE portal=? AND length(COALESCE(descripcion_utf8,descripcion))>300 "
                "ORDER BY RANDOM() LIMIT ?", (portal, por)):
            if str(oid) not in gold:
                out.append({'id': str(oid), 'portal': p, 'desc': d})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=72)
    args = ap.parse_args()
    b123 = _load_v123()
    rows = []
    for i, s in enumerate(_sample(args.n), 1):
        n3 = len(_corr(s['desc'], s['portal'], b123))
        n4 = len(_corr(s['desc'], s['portal'], build_v124))
        rows.append({'id': s['id'], 'portal': s['portal'], 'v123': n3, 'v124': n4})
        print(f"[{i:>2}] {s['id']:12} {s['portal']:12} v123={n3:>2} v124={n4:>2}", flush=True)

    def st(k):
        ns = [r[k] for r in rows]; nz = [x for x in ns if x > 0]
        return {'media_global': round(sum(ns) / len(ns), 2),
                'media_no_vacio': round(sum(nz) / len(nz), 2) if nz else 0,
                'pct_vacio': round(100 * (len(ns) - len(nz)) / len(ns), 1)}
    print('\nv12.3:', st('v123'))
    print('v12.4:', st('v124'))
    print('Lectura: media no-vacío estable + %vacío NO mayor = sin re-apertura de truncamiento.')


if __name__ == '__main__':
    main()
