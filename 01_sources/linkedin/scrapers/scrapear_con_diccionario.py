"""
LinkedIn Multi-Keyword Scraper
===============================

Scraper que usa diccionario de búsquedas para maximizar cobertura en LinkedIn.
"""

import json
import pandas as pd
from pathlib import Path
from linkedin_scraper import LinkedInScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInMultiSearch:
    """Scraper multi-keyword para LinkedIn"""

    def __init__(self, delay_between_searches=3.0):
        """
        Args:
            delay_between_searches: Delay entre búsquedas (default: 3s)
        """
        self.scraper = LinkedInScraper(delay_between_searches)
        self.keywords_config_path = Path(__file__).parent.parent / "config" / "search_keywords.json"

    def cargar_keywords(self, estrategia="general"):
        """
        Carga keywords desde el diccionario

        Args:
            estrategia: Nombre de la estrategia (minima, general, tecnologia, amplia)

        Returns:
            Lista de keywords
        """
        with open(self.keywords_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if estrategia not in config['estrategias']:
            raise ValueError(f"Estrategia '{estrategia}' no encontrada. Disponibles: {list(config['estrategias'].keys())}")

        keywords = config['estrategias'][estrategia]['keywords']
        logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}'")

        return keywords

    def scrapear_multiples_keywords(
        self,
        keywords=None,
        estrategia="minima",
        location="Argentina",
        results_per_keyword=50,
        hours_old=None
    ):
        """
        Scrapea múltiples keywords y consolida resultados

        Args:
            keywords: Lista de keywords (None = usar estrategia)
            estrategia: Estrategia a usar si keywords=None
            location: Ubicación (default: Argentina)
            results_per_keyword: Resultados por keyword
            hours_old: Filtro de horas (None = todas)

        Returns:
            DataFrame consolidado sin duplicados
        """
        # Cargar keywords
        if keywords is None:
            keywords = self.cargar_keywords(estrategia)

        # Scrapear
        df = self.scraper.scrapear_multiples_keywords(
            keywords=keywords,
            location=location,
            results_per_keyword=results_per_keyword,
            hours_old=hours_old
        )

        return df

    def guardar_resultados(self, df, base_filename=None):
        """Guarda resultados en todos los formatos"""
        if base_filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"linkedin_multi_{timestamp}"

        logger.info("\nGuardando resultados...")
        files = self.scraper.save_all_formats(df, base_filename)

        logger.info("Archivos guardados:")
        for fmt, filepath in files.items():
            logger.info(f"  {fmt.upper()}: {filepath}")

        return files


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("LINKEDIN - SCRAPER MULTI-KEYWORD")
    print("="*70)
    print("\nEstrategias disponibles:")
    print("  - minima: 3 keywords (testing)")
    print("  - general: 12 keywords (recomendada)")
    print("  - tecnologia: 15 keywords (IT focus)")
    print("  - amplia: 14 keywords (máxima cobertura)")
    print("")

    # Crear scraper
    multi_scraper = LinkedInMultiSearch(delay_between_searches=3.0)

    # Scrapear con estrategia "minima" para testing
    print("[EJEMPLO] Usando estrategia 'minima' (3 keywords)")
    print("")

    df_ofertas = multi_scraper.scrapear_multiples_keywords(
        estrategia="minima",
        location="Argentina",
        results_per_keyword=30,  # 30 por keyword = ~90 total
        hours_old=168  # Última semana
    )

    # Guardar resultados
    if not df_ofertas.empty:
        files = multi_scraper.guardar_resultados(df_ofertas)
        print("\n" + "="*70)
        print("SCRAPING COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"Total ofertas únicas: {len(df_ofertas)}")
    else:
        print("\nNo se encontraron ofertas")


if __name__ == "__main__":
    main()
