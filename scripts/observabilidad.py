#!/usr/bin/env python3
"""
Observabilidad del Eje 1 — acta de corrida + alertas (SPEC S1C-F0.3).

Acta de corrida (tabla local pipeline_run_actas): fuente de verdad a nivel-corrida.
Se crea al inicio del pipeline y se cierra al final con resultado.

Mecanismo de `incompleta` (decisión consciente, ver spec §4.1):
  Una corrida en curso y una muerta se ven igual con finished_at IS NULL.
  El barrido `barrer_actas_huerfanas()` (invocado al INICIO de cada corrida,
  antes de crear la nueva acta) las distingue por PID vivo + host + timeout.

Paso 3 (alertas) agrega `emitir_alerta()` sobre este mismo módulo.
"""

import os
import json
import socket
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "bumeran_scraping.db"

# Mismo límite que el subprocess timeout del poller (pipeline_command_poller.py)
RUN_TIMEOUT_SECONDS = 8 * 3600


def _conn():
    return sqlite3.connect(str(DB_PATH))


def _now():
    return datetime.now().isoformat()


def _host():
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _pid_vivo(pid, host):
    """True si `pid` corresponde a un proceso vivo EN ESTE host.

    El PID solo es comparable dentro del mismo host: si el acta es de otro host
    no podemos verificar el proceso, así que cae al respaldo por timeout.
    """
    if not pid or host != _host():
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # existe pero no es nuestro → vivo
    except (OSError, ValueError, TypeError):
        return False
    return True


def barrer_actas_huerfanas(con=None):
    """Marca como `incompleta` las actas abiertas (finished_at IS NULL) que están muertas.

    Regla (ver spec §4.1): un acta abierta es muerta si, en su mismo host,
      (1) su PID ya no vive, o
      (2) su started_at supera RUN_TIMEOUT_SECONDS (respaldo cuando el PID
          no es confiable: reinicio que reusa PIDs, u otro host).
    Una corrida viva (PID vivo dentro del timeout) NUNCA se marca incompleta.

    Devuelve la lista de acta_id barridas. No emite alertas en este paso (Paso 2);
    el Paso 3 engancha `emitir_alerta('corrida_incompleta', ...)` por cada barrida.
    """
    own = con is None
    if own:
        con = _conn()
    barridas = []
    ahora = datetime.now()
    rows = con.execute(
        "SELECT acta_id, started_at, pid, host FROM pipeline_run_actas "
        "WHERE finished_at IS NULL"
    ).fetchall()
    for acta_id, started_at, pid, host in rows:
        muerta = not _pid_vivo(pid, host)
        if not muerta:
            # PID vivo: respaldo por timeout
            try:
                edad = (ahora - datetime.fromisoformat(started_at)).total_seconds()
                if edad > RUN_TIMEOUT_SECONDS:
                    muerta = True
            except (ValueError, TypeError):
                pass
        if muerta:
            con.execute(
                "UPDATE pipeline_run_actas SET finished_at = ?, resultado = 'incompleta' "
                "WHERE acta_id = ?",
                (_now(), acta_id),
            )
            barridas.append(acta_id)
    con.commit()
    if own:
        con.close()
    return barridas


def crear_acta(invocador="terminal", args="", alcance_entrada=None):
    """Crea el acta de la corrida en curso (resultado NULL hasta cerrar)."""
    acta_id = f"acta_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    con = _conn()
    con.execute(
        "INSERT INTO pipeline_run_actas "
        "(acta_id, started_at, invocador, args, alcance_entrada, pid, host) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (acta_id, _now(), invocador, args, alcance_entrada, os.getpid(), _host()),
    )
    con.commit()
    con.close()
    return acta_id


def cerrar_acta(acta_id, resultado, alcance_procesado=None,
                matching_run_id=None, fallos=None):
    """Cierra el acta con resultado ∈ {ok, fallida, incompleta} y la lista de fallos."""
    if not acta_id:
        return
    con = _conn()
    con.execute(
        "UPDATE pipeline_run_actas SET finished_at = ?, resultado = ?, "
        "alcance_procesado = ?, matching_run_id = ?, fallos = ? WHERE acta_id = ?",
        (_now(), resultado, alcance_procesado, matching_run_id,
         json.dumps(fallos or [], ensure_ascii=False), acta_id),
    )
    con.commit()
    con.close()


def invocador_actual():
    """Detecta cómo se invocó la corrida: el poller setea MOL_INVOCADOR=poller."""
    return os.environ.get("MOL_INVOCADOR", "terminal")
