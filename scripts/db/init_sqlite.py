"""
Inicializador de Base de Datos SQLite
======================================

Crea y configura la base de datos SQLite para Bumeran Scraping.

Uso:
    # Crear/inicializar DB
    python database/init_sqlite.py

    # Forzar recreación (borra datos existentes)
    python database/init_sqlite.py --reset

    # Desde código
    from database.init_sqlite import init_database
    init_database()
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def init_database(db_path: str = 'database/bumeran_scraping.db', reset: bool = False) -> bool:
    """
    Inicializa la base de datos SQLite ejecutando el schema

    Args:
        db_path: Ruta al archivo de base de datos
        reset: Si True, borra la DB existente y la recrea

    Returns:
        True si se inicializó correctamente
    """
    db_file = Path(db_path)

    # Crear directorio si no existe
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Verificar si ya existe
    if db_file.exists():
        if reset:
            logger.warning(f"Eliminando base de datos existente: {db_path}")
            db_file.unlink()
            print(f"Base de datos eliminada: {db_path}")
        else:
            logger.info(f"Base de datos ya existe: {db_path}")
            print(f"Base de datos ya existe: {db_path}")
            print("Usa --reset para recrearla (CUIDADO: borra todos los datos)")
            return True

    # Leer schema SQL
    schema_path = Path(__file__).parent / 'create_database_sqlite.sql'

    if not schema_path.exists():
        logger.error(f"Archivo de schema no encontrado: {schema_path}")
        print(f"ERROR: No se encontró {schema_path}")
        return False

    logger.info(f"Leyendo schema desde: {schema_path}")

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
    except Exception as e:
        logger.error(f"Error leyendo schema: {e}")
        print(f"ERROR leyendo schema: {e}")
        return False

    # Crear base de datos y ejecutar schema
    logger.info(f"Creando base de datos: {db_path}")
    print(f"Creando base de datos: {db_path}")

    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Habilitar foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Ejecutar schema (puede contener múltiples statements)
        cursor.executescript(schema_sql)

        conn.commit()

        # Verificar tablas creadas
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        logger.info(f"Tablas creadas: {', '.join(tables)}")
        print(f"\n[OK] Base de datos creada exitosamente!")
        print(f"  Ubicacion: {db_file.absolute()}")
        print(f"  Tablas: {len(tables)}")
        print(f"    - {', '.join(tables)}")

        # Verificar vistas
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view'
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]

        if views:
            logger.info(f"Vistas creadas: {', '.join(views)}")
            print(f"  Vistas: {len(views)}")
            print(f"    - {', '.join(views)}")

        conn.close()

        return True

    except Exception as e:
        logger.error(f"Error creando base de datos: {e}")
        print(f"\nERROR creando base de datos: {e}")

        # Limpiar archivo parcial si se creó
        if db_file.exists():
            db_file.unlink()

        return False


def verify_database(db_path: str = 'database/bumeran_scraping.db') -> bool:
    """
    Verifica que la base de datos esté correctamente configurada

    Args:
        db_path: Ruta al archivo de base de datos

    Returns:
        True si la DB está OK
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Base de datos no existe: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Verificar tablas requeridas
        required_tables = [
            'ofertas',
            'metricas_scraping',
            'alertas',
            'circuit_breaker_stats',
            'rate_limiter_stats'
        ]

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing_tables = [t for t in required_tables if t not in existing_tables]

        if missing_tables:
            print(f"Tablas faltantes: {', '.join(missing_tables)}")
            conn.close()
            return False

        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        ofertas_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM metricas_scraping")
        metricas_count = cursor.fetchone()[0]

        print(f"\n[OK] Base de datos verificada:")
        print(f"  Ubicacion: {db_file.absolute()}")
        print(f"  Tamano: {db_file.stat().st_size / 1024:.2f} KB")
        print(f"  Ofertas: {ofertas_count:,}")
        print(f"  Ejecuciones: {metricas_count}")

        conn.close()

        return True

    except Exception as e:
        print(f"Error verificando base de datos: {e}")
        return False


if __name__ == "__main__":
    """Inicializa base de datos desde CLI"""
    import sys

    print("="*70)
    print("INICIALIZADOR DE BASE DE DATOS SQLITE")
    print("="*70)
    print()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parsear argumentos
    reset = '--reset' in sys.argv

    if reset:
        print("MODO: Reset (recrear base de datos)")
        print("ADVERTENCIA: Esto borrará todos los datos existentes!")
        print()
        respuesta = input("¿Confirmar reset? (escribir 'SI' para continuar): ")
        if respuesta.strip().upper() != 'SI':
            print("\nCancelado.")
            sys.exit(0)
        print()

    # Inicializar
    success = init_database(reset=reset)

    print()
    print("="*70)

    if success:
        print("[OK] Inicializacion completada")
        print()

        # Verificar
        verify_database()

        print()
        print("Proximo paso:")
        print("  python run_scheduler.py --test")
        print()
    else:
        print("[ERROR] Error en inicializacion")
        sys.exit(1)
