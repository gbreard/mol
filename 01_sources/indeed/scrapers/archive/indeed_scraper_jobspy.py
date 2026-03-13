"""
Indeed Scraper usando JobSpy
==============================

Scraper para Indeed Jobs Argentina usando la librería JobSpy.
Soporta búsquedas multi-keyword y exportación a múltiples formatos.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
from pathlib import Path
import time
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar path para importar incremental_tracker
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
if str(consolidation_scripts) not in sys.path:
    sys.path.insert(0, str(consolidation_scripts))

try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    logger.warning(f"No se pudo importar IncrementalTracker: {e}")
    logger.warning("Modo incremental deshabilitado")
    IncrementalTracker = None


class IndeedScraper:
    """Scraper para Indeed Jobs usando JobSpy"""

    def __init__(self, delay_between_searches=3.0):
        """
        Args:
            delay_between_searches: Delay entre búsquedas (default: 3s)
        """
        self.delay = delay_between_searches
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def scrapear(
        self,
        search_term="",
        location="Buenos Aires",
        results_wanted=100,
        hours_old=None,
        fetch_description=False
    ):
        """
        Scrapea ofertas de Indeed

        Args:
            search_term: Término de búsqueda (vacío = todas las ofertas)
            location: Ubicación (default: Argentina)
            results_wanted: Cantidad de resultados (default: 100)
            hours_old: Filtrar por horas desde publicación (None = todas)
            fetch_description: Obtener descripción completa (más lento)

        Returns:
            DataFrame con ofertas
        """
        logger.info(f"Scrapeando Indeed: '{search_term}' en {location}")
        logger.info(f"  Resultados deseados: {results_wanted}")
        if hours_old:
            logger.info(f"  Filtro: últimas {hours_old} horas")

        try:
            jobs = scrape_jobs(
                site_name=['indeed'],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                indeed_fetch_description=fetch_description
            )

            if jobs is not None and len(jobs) > 0:
                # Agregar metadata
                jobs['scrapeado_en'] = datetime.now().isoformat()
                jobs['fuente'] = 'indeed'
                jobs['search_term_usado'] = search_term

                logger.info(f"  [OK] {len(jobs)} ofertas encontradas")
                return jobs
            else:
                logger.warning(f"  [X] No se encontraron ofertas")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"  [ERROR] Error: {e}")
            return pd.DataFrame()

    def scrapear_multiples_keywords(
        self,
        keywords,
        location="Buenos Aires, Argentina",
        results_per_keyword=100,
        hours_old=None,
        delay_between_keywords=None,
        incremental=True
    ):
        """
        Scrapea múltiples keywords y consolida resultados

        Args:
            keywords: Lista de keywords a scrapear
            location: Ubicación
            results_per_keyword: Resultados por keyword
            hours_old: Filtro de horas
            delay_between_keywords: Delay entre keywords (None = usar self.delay)
            incremental: Si True, solo trae ofertas nuevas (default: True)

        Returns:
            DataFrame consolidado sin duplicados
        """
        delay = delay_between_keywords if delay_between_keywords else self.delay

        logger.info("="*70)
        logger.info("SCRAPING MULTI-KEYWORD - INDEED")
        logger.info("="*70)
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Resultados por keyword: {results_per_keyword}")
        logger.info(f"Delay entre keywords: {delay}s")
        logger.info(f"Modo: {'Incremental' if incremental else 'Full'}")
        logger.info("")

        # Inicializar tracker si modo incremental
        tracker = None
        existing_ids = set()
        if incremental:
            if IncrementalTracker is None:
                logger.warning("IncrementalTracker no disponible, ejecutando en modo full")
                incremental = False
            else:
                tracker = IncrementalTracker(source='indeed')
                existing_ids = tracker.load_scraped_ids()
                if existing_ids:
                    logger.info(f"Modo incremental: {len(existing_ids):,} IDs ya scrapeados")
                else:
                    logger.info("Primera ejecución: scrapeando TODO")
                logger.info("")

        all_jobs = []
        stats = {
            'keywords_procesadas': 0,
            'keywords_exitosas': 0,
            'ofertas_totales': 0,
            'ofertas_unicas': 0
        }

        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{len(keywords)}] Keyword: '{keyword}'")

            jobs = self.scrapear(
                search_term=keyword,
                location=location,
                results_wanted=results_per_keyword,
                hours_old=hours_old
            )

            if len(jobs) > 0:
                all_jobs.append(jobs)
                stats['keywords_exitosas'] += 1
                stats['ofertas_totales'] += len(jobs)

            stats['keywords_procesadas'] += 1

            # Delay entre keywords
            if i < len(keywords):
                logger.debug(f"  Esperando {delay}s...")
                time.sleep(delay)

        # Consolidar y deduplicar
        logger.info("")
        logger.info("="*70)
        logger.info("CONSOLIDANDO RESULTADOS")
        logger.info("="*70)

        if not all_jobs:
            logger.warning("No se encontraron ofertas")
            return pd.DataFrame()

        df = pd.concat(all_jobs, ignore_index=True)
        logger.info(f"Ofertas totales (con duplicados): {len(df)}")

        # Deduplicar por ID
        df_dedup = df.drop_duplicates(subset='id', keep='first')
        stats['ofertas_unicas'] = len(df_dedup)

        duplicados = len(df) - len(df_dedup)
        logger.info(f"Ofertas únicas: {len(df_dedup)}")
        logger.info(f"Duplicados removidos: {duplicados}")

        # Filtrar ofertas nuevas si modo incremental
        df_final = df_dedup
        if incremental and tracker and existing_ids:
            logger.info("")
            logger.info("Filtrando ofertas nuevas (modo incremental)...")

            # Filtrar ofertas que NO están en existing_ids
            df_final = df_dedup[~df_dedup['id'].astype(str).isin(existing_ids)]

            ofertas_ya_existentes = len(df_dedup) - len(df_final)
            logger.info(f"Ofertas ya scrapeadas anteriormente: {ofertas_ya_existentes}")
            logger.info(f"Ofertas NUEVAS: {len(df_final)}")

            stats['ofertas_ya_existentes'] = ofertas_ya_existentes
            stats['ofertas_nuevas'] = len(df_final)

            # Actualizar tracking con IDs nuevos
            if not df_final.empty:
                new_ids = set(df_final['id'].astype(str))
                tracker.merge_scraped_ids(new_ids)
        elif incremental and tracker:
            # Primera ejecución: todas son nuevas
            logger.info("")
            logger.info("Primera ejecución: todas las ofertas son nuevas")
            if not df_final.empty:
                new_ids = set(df_final['id'].astype(str))
                tracker.merge_scraped_ids(new_ids)

        # Stats
        logger.info("")
        logger.info("="*70)
        logger.info("ESTADÍSTICAS FINALES")
        logger.info("="*70)
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

        if 'search_term_usado' in df_final.columns:
            logger.info("")
            logger.info("Keywords más productivas:")
            top_kw = df_final['search_term_usado'].value_counts().head(10)
            for kw, count in top_kw.items():
                logger.info(f"  - {kw}: {count} ofertas")

        return df_final

    def save_to_csv(self, jobs_df, filename=None):
        """Guarda a CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"indeed_{timestamp}.csv"

        filepath = self.data_dir / filename
        jobs_df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"CSV guardado: {filepath}")
        return filepath

    def save_to_json(self, jobs_df, filename=None):
        """Guarda a JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"indeed_{timestamp}.json"

        filepath = self.data_dir / filename
        jobs_df.to_json(filepath, orient='records', indent=2)
        logger.info(f"JSON guardado: {filepath}")
        return filepath

    def save_to_excel(self, jobs_df, filename=None):
        """Guarda a Excel"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"indeed_{timestamp}.xlsx"

        filepath = self.data_dir / filename
        jobs_df.to_excel(filepath, index=False, engine='openpyxl')
        logger.info(f"Excel guardado: {filepath}")
        return filepath

    def save_all_formats(self, jobs_df, base_filename=None):
        """Guarda en todos los formatos"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"indeed_{timestamp}"

        files = {
            'csv': self.save_to_csv(jobs_df, f"{base_filename}.csv"),
            'json': self.save_to_json(jobs_df, f"{base_filename}.json"),
            'excel': self.save_to_excel(jobs_df, f"{base_filename}.xlsx")
        }

        return files


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("LINKEDIN SCRAPER - TEST")
    print("="*70)
    print("")

    scraper = IndeedScraper(delay_between_searches=3.0)

    # Scrapear ofertas de Python en Argentina
    print("Scrapeando ofertas de 'python' en Argentina...")
    print("")

    jobs = scraper.scrapear(
        search_term="python developer",
        location="Buenos Aires, Argentina",
        results_wanted=50,
        hours_old=168  # Última semana
    )

    if len(jobs) > 0:
        # Guardar
        files = scraper.save_all_formats(jobs, "indeed_test")

        print("")
        print("="*70)
        print("SCRAPING COMPLETADO")
        print("="*70)
        print(f"Total de ofertas: {len(jobs)}")
        print("")
        print("Campos disponibles:")
        for col in jobs.columns:
            non_null = jobs[col].notna().sum()
            pct = (non_null / len(jobs)) * 100
            print(f"  - {col}: {non_null}/{len(jobs)} ({pct:.1f}%)")
    else:
        print("No se encontraron ofertas")


if __name__ == "__main__":
    main()
