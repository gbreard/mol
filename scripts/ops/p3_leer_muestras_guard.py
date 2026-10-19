# -*- coding: utf-8 -*-
"""[CASCADA — lectura guardada] Lee las muestras seed-42 del shadow guardado (30 intra + 20
cruza) y arma las tablas para clasificar mejora/neutral/empeora: id | título | tareas v12.5 |
destino v11 (label) → v12.5 (label) | condición que disparó. Para la lectura del sistema.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'ops'))
sys.path.insert(0, str(ROOT / 'database'))
from p3_shadow_arbol import _build_traductor, _txt

SH = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_shadow_equiv_2026-10-16.json'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
STAGING = ROOT / 'database' / 'cascada_staging.db'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_muestras_guard_2026-10-18.json'


def _cond(r, destino):
    for h in r.get('traza', {}).get('hubs_activados', []):
        if h.get('propone') == destino:
            for reg in h.get('reglas', []):
                if reg.get('matches'):
                    return h.get('hub'), reg.get('regla_id'), sorted({m['termino'] for m in reg['matches']})
            return h.get('hub'), h.get('regla_id'), []
    return None, None, []


def main():
    sh = json.load(open(SH))
    tc = _build_traductor(equiv=True)
    lab = tc._code_label
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)

    def enrich(lista):
        out = []
        for c in lista:
            oid = c['id']
            d = main_con.execute(
                "SELECT titulo_limpio,skills_tecnicas_list,soft_skills_list,conocimientos_especificos_list,"
                "tecnologias_list,sistemas_list,herramientas_list FROM ofertas_nlp WHERE id_oferta=?", (oid,)).fetchone()
            tj = stg.execute("SELECT tareas_json FROM ofertas_nlp_tareas_v124 WHERE id_oferta=?", (oid,)).fetchone()
            tareas = json.loads(tj[0]) if tj and tj[0] else []
            cont = {'tareas_explicitas': _txt(tareas),
                    'skills_habilidades': f"{_txt(d[1])} {_txt(d[2])}", 'conocimientos': _txt(d[3]),
                    'tecnologias': _txt(d[4]), 'sistemas_herramientas': f"{_txt(d[5])} {_txt(d[6])}"}
            r = tc.evaluar(d[0], cont)
            hub, regla, terms = _cond(r, c['v125'])
            out.append({'id': oid, 'titulo': d[0], 'tareas': tareas[:7],
                        'v11': c['v11'], 'v11_label': lab.get(c['v11']),
                        'v125': c['v125'], 'v125_label': lab.get(c['v125']),
                        'hub': hub, 'regla': regla, 'terminos': terms})
        return out

    doc = {'intra_30': enrich(sh.get('muestra_intra_30_seed42', [])),
           'cruza_20': enrich(sh.get('muestra_cruza_20_seed42', []))}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f'-> {OUT}  intra={len(doc["intra_30"])} cruza={len(doc["cruza_20"])}')
    print('\n=== 30 INTRA (seed42) ===')
    for x in doc['intra_30']:
        print(f"{x['id']} «{x['titulo']}» {x['v11']}({x['v11_label']}) → {x['v125']}({x['v125_label']}) | {x['regla']} {x['terminos'][:3]}")
    print('\n=== 20 CRUZA (seed42) ===')
    for x in doc['cruza_20']:
        print(f"{x['id']} «{x['titulo']}» {x['v11']}({x['v11_label']}) → {x['v125']}({x['v125_label']}) | {x['regla']} {x['terminos'][:3]}")


if __name__ == '__main__':
    main()
