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

UMBRAL_MIN_SCORE = 0.45       # Si score_nuevo < umbral → skip
UMBRAL_VIEJO_RUIDO = 0.50     # Si score_viejo < esto, era ruido → aceptar cambio
TOLERANCIA_REGRESION = 0.05   # Aceptar si score_nuevo > score_viejo - tolerancia
ZONA_FALLBACK_LO = 0.59       # Banda donde el matcher devuelve 0.6 como fallback
ZONA_FALLBACK_HI = 0.61       # (combined_score = 0.6*1.0 + 0.4*0 = 0.6 exacto)


def evaluar_cambio(score_viejo: float, score_nuevo: float, decision_metodo_nuevo: str,
                   isco_nuevo: str, isco_viejo: str, umbral_min: float) -> str:
    """
    Política E — decide qué hacer con un re-match.

    Política D + filtro fallback 0.6: el matcher devuelve combined_score = 0.6 exacto
    cuando hay skill_score=1.0 (skill forzada por regla RS_xx) sin match de título.
    Eso NO es un match semántico genuino — solo skills forzadas. Lo descartamos
    cuando el viejo ya tenía un score >= 0.55 (probable match real).

    Retorna uno de:
      - 'actualizada_dispara_regla': cambia decision_metodo a regla curada
      - 'skip_score_bajo': score nuevo bajo el umbral mínimo
      - 'skip_no_cambio': mismo ESCO viejo y nuevo
      - 'skip_fallback_06': score nuevo en zona fallback 0.6 sin match real
      - 'skip_regresion_probable': score nuevo cae mucho desde uno alto viejo
      - 'actualizada': cambio aceptado
    """
    sv = float(score_viejo or 0)
    sn = float(score_nuevo or 0)

    # 1. Regla curada siempre gana
    if decision_metodo_nuevo == 'regla_prioridad':
        return 'actualizada_dispara_regla'

    # 2. Score nuevo bajo umbral → no confiable
    if sn < umbral_min:
        return 'skip_score_bajo'

    # 3. Mismo ESCO → no hay cambio
    if isco_nuevo == isco_viejo:
        return 'skip_no_cambio'

    # 4. NUEVO: Filtro fallback 0.6 (Política E)
    #    Si score_nuevo está en zona [0.59, 0.61] Y score_viejo era razonable (>=0.55),
    #    es probable que sea un fallback de skill forzada sin contexto real.
    if ZONA_FALLBACK_LO <= sn <= ZONA_FALLBACK_HI and sv >= 0.55:
        return 'skip_fallback_06'

    # 5. Política D — proteger contra regresiones
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


