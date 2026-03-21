#!/usr/bin/env python3
"""
Sincronización de ofertas desde VPS a BD local.

Flujo:
  1. Conecta al VPS por SSH
  2. Ejecuta export_nuevas.py en el VPS (dump incremental)
  3. Transfiere el archivo SQL
  4. Importa en BD local (INSERT OR IGNORE)
  5. Ejecuta detección de bajas y republicaciones

Uso:
    python scripts/sync_from_vps.py              # Sync incremental
    python scripts/sync_from_vps.py --full       # Sync completo
    python scripts/sync_from_vps.py --skip-post  # Sin bajas/republicaciones
    python scripts/sync_from_vps.py --import-only archivo.sql  # Solo importar SQL local

Requisitos:
    - SSH key configurada para root@VPS (sin password)
"""

import subprocess
import sqlite3
import sys
import os
import json
import argparse
import tempfile
from datetime import datetime
from pathlib import Path

# Agregar raíz del proyecto al path para imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Config
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'bumeran_scraping.db'
SYNC_LOG = BASE_DIR / 'config' / 'vps_sync_log.json'
IMPORT_DIR = BASE_DIR / 'data' / 'vps_imports'

# VPS
VPS_HOST = 'root@187.124.150.28'
VPS_MOL_DIR = '/opt/mol'
VPS_EXPORT_SCRIPT = f'{VPS_MOL_DIR}/scripts/export_nuevas.py'

# Timeout SSH en segundos
SSH_TIMEOUT = 300


