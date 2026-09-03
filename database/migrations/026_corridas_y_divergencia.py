#!/usr/bin/env python3
"""
Migración 026 — soporte de Fase 3 (transiciones)
================================================

Idempotente, aditiva, reversible. Dos tablas nuevas:

- corridas_scraping: completitud del listado por corrida (§11.7). La escriben
  los runners de CABA/PE. `completa=1` sólo si el listado se bajó entero
  (PE: extraídas == contador del sitio; CABA: paginación agotada sin error).
  El motor de transiciones sólo cuenta una ausencia si ocurrió en corrida completa.

- divergencia_ciclo_log: métrica de divergencia legacy vs estado_ciclo por
  corrida (bonus §modo-sombra): cuántas bajas declaradas por el legacy el nuevo
  modelo considera activas. Argumento empírico para la nota metodológica (Fase 5).
"""
import sqlite3, argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = BASE_DIR / "database" / "bumeran_scraping.db"

TABLAS = {
    "corridas_scraping": """
        CREATE TABLE IF NOT EXISTS corridas_scraping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portal TEXT NOT NULL,
            fecha TEXT NOT NULL,          -- timestamp de fin de corrida
            completa INTEGER NOT NULL,    -- 1 = listado completo, 0 = incompleta/abortada
            n_vistas INTEGER,             -- ofertas vistas en la corrida
            n_esperadas INTEGER,          -- contador del sitio (si existe)
            nota TEXT                     -- método de completitud / motivo de incompleta
        )""",
    "divergencia_ciclo_log": """
        CREATE TABLE IF NOT EXISTS divergencia_ciclo_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            n_legacy_baja_ciclo_activa INTEGER,   -- legacy dice baja, ciclo dice activa (falsas bajas del legacy)
            n_legacy_baja_total INTEGER,
            detalle_json TEXT
        )""",
}
INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_corridas_portal_fecha ON corridas_scraping(portal, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_corridas_completa ON corridas_scraping(portal, completa, fecha)",
]


def aplicar(db_path, dry_run=False):
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    acc = []
    for nombre, ddl in TABLAS.items():
        ya = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nombre,)).fetchone()
        acc.append(f"= tabla {nombre} ya existe (skip)" if ya else f"+ CREATE TABLE {nombre}")
        if not dry_run:
            conn.execute(ddl)
    for idx in INDICES:
        acc.append("~ " + idx.split(" ON ")[0])
        if not dry_run:
            conn.execute(idx)
    if not dry_run:
        conn.commit()
    tablas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    faltan = [t for t in TABLAS if t not in tablas]
    return acc, faltan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print(f"Migración 026 — soporte Fase 3 {'[DRY-RUN]' if args.dry_run else ''}\nBD: {args.db}\n")
    acc, faltan = aplicar(args.db, args.dry_run)
    for a in acc:
        print("  " + a)
    if not args.dry_run:
        print("\nRESULTADO:", "OK ✅" if not faltan else f"REVISAR ❌ faltan {faltan}")


if __name__ == "__main__":
    main()