def persist_matching_result(conn, id_oferta: str, result, estado_actual: dict, run_id: str, uri_to_esco_code: dict = None):
    """Persiste TODOS los campos de matching de ocupación (no toca columnas de skills).

    BUG fix 2026-04-26: la versión anterior solo escribía 9 columnas, dejando
    `regla_aplicada`, `isco_label`, `isco_regla`, `isco_semantico`, `decision_razon`,
    `occupation_match_method`, `esco_occupation_uri`, `dual_coinciden` en valores stale
    de runs previos — provocando inconsistencias del tipo
    "esco_occupation_label = R357 nuevo / regla_aplicada = R240 viejo".

    Respeta el trigger: si estado='validado' estricto, debe haber unlock previo.
    Retorna dict con info de lo actualizado.
    """
    c = conn.cursor()
    meta = result.metadata or {}

    # Campos del MatchResult
    isco_nuevo = str(result.isco_code) if result.isco_code else None
    esco_label_nuevo = result.esco_label or meta.get('esco_label') or ''
    esco_uri_nuevo = result.esco_uri or ''
    titulo_esco_code_nuevo = meta.get('esco_code') or meta.get('titulo_esco_code') or ''
    # Fallback: derivar esco_code desde URI usando metadata global
    if not titulo_esco_code_nuevo and esco_uri_nuevo and uri_to_esco_code:
        titulo_esco_code_nuevo = uri_to_esco_code.get(esco_uri_nuevo, '')
    score_nuevo = float(result.score or 0)
    metodo_nuevo = result.metodo or ''

    # Metadata dual matching (la fuente de las inconsistencias del bug previo)
    decision_metodo_nuevo = meta.get('decision_metodo', estado_actual['decision_metodo'])
    decision_razon_nuevo = meta.get('decision_razon', '')
    isco_regla_nuevo = meta.get('isco_regla')
    isco_semantico_nuevo = meta.get('isco_semantico')
    score_semantico_nuevo = meta.get('score_semantico', score_nuevo)
    regla_aplicada_nuevo = meta.get('regla_aplicada')
    dual_coinciden_nuevo = meta.get('dual_coinciden')
    skills_regla_aplicada_nuevo = meta.get('skills_regla_aplicada')
    dual_coinciden_skills_nuevo = meta.get('dual_coinciden_skills')

    # isco_label en BD = esco_label (mismo patrón que match_ofertas_v3._save_match)
    isco_label_nuevo = esco_label_nuevo

    c.execute('''UPDATE ofertas_esco_matching SET
                     isco_code = ?,
                     isco_label = ?,
                     esco_occupation_label = ?,
                     esco_occupation_uri = ?,
                     titulo_esco_code = ?,
                     occupation_match_score = ?,
                     occupation_match_method = ?,
                     score_semantico = ?,
                     isco_semantico = ?,
                     isco_regla = ?,
                     regla_aplicada = ?,
                     dual_coinciden = ?,
                     decision_metodo = ?,
                     decision_razon = ?,
                     skills_regla_aplicada = ?,
                     dual_coinciden_skills = ?,
                     matching_timestamp = ?,
                     matching_version = ?,
                     run_id = ?
                 WHERE id_oferta = ?''',
              (isco_nuevo, isco_label_nuevo, esco_label_nuevo, esco_uri_nuevo,
               titulo_esco_code_nuevo, score_nuevo, metodo_nuevo,
               score_semantico_nuevo, isco_semantico_nuevo,
               isco_regla_nuevo, regla_aplicada_nuevo, dual_coinciden_nuevo,
               decision_metodo_nuevo, decision_razon_nuevo,
               skills_regla_aplicada_nuevo, dual_coinciden_skills_nuevo,
               datetime.now(timezone.utc).isoformat(), 'spec_h_rematch',
               run_id, str(id_oferta)))

    return {
        'isco_nuevo': isco_nuevo,
        'score_nuevo': score_nuevo,
        'decision_metodo_nuevo': decision_metodo_nuevo,
        'esco_label_nuevo': esco_label_nuevo,
        'regla_aplicada_nuevo': regla_aplicada_nuevo,
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

    # Mapa URI → esco_code (para poblar titulo_esco_code cuando metadata no lo trae)
    print('[H] Cargando mapa URI → esco_code...')
    meta_path = ROOT / 'database/embeddings/esco_occupations_metadata.json'
    uri_to_esco_code = {}
    if meta_path.exists():
        meta_data = json.load(open(meta_path))
        uri_to_esco_code = {m['uri']: m.get('esco_code') for m in meta_data if m.get('esco_code')}
        print(f'[H] Mapa cargado: {len(uri_to_esco_code):,} URIs con esco_code')
    else:
        print('[H] WARN: metadata no encontrada, titulo_esco_code podría quedar vacío')

    run_id = f'spec_h_rematch_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    stats = {'actualizada': 0, 'actualizada_dispara_regla': 0,
             'skip_score_bajo': 0, 'skip_no_cambio': 0,
             'skip_regresion_probable': 0, 'skip_fallback_06': 0,
             'skip_locked': 0, 'error': 0}
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
            elif resultado == 'skip_fallback_06':
                mensaje = f'score nuevo {score_nuevo_pre:.3f} es fallback (zona 0.6)'

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
                    persist_matching_result(conn, oid, result, estado_actual, run_id, uri_to_esco_code)
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