def log(msg):
    """Print con timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_ssh(cmd, timeout=SSH_TIMEOUT):
    """Ejecuta comando en VPS via SSH"""
    full_cmd = f'ssh -o ConnectTimeout=10 {VPS_HOST} "{cmd}"'
    result = subprocess.run(
        full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        log(f"ERROR SSH: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def scp_from_vps(remote_path, local_path):
    """Descarga archivo del VPS"""
    cmd = f'scp -o ConnectTimeout=10 {VPS_HOST}:{remote_path} {local_path}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=SSH_TIMEOUT)
    if result.returncode != 0:
        log(f"ERROR SCP: {result.stderr.strip()}")
        return False
    return True


def export_from_vps(full=False):
    """Ejecuta export en VPS y descarga el archivo"""
    
    log("Conectando al VPS...")
    
    # Verificar conexión
    hostname = run_ssh("hostname")
    if not hostname:
        log("ERROR: No se puede conectar al VPS")
        return None
    log(f"Conectado a {hostname}")
    
    # Ejecutar export
    flag = "--full" if full else ""
    log(f"Ejecutando export {'completo' if full else 'incremental'} en VPS...")
    
    output = run_ssh(f"cd {VPS_MOL_DIR} && python3 {VPS_EXPORT_SCRIPT} {flag}")
    if output is None:
        log("ERROR: Falló el export en VPS")
        return None
    
    print(output)
    
    # Encontrar el archivo exportado
    if "No hay ofertas nuevas" in output:
        log("No hay ofertas nuevas en el VPS.")
        return None
    
    # Buscar la línea con el path del archivo
    export_path = None
    for line in output.split('\n'):
        if 'Exportado:' in line:
            export_path = line.split('Exportado:')[1].strip()
            break
    
    if not export_path:
        log("ERROR: No se encontró el archivo exportado")
        return None
    
    # Descargar
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    local_file = IMPORT_DIR / Path(export_path).name
    
    log(f"Descargando {Path(export_path).name}...")
    if not scp_from_vps(export_path, str(local_file)):
        log("ERROR: Falló la descarga")
        return None
    
    log(f"Descargado: {local_file} ({local_file.stat().st_size / 1024:.1f} KB)")
    return str(local_file)


def import_sql(sql_file):
    """Importa archivo SQL en BD local"""
    
    sql_path = Path(sql_file)
    if not sql_path.exists():
        log(f"ERROR: Archivo no encontrado: {sql_file}")
        return False
    
    log(f"Importando {sql_path.name} en BD local...")
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # Contar ofertas antes
    cur.execute("SELECT COUNT(*) FROM ofertas")
    count_before = cur.fetchone()[0]
    
    # Ejecutar SQL
    sql_content = sql_path.read_text(encoding='utf-8')
    try:
        cur.executescript(sql_content)
        conn.commit()
    except sqlite3.Error as e:
        log(f"ERROR SQL: {e}")
        conn.rollback()
        conn.close()
        return False
    
    # Contar ofertas después
    cur.execute("SELECT COUNT(*) FROM ofertas")
    count_after = cur.fetchone()[0]
    
    nuevas = count_after - count_before
    ignoradas = 0
    
    # Contar INSERTs en el SQL para saber cuántas se ignoraron
    insert_count = sql_content.count('INSERT OR IGNORE')
    ignoradas = insert_count - nuevas
    
    conn.close()
    
    log(f"Importación completada:")
    log(f"  Ofertas en SQL: {insert_count}")
    log(f"  Nuevas insertadas: {nuevas}")
    log(f"  Ya existían (ignoradas): {ignoradas}")
    log(f"  Total en BD: {count_after}")
    
    # Guardar log de sync
    save_sync_log(insert_count, nuevas, ignoradas, count_after)
    
    return True


def run_post_import():
    """Ejecuta detección de bajas y republicaciones en local"""
    
    log("Ejecutando detección de bajas...")
    try:
        from database.detectar_bajas_integrado import DetectorBajasIntegrado
        detector = DetectorBajasIntegrado(DB_PATH)
        detector.connect()
        result = detector.ejecutar()
        if result:
            log(f"  Bajas detectadas: {result.get('nuevas_bajas', 0)}")
            log(f"  Activas confirmadas: {result.get('activas_confirmadas', 0)}")
        detector.close()
    except Exception as e:
        log(f"  Error en detección de bajas: {e}")
    
    log("Ejecutando detección de republicaciones...")
    try:
        from database.detectar_republicaciones import DetectorRepublicaciones
        detector = DetectorRepublicaciones(DB_PATH)
        detector.connect()
        result = detector.ejecutar()
        if result:
            log(f"  Grupos republicados: {result.get('grupos_detectados', 0)}")
        detector.close()
    except Exception as e:
        log(f"  Error en detección de republicaciones: {e}")


def save_sync_log(total_sql, nuevas, ignoradas, total_bd):
    """Guarda log de sincronización"""
    SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if SYNC_LOG.exists():
        data = json.loads(SYNC_LOG.read_text())
    
    data['last_sync'] = datetime.now().isoformat()
    data['last_sync_stats'] = {
        'ofertas_en_sql': total_sql,
        'nuevas_insertadas': nuevas,
        'ignoradas': ignoradas,
        'total_bd': total_bd
    }
    data['history'] = data.get('history', [])
    data['history'].append({
        'timestamp': datetime.now().isoformat(),
        'nuevas': nuevas,
        'total_bd': total_bd
    })
    data['history'] = data['history'][-100:]
    
    SYNC_LOG.write_text(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Sync ofertas desde VPS')
    parser.add_argument('--full', action='store_true', 
                       help='Sync completo (todas las ofertas del VPS)')
    parser.add_argument('--skip-post', action='store_true',
                       help='No ejecutar bajas/republicaciones después del import')
    parser.add_argument('--import-only', type=str, metavar='ARCHIVO.sql',
                       help='Solo importar un archivo SQL local (no conecta al VPS)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("MOL - Sync desde VPS")
    print("=" * 60)
    
    if args.import_only:
        # Solo importar archivo local
        sql_file = args.import_only
    else:
        # Export desde VPS + descarga
        sql_file = export_from_vps(full=args.full)
        if not sql_file:
            return
    
    # Importar en BD local
    success = import_sql(sql_file)
    if not success:
        log("ERROR: Falló la importación")
        sys.exit(1)
    
    # Post-import
    if not args.skip_post:
        run_post_import()
    
    print("=" * 60)
    log("Sync completado")
    print("=" * 60)


if __name__ == '__main__':
    main()
