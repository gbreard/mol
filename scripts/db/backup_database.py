#!/usr/bin/env python3
"""
MOL - Backup automático de SQLite
Issue: MOL-23

Funcionalidades:
- Copia la BD a backups/ con timestamp
- Comprime con gzip
- Verifica integridad (PRAGMA integrity_check)
- Limpia backups > 30 días
- Log de operaciones

Uso:
    python scripts/backup_database.py
    python scripts/backup_database.py --retention 7  # Solo últimos 7 días
    python scripts/backup_database.py --dry-run      # Simular sin ejecutar
"""

import os
import sys
import gzip
import shutil
import sqlite3
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
BACKUP_DIR = BASE_DIR / "backups"
DEFAULT_RETENTION_DAYS = 30

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def verify_integrity(db_path: Path) -> bool:
    """Verifica integridad de la base de datos SQLite."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        return result == "ok"
    except Exception as e:
        logger.error(f"Error verificando integridad: {e}")
        return False


def get_db_stats(db_path: Path) -> dict:
    """Obtiene estadísticas básicas de la BD."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Contar registros en tablas principales
        stats = {}
        for table in ['ofertas', 'ofertas_nlp', 'ofertas_esco_matching']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except:
                stats[table] = 0

        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {}


def create_backup(dry_run: bool = False) -> Path | None:
    """
    Crea backup comprimido de la base de datos.

    Returns:
        Path del backup creado o None si falló
    """
    # Verificar que existe la BD
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return None

    # Crear directorio de backups si no existe
    BACKUP_DIR.mkdir(exist_ok=True)

    # Nombre del backup con timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_name = f"bumeran_scraping_{timestamp}.db.gz"
    backup_path = BACKUP_DIR / backup_name

    # Tamaño original
    original_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB

    logger.info(f"Iniciando backup de {DB_PATH.name}")
    logger.info(f"Tamaño original: {original_size:.2f} MB")

    if dry_run:
        logger.info(f"[DRY-RUN] Se crearía: {backup_path}")
        return backup_path

    # Verificar integridad antes de backup
    logger.info("Verificando integridad de la BD...")
    if not verify_integrity(DB_PATH):
        logger.error("La BD tiene problemas de integridad. Backup cancelado.")
        return None
    logger.info("Integridad OK")

    # Obtener estadísticas
    stats = get_db_stats(DB_PATH)
    if stats:
        logger.info(f"Registros: ofertas={stats.get('ofertas', 0)}, "
                   f"nlp={stats.get('ofertas_nlp', 0)}, "
                   f"matching={stats.get('ofertas_esco_matching', 0)}")

    # Crear backup comprimido
    try:
        logger.info("Comprimiendo...")
        with open(DB_PATH, 'rb') as f_in:
            with gzip.open(backup_path, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Tamaño comprimido
        compressed_size = backup_path.stat().st_size / (1024 * 1024)  # MB
        ratio = (1 - compressed_size / original_size) * 100

        logger.info(f"Backup creado: {backup_path.name}")
        logger.info(f"Tamaño comprimido: {compressed_size:.2f} MB ({ratio:.1f}% reducción)")

        # Verificar que el backup es válido (descomprime sin error)
        try:
            with gzip.open(backup_path, 'rb') as f:
                f.read(1024)  # Leer primeros bytes para verificar
            logger.info("Verificación de backup OK")
        except Exception as e:
            logger.error(f"Backup corrupto: {e}")
            backup_path.unlink()  # Eliminar backup corrupto
            return None

        return backup_path

    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        if backup_path.exists():
            backup_path.unlink()
        return None


def cleanup_old_backups(retention_days: int, dry_run: bool = False) -> int:
    """
    Elimina backups más antiguos que retention_days.

    Returns:
        Cantidad de backups eliminados
    """
    if not BACKUP_DIR.exists():
        return 0

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted = 0

    for backup_file in BACKUP_DIR.glob("bumeran_scraping_*.db.gz"):
        # Extraer fecha del nombre del archivo
        try:
            # Formato: bumeran_scraping_2025-12-04_123456.db.gz
            date_str = backup_file.stem.replace("bumeran_scraping_", "").split("_")[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff_date:
                if dry_run:
                    logger.info(f"[DRY-RUN] Se eliminaría: {backup_file.name}")
                else:
                    backup_file.unlink()
                    logger.info(f"Eliminado backup antiguo: {backup_file.name}")
                deleted += 1
        except (ValueError, IndexError):
            # Si no puede parsear la fecha, ignorar el archivo
            continue

    return deleted


def list_backups() -> list:
    """Lista todos los backups disponibles."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("bumeran_scraping_*.db.gz"), reverse=True):
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        backups.append({
            'path': backup_file,
            'name': backup_file.name,
            'size_mb': size_mb,
            'date': mtime
        })

    return backups


def restore_backup(backup_path: Path, dry_run: bool = False) -> bool:
    """
    Restaura un backup a la ubicación original.

    CUIDADO: Esto sobrescribe la BD actual!
    """
    if not backup_path.exists():
        logger.error(f"Backup no encontrado: {backup_path}")
        return False

    if dry_run:
        logger.info(f"[DRY-RUN] Se restauraría {backup_path.name} a {DB_PATH}")
        return True

    # Crear backup de seguridad de la BD actual
    if DB_PATH.exists():
        safety_backup = DB_PATH.with_suffix('.db.pre_restore')
        shutil.copy2(DB_PATH, safety_backup)
        logger.info(f"Backup de seguridad creado: {safety_backup.name}")

    try:
        logger.info(f"Restaurando {backup_path.name}...")
        with gzip.open(backup_path, 'rb') as f_in:
            with open(DB_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Verificar integridad después de restaurar
        if verify_integrity(DB_PATH):
            logger.info("Restauración exitosa. Integridad OK.")
            return True
        else:
            logger.error("La BD restaurada tiene problemas de integridad!")
            return False

    except Exception as e:
        logger.error(f"Error restaurando: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backup automático de SQLite para MOL')
    parser.add_argument('--retention', type=int, default=DEFAULT_RETENTION_DAYS,
                       help=f'Días de retención de backups (default: {DEFAULT_RETENTION_DAYS})')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simular sin ejecutar cambios')
    parser.add_argument('--list', action='store_true',
                       help='Listar backups existentes')
    parser.add_argument('--restore', type=str, metavar='BACKUP',
                       help='Restaurar un backup específico')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Solo limpiar backups antiguos, no crear nuevo')

    args = parser.parse_args()

    # Listar backups
    if args.list:
        backups = list_backups()
        if not backups:
            print("No hay backups disponibles.")
        else:
            print(f"\n{'='*60}")
            print(f"{'Backup':<45} {'Tamaño':>8} {'Fecha'}")
            print(f"{'='*60}")
            for b in backups:
                print(f"{b['name']:<45} {b['size_mb']:>6.2f}MB  {b['date'].strftime('%Y-%m-%d %H:%M')}")
            print(f"{'='*60}")
            print(f"Total: {len(backups)} backups")
        return 0

    # Restaurar backup
    if args.restore:
        backup_path = BACKUP_DIR / args.restore if not os.path.isabs(args.restore) else Path(args.restore)
        success = restore_backup(backup_path, dry_run=args.dry_run)
        return 0 if success else 1

    # Limpiar backups antiguos
    if args.cleanup_only:
        deleted = cleanup_old_backups(args.retention, dry_run=args.dry_run)
        logger.info(f"Limpieza completada: {deleted} backups eliminados")
        return 0

    # Flujo principal: crear backup + limpiar antiguos
    print(f"\n{'='*60}")
    print("MOL - Backup de Base de Datos")
    print(f"{'='*60}\n")

    # Crear backup
    backup_path = create_backup(dry_run=args.dry_run)

    if backup_path:
        # Limpiar backups antiguos
        deleted = cleanup_old_backups(args.retention, dry_run=args.dry_run)
        if deleted > 0:
            logger.info(f"Limpieza: {deleted} backups antiguos eliminados")

        # Mostrar resumen de backups
        backups = list_backups()
        logger.info(f"Backups disponibles: {len(backups)}")

        print(f"\n{'='*60}")
        print("BACKUP COMPLETADO EXITOSAMENTE")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"\n{'='*60}")
        print("ERROR: Backup falló")
        print(f"{'='*60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
