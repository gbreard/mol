"""Wrapper que adquiere el lock anti-poller y ejecuta run_validated_pipeline.

Uso:
    python scripts/run_canary_with_lock.py <ids_file_o_csv> [reason]

Donde ids_file_o_csv es una ruta a un .txt con IDs separados por coma
o directamente la lista CSV.
"""
import os
import sys
import subprocess
from pathlib import Path

# Asegurar import de scripts.pipeline_lock
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from scripts.pipeline_lock import acquire, release  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Uso: run_canary_with_lock.py <ids_csv_o_archivo> [reason]")
        sys.exit(1)

    arg = sys.argv[1]
    reason = sys.argv[2] if len(sys.argv) > 2 else "canary reanudacion post-spec-u1"

    if os.path.isfile(arg):
        ids_csv = Path(arg).read_text().strip()
    else:
        ids_csv = arg

    n_ids = len(ids_csv.split(','))
    print(f"[CANARY] IDs: {n_ids}")
    print(f"[CANARY] Reason: {reason}")

    acquire(reason)
    print(f"[CANARY] Lock adquirido (PID {os.getpid()})")

    try:
        env = os.environ.copy()
        if 'OLLAMA_HOST' not in env:
            env['OLLAMA_HOST'] = '172.17.0.1'

        # -u: unbuffered stdout/stderr (visible en tiempo real, lección de A1.3)
        cmd = [sys.executable, '-u', 'scripts/run_validated_pipeline.py', '--ids', ids_csv]
        print(f"[CANARY] Ejecutando: {' '.join(cmd[:4])} --ids <{n_ids} ids>", flush=True)

        result = subprocess.run(cmd, cwd=str(PROJECT), env=env)
        print(f"[CANARY] Exit code: {result.returncode}")
        sys.exit(result.returncode)
    finally:
        release()
        print(f"[CANARY] Lock liberado")


if __name__ == '__main__':
    main()
