# -*- coding: utf-8 -*-
"""
[FRENTE N — N4] Gate runner: corre el pipeline nuevo (N1→v12→N3) y arma la tabla
de scoring caso por caso. El gate se aprueba MIRANDO LA TABLA (equivalencia
funcional), no el porcentaje (anexo de laudos, gate 1).

Uso:
  python scripts/frente_n/gate_runner.py --gate1              # los 28 de Cyn
  python scripts/frente_n/gate_runner.py --ids 123,456        # ad-hoc
  python scripts/frente_n/gate_runner.py --sample N --out X    # muestra de BD (gate 2)
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from limpiar_chrome import limpiar_chrome, parece_solo_titulo  # noqa: E402
from prompt_tareas_v12 import build_prompt_v12       # noqa: E402
from postfiltro_tareas import postfiltrar            # noqa: E402

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', '172.17.0.1')
OLLAMA_URL = f'http://{OLLAMA_HOST}:11434/api/generate'
# Modelo configurable: el gate mostró que 14b mejora la granularidad; 7b es el de
# producción. Default 14b (candidato de re-extracción). Override: MODEL_TAREAS env.
MODEL = os.environ.get('MODEL_TAREAS', 'qwen2.5:14b')
GOLD = ROOT / 'metrics/gold_set_tareas.json'

# ── stopwords para el matcher de equivalencia funcional ──
_STOP = set('de la el los las un una unos unas y o u en con para por a al del que se su sus '
            'como sobre entre segun según e cada toda todo todos las del lo le les nuestro '
            'nuestra mismo misma manera forma activa activo'.split())


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9\s]', ' ', s)


def _stem(w):
    """Stemmer ligero: acerca formas verbales/nominales (cargar/carga, gestión/gestionar)."""
    for suf in ('andose', 'iendose', 'ando', 'iendo', 'aciones', 'acion', 'aion',
                'mientos', 'miento', 'ciones', 'cion', 'ando', 'ar', 'er', 'ir',
                'aje', 'os', 'as', 'es', 'a', 'o', 's'):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    return w


def _toks(s):
    return {_stem(w) for w in _norm(s).split() if w not in _STOP and len(w) > 2}


def _raiz_verbo(w):
    """Raíz aproximada de un verbo/nominalización (para 'verbo-núcleo')."""
    for suf in ('ando', 'iendo', 'ar', 'er', 'ir', 'acion', 'ación', 'miento', 'aje'):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w[:5]


def match_funcional(gold_t, extraidas):
    """Devuelve (idx_mejor, score, veredicto) del mejor match de gold_t en extraidas.
    Equivalencia funcional aproximada: solape de tokens de contenido + raíz verbal.
    veredicto: recuperada / parcial / ausente. La ADJUDICACIÓN final es humana.
    """
    gt = _toks(gold_t)
    if not gt:
        return (-1, 0.0, 'ausente')
    mejor = (-1, 0.0)
    for i, e in enumerate(extraidas):
        et = _toks(e)
        if not et:
            continue
        inter = gt & et
        jac = len(inter) / len(gt | et)
        # bonus si comparten raíz verbal de la primera palabra de contenido
        recall = len(inter) / len(gt)
        score = 0.6 * recall + 0.4 * jac
        if score > mejor[1]:
            mejor = (i, score)
    idx, score = mejor
    if score >= 0.55:
        ver = 'recuperada'
    elif score >= 0.30:
        ver = 'parcial'
    else:
        ver = 'ausente'
    return (idx, round(score, 2), ver)


def llamar_v12(cuerpo_limpio, timeout=120):
    payload = {
        'model': MODEL,
        'prompt': build_prompt_v12(cuerpo_limpio),
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.0, 'top_p': 0.1, 'num_predict': 1024, 'num_ctx': 8192},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    txt = r.json().get('response', '')
    try:
        data = json.loads(txt)
        tareas = data.get('tareas', [])
        if isinstance(tareas, str):
            tareas = [t.strip() for t in re.split(r'[;\n]', tareas) if t.strip()]
        return [str(t).strip() for t in tareas if str(t).strip()], txt
    except Exception:
        return [], txt


def correr_caso(cuerpo, portal):
    limpio = limpiar_chrome(cuerpo, portal)
    if not limpio or parece_solo_titulo(limpio):
        # título-only o sin cuerpo → [] sin LLM (guard anti-alucinación)
        return {'cuerpo_limpio': limpio, 'v12_crudas': [], 'v12_final': [],
                'postfiltradas': [], 'raw': '{"tareas": []} [guard:solo_titulo]'}
    crudas, raw = llamar_v12(limpio)
    log = []
    ok, descartadas = postfiltrar(crudas, log)
    return {'cuerpo_limpio': limpio, 'v12_crudas': crudas, 'v12_final': ok,
            'postfiltradas': descartadas, 'raw': raw}


def _cuerpos_full_db(ids):
    """Descripción COMPLETA desde BD (el 'cuerpo' del Excel está truncado ~1100 ch)."""
    import sqlite3
    db = ROOT / 'database' / 'bumeran_scraping.db'
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    ints = [int(x) for x in ids]
    ph = ','.join('?' * len(ints))
    m = {}
    for r in con.execute(f"SELECT id_oferta, COALESCE(descripcion_utf8, descripcion) "
                         f"FROM ofertas WHERE id_oferta IN ({ph})", ints):
        m[str(r[0])] = r[1]
    con.close()
    return m


def scorear_gate1():
    doc = json.loads(GOLD.read_text())
    full = _cuerpos_full_db([c['id_oferta'] for c in doc['casos']])
    resultados = []
    for c in doc['casos']:
        print(f'[{c["n"]:>2}] id={c["id_oferta"]} {c["portal"]:12} ...', flush=True, end='')
        t0 = time.time()
        cuerpo = full.get(c['id_oferta']) or c['cuerpo']  # full DB body; fallback Excel
        run = correr_caso(cuerpo, c['portal'])
        extr = run['v12_final']
        gold = c['gold_tareas']
        # match gold → extraída
        filas = []
        usados = set()
        for gt in gold:
            idx, score, ver = match_funcional(gt, extr)
            match_txt = extr[idx] if idx >= 0 and ver != 'ausente' else ''
            if idx >= 0 and ver != 'ausente':
                usados.add(idx)
            filas.append({'gold': gt, 'match_v12': match_txt, 'score': score, 'veredicto': ver})
        # extras: v12 que no matchearon ningún gold → compatible/invención (revisión humana)
        extras = [e for i, e in enumerate(extr) if i not in usados]
        # sobras tipificadas: SOLO cuentan si aparecen como item AUTÓNOMO (en extras);
        # si la sobra está DENTRO de una tarea que matcheó un gold (ej. "seguridad y
        # usabilidad" dentro de la responsabilidad correcta), NO es sobra.
        sobras_hit = []
        for s in c['sobras_tipificadas']:
            for e in extras:
                if _toks(s) and len(_toks(s) & _toks(e)) / max(len(_toks(s)), 1) >= 0.6:
                    sobras_hit.append({'sobra_cyn': s, 'extraida': e})
        cubiertas = sum(1 for f in filas if f['veredicto'] == 'recuperada')
        parciales = sum(1 for f in filas if f['veredicto'] == 'parcial')
        cobertura = cubiertas / len(gold) if gold else (1.0 if not extr else 0.0)
        precision = cubiertas / len(extr) if extr else (1.0 if not gold else 0.0)
        resultados.append({
            **{k: c[k] for k in ('n', 'id_oferta', 'portal', 'titulo', 'veredicto_cyn')},
            'gold_n': len(gold), 'v12_n': len(extr),
            'v12_final': extr, 'postfiltradas': run['postfiltradas'],
            'filas': filas, 'extras_para_revision': extras, 'sobras_tipificadas_hit': sobras_hit,
            'cubiertas': cubiertas, 'parciales': parciales,
            'cobertura': round(cobertura, 3), 'precision': round(precision, 3),
        })
        print(f' {time.time()-t0:.0f}s  cob={cobertura:.0%} extr={len(extr)} extras={len(extras)} sobras={len(sobras_hit)}', flush=True)
    return {'gold_version': doc['version'], 'resultados': resultados}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gate1', action='store_true')
    ap.add_argument('--out', default=str(ROOT / 'exports/reportes/N_gate1_raw.json'))
    args = ap.parse_args()
    if args.gate1:
        res = scorear_gate1()
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2))
        print(f'\n-> {args.out}')


if __name__ == '__main__':
    main()
