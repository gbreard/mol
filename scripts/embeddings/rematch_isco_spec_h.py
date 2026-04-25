#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC H — Re-matching de ocupación ESCO para ofertas validadas con decision_metodo='semantico_unico'.

Usa `MatcherV3.match()` (pipeline completo con embeddings enriquecidos de SPEC E)
pero persiste SOLO los campos del matching de ocupación — NO toca skills.
Las skills se regeneran después en retropropagación combinada SPEC E + G.

Scope: 18,880 ofertas (15,516 validado_claude + 3,364 validado estricto con unlock).

Uso:
    python3 scripts/embeddings/rematch_isco_spec_h.py --tanda piloto
    python3 scripts/embeddings/rematch_isco_spec_h.py --tanda verificacion
    python3 scripts/embeddings/rematch_isco_spec_h.py --tanda resto
    python3 scripts/embeddings/rematch_isco_spec_h.py --ids X,Y --dry-run
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

UMBRAL_MIN_SCORE = 0.45  # Si el top-1 nuevo < umbral → skip (deja ESCO viejo)
UMBRAL_VIEJO_RUIDO = 0.50  # Si score_viejo < esto, era ruido → siempre aceptar el cambio
TOLERANCIA_REGRESION = 0.05  # Aceptar cambio si score_nuevo > score_viejo - tolerancia


def evaluar_cambio(score_viejo: float, score_nuevo: float, decision_metodo_nuevo: str,
                   isco_nuevo: str, isco_viejo: str, umbral_min: float) -> str:
    """
    Política D (mixta) — decide qué hacer con un re-match.

    Retorna uno de:
      - 'actualizada_dispara_regla': cambia decision_metodo a regla
      - 'skip_score_bajo': score nuevo bajo el umbral mínimo
      - 'skip_no_cambio': mismo ESCO viejo y nuevo
      - 'skip_regresion_probable': score nuevo cae mucho desde uno alto viejo
      - 'actualizada': cambio aceptado
    """
    sv = float(score_viejo or 0)
    sn = float(score_nuevo or 0)

    # 1. Regla curada siempre gana
    if decision_metodo_nuevo == 'regla_prioridad':
        return 'actualizada_dispara_regla'

    # 2. Score nuevo bajo umbral → no confiable, dejamos viejo
    if sn < umbral_min:
        return 'skip_score_bajo'

    # 3. Mismo ESCO → no hay cambio que aplicar
    if isco_nuevo == isco_viejo:
        return 'skip_no_cambio'

    # 4. Política D — proteger casos donde el viejo probablemente era correcto.
    #    Aceptamos el cambio si:
    #      a) score sube (con tolerancia de TOLERANCIA_REGRESION)
    #      b) o el viejo era bajo (< UMBRAL_VIEJO_RUIDO) → era ruido
    if sn > sv - TOLERANCIA_REGRESION:
        return 'actualizada'
    if sv < UMBRAL_VIEJO_RUIDO:
        return 'actualizada'
    return 'skip_regresion_probable'


