#!/usr/bin/env python3
"""
SPEC U-1 Pre-Tarea 4 — Cargar esco_occupation_ancestors desde API ESCO.

Para cada URI en esco_occupations, llama:
  https://ec.europa.eu/esco/api/resource/occupation?uri=<URI>&language=es&selectedVersion=v1.2.0
y extrae _embedded.ancestors. Persiste en esco_occupation_ancestors.

Latencia API observada: ~1.8 s/request (rate natural ~0.5 req/s).
Total esperado: 3.046 ofertas × 1.8s = ~91 min.

Schema destino:
  occupation_uri (PK)
  ancestor_uri (PK)
  ancestor_level INTEGER (1=propia ocupación, 2=padre directo, ..., n=ancestro más alto)
  ancestor_title TEXT
  ancestor_type TEXT (Occupation | IscoGroup)
  ancestor_isco_code TEXT (si aplica, ej "C2654")
  loaded_at TEXT (ISO timestamp)

Uso:
  nohup python3 -u scripts/spec_u1/load_esco_ancestors.py > /tmp/esco_anc_stdout.log 2>&1 &
"""
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import re
import traceback
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path('/mnt/d/OEDE/Webscrapping')
DB_PATH = str(ROOT / 'database/bumeran_scraping.db')
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_PATH = ROOT / f'logs/load_esco_ancestors_{TS}.log'
SUMMARY_PATH = ROOT / f'logs/load_esco_ancestors_summary_{TS}.json'

API_BASE = 'https://ec.europa.eu/esco/api/resource/occupation'
VERSION = 'v1.2.0'
LANG = 'es'
TIMEOUT = 15  # seg
MAX_RETRIES = 3
COMMIT_BATCH = 100

ISCO_PATTERN = re.compile(r'/isco/(C\d+)')


def fetch_with_retry(uri):
    """GET con retry exponencial. Devuelve dict {ok, data, latency, error}."""
    params = urllib.parse.urlencode({'uri': uri, 'language': LANG, 'selectedVersion': VERSION})
    api_url = f'{API_BASE}?{params}'
    req = urllib.request.Request(api_url, headers={
        'Accept': 'application/json',
        'User-Agent': 'MOL-SPEC-U1/1.0 (Pre-Tarea-4 ancestors loader)',
    })
    last_err = None
    for attempt in range(MAX_RETRIES):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read()
                latency = time.time() - t0
                data = json.loads(body)
                return {'ok': True, 'latency': latency, 'data': data}
        except urllib.error.HTTPError as e:
            last_err = f'HTTP {e.code}: {e.reason}'
            if e.code in (429, 502, 503, 504):
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                continue
            return {'ok': False, 'latency': time.time() - t0, 'error': last_err}
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
            last_err = f'{type(e).__name__}: {e}'
            wait = 2 ** (attempt + 1)
            time.sleep(wait)
            continue
        except Exception as e:
            return {'ok': False, 'latency': time.time() - t0, 'error': f'{type(e).__name__}: {e}'}
    return {'ok': False, 'latency': time.time() - t0, 'error': f'max retries: {last_err}'}


