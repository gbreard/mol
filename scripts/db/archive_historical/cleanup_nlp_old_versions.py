# -*- coding: utf-8 -*-
"""
Limpieza de datos NLP versiones obsoletas (v4.0.0, v3.7.0)
==========================================================

Contexto:
- Las versiones v4.0.0 y v3.7.0 fueron procesadas sin las mejoras de Gold Set
- La version actual v10.0.0 tiene configs externalizadas y validacion controlada
- Los datos viejos no son comparables con el nuevo pipeline

Este script:
1. Crea backup de ofertas_nlp (versiones a eliminar)
2. Elimina registros de versiones obsoletas
3. Mantiene solo v10.0.0 para optimizacion controlada

IMPORTANTE: Las ofertas scrapeadas (tabla ofertas) NO se tocan.

Fecha: 2026-01-03
Autor: Claude Code
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
METRICS_PATH = BASE_DIR / "metrics" / "cleanup_history.json"

def create_backup(conn, versions_to_delete: list) -> str:
    """Crea backup de registros NLP a eliminar."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ofertas_nlp_backup_oldversions_{timestamp}"

    cursor = conn.cursor()

    # Construir WHERE clause
    placeholders = ','.join(['?' for _ in versions_to_delete])

    # Contar registros a respaldar
    cursor.execute(f"""
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE nlp_version IN ({placeholders})
    """, versions_to_delete)
    count_backup = cursor.fetchone()[0]

    # Crear tabla backup solo con registros a eliminar
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {backup_name} AS
        SELECT * FROM ofertas_nlp
        WHERE nlp_version IN ({placeholders})
    """, versions_to_delete)
    conn.commit()

    print(f"Backup creado: {backup_name}")
    print(f"  Registros respaldados: {count_backup:,}")

    return backup_name

def get_version_stats(conn) -> dict:
    """Obtiene estadisticas por version de NLP."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nlp_version, COUNT(*) as cantidad
        FROM ofertas_nlp
        GROUP BY nlp_version
        ORDER BY cantidad DESC
    """)
    return {row[0]: row[1] for row in cursor.fetchall()}

def cleanup_old_versions(conn, versions_to_delete: list, dry_run: bool = True) -> dict:
    """Elimina registros de versiones NLP obsoletas."""
    cursor = conn.cursor()

    # Contar por version
    stats = {}
    for version in versions_to_delete:
        cursor.execute(
            "SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_version = ?",
            (version,)
        )
        stats[version] = cursor.fetchone()[0]

    total_to_delete = sum(stats.values())

    print(f"\nRegistros a eliminar:")
    for version, count in stats.items():
        if count > 0:
            print(f"  {version}: {count:,}")
    print(f"  TOTAL: {total_to_delete:,}")

    if dry_run:
        print("\n[DRY RUN] No se eliminaron registros.")
        print("Ejecutar con --execute para aplicar cambios.")
        return stats

    # Eliminar registros de versiones obsoletas
    for version in versions_to_delete:
        cursor.execute(
            "DELETE FROM ofertas_nlp WHERE nlp_version = ?",
            (version,)
        )
        print(f"  Eliminados {version}: {cursor.rowcount:,}")

    conn.commit()

    # Verificar estado final
    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
    remaining = cursor.fetchone()[0]

    # Contar ofertas scrapeadas (no se tocan)
    cursor.execute("SELECT COUNT(*) FROM ofertas")
    total_ofertas = cursor.fetchone()[0]

    print(f"\nLimpieza completada:")
    print(f"  Eliminados: {total_to_delete:,}")
    print(f"  NLP restantes: {remaining:,}")
    print(f"  Ofertas scrapeadas (intactas): {total_ofertas:,}")

    return stats

def save_cleanup_log(stats: dict, backup_name: str, dry_run: bool):
    """Guarda log de la operacion en metrics/."""
    METRICS_PATH.parent.mkdir(exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "cleanup_nlp_old_versions",
        "dry_run": dry_run,
        "backup_table": backup_name if not dry_run else None,
        "deleted_by_version": stats,
        "total_deleted": sum(stats.values())
    }

    # Cargar historial existente o crear nuevo
    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r') as f:
            history = json.load(f)
    else:
        history = []

    history.append(log_entry)

    with open(METRICS_PATH, 'w') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"\nLog guardado en: {METRICS_PATH}")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Limpia datos NLP de versiones obsoletas"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Ejecutar limpieza (sin esto solo muestra preview)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='No crear tabla backup (no recomendado)'
    )
    args = parser.parse_args()

    dry_run = not args.execute

    # Versiones a eliminar
    versions_to_delete = ['v4.0.0', '3.7.0']

    print("=" * 60)
    print("LIMPIEZA DE NLP VERSIONES OBSOLETAS")
    print("=" * 60)
    print(f"\nVersiones a eliminar: {versions_to_delete}")
    print("Version a mantener: v10.0.0")

    conn = sqlite3.connect(str(DB_PATH))

    # Estado actual
    print("\nEstado actual de ofertas_nlp:")
    version_stats = get_version_stats(conn)
    for version, count in version_stats.items():
        marker = " <- MANTENER" if version == "10.0.0" or version == "v10.0.0" else " <- ELIMINAR"
        print(f"  {version}: {count:,}{marker}")

    # Crear backup si no es dry_run
    backup_name = None
    if not dry_run and not args.no_backup:
        backup_name = create_backup(conn, versions_to_delete)

    # Ejecutar limpieza
    stats = cleanup_old_versions(conn, versions_to_delete, dry_run=dry_run)

    # Guardar log
    save_cleanup_log(stats, backup_name, dry_run)

    conn.close()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
