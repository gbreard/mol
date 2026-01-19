"""
Script de Verificación de Calidad de Datos
==========================================

Verifica la calidad de los datos en la base de datos de ofertas,
identificando ofertas con campos críticos vacíos o incompletos.

Uso:
    python verify_data_quality.py [--detailed]

Opciones:
    --detailed    Muestra lista detallada de ofertas con problemas

Autor: Claude Code (OEDE)
Fecha: 2025-11-03
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path a la base de datos
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


def verificar_calidad_ofertas(conn: sqlite3.Connection, detailed: bool = False) -> Dict:
    """
    Verifica la calidad de las ofertas en la base de datos

    Args:
        conn: Conexión a la base de datos
        detailed: Si True, muestra ofertas problemáticas en detalle

    Returns:
        Dict con estadísticas de calidad
    """
    cursor = conn.cursor()

    # Total de ofertas
    cursor.execute("SELECT COUNT(*) FROM ofertas")
    total_ofertas = cursor.fetchone()[0]

    # Campos críticos a verificar
    campos_criticos = {
        'titulo': 'Título',
        'descripcion': 'Descripción',
        'empresa': 'Empresa',
        'modalidad_trabajo': 'Modalidad de Trabajo',
        'tipo_trabajo': 'Tipo de Trabajo',
        'id_empresa': 'ID Empresa'
    }

    stats = {
        'total_ofertas': total_ofertas,
        'ofertas_completas': 0,
        'ofertas_incompletas': 0,
        'campos_vacios': {},
        'ofertas_problematicas': []
    }

    # Verificar cada campo crítico
    logger.info("")
    logger.info("="*80)
    logger.info("VERIFICACIÓN DE CAMPOS CRÍTICOS")
    logger.info("="*80)

    for campo_db, campo_nombre in campos_criticos.items():
        # Contar campos vacíos o NULL
        if campo_db == 'id_empresa':
            # Para id_empresa, solo verificar NULL
            query = f"SELECT COUNT(*) FROM ofertas WHERE {campo_db} IS NULL"
        else:
            # Para campos de texto, verificar NULL o vacío
            query = f"""
                SELECT COUNT(*) FROM ofertas
                WHERE {campo_db} IS NULL OR {campo_db} = ''
            """

        cursor.execute(query)
        vacios = cursor.fetchone()[0]
        porcentaje = (vacios / total_ofertas * 100) if total_ofertas > 0 else 0

        stats['campos_vacios'][campo_db] = {
            'vacios': vacios,
            'porcentaje': porcentaje
        }

        # Mostrar resultado con color según calidad
        if porcentaje == 0:
            estado = "✓ PERFECTO"
        elif porcentaje < 1:
            estado = "⚠ BIEN (pocos vacíos)"
        elif porcentaje < 5:
            estado = "⚠ ACEPTABLE"
        else:
            estado = "❌ CRÍTICO"

        logger.info(
            f"  {campo_nombre:25} {estado:20} "
            f"{vacios:5,} vacíos ({porcentaje:5.1f}%)"
        )

    logger.info("")

    # Identificar ofertas con múltiples campos vacíos
    query_problematicas = """
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
        WHERE
            (descripcion IS NULL OR descripcion = '')
            OR (modalidad_trabajo IS NULL OR modalidad_trabajo = '')
            OR (tipo_trabajo IS NULL OR tipo_trabajo = '')
            OR (id_empresa IS NULL)
    """

    cursor.execute(query_problematicas)
    ofertas_problematicas = cursor.fetchall()

    stats['ofertas_incompletas'] = len(ofertas_problematicas)
    stats['ofertas_completas'] = total_ofertas - stats['ofertas_incompletas']

    # Analizar ofertas problemáticas por fecha
    if ofertas_problematicas:
        ofertas_por_fecha = {}

        for oferta in ofertas_problematicas:
            id_oferta, titulo, empresa, scrapeado_en, desc_vacia, modal_vacia, tipo_vacio, id_null = oferta
            fecha_scrapeo = scrapeado_en[:10] if scrapeado_en else 'DESCONOCIDA'

            if fecha_scrapeo not in ofertas_por_fecha:
                ofertas_por_fecha[fecha_scrapeo] = 0
            ofertas_por_fecha[fecha_scrapeo] += 1

            # Guardar para reporte detallado
            campos_problematicos = []
            if desc_vacia:
                campos_problematicos.append('descripcion')
            if modal_vacia:
                campos_problematicos.append('modalidad_trabajo')
            if tipo_vacio:
                campos_problematicos.append('tipo_trabajo')
            if id_null:
                campos_problematicos.append('id_empresa')

            stats['ofertas_problematicas'].append({
                'id_oferta': id_oferta,
                'titulo': titulo,
                'empresa': empresa,
                'scrapeado_en': scrapeado_en,
                'campos_vacios': campos_problematicos
            })

        stats['ofertas_por_fecha'] = ofertas_por_fecha

    return stats


def mostrar_reporte(stats: Dict, detailed: bool = False):
    """
    Muestra reporte de calidad de datos

    Args:
        stats: Diccionario con estadísticas
        detailed: Si True, muestra ofertas problemáticas en detalle
    """
    logger.info("="*80)
    logger.info("RESUMEN DE CALIDAD DE DATOS")
    logger.info("="*80)
    logger.info("")

    total = stats['total_ofertas']
    completas = stats['ofertas_completas']
    incompletas = stats['ofertas_incompletas']

    logger.info(f"Total de ofertas:       {total:,}")
    logger.info(f"Ofertas completas:      {completas:,} ({completas/total*100:.1f}%)")
    logger.info(f"Ofertas incompletas:    {incompletas:,} ({incompletas/total*100:.1f}%)")
    logger.info("")

    # Estado general de calidad
    if incompletas == 0:
        logger.info("✓✓✓ CALIDAD EXCELENTE: Todas las ofertas tienen campos completos")
    elif incompletas / total < 0.01:
        logger.info("✓✓ CALIDAD BUENA: Menos del 1% de ofertas incompletas")
    elif incompletas / total < 0.05:
        logger.info("✓ CALIDAD ACEPTABLE: Menos del 5% de ofertas incompletas")
    else:
        logger.info("❌ CALIDAD CRÍTICA: Más del 5% de ofertas incompletas")

    logger.info("")

    # Distribución por fecha de scraping
    if incompletas > 0 and 'ofertas_por_fecha' in stats:
        logger.info("="*80)
        logger.info("DISTRIBUCIÓN DE OFERTAS INCOMPLETAS POR FECHA DE SCRAPING")
        logger.info("="*80)
        logger.info("")

        for fecha, count in sorted(stats['ofertas_por_fecha'].items()):
            logger.info(f"  {fecha}:  {count:,} ofertas incompletas")

        logger.info("")

    # Muestra detallada si se solicita
    if detailed and incompletas > 0:
        logger.info("="*80)
        logger.info("DETALLE DE OFERTAS INCOMPLETAS (primeras 20)")
        logger.info("="*80)
        logger.info("")

        for i, oferta in enumerate(stats['ofertas_problematicas'][:20], 1):
            logger.info(f"  {i}. ID: {oferta['id_oferta']}")
            logger.info(f"     Título: {oferta['titulo'][:60]}...")
            logger.info(f"     Empresa: {oferta['empresa']}")
            logger.info(f"     Scrapeado: {oferta['scrapeado_en']}")
            logger.info(f"     Campos vacíos: {', '.join(oferta['campos_vacios'])}")
            logger.info("")

        if len(stats['ofertas_problematicas']) > 20:
            logger.info(f"  ... y {len(stats['ofertas_problematicas']) - 20} más")
            logger.info("")


def verificar_fechas(conn: sqlite3.Connection):
    """
    Verifica que las fechas estén correctamente normalizadas

    Args:
        conn: Conexión a la base de datos
    """
    cursor = conn.cursor()

    logger.info("="*80)
    logger.info("VERIFICACIÓN DE FECHAS")
    logger.info("="*80)
    logger.info("")

    # Verificar fecha_publicacion_iso
    cursor.execute("""
        SELECT COUNT(*) FROM ofertas
        WHERE fecha_publicacion_iso IS NULL OR fecha_publicacion_iso = ''
    """)
    sin_fecha_pub = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ofertas")
    total = cursor.fetchone()[0]

    if sin_fecha_pub == 0:
        logger.info("✓ fecha_publicacion_iso:  PERFECTO - Todas las ofertas tienen fecha")
    else:
        porcentaje = sin_fecha_pub / total * 100
        logger.info(
            f"⚠ fecha_publicacion_iso:  {sin_fecha_pub:,} ofertas sin fecha ({porcentaje:.1f}%)"
        )

    logger.info("")


def main(detailed: bool = False):
    """
    Función principal de verificación

    Args:
        detailed: Mostrar detalles de ofertas problemáticas
    """
    logger.info("="*80)
    logger.info("VERIFICACIÓN DE CALIDAD DE DATOS - Bumeran Scraping")
    logger.info("="*80)
    logger.info("")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Base de datos: {DB_PATH}")
    logger.info("")

    if not DB_PATH.exists():
        logger.error(f"❌ ERROR: Base de datos no encontrada en {DB_PATH}")
        return 1

    # Conectar a base de datos
    conn = sqlite3.connect(DB_PATH)

    try:
        # Verificar calidad de ofertas
        stats = verificar_calidad_ofertas(conn, detailed)

        # Verificar fechas
        verificar_fechas(conn)

        # Mostrar reporte
        mostrar_reporte(stats, detailed)

        # Código de salida según calidad
        if stats['ofertas_incompletas'] == 0:
            logger.info("✓ VERIFICACIÓN COMPLETADA: Base de datos en perfecto estado")
            return 0
        elif stats['ofertas_incompletas'] / stats['total_ofertas'] < 0.01:
            logger.info("✓ VERIFICACIÓN COMPLETADA: Calidad de datos buena")
            return 0
        else:
            logger.warning("⚠ VERIFICACIÓN COMPLETADA: Se encontraron problemas de calidad")
            return 1

    except Exception as e:
        logger.error("="*80)
        logger.error("ERROR DURANTE VERIFICACIÓN")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        return 2

    finally:
        conn.close()


if __name__ == "__main__":
    # Detectar modo detallado
    detailed = '--detailed' in sys.argv

    # Ejecutar verificación
    exit_code = main(detailed)

    logger.info("")
    logger.info("="*80)

    sys.exit(exit_code)
