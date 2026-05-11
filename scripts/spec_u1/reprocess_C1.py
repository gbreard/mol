#!/usr/bin/env python3
"""
SPEC U-1 v3.1 C1 — Re-rematch de las 8.217 ofertas (lenguaje URI ESCO puro).

Set: ofertas con matching_version='spec_h_rematch' AND estado_validacion='en_revision'
     EXCLUYENDO 4 ofertas humanas/ambiguas.

Estrategia:
  - Para cada oferta: cargar NLP, instanciar MatcherV3 (post-fix sub-fase C, JSON v2,
    embeddings restaurados), match_and_persist().
  - Log estructurado en lenguaje URI ESCO:
      header: timestamp, commit, total
      por oferta: id, esco_uri_pre, esco_uri_post, cambio_uri, esco_label_pre,
                  esco_label_post, match_method_post, score_post, decision_metodo_post,
                  isco_pre/post (atributo informativo, no criterio)
      progress cada 100: idx, pct, rate, ETA, errores, error_rate
      summary: totales + distribución métodos + cambio_uri counts
  - Aborta si tasa de errores acumulados > 5% (después de 100 ofertas).

Uso:
  nohup python3 scripts/spec_u1/reprocess_C1.py > /tmp/c1_stdout.log 2>&1 &
"""
import sys
import json
import sqlite3
import subprocess
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path('/mnt/d/OEDE/Webscrapping')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'database'))

DB_PATH = ROOT / 'database/bumeran_scraping.db'
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_PATH = ROOT / f'logs/spec_u1_C1_re_rematch_{TS}.log'
SUMMARY_PATH = ROOT / f'logs/spec_u1_C1_re_rematch_summary_{TS}.json'

EXCLUIDAS = ('1118115497', '1118115501', '1118115516', '1118099854')

ERROR_RATE_ABORT = 0.05  # 5%
ERROR_CHECK_AFTER = 100
THROUGHPUT_MIN_ABORT = 0.4  # ofertas/s — si baja de esto en sostenido, abortar
THROUGHPUT_CHECK_AFTER = 600  # solo evaluar throughput sostenido después de 600 ofertas


def get_commit_hash():
    try:
        return subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD']).decode().strip()
    except Exception:
        return 'unknown'


def log_line(fh, payload):
    fh.write(json.dumps(payload, default=str, ensure_ascii=False) + '\n')
    fh.flush()


