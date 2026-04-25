#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC E Fase 4 — Retropropagación gradual de skills con embeddings enriquecidos.

Para cada oferta validada:
  1. Toma snapshot del skills_semantico_json actual en skills_semantico_json_backup_spec_e
     (solo la primera vez que la procesamos).
  2. Re-ejecuta extract_skills() con embeddings nuevos (ya en producción).
  3. Actualiza skills_semantico_json.
  4. Registra en tabla de progreso spec_e_retro_progress.

Resumable: si crashea, al reiniciar salta las ya procesadas.

Uso:
    python3 scripts/embeddings/retropropagar_skills_spec_e.py --tanda piloto
    python3 scripts/embeddings/retropropagar_skills_spec_e.py --tanda verificacion
    python3 scripts/embeddings/retropropagar_skills_spec_e.py --tanda scaleup
    python3 scripts/embeddings/retropropagar_skills_spec_e.py --tanda resto

    python3 scripts/embeddings/retropropagar_skills_spec_e.py --ids 7907119232,9255109063
    python3 scripts/embeddings/retropropagar_skills_spec_e.py --dry-run --tanda piloto
"""
import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'config'))


# Ofertas "gold" de referencia
GOLD_IDS = [
    7907119232, 9255109063, 1118173872, 10811633309, 10417283746,
    10659377867, 1116643439, 1117786913, 1116536336, 1117974750,
    7398018208, 1117953485, 1118020378, 7942527874, 1118168092,
    1118038669, 6284447759, 7411191076, 1118092286, 1117995971,
]


def ensure_tables(conn):
    """Crea tablas de backup y progreso si no existen."""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills_semantico_json_backup_spec_e (
        id_oferta TEXT PRIMARY KEY,
        skills_semantico_json TEXT,
        skills_semantico_json_size INTEGER,
        backup_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS spec_e_retro_progress (
        id_oferta TEXT PRIMARY KEY,
        tanda TEXT,
        procesada_at TEXT,
        skills_antes INTEGER,
        skills_despues INTEGER,
        tiempo_ms INTEGER
    )''')
    conn.commit()


def seleccionar_ids(conn, tanda: str, limit: int = None, extra_ids=None):
    """Selecciona IDs por tanda:
       piloto: 20 gold + 80 random validated con regla aplicada
       verificacion: 1000 estratificadas por ISCO top
       scaleup: 10000 con regla
       resto: todas las validadas sin procesar
    """
    c = conn.cursor()
    # Excluir ya procesadas
    c.execute('SELECT id_oferta FROM spec_e_retro_progress')
    procesadas = {r[0] for r in c.fetchall()}

    ids = []

    if extra_ids:
        ids.extend(str(i) for i in extra_ids if str(i) not in procesadas)

    if tanda == 'piloto':
        # 20 gold + 80 random validated con regla
        placeholder = ','.join('?' for _ in GOLD_IDS)
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                      WHERE id_oferta IN ({placeholder})
                        AND estado_validacion IN ('validado','validado_claude','validado_humano')''',
                  GOLD_IDS)
        gold_found = [r[0] for r in c.fetchall() if r[0] not in procesadas]
        ids.extend(gold_found)

        # 80 random con regla
        excluir = list(procesadas) + ids
        excl_p = ','.join('?' for _ in excluir) if excluir else "''"
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                      WHERE estado_validacion IN ('validado','validado_claude','validado_humano')
                        AND decision_metodo = 'regla_prioridad'
                        AND skills_semantico_json IS NOT NULL AND skills_semantico_json != 'null'
                        AND id_oferta NOT IN ({excl_p})
                      ORDER BY RANDOM() LIMIT 80''', excluir)
        ids.extend(r[0] for r in c.fetchall())

    elif tanda == 'verificacion':
        # 1000 estratificado: 20 por cada top 50 ISCOs
        c.execute('''SELECT isco_code, COUNT(*) FROM ofertas_esco_matching
                     WHERE estado_validacion IN ('validado','validado_claude','validado_humano')
                     GROUP BY isco_code ORDER BY 2 DESC LIMIT 50''')
        top_iscos = [r[0] for r in c.fetchall()]
        for isco in top_iscos:
            excluir = list(procesadas) + ids
            excl_p = ','.join('?' for _ in excluir) if excluir else "''"
            params = [isco] + excluir
            c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                          WHERE isco_code = ?
                            AND estado_validacion IN ('validado','validado_claude','validado_humano')
                            AND skills_semantico_json IS NOT NULL
                            AND id_oferta NOT IN ({excl_p})
                          ORDER BY RANDOM() LIMIT 20''', params)
            ids.extend(r[0] for r in c.fetchall())

    elif tanda == 'scaleup':
        # 10000 con regla aplicada
        excluir = list(procesadas) + ids
        excl_p = ','.join('?' for _ in excluir) if excluir else "''"
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                      WHERE decision_metodo = 'regla_prioridad'
                        AND estado_validacion IN ('validado','validado_claude','validado_humano')
                        AND skills_semantico_json IS NOT NULL
                        AND id_oferta NOT IN ({excl_p})
                      LIMIT 10000''', excluir)
        ids.extend(r[0] for r in c.fetchall())

    elif tanda == 'resto':
        excluir = list(procesadas) + ids
        excl_p = ','.join('?' for _ in excluir) if excluir else "''"
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                      WHERE estado_validacion IN ('validado','validado_claude','validado_humano')
                        AND skills_semantico_json IS NOT NULL
                        AND id_oferta NOT IN ({excl_p})''', excluir)
        ids.extend(r[0] for r in c.fetchall())

    if limit:
        ids = ids[:limit]
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    parser.add_argument('--tanda', choices=['piloto', 'verificacion', 'scaleup', 'resto'])
    parser.add_argument('--ids', help='IDs específicos separados por coma')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--batch-size', type=int, default=50)
    args = parser.parse_args()

    if not args.tanda and not args.ids:
        parser.error('requiere --tanda o --ids')

    conn = sqlite3.connect(args.db)
    ensure_tables(conn)

    extra_ids = args.ids.split(',') if args.ids else None
    ids_a_procesar = seleccionar_ids(conn, args.tanda or '', args.limit, extra_ids)
    print(f'[retro] Tanda "{args.tanda or args.ids}" → {len(ids_a_procesar):,} ofertas')
    if not ids_a_procesar:
        print('[retro] Nada que hacer (todas procesadas?)')
        conn.close()
        return

    if args.dry_run:
        print('[retro] DRY-RUN — no se persisten cambios')
        print(f'  Primeros 10 IDs: {ids_a_procesar[:10]}')
        conn.close()
        return

    # Cargar extractor (embeddings ya en producción apuntan a enriched)
    print('[retro] Cargando extractor...')
    from skills_implicit_extractor import SkillsImplicitExtractor
    extractor = SkillsImplicitExtractor(verbose=False)
    print(f'[retro] Metadata: {len(extractor.metadata):,} skills, shape {extractor.embeddings.shape}')

    stats = {'ok': 0, 'skipped_no_nlp': 0, 'errores': 0, 'skills_antes': 0, 'skills_despues': 0}
    t0 = time.time()

    # Procesar en batches
    c = conn.cursor()
    for i, oid in enumerate(ids_a_procesar, 1):
        try:
            # Leer NLP + skills actuales
            c.execute('''SELECT m.skills_semantico_json, n.titulo_limpio, n.tareas_explicitas,
                                n.skills_tecnicas_list, n.soft_skills_list,
                                n.sector_empresa, n.nivel_seniority, n.area_funcional
                         FROM ofertas_esco_matching m
                         LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
                         WHERE m.id_oferta = ?''', (oid,))
            row = c.fetchone()
            if not row:
                stats['errores'] += 1; continue
            sjson_viejo, tl, tareas, sk_nlp_raw, soft_raw, sector, sen, area = row
            if not tl:
                stats['skipped_no_nlp'] += 1; continue

            # Backup (solo primera vez)
            c.execute('''INSERT OR IGNORE INTO skills_semantico_json_backup_spec_e
                         (id_oferta, skills_semantico_json, skills_semantico_json_size, backup_at)
                         VALUES (?, ?, ?, ?)''',
                      (oid, sjson_viejo, len(sjson_viejo or ''), datetime.now(timezone.utc).isoformat()))

            # Re-extraer
            skills_nlp = [s.strip() for s in (sk_nlp_raw or '').split(',') if s.strip()] if sk_nlp_raw else []
            soft_nlp = [s.strip() for s in (soft_raw or '').split(',') if s.strip()] if soft_raw else []
            t_oferta0 = time.time()
            skills_nuevas = extractor.extract_skills(
                titulo_limpio=tl, tareas_explicitas=tareas or '',
                skills_nlp=skills_nlp, soft_skills_nlp=soft_nlp,
                sector_empresa=sector, nivel_seniority=sen, area_funcional=area,
            )
            dt_ms = int((time.time() - t_oferta0) * 1000)

            # Conteos
            try:
                sk_antes = len(json.loads(sjson_viejo) if sjson_viejo else [])
            except Exception:
                sk_antes = 0
            sk_despues = len(skills_nuevas)
            stats['skills_antes'] += sk_antes
            stats['skills_despues'] += sk_despues

            # Update JSON
            nuevo_json = json.dumps(skills_nuevas, ensure_ascii=False)
            c.execute('UPDATE ofertas_esco_matching SET skills_semantico_json = ? WHERE id_oferta = ?',
                      (nuevo_json, oid))

            # Update tabla normalizada ofertas_esco_skills_detalle
            # (imita el DELETE+INSERT de match_ofertas_v3._persist_skills_detail)
            c.execute('DELETE FROM ofertas_esco_skills_detalle WHERE id_oferta = ?',
                      (str(oid),))
            seen_uris = {}
            for sk in skills_nuevas:
                uri = (sk.get('skill_uri') or '').strip()
                if not uri:
                    continue
                if uri not in seen_uris or (sk.get('score') or 0) > (seen_uris[uri].get('score') or 0):
                    seen_uris[uri] = sk
            for sk in seen_uris.values():
                texto_orig = sk.get('texto_fuente') or sk.get('tarea') or None
                if texto_orig and len(texto_orig) > 200:
                    texto_orig = texto_orig[:200]
                c.execute('''INSERT INTO ofertas_esco_skills_detalle (
                                id_oferta, skill_mencionado, skill_tipo_fuente,
                                esco_skill_uri, esco_skill_label, match_score, match_method,
                                esco_skill_type, source_classification, texto_original
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (str(oid),
                           sk.get('skill_esco', sk.get('skill', '')),
                           sk.get('origen', 'unknown'),
                           sk.get('skill_uri', ''),
                           sk.get('skill_esco', ''),
                           sk.get('score', 0),
                           'implicit_bge_m3',
                           sk.get('L1', 'T'),
                           json.dumps({
                               'L1': sk.get('L1', ''),
                               'L1_nombre': sk.get('L1_nombre', ''),
                               'L2': sk.get('L2', ''),
                               'L2_nombre': sk.get('L2_nombre', ''),
                               'es_digital': sk.get('es_digital', False)
                           }, ensure_ascii=False),
                           texto_orig))

            c.execute('''INSERT OR REPLACE INTO spec_e_retro_progress
                         (id_oferta, tanda, procesada_at, skills_antes, skills_despues, tiempo_ms)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (oid, args.tanda or 'ids', datetime.now(timezone.utc).isoformat(),
                       sk_antes, sk_despues, dt_ms))
            stats['ok'] += 1
        except Exception as e:
            stats['errores'] += 1
            print(f'  [retro] ERROR en {oid}: {e}')
            continue

        # Commit cada batch
        if i % args.batch_size == 0:
            conn.commit()
            el = time.time() - t0
            rate = i / el
            eta = (len(ids_a_procesar) - i) / rate
            print(f'  [{i}/{len(ids_a_procesar)}] {rate:.1f}/s  ETA {eta:.0f}s  ok={stats["ok"]} err={stats["errores"]}')

    conn.commit()
    el = time.time() - t0
    print(f'\n[retro] Terminado en {el/60:.1f} min')
    print(f'  OK: {stats["ok"]}  Sin NLP: {stats["skipped_no_nlp"]}  Errores: {stats["errores"]}')
    if stats["ok"]:
        print(f'  Skills promedio: antes {stats["skills_antes"]/stats["ok"]:.1f}  → después {stats["skills_despues"]/stats["ok"]:.1f}')

    conn.close()


if __name__ == '__main__':
    main()
