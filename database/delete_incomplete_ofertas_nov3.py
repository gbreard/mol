"""
Script de Limpieza - Eliminar Ofertas Defectuosas del 3 de Noviembre 2025
===========================================================================

Elimina las 5,181 ofertas scrapeadas el 2025-11-03 que tienen datos incompletos
debido a un bug en run_scheduler.py (ya corregido).

Campos faltantes en estas ofertas:
- descripcion (100% vacías)
- modalidad_trabajo (100% vacías)
- tipo_trabajo (100% vacías)
- id_empresa (100% NULL)
- fecha_modificado_original (97% vacías)

Uso:
    python delete_incomplete_ofertas_nov3.py [--dry-run]

Autor: Claude Code (OEDE)
Fecha: 2025-11-03
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path a la base de datos
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


def main(dry_run=False):
    """
    Elimina ofertas del 3 de noviembre con datos incompletos

    Args:
        dry_run: Si es True, solo muestra qué se eliminaría sin hacer cambios
    """

    logger.info("="*80)
    logger.info("LIMPIEZA DE DATOS - Ofertas defectuosas del 3 de noviembre 2025")
    logger.info("="*80)
    logger.info("")

    if dry_run:
        logger.info("MODO DRY-RUN: No se realizarán cambios en la base de datos")
        logger.info("")

    # Conectar a base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # PASO 1: Contar total antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_antes = cursor.fetchone()[0]
        logger.info(f"Total ofertas en BD (antes): {total_antes:,}")

        cursor.execute("SELECT COUNT(*) FROM ofertas_raw")
        total_antes_v2 = cursor.fetchone()[0]
        logger.info(f"Total ofertas en BD v2 (antes): {total_antes_v2:,}")
        logger.info("")

        # PASO 2: Identificar ofertas a eliminar
        query_identificar = """
            SELECT
                id_oferta,
                titulo,
                empresa,
                scrapeado_en,
                CASE WHEN descripcion IS NULL OR descripcion = '' THEN 1 ELSE 0 END as desc_vacia,
                CASE WHEN modalidad_trabajo IS NULL OR modalidad_trabajo = '' THEN 1 ELSE 0 END as modal_vacia,
                CASE WHEN tipo_trabajo IS NULL OR tipo_trabajo = '' THEN 1 ELSE 0 END as tipo_vacio,
                CASE WHEN id_empresa IS NULL THEN 1 ELSE 0 END as id_empresa_null
            FROM ofertas
            WHERE DATE(scrapeado_en) = '2025-11-03'
        """

        cursor.execute(query_identificar)
        ofertas_a_eliminar = cursor.fetchall()

        if not ofertas_a_eliminar:
            logger.info("✓ No se encontraron ofertas del 3 de noviembre para eliminar")
            return

        logger.info(f"Ofertas del 3/11 encontradas: {len(ofertas_a_eliminar):,}")
        logger.info("")

        # Analizar campos vacíos
        total = len(ofertas_a_eliminar)
        desc_vacias = sum(1 for o in ofertas_a_eliminar if o[4] == 1)
        modal_vacias = sum(1 for o in ofertas_a_eliminar if o[5] == 1)
        tipo_vacias = sum(1 for o in ofertas_a_eliminar if o[6] == 1)
        id_empresa_null = sum(1 for o in ofertas_a_eliminar if o[7] == 1)

        logger.info("Análisis de campos vacíos:")
        logger.info(f"  - descripcion vacía: {desc_vacias}/{total} ({desc_vacias/total*100:.1f}%)")
        logger.info(f"  - modalidad_trabajo vacía: {modal_vacias}/{total} ({modal_vacias/total*100:.1f}%)")
        logger.info(f"  - tipo_trabajo vacío: {tipo_vacias}/{total} ({tipo_vacias/total*100:.1f}%)")
        logger.info(f"  - id_empresa NULL: {id_empresa_null}/{total} ({id_empresa_null/total*100:.1f}%)")
        logger.info("")

        # Mostrar muestra de ofertas a eliminar
        logger.info("Muestra de ofertas a eliminar (primeras 5):")
        for i, oferta in enumerate(ofertas_a_eliminar[:5], 1):
            id_oferta, titulo, empresa, scrapeado, *flags = oferta
            logger.info(f"  {i}. ID={id_oferta} - {titulo[:50]}... ({empresa})")

        if len(ofertas_a_eliminar) > 5:
            logger.info(f"  ... y {len(ofertas_a_eliminar) - 5} más")

        logger.info("")

        if dry_run:
            logger.info("="*80)
            logger.info("DRY-RUN COMPLETADO")
            logger.info("="*80)
            logger.info(f"Se eliminarían {len(ofertas_a_eliminar):,} ofertas")
            logger.info(f"Total resultante: {total_antes - len(ofertas_a_eliminar):,} ofertas")
            return

        # PASO 3: Eliminar de v1 (ofertas)
        logger.info("="*80)
        logger.info("ELIMINANDO de tabla ofertas (v1)...")
        logger.info("="*80)

        delete_v1_query = """
            DELETE FROM ofertas
            WHERE DATE(scrapeado_en) = '2025-11-03'
        """

        cursor.execute(delete_v1_query)
        deleted_v1 = cursor.rowcount
        logger.info(f"✓ Eliminadas {deleted_v1:,} ofertas de v1")

        # PASO 4: Eliminar de v2 (ofertas_raw)
        logger.info("")
        logger.info("ELIMINANDO de tabla ofertas_raw (v2)...")

        delete_v2_query = """
            DELETE FROM ofertas_raw
            WHERE DATE(scrapeado_en) = '2025-11-03'
        """

        cursor.execute(delete_v2_query)
        deleted_v2 = cursor.rowcount
        logger.info(f"✓ Eliminadas {deleted_v2:,} ofertas de v2")

        # PASO 5: Commit
        logger.info("")
        logger.info("Aplicando cambios (COMMIT)...")
        conn.commit()
        logger.info("✓ Cambios aplicados")

        # PASO 6: Verificar resultado
        logger.info("")
        logger.info("="*80)
        logger.info("VERIFICACIÓN POST-ELIMINACIÓN")
        logger.info("="*80)

        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_despues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ofertas_raw")
        total_despues_v2 = cursor.fetchone()[0]

        # Verificar que no queden ofertas del 3/11
        cursor.execute("SELECT COUNT(*) FROM ofertas WHERE DATE(scrapeado_en) = '2025-11-03'")
        quedan = cursor.fetchone()[0]

        logger.info(f"Total ofertas v1 (después): {total_despues:,}")
        logger.info(f"Total ofertas v2 (después): {total_despues_v2:,}")
        logger.info(f"Ofertas del 3/11 restantes: {quedan}")
        logger.info("")

        if quedan == 0:
            logger.info("✓ LIMPIEZA COMPLETADA EXITOSAMENTE")
        else:
            logger.warning(f"⚠️ ADVERTENCIA: Aún quedan {quedan} ofertas del 3/11")

        logger.info("")
        logger.info("="*80)
        logger.info("RESUMEN")
        logger.info("="*80)
        logger.info(f"Ofertas eliminadas v1: {deleted_v1:,}")
        logger.info(f"Ofertas eliminadas v2: {deleted_v2:,}")
        logger.info(f"Total antes: {total_antes:,}")
        logger.info(f"Total después: {total_despues:,}")
        logger.info(f"Diferencia: {total_antes - total_despues:,}")
        logger.info("")
        logger.info("Razón de eliminación: Datos incompletos por bug en run_scheduler.py")
        logger.info("Bug corregido en: run_scheduler.py líneas 105-116")
        logger.info("")

    except Exception as e:
        logger.error("="*80)
        logger.error("ERROR DURANTE ELIMINACIÓN")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        logger.error("")
        logger.error("Realizando ROLLBACK...")
        conn.rollback()
        logger.error("✓ Cambios revertidos")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    # Detectar modo dry-run
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("")
        print("Ejecutando en modo DRY-RUN (sin cambios reales)")
        print("")
    else:
        print("")
        print("ADVERTENCIA: Esta operacion ELIMINARA datos de la base de datos")
        print("")
        print("Deseas continuar? (escribe 'SI' para confirmar)")
        respuesta = input("> ")

        if respuesta.strip().upper() != 'SI':
            print("")
            print("Operacion cancelada por el usuario")
            print("")
            sys.exit(0)

        print("")

    main(dry_run=dry_run)
