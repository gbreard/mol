"""Wrapper que adquiere el lock anti-poller y ejecuta run_validated_pipeline con args arbitrarios.

Uso:
    python scripts/run_batch_with_lock.py "<reason>" <pipeline_args...>

Ejemplo Fase 3a (matching solo):
    python scripts/run_batch_with_lock.py "fase 3a matching" --skip-nlp --ids 1,2,3

Ejemplo NLP+matching (canary o tanda):
    python scripts/run_batch_with_lock.py "tanda 1 fase 3b" --ids 1,2,3
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from scripts.pipeline_lock import acquire, release  # noqa: E402


def main():
    if len(sys.argv) < 3:
        print("Uso: run_batch_with_lock.py <reason> <pipeline_args...>", flush=True)
        sys.exit(1)

    reason = sys.argv[1]
    pipeline_args = sys.argv[2:]

    acquire(reason)
    print(f"[BATCH] Lock adquirido (PID {os.getpid()})", flush=True)
    print(f"[BATCH] Reason: {reason}", flush=True)

    try:
        env = os.environ.copy()
        if 'OLLAMA_HOST' not in env:
            env['OLLAMA_HOST'] = '172.17.0.1'

        cmd = [sys.executable, '-u', 'scripts/run_validated_pipeline.py'] + pipeline_args
        print(f"[BATCH] Ejecutando: {' '.join(cmd[:5])}{'...' if len(cmd)>5 else ''}", flush=True)

        result = subprocess.run(cmd, cwd=str(PROJECT), env=env)
        print(f"[BATCH] Exit code: {result.returncode}", flush=True)
        sys.exit(result.returncode)
    finally:
        release()
        print(f"[BATCH] Lock liberado", flush=True)


if __name__ == '__main__':
    main()
