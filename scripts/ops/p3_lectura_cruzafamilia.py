# -*- coding: utf-8 -*-
"""[CASCADA — salvaguarda swap] Lectura de 20 cambios de destino CRUZA-FAMILIA del re-gate
con capa. Por caso: id | título | tareas v12.5 | destino v11 → v12.5 | la condición que disparó
(regla_id + términos que matchearon en el eval v12.5-con-capa). A Gerardo para su lectura.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'ops'))
sys.path.insert(0, str(ROOT / 'database'))
from p3_shadow_arbol import _build_traductor, _txt

SHADOW = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_shadow_equiv_2026-10-16.json'
STAGING = ROOT / 'database' / 'cascada_staging.db'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_lectura20_cruzafamilia_2026-10-16.md'


def _cond_que_disparo(r, destino):
    """Del traza del eval, la regla cuyo 'propone' == destino + sus términos matcheados."""
    for h in r.get('traza', {}).get('hubs_activados', []):
        if h.get('propone') == destino:
            for reg in h.get('reglas', []):
                if reg.get('matches'):
                    terms = sorted({m['termino'] for m in reg['matches']})
                    return h.get('hub_id'), reg.get('regla_id'), terms
            return h.get('hub_id'), h.get('regla_id'), []
    return r.get('hub_id'), r.get('regla_id'), []


def main():
    sh = json.load(open(SHADOW))
    cruza = [c for c in sh['muestra_cambios_destino'] if not c.get('misma_fam')][:20]
    tc = _build_traductor(equiv=True)
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    nlp = {}
    ids = [c['id'] for c in cruza]
    ph = ','.join('?' * len(ids))
    for row in main_con.execute(
            f"SELECT id_oferta, titulo_limpio, skills_tecnicas_list, soft_skills_list, "
            f"conocimientos_especificos_list, tecnologias_list, sistemas_list, herramientas_list "
            f"FROM ofertas_nlp WHERE id_oferta IN ({ph})", ids):
        nlp[row[0]] = dict(zip(['id', 'tl', 'sk', 'soft', 'con', 'tec', 'sis', 'her'], row))
    tareas = {r[0]: (json.loads(r[1]) if r[1] else []) for r in
              stg.execute(f"SELECT id_oferta, tareas_json FROM ofertas_nlp_tareas_v124 WHERE id_oferta IN ({ph})", ids)}

    L = ['# [CASCADA] Lectura de 20 cambios de destino CRUZA-FAMILIA (re-gate con capa) — 2026-10-16', '',
         'Salvaguarda del swap: los 377 cruza-familia (7,2%, bajo techo). Muestra de 20 para tu lectura.',
         'Por caso: destino v11 → v12.5 · tareas v12.5 · la condición (regla + términos) que disparó el destino nuevo.', '']
    for c in cruza:
        oid = c['id']
        d = nlp.get(oid, {})
        titulo = d.get('tl') or ''
        cont = {
            'tareas_explicitas': _txt(tareas.get(oid, [])),
            'skills_habilidades': f"{_txt(d.get('sk'))} {_txt(d.get('soft'))}",
            'conocimientos': _txt(d.get('con')),
            'tecnologias': _txt(d.get('tec')),
            'sistemas_herramientas': f"{_txt(d.get('sis'))} {_txt(d.get('her'))}",
        }
        r = tc.evaluar(titulo, cont)
        hub_id, regla_id, terms = _cond_que_disparo(r, c['v125'])
        L.append(f"## {oid} — «{titulo}»")
        L.append(f"- **destino: {c['v11']} → {c['v125']}**")
        L.append(f"- tareas v12.5: {json.dumps(tareas.get(oid, [])[:7], ensure_ascii=False)}")
        L.append(f"- condición que disparó: hub `{hub_id}` regla `{regla_id}` · términos: {terms}")
        L.append('')
    OUT.write_text('\n'.join(L))
    print(f'-> {OUT}  ({len(cruza)} casos)')
    for c in cruza[:6]:
        print(f"  {c['id']} {c['v11']}→{c['v125']}")


if __name__ == '__main__':
    main()
