"""
Scraping Completo de Bumeran - Validación de Producción
=========================================================

Ejecuta scraping de TODAS las ofertas disponibles (~12,000)
para validar optimizaciones de Fase 1+2+3 a escala real.

Uso:
    python run_scraping_completo.py
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging más detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Importar scraper
sys.path.insert(0, str(Path(__file__).parent))
from bumeran_scraper import BumeranScraper

def main():
    """Ejecuta scraping completo de Bumeran"""

    print("="*80)
    print("SCRAPING COMPLETO DE BUMERAN - VALIDACION DE PRODUCCION")
    print("="*80)
    print()
    print("Este script va a:")
    print("  1. Scrapear TODAS las ofertas disponibles (~12,000)")
    print("  2. Usar modo incremental (solo ofertas nuevas)")
    print("  3. Validar optimizaciones de Fase 1+2+3 a escala real")
    print("  4. Generar métricas completas de performance")
    print("  5. Guardar datos en todos los formatos (CSV, JSON, Excel)")
    print()
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Confirmar ejecución
    response = input("¿Continuar? (s/n): ").lower()
    if response != 's':
        print("Cancelado por usuario")
        return

    print()
    print("-"*80)
    print()

    try:
        # Crear scraper con optimizaciones de Fase 3
        logger.info("Inicializando scraper...")
        scraper = BumeranScraper(delay_between_requests=2.0)

        # Scrapear TODO (incremental)
        logger.info("Iniciando scraping completo...")
        start_time = datetime.now()

        ofertas = scraper.scrapear_todo(
            max_paginas=None,  # TODAS las páginas
            max_resultados=None,  # TODOS los resultados
            page_size=20,  # 20 ofertas por página (estándar)
            incremental=True  # Solo nuevas
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Resultados
        print()
        print("="*80)
        print("RESUMEN DE SCRAPING")
        print("="*80)
        print(f"Inicio:           {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Fin:              {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duración:         {duration:.2f}s ({duration/60:.2f} min)")
        print(f"Ofertas obtenidas: {len(ofertas):,}")

        if len(ofertas) > 0:
            print(f"Velocidad:        {len(ofertas)/duration:.2f} ofertas/segundo")
            print()

            # Guardar en todos los formatos
            logger.info("Guardando datos en todos los formatos...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"bumeran_completo_{timestamp}"

            files = scraper.save_all_formats(ofertas, base_filename)

            print("Archivos generados:")
            for fmt, filepath in files.items():
                print(f"  {fmt.upper():8s}: {filepath}")

            print()
            print("="*80)
            print(f"SCRAPING COMPLETADO EXITOSAMENTE - {len(ofertas):,} OFERTAS")
            print("="*80)

        else:
            print()
            print("ADVERTENCIA: No se obtuvieron ofertas nuevas")
            print("  - Posible causa: Todas las ofertas ya fueron scrapeadas (modo incremental)")
            print("  - Solución: Ejecutar con incremental=False para scrapear todo de nuevo")

        print()

    except KeyboardInterrupt:
        print()
        print("="*80)
        print("SCRAPING INTERRUMPIDO POR USUARIO")
        print("="*80)
        logger.warning("Scraping interrumpido por usuario (Ctrl+C)")

    except Exception as e:
        print()
        print("="*80)
        print("ERROR DURANTE SCRAPING")
        print("="*80)
        print(f"Error: {e}")
        logger.error(f"Error durante scraping: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
