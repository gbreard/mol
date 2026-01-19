"""
Rate Limiting Adaptativo
========================

Ajusta automáticamente el delay entre requests basado en el comportamiento de la API:
- Si todo va bien: reduce delay gradualmente (optimiza velocidad)
- Si recibe 429 o errores: aumenta delay (evita sobrecarga)

Uso:
    from adaptive_rate_limiter import AdaptiveRateLimiter

    limiter = AdaptiveRateLimiter(
        initial_delay=2.0,
        min_delay=0.5,
        max_delay=10.0
    )

    # Antes de cada request
    time.sleep(limiter.get_delay())

    # Después del request
    if response.status_code == 200:
        limiter.on_success()
    elif response.status_code == 429:
        limiter.on_rate_limit()
    else:
        limiter.on_error()
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Rate limiter que ajusta el delay automáticamente según respuestas de la API

    Estrategia:
    - Éxitos consecutivos (5+): reduce delay 10%
    - Rate limit (429): aumenta delay 50%
    - Errores consecutivos (3+): aumenta delay 25%
    """

    def __init__(
        self,
        initial_delay: float = 2.0,
        min_delay: float = 0.5,
        max_delay: float = 10.0,
        success_threshold: int = 5,
        error_threshold: int = 3
    ):
        """
        Inicializa el rate limiter adaptativo

        Args:
            initial_delay: Delay inicial en segundos
            min_delay: Delay mínimo permitido
            max_delay: Delay máximo permitido
            success_threshold: Éxitos consecutivos para reducir delay
            error_threshold: Errores consecutivos para aumentar delay
        """
        self.delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.success_threshold = success_threshold
        self.error_threshold = error_threshold

        # Contadores
        self.consecutive_success = 0
        self.consecutive_errors = 0
        self.total_requests = 0
        self.total_success = 0
        self.total_errors = 0
        self.total_rate_limits = 0

        # Historial de delays (últimos 10)
        self.delay_history = [initial_delay]

        logger.debug(
            f"AdaptiveRateLimiter inicializado: "
            f"delay={initial_delay}s, min={min_delay}s, max={max_delay}s"
        )

    def get_delay(self) -> float:
        """
        Obtiene el delay actual

        Returns:
            Delay en segundos
        """
        return self.delay

    def wait(self):
        """Espera el delay actual (bloquea el hilo)"""
        time.sleep(self.delay)

    def on_success(self):
        """
        Registra un request exitoso

        Si hay suficientes éxitos consecutivos, reduce el delay
        """
        self.total_requests += 1
        self.total_success += 1
        self.consecutive_success += 1
        self.consecutive_errors = 0  # Reset

        # Reducir delay si alcanzamos el threshold
        if self.consecutive_success >= self.success_threshold:
            old_delay = self.delay
            self.delay = max(self.min_delay, self.delay * 0.9)  # Reducir 10%

            if self.delay < old_delay:
                logger.info(
                    f"Rate limiter: {self.consecutive_success} éxitos → "
                    f"reduciendo delay {old_delay:.2f}s → {self.delay:.2f}s"
                )

            self.consecutive_success = 0  # Reset después de ajuste
            self._update_history()

    def on_rate_limit(self):
        """
        Registra un rate limit (429)

        Aumenta el delay significativamente
        """
        self.total_requests += 1
        self.total_rate_limits += 1
        self.consecutive_success = 0
        self.consecutive_errors += 1

        old_delay = self.delay
        self.delay = min(self.max_delay, self.delay * 1.5)  # Aumentar 50%

        logger.warning(
            f"Rate limiter: 429 recibido → "
            f"aumentando delay {old_delay:.2f}s → {self.delay:.2f}s"
        )

        self._update_history()

    def on_error(self):
        """
        Registra un error (500, 502, 503, timeout, etc.)

        Si hay varios errores consecutivos, aumenta el delay
        """
        self.total_requests += 1
        self.total_errors += 1
        self.consecutive_success = 0
        self.consecutive_errors += 1

        # Aumentar delay si alcanzamos el threshold de errores
        if self.consecutive_errors >= self.error_threshold:
            old_delay = self.delay
            self.delay = min(self.max_delay, self.delay * 1.25)  # Aumentar 25%

            logger.warning(
                f"Rate limiter: {self.consecutive_errors} errores consecutivos → "
                f"aumentando delay {old_delay:.2f}s → {self.delay:.2f}s"
            )

            self._update_history()

    def reset_to_initial(self):
        """Resetea el delay al valor inicial"""
        old_delay = self.delay
        self.delay = self.delay_history[0]  # Delay inicial
        self.consecutive_success = 0
        self.consecutive_errors = 0

        logger.info(f"Rate limiter: reset {old_delay:.2f}s → {self.delay:.2f}s")

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del rate limiter

        Returns:
            Dict con estadísticas
        """
        success_rate = (self.total_success / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            'current_delay': round(self.delay, 2),
            'min_delay': self.min_delay,
            'max_delay': self.max_delay,
            'total_requests': self.total_requests,
            'total_success': self.total_success,
            'total_errors': self.total_errors,
            'total_rate_limits': self.total_rate_limits,
            'success_rate': round(success_rate, 2),
            'consecutive_success': self.consecutive_success,
            'consecutive_errors': self.consecutive_errors,
            'delay_history': self.delay_history[-10:]  # Últimos 10
        }

    def print_stats(self):
        """Imprime estadísticas en consola"""
        stats = self.get_stats()

        print()
        print("="*60)
        print("ADAPTIVE RATE LIMITER - ESTADISTICAS")
        print("="*60)
        print(f"Delay actual:         {stats['current_delay']}s")
        print(f"Rango:                {stats['min_delay']}s - {stats['max_delay']}s")
        print()
        print(f"Total requests:       {stats['total_requests']}")
        print(f"  Exitosos:           {stats['total_success']}")
        print(f"  Errores:            {stats['total_errors']}")
        print(f"  Rate limits (429):  {stats['total_rate_limits']}")
        print(f"Tasa de exito:        {stats['success_rate']}%")
        print()
        print(f"Consecutivos:")
        print(f"  Exitos:             {stats['consecutive_success']}")
        print(f"  Errores:            {stats['consecutive_errors']}")
        print()
        print(f"Historial de delays (ultimos 10):")
        for i, delay in enumerate(stats['delay_history'], 1):
            print(f"  {i}. {delay:.2f}s")
        print("="*60)
        print()

    def _update_history(self):
        """Actualiza el historial de delays"""
        self.delay_history.append(self.delay)
        # Mantener solo los últimos 20
        if len(self.delay_history) > 20:
            self.delay_history = self.delay_history[-20:]


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()

    limiter = AdaptiveRateLimiter(
        initial_delay=2.0,
        min_delay=0.5,
        max_delay=10.0
    )

    # Simular requests
    print("Simulando 10 requests exitosos...")
    for i in range(10):
        limiter.on_success()
        print(f"Request {i+1}: delay={limiter.get_delay():.2f}s")

    print()
    print("Simulando 2 rate limits (429)...")
    for i in range(2):
        limiter.on_rate_limit()
        print(f"429 #{i+1}: delay={limiter.get_delay():.2f}s")

    print()
    print("Simulando 5 errores...")
    for i in range(5):
        limiter.on_error()
        print(f"Error #{i+1}: delay={limiter.get_delay():.2f}s")

    # Mostrar estadísticas
    limiter.print_stats()
