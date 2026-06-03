"""Lock para evitar que el poller dispare pipeline mientras un batch local corre.

Uso desde un script de batch:

    from scripts.pipeline_lock import acquire, release
    acquire("canary reanudacion post-spec-u1")
    try:
        ...
    finally:
        release()
"""
import json
import os
from datetime import datetime
from pathlib import Path

LOCK_FILE = Path('/tmp/mol_pipeline_running.lock')


def acquire(reason: str, *, allow_steal_stale: bool = True) -> Path:
    if LOCK_FILE.exists():
        try:
            info = json.loads(LOCK_FILE.read_text())
            pid = info.get('pid')
            if pid and Path(f'/proc/{pid}').exists():
                raise RuntimeError(f"Lock activo: {info}")
            if allow_steal_stale:
                LOCK_FILE.unlink()
        except (json.JSONDecodeError, OSError):
            if allow_steal_stale:
                LOCK_FILE.unlink(missing_ok=True)
            else:
                raise

    LOCK_FILE.write_text(json.dumps({
        'pid': os.getpid(),
        'started_at': datetime.now().isoformat(),
        'reason': reason,
    }, indent=2))
    return LOCK_FILE


def release() -> None:
    LOCK_FILE.unlink(missing_ok=True)


def is_locked() -> bool:
    if not LOCK_FILE.exists():
        return False
    try:
        info = json.loads(LOCK_FILE.read_text())
        pid = info.get('pid')
        if pid and Path(f'/proc/{pid}').exists():
            return True
        LOCK_FILE.unlink()
        return False
    except (json.JSONDecodeError, OSError):
        return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: pipeline_lock.py [status|release]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'status':
        if LOCK_FILE.exists():
            print(LOCK_FILE.read_text())
        else:
            print("No lock")
    elif cmd == 'release':
        release()
        print("Released")
    else:
        print(f"Comando desconocido: {cmd}")
        sys.exit(1)
