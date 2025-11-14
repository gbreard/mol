"""
Script de Migracion de Datos Historicos - v1 a v2
===================================================

Migra las 5,479 ofertas existentes de schema v1 (tabla 'ofertas')
a schema v2 (tabla 'ofertas_raw' con JSON + SHA256).

Uso:
    # Dry-run (simulacion sin cambios)
    python migrate_historical_data.py --dry-run

    # Migracion real
    python migrate_historical_data.py

    # Con batch size personalizado
    python migrate_historical_data.py --batch-size 100

Caracteristicas:
- Crea sesion de scraping para tracking
- Barra de progreso con tqdm
- Procesamiento en batches
- Rollback automatico en errores
- Log detallado del proceso
- Modo dry-run para testing
"""

import sys
import os
import argparse
import logging
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tqdm import tqdm
except ImportError:
    print("ERROR: tqdm no esta instalado")
    print("Instalar con: pip install tqdm")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_historical.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HistoricalDataMigrator:
    """Migrador de datos historicos v1 -> v2"""

    def __init__(self, db_path: str = '../bumeran_scraping.db', batch_size: int = 500):
        """
        Inicializa migrador

        Args:
            db_path: Ruta a la base de datos
            batch_size: Tamanio de batch para procesamiento
        """
        self.db_path = Path(db_path)
        self.batch_size = batch_size
        self.conn = None
        self.cursor = None
        self.session_id = None
        self.session_uuid = None

        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

    def connect(self):
        """Establece conexion con SQLite"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Conexion establecida: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a SQLite: {e}")
            return False

    def disconnect(self):
        """Cierra conexion"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Conexion cerrada")

    def create_migration_session(self) -> Tuple[int, str]:
        """
        Crea sesion de scraping para tracking de migracion

        Returns:
            (session_id, session_uuid)
        """
        try:
            import uuid
            session_uuid = str(uuid.uuid4())

            query = """
                INSERT INTO scraping_sessions (
                    session_uuid, source, mode, start_time, status
                ) VALUES (?, 'bumeran', 'full', ?, 'running')
            """

            self.cursor.execute(query, (
                session_uuid,
                datetime.now().isoformat()
            ))

            session_id = self.cursor.lastrowid
            self.session_id = session_id
            self.session_uuid = session_uuid

            logger.info(f"Sesion de migracion creada: ID={session_id}, UUID={session_uuid[:8]}...")
            return (session_id, session_uuid)

        except Exception as e:
            logger.error(f"Error creando sesion de migracion: {e}")
            raise

    def close_migration_session(self, ofertas_migradas: int, status: str = 'completed'):
        """Cierra sesion de migracion"""
        if not self.session_id:
            return

        try:
            query = """
                UPDATE scraping_sessions
                SET end_time = ?,
                    ofertas_total = ?,
                    ofertas_nuevas = ?,
                    status = ?
                WHERE id = ?
            """

            self.cursor.execute(query, (
                datetime.now().isoformat(),
                ofertas_migradas,
                ofertas_migradas,  # Todas son "nuevas" en v2
                status,
                self.session_id
            ))

            logger.info(f"Sesion de migracion cerrada: {ofertas_migradas} ofertas migradas")

        except Exception as e:
            logger.warning(f"Error cerrando sesion de migracion: {e}")

    def get_ofertas_count_v1(self) -> int:
        """Obtiene total de ofertas en v1"""
        self.cursor.execute("SELECT COUNT(*) FROM ofertas")
        count = self.cursor.fetchone()[0]
        logger.info(f"Total ofertas en v1: {count:,}")
        return count

    def get_ofertas_count_v2(self) -> int:
        """Obtiene total de ofertas en v2 (ofertas_raw)"""
        self.cursor.execute("SELECT COUNT(*) FROM ofertas_raw")
        count = self.cursor.fetchone()[0]
        logger.info(f"Total ofertas en v2 (ofertas_raw): {count:,}")
        return count

    def fetch_ofertas_batch(self, offset: int, limit: int) -> List[Dict]:
        """
        Obtiene batch de ofertas de v1

        Args:
            offset: Offset para paginacion
            limit: Cantidad de ofertas a obtener

        Returns:
            Lista de ofertas como diccionarios
        """
        query = "SELECT * FROM ofertas LIMIT ? OFFSET ?"
        self.cursor.execute(query, (limit, offset))

        rows = self.cursor.fetchall()
        ofertas = [dict(row) for row in rows]

        return ofertas

    def migrate_batch_to_v2(self, ofertas: List[Dict], dry_run: bool = False) -> int:
        """
        Migra batch de ofertas a v2

        Args:
            ofertas: Lista de ofertas a migrar
            dry_run: Si es True, no hace cambios reales

        Returns:
            Numero de ofertas migradas
        """
        if dry_run:
            return len(ofertas)

        migrated_count = 0

        for oferta in ofertas:
            try:
                # Convertir oferta a JSON
                raw_json = json.dumps(oferta, ensure_ascii=False)

                # Calcular SHA256 hash
                content_hash = hashlib.sha256(raw_json.encode('utf-8')).hexdigest()

                # Obtener campos principales
                id_oferta = oferta.get('id_oferta')
                url_oferta = oferta.get('url_oferta')
                scrapeado_en = oferta.get('scrapeado_en', datetime.now().isoformat())

                # INSERT OR IGNORE (evita duplicados)
                query = """
                    INSERT OR IGNORE INTO ofertas_raw (
                        id_oferta, scraping_session_id, raw_json, content_hash,
                        scrapeado_en, source, url_oferta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                self.cursor.execute(query, (
                    id_oferta,
                    self.session_id,
                    raw_json,
                    content_hash,
                    scrapeado_en,
                    'bumeran',  # source
                    url_oferta
                ))

                migrated_count += 1

            except Exception as e:
                logger.error(f"Error migrando oferta {oferta.get('id_oferta')}: {e}")
                raise

        return migrated_count

    def run_migration(self, dry_run: bool = False):
        """
        Ejecuta migracion completa

        Args:
            dry_run: Si es True, simula sin hacer cambios
        """
        logger.info("="*70)
        logger.info("INICIO DE MIGRACION DE DATOS HISTORICOS v1 -> v2")
        logger.info("="*70)

        if dry_run:
            logger.warning("MODO DRY-RUN: No se realizaran cambios reales")

        try:
            # Conectar
            if not self.connect():
                raise Exception("No se pudo conectar a la base de datos")

            # Verificar conteos iniciales
            count_v1 = self.get_ofertas_count_v1()
            count_v2_inicial = self.get_ofertas_count_v2()

            logger.info(f"Ofertas en v1: {count_v1:,}")
            logger.info(f"Ofertas en v2 (antes): {count_v2_inicial:,}")
            logger.info(f"Batch size: {self.batch_size}")

            if count_v1 == 0:
                logger.warning("No hay ofertas para migrar en v1")
                return

            # Crear sesion de migracion
            if not dry_run:
                self.create_migration_session()

            # Procesar en batches con barra de progreso
            total_migradas = 0
            offset = 0

            with tqdm(total=count_v1, desc="Migrando ofertas", unit="ofertas") as pbar:
                while offset < count_v1:
                    # Fetch batch
                    batch = self.fetch_ofertas_batch(offset, self.batch_size)

                    if not batch:
                        break

                    # Migrar batch
                    count = self.migrate_batch_to_v2(batch, dry_run=dry_run)

                    # Commit batch (o simular en dry-run)
                    if not dry_run:
                        self.conn.commit()

                    total_migradas += count
                    offset += len(batch)

                    pbar.update(len(batch))

            # Verificar conteo final
            if not dry_run:
                count_v2_final = self.get_ofertas_count_v2()
                ofertas_agregadas = count_v2_final - count_v2_inicial

                logger.info("")
                logger.info("="*70)
                logger.info("RESULTADO DE MIGRACION")
                logger.info("="*70)
                logger.info(f"Ofertas migradas: {total_migradas:,}")
                logger.info(f"Ofertas en v2 (despues): {count_v2_final:,}")
                logger.info(f"Ofertas agregadas a v2: {ofertas_agregadas:,}")

                # Cerrar sesion
                self.close_migration_session(total_migradas, status='completed')
            else:
                logger.info("")
                logger.info("="*70)
                logger.info("SIMULACION COMPLETADA (DRY-RUN)")
                logger.info("="*70)
                logger.info(f"Ofertas que se migrarian: {total_migradas:,}")

            logger.info("="*70)
            logger.info("MIGRACION COMPLETADA EXITOSAMENTE")
            logger.info("="*70)

        except Exception as e:
            logger.error(f"ERROR durante migracion: {e}")

            if not dry_run:
                logger.warning("Ejecutando ROLLBACK...")
                self.conn.rollback()

                # Cerrar sesion como fallida
                if self.session_id:
                    self.close_migration_session(0, status='failed')

            raise

        finally:
            self.disconnect()


def main():
    """Funcion principal"""
    parser = argparse.ArgumentParser(
        description='Migra datos historicos de v1 a v2 schema'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula migracion sin hacer cambios'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Tamanio de batch para procesamiento (default: 500)'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='../bumeran_scraping.db',
        help='Ruta a la base de datos'
    )

    args = parser.parse_args()

    # Crear migrador y ejecutar
    migrator = HistoricalDataMigrator(
        db_path=args.db_path,
        batch_size=args.batch_size
    )

    migrator.run_migration(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
