#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC B v2 — Análisis de impacto del filtro trust-source sobre BD.

Modo read-only: corre `_classify_skill_trust` sobre cada skill ya guardada en
`skills_semantico_json` (ofertas validadas) y reporta qué pasaría si se
aplicara el filtro. NO modifica ningún registro.

Salidas:
  * Distribución de trust_motivo (global)
  * % skills que serían descartadas
  * Ofertas con reducción drástica (>80% caídas) — muestra IDs
  * Por banda de contexto (crítico / pobre / medio / bueno)

Uso:
    python3 scripts/analyze_trust_impact.py [--db PATH] [--limit N] [--sample-ofertas N]
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "database"))
sys.path.insert(0, str(ROOT / "config"))


def load_classifier():
    """Retorna extractor que solo usa el clasificador (sin inicializar BGE-M3)."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    return SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)


def banda_contexto(desc_len: int, tareas_count: int) -> str:
    if desc_len < 400 and tareas_count == 0:
        return "critico"
    if desc_len < 400 and tareas_count <= 2:
        return "pobre"
    if desc_len < 600 and tareas_count < 2:
        return "corto_pobre"
    if desc_len <= 800 and tareas_count <= 5:
        return "medio"
    return "bueno"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "database" / "bumeran_scraping.db"))
    parser.add_argument("--limit", type=int, default=None,
                        help="Máximo de ofertas a analizar")
    parser.add_argument("--sample-ofertas", type=int, default=15,
                        help="Número de ofertas con reducción drástica a mostrar")
    args = parser.parse_args()

    classifier = load_classifier()

    conn = sqlite3.connect(args.db)
    c = conn.cursor()

    query = """
        SELECT m.id_oferta,
               m.skills_semantico_json,
               COALESCE(n.titulo_limpio, o.titulo) AS titulo_limpio,
               COALESCE(LENGTH(o.descripcion), 0) AS desc_len,
               COALESCE(n.tareas_explicitas, '') AS tareas_explicitas,
               COALESCE(n.skills_tecnicas_list, '') AS skills_nlp
        FROM ofertas_esco_matching m
        JOIN ofertas o ON o.id_oferta = m.id_oferta
        LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado','validado_claude','validado_humano')
          AND m.skills_semantico_json IS NOT NULL
          AND m.skills_semantico_json != 'null'
    """
    if args.limit:
        query += f" LIMIT {int(args.limit)}"

    c.execute(query)

    motivos_totales = Counter()
    motivos_por_origen = defaultdict(Counter)
    por_banda = defaultdict(lambda: {"skills": 0, "descartadas": 0, "ofertas": 0})
    reduccion_drastica = []
    total_ofertas = 0
    total_skills = 0
    total_descartadas = 0

    ofertas_con_skills_regla = 0

    for row in c.fetchall():
        oid, sjson, titulo_limpio, desc_len, tareas_explicitas, skills_nlp_raw = row

        try:
            skills = json.loads(sjson)
        except Exception:
            continue
        if not isinstance(skills, list) or not skills:
            continue

        # Construir contexto
        tareas_count = len([t for t in (tareas_explicitas or '').split(';') if t.strip()])
        skills_nlp_list = []
        if skills_nlp_raw:
            skills_nlp_list = [s for s in (skills_nlp_raw or '').split(',') if s.strip()]

        ctx = {
            'titulo_limpio': titulo_limpio or '',
            'tareas_explicitas': tareas_explicitas or '',
            'skills_tecnicas_list': skills_nlp_list,
        }
        banda = banda_contexto(desc_len, tareas_count)

        total_ofertas += 1
        por_banda[banda]["ofertas"] += 1

        descartadas_oferta = 0
        for s in skills:
            trust, motivo = classifier._classify_skill_trust(s, ctx)
            motivos_totales[motivo] += 1
            motivos_por_origen[s.get('origen', 'MISSING')][motivo] += 1
            total_skills += 1
            por_banda[banda]["skills"] += 1
            if not trust:
                total_descartadas += 1
                descartadas_oferta += 1
                por_banda[banda]["descartadas"] += 1

        if descartadas_oferta and len(skills) > 0:
            ratio = descartadas_oferta / len(skills)
            if ratio >= 0.80:
                reduccion_drastica.append((oid, titulo_limpio, len(skills), descartadas_oferta, banda))

    conn.close()

    # Reporte
    print("=" * 70)
    print("SPEC B v2 — Análisis de impacto trust-source")
    print("=" * 70)
    print(f"\nOfertas analizadas: {total_ofertas:,}")
    print(f"Skills totales: {total_skills:,}")
    print(f"Skills que caerían: {total_descartadas:,} ({total_descartadas*100/max(total_skills,1):.1f}%)")

    print(f"\n— Distribución de trust_motivo —")
    for motivo, n in motivos_totales.most_common():
        pct = n * 100 / max(total_skills, 1)
        bar = '#' * min(int(pct), 50)
        marcador = '✗' if motivo.startswith(('origen_tarea_corta_score_bajo',
                                              'titulo_corto_score_medio',
                                              'titulo_solo_fuente_score_bajo',
                                              'titulo_redundante_score_bajo',
                                              'fallback_origen_desconocido')) else '✓'
        print(f"  {marcador} {motivo:40}: {n:7,} ({pct:5.1f}%) {bar}")

    print(f"\n— Por origen —")
    for origen, c in sorted(motivos_por_origen.items()):
        total_origen = sum(c.values())
        descart_origen = sum(n for m, n in c.items() if m.startswith((
            'origen_tarea_corta_score_bajo', 'titulo_corto_score_medio',
            'titulo_solo_fuente_score_bajo', 'titulo_redundante_score_bajo',
            'fallback_origen_desconocido')))
        pct = descart_origen * 100 / max(total_origen, 1)
        print(f"  [{origen:20}] total={total_origen:7,}  descartadas={descart_origen:6,} ({pct:5.1f}%)")

    print(f"\n— Por banda de contexto —")
    for banda in ["critico", "pobre", "corto_pobre", "medio", "bueno"]:
        b = por_banda[banda]
        if b["ofertas"] == 0:
            continue
        pct_descart = b["descartadas"] * 100 / max(b["skills"], 1)
        skills_prom = b["skills"] / max(b["ofertas"], 1)
        descart_prom = b["descartadas"] / max(b["ofertas"], 1)
        print(f"  {banda:12}  ofertas={b['ofertas']:6,}  skills_prom={skills_prom:4.1f}  "
              f"descartadas_prom={descart_prom:4.1f}  ({pct_descart:4.1f}%)")

    print(f"\n— Ofertas con reducción drástica (≥80% descartadas): {len(reduccion_drastica):,} —")
    reduccion_drastica.sort(key=lambda r: -r[3])
    for oid, titulo, total, descart, banda in reduccion_drastica[:args.sample_ofertas]:
        titulo_short = (titulo or '')[:60]
        print(f"  [{oid}] {titulo_short:60} | banda={banda:10} | {descart}/{total} descartadas")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
