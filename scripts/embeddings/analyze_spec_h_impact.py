#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC H Fase 3 — Análisis de impacto en dry-run sobre las 18,880 ofertas del scope.

Ejecuta MatcherV3.match() sobre cada oferta sin persistir, y genera:
  - /tmp/spec_h_dry_run/detalle.csv   (1 fila por oferta con antes/después)
  - /tmp/spec_h_dry_run/agregados.txt (métricas resumen)
  - /tmp/spec_h_dry_run/sospechosos.csv (score baja + cambio ISCO)
  - /tmp/spec_h_dry_run/ahora_dispara_regla.csv (decision_metodo cambia)

Uso:
    python3 scripts/embeddings/analyze_spec_h_impact.py [--limit N] [--out /tmp/spec_h_dry_run]
"""
import argparse
import csv
import json
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'config'))

UMBRAL = 0.45


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--out', default='/tmp/spec_h_dry_run')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Scope: semantico_unico + validadas
    conn = sqlite3.connect(args.db)
    c = conn.cursor()
    q = '''SELECT m.id_oferta, m.isco_code, m.esco_occupation_label, m.score_semantico,
                  m.decision_metodo, m.estado_validacion,
                  n.titulo_limpio, n.tareas_explicitas,
                  n.skills_tecnicas_list, n.soft_skills_list,
                  n.sector_empresa, n.nivel_seniority, n.area_funcional,
                  o.titulo, o.descripcion
           FROM ofertas_esco_matching m
           LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
           LEFT JOIN ofertas o ON o.id_oferta = m.id_oferta
           WHERE m.decision_metodo = 'semantico_unico'
             AND m.estado_validacion IN ('validado','validado_claude','validado_humano')
             AND m.skills_semantico_json IS NOT NULL AND m.skills_semantico_json != 'null' '''
    if args.limit:
        q += f' LIMIT {int(args.limit)}'
    c.execute(q)
    ofertas = c.fetchall()
    print(f'[analyze] Scope: {len(ofertas):,} ofertas')

    # Cargar matcher (usa embeddings enriquecidos ya en prod)
    print('[analyze] Cargando MatcherV3...')
    from match_ofertas_v3 import MatcherV3
    matcher = MatcherV3(db_conn=conn, verbose=False)
    print(f'[analyze] Matcher v{matcher.VERSION} listo')

    stats = {
        'total': 0,
        'sin_cambio': 0,
        'cambian_isco': 0,
        'cambian_isco_misma_familia': 0,
        'score_sube': 0,
        'score_baja': 0,
        'ahora_dispara_regla': 0,
        'score_bajo_skip': 0,
        'error': 0,
    }
    detalle_rows = []
    sospechosos = []
    ahora_regla = []

    t0 = time.time()
    for i, row in enumerate(ofertas, 1):
        oid, isco_v, esco_v, score_v, dec_v, estado, tl, tareas, sk, soft, sec, sen, area, tit, desc = row
        oferta_nlp = {
            'titulo_limpio': tl, 'titulo': tit or tl or '',
            'tareas_explicitas': tareas or '', 'skills_tecnicas_list': sk or '',
            'soft_skills_list': soft or '', 'sector_empresa': sec,
            'nivel_seniority': sen, 'area_funcional': area, 'descripcion': desc or '',
        }
        if not tl and not tit:
            stats['error'] += 1
            continue
        try:
            result = matcher.match(oferta_nlp)
        except Exception as e:
            stats['error'] += 1
            if args.verbose:
                print(f'  ERROR {oid}: {e}')
            continue

        isco_n = str(result.isco_code) if result.isco_code else ''
        score_n = float(result.score or 0)
        dec_n = result.metadata.get('decision_metodo', dec_v)
        esco_n = result.esco_label or result.metadata.get('esco_label') or ''

        stats['total'] += 1
        cambia = isco_n != isco_v
        if not cambia:
            stats['sin_cambio'] += 1
        else:
            stats['cambian_isco'] += 1
            if isco_v and isco_n and isco_v[:2] == isco_n[:2]:
                stats['cambian_isco_misma_familia'] += 1

        if (score_v or 0) and score_n > score_v: stats['score_sube'] += 1
        else: stats['score_baja'] += 1

        if dec_n == 'regla_prioridad' and dec_v != 'regla_prioridad':
            stats['ahora_dispara_regla'] += 1
            ahora_regla.append({
                'id_oferta': oid, 'titulo': (tl or tit or '')[:60],
                'isco_viejo': isco_v, 'isco_nuevo': isco_n,
                'regla': result.metadata.get('regla_aplicada', ''),
                'score_nuevo': round(score_n, 3),
            })

        if score_n < UMBRAL:
            stats['score_bajo_skip'] += 1

        # Sospechoso: score baja + cambio ISCO
        if cambia and (score_v or 0) and score_n < score_v - 0.05:
            sospechosos.append({
                'id_oferta': oid, 'titulo': (tl or tit or '')[:60],
                'isco_viejo': isco_v, 'esco_viejo': esco_v,
                'score_viejo': round(score_v or 0, 3),
                'isco_nuevo': isco_n, 'esco_nuevo': esco_n,
                'score_nuevo': round(score_n, 3),
            })

        detalle_rows.append({
            'id_oferta': oid, 'titulo': (tl or tit or '')[:60],
            'isco_viejo': isco_v, 'esco_viejo': (esco_v or '')[:40],
            'score_viejo': round(score_v or 0, 3),
            'isco_nuevo': isco_n, 'esco_nuevo': (esco_n or '')[:40],
            'score_nuevo': round(score_n, 3),
            'decision_metodo_nuevo': dec_n,
            'cambia_isco': cambia,
            'misma_familia_2dig': (isco_v and isco_n and isco_v[:2] == isco_n[:2]),
        })

        if i % 500 == 0:
            el = time.time() - t0
            rate = i / el
            eta = (len(ofertas) - i) / rate
            print(f'  [{i}/{len(ofertas)}] {rate:.1f}/s  ETA {eta/60:.0f} min')

    conn.close()
    el = time.time() - t0

    # Escribir reportes
    detalle_path = out_dir / 'detalle.csv'
    with open(detalle_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(detalle_rows[0].keys()) if detalle_rows else [])
        if detalle_rows:
            w.writeheader()
            w.writerows(detalle_rows)

    sospechosos_path = out_dir / 'sospechosos.csv'
    with open(sospechosos_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(sospechosos[0].keys()) if sospechosos else
                           ['id_oferta','titulo','isco_viejo','esco_viejo','score_viejo',
                            'isco_nuevo','esco_nuevo','score_nuevo'])
        w.writeheader()
        if sospechosos:
            w.writerows(sospechosos)

    ahora_regla_path = out_dir / 'ahora_dispara_regla.csv'
    with open(ahora_regla_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(ahora_regla[0].keys()) if ahora_regla else
                           ['id_oferta','titulo','isco_viejo','isco_nuevo','regla','score_nuevo'])
        w.writeheader()
        if ahora_regla:
            w.writerows(ahora_regla)

    # Agregados
    agg_path = out_dir / 'agregados.txt'
    with open(agg_path, 'w') as f:
        def pr(m): print(m); f.write(m + '\n')
        pr('=' * 70)
        pr('SPEC H Fase 3 — Análisis de impacto (dry-run)')
        pr('=' * 70)
        pr(f'Tiempo ejecución: {el/60:.1f} min')
        pr(f'Ofertas procesadas: {stats["total"]:,}')
        pr(f'Errores: {stats["error"]}')
        pr('')
        pr('CAMBIOS DE ISCO:')
        pr(f'  Sin cambio (mismo ISCO): {stats["sin_cambio"]} ({stats["sin_cambio"]*100/max(stats["total"],1):.1f}%)')
        pr(f'  Cambian ISCO:            {stats["cambian_isco"]} ({stats["cambian_isco"]*100/max(stats["total"],1):.1f}%)')
        pr(f'    ↳ misma familia (2-dig): {stats["cambian_isco_misma_familia"]} ({stats["cambian_isco_misma_familia"]*100/max(stats["cambian_isco"],1):.0f}% de los cambios)')
        pr('')
        pr('SCORE SEMÁNTICO:')
        pr(f'  Score sube: {stats["score_sube"]} ({stats["score_sube"]*100/max(stats["total"],1):.1f}%)')
        pr(f'  Score baja o igual: {stats["score_baja"]}')
        pr('')
        pr('CASOS ESPECIALES:')
        pr(f'  Ahora dispara regla (antes era semantico_unico): {stats["ahora_dispara_regla"]} ({stats["ahora_dispara_regla"]*100/max(stats["total"],1):.1f}%)')
        pr(f'  Score nuevo < 0.45 (skip umbral): {stats["score_bajo_skip"]}')
        pr(f'  Sospechosos (cambio ISCO + score baja >0.05): {len(sospechosos)}')
        pr('')
        pr(f'Outputs:')
        pr(f'  - {detalle_path}')
        pr(f'  - {sospechosos_path} ({len(sospechosos)} filas)')
        pr(f'  - {ahora_regla_path} ({len(ahora_regla)} filas)')


if __name__ == '__main__':
    main()
