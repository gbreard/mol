# -*- coding: utf-8 -*-
"""[CASCADA — residual mini-frente] Paquete para Cyn de las ~295 regresiones que la capa de
equivalencia NO resuelve (cambio de FONDO, no de forma: v12.5 re-frasea con otro núcleo).
Por caso: condición del hub | término que espera | cómo v12.5 lo re-frasea | la pregunta.
Corre con capa ON: si aún abstiene con 3+ tareas, el término no es nominalización↔verbo.
"""
import gzip
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'ops'))
sys.path.insert(0, str(ROOT / 'database'))
from p3_shadow_arbol import _build_traductor, _txt

STAGING = ROOT / 'database' / 'cascada_staging.db'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
SNAP = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz'
OUT = ROOT / 'exports' / 'cyn_backlog' / 'residual_arbol_v125_para_cyn_2026-10-16.md'
N = 40  # muestra representativa de las ~295 (el resto queda en el JSON crudo)


def _terms_matched(r):
    out = set()
    for h in r.get('traza', {}).get('hubs_activados', []):
        for reg in h.get('reglas', []):
            for m in reg.get('matches', []):
                out.add(m['termino'])
    return out


def main():
    tc_off = _build_traductor(equiv=False)   # baseline v11
    tc_on = _build_traductor(equiv=True)      # v12.5 con capa
    v11_tar = {}
    with gzip.open(SNAP, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            v11_tar[r['id_oferta']] = _txt(r.get('tareas_explicitas'))
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    nlp = {}
    for row in main_con.execute(
            "SELECT id_oferta, titulo_limpio, skills_tecnicas_list, soft_skills_list, "
            "conocimientos_especificos_list, tecnologias_list, sistemas_list, herramientas_list FROM ofertas_nlp"):
        nlp[row[0]] = dict(zip(['id', 'tl', 'sk', 'soft', 'con', 'tec', 'sis', 'her'], row))
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)

    def cont(oid, tareas_str):
        d = nlp.get(oid, {})
        return {'tareas_explicitas': tareas_str,
                'skills_habilidades': f"{_txt(d.get('sk'))} {_txt(d.get('soft'))}",
                'conocimientos': _txt(d.get('con')), 'tecnologias': _txt(d.get('tec')),
                'sistemas_herramientas': f"{_txt(d.get('sis'))} {_txt(d.get('her'))}"}

    casos = []
    for oid, tj, nt in stg.execute("SELECT id_oferta, tareas_json, n_tareas FROM ofertas_nlp_tareas_v124 WHERE n_tareas >= 3"):
        if oid not in nlp or oid not in v11_tar:
            continue
        titulo = nlp[oid]['tl'] or ''
        t125 = json.loads(tj)
        r11 = tc_off.evaluar(titulo, cont(oid, v11_tar[oid]))
        r125 = tc_on.evaluar(titulo, cont(oid, _txt(t125)))
        if not (r11.get('decide') and not r125.get('decide')):
            continue  # solo residual: decidía v11, aún abstiene con capa
        perdidos = sorted(_terms_matched(r11) - _terms_matched(r125))
        casos.append({'id': oid, 'titulo': titulo, 'v11_destino': r11.get('codigo_esco'),
                      'terminos_que_espera': perdidos[:5], 'tareas_v125': t125[:7]})
    # reporte (muestra N) + crudo completo
    (OUT.parent / 'residual_arbol_v125_para_cyn_2026-10-16.json').write_text(
        json.dumps(casos, ensure_ascii=False, indent=2))
    L = ['# [CASCADA] Residual del árbol v12.5 — para Cyn (cambio de FONDO, no de forma) — 2026-10-16', '',
         f'Son {len(casos)} ofertas donde el árbol decidía con tareas v11 y **sigue abstenién­dose** con las '
         'tareas v12.5 AUNQUE la capa de equivalencia funcional (nominalización↔verbo) está activa. '
         'Es decir: v12.5 NO re-frasea por forma, re-frasea por CONTENIDO (otro núcleo) — la condición '
         'del hub necesitaría un término nuevo. Eso es cambio de fondo: **requiere tu firma, no se re-escribe solo.**', '',
         'Por caso: el término que la condición espera | cómo v12.5 re-frasea la tarea | la pregunta.', '',
         '| id | título | hub decidía | término que espera la condición | tareas v12.5 (núcleo re-fraseado) |',
         '|---|---|---|---|---|']
    for c in casos[:N]:
        L.append(f"| {c['id']} | {c['titulo']} | {c['v11_destino']} | {c['terminos_que_espera']} | "
                 f"{json.dumps(c['tareas_v125'][:4], ensure_ascii=False)} |")
    L += ['', '## La pregunta para cada familia de término',
          '¿Se agrega el término nuevo (como lo dice v12.5) a la condición del hub? '
          'Ej: si la condición espera «prospectar» y v12.5 dice «desarrollar y expandir la cartera», '
          '¿«desarrollar cartera» entra como término de esa condición? '
          '(cambio de FONDO en la prosa compilada — solo con tu firma).']
    OUT.write_text('\n'.join(L))
    print(f'-> {OUT}  ({len(casos)} casos; muestra {min(N,len(casos))} en la tabla)')
    for c in casos[:8]:
        print(f"  {c['id']} {c['v11_destino']} espera={c['terminos_que_espera']}")


if __name__ == '__main__':
    main()
