"""Wrapper que adquiere el lock anti-poller y ejecuta el backfill CT.

Uso:
    python scripts/run_backfill_with_lock.py [--limit N]
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from scripts.pipeline_lock import acquire, release  # noqa: E402


def main():
    extra_args = sys.argv[1:]
    acquire("backfill CT A1.3 — 3318 ofertas restantes")
    print(f"[BACKFILL] Lock adquirido (PID {os.getpid()})")
    try:
        cmd = [sys.executable, 'scripts/backfill_ct_descripciones.py'] + extra_args
        print(f"[BACKFILL] Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(PROJECT))
        sys.exit(result.returncode)
    finally:
        release()
        print(f"[BACKFILL] Lock liberado")


if __name__ == '__main__':
    main()
