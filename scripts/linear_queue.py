#!/usr/bin/env python3
"""
Linear Queue - Sistema de cola para updates no bloqueantes

Permite encolar updates que se procesan en background.
Soporta reintentos automáticos si falla.

Uso:
    # Agregar a la cola (instantáneo)
    python scripts/linear_queue.py add MOL-31 --status=done --comment="Listo"

    # Procesar cola (ejecutar en background o cron)
    python scripts/linear_queue.py process

    # Ver estado de la cola
    python scripts/linear_queue.py status

    # Limpiar cola procesada
    python scripts/linear_queue.py clean
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Importar el módulo de update
sys.path.insert(0, str(Path(__file__).parent))

# Configuración
BASE_DIR = Path(__file__).parent.parent
QUEUE_FILE = BASE_DIR / ".linear" / "pending_updates.json"
LOG_FILE = BASE_DIR / ".linear" / "update_log.txt"
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos


def load_queue() -> list:
    """Carga la cola de updates pendientes"""
    if not QUEUE_FILE.exists():
        return []

    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_queue(queue: list):
    """Guarda la cola de updates"""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def log_update(identifier: str, action: str, status: str, message: str = ""):
    """Registra en el log"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {status} | {identifier} | {action}"
    if message:
        log_entry += f" | {message}"
    log_entry += "\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def add_to_queue(identifier: str, args: list):
    """Agrega un update a la cola"""
    queue = load_queue()

    update = {
        "id": f"{identifier}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "identifier": identifier,
        "args": args,
        "status": "pending",
        "retries": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "error": None
    }

    queue.append(update)
    save_queue(queue)

    log_update(identifier, " ".join(args), "QUEUED")
    print(f"✓ Agregado a cola: {identifier}")
    print(f"  Cola: {len(queue)} updates pendientes")

    return update["id"]


def process_single_update(update: dict) -> bool:
    """Procesa un update individual. Retorna True si exitoso."""
    identifier = update["identifier"]
    args = update["args"]

    try:
        # Importar y ejecutar el update directamente
        import linear_update

        # Construir argumentos para el parser
        sys.argv = ["linear_update.py", identifier] + args

        # Capturar stdout/stderr
        from io import StringIO
        import contextlib

        stdout_capture = StringIO()
        stderr_capture = StringIO()

        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            try:
                linear_update.main()
                return True
            except SystemExit as e:
                if e.code == 0:
                    return True
                return False

    except Exception as e:
        update["error"] = str(e)
        return False


def process_queue():
    """Procesa todos los updates pendientes en la cola"""
    queue = load_queue()

    if not queue:
        print("Cola vacía - nada que procesar")
        return

    pending = [u for u in queue if u["status"] == "pending"]
    print(f"Procesando {len(pending)} updates pendientes...")

    for update in queue:
        if update["status"] != "pending":
            continue

        identifier = update["identifier"]
        args_str = " ".join(update["args"])

        print(f"\n→ {identifier}: {args_str}")

        success = process_single_update(update)

        if success:
            update["status"] = "completed"
            update["updated_at"] = datetime.now().isoformat()
            log_update(identifier, args_str, "SUCCESS")
            print(f"  ✓ Completado")
        else:
            update["retries"] += 1
            update["updated_at"] = datetime.now().isoformat()

            if update["retries"] >= MAX_RETRIES:
                update["status"] = "failed"
                log_update(identifier, args_str, "FAILED", f"Max retries ({MAX_RETRIES})")
                print(f"  ✗ Falló después de {MAX_RETRIES} intentos")
            else:
                log_update(identifier, args_str, "RETRY", f"Intento {update['retries']}/{MAX_RETRIES}")
                print(f"  ⟳ Reintento {update['retries']}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY)

        save_queue(queue)

    # Resumen
    completed = len([u for u in queue if u["status"] == "completed"])
    failed = len([u for u in queue if u["status"] == "failed"])
    pending = len([u for u in queue if u["status"] == "pending"])

    print(f"\n=== Resumen ===")
    print(f"Completados: {completed}")
    print(f"Fallidos: {failed}")
    print(f"Pendientes: {pending}")


def show_status():
    """Muestra el estado de la cola"""
    queue = load_queue()

    if not queue:
        print("Cola vacía")
        return

    pending = [u for u in queue if u["status"] == "pending"]
    completed = [u for u in queue if u["status"] == "completed"]
    failed = [u for u in queue if u["status"] == "failed"]

    print(f"=== Estado de la Cola ===")
    print(f"Total: {len(queue)}")
    print(f"  Pendientes: {len(pending)}")
    print(f"  Completados: {len(completed)}")
    print(f"  Fallidos: {len(failed)}")

    if pending:
        print(f"\nPendientes:")
        for u in pending:
            print(f"  - {u['identifier']}: {' '.join(u['args'])}")

    if failed:
        print(f"\nFallidos:")
        for u in failed:
            print(f"  - {u['identifier']}: {u.get('error', 'Error desconocido')}")


def clean_queue():
    """Limpia updates completados de la cola"""
    queue = load_queue()
    original_len = len(queue)

    # Mantener solo pendientes y fallidos
    queue = [u for u in queue if u["status"] not in ("completed",)]
    save_queue(queue)

    removed = original_len - len(queue)
    print(f"Limpiados {removed} updates completados")
    print(f"Cola actual: {len(queue)} items")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) < 3:
            print("Uso: python linear_queue.py add MOL-XX [--status=X] [--comment=X]")
            sys.exit(1)

        identifier = sys.argv[2].upper()
        args = sys.argv[3:]
        add_to_queue(identifier, args)

    elif command == "process":
        process_queue()

    elif command == "status":
        show_status()

    elif command == "clean":
        clean_queue()

    else:
        print(f"Comando desconocido: {command}")
        print("Comandos: add, process, status, clean")
        sys.exit(1)


if __name__ == "__main__":
    main()
