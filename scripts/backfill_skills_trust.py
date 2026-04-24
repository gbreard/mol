#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC B v2 — Fase 4: Retropropagación de trust + trust_motivo.

Enriquece cada skill en `ofertas_esco_matching.skills_semantico_json` con los
campos `trust` (bool) y `trust_motivo` (str) calculados con el clasificador
`_classify_skill_trust()`. NO descarta ninguna skill.

Objetivo: telemetría permanente para decisiones futuras sin alterar el
resultado del pipeline de matching.

Uso:
    python3 scripts/backfill_skills_trust.py                 # BD default
    python3 scripts/backfill_skills_trust.py --dry-run       # sin escribir
    python3 scripts/backfill_skills_trust.py --db /path.db
    python3 scripts/backfill_skills_trust.py --limit 1000    # subset
"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "database"))
sys.path.insert(0, str(ROOT / "config"))


def load_classifier():
    from skills_implicit_extractor import SkillsImplicitExtractor
    return SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "database" / "bumeran_scraping.db"))
    parser.add_argument("--dry-run", action="store_true",
                        help="No escribir cambios, solo reportar")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Commits cada N ofertas")
    args = parser.parse_args()

    classifier = load_classifier()
    conn = sqlite3.connect(args.db)
    c = conn.cursor()

    query = """
        SELECT m.id_oferta,
               m.skills_semantico_json,
               COALESCE(n.titulo_limpio, o.titulo) AS titulo_limpio,
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
    rows = c.fetchall()
    print(f"[INFO] Ofertas a procesar: {len(rows):,}")

    stats = {"ofertas": 0, "skills_total": 0, "trust_true": 0, "trust_false": 0,
             "sin_cambios": 0, "actualizadas": 0, "errores": 0}
    t0 = time.time()

    pending_updates = []

    for i, (oid, sjson, titulo_limpio, tareas_explicitas, skills_nlp_raw) in enumerate(rows, 1):
        try:
            skills = json.loads(sjson)
        except Exception:
            stats["errores"] += 1
            continue
        if not isinstance(skills, list):
            continue

        skills_nlp_list = [s for s in (skills_nlp_raw or '').split(',') if s.strip()]
        ctx = {
            'titulo_limpio': titulo_limpio or '',
            'tareas_explicitas': tareas_explicitas or '',
            'skills_tecnicas_list': skills_nlp_list,
        }

        modificada = False
        for s in skills:
            trust, motivo = classifier._classify_skill_trust(s, ctx)
            nuevo_trust = bool(trust)
            if s.get('trust') != nuevo_trust or s.get('trust_motivo') != motivo:
                s['trust'] = nuevo_trust
                s['trust_motivo'] = motivo
                modificada = True
            stats["skills_total"] += 1
            if trust:
                stats["trust_true"] += 1
            else:
                stats["trust_false"] += 1

        stats["ofertas"] += 1
        if modificada:
            stats["actualizadas"] += 1
            pending_updates.append((json.dumps(skills, ensure_ascii=False), oid))
        else:
            stats["sin_cambios"] += 1

        if len(pending_updates) >= args.batch_size and not args.dry_run:
            c.executemany(
                "UPDATE ofertas_esco_matching SET skills_semantico_json=? WHERE id_oferta=?",
                pending_updates,
            )
            conn.commit()
            pending_updates = []
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(rows) - i) / rate if rate else 0
            print(f"  [{i:>7,}/{len(rows):,}] {rate:5.0f} ofertas/s | ETA {eta/60:5.1f} min")

    if pending_updates and not args.dry_run:
        c.executemany(
            "UPDATE ofertas_esco_matching SET skills_semantico_json=? WHERE id_oferta=?",
            pending_updates,
        )
        conn.commit()

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"SPEC B v2 — Fase 4 {'DRY-RUN' if args.dry_run else 'APLICADO'}")
    print("=" * 60)
    print(f"Ofertas procesadas: {stats['ofertas']:,}")
    print(f"Skills tocadas: {stats['skills_total']:,}")
    print(f"  trust=True:  {stats['trust_true']:,} ({stats['trust_true']*100/max(stats['skills_total'],1):.1f}%)")
    print(f"  trust=False: {stats['trust_false']:,} ({stats['trust_false']*100/max(stats['skills_total'],1):.1f}%)")
    print(f"Ofertas actualizadas: {stats['actualizadas']:,}")
    print(f"Ofertas sin cambios: {stats['sin_cambios']:,}")
    print(f"Errores JSON: {stats['errores']:,}")
    print(f"Tiempo total: {elapsed/60:.1f} min")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
