#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC E Fase 2 — A/B test: embeddings viejos (solo label) vs nuevos (enriquecidos).

Para 100 ofertas (20 gold + 60 top reglas + 20 sin regla), corre matching contra
ambos pools y genera reportes comparativos.

Outputs:
  - /tmp/spec_e_ab/summary.csv       — 1 fila por oferta (resumen)
  - /tmp/spec_e_ab/detalle.csv       — 1 fila por (oferta, fuente, tarea, rank)
  - /tmp/spec_e_ab/agregados.txt     — métricas agregadas
  - /tmp/spec_e_ab/gold_comparison.md — revisión visual de las 20 gold

Sample:
    python3 scripts/embeddings/ab_test_embeddings.py
"""
import argparse
import csv
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'config'))


# Ofertas "gold" de referencia conocidas
GOLD_IDS = [
    # Caso Cyn metalúrgico y plástico
    7907119232,
    9255109063,
    # Enfermera (control positivo)
    1118173872,
    # Cajero
    10811633309,
    # Cocinero
    10417283746,
    # Mozo/camarero
    10659377867,
    # Abogada / compliance
    1116643439,
    # Asistente ejecutiva
    1117786913,
    # Contador
    1116536336,
    # Analista IT
    1117974750,
    # Analista administrativo
    7398018208,
    # Operario de mantenimiento (dominio mixto)
    1117953485,
    # Personal de limpieza
    1118020378,
    # Operario CNC
    7942527874,
    # Ingeniero civil
    1118168092,  # Project manager
    # Asesor matrículas universitarias
    1118038669,
    # Vendedor
    6284447759,
    # Operarios envasado
    7411191076,
    # Electricista
    1118092286,
    # Veterinaria
    1117995971,
]


def seleccionar_muestra(conn, n_random=60, n_sin_regla=20):
    """Selecciona 100 ofertas: 20 gold + 60 top reglas + 20 sin regla."""
    c = conn.cursor()
    ids = set()

    # 1) Gold
    placeholder = ','.join('?' for _ in GOLD_IDS)
    c.execute(f'''SELECT m.id_oferta FROM ofertas_esco_matching m
                  WHERE m.id_oferta IN ({placeholder})
                    AND m.estado_validacion IN ('validado','validado_claude','validado_humano')
                    AND m.skills_semantico_json IS NOT NULL
                    AND m.skills_semantico_json != 'null' ''', GOLD_IDS)
    gold_encontrados = [r[0] for r in c.fetchall()]
    print(f'[ab] Gold encontrados: {len(gold_encontrados)}/{len(GOLD_IDS)}')
    ids.update(gold_encontrados)
    gold_set = set(gold_encontrados)

    # 2) Top reglas aleatorias (cubrir diversidad de dominios)
    c.execute('''SELECT regla_aplicada, isco_code, COUNT(*) as n
                 FROM ofertas_esco_matching
                 WHERE decision_metodo = 'regla_prioridad'
                   AND estado_validacion IN ('validado','validado_claude','validado_humano')
                 GROUP BY regla_aplicada
                 ORDER BY n DESC LIMIT 20''')
    top_reglas = c.fetchall()
    per_regla = max(n_random // len(top_reglas), 2)
    for regla, isco, _ in top_reglas:
        excluir_placeholders = ','.join('?' for _ in ids) if ids else "''"
        params = [regla] + list(ids) + [per_regla]
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                     WHERE regla_aplicada = ?
                       AND estado_validacion IN ('validado','validado_claude','validado_humano')
                       AND skills_semantico_json IS NOT NULL
                       AND id_oferta NOT IN ({excluir_placeholders})
                     ORDER BY RANDOM() LIMIT ?''', params)
        for (oid,) in c.fetchall():
            if len(ids) >= 20 + n_random:
                break
            ids.add(oid)
        if len(ids) >= 20 + n_random:
            break

    # 3) Sin regla
    c.execute('''SELECT id_oferta FROM ofertas_esco_matching
                 WHERE decision_metodo != 'regla_prioridad'
                   AND estado_validacion IN ('validado','validado_claude','validado_humano')
                   AND skills_semantico_json IS NOT NULL
                 ORDER BY RANDOM() LIMIT ?''', (n_sin_regla,))
    sin_regla_ids = [r[0] for r in c.fetchall()]
    sin_regla_set = set(sin_regla_ids)
    ids.update(sin_regla_ids)

    # Obtener datos de cada oferta
    placeholders = ','.join('?' for _ in ids)
    c.execute(f'''SELECT m.id_oferta, m.isco_code, m.regla_aplicada, m.decision_metodo,
                         n.titulo_limpio, o.titulo, n.tareas_explicitas,
                         n.skills_tecnicas_list, n.soft_skills_list,
                         n.sector_empresa, n.nivel_seniority, n.area_funcional
                  FROM ofertas_esco_matching m
                  JOIN ofertas o ON o.id_oferta = m.id_oferta
                  LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
                  WHERE m.id_oferta IN ({placeholders})''', list(ids))
    ofertas = []
    for row in c.fetchall():
        oid = row[0]
        categoria = 'gold' if oid in gold_set else ('sin_regla' if oid in sin_regla_set else 'random')
        ofertas.append({
            'id_oferta': oid,
            'categoria': categoria,
            'isco_code': row[1],
            'regla_aplicada': row[2],
            'decision_metodo': row[3],
            'titulo_limpio': row[4] or row[5] or '',
            'tareas_explicitas': row[6] or '',
            'skills_nlp_raw': row[7] or '',
            'soft_nlp_raw': row[8] or '',
            'sector': row[9],
            'seniority': row[10],
            'area': row[11],
        })
    return ofertas


def top_k_skills(model, embeddings_pool, metadata_pool, texto, k=5):
    """Para un texto, devuelve top-K skills del pool."""
    t_emb = model.encode(texto, normalize_embeddings=True)
    sims = embeddings_pool @ t_emb
    top_idx = np.argsort(sims)[-k:][::-1]
    return [
        {
            'rank': rank + 1,
            'skill_label': metadata_pool[int(i)].get('label', ''),
            'skill_uri': metadata_pool[int(i)].get('uri', ''),
            'score': float(sims[int(i)]),
        }
        for rank, i in enumerate(top_idx)
    ]


def get_esco_target_codes(regla_aplicada, regla_to_esco_codes):
    """Devuelve los esco_codes de la ocupación target de una regla, si hay mapa."""
    return regla_to_esco_codes.get(regla_aplicada, [])


def build_regla_to_esco_code_map():
    """Mapea regla → esco_code a partir de matching_rules_business.json + metadata ocupaciones nuevo."""
    rules = json.load(open(ROOT / 'config/matching_rules_business.json'))
    reglas_to_label = {}
    def walk(d):
        if isinstance(d, dict):
            if 'accion' in d and 'condicion' in d:
                return
            for k, v in d.items():
                if isinstance(v, dict) and 'accion' in v:
                    label = v['accion'].get('esco_label', '')
                    if label:
                        reglas_to_label[k] = label.lower().strip()
                else:
                    walk(v)
        elif isinstance(d, list):
            for v in d: walk(v)
    walk(rules)

    # Mapa label → esco_code desde metadata nueva
    metadata_occ = json.load(open(ROOT / 'database/embeddings/enriched/esco_occupations_metadata.json'))
    label_to_code = {}
    for o in metadata_occ:
        lbl = (o.get('label') or '').lower().strip()
        code = o.get('esco_code', '')
        if lbl and code:
            label_to_code[lbl] = code
            # También sin la parte "/femenina"
            lbl_short = lbl.split('/')[0].strip()
            label_to_code.setdefault(lbl_short, code)

    regla_to_code = {}
    for regla, label in reglas_to_label.items():
        code = label_to_code.get(label)
        if not code:
            code = label_to_code.get(label.split('/')[0].strip())
        if code:
            regla_to_code[regla] = code
    return regla_to_code


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b: return 1.0
    return len(a & b) / len(a | b)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    parser.add_argument('--out', default='/tmp/spec_e_ab')
    parser.add_argument('--k', type=int, default=5, help='Top K por tarea')
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Cargar embeddings y metadata ambos sets
    print('[ab] Cargando embeddings viejos...')
    emb_viejo = np.load(ROOT / 'database/embeddings/esco_skills_embeddings_full.npy')
    meta_viejo = json.load(open(ROOT / 'database/embeddings/esco_skills_metadata_full.json'))

    print('[ab] Cargando embeddings nuevos (enriched)...')
    emb_nuevo = np.load(ROOT / 'database/embeddings/enriched/esco_skills_embeddings_full.npy')
    meta_nuevo = json.load(open(ROOT / 'database/embeddings/enriched/esco_skills_metadata_full.json'))

    print(f'[ab] Viejo: {emb_viejo.shape}, Nuevo: {emb_nuevo.shape}')

    # 2) Mapa regla → esco_code target
    regla_to_esco = build_regla_to_esco_code_map()
    print(f'[ab] Reglas mapeadas a esco_code: {len(regla_to_esco)}')

    # 3) Seleccionar muestra
    conn = sqlite3.connect(args.db)
    ofertas = seleccionar_muestra(conn)
    conn.close()
    print(f'[ab] Ofertas seleccionadas: {len(ofertas)}')
    by_cat = Counter(o['categoria'] for o in ofertas)
    print(f'[ab] Por categoría: {dict(by_cat)}')

    # 4) Cargar modelo BGE-M3
    print('[ab] Cargando BGE-M3...')
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('BAAI/bge-m3')

    # 5) Correr matching sobre ambos sets
    summary_rows = []
    detalle_rows = []
    jaccard_scores = []
    hits_in_target_viejo = 0
    hits_in_target_nuevo = 0
    total_skills_con_target = 0

    # Lookup esco_codes_aplicable por skill_uri (solo para el set NUEVO, que es el único con ese campo)
    uri_to_esco_codes_nuevo = {m['uri']: m.get('esco_codes_aplicable', []) for m in meta_nuevo}

    t0 = time.time()
    for i, oferta in enumerate(ofertas, 1):
        oid = oferta['id_oferta']
        tareas = [t.strip() for t in oferta['tareas_explicitas'].split(';') if t.strip()]
        if not tareas:
            # Usar titulo como tarea si no hay tareas
            tareas = [oferta['titulo_limpio']]

        # Top-K por tarea con ambos sets
        skills_viejo_all = []
        skills_nuevo_all = []

        for tarea in tareas[:5]:  # máximo 5 tareas por oferta
            top_viejo = top_k_skills(model, emb_viejo, meta_viejo, tarea, k=args.k)
            top_nuevo = top_k_skills(model, emb_nuevo, meta_nuevo, tarea, k=args.k)

            for r in top_viejo:
                detalle_rows.append({
                    'id_oferta': oid, 'fuente': 'viejo', 'tarea': tarea[:100],
                    'rank': r['rank'], 'skill': r['skill_label'],
                    'score': round(r['score'], 4),
                })
                skills_viejo_all.append(r['skill_label'])

            for r in top_nuevo:
                detalle_rows.append({
                    'id_oferta': oid, 'fuente': 'nuevo', 'tarea': tarea[:100],
                    'rank': r['rank'], 'skill': r['skill_label'],
                    'score': round(r['score'], 4),
                })
                skills_nuevo_all.append(r['skill_label'])

        # Dedupe
        skills_viejo_dedup = list(dict.fromkeys(skills_viejo_all))[:10]
        skills_nuevo_dedup = list(dict.fromkeys(skills_nuevo_all))[:10]

        # Jaccard
        j = jaccard(skills_viejo_dedup, skills_nuevo_dedup)
        jaccard_scores.append(j)

        # Hits en target esco_code (solo relevante si tiene regla)
        esco_target = regla_to_esco.get(oferta['regla_aplicada'], '')
        hits_v = hits_n = 0
        if esco_target:
            total_skills_con_target += 1
            # Para el viejo: necesitamos los URIs top de cada tarea. Ya los tenemos en detalle_rows del viejo.
            # Más simple: para cada skill_uri que aparece en top-K nuevo, miro sus esco_codes_aplicable.
            # Para el viejo no tenemos esco_codes_aplicable, así que tenemos que cross-referenciar
            # usando el URI → esco_codes_aplicable del NUEVO metadata.
            # Es decir: "¿esta skill del top viejo, si la buscamos en el catálogo nuevo, aplica al esco_target?"
            uris_viejo = set()
            for r in detalle_rows:
                if r['id_oferta'] == oid and r['fuente'] == 'viejo':
                    # buscar el URI por label
                    pass  # simpler: usar metadata viejo
            # Simplificar: recalcular top con URIs
            for tarea in tareas[:5]:
                for r in top_k_skills(model, emb_viejo, meta_viejo, tarea, k=args.k):
                    codes = uri_to_esco_codes_nuevo.get(r['skill_uri'], [])
                    if esco_target in codes:
                        hits_v += 1
                        break  # 1 hit por tarea es suficiente
                for r in top_k_skills(model, emb_nuevo, meta_nuevo, tarea, k=args.k):
                    codes = uri_to_esco_codes_nuevo.get(r['skill_uri'], [])
                    if esco_target in codes:
                        hits_n += 1
                        break
            if hits_v: hits_in_target_viejo += 1
            if hits_n: hits_in_target_nuevo += 1

        summary_rows.append({
            'id_oferta': oid,
            'categoria': oferta['categoria'],
            'titulo_limpio': oferta['titulo_limpio'][:60],
            'regla': oferta['regla_aplicada'] or '-',
            'isco_code': oferta['isco_code'] or '-',
            'esco_target': esco_target or '-',
            'n_tareas': len(tareas),
            'top_skills_viejo': ' | '.join(skills_viejo_dedup[:5]),
            'top_skills_nuevo': ' | '.join(skills_nuevo_dedup[:5]),
            'jaccard_top10': round(j, 3),
            'target_viejo_hit': bool(hits_v),
            'target_nuevo_hit': bool(hits_n),
        })

        if i % 10 == 0:
            el = time.time() - t0
            print(f'  [{i}/{len(ofertas)}] {el:.0f}s  ETA {(len(ofertas)-i)*el/i:.0f}s')

    # 6) Escribir CSVs
    summary_path = out_dir / 'summary.csv'
    with open(summary_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    print(f'[ab] Escrito {summary_path}')

    detalle_path = out_dir / 'detalle.csv'
    with open(detalle_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(detalle_rows[0].keys()))
        w.writeheader()
        w.writerows(detalle_rows)
    print(f'[ab] Escrito {detalle_path}')

    # 7) Agregados
    agg_path = out_dir / 'agregados.txt'
    with open(agg_path, 'w', encoding='utf-8') as f:
        def p(msg):
            print(msg); f.write(msg + '\n')
        p('=' * 70)
        p('SPEC E — A/B test embeddings viejos vs enriquecidos')
        p('=' * 70)
        p(f'Ofertas procesadas: {len(ofertas)}')
        p(f'  Gold: {by_cat["gold"]}  Random: {by_cat.get("random",0)}  Sin regla: {by_cat.get("sin_regla",0)}')
        p('')
        p(f'Jaccard top-10 skills viejo vs nuevo:')
        p(f'  Promedio: {np.mean(jaccard_scores):.3f}')
        p(f'  Mediana:  {np.median(jaccard_scores):.3f}')
        p(f'  (Bajo = cambio dramático, Alto = cambio marginal)')
        p('')
        p(f'Hits en esco_target (skills que aplican al esco_code target de la regla):')
        p(f'  Ofertas con regla matching analizadas: {total_skills_con_target}')
        p(f'  VIEJO — con al menos 1 hit en alguna tarea: {hits_in_target_viejo}/{total_skills_con_target} ({hits_in_target_viejo*100/max(total_skills_con_target,1):.1f}%)')
        p(f'  NUEVO — con al menos 1 hit en alguna tarea: {hits_in_target_nuevo}/{total_skills_con_target} ({hits_in_target_nuevo*100/max(total_skills_con_target,1):.1f}%)')
        mejora = hits_in_target_nuevo - hits_in_target_viejo
        p(f'  MEJORA: +{mejora} ofertas ({mejora*100/max(total_skills_con_target,1):.1f} pp)')

    # 8) Reporte visual gold
    gold_path = out_dir / 'gold_comparison.md'
    with open(gold_path, 'w', encoding='utf-8') as f:
        f.write('# SPEC E A/B — revisión visual ofertas gold\n\n')
        for r in summary_rows:
            if r['categoria'] != 'gold': continue
            f.write(f"## [{r['id_oferta']}] {r['titulo_limpio']}\n\n")
            f.write(f"- Regla: `{r['regla']}`\n")
            f.write(f"- ISCO: {r['isco_code']}, ESCO target: {r['esco_target']}\n")
            f.write(f"- Jaccard top-10: {r['jaccard_top10']}\n")
            f.write(f"- Target hit: viejo={r['target_viejo_hit']}, nuevo={r['target_nuevo_hit']}\n\n")
            f.write(f"**Skills viejo:** {r['top_skills_viejo']}\n\n")
            f.write(f"**Skills nuevo:** {r['top_skills_nuevo']}\n\n")
            f.write('---\n\n')

    print(f'[ab] Listo. Outputs en {out_dir}/')


if __name__ == '__main__':
    main()
