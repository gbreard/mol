#!/usr/bin/env python3
"""
Migración 024 — Ciclo de vida de ofertas (Fase 1: schema)
=========================================================

Spec: exports/reportes/SPEC_ciclo_vida_ofertas.md (aprobada + addendum 2026-09-02).

Fase 1 = SOLO schema, aditivo y REVERSIBLE. No toca datos existentes ni cambia
comportamiento: agrega columnas nuevas (NULL/DEFAULT) + tablas nuevas + índices.
La legacy (estado_oferta/fecha_baja) queda intacta (dual-write en fases siguientes).

IDEMPOTENTE: ADD COLUMN guardado por PRAGMA table_info; CREATE ... IF NOT EXISTS.
Correr dos veces no debe fallar ni duplicar nada.

Uso:
    python3 database/migrations/024_ciclo_vida_ofertas.py --db <ruta> [--dry-run]
"""
import sqlite3
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = BASE_DIR / "database" / "bumeran_scraping.db"

# (columna, definición) — aditivas sobre `ofertas`. fecha_ultimo_visto YA existe.
COLUMNAS_OFERTAS = [
    ("estado_ciclo", "TEXT"),
    ("verificaciones_caida_count", "INTEGER DEFAULT 0"),
    ("fecha_primera_verificacion_caida", "TEXT"),
    ("fecha_ultima_verificacion", "TEXT"),
    ("fecha_baja_estimada", "TEXT"),
    ("fecha_baja_intervalo_desde", "TEXT"),
    ("fecha_baja_intervalo_hasta", "TEXT"),
    ("fecha_baja_incertidumbre_dias", "INTEGER"),
    ("grupo_oferta_id", "TEXT"),  # previsión dedup cross-portal (sin lógica en esta fase)
]

TABLAS = {
    "verificaciones_baja": """
        CREATE TABLE IF NOT EXISTS verificaciones_baja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta INTEGER NOT NULL,
            portal TEXT,
            fecha TEXT NOT NULL,
            via TEXT,                 -- searchv2 / html_detalle / listado_completo
            resultado TEXT,           -- viva / caida / ambigua
            senal_cruda TEXT          -- JSON corto con la evidencia
        )""",
    "recompute_ciclo_vida_log": """
        CREATE TABLE IF NOT EXISTS recompute_ciclo_vida_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            id_oferta INTEGER NOT NULL,
            estado_oferta_anterior TEXT,
            estado_ciclo_anterior TEXT,
            estado_ciclo_nuevo TEXT,
            fecha_ultimo_visto_usada TEXT,
            antiguedad_dias INTEGER,
            timestamp TEXT NOT NULL
        )""",
    "transiciones_ciclo_vida": """
        CREATE TABLE IF NOT EXISTS transiciones_ciclo_vida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta INTEGER NOT NULL,
            portal TEXT,
            estado_desde TEXT,
            estado_hacia TEXT,
            motivo TEXT,              -- scraping_reaparece / umbral / verificacion_caida / 2a_ausencia / recompute / fromage
            fecha TEXT NOT NULL
        )""",
}

INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_ofertas_estado_ciclo ON ofertas(estado_ciclo)",
    "CREATE INDEX IF NOT EXISTS idx_ofertas_portal_estado_ciclo ON ofertas(portal, estado_ciclo)",
    "CREATE INDEX IF NOT EXISTS idx_ofertas_grupo_oferta ON ofertas(grupo_oferta_id) WHERE grupo_oferta_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS idx_verif_baja_oferta ON verificaciones_baja(id_oferta)",
    "CREATE INDEX IF NOT EXISTS idx_recompute_run ON recompute_ciclo_vida_log(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_transiciones_oferta ON transiciones_ciclo_vida(id_oferta)",
    "CREATE INDEX IF NOT EXISTS idx_transiciones_estados ON transiciones_ciclo_vida(estado_desde, estado_hacia)",
]


def columnas_existentes(conn, tabla):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({tabla})")}


def aplicar(db_path, dry_run=False):
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    acciones = []

    filas_antes = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]

    existentes = columnas_existentes(conn, "ofertas")
    for col, definicion in COLUMNAS_OFERTAS:
        if col in existentes:
            acciones.append(f"= columna ofertas.{col} ya existe (skip)")
        else:
            sql = f"ALTER TABLE ofertas ADD COLUMN {col} {definicion}"
            acciones.append(f"+ {sql}")
            if not dry_run:
                conn.execute(sql)

    for nombre, ddl in TABLAS.items():
        ya = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nombre,)
        ).fetchone()
        acciones.append(f"= tabla {nombre} ya existe (skip)" if ya else f"+ CREATE TABLE {nombre}")
        if not dry_run:
            conn.execute(ddl)

    for idx in INDICES:
        nombre = idx.split("idx_", 1)[1].split(" ", 1)[0]
        acciones.append(f"~ CREATE INDEX IF NOT EXISTS idx_{nombre}")
        if not dry_run:
            conn.execute(idx)

    if not dry_run:
        conn.commit()

    filas_despues = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
    conn.close()
    return acciones, filas_antes, filas_despues


def verificar(db_path):
    """Post-condición: todas las columnas y tablas presentes."""
    conn = sqlite3.connect(str(db_path), timeout=60)
    cols = columnas_existentes(conn, "ofertas")
    faltan_cols = [c for c, _ in COLUMNAS_OFERTAS if c not in cols]
    tablas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    faltan_tablas = [t for t in TABLAS if t not in tablas]
    indices = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    faltan_idx = [i.split("idx_", 1)[1].split(" ", 1)[0] for i in INDICES
                  if ("idx_" + i.split("idx_", 1)[1].split(" ", 1)[0]) not in indices]
    conn.close()
    return faltan_cols, faltan_tablas, faltan_idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Migración 024 — ciclo de vida (Fase 1 schema) {'[DRY-RUN]' if args.dry_run else ''}")
    print(f"BD: {args.db}\n")
    acciones, antes, despues = aplicar(args.db, args.dry_run)
    for a in acciones:
        print("  " + a)
    print(f"\nFilas en ofertas: antes={antes:,}  después={despues:,}  (debe ser igual)")

    if not args.dry_run:
        fc, ft, fi = verificar(args.db)
        ok = not (fc or ft or fi)
        print(f"\nVerificación: columnas_faltantes={fc} tablas_faltantes={ft} indices_faltantes={fi}")
        print("RESULTADO: " + ("OK ✅" if ok and antes == despues else "REVISAR ❌"))


if __name__ == "__main__":
    main()
