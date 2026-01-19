# -*- coding: utf-8 -*-
"""
Limpieza de datos de matching versiones obsoletas (v8.x)
=========================================================

Contexto:
- Las versiones v8.1, v8.3, v8.4 usaban reglas de matching
- La version actual v2.1.1 usa embeddings BGE-M3 (100% Gold Set)
- Los datos v8.x generan ruido y no son comparables

Este script:
1. Crea backup de ofertas_esco_matching
2. Elimina registros de versiones v8.x
3. Mantiene estructura de tabla para re-procesamiento futuro

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
BACKUP_DIR = BASE_DIR / "backups"
METRICS_PATH = BASE_DIR / "metrics" / "cleanup_history.json"

def create_backup(conn, backup_dir: Path) -> str:
    """Crea backup de la tabla ofertas_esco_matching."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ofertas_esco_matching_backup_{timestamp}"

    cursor = conn.cursor()

    # Contar registros antes
    cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
    count_before = cursor.fetchone()[0]

    # Crear tabla backup
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {backup_name} AS
        SELECT * FROM ofertas_esco_matching
    """)
    conn.commit()

    print(f"Backup creado: {backup_name}")
    print(f"  Registros respaldados: {count_before:,}")

    return backup_name

def get_version_stats(conn) -> dict:
    """Obtiene estadisticas por version de matching."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT matching_version, COUNT(*) as cantidad
        FROM ofertas_esco_matching
        GROUP BY matching_version
        ORDER BY cantidad DESC
    """)
    return {row[0]: row[1] for row in cursor.fetchall()}

def cleanup_v8x(conn, dry_run: bool = True) -> dict:
    """Elimina registros de versiones v8.x."""
    cursor = conn.cursor()

    # Versiones a eliminar
    v8x_versions = [
        'v8.1_esco_multicriterio_validado',
        'v8.3_diccionario_argentino_validated',
        'v8.4_multicriterio_nivel_validated'
    ]

    # Contar por version
    stats = {}
    for version in v8x_versions:
        cursor.execute(
            "SELECT COUNT(*) FROM ofertas_esco_matching WHERE matching_version = ?",
            (version,)
        )
        stats[version] = cursor.fetchone()[0]

    # Contar NULL versions
    cursor.execute(
        "SELECT COUNT(*) FROM ofertas_esco_matching WHERE matching_version IS NULL"
    )
    stats['NULL'] = cursor.fetchone()[0]

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

    # Eliminar registros v8.x
    for version in v8x_versions:
        cursor.execute(
            "DELETE FROM ofertas_esco_matching WHERE matching_version = ?",
            (version,)
        )

    # Eliminar NULL versions
    cursor.execute(
        "DELETE FROM ofertas_esco_matching WHERE matching_version IS NULL"
    )

    conn.commit()

    # Verificar estado final
    cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
    remaining = cursor.fetchone()[0]

    print(f"\nLimpieza completada:")
    print(f"  Eliminados: {total_to_delete:,}")
    print(f"  Restantes: {remaining:,}")

    return stats

def save_cleanup_log(stats: dict, backup_name: str, dry_run: bool):
    """Guarda log de la operacion en metrics/."""
    METRICS_PATH.parent.mkdir(exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "cleanup_matching_v8x",
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
        description="Limpia datos de matching v8.x obsoletos"
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

    print("=" * 60)
    print("LIMPIEZA DE MATCHING V8.X")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))

    # Estado actual
    print("\nEstado actual:")
    version_stats = get_version_stats(conn)
    for version, count in version_stats.items():
        print(f"  {version}: {count:,}")

    # Crear backup si no es dry_run
    backup_name = None
    if not dry_run and not args.no_backup:
        backup_name = create_backup(conn, BACKUP_DIR)

    # Ejecutar limpieza
    stats = cleanup_v8x(conn, dry_run=dry_run)

    # Guardar log
    save_cleanup_log(stats, backup_name, dry_run)

    conn.close()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
