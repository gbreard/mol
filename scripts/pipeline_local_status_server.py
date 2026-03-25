#!/usr/bin/env python3
"""
Pipeline Local Status Server — HTTP endpoint que lee SQLite y devuelve estado real.
Corre en localhost:8099. La Fábrica (Vercel) lo consulta via API proxy.

Uso:
    python scripts/pipeline_local_status_server.py          # Puerto 8099
    python scripts/pipeline_local_status_server.py --port 8100
"""

import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
SUPABASE_SYNC_LOG = Path(__file__).parent.parent / "config" / "supabase_sync_log.json"


def get_local_stats() -> dict:
    """Lee stats reales de SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        total = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
        con_nlp = conn.execute("SELECT COUNT(*) FROM ofertas_nlp").fetchone()[0]
        sin_nlp = total - con_nlp

        # NLP Gate
        try:
            aprobados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'aprobado'").fetchone()[0]
            bloqueados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'bloqueado'").fetchone()[0]
            sin_gate = con_nlp - aprobados - bloqueados
        except Exception:
            aprobados = con_nlp
            bloqueados = 0
            sin_gate = 0

        # Matching
        try:
            con_matching = conn.execute("SELECT COUNT(*) FROM ofertas_esco_matching").fetchone()[0]
        except Exception:
            con_matching = 0
        sin_matching = aprobados - con_matching if aprobados > con_matching else 0

        # Validación
        try:
            validadas = conn.execute(
                "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion IN ('validado','validado_claude','validado_humano')"
            ).fetchone()[0]
        except Exception:
            validadas = 0

        # Errores
        try:
            errores_pendientes = conn.execute("SELECT COUNT(*) FROM validation_errors WHERE resuelto = 0").fetchone()[0]
            errores_total = conn.execute("SELECT COUNT(*) FROM validation_errors").fetchone()[0]
        except Exception:
            errores_pendientes = 0
            errores_total = 0

        # Último pipeline run
        try:
            ultimo_run = conn.execute(
                "SELECT run_id, timestamp, total_ofertas FROM pipeline_runs ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            ultimo_run_info = {
                "run_id": ultimo_run[0] if ultimo_run else None,
                "timestamp": ultimo_run[1] if ultimo_run else None,
                "ofertas": ultimo_run[2] if ultimo_run else None,
            }
        except Exception:
            ultimo_run_info = {"run_id": None, "timestamp": None, "ofertas": None}

        # Sync status
        try:
            sync_log = json.loads(SUPABASE_SYNC_LOG.read_text()) if SUPABASE_SYNC_LOG.exists() else {}
            ultimo_sync = sync_log.get("last_sync_timestamp") or sync_log.get("ultimo_sync")
            en_supabase = sync_log.get("ofertas_synced") or sync_log.get("total_synced", 0)
        except Exception:
            ultimo_sync = None
            en_supabase = 0

        pendientes_sync = validadas - en_supabase if validadas > en_supabase else 0

        # NLP Gate percentages
        gate_total = aprobados + bloqueados
        gate_aprobado_pct = round(aprobados / gate_total * 100, 1) if gate_total > 0 else 100

        return {
            "source": "local",
            "timestamp": datetime.utcnow().isoformat(),
            "scraping": {
                "total_ofertas": total,
            },
            "nlp": {
                "procesadas": con_nlp,
                "pendientes": sin_nlp,
                "aprobados": aprobados,
                "bloqueados": bloqueados,
                "sin_gate": sin_gate,
                "gate_aprobado_pct": gate_aprobado_pct,
            },
            "matching": {
                "con_matching": con_matching,
                "sin_matching": sin_matching,
            },
            "validacion": {
                "validadas": validadas,
                "errores_pendientes": errores_pendientes,
                "errores_total": errores_total,
            },
            "sync": {
                "en_supabase": en_supabase,
                "pendientes_sync": pendientes_sync,
                "ultimo_sync": ultimo_sync,
            },
            "ultimo_run": ultimo_run_info,
        }

    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/pipeline-local-status":
            try:
                data = get_local_stats()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silenciar logs de requests


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline Local Status Server")
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"[LOCAL-STATUS] Servidor en http://localhost:{args.port}/pipeline-local-status")
    print(f"[LOCAL-STATUS] BD: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[LOCAL-STATUS] Apagado")


if __name__ == "__main__":
    main()
