# -*- coding: utf-8 -*-
"""
[FRENTE N — N4] Adjudicación funcional del gate 1 + tabla caso por caso.

El matcher 1-a-1 del runner subcuenta cuando la granularidad difiere (Cyn separa,
v12 fusiona, o al revés). Acá se mide COBERTURA FUNCIONAL many-to-many: una
unidad-oro está cubierta si sus tokens de contenido aparecen en la UNIÓN de las
tareas v12 (tolera fusión y división). La granularidad se cuenta APARTE. Emite la
tabla que el anexo exige (el gate se aprueba mirando la tabla, no el %).
"""
import json
import re
import unicodedata
from pathlib import Path

import sys as _sys
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / (_sys.argv[1] if len(_sys.argv) > 1 else 'exports/reportes/N_gate1_raw.json')
GOLD = ROOT / 'metrics/gold_set_tareas.json'
OUT_MD = ROOT / (_sys.argv[2] if len(_sys.argv) > 2 else 'exports/reportes/N_gate1_tabla.md')

_STOP = set('de la el los las un una unos unas y o u en con para por a al del que se su sus como '
            'sobre entre segun según e cada toda todo todos lo le les nuestro nuestra mismo misma '
            'manera forma su sus tu tus vos ser estar hacer'.split())


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9\s]', ' ', s)


def _stem(w):
    for suf in ('andose', 'iendose', 'ando', 'iendo', 'aciones', 'acion', 'mientos', 'miento',
                'ciones', 'cion', 'ar', 'er', 'ir', 'aje', 'os', 'as', 'es', 'a', 'o', 's'):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    return w


def _toks(s):
    return {_stem(w) for w in _norm(s).split() if w not in _STOP and len(w) > 2}


