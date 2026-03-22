#!/usr/bin/env python3
"""
Sincroniza métricas de procesamiento desde SQLite a Supabase.
Lee pipeline_runs, validation_errors, ofertas_esco_matching.

Uso:
    python3 scripts/sync_processing_metrics.py
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'bumeran_scraping.db'


def get_supabase_client():
    config = json.loads((BASE_DIR / 'config' / 'supabase_config.json').read_text())
    from supabase import create_client
    return create_client(config['url'], config['service_role_key'])


def get_metrics(db_path):
    conn = sqlite3.connect(str(db_path))

    # Pipeline runs por día
    runs = conn.execute('''
        SELECT DATE(timestamp) as fecha, run_id, ofertas_count,
               metricas_errores, metricas_precision, reglas_negocio_count,
               delta_reglas
        FROM pipeline_runs
        ORDER BY timestamp
    ''').fetchall()

    runs_by_day = defaultdict(list)
    for fecha, run_id, ofertas, errores, precision, reglas, delta in runs:
        if fecha:
            runs_by_day[fecha].append({
                'run_id': run_id, 'ofertas': ofertas or 0,
                'errores': errores or 0, 'precision': precision or 0,
                'reglas': reglas or 0, 'delta': delta or 0,
            })

    # Matching stats
    matching_stats = {}
    rows = conn.execute('''
        SELECT decision_metodo, COUNT(*) FROM ofertas_esco_matching GROUP BY decision_metodo
    ''').fetchall()
    for metodo, cnt in rows:
        matching_stats[metodo or 'sin_metodo'] = cnt

    dual = conn.execute('''
        SELECT dual_coinciden, COUNT(*) FROM ofertas_esco_matching GROUP BY dual_coinciden
    ''').fetchall()
    dual_stats = {str(k): v for k, v in dual}

    score = conn.execute('SELECT AVG(score_semantico) FROM ofertas_esco_matching WHERE score_semantico IS NOT NULL').fetchone()
    score_prom = round(score[0], 3) if score[0] else 0

    # NLP counts
    nlp_total = conn.execute('SELECT COUNT(*) FROM ofertas_nlp').fetchone()[0]
    total_ofertas = conn.execute('SELECT COUNT(*) FROM ofertas').fetchone()[0]

    # Validation errors by type
    errors_by_type = conn.execute('''
        SELECT error_tipo, COUNT(*) as total, SUM(resuelto) as resueltos,
               MAX(severidad) as sev, MAX(detectado_timestamp) as ultimo
        FROM validation_errors
        GROUP BY error_tipo
    ''').fetchall()

    conn.close()

    # Build daily metrics
    daily = []
    for fecha, day_runs in sorted(runs_by_day.items()):
        last_run = day_runs[-1]
        total_ofertas_run = sum(r['ofertas'] for r in day_runs)
        total_errores_run = sum(r['errores'] for r in day_runs)

        daily.append({
            'fecha': fecha,
            'nlp_procesadas': nlp_total,
            'nlp_pendientes': total_ofertas - nlp_total,
            'nlp_version': 'v11.4',
            'matching_total': matching_stats.get('regla_prioridad', 0) + matching_stats.get('semantico_default', 0),
            'matching_por_regla': matching_stats.get('regla_prioridad', 0),
            'matching_por_semantico': matching_stats.get('semantico_default', 0),
            'matching_dual_coinciden': int(dual_stats.get('1', 0)),
            'matching_dual_difieren': int(dual_stats.get('0', 0)),
            'matching_score_promedio': score_prom,
            'validacion_ok': nlp_total,  # simplificado
            'validacion_warnings': 0,
            'validacion_errores': total_errores_run,
            'errores_resueltos': 0,
            'errores_pendientes': total_errores_run,
            'run_id': last_run['run_id'],
            'ofertas_en_run': total_ofertas_run,
            'precision_run': last_run['precision'],
            'reglas_negocio_count': last_run['reglas'],
            'reglas_nuevas': last_run['delta'],
        })

    # Errors by type for separate table
    errors = []
    for tipo, total, resueltos, sev, ultimo in errors_by_type:
        resueltos = resueltos or 0
        errors.append({
            'error_tipo': tipo,
            'total': total,
            'resueltos': resueltos,
            'pendientes': total - resueltos,
            'severidad_predominante': sev,
            'ultimo_detectado': ultimo[:10] if ultimo else None,
        })

    return daily, errors


def sync_to_supabase(daily, errors):
    client = get_supabase_client()

    # Metrics timeline
    if daily:
        client.table('processing_metrics').delete().neq('id', 0).execute()
        for i in range(0, len(daily), 500):
            client.table('processing_metrics').insert(daily[i:i+500]).execute()
        print(f"  processing_metrics: {len(daily)} registros")

    # Errors by type
    if errors:
        client.table('processing_errors_by_type').delete().neq('error_tipo', '').execute()
        client.table('processing_errors_by_type').insert(errors).execute()
        print(f"  processing_errors_by_type: {len(errors)} tipos")


def main():
    print("=== Sync Processing Metrics ===")
    daily, errors = get_metrics(DB_PATH)
    print(f"  Días con corridas: {len(daily)}")
    print(f"  Tipos de error: {len(errors)}")

    if daily or errors:
        sync_to_supabase(daily, errors)

    print("=== Completado ===")


if __name__ == '__main__':
    main()
