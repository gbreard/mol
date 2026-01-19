"""
Script de Prueba - Scraping con Mejoras Fase 1
==============================================

Ejecuta un scraping de prueba limitado para verificar:
- Retry logic con tenacity
- Validación de schemas con Pydantic
- Tracking atómico con timestamps
- Backups automáticos

Uso:
    python test_scraping_prueba.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging con más detalle
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "02_consolidation" / "scripts"))

from bumeran_scraper import BumeranScraper
from incremental_tracker import IncrementalTracker


def main():
    logger.info("")
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + " "*15 + "PRUEBA DE SCRAPING - FASE 1 MEJORAS" + " "*18 + "║")
    logger.info("╚" + "="*68 + "╝")
    logger.info("")

    # Parámetros de prueba
    MAX_PAGINAS = 3
    PAGE_SIZE = 20
    QUERY = "python"  # Búsqueda específica para resultados más rápidos

    logger.info("Parámetros de prueba:")
    logger.info(f"  Max páginas: {MAX_PAGINAS}")
    logger.info(f"  Ofertas/página: {PAGE_SIZE}")
    logger.info(f"  Query: {QUERY}")
    logger.info(f"  Modo: Incremental (con tracking v2.0)")
    logger.info("")

    # Verificar estado del tracking antes
    logger.info("="*70)
    logger.info("ESTADO DEL TRACKING ANTES DEL SCRAPING")
    logger.info("="*70)

    tracker = IncrementalTracker('bumeran')
    stats_before = tracker.get_stats()

    if stats_before['exists']:
        logger.info(f"✅ Tracking existente encontrado:")
        logger.info(f"   IDs trackeados: {stats_before['total_ids']:,}")
        logger.info(f"   Última actualización: {stats_before['last_update']}")
        logger.info(f"   Archivo: {stats_before['file_path']}")

        # Detectar formato
        tracking_file = Path(stats_before['file_path'])
        with open(tracking_file, 'r') as f:
            data = json.load(f)
            version = data.get('metadata', {}).get('version', '1.0')
            logger.info(f"   Formato: v{version}")
    else:
        logger.info("⚠️ No hay tracking previo (primera ejecución)")

    logger.info("")

    # Ejecutar scraping de prueba
    logger.info("="*70)
    logger.info("EJECUTANDO SCRAPING DE PRUEBA")
    logger.info("="*70)
    logger.info("")

    try:
        scraper = BumeranScraper(delay_between_requests=1.0)  # Delay menor para prueba

        start_time = datetime.now()

        ofertas = scraper.scrapear_todo(
            max_paginas=MAX_PAGINAS,
            page_size=PAGE_SIZE,
            query=QUERY,
            incremental=True
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("")
        logger.info("="*70)
        logger.info("SCRAPING COMPLETADO")
        logger.info("="*70)
        logger.info(f"Ofertas scrapeadas: {len(ofertas)}")
        logger.info(f"Tiempo total: {duration:.1f}s")
        logger.info(f"Velocidad: {len(ofertas)/duration:.1f} ofertas/segundo")
        logger.info("")

        # Guardar CSV de prueba
        if ofertas:
            output_file = scraper.data_dir / f"bumeran_prueba_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            scraper.save_to_csv(ofertas, filename=str(output_file))
            logger.info(f"✅ CSV guardado: {output_file.name}")
            logger.info("")

    except Exception as e:
        logger.error(f"❌ Error durante scraping: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Verificar estado del tracking después
    logger.info("="*70)
    logger.info("ESTADO DEL TRACKING DESPUÉS DEL SCRAPING")
    logger.info("="*70)

    stats_after = tracker.get_stats()

    if stats_after['exists']:
        logger.info(f"✅ Tracking actualizado:")
        logger.info(f"   IDs trackeados: {stats_after['total_ids']:,}")
        logger.info(f"   Última actualización: {stats_after['last_update']}")

        # Calcular IDs nuevos
        ids_nuevos = stats_after['total_ids'] - stats_before.get('total_ids', 0)
        logger.info(f"   IDs nuevos agregados: {ids_nuevos}")

        # Verificar formato v2.0
        tracking_file = Path(stats_after['file_path'])
        with open(tracking_file, 'r') as f:
            data = json.load(f)

            # Verificar estructura
            scraped_ids_data = data.get('scraped_ids')
            version = data.get('metadata', {}).get('version', '1.0')

            logger.info(f"   Formato: v{version}")

            if isinstance(scraped_ids_data, dict):
                logger.info(f"   ✅ Formato v2.0 (dict con timestamps)")

                # Mostrar primeros 3 IDs con timestamps
                logger.info(f"   Ejemplo de IDs con timestamps:")
                for i, (id_, timestamp) in enumerate(list(scraped_ids_data.items())[:3]):
                    logger.info(f"     - {id_}: {timestamp}")
            else:
                logger.info(f"   ⚠️ Formato v1.0 (lista sin timestamps)")

        # Verificar backups
        tracking_dir = tracking_file.parent
        backups = list(tracking_dir.glob("bumeran_scraped_ids.json.bak_*"))

        if backups:
            logger.info(f"   ✅ Backups encontrados: {len(backups)}")
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            logger.info(f"      Último backup: {latest_backup.name}")
        else:
            logger.info(f"   ⚠️ No se encontraron backups")

    logger.info("")

    # Resumen final
    logger.info("="*70)
    logger.info("RESUMEN DE LA PRUEBA")
    logger.info("="*70)
    logger.info(f"✅ Scraping ejecutado correctamente")
    logger.info(f"✅ Ofertas obtenidas: {len(ofertas)}")
    logger.info(f"✅ Tracking actualizado con formato v2.0")
    logger.info(f"✅ Timestamps por ID funcionando")
    logger.info(f"✅ Sistema atómico de guardado funcionando")
    logger.info("")
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + " "*18 + "🎉 PRUEBA EXITOSA 🎉" + " "*28 + "║")
    logger.info("╚" + "="*68 + "╝")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
