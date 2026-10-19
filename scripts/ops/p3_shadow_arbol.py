# -*- coding: utf-8 -*-
"""[CASCADA — P3] Shadow del árbol: el evaluador del traductor con tareas v11 vs v12.5.

Corre TraductorContexto.evaluar() sobre cada oferta del staging dos veces (mismo título
y mismos otros campos; SOLO cambia tareas: v11 del snapshot vs v12.5 del staging neteado).
Aísla el efecto de las tareas sobre la decisión del árbol (Eje 4). NO cambia decisiones.

Dos poblaciones:
  (i)  decidía-v11  → estabilidad (¿mismo código con v12.5?)
  (ii) abstenía-v11 y decide-v12.5  → territorio nuevo (SOBRE-muestreado para lectura)
Vara dual: no-explicadas (cambió destino entre v11 y v12.5) <15%; costo (decidía-v11 y
ahora abstiene/cambia) techo 10% declarado; mejoras (nueva cobertura) a la vista.

Read-only. Emite exports/reportes/CASCADA_P3_shadow_<fecha>.json.
"""
import gzip
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'database'))
STAGING = ROOT / 'database' / 'cascada_staging.db'
MAIN = ROOT / 'database' / 'bumeran_scraping.db'
SNAP = ROOT / 'exports' / 'cohorts' / 'snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz'
OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_shadow_2026-10-16.json'


def _build_traductor(equiv=False):
    from traductor_contexto import TraductorContexto
    base = ROOT / 'config'
    excl = json.load(open(base / 'traductor_exclusiones_trigger.json'))['exclusiones']
    piso = json.load(open(base / 'traductor_piso_satelites.json'))['triggers']
    sats = {}
    for t in piso:
        sats.setdefault(t['trigger'], t['satelite'])
    tc = TraductorContexto(exclusiones_trigger=excl, satelites=sats, equivalencia_funcional=equiv)
    ya = {t for t, _ in tc._triggers}
    tc._triggers += [(t['trigger'], t['hub']) for t in piso if t['trigger'] not in ya]
    return tc


def _txt(v):
    if isinstance(v, list):
        return ' '.join(str(x) for x in v)
    return str(v or '')


