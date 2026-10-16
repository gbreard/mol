# -*- coding: utf-8 -*-
"""[CASCADA — mini-frente árbol] Diagnóstico de la regresión: qué término de condición
matcheaba con tareas v11 y v12.5 perdió. Material para diseñar la capa de equivalencia
funcional (verbo-núcleo+objeto) y para los 10 casos ejemplo.

Para una muestra de las d_a-con-3+ (regresión dura): corre evaluar(v11) y evaluar(v12.5)
con traza, extrae los términos matcheados de cada una, diff → términos perdidos. Reporta
el término de condición, la tarea v11 que lo contenía y la tarea v12.5 que debería.
"""
import gzip
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'scripts' / 'ops'))
from p3_shadow_arbol import _build_traductor, _txt  # reusa setup

_NLP = {}


def _contenidos(oid, tareas_str):
    d = _NLP.get(oid, {})
    return {
        'tareas_explicitas': tareas_str,
        'skills_habilidades': f"{_txt(d.get('sk'))} {_txt(d.get('soft'))}",
        'conocimientos': _txt(d.get('con')),
        'tecnologias': _txt(d.get('tec')),
        'sistemas_herramientas': f"{_txt(d.get('sis'))} {_txt(d.get('her'))}",
    }

STAGING = ROOT / 'database' / 'cascada_staging.db'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
SNAP = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_diag_equivalencia_2026-10-16.json'
N_TARGET = 25


def _terms_matched(r):
    out = set()
    for h in r.get('traza', {}).get('hubs_activados', []):
        for reg in h.get('reglas', []):
            for m in reg.get('matches', []):
                out.add(m['termino'])
    return out


def _tarea_con(term, tareas_list):
    t = term.lower()
    for ta in tareas_list:
        if t in ta.lower():
            return ta
    return None


def main():
    tc = _build_traductor()
    v11_tar = {}
    with gzip.open(SNAP, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            v11_tar[r['id_oferta']] = _txt(r.get('tareas_explicitas'))
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    nlp = {}
    for row in main_con.execute(
            "SELECT id_oferta, titulo_limpio, skills_tecnicas_list, soft_skills_list, "
            "conocimientos_especificos_list, tecnologias_list, sistemas_list, herramientas_list "
            "FROM ofertas_nlp"):
        d = dict(zip(['id', 'tl', 'sk', 'soft', 'con', 'tec', 'sis', 'her'], row))
        nlp[d['id']] = d
    _NLP.update(nlp)
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    rows = stg.execute("SELECT id_oferta, tareas_json FROM ofertas_nlp_tareas_v124 "
                       "WHERE n_tareas >= 3").fetchall()

    casos = []
    for oid, tj in rows:
        if oid not in nlp or oid not in v11_tar:
            continue
        titulo = nlp[oid]['tl'] or ''
        tareas_v11 = v11_tar[oid]
        tareas_v125_list = json.loads(tj)
        tareas_v125 = _txt(tareas_v125_list)
        r11 = tc.evaluar(titulo, _contenidos(oid, tareas_v11))
        r125 = tc.evaluar(titulo, _contenidos(oid, tareas_v125))
        if not (r11.get('decide') and not r125.get('decide')):
            continue
        perdidos = _terms_matched(r11) - _terms_matched(r125)
        ejemplos = []
        for term in sorted(perdidos):
            ejemplos.append({
                'termino_condicion': term,
                'tarea_v11_que_matcheaba': _tarea_con(term, tareas_v11.split(';')),
                'tareas_v125_disponibles': tareas_v125_list[:8],
            })
        casos.append({'id': oid, 'titulo': titulo, 'v11_decide': r11.get('codigo_esco'),
                      'v125_telemetria': r125.get('telemetria'),
                      'terminos_perdidos': sorted(perdidos)[:8], 'detalle': ejemplos[:4]})
        if len(casos) >= N_TARGET:
            break
    OUT.write_text(json.dumps(casos, ensure_ascii=False, indent=2))
    print(f'-> {OUT}  ({len(casos)} casos)')
    for c in casos[:12]:
        print(f"\n[{c['id']}] '{c['titulo']}' v11→{c['v11_decide']} / v12.5 {c['v125_telemetria']}")
        print(f"  términos perdidos: {c['terminos_perdidos']}")
        for e in c['detalle'][:2]:
            print(f"    cond '{e['termino_condicion']}' | v11 tarea: {str(e['tarea_v11_que_matcheaba'])[:80]}")


if __name__ == '__main__':
    main()
