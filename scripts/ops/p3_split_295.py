# -*- coding: utf-8 -*-
"""[CASCADA — LAUDO 3] Split de las 295 residuales con la capa EXTENDIDA (sinónimos comerciales
de Cyn + núcleo funcional). Las que reconectan por equivalencia ACEPTADA → deciden; las que
dependían de una equivalencia RECHAZADA/parcial → abstención LEGÍTIMA (regla de Cyn operando,
ya no "regresión"). Reporta el split. Read-only.
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

RES = ROOT / 'exports' / 'cyn_backlog' / 'residual_arbol_v125_para_cyn_2026-10-16.json'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
STAGING = ROOT / 'database' / 'cascada_staging.db'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_split_295_2026-10-20.json'


def main():
    casos = json.loads(RES.read_text())
    ids = [c['id'] for c in casos]
    tc = _build_traductor(equiv=True)   # capa + sinónimos + núcleo + guard
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    nlp = {}
    for i in range(0, len(ids), 900):
        ch = ids[i:i + 900]; ph = ','.join('?' * len(ch))
        for row in main_con.execute(
                f"SELECT id_oferta, titulo_limpio, skills_tecnicas_list, soft_skills_list, "
                f"conocimientos_especificos_list, tecnologias_list, sistemas_list, herramientas_list "
                f"FROM ofertas_nlp WHERE id_oferta IN ({ph})", ch):
            nlp[row[0]] = dict(zip(['id', 'tl', 'sk', 'soft', 'con', 'tec', 'sis', 'her'], row))
    tareas = {}
    for i in range(0, len(ids), 900):
        ch = ids[i:i + 900]; ph = ','.join('?' * len(ch))
        for oid, tj in stg.execute(f"SELECT id_oferta, tareas_json FROM ofertas_nlp_tareas_v124 WHERE id_oferta IN ({ph})", ch):
            tareas[oid] = json.loads(tj) if tj else []

    reconecta, abstiene = [], []
    for oid in ids:
        d = nlp.get(oid)
        if not d:
            continue
        cont = {'tareas_explicitas': _txt(tareas.get(oid, [])),
                'skills_habilidades': f"{_txt(d['sk'])} {_txt(d['soft'])}", 'conocimientos': _txt(d['con']),
                'tecnologias': _txt(d['tec']), 'sistemas_herramientas': f"{_txt(d['sis'])} {_txt(d['her'])}"}
        r = tc.evaluar(d['tl'] or '', cont)
        (reconecta if r.get('decide') else abstiene).append(
            {'id': oid, 'decide': r.get('codigo_esco'), 'titulo': d['tl']})
    doc = {'total': len(ids), 'reconecta': len(reconecta), 'abstiene_legitima': len(abstiene),
           'muestra_reconecta': reconecta[:15], 'muestra_abstiene': abstiene[:15]}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f'-> {OUT}')
    print(f'295 split: RECONECTA (decide por equivalencia aceptada) = {len(reconecta)} '
          f'| ABSTENCIÓN LEGÍTIMA (dependía de rechazada/parcial) = {len(abstiene)}')
    print('ejemplos reconecta:', [(x['id'], x['decide']) for x in reconecta[:6]])


if __name__ == '__main__':
    main()
