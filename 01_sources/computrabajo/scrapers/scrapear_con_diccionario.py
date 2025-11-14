"""
Scraper de ComputRabajo usando diccionario de búsquedas
=======================================================

ComputRabajo requiere keywords específicas para mostrar ofertas.
Este script itera por un diccionario de búsquedas y consolida resultados.
"""

import json
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path
import time
from computrabajo_scraper import ComputRabajoScraper
import logging

# Agregar paths para imports
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
config_scripts = project_root / "data" / "config"

for path in [consolidation_scripts, config_scripts]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar tracker e keywords_loader
try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    logger.warning(f"No se pudo importar IncrementalTracker: {e}")
    logger.warning("Modo incremental deshabilitado")
    IncrementalTracker = None

try:
    from keywords_loader import load_keywords, get_available_strategies
except ImportError as e:
    logger.warning(f"No se pudo importar keywords_loader: {e}")
    logger.warning("Usando diccionario local como fallback")
    load_keywords = None
    get_available_strategies = None

try:
    from date_filter import filter_by_date_window
except ImportError as e:
    logger.warning(f"No se pudo importar date_filter: {e}")
    logger.warning("Filtrado por fecha deshabilitado")
    filter_by_date_window = None


class ComputRabajoMultiSearch:
    """Scraper multi-keyword para ComputRabajo"""

    def __init__(self, delay_between_requests=2.0, delay_between_keywords=5.0):
        """
        Args:
            delay_between_requests: Delay entre páginas (default: 2s)
            delay_between_keywords: Delay entre keywords (default: 5s)
        """
        self.scraper = ComputRabajoScraper(delay_between_requests)
        self.delay_keywords = delay_between_keywords
        # Diccionario local como fallback (legacy)
        self.keywords_config_path = Path(__file__).parent.parent / "config" / "search_keywords.json"

    def cargar_keywords(self, estrategia="general"):
        """
        Carga keywords desde el diccionario maestro centralizado

        Args:
            estrategia: Nombre de la estrategia (maxima, completa, general, tecnologia, etc.)

        Returns:
            Lista de keywords
        """
        # Intentar usar diccionario maestro centralizado
        if load_keywords is not None:
            try:
                keywords = load_keywords(estrategia)
                logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}' (diccionario MAESTRO)")
                return keywords
            except Exception as e:
                logger.warning(f"Error cargando diccionario maestro: {e}")
                logger.warning("Usando diccionario local como fallback")

        # Fallback a diccionario local (legacy)
        with open(self.keywords_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if estrategia not in config['estrategias']:
            raise ValueError(f"Estrategia '{estrategia}' no encontrada. Disponibles: {list(config['estrategias'].keys())}")

        keywords = config['estrategias'][estrategia]['keywords']
        logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}' (diccionario LOCAL)")

        return keywords

    def scrapear_multiples_keywords(
        self,
        keywords=None,
        estrategia="general",
        max_paginas_por_keyword=5,
        max_resultados_por_keyword=100,
        incremental=True,
        date_window_days=7
    ):
        """
        Scrapea múltiples keywords y consolida resultados

        Args:
            keywords: Lista de keywords (None = usar estrategia)
            estrategia: Estrategia a usar si keywords=None
            max_paginas_por_keyword: Páginas por keyword (default: 5)
            max_resultados_por_keyword: Resultados por keyword (default: 100)
            incremental: Si True, solo trae ofertas nuevas (default: True)
            date_window_days: Ventana temporal en días (default: 7, 0=sin filtro)

        Returns:
            DataFrame consolidado sin duplicados, filtrado por fecha
        """
        # Cargar keywords
        if keywords is None:
            keywords = self.cargar_keywords(estrategia)

        logger.info("="*70)
        logger.info("SCRAPING MULTI-KEYWORD - COMPUTRABAJO")
        logger.info("="*70)
        logger.info(f"Keywords a scrapear: {len(keywords)}")
        logger.info(f"Max paginas por keyword: {max_paginas_por_keyword}")
        logger.info(f"Max resultados por keyword: {max_resultados_por_keyword}")
        logger.info(f"Delay entre keywords: {self.delay_keywords}s")
        logger.info(f"Modo: {'Incremental' if incremental else 'Full'}")
        logger.info(f"Ventana temporal: {date_window_days} días" if date_window_days > 0 else "Ventana temporal: deshabilitada")
        logger.info("")

        # Inicializar tracker si modo incremental
        tracker = None
        existing_ids = set()
        if incremental:
            if IncrementalTracker is None:
                logger.warning("IncrementalTracker no disponible, ejecutando en modo full")
                incremental = False
            else:
                tracker = IncrementalTracker(source='computrabajo')
                existing_ids = tracker.load_scraped_ids()
                if existing_ids:
                    logger.info(f"Modo incremental: {len(existing_ids):,} IDs ya scrapeados")
                else:
                    logger.info("Primera ejecución: scrapeando TODO")
                logger.info("")

        todas_ofertas = []
        estadisticas = {
            'keywords_procesadas': 0,
            'keywords_exitosas': 0,
            'keywords_sin_resultados': 0,
            'ofertas_totales_brutas': 0,
            'ofertas_despues_dedup': 0
        }

        # Scrapear cada keyword
        for i, keyword in enumerate(keywords, 1):
            logger.info(f"\n[{i}/{len(keywords)}] Scrapeando keyword: '{keyword}'")

            try:
                ofertas = self.scraper.scrapear_todo(
                    max_paginas=max_paginas_por_keyword,
                    max_resultados=max_resultados_por_keyword,
                    query=keyword
                )

                if ofertas:
                    # Agregar keyword usada a cada oferta
                    for oferta in ofertas:
                        oferta['keyword_busqueda'] = keyword

                    todas_ofertas.extend(ofertas)
                    estadisticas['keywords_exitosas'] += 1
                    logger.info(f"  OK - {len(ofertas)} ofertas encontradas")
                else:
                    estadisticas['keywords_sin_resultados'] += 1
                    logger.warning(f"  WARNING - Sin resultados")

                estadisticas['keywords_procesadas'] += 1

            except Exception as e:
                logger.error(f"  ERROR - {e}")
                continue

            # Delay entre keywords (excepto última)
            if i < len(keywords):
                logger.debug(f"  Esperando {self.delay_keywords}s antes de siguiente keyword...")
                time.sleep(self.delay_keywords)

        # Consolidar y deduplicar
        logger.info("\n" + "="*70)
        logger.info("CONSOLIDANDO RESULTADOS")
        logger.info("="*70)

        estadisticas['ofertas_totales_brutas'] = len(todas_ofertas)
        logger.info(f"Ofertas totales (con duplicados): {estadisticas['ofertas_totales_brutas']}")

        if not todas_ofertas:
            logger.warning("No se encontraron ofertas")
            return pd.DataFrame()

        # Convertir a DataFrame
        df = pd.DataFrame(todas_ofertas)

        # Deduplicar por id_oferta (puede aparecer en múltiples keywords)
        df_dedup = df.drop_duplicates(subset='id_oferta', keep='first')
        estadisticas['ofertas_despues_dedup'] = len(df_dedup)

        duplicados_removidos = estadisticas['ofertas_totales_brutas'] - estadisticas['ofertas_despues_dedup']
        logger.info(f"Ofertas únicas (sin duplicados): {estadisticas['ofertas_despues_dedup']}")
        logger.info(f"Duplicados removidos: {duplicados_removidos}")

        # Aplicar filtro de fecha si está habilitado
        df_filtered = df_dedup
        if date_window_days > 0 and filter_by_date_window is not None:
            logger.info(f"\nAplicando filtro temporal: últimos {date_window_days} días")
            df_filtered = filter_by_date_window(
                df_dedup,
                date_column='fecha_publicacion',
                days=date_window_days,
                verbose=True
            )
            estadisticas['ofertas_despues_filtro_fecha'] = len(df_filtered)
        elif date_window_days > 0:
            logger.warning("Filtro de fecha deshabilitado (date_filter no importado)")
        else:
            logger.info("Filtro de fecha deshabilitado (date_window_days=0)")

        # Filtrar ofertas nuevas si modo incremental
        df_final = df_filtered
        if incremental and tracker and existing_ids:
            logger.info("\nFiltrando ofertas nuevas (modo incremental)...")

            # Filtrar ofertas que NO están en existing_ids
            df_final = df_dedup[~df_dedup['id_oferta'].astype(str).isin(existing_ids)]

            ofertas_ya_existentes = len(df_dedup) - len(df_final)
            logger.info(f"Ofertas ya scrapeadas anteriormente: {ofertas_ya_existentes}")
            logger.info(f"Ofertas NUEVAS: {len(df_final)}")

            estadisticas['ofertas_ya_existentes'] = ofertas_ya_existentes
            estadisticas['ofertas_nuevas'] = len(df_final)

            # Actualizar tracking con IDs nuevos
            if not df_final.empty:
                new_ids = set(df_final['id_oferta'].astype(str))
                tracker.merge_scraped_ids(new_ids)
        elif incremental and tracker:
            # Primera ejecución: todas son nuevas
            logger.info("\nPrimera ejecución: todas las ofertas son nuevas")
            if not df_final.empty:
                new_ids = set(df_final['id_oferta'].astype(str))
                tracker.merge_scraped_ids(new_ids)

        # Estadísticas finales
        logger.info("\n" + "="*70)
        logger.info("ESTADISTICAS FINALES")
        logger.info("="*70)
        for key, value in estadisticas.items():
            logger.info(f"  {key}: {value}")

        logger.info("\nKeywords más productivas:")
        if 'keyword_busqueda' in df_final.columns:
            top_keywords = df_final['keyword_busqueda'].value_counts().head(10)
            for keyword, count in top_keywords.items():
                logger.info(f"  - {keyword}: {count} ofertas")

        return df_final

    def guardar_resultados(self, df, base_filename=None):
        """Guarda resultados consolidados en todos los formatos"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"computrabajo_multi_{timestamp}"

        logger.info("\nGuardando resultados...")

        # Usar métodos del scraper para guardar
        ofertas_list = df.to_dict('records')

        files = self.scraper.save_all_formats(ofertas_list, base_filename)

        logger.info("Archivos guardados:")
        for fmt, filepath in files.items():
            logger.info(f"  {fmt.upper()}: {filepath}")

        return files


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("COMPUTRABAJO - SCRAPER MULTI-KEYWORD")
    print("="*70)
    print("\nEstrategias disponibles:")
    print("  - minima: 4 keywords (testing)")
    print("  - general: 14 keywords (recomendada)")
    print("  - tecnologia: 20 keywords (IT focus)")
    print("  - amplia: 15 keywords (máxima cobertura)")
    print("")

    # Crear scraper
    multi_scraper = ComputRabajoMultiSearch(
        delay_between_requests=2.0,
        delay_between_keywords=5.0
    )

    # Scrapear con estrategia "minima" para testing
    print("[EJEMPLO] Usando estrategia 'minima' (4 keywords)")
    print("")

    df_ofertas = multi_scraper.scrapear_multiples_keywords(
        estrategia="minima",
        max_paginas_por_keyword=2,  # 2 páginas por keyword = 40 ofertas max
        max_resultados_por_keyword=50
    )

    # Guardar resultados
    if not df_ofertas.empty:
        files = multi_scraper.guardar_resultados(df_ofertas)
        print("\n" + "="*70)
        print("SCRAPING COMPLETADO EXITOSAMENTE")
        print("="*70)
    else:
        print("\nNo se encontraron ofertas")


if __name__ == "__main__":
    main()
