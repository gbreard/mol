"""
Sistema de Alertas
==================

Genera alertas basadas en métricas del scraping:
- Scraping fallido completamente
- Tasa de validación baja (< 80%)
- Tasa de éxito de páginas baja (< 50%)
- Circuit breaker abierto
- Tiempo de scraping anormalmente alto

Uso:
    from alert_manager import AlertManager

    alert_mgr = AlertManager()

    # Verificar métricas
    alert_mgr.check_metrics(metrics_report)

    # Verificar circuit breaker
    alert_mgr.check_circuit_breaker(breaker_stats)

    # Enviar alertas
    alert_mgr.send_alerts()
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Niveles de severidad de alertas"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertManager:
    """
    Gestiona alertas basadas en métricas de scraping

    Actualmente solo registra en logs, pero preparado para envío por email
    """

    def __init__(
        self,
        email_enabled: bool = False,
        email_to: Optional[str] = None,
        enable_console_output: bool = True
    ):
        """
        Inicializa el gestor de alertas

        Args:
            email_enabled: Si está habilitado el envío por email (futuro)
            email_to: Email destino para alertas
            enable_console_output: Si imprimir alertas en consola
        """
        self.email_enabled = email_enabled
        self.email_to = email_to
        self.enable_console_output = enable_console_output

        self.alerts: List[Dict] = []

        logger.debug(f"AlertManager inicializado (email_enabled={email_enabled})")

    def add_alert(
        self,
        level: AlertLevel,
        message: str,
        context: Optional[Dict] = None
    ):
        """
        Agrega una alerta

        Args:
            level: Nivel de severidad
            message: Mensaje de la alerta
            context: Información adicional (opcional)
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'message': message,
            'context': context or {}
        }

        self.alerts.append(alert)

        # Log según nivel
        log_msg = f"[{level.value}] {message}"
        if level == AlertLevel.INFO:
            logger.info(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        elif level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif level == AlertLevel.CRITICAL:
            logger.critical(log_msg)

    def check_metrics(self, metrics_report: Dict):
        """
        Verifica métricas y genera alertas si hay problemas

        Args:
            metrics_report: Dict con métricas del scraping (de ScrapingMetrics)
        """
        logger.debug("Verificando métricas para alertas...")

        # 1. Scraping completamente fallido
        if metrics_report.get('pages_scraped', 0) == 0:
            self.add_alert(
                AlertLevel.CRITICAL,
                "SCRAPING FALLIDO: No se scrapeó ninguna página",
                {'total_pages': metrics_report.get('pages_total', 0)}
            )

        # 2. Tasa de éxito de páginas < 50%
        success_rate = metrics_report.get('success_rate', 0)
        if success_rate < 50 and metrics_report.get('pages_total', 0) > 0:
            self.add_alert(
                AlertLevel.ERROR,
                f"Tasa de éxito muy baja: {success_rate}% (< 50%)",
                {'success_rate': success_rate}
            )

        # 3. Tasa de validación < 80%
        validation_rate = metrics_report.get('validation_rate_avg', 100)
        if validation_rate < 80 and validation_rate > 0:
            self.add_alert(
                AlertLevel.WARNING,
                f"Tasa de validación baja: {validation_rate}% (< 80%)",
                {'validation_rate': validation_rate}
            )

        # 4. Errores presentes
        errors_count = metrics_report.get('errors_count', 0)
        if errors_count > 0:
            self.add_alert(
                AlertLevel.WARNING,
                f"{errors_count} errores detectados durante scraping",
                {
                    'errors_count': errors_count,
                    'errors': metrics_report.get('errors', [])[:3]  # Primeros 3
                }
            )

        # 5. Sin ofertas scrapeadas (posible problema)
        offers_total = metrics_report.get('offers_total', 0)
        if offers_total == 0 and metrics_report.get('pages_scraped', 0) > 0:
            self.add_alert(
                AlertLevel.WARNING,
                "Ninguna oferta scrapeada (posible problema con API)",
                {'pages_scraped': metrics_report.get('pages_scraped')}
            )

        # 6. Tiempo de scraping muy alto (> 2x esperado)
        avg_time = metrics_report.get('avg_time_per_page', 0)
        if avg_time > 60:  # Más de 1 min por página es anormal
            self.add_alert(
                AlertLevel.WARNING,
                f"Tiempo por página muy alto: {avg_time:.1f}s (> 60s esperado)",
                {'avg_time_per_page': avg_time}
            )

    def check_circuit_breaker(self, breaker_stats: Dict):
        """
        Verifica estado del circuit breaker y genera alertas

        Args:
            breaker_stats: Dict con stats del circuit breaker
        """
        state = breaker_stats.get('state', 'closed')

        if state == 'open':
            self.add_alert(
                AlertLevel.CRITICAL,
                f"Circuit breaker ABIERTO: API no disponible",
                {
                    'consecutive_failures': breaker_stats.get('consecutive_failures'),
                    'times_opened': breaker_stats.get('times_opened')
                }
            )

        elif state == 'half_open':
            self.add_alert(
                AlertLevel.WARNING,
                "Circuit breaker en HALF_OPEN: probando recuperación de API",
                {}
            )

    def check_rate_limiter(self, limiter_stats: Dict):
        """
        Verifica estado del rate limiter y genera alertas

        Args:
            limiter_stats: Dict con stats del rate limiter
        """
        # Si delay está en el máximo, puede ser problema
        current_delay = limiter_stats.get('current_delay', 0)
        max_delay = limiter_stats.get('max_delay', 10)

        if current_delay >= max_delay:
            self.add_alert(
                AlertLevel.WARNING,
                f"Rate limiter en delay máximo: {current_delay}s (API limitando requests)",
                {'current_delay': current_delay}
            )

        # Si hubo muchos rate limits (429)
        rate_limits = limiter_stats.get('total_rate_limits', 0)
        if rate_limits > 5:
            self.add_alert(
                AlertLevel.WARNING,
                f"{rate_limits} rate limits (429) recibidos durante scraping",
                {'total_rate_limits': rate_limits}
            )

    def get_alerts_by_level(self, level: AlertLevel) -> List[Dict]:
        """
        Obtiene alertas de un nivel específico

        Args:
            level: Nivel de alerta

        Returns:
            Lista de alertas de ese nivel
        """
        return [a for a in self.alerts if a['level'] == level.value]

    def has_alerts(self, min_level: AlertLevel = AlertLevel.WARNING) -> bool:
        """
        Verifica si hay alertas de un nivel mínimo

        Args:
            min_level: Nivel mínimo de alerta a considerar

        Returns:
            True si hay alertas >= min_level
        """
        levels_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

        min_level_value = levels_order[min_level]

        for alert in self.alerts:
            alert_level_value = levels_order.get(
                AlertLevel(alert['level']),
                0
            )
            if alert_level_value >= min_level_value:
                return True

        return False

    def send_alerts(self):
        """
        Envía todas las alertas pendientes

        Por ahora solo imprime en consola y logs
        En el futuro: envío por email, Slack, etc.
        """
        if not self.alerts:
            logger.debug("No hay alertas para enviar")
            return

        # Agrupar por nivel
        critical = self.get_alerts_by_level(AlertLevel.CRITICAL)
        error = self.get_alerts_by_level(AlertLevel.ERROR)
        warning = self.get_alerts_by_level(AlertLevel.WARNING)
        info = self.get_alerts_by_level(AlertLevel.INFO)

        if self.enable_console_output:
            self._print_alerts_console(critical, error, warning, info)

        if self.email_enabled and self.email_to:
            self._send_alerts_email(critical, error, warning, info)
        else:
            logger.debug("Envío de email deshabilitado")

        logger.info(f"Alertas procesadas: {len(self.alerts)} total")

    def _print_alerts_console(
        self,
        critical: List[Dict],
        error: List[Dict],
        warning: List[Dict],
        info: List[Dict]
    ):
        """Imprime alertas en consola"""
        print()
        print("="*70)
        print("ALERTAS DEL SCRAPING")
        print("="*70)
        print()

        if critical:
            print(f"CRITICAL ({len(critical)}):")
            for alert in critical:
                print(f"  - {alert['message']}")
            print()

        if error:
            print(f"ERROR ({len(error)}):")
            for alert in error:
                print(f"  - {alert['message']}")
            print()

        if warning:
            print(f"WARNING ({len(warning)}):")
            for alert in warning:
                print(f"  - {alert['message']}")
            print()

        if info:
            print(f"INFO ({len(info)}):")
            for alert in info:
                print(f"  - {alert['message']}")
            print()

        print("="*70)
        print()

    def _send_alerts_email(
        self,
        critical: List[Dict],
        error: List[Dict],
        warning: List[Dict],
        info: List[Dict]
    ):
        """
        Envía alertas por email (placeholder para futuro)

        TODO: Implementar envío real con SMTP
        """
        logger.info(f"Enviando alertas por email a {self.email_to}...")
        logger.warning("Envío de email no implementado aún (placeholder)")

        # Futuro: usar smtplib para enviar email
        # subject = f"Alertas Scraping Bumeran - {datetime.now()}"
        # body = self._format_email_body(critical, error, warning, info)
        # send_email(self.email_to, subject, body)

    def clear_alerts(self):
        """Limpia todas las alertas"""
        self.alerts = []
        logger.debug("Alertas limpiadas")


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()

    alert_mgr = AlertManager()

    # Simular métricas problemáticas
    bad_metrics = {
        'pages_scraped': 2,
        'pages_total': 10,
        'success_rate': 20.0,  # Muy bajo
        'validation_rate_avg': 65.0,  # Bajo
        'errors_count': 8,
        'offers_total': 0  # Problema
    }

    print("Verificando métricas problemáticas...")
    alert_mgr.check_metrics(bad_metrics)

    # Simular circuit breaker abierto
    breaker_stats = {
        'state': 'open',
        'consecutive_failures': 5
    }

    print("Verificando circuit breaker...")
    alert_mgr.check_circuit_breaker(breaker_stats)

    # Enviar alertas
    alert_mgr.send_alerts()
