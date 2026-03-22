#!/usr/bin/env python3
"""
VPS Command Poller — Bloque H2b

Corre en el VPS como servicio. Cada 60 segundos consulta Supabase
por comandos pendientes y los ejecuta.

Uso:
    python3 scripts/vps_command_poller.py           # Corre en loop
    python3 scripts/vps_command_poller.py --once     # Ejecuta una vez y sale

Instalar como servicio systemd:
    sudo cp scripts/vps_command_poller.service /etc/systemd/system/
    sudo systemctl enable vps_command_poller
    sudo systemctl start vps_command_poller
"""

import json
import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path

# Config
POLL_INTERVAL = 60  # segundos
MOL_DIR = Path('/opt/mol')
SCRIPTS_DIR = MOL_DIR / 'scripts'
LOG_DIR = MOL_DIR / 'logs'

# Supabase config — leer de archivo o env
def get_supabase_client():
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: pip install supabase")
        sys.exit(1)

    config_file = MOL_DIR / 'config' / 'supabase_config.json'
    if config_file.exists():
        config = json.loads(config_file.read_text())
        return create_client(config['url'], config['service_role_key'])

    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if url and key:
        return create_client(url, key)

    print("ERROR: No se encontró configuración de Supabase")
    sys.exit(1)


# Mapeo de comandos a scripts
COMMAND_MAP = {
    'lanzar_portal': lambda params: run_scraping_portal(params.get('portal')),
    'lanzar_todos': lambda params: run_scraping_todos(),
    'sync_vps_local': lambda params: run_export(),
    'pausar_portal': lambda params: log_only(f"Pausa de {params.get('portal')} no implementada aún"),
}


def run_shell(cmd, timeout=3600):
    """Ejecuta comando shell y retorna (exit_code, output)"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(MOL_DIR)
        )
        output = result.stdout + result.stderr
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, f"Timeout después de {timeout}s"
    except Exception as e:
        return 1, str(e)


def run_scraping_portal(portal):
    """Lanza scraping de un portal específico"""
    if not portal:
        return 1, "Falta parámetro portal", {}

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f'cmd_{portal}_{timestamp}.log'

    # El scraping de cada portal está en run_scheduler.py
    cmd = f'python3 run_scheduler.py --portal {portal} 2>&1 | tee {log_file}'
    code, output = run_shell(cmd, timeout=7200)  # 2h max

    # Contar ofertas del output
    ofertas = 0
    for line in output.split('\n'):
        if 'nuevas:' in line.lower() or 'insertadas:' in line.lower():
            try:
                ofertas = int(''.join(filter(str.isdigit, line.split(':')[-1])))
            except:
                pass

    return code, output[-2000:], {'ofertas': ofertas, 'log_file': str(log_file)}


def run_scraping_todos():
    """Lanza scraping de todos los portales"""
    script = SCRIPTS_DIR / 'scraping' / 'run_scraping_vps.sh'
    if not script.exists():
        return 1, f"Script no encontrado: {script}", {}

    code, output = run_shell(f'bash {script}', timeout=21600)  # 6h max
    return code, output[-2000:], {'log_file': 'ver logs en /opt/mol/logs/'}


def run_export():
    """Exporta ofertas nuevas para que local las baje"""
    cmd = 'python3 scripts/export_nuevas.py'
    code, output = run_shell(cmd, timeout=300)
    return code, output[-2000:], {}


def log_only(msg):
    """Para comandos no implementados"""
    return 0, msg, {}


def process_command(client, cmd):
    """Procesa un comando pendiente"""
    cmd_id = cmd['id']
    comando = cmd['comando']
    params = cmd.get('params', {})

    print(f"[{datetime.now().isoformat()}] Ejecutando: {comando} {json.dumps(params)}")

    # Marcar como ejecutando
    client.table('scraping_commands').update({
        'estado': 'ejecutando',
        'started_at': datetime.now().isoformat(),
    }).eq('id', cmd_id).execute()

    # Ejecutar
    handler = COMMAND_MAP.get(comando)
    if not handler:
        client.table('scraping_commands').update({
            'estado': 'error',
            'error_mensaje': f'Comando no soportado: {comando}',
            'completed_at': datetime.now().isoformat(),
        }).eq('id', cmd_id).execute()
        return

    try:
        code, output, resultado = handler(params)

        client.table('scraping_commands').update({
            'estado': 'completado' if code == 0 else 'error',
            'log': output,
            'resultado': resultado,
            'error_mensaje': output[-500:] if code != 0 else None,
            'completed_at': datetime.now().isoformat(),
        }).eq('id', cmd_id).execute()

        status = 'OK' if code == 0 else 'ERROR'
        print(f"[{datetime.now().isoformat()}] {comando}: {status}")

    except Exception as e:
        client.table('scraping_commands').update({
            'estado': 'error',
            'error_mensaje': str(e)[:500],
            'completed_at': datetime.now().isoformat(),
        }).eq('id', cmd_id).execute()
        print(f"[{datetime.now().isoformat()}] {comando}: EXCEPTION {e}")


def poll_once(client):
    """Busca y ejecuta comandos pendientes"""
    result = client.table('scraping_commands') \
        .select('*') \
        .eq('estado', 'pendiente') \
        .order('created_at') \
        .limit(1) \
        .execute()

    if not result.data:
        return False

    process_command(client, result.data[0])
    return True


def main():
    once = '--once' in sys.argv
    client = get_supabase_client()

    print(f"[{datetime.now().isoformat()}] VPS Command Poller iniciado")
    print(f"  Intervalo: {POLL_INTERVAL}s | Modo: {'once' if once else 'loop'}")

    if once:
        poll_once(client)
        return

    while True:
        try:
            had_work = poll_once(client)
            if had_work:
                continue  # Si hubo trabajo, buscar más inmediatamente
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nPoller detenido")
            break
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error en poll: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