def main():
    import os
    EQUIV = os.environ.get('EQUIV_V125') == '1'   # capa de equivalencia en el eval v12.5
    tc = _build_traductor(equiv=False)             # baseline v11 = producción (capa OFF)
    tc_v125 = _build_traductor(equiv=EQUIV)         # candidato v12.5 (capa ON si EQUIV)
    if EQUIV:
        global OUT
        OUT = ROOT / 'exports' / 'reportes' / 'CASCADA_P3_shadow_equiv_2026-10-16.json'
        print('[gate mini-frente] capa de equivalencia funcional ON para v12.5')
    # v11 tareas del snapshot
    v11_tar = {}
    with gzip.open(SNAP, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            v11_tar[r['id_oferta']] = _txt(r.get('tareas_explicitas'))
    # otros campos (NLP v11, congelados) + titulo
    main_con = sqlite3.connect(f'file:{MAIN}?mode=ro', uri=True)
    nlp = {}
    for row in main_con.execute(
            "SELECT id_oferta, titulo_limpio, skills_tecnicas_list, soft_skills_list, "
            "conocimientos_especificos_list, tecnologias_list, sistemas_list, herramientas_list "
            "FROM ofertas_nlp"):
        d = dict(zip(['id', 'tl', 'sk', 'soft', 'con', 'tec', 'sis', 'her'], row))
        nlp[d['id']] = d
    # v12.5 del staging
    stg = sqlite3.connect(f'file:{STAGING}?mode=ro', uri=True)
    stg_rows = stg.execute("SELECT id_oferta, tareas_json, primera_extraccion FROM ofertas_nlp_tareas_v124").fetchall()

    def _contenidos(oid, tareas_str):
        d = nlp.get(oid, {})
        return {
            'tareas_explicitas': tareas_str,
            'skills_habilidades': f"{_txt(d.get('sk'))} {_txt(d.get('soft'))}",
            'conocimientos': _txt(d.get('con')),
            'tecnologias': _txt(d.get('tec')),
            'sistemas_herramientas': f"{_txt(d.get('sis'))} {_txt(d.get('her'))}",
        }

    # categorías de transición
    cnt = {'dd_igual': 0, 'dd_cambia': 0, 'd_a': 0, 'a_d': 0, 'a_a': 0}
    nuevos = []          # abstenía→decide (población ii, para lectura)
    cambios_destino = [] # decidía ambos pero destino distinto (no-explicadas)
    todos_cambios = []   # TODOS los cambios de destino (para muestreo seed)
    perdidas = []        # decidía v11 → abstiene v12.5 (costo)
    for oid, tj, prim in stg_rows:
        d = nlp.get(oid, {})
        titulo = d.get('tl') or ''
        tareas_v125 = _txt(json.loads(tj) if tj else [])
        tareas_v11 = v11_tar.get(oid, '')
        r11 = tc.evaluar(titulo, _contenidos(oid, tareas_v11))
        r125 = tc_v125.evaluar(titulo, _contenidos(oid, tareas_v125))
        d11, d125 = r11.get('decide'), r125.get('decide')
        c11, c125 = r11.get('codigo_esco'), r125.get('codigo_esco')
        if d11 and d125:
            if c11 == c125:
                cnt['dd_igual'] += 1
            else:
                cnt['dd_cambia'] += 1
                # familia ISCO-2 (primeros 2 díg. del código antes del punto)
                f11 = (c11 or '').split('.')[0][:2]
                f125 = (c125 or '').split('.')[0][:2]
                cnt.setdefault('dd_cambia_misma_fam', 0); cnt.setdefault('dd_cambia_cruza_fam', 0)
                if f11 == f125:
                    cnt['dd_cambia_misma_fam'] += 1
                else:
                    cnt['dd_cambia_cruza_fam'] += 1
                todos_cambios.append({'id': oid, 'v11': c11, 'v125': c125,
                                      'misma_fam': f11 == f125})
                if len(cambios_destino) < 60:
                    cambios_destino.append({'id': oid, 'v11': c11, 'v125': c125,
                                            'misma_fam': f11 == f125})
        elif d11 and not d125:
            cnt['d_a'] += 1
            # bucket por riqueza de tareas v12.5 (regresión-del-evaluador vs v12.5-adelgazó/legítimo)
            nt = len(json.loads(tj)) if tj else 0
            cnt.setdefault('d_a_v125_3plus', 0); cnt.setdefault('d_a_v125_1_2', 0); cnt.setdefault('d_a_v125_0', 0)
            if nt >= 3:
                cnt['d_a_v125_3plus'] += 1   # v12.5 tiene tareas ricas pero el árbol abstiene = regresión evaluador
            elif nt >= 1:
                cnt['d_a_v125_1_2'] += 1
            else:
                cnt['d_a_v125_0'] += 1
            if len(perdidas) < 40:
                perdidas.append({'id': oid, 'v11': c11, 'tele_v125': r125.get('telemetria'), 'v125_n': nt})
        elif not d11 and d125:
            cnt['a_d'] += 1
            if len(nuevos) < 120:
                nuevos.append({'id': oid, 'v125': c125, 'label': r125.get('esco_label'),
                               'primera': prim, 'tele_v11': r11.get('telemetria')})
        else:
            cnt['a_a'] += 1

    import random
    random.seed(42)  # semilla documentada (laudo: muestra aleatoria, no casos lindos)
    _intra = [c for c in todos_cambios if c['misma_fam']]
    _cruza = [c for c in todos_cambios if not c['misma_fam']]
    muestra_intra_30 = random.sample(_intra, min(30, len(_intra)))
    muestra_cruza_20 = random.sample(_cruza, min(20, len(_cruza)))

    n = len(stg_rows)
    decide_v11 = cnt['dd_igual'] + cnt['dd_cambia'] + cnt['d_a']
    decide_v125 = cnt['dd_igual'] + cnt['dd_cambia'] + cnt['a_d']
    # vara dual
    estables = cnt['dd_igual']
    no_expl = cnt['dd_cambia']          # cambió destino: a explicar
    costo = cnt['d_a']                   # decidía y ahora abstiene: costo
    mejora = cnt['a_d']                  # nueva cobertura
    base_dd = cnt['dd_igual'] + cnt['dd_cambia']
    doc = {
        'fecha': '2026-10-16', 'n_total': n,
        'decide_v11': decide_v11, 'decide_v125': decide_v125,
        'transiciones': cnt,
        'vara_dual': {
            'estabilidad_dd_igual': estables,
            'no_explicadas_cambio_destino': no_expl,
            'pct_no_explicadas_sobre_decididos_ambos': round(100 * no_expl / base_dd, 1) if base_dd else 0,
            'costo_decidia_ahora_abstiene': costo,
            'pct_costo_sobre_decide_v11': round(100 * costo / decide_v11, 1) if decide_v11 else 0,
            'mejora_nueva_cobertura': mejora,
        },
        'muestra_nuevos': nuevos,
        'muestra_cambios_destino': cambios_destino,
        'muestra_intra_30_seed42': muestra_intra_30,
        'muestra_cruza_20_seed42': muestra_cruza_20,
        'muestra_perdidas': perdidas,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f'-> {OUT}')
    print(f'n={n}  decide v11={decide_v11}  decide v12.5={decide_v125}')
    print(f'transiciones: {cnt}')
    vd = doc['vara_dual']
    print(f'VARA DUAL:')
    print(f'  no-explicadas (cambio destino): {no_expl} = {vd["pct_no_explicadas_sobre_decididos_ambos"]}% de decididos-ambos (techo 15%)')
    print(f'  costo (decidía→abstiene): {costo} = {vd["pct_costo_sobre_decide_v11"]}% de decide-v11 (techo 10%)')
    print(f'  mejora (nueva cobertura, abstenía→decide): {mejora}')


if __name__ == '__main__':
    main()
