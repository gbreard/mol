#!/usr/bin/env python3
"""
ZonaJobs Scraping para VPS
==========================

Scrapea ZonaJobs via keyword strategy y guarda en la misma BD SQLite.
Diseñado para correr en el VPS junto con el scraper de Bumeran.

Uso:
    python3 scripts/scraping/run_zonajobs_vps.py
    python3 scripts/scraping/run_zonajobs_vps.py --estrategia completa
    python3 scripts/scraping/run_zonajobs_vps.py --no-incremental
"""

import sqlite3
import json
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "zonajobs" / "scrapers"))
sys.path.insert(0, str(BASE_DIR))

from database.colisiones_id import (
    asegurar_tabla as _asegurar_colisiones,
    registrar_si_cross_portal as _registrar_colision,
)

from zonajobs_scraper_v2 import ZonaJobsScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Nodo donde corre este runner (para la tabla colisiones_id)
NODO_COLISIONES = 'vps'

# Columnas para INSERT (debe coincidir con schema)
COLUMNAS = [
    'id_oferta', 'id_empresa', 'titulo', 'empresa', 'descripcion',
    'confidencial', 'localizacion', 'modalidad_trabajo', 'tipo_trabajo',
    'fecha_publicacion_original', 'fecha_hora_publicacion_original',
    'fecha_modificado_original', 'fecha_publicacion_iso',
    'fecha_hora_publicacion_iso', 'fecha_modificado_iso',
    'fecha_publicacion_datetime', 'fecha_hora_publicacion_datetime',
    'fecha_modificado_datetime', 'cantidad_vacantes', 'apto_discapacitado',
    'id_area', 'id_subarea', 'id_pais', 'logo_url', 'empresa_validada',
    'empresa_pro', 'promedio_empresa', 'plan_publicacion_id',
    'plan_publicacion_nombre', 'portal', 'tipo_aviso', 'tiene_preguntas',
    'salario_obligatorio', 'alta_revision_perfiles', 'guardado', 'gptw_url',
    'url_oferta', 'scrapeado_en'
]


def insertar_en_bd(ofertas: list, db_path: str) -> dict:
    """
    Inserta ofertas en la BD SQLite (INSERT OR IGNORE).

    Returns:
        Dict con estadísticas: insertadas, duplicadas, errores
    """
    conn = sqlite3.connect(db_path, timeout=30)
    cur = conn.cursor()
    _asegurar_colisiones(cur)

    cols_str = ', '.join(COLUMNAS)
    placeholders = ', '.join(['?'] * len(COLUMNAS))
    sql = f"INSERT OR IGNORE INTO ofertas ({cols_str}) VALUES ({placeholders})"

    insertadas = 0
    duplicadas = 0
    errores = 0

    for oferta in ofertas:
        try:
            valores = tuple(oferta.get(col) for col in COLUMNAS)
            cur.execute(sql, valores)
            if cur.rowcount > 0:
                insertadas += 1
            else:
                # rowcount 0: duplicado legitimo del mismo portal, o COLISION de id
                # entre portales (espacio de ids mal dimensionado). El SELECT del
                # portal existente ocurre solo aca, no en el camino de insercion.
                _registrar_colision(cur, valores[0], 'zonajobs', oferta, nodo=NODO_COLISIONES)
                duplicadas += 1
        except Exception as e:
            errores += 1
            if errores <= 5:
                logger.warning(f"Error insertando oferta {oferta.get('id_oferta')}: {e}")

    conn.commit()

    # Estadísticas
    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'zonajobs'")
    total_zj = cur.fetchone()[0]

    conn.close()

    return {
        'insertadas': insertadas,
        'duplicadas': duplicadas,
        'errores': errores,
        'total_bd': total,
        'total_zonajobs': total_zj
    }


def main():
    parser = argparse.ArgumentParser(description="ZonaJobs scraping para VPS")
    parser.add_argument('--estrategia', default='exhaustiva',
                       help='Estrategia de keywords (default: exhaustiva)')
    parser.add_argument('--no-incremental', action='store_true',
                       help='Desactivar modo incremental')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay entre requests (default: 0.5s)')
    parser.add_argument('--db', type=str,
                       default=str(BASE_DIR / 'database' / 'bumeran_scraping.db'),
                       help='Ruta a la BD SQLite')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("ZONAJOBS SCRAPING - VPS")
    logger.info("=" * 70)

    start = time.time()

    # Paso 1: Scrapear
    scraper = ZonaJobsScraper(delay_between_requests=args.delay)
    ofertas = scraper.scrapear_todo(
        estrategia=args.estrategia,
        incremental=not args.no_incremental
    )

    if not ofertas:
        logger.info("No se obtuvieron ofertas nuevas")
        return

    # Paso 2: Insertar en BD
    logger.info(f"Insertando {len(ofertas)} ofertas en BD...")
    stats = insertar_en_bd(ofertas, args.db)

    elapsed = time.time() - start

    logger.info("=" * 70)
    logger.info("RESULTADO FINAL")
    logger.info(f"  Scrapeadas: {len(ofertas)}")
    logger.info(f"  Insertadas: {stats['insertadas']}")
    logger.info(f"  Duplicadas: {stats['duplicadas']}")
    logger.info(f"  Errores: {stats['errores']}")
    logger.info(f"  Total en BD: {stats['total_bd']} ({stats['total_zonajobs']} ZonaJobs)")
    logger.info(f"  Tiempo: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
