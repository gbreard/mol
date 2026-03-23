#!/usr/bin/env python3
"""
Pipeline Command Poller — Gateway local para la fábrica de procesamiento.
Mismo patrón que el scraping command poller del VPS.

Lee comandos pendientes de Supabase (pipeline_commands) y los ejecuta localmente.
Diseñado para correr como cron cada 1 minuto o como servicio systemd.

Uso:
    python scripts/pipeline_command_poller.py          # Ejecuta un comando pendiente
    python scripts/pipeline_command_poller.py --daemon  # Loop continuo (cada 60s)
    python scripts/pipeline_command_poller.py --dry-run # Muestra qué haría sin ejecutar
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DB_DIR = PROJECT_DIR / "database"

# Add project to path
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(DB_DIR))


def get_supabase_client():
    """Crea cliente Supabase con service_role_key."""
    config_path = PROJECT_DIR / "config" / "supabase_config.json"
    if not config_path.exists():
        print("[POLLER] ERROR: config/supabase_config.json no encontrado")
        return None

    config = json.loads(config_path.read_text())
    try:
        from supabase import create_client
        return create_client(config['url'], config['service_role_key'])
    except Exception as e:
        print(f"[POLLER] ERROR: No se pudo conectar a Supabase: {e}")
        return None


# Command → script mapping
COMMAND_MAP = {
    'run_pipeline': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--limit', str(p.get('limit', 100))] if p.get('limit') else ['--ids', p.get('ids', '')],
    },
    'run_nlp': {
        'script': 'database/process_nlp_from_db_v11.py',
        'build_args': lambda p: ['--limit', str(p.get('limit', 100))] if p.get('limit') else ['--ids', p.get('ids', '')],
    },
    'run_matching': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-nlp'] + (['--ids', p.get('ids', '')] if p.get('ids') else ['--limit', str(p.get('limit', 100))]),
    },
    'reprocess_errors': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--only-pending', '--limit', str(p.get('limit', 200))],
    },
    'revalidate_nlp': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-matching'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'revalidate_matching': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-nlp'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'reapply_rules': {
        'script': 'scripts/reapply_rules_to_validated.py',
        'build_args': lambda p: [],
    },
    'export_excel': {
        'script': 'scripts/exports/export_validation_excel.py',
        'build_args': lambda p: ['--etapa', 'completo'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'sync_supabase': {
        'script': 'scripts/exports/sync_to_supabase.py',
        'build_args': lambda p: [],
    },
    'sync_supabase_full': {
        'script': 'scripts/exports/sync_to_supabase.py',
        'build_args': lambda p: ['--full'],
    },
    'generate_training': {
        'script': 'scripts/exports/generate_training_pairs.py',
        'build_args': lambda p: [],
    },
}


def fetch_pending_command(client):
    """Lee el comando pendiente más antiguo."""
    result = client.table('pipeline_commands') \
        .select('*') \
        .eq('estado', 'pendiente') \
        .order('created_at') \
        .limit(1) \
        .execute()

    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def update_command(client, cmd_id, **kwargs):
    """Actualiza un comando en Supabase."""
    try:
        client.table('pipeline_commands').update(kwargs).eq('id', cmd_id).execute()
    except Exception as e:
        print(f"[POLLER] WARN: No se pudo actualizar comando {cmd_id}: {e}")


def execute_command(client, cmd, dry_run=False):
    """Ejecuta un comando del pipeline."""
    cmd_id = cmd['id']
    comando = cmd['comando']
    params = cmd.get('params', {}) or {}

    print(f"\n[POLLER] === Ejecutando: {comando} ===")
    print(f"[POLLER] ID: {cmd_id}")
    print(f"[POLLER] Params: {json.dumps(params)}")
    print(f"[POLLER] Creado por: {cmd.get('creado_por', '?')}")

    if comando not in COMMAND_MAP:
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Comando desconocido: {comando}",
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] ERROR: Comando desconocido: {comando}")
        return False

    mapping = COMMAND_MAP[comando]
    script_path = PROJECT_DIR / mapping['script']

    if not script_path.exists():
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Script no encontrado: {mapping['script']}",
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] ERROR: Script no encontrado: {script_path}")
        return False

    args = mapping['build_args'](params)
    full_cmd = [sys.executable, str(script_path)] + [str(a) for a in args if a]

    print(f"[POLLER] Comando: {' '.join(full_cmd)}")

    if dry_run:
        print(f"[POLLER] DRY RUN — no se ejecuta")
        return True

    # Mark as executing
    update_command(client, cmd_id,
        estado='ejecutando',
        started_at=datetime.utcnow().isoformat()
    )

    # Execute
    start_time = time.time()
    try:
        # Set OLLAMA_HOST for WSL if needed
        env = os.environ.copy()
        if 'OLLAMA_HOST' not in env:
            env['OLLAMA_HOST'] = '172.17.0.1'

        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=28800,  # 8 hours max
            cwd=str(PROJECT_DIR),
            env=env,
        )

        duration = round(time.time() - start_time, 1)
        log_output = result.stdout[-5000:] if result.stdout else ''  # Last 5K chars
        if result.stderr:
            log_output += f"\n--- STDERR ---\n{result.stderr[-2000:]}"

        if result.returncode == 0:
            update_command(client, cmd_id,
                estado='completado',
                log=log_output,
                resultado={
                    'exit_code': 0,
                    'duracion_seg': duration,
                },
                completed_at=datetime.utcnow().isoformat()
            )
            print(f"[POLLER] OK — {duration}s")
            return True
        else:
            update_command(client, cmd_id,
                estado='error',
                log=log_output,
                error_message=f"Exit code {result.returncode}",
                resultado={
                    'exit_code': result.returncode,
                    'duracion_seg': duration,
                },
                completed_at=datetime.utcnow().isoformat()
            )
            print(f"[POLLER] ERROR — exit code {result.returncode} — {duration}s")
            return False

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 1)
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Timeout ({duration}s)",
            resultado={'duracion_seg': duration},
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] TIMEOUT — {duration}s")
        return False

    except Exception as e:
        update_command(client, cmd_id,
            estado='error',
            error_message=str(e),
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] EXCEPTION: {e}")
        return False


def poll_once(dry_run=False):
    """Ejecuta un ciclo de polling."""
    client = get_supabase_client()
    if not client:
        return False

    cmd = fetch_pending_command(client)
    if not cmd:
        return False

    return execute_command(client, cmd, dry_run=dry_run)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Pipeline Command Poller')
    parser.add_argument('--daemon', action='store_true', help='Loop continuo cada 60s')
    parser.add_argument('--dry-run', action='store_true', help='No ejecutar, solo mostrar')
    parser.add_argument('--interval', type=int, default=60, help='Intervalo en segundos (default: 60)')
    args = parser.parse_args()

    print(f"[POLLER] Pipeline Command Poller v1.0")
    print(f"[POLLER] Proyecto: {PROJECT_DIR}")
    print(f"[POLLER] Modo: {'daemon' if args.daemon else 'single'}")

    if args.daemon:
        print(f"[POLLER] Intervalo: {args.interval}s")
        while True:
            try:
                poll_once(dry_run=args.dry_run)
            except Exception as e:
                print(f"[POLLER] ERROR en ciclo: {e}")
            time.sleep(args.interval)
    else:
        executed = poll_once(dry_run=args.dry_run)
        if not executed:
            print("[POLLER] Sin comandos pendientes")


if __name__ == '__main__':
    main()
