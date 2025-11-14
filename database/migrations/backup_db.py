#!/usr/bin/env python3
"""
Script de Backup de Base de Datos - FASE 1 Migración
=====================================================

Crea backups completos de la base de datos SQLite actual antes de la migración.
Incluye verificación de integridad, metadata y compresión opcional.

Uso:
    python backup_db.py
    python backup_db.py --compress
    python backup_db.py --output /custom/path/
"""

import sqlite3
import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
import argparse
import sys


class DatabaseBackup:
    """Gestor de backups de la base de datos SQLite"""

    def __init__(self, db_path: Path, backup_dir: Path):
        """
        Args:
            db_path: Path a la base de datos a respaldar
            backup_dir: Directorio donde guardar backups
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calcula checksum SHA256 de un archivo

        Returns:
            Checksum hexadecimal
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Leer en chunks para archivos grandes
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def get_database_stats(self) -> dict:
        """
        Obtiene estadísticas de la base de datos

        Returns:
            Dict con stats de todas las tablas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        stats = {
            'database_size_mb': self.db_path.stat().st_size / (1024 * 1024),
            'tables': {},
            'total_records': 0
        }

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats['tables'][table] = count
                stats['total_records'] += count
            except Exception as e:
                stats['tables'][table] = f"ERROR: {e}"

        conn.close()
        return stats

    def verify_backup_integrity(self, backup_path: Path) -> bool:
        """
        Verifica integridad de un backup

        Returns:
            True si el backup es válido
        """
        try:
            # Intentar conectar a la BD backup
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()

            # Ejecutar PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            conn.close()

            return result == "ok"
        except Exception as e:
            print(f"[ERROR] Verificación falló: {e}")
            return False

    def create_backup(self, description: str = "", compress: bool = False) -> Path:
        """
        Crea un backup completo de la base de datos

        Args:
            description: Descripción del backup
            compress: Si True, comprimir el backup (usar para BDs grandes)

        Returns:
            Path al archivo de backup creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.db_path.stem}_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        print("=" * 70)
        print("CREANDO BACKUP DE BASE DE DATOS")
        print("=" * 70)
        print(f"Origen:      {self.db_path}")
        print(f"Destino:     {backup_path}")
        print(f"Timestamp:   {timestamp}")
        print()

        # 1. Obtener stats antes del backup
        print("[1/6] Obteniendo estadísticas de la base de datos...")
        stats_before = self.get_database_stats()
        print(f"      Tamaño: {stats_before['database_size_mb']:.2f} MB")
        print(f"      Tablas: {len(stats_before['tables'])}")
        print(f"      Registros totales: {stats_before['total_records']:,}")
        print()

        # 2. Crear backup usando SQLite backup API (más seguro que shutil.copy)
        print("[2/6] Copiando base de datos...")
        try:
            # Conectar a ambas bases
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            # Realizar backup usando API oficial de SQLite
            with backup_conn:
                source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            print(f"      [OK] Backup creado: {backup_path.name}")
        except Exception as e:
            print(f"      [ERROR] Fallo al crear backup: {e}")
            return None
        print()

        # 3. Verificar integridad del backup
        print("[3/6] Verificando integridad del backup...")
        if self.verify_backup_integrity(backup_path):
            print("      [OK] Integridad verificada")
        else:
            print("      [ERROR] Backup corrupto - Abortando")
            backup_path.unlink()  # Eliminar backup corrupto
            return None
        print()

        # 4. Calcular checksum
        print("[4/6] Calculando checksum SHA256...")
        checksum = self.calculate_checksum(backup_path)
        print(f"      Checksum: {checksum}")
        print()

        # 5. Crear metadata
        print("[5/6] Creando metadata del backup...")
        metadata = {
            'backup_filename': backup_filename,
            'backup_timestamp': timestamp,
            'backup_date_iso': datetime.now().isoformat(),
            'original_db_path': str(self.db_path),
            'original_db_size_mb': stats_before['database_size_mb'],
            'backup_size_mb': backup_path.stat().st_size / (1024 * 1024),
            'checksum_sha256': checksum,
            'description': description,
            'compressed': compress,
            'tables_count': len(stats_before['tables']),
            'total_records': stats_before['total_records'],
            'tables_stats': stats_before['tables'],
            'integrity_check': 'passed',
            'created_by': 'backup_db.py v1.0',
            'migration_phase': 'FASE_1_preparacion'
        }

        metadata_path = backup_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"      [OK] Metadata guardada: {metadata_path.name}")
        print()

        # 6. Compresión opcional (para BDs grandes >50 MB)
        if compress and backup_path.stat().st_size > (50 * 1024 * 1024):
            print("[6/6] Comprimiendo backup...")
            import gzip

            compressed_path = backup_path.with_suffix('.db.gz')
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Eliminar archivo sin comprimir
            backup_path.unlink()
            print(f"      [OK] Backup comprimido: {compressed_path.name}")
            backup_path = compressed_path
        else:
            print("[6/6] Compresión no requerida (deshabilitada o BD <50MB)")
        print()

        # Reporte final
        print("=" * 70)
        print("BACKUP COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"Archivo:     {backup_path.name}")
        print(f"Tamaño:      {backup_path.stat().st_size / (1024 * 1024):.2f} MB")
        print(f"Checksum:    {checksum}")
        print(f"Metadata:    {metadata_path.name}")
        print()
        print("Para restaurar este backup:")
        print(f"  cp {backup_path} {self.db_path}")
        print()

        return backup_path

    def list_backups(self):
        """Lista todos los backups disponibles con su metadata"""
        backup_files = sorted(self.backup_dir.glob("*_backup_*.db*"), reverse=True)

        if not backup_files:
            print("No hay backups disponibles")
            return

        print("=" * 70)
        print(f"BACKUPS DISPONIBLES ({len(backup_files)})")
        print("=" * 70)
        print()

        for backup_file in backup_files:
            metadata_file = backup_file.with_suffix('.json')

            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                print(f"Archivo:    {backup_file.name}")
                print(f"Fecha:      {metadata['backup_date_iso']}")
                print(f"Tamaño:     {metadata['backup_size_mb']:.2f} MB")
                print(f"Registros:  {metadata['total_records']:,}")
                print(f"Checksum:   {metadata['checksum_sha256'][:16]}...")
                if metadata.get('description'):
                    print(f"Desc:       {metadata['description']}")
                print()
            else:
                print(f"Archivo:    {backup_file.name}")
                print(f"Tamaño:     {backup_file.stat().st_size / (1024 * 1024):.2f} MB")
                print(f"[WARNING]   Metadata no encontrada")
                print()


def main():
    parser = argparse.ArgumentParser(
        description='Crea backup de la base de datos SQLite con verificación de integridad'
    )
    parser.add_argument(
        '--db-path',
        default='D:/OEDE/Webscrapping/database/bumeran_scraping.db',
        help='Path a la base de datos (default: bumeran_scraping.db en database/)'
    )
    parser.add_argument(
        '--output',
        default='D:/OEDE/Webscrapping/database/backups',
        help='Directorio para guardar backups (default: database/backups/)'
    )
    parser.add_argument(
        '--description',
        default='Backup pre-migración FASE 1',
        help='Descripción del backup'
    )
    parser.add_argument(
        '--compress',
        action='store_true',
        help='Comprimir backup con gzip (para BDs >50 MB)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='Listar backups existentes'
    )

    args = parser.parse_args()

    # Crear instancia del gestor de backups
    backup_manager = DatabaseBackup(
        db_path=Path(args.db_path),
        backup_dir=Path(args.output)
    )

    # Listar backups si se solicita
    if args.list:
        backup_manager.list_backups()
        return

    # Verificar que la BD existe
    if not Path(args.db_path).exists():
        print(f"[ERROR] Base de datos no encontrada: {args.db_path}")
        sys.exit(1)

    # Crear backup
    backup_path = backup_manager.create_backup(
        description=args.description,
        compress=args.compress
    )

    if backup_path:
        print("[OK] Backup completado exitosamente")
        sys.exit(0)
    else:
        print("[ERROR] Fallo al crear backup")
        sys.exit(1)


if __name__ == '__main__':
    main()