def extract_ancestors(data, occupation_uri):
    """Extrae filas (occupation_uri, ancestor_uri, level, title, type, isco_code) del response."""
    ancestors = data.get('_embedded', {}).get('ancestors', [])
    rows = []
    for level, a in enumerate(ancestors, start=1):
        if not isinstance(a, dict):
            continue
        # Self URI
        self_uri = ''
        if '_links' in a and 'self' in a['_links']:
            self_link = a['_links']['self']
            if isinstance(self_link, dict):
                self_uri = self_link.get('uri', '')
        if not self_uri:
            continue
        title = a.get('title', '')
        # Determinar tipo desde la URI
        if '/isco/' in self_uri:
            ancestor_type = 'IscoGroup'
            m = ISCO_PATTERN.search(self_uri)
            isco_code = m.group(1) if m else None
        elif '/occupation/' in self_uri:
            ancestor_type = 'Occupation'
            isco_code = None
        else:
            ancestor_type = 'Other'
            isco_code = None
        rows.append({
            'occupation_uri': occupation_uri,
            'ancestor_uri': self_uri,
            'ancestor_level': level,
            'ancestor_title': title,
            'ancestor_type': ancestor_type,
            'ancestor_isco_code': isco_code,
        })
    return rows


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, 'w', encoding='utf-8')

    def logj(d):
        fh.write(json.dumps(d, default=str, ensure_ascii=False) + '\n')
        fh.flush()

    started_at = datetime.now()
    print(f"=== SPEC U-1 Pre-Tarea 4 — load_esco_ancestors ===")
    print(f"Started: {started_at.isoformat()}")
    print(f"Log: {LOG_PATH}")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    # Cargar URIs a procesar (3.046 esperado, status released)
    rows = con.execute("""
        SELECT occupation_uri, isco_code, preferred_label_es
        FROM esco_occupations
        WHERE occupation_uri IS NOT NULL AND status = 'released'
        ORDER BY occupation_uri
    """).fetchall()
    total = len(rows)
    print(f"URIs a procesar: {total}")

    logj({'event': 'header', 'timestamp': started_at.isoformat(),
          'total': total, 'api_base': API_BASE, 'version': VERSION, 'lang': LANG,
          'commit_batch': COMMIT_BATCH, 'max_retries': MAX_RETRIES, 'timeout': TIMEOUT})

    # Filtrar URIs ya cargadas (para reanudación)
    already = set(r[0] for r in con.execute("SELECT DISTINCT occupation_uri FROM esco_occupation_ancestors").fetchall())
    pending = [r for r in rows if r['occupation_uri'] not in already]
    if already:
        print(f"Ya cargadas previamente: {len(already)}")
        print(f"Pendientes: {len(pending)}")
    logj({'event': 'preload', 'already_loaded': len(already), 'pending': len(pending)})

    # Loop principal
    procesadas = 0
    errores = 0
    total_filas_insertadas = 0
    total_ancestros_extraidos = 0
    distribucion_niveles = {}
    pending_inserts = []

    write_con = sqlite3.connect(DB_PATH)
    cur = write_con.cursor()
    now_iso = datetime.now().isoformat()

    for idx, row in enumerate(pending, 1):
        uri = row['occupation_uri']
        result = fetch_with_retry(uri)

        if not result['ok']:
            errores += 1
            logj({'event': 'offer', 'idx': idx, 'uri': uri,
                  'status': 'error', 'error': result.get('error'),
                  'latency': result['latency']})
            # Si error rate alto, abortar
            if idx >= 50 and errores / idx > 0.10:  # > 10%
                msg = f"Error rate {errores/idx*100:.1f}% > 10%. ABORTAR."
                print(msg)
                logj({'event': 'abort', 'reason': msg, 'idx': idx, 'errores': errores})
                break
            continue

        ancestors_rows = extract_ancestors(result['data'], uri)
        n_anc = len(ancestors_rows)
        total_ancestros_extraidos += n_anc

        for ar in ancestors_rows:
            distribucion_niveles[ar['ancestor_level']] = distribucion_niveles.get(ar['ancestor_level'], 0) + 1
            pending_inserts.append((
                ar['occupation_uri'], ar['ancestor_uri'], ar['ancestor_level'],
                ar['ancestor_title'], ar['ancestor_type'], ar['ancestor_isco_code'],
                now_iso,
            ))

        procesadas += 1

        logj({'event': 'offer', 'idx': idx, 'uri': uri, 'isco': row['isco_code'],
              'label': row['preferred_label_es'],
              'n_ancestros': n_anc, 'latency': round(result['latency'], 3),
              'status': 'ok'})

        # Commit cada COMMIT_BATCH
        if procesadas % COMMIT_BATCH == 0:
            cur.executemany("""
                INSERT OR IGNORE INTO esco_occupation_ancestors
                (occupation_uri, ancestor_uri, ancestor_level, ancestor_title,
                 ancestor_type, ancestor_isco_code, loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, pending_inserts)
            total_filas_insertadas += cur.rowcount
            write_con.commit()
            pending_inserts = []

            elapsed = (datetime.now() - started_at).total_seconds()
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = len(pending) - idx
            eta_sec = remaining / rate if rate > 0 else 0
            eta = (datetime.now() + timedelta(seconds=eta_sec)).strftime('%H:%M:%S')
            err_rate = errores / idx
            progress = {
                'event': 'progress',
                'idx': idx, 'total': len(pending),
                'pct': round(idx / len(pending) * 100, 2),
                'elapsed_s': round(elapsed, 1),
                'rate_per_sec': round(rate, 2),
                'eta_at': eta,
                'errores': errores, 'error_rate': round(err_rate, 4),
                'filas_insertadas': total_filas_insertadas,
                'ancestros_extraidos': total_ancestros_extraidos,
            }
            logj(progress)
            print(f"[{idx}/{len(pending)}] {progress['pct']}%  rate={rate:.2f}/s  ETA={eta}  errores={errores} ({err_rate*100:.1f}%)  filas={total_filas_insertadas}")

    # Commit final
    if pending_inserts:
        cur.executemany("""
            INSERT OR IGNORE INTO esco_occupation_ancestors
            (occupation_uri, ancestor_uri, ancestor_level, ancestor_title,
             ancestor_type, ancestor_isco_code, loaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pending_inserts)
        total_filas_insertadas += cur.rowcount
        write_con.commit()

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

    # Conteos finales independientes desde BD
    n_total_filas = write_con.execute("SELECT COUNT(*) FROM esco_occupation_ancestors").fetchone()[0]
    n_ocup_cubiertas = write_con.execute("SELECT COUNT(DISTINCT occupation_uri) FROM esco_occupation_ancestors").fetchone()[0]
    n_ancestros_unicos = write_con.execute("SELECT COUNT(DISTINCT ancestor_uri) FROM esco_occupation_ancestors").fetchone()[0]

    summary = {
        'event': 'summary',
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'duration_seconds': round(duration, 1),
        'duration_human': f"{int(duration//3600)}h{int((duration%3600)//60)}m",
        'total_uris_input': total,
        'pending_at_start': len(pending),
        'procesadas_ok': procesadas,
        'errores': errores,
        'error_rate': round(errores / max(1, len(pending)), 4),
        'filas_insertadas_esta_corrida': total_filas_insertadas,
        'ancestros_extraidos_esta_corrida': total_ancestros_extraidos,
        'distribucion_niveles_esta_corrida': distribucion_niveles,
        'bd_total_filas': n_total_filas,
        'bd_ocupaciones_cubiertas': n_ocup_cubiertas,
        'bd_ancestros_unicos': n_ancestros_unicos,
        'bd_cobertura_pct': round(100 * n_ocup_cubiertas / total, 2),
    }
    logj(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print()
    print("=" * 60)
    print("RESUMEN — load_esco_ancestors")
    print("=" * 60)
    for k in ['duration_human', 'procesadas_ok', 'errores', 'error_rate',
              'bd_total_filas', 'bd_ocupaciones_cubiertas', 'bd_ancestros_unicos',
              'bd_cobertura_pct']:
        print(f"  {k:35} {summary[k]}")
    print(f"\n  Distribución niveles: {summary['distribucion_niveles_esta_corrida']}")

    fh.close()
    write_con.close()
    con.close()


if __name__ == '__main__':
    main()