def ensure_tables(conn):
    """Crea tablas de backup + progress."""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ofertas_matching_backup_spec_h (
        id_oferta TEXT PRIMARY KEY,
        isco_code_antes TEXT,
        esco_occupation_label_antes TEXT,
        titulo_esco_code_antes TEXT,
        score_semantico_antes REAL,
        decision_metodo_antes TEXT,
        estado_validacion_antes TEXT,
        matching_timestamp_antes TEXT,
        backup_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS spec_h_rematch_progress (
        id_oferta TEXT PRIMARY KEY,
        tanda TEXT,
        procesada_at TEXT,
        isco_anterior TEXT,
        isco_nuevo TEXT,
        score_anterior REAL,
        score_nuevo REAL,
        decision_metodo_anterior TEXT,
        decision_metodo_nuevo TEXT,
        resultado TEXT,  -- 'actualizada' | 'skip_score_bajo' | 'skip_regla' | 'skip_no_cambio' | 'error'
        tiempo_ms INTEGER,
        mensaje TEXT
    )''')
    conn.commit()


def seleccionar_ids(conn, tanda: str, limit: int = None, extra_ids=None):
    """Selecciona IDs por tanda, excluyendo las ya procesadas."""
    c = conn.cursor()
    c.execute('SELECT id_oferta FROM spec_h_rematch_progress')
    procesadas = {r[0] for r in c.fetchall()}

    ids = []
    if extra_ids:
        ids.extend(str(i) for i in extra_ids if str(i) not in procesadas)

    # Scope base: semantico_unico + validadas
    base_where = '''decision_metodo = 'semantico_unico'
                   AND estado_validacion IN ('validado','validado_claude','validado_humano')
                   AND skills_semantico_json IS NOT NULL'''

    if tanda == 'piloto':
        # 100 aleatorias
        excl = list(procesadas) + ids
        excl_ph = ','.join('?' for _ in excl) if excl else "''"
        query = f'''SELECT id_oferta FROM ofertas_esco_matching
                    WHERE {base_where}
                      AND id_oferta NOT IN ({excl_ph})
                    ORDER BY RANDOM() LIMIT 100'''
        c.execute(query, excl)
        ids.extend(r[0] for r in c.fetchall())

    elif tanda == 'verificacion':
        # 1000 estratificadas por isco_code
        c.execute(f'''SELECT isco_code, COUNT(*) FROM ofertas_esco_matching
                      WHERE {base_where}
                      GROUP BY isco_code ORDER BY 2 DESC LIMIT 50''')
        top_iscos = [r[0] for r in c.fetchall()]
        for isco in top_iscos:
            excl = list(procesadas) + ids
            excl_ph = ','.join('?' for _ in excl) if excl else "''"
            params = [isco] + excl
            c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                          WHERE {base_where} AND isco_code = ?
                            AND id_oferta NOT IN ({excl_ph})
                          ORDER BY RANDOM() LIMIT 20''', params)
            ids.extend(r[0] for r in c.fetchall())

    elif tanda == 'resto':
        excl = list(procesadas) + ids
        excl_ph = ','.join('?' for _ in excl) if excl else "''"
        c.execute(f'''SELECT id_oferta FROM ofertas_esco_matching
                      WHERE {base_where}
                        AND id_oferta NOT IN ({excl_ph})''', excl)
        ids.extend(r[0] for r in c.fetchall())

    if limit:
        ids = ids[:limit]
    return ids


def get_oferta_nlp(conn, id_oferta: str):
    """Construye el dict oferta_nlp que espera match_ofertas_v3."""
    c = conn.cursor()
    c.execute('''SELECT n.titulo_limpio, n.tareas_explicitas,
                        n.skills_tecnicas_list, n.soft_skills_list,
                        n.sector_empresa, n.nivel_seniority, n.area_funcional,
                        o.titulo, o.descripcion
                 FROM ofertas_nlp n
                 LEFT JOIN ofertas o ON o.id_oferta = n.id_oferta
                 WHERE n.id_oferta = ?''', (str(id_oferta),))
    row = c.fetchone()
    if not row:
        return None
    return {
        'titulo_limpio': row[0],
        'titulo': row[7] or row[0] or '',
        'tareas_explicitas': row[1] or '',
        'skills_tecnicas_list': row[2] or '',
        'soft_skills_list': row[3] or '',
        'sector_empresa': row[4],
        'nivel_seniority': row[5],
        'area_funcional': row[6],
        'descripcion': row[8] or '',
    }


def get_estado_actual(conn, id_oferta: str):
    """Lee estado matching actual para comparación + snapshot."""
    c = conn.cursor()
    c.execute('''SELECT isco_code, esco_occupation_label, titulo_esco_code,
                        score_semantico, decision_metodo, estado_validacion,
                        matching_timestamp
                 FROM ofertas_esco_matching WHERE id_oferta = ?''', (str(id_oferta),))
    row = c.fetchone()
    if not row: return None
    return dict(zip([
        'isco_code','esco_occupation_label','titulo_esco_code',
        'score_semantico','decision_metodo','estado_validacion','matching_timestamp'
    ], row))


