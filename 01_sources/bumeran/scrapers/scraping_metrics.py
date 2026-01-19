"""
Sistema de Métricas de Scraping
================================

Captura métricas de performance y calidad durante el scraping:
- Tiempo por página
- Tasas de éxito/fallo
- Ofertas scrapeadas vs duplicadas
- Tasa de validación
- Errores y warnings

Uso:
    from scraping_metrics import ScrapingMetrics

    metrics = ScrapingMetrics()
    metrics.start()

    # Durante scraping
    metrics.page_start()
    # ... scrapear página ...
    metrics.page_end(offers_count=20, validation_rate=100.0)

    # Al finalizar
    metrics.end()
    report = metrics.get_report()
    print(report)
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ScrapingMetrics:
    """Captura y calcula métricas de performance del scraping"""

    def __init__(self):
        """Inicializa el sistema de métricas"""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Métricas por página
        self.pages_scraped: int = 0
        self.pages_failed: int = 0
        self.page_times: List[float] = []
        self.current_page_start: Optional[datetime] = None

        # Métricas de ofertas
        self.offers_total: int = 0
        self.offers_new: int = 0
        self.offers_duplicates: int = 0

        # Métricas de validación
        self.validation_rates: List[float] = []

        # Errores y warnings
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

        logger.debug("ScrapingMetrics inicializado")

    def start(self):
        """Inicia el cronómetro del scraping"""
        self.start_time = datetime.now()
        logger.debug(f"Scraping iniciado: {self.start_time.isoformat()}")

    def end(self):
        """Finaliza el cronómetro del scraping"""
        self.end_time = datetime.now()
        logger.debug(f"Scraping finalizado: {self.end_time.isoformat()}")

    def page_start(self):
        """Marca el inicio del scraping de una página"""
        self.current_page_start = datetime.now()

    def page_end(self,offers_count: int = 0,
                  new_offers: int = None,
                  validation_rate: Optional[float] = None,
                  failed: bool = False):
        """
        Marca el fin del scraping de una página y registra métricas

        Args:
            offers_count: Total de ofertas en la página
            new_offers: Ofertas nuevas (no duplicadas)
            validation_rate: % de ofertas válidas (0-100)
            failed: True si la página falló
        """
        if self.current_page_start:
            page_time = (datetime.now() - self.current_page_start).total_seconds()
            self.page_times.append(page_time)
            logger.debug(f"Página completada en {page_time:.2f}s")

        if failed:
            self.pages_failed += 1
        else:
            self.pages_scraped += 1
            self.offers_total += offers_count

            if new_offers is not None:
                self.offers_new += new_offers
                self.offers_duplicates += (offers_count - new_offers)

            if validation_rate is not None:
                self.validation_rates.append(validation_rate)

        self.current_page_start = None

    def add_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """
        Registra un error

        Args:
            error_type: Tipo de error (connection, validation, etc.)
            message: Mensaje descriptivo
            context: Info adicional (página, oferta_id, etc.)
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'context': context or {}
        }
        self.errors.append(error_entry)
        logger.debug(f"Error registrado: {error_type} - {message}")

    def add_warning(self, warning_type: str, message: str, context: Optional[Dict] = None):
        """
        Registra un warning

        Args:
            warning_type: Tipo de warning
            message: Mensaje descriptivo
            context: Info adicional
        """
        warning_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': warning_type,
            'message': message,
            'context': context or {}
        }
        self.warnings.append(warning_entry)
        logger.debug(f"Warning registrado: {warning_type} - {message}")

    def get_report(self) -> Dict:
        """
        Genera reporte completo de métricas

        Returns:
            Dict con todas las métricas calculadas
        """
        if not self.start_time or not self.end_time:
            logger.warning("Scraping no iniciado/finalizado correctamente")
            total_time = 0.0
        else:
            total_time = (self.end_time - self.start_time).total_seconds()

        # Calcular promedios
        avg_page_time = sum(self.page_times) / len(self.page_times) if self.page_times else 0.0
        avg_validation_rate = sum(self.validation_rates) / len(self.validation_rates) if self.validation_rates else 0.0

        # Tasa de éxito
        total_pages = self.pages_scraped + self.pages_failed
        success_rate = (self.pages_scraped / total_pages * 100) if total_pages > 0 else 0.0

        # Ofertas por segundo
        offers_per_second = self.offers_total / total_time if total_time > 0 else 0.0

        report = {
            # Tiempo
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_time_seconds': round(total_time, 2),
            'total_time_formatted': self._format_duration(total_time),

            # Páginas
            'pages_scraped': self.pages_scraped,
            'pages_failed': self.pages_failed,
            'pages_total': total_pages,
            'success_rate': round(success_rate, 2),
            'avg_time_per_page': round(avg_page_time, 2),

            # Ofertas
            'offers_total': self.offers_total,
            'offers_new': self.offers_new,
            'offers_duplicates': self.offers_duplicates,
            'offers_per_second': round(offers_per_second, 2),

            # Validación
            'validation_rate_avg': round(avg_validation_rate, 2),
            'validation_rate_min': round(min(self.validation_rates), 2) if self.validation_rates else None,
            'validation_rate_max': round(max(self.validation_rates), 2) if self.validation_rates else None,

            # Errores y Warnings
            'errors_count': len(self.errors),
            'warnings_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }

        return report

    def print_report(self):
        """Imprime reporte formateado en consola (compatible Windows)"""
        report = self.get_report()

        print()
        print("="*70)
        print("REPORTE DE METRICAS - SCRAPING")
        print("="*70)
        print()

        # Tiempo
        print("TIEMPO:")
        print(f"   Inicio:       {report['start_time']}")
        print(f"   Fin:          {report['end_time']}")
        print(f"   Duracion:     {report['total_time_formatted']}")
        print()

        # Páginas
        print("PAGINAS:")
        print(f"   Exitosas:     {report['pages_scraped']}")
        print(f"   Fallidas:     {report['pages_failed']}")
        print(f"   Total:        {report['pages_total']}")
        print(f"   Tasa exito:   {report['success_rate']}%")
        print(f"   Tiempo/pag:   {report['avg_time_per_page']}s")
        print()

        # Ofertas
        print("OFERTAS:")
        print(f"   Total:        {report['offers_total']}")
        print(f"   Nuevas:       {report['offers_new']}")
        print(f"   Duplicadas:   {report['offers_duplicates']}")
        print(f"   Velocidad:    {report['offers_per_second']} ofertas/s")
        print()

        # Validación
        if report['validation_rate_avg'] > 0:
            print("VALIDACION:")
            print(f"   Promedio:     {report['validation_rate_avg']}%")
            print(f"   Minimo:       {report['validation_rate_min']}%")
            print(f"   Maximo:       {report['validation_rate_max']}%")
            print()

        # Errores y Warnings
        if report['errors_count'] > 0:
            print(f"ERRORES: {report['errors_count']}")
            for error in report['errors'][:5]:  # Mostrar primeros 5
                print(f"   - [{error['type']}] {error['message']}")
            if report['errors_count'] > 5:
                print(f"   ... y {report['errors_count'] - 5} mas")
            print()

        if report['warnings_count'] > 0:
            print(f"WARNINGS: {report['warnings_count']}")
            for warning in report['warnings'][:5]:  # Mostrar primeros 5
                print(f"   - [{warning['type']}] {warning['message']}")
            if report['warnings_count'] > 5:
                print(f"   ... y {report['warnings_count'] - 5} mas")
            print()

        print("="*70)
        print()

    def save_report(self, output_path: Path):
        """
        Guarda reporte en archivo JSON

        Args:
            output_path: Path donde guardar el reporte
        """
        report = self.get_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Reporte guardado en: {output_path}")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Formatea duración en formato legible (HH:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()

    metrics = ScrapingMetrics()
    metrics.start()

    # Simular scraping de 3 páginas
    import time

    for i in range(3):
        metrics.page_start()
        time.sleep(0.5)  # Simular scraping
        metrics.page_end(
            offers_count=20,
            new_offers=15,
            validation_rate=98.5
        )

    metrics.end()

    # Mostrar reporte
    metrics.print_report()
