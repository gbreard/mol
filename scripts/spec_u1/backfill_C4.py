#!/usr/bin/env python3
"""
SPEC U-1 C4 — Backfill flags ESCO en ofertas_esco_skills_detalle.

Ejecuta el UPDATE del SPEC §7.2:
- is_essential_for_occupation = 1 si (occupation_uri, skill_uri, 'essential') existe en esco_associations
- is_optional_for_occupation = 1 si (occupation_uri, skill_uri, 'optional') existe
- 0 en caso contrario

WHERE EXISTS filtra a ofertas con esco_occupation_uri != '' (~1.27M filas backfilleables).

Ejecuta como sentencia SQLite single. Mide latencia. Loguea métricas pre/post.
"""
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

ROOT = Path('/mnt/d/OEDE/Webscrapping')
DB_PATH = str(ROOT / 'database/bumeran_scraping.db')
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_PATH = ROOT / f'logs/spec_u1_C4_backfill_{TS}.log'
SUMMARY_PATH = ROOT / f'logs/spec_u1_C4_backfill_summary_{TS}.json'


def log_event(fh, payload):
    fh.write(json.dumps(payload, default=str, ensure_ascii=False) + '\n')
    fh.flush()


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, 'w', encoding='utf-8')

    started_at = datetime.now()
    print(f"=== SPEC U-1 C4 — Backfill flags ESCO ===")
    print(f"Started: {started_at.isoformat()}")
    print(f"Log: {LOG_PATH}")

    log_event(fh, {'event': 'header', 'timestamp': started_at.isoformat()})

    con = sqlite3.connect(DB_PATH, timeout=3600)  # 1h timeout en lock
    con.execute("PRAGMA journal_mode = WAL")  # mejor concurrencia
    con.execute("PRAGMA synchronous = NORMAL")  # menos fsync, OK para batch
    cur = con.cursor()

    # Pre-conteo
    print("\n=== Pre-conteo ===")
    pre_total = cur.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle").fetchone()[0]
    pre_zero = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle
        WHERE is_essential_for_occupation = 0 AND is_optional_for_occupation = 0
    """).fetchone()[0]
    pre_essential = cur.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle WHERE is_essential_for_occupation = 1").fetchone()[0]
    pre_optional = cur.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle WHERE is_optional_for_occupation = 1").fetchone()[0]
    print(f"  total: {pre_total:,}")
    print(f"  pre essential=1: {pre_essential:,}")
    print(f"  pre optional=1:  {pre_optional:,}")
    print(f"  pre zero (ambos 0): {pre_zero:,}")
    log_event(fh, {'event': 'pre_count', 'total': pre_total,
                    'essential': pre_essential, 'optional': pre_optional, 'zero': pre_zero})

    # UPDATE
    update_sql = """
        UPDATE ofertas_esco_skills_detalle AS sd
        SET
          is_essential_for_occupation = COALESCE((
            SELECT 1 FROM esco_associations ea
            JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
            WHERE ea.occupation_uri = om.esco_occupation_uri
              AND ea.skill_uri = sd.esco_skill_uri
              AND ea.relation_type = 'essential'
            LIMIT 1
          ), 0),
          is_optional_for_occupation = COALESCE((
            SELECT 1 FROM esco_associations ea
            JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
            WHERE ea.occupation_uri = om.esco_occupation_uri
              AND ea.skill_uri = sd.esco_skill_uri
              AND ea.relation_type = 'optional'
            LIMIT 1
          ), 0)
        WHERE EXISTS (
          SELECT 1 FROM ofertas_esco_matching om
          WHERE om.id_oferta = sd.id_oferta
            AND om.esco_occupation_uri != ''
            AND om.esco_occupation_uri IS NOT NULL
        )
    """

    print("\n=== Ejecutando UPDATE ===")
    log_event(fh, {'event': 'update_start', 'timestamp': datetime.now().isoformat()})
    t0 = time.time()
    cur.execute(update_sql)
    elapsed = time.time() - t0
    rows_changed = cur.rowcount
    print(f"  UPDATE completado en {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Filas modificadas: {rows_changed:,}")
    log_event(fh, {'event': 'update_done',
                    'elapsed_seconds': round(elapsed, 1),
                    'rows_changed': rows_changed})

    print("\n  Commit...")
    t1 = time.time()
    con.commit()
    print(f"  Commit en {time.time()-t1:.1f}s")

    # Post-conteo (Q1 del SPEC §7.4)
    print("\n=== Post-conteo (Q1 SPEC §7.4) ===")
    post_essential = cur.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle WHERE is_essential_for_occupation = 1").fetchone()[0]
    post_optional = cur.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle WHERE is_optional_for_occupation = 1").fetchone()[0]
    post_zero_total = cur.execute("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle
        WHERE is_essential_for_occupation = 0 AND is_optional_for_occupation = 0
    """).fetchone()[0]
    print(f"  n_essential: {post_essential:,}")
    print(f"  n_optional:  {post_optional:,}")
    print(f"  n_zero:      {post_zero_total:,}")
    print(f"  total:       {pre_total:,}")

    # Post-conteo restringido a backfilleables
    print("\n=== Post-conteo solo en backfilleables (donde URI != '') ===")
    backfill_filter = """
        FROM ofertas_esco_skills_detalle sd
        WHERE EXISTS (
          SELECT 1 FROM ofertas_esco_matching om
          WHERE om.id_oferta = sd.id_oferta
            AND om.esco_occupation_uri != ''
            AND om.esco_occupation_uri IS NOT NULL
        )
    """
    bf_essential = cur.execute(f"SELECT COUNT(*) {backfill_filter} AND sd.is_essential_for_occupation = 1").fetchone()[0]
    bf_optional = cur.execute(f"SELECT COUNT(*) {backfill_filter} AND sd.is_optional_for_occupation = 1").fetchone()[0]
    bf_zero = cur.execute(f"SELECT COUNT(*) {backfill_filter} AND sd.is_essential_for_occupation = 0 AND sd.is_optional_for_occupation = 0").fetchone()[0]
    bf_total = cur.execute(f"SELECT COUNT(*) {backfill_filter}").fetchone()[0]
    print(f"  Backfilleables total: {bf_total:,}")
    print(f"    essential=1: {bf_essential:,}  ({bf_essential*100/bf_total:.1f}%)")
    print(f"    optional=1:  {bf_optional:,}  ({bf_optional*100/bf_total:.1f}%)")
    print(f"    zero:        {bf_zero:,}  ({bf_zero*100/bf_total:.1f}%)")

    # F-meta
    print("\n=== F-meta (SPEC §7.5) ===")
    fmeta = cur.execute("""
        WITH oferta_cobertura AS (
            SELECT om.id_oferta,
                   SUM(CASE WHEN sd.is_essential_for_occupation = 1 OR sd.is_optional_for_occupation = 1
                            THEN 1 ELSE 0 END) AS skills_en_catalogo
            FROM ofertas_esco_matching om
            JOIN ofertas_esco_skills_detalle sd ON om.id_oferta = sd.id_oferta
            WHERE om.esco_occupation_uri != ''
            GROUP BY om.id_oferta
        )
        SELECT
            AVG(CASE WHEN skills_en_catalogo >= 1 THEN 1.0 ELSE 0.0 END) * 100 AS K1,
            AVG(CASE WHEN skills_en_catalogo >= 3 THEN 1.0 ELSE 0.0 END) * 100 AS K3,
            AVG(CASE WHEN skills_en_catalogo >= 5 THEN 1.0 ELSE 0.0 END) * 100 AS K5,
            COUNT(*) AS n_ofertas,
            AVG(skills_en_catalogo) AS avg_skills_en_catalogo
        FROM oferta_cobertura
    """).fetchone()
    K1, K3, K5, n_ofertas, avg_sk = fmeta
    print(f"  cobertura_K1 (>=1 skill en catálogo): {K1:.2f}%")
    print(f"  cobertura_K3 (>=3 skills en catálogo): {K3:.2f}%")
    print(f"  cobertura_K5 (>=5 skills en catálogo): {K5:.2f}%")
    print(f"  Avg skills en catálogo por oferta: {avg_sk:.2f}")
    print(f"  Total ofertas con URI: {n_ofertas:,}")

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

    summary = {
        'event': 'summary',
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'duration_seconds': round(duration, 1),
        'duration_human': f"{int(duration//60)}m{int(duration%60)}s",
        'update_elapsed_seconds': round(elapsed, 1),
        'update_rows_changed': rows_changed,
        'pre': {'total': pre_total, 'essential': pre_essential, 'optional': pre_optional, 'zero': pre_zero},
        'post': {'total': pre_total, 'essential': post_essential, 'optional': post_optional, 'zero': post_zero_total},
        'backfilleables': {'total': bf_total, 'essential': bf_essential, 'optional': bf_optional, 'zero': bf_zero},
        'F_meta': {'K1': round(K1, 2), 'K3': round(K3, 2), 'K5': round(K5, 2),
                    'n_ofertas': n_ofertas, 'avg_skills_en_catalogo': round(avg_sk, 2)},
    }
    log_event(fh, summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print()
    print("=" * 60)
    print("RESUMEN C4")
    print("=" * 60)
    print(f"Duración total:    {summary['duration_human']}")
    print(f"UPDATE elapsed:    {elapsed:.0f}s")
    print(f"Filas modificadas: {rows_changed:,}")
    print(f"F-meta: K1={K1:.1f}% K3={K3:.1f}% K5={K5:.1f}%")
    print()
    print(f"Log: {LOG_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    fh.close()
    con.close()


if __name__ == '__main__':
    main()
