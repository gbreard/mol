# -*- coding: utf-8 -*-
"""[FRENTE N — N4] Análisis del gate 2: v11 vs v12 (14b) sobre muestra fresca +
población anti-alucinación. Vara del anexo."""
import json
import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from postfiltro_tareas import _REQ_RE, _BENEF_RE   # noqa: E402

RAW = ROOT / 'exports/reportes/N_gate2_raw.json'


def es_requisito_como_tarea(t):
    return bool(_REQ_RE.match(t) or _BENEF_RE.match(t))


def main():
    doc = json.loads(RAW.read_text())
    res = doc['resultados']
    muestra = [r for r in res if not r['anti']]
    anti = [r for r in res if r['anti']]

    # ── población general: n_tareas v11 vs v12 ──
    v11 = [r['n_v11'] for r in muestra]
    v12 = [r['n_v12'] for r in muestra]
    print(f"MODELO v12: {doc['model']}  ·  muestra={len(muestra)}  anti-alucinación={len(anti)}")
    print("\n=== n_tareas por oferta (muestra {}): v11 vs v12 ===".format(len(muestra)))
    print(f"  media:   v11={sum(v11)/len(v11):.2f}  v12={sum(v12)/len(v12):.2f}")
    print(f"  mediana: v11={median(v11)}  v12={median(v12)}")
    print(f"  % vacías (0 tareas): v11={100*sum(1 for x in v11 if x==0)/len(v11):.0f}%  "
          f"v12={100*sum(1 for x in v12 if x==0)/len(v12):.0f}%")

    # ── población LLM-ciega: v11 ≤2 tareas sobre cuerpo rico (limpio>=400) ──
    ciega = [r for r in muestra if r['n_v11'] <= 2 and r['limpio_len'] >= 400]
    if ciega:
        cv11 = [r['n_v11'] for r in ciega]; cv12 = [r['n_v12'] for r in ciega]
        mejora = sum(1 for r in ciega if r['n_v12'] > r['n_v11'])
        print(f"\n=== POBLACIÓN LLM-CIEGA (v11≤2 sobre cuerpo rico), n={len(ciega)} ===")
        print(f"  mediana n_tareas: v11={median(cv11)} → v12={median(cv12)}")
        print(f"  media n_tareas:   v11={sum(cv11)/len(cv11):.2f} → v12={sum(cv12)/len(cv12):.2f}")
        print(f"  ofertas donde v12 sube: {mejora}/{len(ciega)} ({100*mejora/len(ciega):.0f}%)")

    # ── requisito-como-tarea (post-filtro como detector) v11 vs v12 ──
    def rr(pop, campo, split):
        c = 0; tot = 0
        for r in pop:
            items = ([x.strip() for x in (r[campo] or '').split(';') if x.strip()] if split
                     else r[campo])
            for it in items:
                tot += 1
                if es_requisito_como_tarea(it):
                    c += 1
        return c, tot
    r11, t11 = rr(muestra, 'v11', True)
    r12, t12 = rr(muestra, 'v12', False)
    print(f"\n=== requisito/beneficio-como-tarea (detector N3) ===")
    print(f"  v11: {r11}/{t11} items ({100*r11/max(t11,1):.1f}%)")
    print(f"  v12: {r12}/{t12} items ({100*r12/max(t12,1):.1f}%)")

    # ── ANTI-ALUCINACIÓN (requisito DURO) ──
    anti_v12_no_vacio = [r for r in anti if r['n_v12'] > 0]
    print(f"\n=== ANTI-ALUCINACIÓN (población genuinamente-sin-tareas), n={len(anti)} ===")
    print(f"  v11 ya daba 0: {sum(1 for r in anti if r['n_v11']==0)}/{len(anti)}")
    print(f"  v12 da 0:      {sum(1 for r in anti if r['n_v12']==0)}/{len(anti)}")
    print(f"  *** v12 con n>0 (REGRESIONES a investigar): {len(anti_v12_no_vacio)} ***")
    for r in anti_v12_no_vacio:
        print(f"     id={r['id']} {r['portal']} len={r['cuerpo_len']} v12={r['v12']}")

    # muestra de 30 para lectura humana (ids)
    import random
    random.seed(7)
    lectura = random.sample(muestra, min(30, len(muestra)))
    Path(ROOT / 'exports/reportes/N_gate2_lectura30_ids.json').write_text(
        json.dumps([r['id'] for r in lectura]))
    print(f"\n30 ids para lectura humana -> exports/reportes/N_gate2_lectura30_ids.json")


if __name__ == '__main__':
    main()