def persist_matching_result(conn, id_oferta: str, result, estado_actual: dict, run_id: str):
    """Persiste SOLO los campos de matching de ocupación. NO toca skills.

    Respeta el trigger: si estado='validado', debe haber unlock previo.
    Retorna dict con info de lo actualizado.
    """
    c = conn.cursor()

    # Extraer campos del MatchResult
    isco_nuevo = str(result.isco_code) if result.isco_code else None
    esco_label_nuevo = result.esco_label or result.metadata.get('esco_label') or ''
    titulo_esco_code_nuevo = result.metadata.get('esco_code') or result.metadata.get('titulo_esco_code') or ''
    score_nuevo = float(result.score or 0)
    decision_metodo_nuevo = result.metadata.get('decision_metodo', estado_actual['decision_metodo'])

    c.execute('''UPDATE ofertas_esco_matching SET
                     isco_code = ?,
                     esco_occupation_label = ?,
                     titulo_esco_code = ?,
                     score_semantico = ?,
                     occupation_match_score = ?,
                     decision_metodo = ?,
                     matching_timestamp = ?,
                     matching_version = ?,
                     run_id = ?
                 WHERE id_oferta = ?''',
              (isco_nuevo, esco_label_nuevo, titulo_esco_code_nuevo,
               score_nuevo, score_nuevo, decision_metodo_nuevo,
               datetime.now(timezone.utc).isoformat(), 'spec_h_rematch',
               run_id, str(id_oferta)))

    return {
        'isco_nuevo': isco_nuevo,
        'score_nuevo': score_nuevo,
        'decision_metodo_nuevo': decision_metodo_nuevo,
        'esco_label_nuevo': esco_label_nuevo,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    parser.add_argument('--tanda', choices=['piloto', 'verificacion', 'resto'])
    parser.add_argument('--ids')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--umbral-score', type=float, default=UMBRAL_MIN_SCORE)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    if not args.tanda and not args.ids:
        parser.error('requiere --tanda o --ids')

    conn = sqlite3.connect(args.db)
    ensure_tables(conn)

    extra_ids = args.ids.split(',') if args.ids else None
    ids = seleccionar_ids(conn, args.tanda or '', args.limit, extra_ids)
    print(f'[H] Tanda "{args.tanda or "ids"}" → {len(ids):,} ofertas')
    if not ids:
        print('[H] Nada que procesar')
        conn.close(); return

    if args.dry_run:
        print('[H] DRY-RUN (no persiste)')

    # Cargar matcher (usa embeddings enriquecidos ya en producción)
    print('[H] Cargando MatcherV3...')
    from match_ofertas_v3 import MatcherV3
    matcher = MatcherV3(db_conn=conn, verbose=args.verbose)
    print(f'[H] Matcher cargado (version {matcher.VERSION})')

    run_id = f'spec_h_rematch_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    stats = {'actualizada': 0, 'actualizada_dispara_regla': 0,
             'skip_score_bajo': 0, 'skip_no_cambio': 0,
             'skip_regresion_probable': 0, 'skip_locked': 0, 'error': 0}
    t0 = time.time()
    nowiso = lambda: datetime.now(timezone.utc).isoformat()

    for i, oid in enumerate(ids, 1):
        try:
            estado_actual = get_estado_actual(conn, oid)
            if not estado_actual:
                stats['error'] += 1
                continue

            oferta_nlp = get_oferta_nlp(conn, oid)
            if not oferta_nlp:
                stats['error'] += 1
                continue

            t_1 = time.time()
            result = matcher.match(oferta_nlp)
            dt_ms = int((time.time() - t_1) * 1000)

            isco_viejo = estado_actual['isco_code']
            score_viejo = estado_actual['score_semantico']
            decision_viejo = estado_actual['decision_metodo']
            isco_nuevo_pre = str(result.isco_code) if result.isco_code else None
            score_nuevo_pre = float(result.score or 0)
            decision_nuevo_pre = result.metadata.get('decision_metodo', decision_viejo)

            # Política D (mixta) — ver evaluar_cambio() arriba
            resultado = evaluar_cambio(
                score_viejo=score_viejo,
                score_nuevo=score_nuevo_pre,
                decision_metodo_nuevo=decision_nuevo_pre,
                isco_nuevo=isco_nuevo_pre or '',
                isco_viejo=isco_viejo or '',
                umbral_min=args.umbral_score,
            )
            mensaje = ''
            if resultado == 'actualizada_dispara_regla':
                mensaje = f'regla_aplicada={result.metadata.get("regla_aplicada","?")}'
            elif resultado == 'skip_score_bajo':
                mensaje = f'score nuevo {score_nuevo_pre:.3f} < {args.umbral_score}'
            elif resultado == 'skip_no_cambio':
                mensaje = 'mismo ESCO viejo y nuevo'
            elif resultado == 'skip_regresion_probable':
                mensaje = f'score baja de {score_viejo:.3f} a {score_nuevo_pre:.3f} (>tolerancia)'

            # Persistencia
            if resultado in ('actualizada', 'actualizada_dispara_regla') and not args.dry_run:
                # Snapshot ANTES de modificar
                c = conn.cursor()
                c.execute('''INSERT OR IGNORE INTO ofertas_matching_backup_spec_h
                             (id_oferta, isco_code_antes, esco_occupation_label_antes,
                              titulo_esco_code_antes, score_semantico_antes,
                              decision_metodo_antes, estado_validacion_antes,
                              matching_timestamp_antes, backup_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (str(oid), estado_actual['isco_code'],
                           estado_actual['esco_occupation_label'],
                           estado_actual['titulo_esco_code'],
                           estado_actual['score_semantico'],
                           estado_actual['decision_metodo'],
                           estado_actual['estado_validacion'],
                           estado_actual['matching_timestamp'],
                           nowiso()))
                try:
                    persist_matching_result(conn, oid, result, estado_actual, run_id)
                except sqlite3.IntegrityError as e:
                    # Trigger protect_validated_matching si estado='validado' estricto
                    if 'No se puede modificar oferta validada' in str(e):
                        resultado = 'skip_locked'
                        mensaje = 'trigger bloqueó (estado=validado, requiere unlock)'
                    else:
                        raise

            # Stats counting simple
            stats[resultado] = stats.get(resultado, 0) + 1
            # Log progress
            if not args.dry_run:
                c = conn.cursor()
                c.execute('''INSERT OR REPLACE INTO spec_h_rematch_progress
                             (id_oferta, tanda, procesada_at, isco_anterior, isco_nuevo,
                              score_anterior, score_nuevo, decision_metodo_anterior,
                              decision_metodo_nuevo, resultado, tiempo_ms, mensaje)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (str(oid), args.tanda or 'ids', nowiso(),
                           isco_viejo, isco_nuevo_pre, score_viejo, score_nuevo_pre,
                           decision_viejo, decision_nuevo_pre, resultado, dt_ms, mensaje))

        except Exception as e:
            stats['error'] += 1
            if args.verbose:
                print(f'  [H] ERROR en {oid}: {e}')
            continue

        if i % args.batch_size == 0 and not args.dry_run:
            conn.commit()
            el = time.time() - t0
            rate = i / el
            eta = (len(ids) - i) / rate if rate else 0
            print(f'  [{i}/{len(ids)}] {rate:.1f}/s ETA {eta:.0f}s  {stats}')

    if not args.dry_run:
        conn.commit()

    el = time.time() - t0
    print(f'\n[H] Terminado en {el/60:.1f} min  (run_id={run_id})')
    print(f'  Resultado:')
    for k, v in sorted(stats.items()):
        print(f'    {k}: {v}')
    conn.close()


if __name__ == '__main__':
    main()
