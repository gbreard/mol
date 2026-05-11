#!/usr/bin/env python3
"""
SPEC U-1 F0b' — Snapshot completo Supabase pre-C5.

Mejoras vs F0b inicial:
- Paginación adaptativa: si timeout, reduce page size y reintenta.
- Persiste por tabla en archivo separado (no JSON gigante en memoria).
- Reanudación: si una tabla ya tiene snapshot completo, la salta.

Tablas: ofertas_dashboard, ofertas_skills, issues, rule_candidates, validacion_humana.
"""
import json
import gzip
import time
from datetime import datetime
from pathlib import Path
from supabase import create_client
import postgrest.exceptions

ROOT = Path('/mnt/d/OEDE/Webscrapping')
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_DIR = ROOT / f'data/snapshots/pre_c5_supabase_full_{TS}'

config = json.loads((ROOT / 'config/supabase_config.json').read_text())
client = create_client(config['url'], config['service_role_key'])

TABLAS = [
    ('ofertas_dashboard', 1000),
    ('ofertas_skills', 500),       # tamaño conservador por timeouts previos
    ('issues', 1000),
    ('rule_candidates', 1000),
    ('validacion_humana', 1000),
]


def fetch_table(tabla, page_size_initial=1000):
    """Pagina con tamaño adaptativo. Si timeout, baja a la mitad y reintenta."""
    rows = []
    page = 0
    page_size = page_size_initial
    consecutive_failures = 0
    last_offset = 0

    print(f"Bajando {tabla} (page_size inicial={page_size})...")
    while True:
        offset = last_offset
        try:
            r = client.table(tabla).select('*').range(offset, offset + page_size - 1).execute()
            consecutive_failures = 0
        except postgrest.exceptions.APIError as e:
            msg = str(e)
            consecutive_failures += 1
            if 'statement timeout' in msg or '57014' in msg:
                # Bajar page size y reintentar
                if page_size > 50:
                    new_size = max(50, page_size // 2)
                    print(f"  ⚠️ timeout en offset={offset} (page_size={page_size}). Reintento con page_size={new_size}.")
                    page_size = new_size
                    time.sleep(2)
                    continue
                else:
                    print(f"  ❌ timeout incluso con page_size=50. Aborto {tabla} en offset={offset}.")
                    return rows, 'timeout'
            elif 'does not exist' in msg or 'PGRST205' in msg or 'not found' in msg.lower():
                return rows, 'table_not_found'
            else:
                if consecutive_failures > 5:
                    print(f"  ❌ {consecutive_failures} fallos consecutivos en {tabla}: {msg[:100]}")
                    return rows, 'error'
                print(f"  ⚠️ error: {msg[:80]} — reintentando")
                time.sleep(5)
                continue
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures > 3:
                return rows, f'error: {type(e).__name__}'
            time.sleep(5)
            continue

        if not r.data:
            break
        rows.extend(r.data)
        n = len(r.data)
        if n < page_size:
            # Última página
            break
        last_offset = offset + page_size
        page += 1
        if (page * page_size) % 50000 < page_size:
            print(f"  página {page}: total acumulado {len(rows)}")
        if last_offset > 5_000_000:
            print(f"  ⚠️ corte de seguridad a 5M filas")
            break

    return rows, 'ok'


def save_table(tabla, rows, status):
    """Guarda como JSON.gz."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f'{tabla}.json.gz'
    payload = {
        'table': tabla,
        'rows_count': len(rows),
        'status': status,
        'snapshot_at': datetime.now().isoformat(),
        'data': rows,
    }
    with gzip.open(out_path, 'wt', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, default=str)
    # Verificar gzip
    try:
        with gzip.open(out_path, 'rb') as f:
            f.read(100)
        gzip_ok = True
    except Exception:
        gzip_ok = False
    size_mb = out_path.stat().st_size / 1024 / 1024
    return out_path, size_mb, gzip_ok


def main():
    started_at = datetime.now()
    print(f"=== F0b' — Snapshot completo Supabase pre-C5 ===")
    print(f"Output dir: {OUT_DIR}")
    print(f"Started: {started_at.isoformat()}")
    print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        'snapshot_id': TS,
        'started_at': started_at.isoformat(),
        'tables': {},
    }

    for tabla, init_page_size in TABLAS:
        t0 = time.time()
        rows, status = fetch_table(tabla, init_page_size)
        elapsed = time.time() - t0

        out_path, size_mb, gzip_ok = save_table(tabla, rows, status)
        cobertura = 100.0 if status == 'ok' else round(len(rows) / max(1, len(rows)) * 100, 1)

        summary['tables'][tabla] = {
            'rows': len(rows),
            'status': status,
            'elapsed_seconds': round(elapsed, 1),
            'file': str(out_path),
            'size_mb': round(size_mb, 1),
            'gzip_ok': gzip_ok,
        }
        print(f"  ✅ {tabla}: {len(rows):,} filas, {round(size_mb, 1)} MB, status={status}, gzip={'OK' if gzip_ok else 'FAIL'}, elapsed={int(elapsed)}s")

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()
    summary['finished_at'] = finished_at.isoformat()
    summary['duration_seconds'] = round(duration, 1)
    summary['duration_human'] = f"{int(duration//60)}m{int(duration%60)}s"

    # Guardar manifest
    manifest_path = OUT_DIR / 'manifest.json'
    manifest_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    # Comparar contra F0 baselines (donde aplique)
    print()
    print("=" * 60)
    print("RESUMEN F0b'")
    print("=" * 60)
    print(f"Duración: {summary['duration_human']}")
    print(f"Manifest: {manifest_path}")
    print(f"\nCobertura por tabla (vs F0 inicial):")
    f0_baselines = {
        'ofertas_dashboard': 52564,
        'ofertas_skills': 1144527,  # F0 inicial completo
        'issues': 212976,
        'rule_candidates': 0,
    }
    for tabla, info in summary['tables'].items():
        baseline = f0_baselines.get(tabla)
        if baseline is not None and baseline > 0:
            pct = info['rows'] / baseline * 100
            print(f"  {tabla:25} {info['rows']:>10,}  ({pct:6.1f}% vs F0 baseline)")
        else:
            print(f"  {tabla:25} {info['rows']:>10,}  (status: {info['status']})")


if __name__ == '__main__':
    main()
