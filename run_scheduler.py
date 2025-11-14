"""
Scheduler Automatizado - Bumeran Scraping
==========================================

Ejecuta scraping automático de Bumeran según calendario configurado.

Por defecto: Lunes y Jueves a las 8:00 AM (hora Argentina)

Uso:
    # Ejecutar scheduler (loop infinito)
    python run_scheduler.py

    # O dejar corriendo en background
    pythonw run_scheduler.py  # Windows (sin consola)

Configuración:
    Editar database/config.py para cambiar días/horarios
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path
import schedule

# Agregar paths necesarios
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "01_sources" / "bumeran" / "scrapers"))
sys.path.insert(0, str(PROJECT_ROOT))

# Imports del proyecto
from scrapear_con_diccionario import BumeranMultiSearch
from database.config import SCHEDULER_CONFIG, SCRAPING_CONFIG, DB_CONFIG
from database.db_manager import DatabaseManager

# =====================================================================
# LOGGING
# =====================================================================

# Configurar logging con rotación de archivos
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"scheduler_{datetime.now().strftime('%Y%m')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# =====================================================================
# FUNCIÓN DE SCRAPING
# =====================================================================

def ejecutar_scraping():
    """
    Ejecuta scraping completo y guarda resultados en PostgreSQL

    Esta función se ejecuta según el calendario configurado
    """
    logger.info("="*80)
    logger.info("INICIANDO SCRAPING PROGRAMADO")
    logger.info("="*80)

    start_time = datetime.now()

    try:
        # 1. Crear scraper con diccionario v3.2
        logger.info("Inicializando scraper con diccionario v3.2...")
        scraper = BumeranMultiSearch(
            delay_between_requests=SCRAPING_CONFIG['initial_delay'],
            delay_between_keywords=2.0
        )

        # 2. Scrapear ofertas usando estrategia del diccionario (modo incremental)
        logger.info("Iniciando scraping con estrategia ultra_exhaustiva_v3_2...")
        df_ofertas = scraper.scrapear_multiples_keywords(
            estrategia='ultra_exhaustiva_v3_2',
            max_paginas_por_keyword=1,
            page_size=SCRAPING_CONFIG['page_size'],
            incremental=SCRAPING_CONFIG['incremental'],
            date_window_days=0
        )

        logger.info(f"Scraping completado: {len(df_ofertas)} ofertas obtenidas")

        if len(df_ofertas) == 0:
            logger.warning("No se obtuvieron ofertas nuevas")
            return

        # 3. Guardar en CSV (backup local)
        logger.info("Guardando CSV de respaldo...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = scraper.guardar_resultados(df_ofertas, f"bumeran_auto_{timestamp}")
        logger.info(f"Archivos guardados: {', '.join(files)}")

        # 4. Procesar ofertas (agregar fechas normalizadas y campos adicionales)
        logger.info("Procesando fechas y campos adicionales...")
        ofertas_list = df_ofertas.to_dict('records')
        df_ofertas_procesadas = scraper.scraper.procesar_ofertas(ofertas_list)
        logger.info(f"Ofertas procesadas con fechas: {len(df_ofertas_procesadas)}")

        # 5. Guardar en SQLite
        logger.info("Guardando en SQLite...")

        with DatabaseManager(**DB_CONFIG) as db:
            # Insertar ofertas procesadas (con fechas normalizadas)
            ofertas_insertadas = db.insert_ofertas(df_ofertas_procesadas)
            logger.info(f"Ofertas insertadas/actualizadas: {ofertas_insertadas}")

            # TODO: Agregar métricas y alertas cuando BumeranMultiSearch las implemente
            # Por ahora solo guardamos las ofertas

            # Verificar total en DB
            total_ofertas_db = db.get_ofertas_count()
            logger.info(f"Total ofertas en DB: {total_ofertas_db:,}")

        # Fin
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("="*80)
        logger.info(f"SCRAPING COMPLETADO EXITOSAMENTE - {duration/60:.2f} minutos")
        logger.info("="*80)

    except Exception as e:
        logger.error("="*80)
        logger.error("ERROR DURANTE SCRAPING PROGRAMADO")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        logger.error("Scraping fallido, se reintentará en el próximo horario programado")


# =====================================================================
# SCHEDULER
# =====================================================================

def configurar_schedule():
    """
    Configura el scheduler según SCHEDULER_CONFIG

    Días: 0=lunes, 1=martes, ..., 6=domingo
    """
    dias_nombres = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    hora = f"{SCHEDULER_CONFIG['hour']:02d}:{SCHEDULER_CONFIG['minute']:02d}"

    logger.info("="*80)
    logger.info("CONFIGURACIÓN DEL SCHEDULER")
    logger.info("="*80)

    for dia_num in SCHEDULER_CONFIG['days_of_week']:
        dia_nombre = dias_nombres[dia_num]

        # Mapeo día número → función schedule
        dia_funcs = [
            schedule.every().monday,
            schedule.every().tuesday,
            schedule.every().wednesday,
            schedule.every().thursday,
            schedule.every().friday,
            schedule.every().saturday,
            schedule.every().sunday,
        ]

        # Programar scraping
        dia_funcs[dia_num].at(hora).do(ejecutar_scraping)

        logger.info(f"  • {dia_nombre.capitalize()} a las {hora}")

    logger.info(f"  • Timezone: {SCHEDULER_CONFIG['timezone']}")
    logger.info("="*80)
    logger.info("")


def main():
    """Función principal del scheduler"""
    print("="*80)
    print("SCHEDULER - BUMERAN SCRAPING")
    print("="*80)
    print()
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Configurar schedule
    configurar_schedule()

    # Mensaje de inicio
    logger.info("Scheduler iniciado - Esperando próximo horario programado...")
    logger.info("Presiona Ctrl+C para detener")
    print()

    # Loop principal
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto

    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*80)
        logger.info("SCHEDULER DETENIDO POR USUARIO")
        logger.info("="*80)
        logger.info(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# =====================================================================
# TESTING MANUAL
# =====================================================================

def test_scraping_now():
    """
    Ejecuta scraping inmediatamente (para testing)

    Uso:
        python run_scheduler.py --test
    """
    print("="*80)
    print("TEST MODE - Ejecutando scraping inmediatamente")
    print("="*80)
    print()

    ejecutar_scraping()

    print()
    print("="*80)
    print("TEST COMPLETADO")
    print("="*80)


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    """Punto de entrada del scheduler"""

    # Verificar modo test
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_scraping_now()
    else:
        main()
