#!/usr/bin/env python3
"""
Linear Update Async - Ejecuta actualizaciones en background

Wrapper no-bloqueante para linear_update.py.
Retorna inmediatamente mientras el update se procesa en background.

Uso:
    python scripts/linear_update_async.py MOL-31 --status=done
    python scripts/linear_update_async.py MOL-31 --status=done --comment="Completado"
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_FILE = BASE_DIR / ".linear" / "update_log.txt"
UPDATE_SCRIPT = SCRIPTS_DIR / "linear_update.py"


def log_update(identifier: str, args: list, status: str, message: str = ""):
    """Registra el update en el log"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    args_str = " ".join(args)
    log_entry = f"[{timestamp}] {status} | {identifier} | {args_str}"
    if message:
        log_entry += f" | {message}"
    log_entry += "\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def run_update_background(args: list):
    """Ejecuta linear_update.py en background sin bloquear"""

    cmd = [sys.executable, str(UPDATE_SCRIPT)] + args

    try:
        if sys.platform == "win32":
            # Windows: CREATE_NO_WINDOW para no mostrar consola
            CREATE_NO_WINDOW = 0x08000000
            DETACHED_PROCESS = 0x00000008

            subprocess.Popen(
                cmd,
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
        else:
            # Unix: nohup equivalent
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )

        return True
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        print("Uso: python linear_update_async.py MOL-XX [--status=X] [--comment=X]")
        sys.exit(1)

    # Extraer identifier del primer argumento
    identifier = sys.argv[1].upper()
    args = sys.argv[1:]  # Todos los argumentos incluyendo identifier

    # Log inicio
    log_update(identifier, args[1:], "QUEUED", "Enviado a background")

    # Ejecutar en background
    result = run_update_background(args)

    if result is True:
        print(f"[OK] Update {identifier} enviado a background")
        print(f"  Log: {LOG_FILE}")
    else:
        error = result[1] if isinstance(result, tuple) else "Error desconocido"
        log_update(identifier, args[1:], "ERROR", error)
        print(f"[ERROR] Error enviando update: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
