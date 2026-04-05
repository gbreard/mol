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
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-matching', '--limit', str(p.get('limit', 100))] if p.get('limit') else ['--skip-matching', '--ids', p.get('ids', '')],
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
    'recluster_preview': {
        'script': 'scripts/generate_skill_equivalences.py',
        'build_args': lambda p: ['--partial', '--preview'] + (['--threshold', str(p['threshold'])] if p.get('threshold') else []),
    },
    'recluster_apply': {
        'script': 'scripts/generate_skill_equivalences.py',
        'build_args': lambda p: ['--partial'] + (['--threshold', str(p['threshold'])] if p.get('threshold') else []),
    },
    'scrape_indeed': {
        'script': 'scripts/scraping/run_indeed_local.py',
        'build_args': lambda p: (
            ['--delay', '4', '--detail-delay', '4']
            + (['--force-chunk', str(p['chunk'])] if p.get('chunk') is not None else [])
            + (['--all-keywords'] if p.get('all_keywords') else [])
        ),
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
            # M-08c: Intentar parsear JSON estructurado de la última línea
            resultado = {'exit_code': 0, 'duracion_seg': duration}
            try:
                stdout_lines = (result.stdout or '').strip().split('\n')
                if stdout_lines:
                    last_line = stdout_lines[-1].strip()
                    parsed = json.loads(last_line)
                    if isinstance(parsed, dict) and 'tipo' in parsed:
                        resultado.update(parsed)
                        resultado['duracion_seg'] = duration
            except (json.JSONDecodeError, IndexError):
                pass

            update_command(client, cmd_id,
                estado='completado',
                log=log_output,
                resultado=resultado,
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


def sync_local_status(client):
    """Sube el estado real de SQLite a Supabase para que la Fábrica lo muestre."""
    db_path = PROJECT_DIR / "database" / "bumeran_scraping.db"
    sync_log_path = PROJECT_DIR / "config" / "supabase_sync_log.json"

    if not db_path.exists():
        return

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))

        total = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
        con_nlp = conn.execute("SELECT COUNT(*) FROM ofertas_nlp").fetchone()[0]

        try:
            aprobados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'aprobado'").fetchone()[0]
            bloqueados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'bloqueado'").fetchone()[0]
        except Exception:
            aprobados = con_nlp
            bloqueados = 0

        try:
            con_matching = conn.execute("SELECT COUNT(*) FROM ofertas_esco_matching").fetchone()[0]
        except Exception:
            con_matching = 0

        try:
            validadas = conn.execute(
                "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion IN ('validado','validado_claude','validado_humano')"
            ).fetchone()[0]
        except Exception:
            validadas = 0

        try:
            errores = conn.execute("SELECT COUNT(*) FROM validation_errors WHERE resuelto = 0").fetchone()[0]
        except Exception:
            errores = 0

        conn.close()

        # Sync log
        try:
            sync_log = json.loads(sync_log_path.read_text()) if sync_log_path.exists() else {}
            en_supabase = sync_log.get("ofertas_synced", sync_log.get("total_synced", 0))
            ultimo_sync = sync_log.get("last_sync_timestamp", sync_log.get("ultimo_sync"))
        except Exception:
            en_supabase = 0
            ultimo_sync = None

        gate_total = aprobados + bloqueados
        gate_pct = round(aprobados / gate_total * 100, 1) if gate_total > 0 else 100

        client.table('pipeline_local_status').upsert({
            'id': 'current',
            'timestamp': datetime.utcnow().isoformat(),
            'total_ofertas': total,
            'nlp_procesadas': con_nlp,
            'nlp_pendientes': total - con_nlp,
            'nlp_aprobados': aprobados,
            'nlp_bloqueados': bloqueados,
            'nlp_gate_aprobado_pct': gate_pct,
            'matching_con': con_matching,
            'matching_sin': max(aprobados - con_matching, 0),
            'validadas': validadas,
            'errores_pendientes': errores,
            'en_supabase': en_supabase,
            'pendientes_sync': max(validadas - en_supabase, 0),
            'ultimo_sync': ultimo_sync,
        }).execute()

    except Exception as e:
        print(f"[POLLER] WARN: No se pudo sync status local: {e}")


def poll_once(dry_run=False):
    """Ejecuta un ciclo de polling."""
    client = get_supabase_client()
    if not client:
        return False

    # Siempre sincronizar status local
    sync_local_status(client)

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