def main():
    print(f"=== SPEC U-1 v3.1 C1 — RE-REMATCH ===")
    print(f"Log: {LOG_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, 'w', encoding='utf-8')

    commit = get_commit_hash()
    started_at = datetime.now()

    # 1. Cargar set
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    placeholders = ','.join(['?'] * len(EXCLUIDAS))
    rows = con.execute(f"""
        SELECT id_oferta, esco_occupation_uri, esco_occupation_label, isco_code,
               occupation_match_score, decision_metodo, occupation_match_method
        FROM ofertas_esco_matching
        WHERE matching_version = 'spec_h_rematch'
          AND estado_validacion = 'en_revision'
          AND id_oferta NOT IN ({placeholders})
        ORDER BY id_oferta
    """, EXCLUIDAS).fetchall()

    total = len(rows)
    pre_state = {r['id_oferta']: dict(r) for r in rows}

    header = {
        'event': 'header',
        'timestamp': started_at.isoformat(),
        'commit': commit,
        'total_a_procesar': total,
        'set': "matching_version='spec_h_rematch' AND estado_validacion='en_revision' AND id_oferta NOT IN excluidas",
        'excluidas': list(EXCLUIDAS),
        'matcher_version': '3.5.2',
        'json_v2_version': '2.0.0',
        'language': 'URI ESCO puro (ISCO se persiste como atributo derivado)',
    }
    log_line(fh, header)
    print(f"Header: total={total}  commit={commit}")

    if total != 8217:
        msg = f"Conteo total inesperado: {total}, esperado 8217. ABORTAR."
        log_line(fh, {'event': 'abort', 'reason': msg})
        print(msg)
        fh.close()
        sys.exit(1)

    con.close()
    write_con = sqlite3.connect(str(DB_PATH))
    from match_ofertas_v3 import MatcherV3
    matcher = MatcherV3(db_conn=write_con, verbose=False)
    log_line(fh, {
        'event': 'matcher_loaded',
        'occ_embeddings_shape': list(matcher.occ_embeddings.shape) if matcher.occ_embeddings is not None else None,
        'code_to_occupation': len(matcher.code_to_occupation),
        'isco_to_canonical_occupation': len(matcher.isco_to_canonical_occupation),
        'sinonimos_version': matcher.sinonimos_arg.get('version') if matcher.sinonimos_arg else None,
    })

    # 2. Loop principal
    procesadas = 0
    errores = 0
    cambio_uri = 0
    sin_cambio_uri = 0
    quedaron_sin_uri = 0
    method_dist = {}
    estado_dist_post = {}

    nlp_query = """
        SELECT n.*, o.titulo, o.descripcion, o.empresa
        FROM ofertas_nlp n
        JOIN ofertas o ON o.id_oferta = n.id_oferta
        WHERE n.id_oferta = ?
    """
    nlp_query_cols = None  # se rellena en la primera ejecución

    for idx, row in enumerate(rows, 1):
        id_oferta = row['id_oferta']
        uri_pre = row['esco_occupation_uri'] or ''
        label_pre = row['esco_occupation_label'] or ''
        isco_pre = row['isco_code']
        score_pre = row['occupation_match_score']
        decision_pre = row['decision_metodo']
        method_pre = row['occupation_match_method']

        try:
            cur = write_con.execute(nlp_query, (id_oferta,))
            if nlp_query_cols is None:
                nlp_query_cols = [d[0] for d in cur.description]
            nlp_row = cur.fetchone()
            if nlp_row is None:
                log_line(fh, {'event': 'offer', 'idx': idx, 'id_oferta': id_oferta,
                              'status': 'skipped_no_nlp', 'uri_pre': uri_pre})
                errores += 1
                continue

            oferta_nlp = dict(zip(nlp_query_cols, nlp_row))
            ok = matcher.match_and_persist(id_oferta, oferta_nlp, _allow_no_run=True)

            post_row = write_con.execute("""
                SELECT esco_occupation_uri, esco_occupation_label, isco_code,
                       occupation_match_method, occupation_match_score,
                       decision_metodo, estado_validacion
                FROM ofertas_esco_matching WHERE id_oferta = ?
            """, (id_oferta,)).fetchone()

            if post_row is None:
                log_line(fh, {'event': 'offer', 'idx': idx, 'id_oferta': id_oferta,
                              'status': 'error_no_post_state'})
                errores += 1
                continue

            uri_post = post_row[0] or ''
            label_post = post_row[1] or ''
            isco_post = post_row[2]
            method_post = post_row[3] or ''
            score_post = post_row[4]
            decision_post = post_row[5] or ''
            estado_post = post_row[6] or 'NULL'

            cambio_uri_flag = uri_post != uri_pre
            if uri_post:
                if cambio_uri_flag:
                    cambio_uri += 1
                else:
                    sin_cambio_uri += 1
            else:
                quedaron_sin_uri += 1

            method_dist[method_post] = method_dist.get(method_post, 0) + 1
            estado_dist_post[estado_post] = estado_dist_post.get(estado_post, 0) + 1

            log_line(fh, {
                'event': 'offer',
                'idx': idx,
                'id_oferta': id_oferta,
                # Campos en lenguaje URI ESCO (autoritativos)
                'esco_uri_pre': uri_pre,
                'esco_uri_post': uri_post,
                'cambio_uri': cambio_uri_flag,
                'esco_label_pre': label_pre,
                'esco_label_post': label_post,
                'match_method_post': method_post,
                'score_post': score_post,
                'decision_metodo_post': decision_post,
                'estado_post': estado_post,
                # Atributos derivados (informativos, no criterio)
                '_isco_pre': isco_pre,
                '_isco_post': isco_post,
                '_match_method_pre': method_pre,
                'status': 'ok',
            })
            procesadas += 1

        except Exception as e:
            errores += 1
            log_line(fh, {'event': 'offer', 'idx': idx, 'id_oferta': id_oferta,
                          'status': 'error',
                          'error': f'{type(e).__name__}: {e}',
                          'traceback': traceback.format_exc()})

        # Progress cada 100
        if idx % 100 == 0 or idx == total:
            elapsed = (datetime.now() - started_at).total_seconds()
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = total - idx
            eta_seconds = remaining / rate if rate > 0 else 0
            eta = (datetime.now() + timedelta(seconds=eta_seconds)).strftime('%H:%M:%S') if rate > 0 else 'N/A'
            err_rate = errores / idx
            progress = {
                'event': 'progress',
                'idx': idx,
                'total': total,
                'pct': round(idx / total * 100, 2),
                'elapsed_seconds': round(elapsed, 1),
                'rate_per_sec': round(rate, 2),
                'eta_at': eta,
                'errors': errores,
                'error_rate': round(err_rate, 4),
                'cambio_uri': cambio_uri,
                'sin_cambio_uri': sin_cambio_uri,
                'quedaron_sin_uri': quedaron_sin_uri,
            }
            log_line(fh, progress)
            print(f"[{idx}/{total}] {round(idx/total*100,1)}%  rate={rate:.2f}/s  ETA={eta}  errores={errores} ({err_rate*100:.2f}%)  cambio_uri={cambio_uri} sin_cambio={sin_cambio_uri}")

            # Abort triggers
            if idx >= ERROR_CHECK_AFTER and err_rate > ERROR_RATE_ABORT:
                msg = f"Tasa de errores {err_rate*100:.2f}% supera umbral {ERROR_RATE_ABORT*100:.0f}%. ABORTAR."
                log_line(fh, {'event': 'abort', 'reason': msg, 'idx': idx, 'errors': errores})
                print(msg)
                break
            if idx >= THROUGHPUT_CHECK_AFTER and rate < THROUGHPUT_MIN_ABORT:
                msg = f"Throughput {rate:.2f}/s baja del mínimo {THROUGHPUT_MIN_ABORT}/s. ABORTAR."
                log_line(fh, {'event': 'abort', 'reason': msg, 'idx': idx, 'rate': rate})
                print(msg)
                break

    write_con.commit()

    # 3. Summary
    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

    final_uri_vacia = write_con.execute("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE (esco_occupation_uri = '' OR esco_occupation_uri IS NULL)
          AND matching_version = 'spec_h_rematch'
    """).fetchone()[0]

    summary = {
        'event': 'summary',
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'duration_seconds': round(duration, 1),
        'duration_human': f"{int(duration//3600)}h{int((duration%3600)//60)}m",
        'total_input': total,
        'procesadas': procesadas,
        'errores': errores,
        'error_rate': round(errores / total, 4) if total > 0 else 0,
        'cambio_uri': cambio_uri,
        'sin_cambio_uri': sin_cambio_uri,
        'quedaron_sin_uri_post': quedaron_sin_uri,
        'method_dist_post': method_dist,
        'estado_dist_post': estado_dist_post,
        'final_uri_vacia_set': final_uri_vacia,
        'language': 'URI ESCO puro',
    }
    log_line(fh, summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print()
    print("=" * 60)
    print("RESUMEN FINAL — C1 RE-REMATCH")
    print("=" * 60)
    print(f"Duración:          {summary['duration_human']}  ({duration:.0f}s)")
    print(f"Procesadas:        {procesadas}/{total}")
    print(f"Errores:           {errores} ({summary['error_rate']*100:.2f}%)")
    print(f"Cambio URI ESCO:   {cambio_uri}")
    print(f"Sin cambio URI:    {sin_cambio_uri}")
    print(f"Quedaron sin URI:  {quedaron_sin_uri}")
    print(f"URI vacía en set spec_h_rematch post: {final_uri_vacia}")
    print(f"Method dist top 5: {sorted(method_dist.items(), key=lambda x: -x[1])[:5]}")
    print(f"Estado dist post:  {estado_dist_post}")
    print()
    print(f"Log:     {LOG_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    fh.close()
    write_con.close()


if __name__ == '__main__':
    main()