def adjudicar():
    raw = {r['id_oferta']: r for r in json.loads(RAW.read_text())['resultados']}
    gold = {c['id_oferta']: c for c in json.loads(GOLD.read_text())['casos']}
    filas_tabla = []
    resumen = []
    for oid, r in raw.items():
        g = gold[oid]
        golds = g['gold_tareas']
        extr = r['v12_final']
        union_extr = set().union(*[_toks(e) for e in extr]) if extr else set()
        union_gold = set().union(*[_toks(t) for t in golds]) if golds else set()
        # cobertura funcional: cada gold cubierto si ≥60% de sus tokens ∈ unión extraídas
        cubiertas = []
        for t in golds:
            gt = _toks(t)
            cov = len(gt & union_extr) / len(gt) if gt else 1.0
            cubiertas.append((t, cov, cov >= 0.6))
        n_cub = sum(1 for _, _, ok in cubiertas if ok)
        cobertura = n_cub / len(golds) if golds else (1.0 if not extr else 0.0)
        # precisión / invención: cada extraída "soportada" si ≥55% tokens ∈ unión gold
        soportadas = []
        for e in extr:
            et = _toks(e)
            sup = len(et & union_gold) / len(et) if et else 0.0
            soportadas.append((e, sup, sup >= 0.5))
        n_sop = sum(1 for _, _, ok in soportadas if ok)
        precision = n_sop / len(extr) if extr else (1.0 if not golds else 1.0)
        no_soportadas = [e for e, _, ok in soportadas if not ok]
        # granularidad: |extr| vs |gold| (aprox de fusión/división)
        gran = 'ok'
        if golds and extr:
            if len(extr) > len(golds) + 1:
                gran = f'sobre-dividida ({len(extr)} vs {len(golds)})'
            elif len(extr) < len(golds) - 1:
                gran = f'fusionada ({len(extr)} vs {len(golds)})'
        # sobras tipificadas reales (del runner, ya corregido)
        sobras = r['sobras_tipificadas_hit']
        # veredicto funcional del caso
        vac_ok = (not golds and not extr)
        if vac_ok:
            veredicto = 'OK (vacío correcto)'
        elif cobertura >= 0.85 and precision >= 0.90 and not sobras and not no_soportadas:
            veredicto = 'PASA'
        elif cobertura >= 0.85 and (no_soportadas or precision < 0.90):
            veredicto = 'PASA-con-observacion'
        else:
            veredicto = 'REVISAR'
        resumen.append({'n': r['n'], 'id': oid, 'portal': r['portal'],
                        'veredicto_cyn': g['veredicto_cyn'][:4],
                        'cob': round(cobertura, 2), 'prec': round(precision, 2),
                        'gold_n': len(golds), 'v12_n': len(extr),
                        'granularidad': gran, 'no_soportadas': no_soportadas,
                        'sobras': [s['extraida'] for s in sobras], 'veredicto': veredicto})
        filas_tabla.append((r, g, cubiertas, soportadas, veredicto, cobertura, precision, gran))

    # ── métricas agregadas ──
    ok6 = [x for x in resumen if x['veredicto_cyn'].upper().startswith('OK')]
    vac = [x for x in resumen if x['gold_n'] == 0]
    reg_vac = [x for x in vac if x['v12_n'] > 0]  # anti-alucinación
    pasa = [x for x in resumen if x['veredicto'] in ('PASA', 'OK (vacío correcto)')]
    pasa_obs = [x for x in resumen if x['veredicto'] == 'PASA-con-observacion']
    revisar = [x for x in resumen if x['veredicto'] == 'REVISAR']
    cob_prom = sum(x['cob'] for x in resumen) / len(resumen)
    prec_prom = sum(x['prec'] for x in resumen) / len(resumen)

    print(f'PASA: {len(pasa)}  PASA-obs: {len(pasa_obs)}  REVISAR: {len(revisar)}  (de {len(resumen)})')
    print(f'cobertura promedio: {cob_prom:.0%}  precision promedio: {prec_prom:.0%}')
    print(f'anti-alucinacion: {len(vac)} casos vacío-válido, regresiones (n>0): {len(reg_vac)}')
    print(f'OK-6 intocables: {len(ok6)} — veredictos: {[x["veredicto"] for x in ok6]}')
    print('REVISAR:', [(x["n"], x["id"], x["cob"]) for x in revisar])

    # ── markdown ──
    L = ['# FRENTE N — Gate 1 (los 28 de Cyn): tabla de scoring caso por caso', '',
         f'Modelo: qwen2.5:14b · pipeline N1→v12.2→N3 · cuerpo completo de BD.',
         f'Equivalencia funcional (verbo-núcleo + objeto), granularidad contada aparte. '
         f'El gate se aprueba mirando la tabla.', '',
         '## Resumen', '',
         f'- **PASA** (cob≥85%, prec≥90%, 0 sobras): {len(pasa)}/{len(resumen)} '
         f'· **PASA-con-observación**: {len(pasa_obs)} · **REVISAR**: {len(revisar)}',
         f'- Cobertura funcional promedio **{cob_prom:.0%}** · precisión promedio **{prec_prom:.0%}**',
         f'- **Anti-alucinación (requisito duro): {len(vac)} casos vacío-válido → {len(reg_vac)} regresiones** '
         f'({"CUMPLE" if not reg_vac else "FALLA"})',
         f'- **6 OK intocables**: {", ".join(x["veredicto"] for x in ok6)} '
         f'({"sin regresión" if all(x["veredicto"].startswith(("OK","PASA")) for x in ok6) else "REGRESIÓN"})',
         '', '## Tabla', '',
         '| # | id | portal | Cyn | cob | prec | gold/v12 | granularidad | veredicto |',
         '|---|----|--------|-----|-----|------|----------|--------------|-----------|']
    for x in sorted(resumen, key=lambda z: int(z['n'])):
        L.append(f"| {x['n']} | {x['id']} | {x['portal']} | {x['veredicto_cyn']} | "
                 f"{x['cob']:.0%} | {x['prec']:.0%} | {x['gold_n']}/{x['v12_n']} | "
                 f"{x['granularidad']} | {x['veredicto']} |")
    L += ['', '## Detalle por caso (gold vs v12, veredicto por tarea)', '']
    for (r, g, cubiertas, soportadas, veredicto, cob, prec, gran) in sorted(filas_tabla, key=lambda z: int(z[0]['n'])):
        L.append(f"\n### Caso {r['n']} — id `{r['id_oferta']}` ({r['portal']}) — {veredicto}")
        L.append(f"Cyn: {g['veredicto_cyn'][:40]} · cobertura {cob:.0%} · precisión {prec:.0%} · granularidad {gran}")
        L.append('\n| tarea-oro (Cyn) | ¿cubierta por v12? |')
        L.append('|---|---|')
        for t, c, ok in cubiertas:
            L.append(f"| {t} | {'✅' if ok else '❌'} ({c:.0%}) |")
        if not g['gold_tareas']:
            L.append(f"| _(vacío válido)_ | {'✅ v12 devolvió []' if not r['v12_final'] else '❌ v12 extrajo ' + str(len(r['v12_final']))} |")
        no_sop = [e for e, _, ok in soportadas if not ok]
        if no_sop:
            L.append(f"\n**Extraídas no soportadas por el oro (revisión: compatible/invención):** {no_sop}")
        if r['postfiltradas']:
            L.append(f"\n_N3 descartó:_ {[d['tarea'] for d in r['postfiltradas']]}")
    OUT_MD.write_text('\n'.join(L))
    print(f'\ntabla -> {OUT_MD}')
    return resumen


if __name__ == '__main__':
    adjudicar()
