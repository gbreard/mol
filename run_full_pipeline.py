"""
Script Maestro del Pipeline de Scraping
========================================

Ejecuta el pipeline completo de scraping incremental para todas las fuentes:
1. Bumeran (API REST - ~12K ofertas)
2. ComputRabajo (HTML + multi-keyword - ~20K ofertas)
3. ZonaJobs (API REST - ~5K ofertas)
4. LinkedIn (JobSpy - multi-keyword)
5. Indeed (JobSpy - multi-keyword)

Luego consolida y normaliza todos los datos.

Uso:
    # Scraping completo (primera vez)
    python run_full_pipeline.py --full

    # Scraping incremental (solo ofertas nuevas)
    python run_full_pipeline.py

    # Solo una fuente específica
    python run_full_pipeline.py --source bumeran

    # Con límite de ofertas (testing)
    python run_full_pipeline.py --limit 100
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orquestador del pipeline de scraping multi-fuente"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.sources_dir = self.project_root / "01_sources"
        self.consolidation_dir = self.project_root / "02_consolidation"
        self.config_dir = self.project_root / "data" / "config"

        # NO agregar todos los paths al sys.path para evitar conflictos de nombres
        # Solo agregar consolidation y config que son comunes
        sys.path.insert(0, str(self.consolidation_dir / "scripts"))
        sys.path.insert(0, str(self.config_dir))

        # Importar keywords_loader
        try:
            from keywords_loader import load_keywords
            self.load_keywords = load_keywords
            logger.info("Diccionario maestro de keywords cargado exitosamente")
        except ImportError as e:
            logger.warning(f"No se pudo importar keywords_loader: {e}")
            self.load_keywords = None

        self.results = {}

    def scrapear_bumeran(self, incremental=True, max_resultados=None):
        """Scrapea Bumeran usando API REST"""
        logger.info("=" * 70)
        logger.info("SCRAPEANDO BUMERAN")
        logger.info("=" * 70)

        try:
            # Agregar path específico de Bumeran
            bumeran_path = str(self.sources_dir / "bumeran" / "scrapers")
            if bumeran_path not in sys.path:
                sys.path.insert(0, bumeran_path)

            from bumeran_scraper import BumeranScraper

            scraper = BumeranScraper(delay_between_requests=2.0)

            # Scrapear con max_paginas=None para traer todo
            ofertas = scraper.scrapear_todo(
                max_paginas=None if not max_resultados else 10,
                max_resultados=max_resultados,
                incremental=incremental
            )

            logger.info(f"[OK] Bumeran: {len(ofertas)} ofertas scrapeadas")

            # Guardar
            if ofertas:
                files = scraper.save_all_formats(ofertas, 'bumeran_consolidacion')
                self.results['bumeran'] = {
                    'count': len(ofertas),
                    'files': files,
                    'status': 'success'
                }
                return True

        except Exception as e:
            logger.error(f"[ERROR] Error en Bumeran: {e}")
            self.results['bumeran'] = {'status': 'error', 'error': str(e)}
            return False

    def scrapear_computrabajo(self, incremental=True, max_resultados=None):
        """Scrapea ComputRabajo con estrategia multi-keyword"""
        logger.info("=" * 70)
        logger.info("SCRAPEANDO COMPUTRABAJO")
        logger.info("=" * 70)

        try:
            # Agregar path específico de ComputRabajo
            computrabajo_path = str(self.sources_dir / "computrabajo" / "scrapers")
            if computrabajo_path not in sys.path:
                sys.path.insert(0, computrabajo_path)

            from scrapear_con_diccionario import ComputRabajoMultiSearch

            scraper = ComputRabajoMultiSearch(
                delay_between_requests=2.0,
                delay_between_keywords=3.0
            )

            # Usar estrategia del diccionario MAESTRO optimizado
            # maxima: ~90 keywords (primera ejecución)
            # completa: ~55 keywords (normal)
            # general: ~30 keywords (rápido)
            df = scraper.scrapear_multiples_keywords(
                estrategia='completa' if not max_resultados else 'general',
                max_paginas_por_keyword=None if not max_resultados else 3,
                max_resultados_por_keyword=max_resultados if max_resultados else None,
                incremental=incremental
            )

            logger.info(f"[OK] ComputRabajo: {len(df)} ofertas scrapeadas")

            # Guardar
            if not df.empty:
                files = scraper.guardar_resultados(df, 'computrabajo_consolidacion')
                self.results['computrabajo'] = {
                    'count': len(df),
                    'files': files,
                    'status': 'success'
                }
                return True

        except Exception as e:
            logger.error(f"[ERROR] Error en ComputRabajo: {e}")
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            self.results['computrabajo'] = {'status': 'error', 'error': str(e)}
            return False

    def scrapear_zonajobs(self, incremental=True, max_resultados=None):
        """Scrapea ZonaJobs usando API REST"""
        logger.info("=" * 70)
        logger.info("SCRAPEANDO ZONAJOBS")
        logger.info("=" * 70)

        try:
            # Agregar path específico de ZonaJobs
            zonajobs_path = str(self.sources_dir / "zonajobs" / "scrapers")
            if zonajobs_path not in sys.path:
                sys.path.insert(0, zonajobs_path)

            from zonajobs_scraper_final import ZonaJobsScraperFinal

            scraper = ZonaJobsScraperFinal(delay_between_requests=2.0)

            ofertas = scraper.scrapear_todo(
                max_paginas=None if not max_resultados else 5,
                max_resultados=max_resultados,
                incremental=incremental
            )

            logger.info(f"[OK] ZonaJobs: {len(ofertas)} ofertas scrapeadas")

            # Guardar
            if ofertas:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                scraper.save_to_csv(ofertas, f'zonajobs_consolidacion_{timestamp}.csv')
                self.results['zonajobs'] = {
                    'count': len(ofertas),
                    'status': 'success'
                }
                return True

        except Exception as e:
            logger.error(f"[ERROR] Error en ZonaJobs: {e}")
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            self.results['zonajobs'] = {'status': 'error', 'error': str(e)}
            return False

    def scrapear_linkedin(self, incremental=True, max_resultados=None):
        """Scrapea LinkedIn usando JobSpy con multi-keyword"""
        logger.info("=" * 70)
        logger.info("SCRAPEANDO LINKEDIN")
        logger.info("=" * 70)

        try:
            # Agregar path específico de LinkedIn
            linkedin_path = str(self.sources_dir / "linkedin" / "scrapers")
            if linkedin_path not in sys.path:
                sys.path.insert(0, linkedin_path)

            from linkedin_scraper import LinkedInScraper

            scraper = LinkedInScraper(delay_between_searches=3.0)

            # Estrategia multi-keyword para máxima cobertura
            # LinkedIn: límite ~1000/keyword pero rate limit en página 10
            # Usar 500/keyword es conservador y seguro
            if self.load_keywords:
                keywords = self.load_keywords('general')  # 30 keywords optimizadas
                logger.info(f"Usando {len(keywords)} keywords del diccionario maestro")
            else:
                keywords = [""]  # Fallback a búsqueda vacía
                logger.warning("keywords_loader no disponible, usando búsqueda vacía")

            df = scraper.scrapear_multiples_keywords(
                keywords=keywords,
                location="Argentina",
                results_per_keyword=max_resultados if max_resultados else 500,
                incremental=incremental
            )

            logger.info(f"[OK] LinkedIn: {len(df)} ofertas scrapeadas")

            # Guardar
            if not df.empty:
                files = scraper.save_all_formats(df, 'linkedin_consolidacion')
                self.results['linkedin'] = {
                    'count': len(df),
                    'files': files,
                    'status': 'success'
                }
                return True

        except Exception as e:
            logger.error(f"[ERROR] Error en LinkedIn: {e}")
            self.results['linkedin'] = {'status': 'error', 'error': str(e)}
            return False

    def scrapear_indeed(self, incremental=True, max_resultados=None):
        """Scrapea Indeed usando JobSpy con multi-keyword"""
        logger.info("=" * 70)
        logger.info("SCRAPEANDO INDEED")
        logger.info("=" * 70)

        try:
            # Agregar path específico de Indeed
            indeed_path = str(self.sources_dir / "indeed" / "scrapers")
            if indeed_path not in sys.path:
                sys.path.insert(0, indeed_path)

            from indeed_scraper import IndeedScraper

            scraper = IndeedScraper(delay_between_searches=3.0)

            # Estrategia multi-keyword para máxima cobertura
            # Indeed: límite ~1000/keyword pero SIN rate limiting (mejor scraper)
            # Usar 1000/keyword es seguro y maximiza cobertura
            if self.load_keywords:
                keywords = self.load_keywords('general')  # 30 keywords optimizadas
                logger.info(f"Usando {len(keywords)} keywords del diccionario maestro")
            else:
                keywords = [""]  # Fallback a búsqueda vacía
                logger.warning("keywords_loader no disponible, usando búsqueda vacía")

            df = scraper.scrapear_multiples_keywords(
                keywords=keywords,
                location="Buenos Aires",
                results_per_keyword=max_resultados if max_resultados else 1000,
                incremental=incremental
            )

            logger.info(f"[OK] Indeed: {len(df)} ofertas scrapeadas")

            # Guardar
            if not df.empty:
                files = scraper.save_all_formats(df, 'indeed_consolidacion')
                self.results['indeed'] = {
                    'count': len(df),
                    'files': files,
                    'status': 'success'
                }
                return True

        except Exception as e:
            logger.error(f"[ERROR] Error en Indeed: {e}")
            self.results['indeed'] = {'status': 'error', 'error': str(e)}
            return False

    def consolidar_todo(self):
        """Ejecuta consolidación de todas las fuentes"""
        logger.info("=" * 70)
        logger.info("CONSOLIDANDO TODAS LAS FUENTES")
        logger.info("=" * 70)

        try:
            from consolidar_fuentes import ConsolidadorMultiFuente

            consolidador = ConsolidadorMultiFuente()

            # Consolidar
            df = consolidador.consolidar_todas()

            if df is not None and not df.empty:
                # Guardar en todos los formatos
                consolidador.guardar_consolidado(df, formato='all')
                consolidador.generar_reporte_consolidacion(df)

                self.results['consolidacion'] = {
                    'count': len(df),
                    'status': 'success'
                }

                logger.info(f"[OK] Consolidación completada: {len(df)} ofertas totales")
                return True
            else:
                logger.warning("No se pudo consolidar ninguna fuente")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Error en consolidación: {e}")
            import traceback
            traceback.print_exc()
            self.results['consolidacion'] = {'status': 'error', 'error': str(e)}
            return False

    def ejecutar_pipeline_completo(self, incremental=True, max_resultados=None, sources=None):
        """
        Ejecuta el pipeline completo

        Args:
            incremental: Si True, solo trae ofertas nuevas
            max_resultados: Límite de ofertas por fuente (None = ilimitado)
            sources: Lista de fuentes a scrapear (None = todas)
        """
        logger.info("\n" + "=" * 70)
        logger.info("INICIANDO PIPELINE DE SCRAPING")
        logger.info("=" * 70)
        logger.info(f"Modo: {'INCREMENTAL' if incremental else 'FULL'}")
        logger.info(f"Límite por fuente: {max_resultados or 'SIN LÍMITE'}")
        logger.info(f"Fuentes: {sources or 'TODAS'}")
        logger.info("=" * 70)

        inicio = datetime.now()

        # Definir fuentes a scrapear
        all_sources = {
            'bumeran': self.scrapear_bumeran,
            'computrabajo': self.scrapear_computrabajo,
            'zonajobs': self.scrapear_zonajobs,
            'linkedin': self.scrapear_linkedin,
            'indeed': self.scrapear_indeed
        }

        if sources:
            sources_to_run = {k: v for k, v in all_sources.items() if k in sources}
        else:
            sources_to_run = all_sources

        # Scrapear cada fuente
        for source_name, scraper_func in sources_to_run.items():
            try:
                scraper_func(incremental=incremental, max_resultados=max_resultados)
            except Exception as e:
                logger.error(f"Error crítico en {source_name}: {e}")
                import traceback
                logger.error(f"Traceback completo:\n{traceback.format_exc()}")
                continue

        # Consolidar
        self.consolidar_todo()

        # Reporte final
        fin = datetime.now()
        duracion = fin - inicio

        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETADO")
        logger.info("=" * 70)
        logger.info(f"Duración total: {duracion}")
        logger.info("\nResultados por fuente:")

        total_ofertas = 0
        for source, result in self.results.items():
            status = result.get('status', 'unknown')
            count = result.get('count', 0)
            total_ofertas += count

            status_emoji = "[OK]" if status == 'success' else "[ERROR]"
            logger.info(f"  {status_emoji} {source}: {count} ofertas ({status})")

        logger.info(f"\nTotal de ofertas scrapeadas: {total_ofertas:,}")
        logger.info("=" * 70)

        # Verificar tracking
        try:
            from incremental_tracker import print_tracking_summary
            print()
            print_tracking_summary()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de scraping multi-fuente con modo incremental'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Modo full (scrapear todo, ignorar tracking)'
    )

    parser.add_argument(
        '--source',
        choices=['bumeran', 'computrabajo', 'zonajobs', 'linkedin', 'indeed'],
        help='Scrapear solo una fuente específica'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Límite de ofertas por fuente (para testing)'
    )

    args = parser.parse_args()

    # Crear orquestador
    pipeline = PipelineOrchestrator()

    # Ejecutar
    incremental = not args.full
    sources = [args.source] if args.source else None

    pipeline.ejecutar_pipeline_completo(
        incremental=incremental,
        max_resultados=args.limit,
        sources=sources
    )


if __name__ == "__main__":
    main()
