"""
Circuit Breaker Pattern
=======================

Protege el sistema deteniendo requests a una API que falla consecutivamente.

Estados:
- CLOSED: Normal, requests permitidos
- OPEN: Circuito abierto, no hacer requests (API caída)
- HALF_OPEN: Probando si API ya funciona

Flujo:
1. CLOSED → max_failures alcanzado → OPEN
2. OPEN → timeout pasado → HALF_OPEN
3. HALF_OPEN → request exitoso → CLOSED
4. HALF_OPEN → request falla → OPEN

Uso:
    from circuit_breaker import CircuitBreaker, CircuitOpenError

    breaker = CircuitBreaker(max_failures=5, timeout=30)

    try:
        result = breaker.call(api_function, arg1, arg2)
    except CircuitOpenError:
        logger.error("API no disponible, circuito abierto")
"""

import time
import logging
from typing import Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"        # Todo bien, requests normales
    OPEN = "open"            # Circuito abierto, API caída
    HALF_OPEN = "half_open"  # Probando si API ya funciona


class CircuitOpenError(Exception):
    """
    Excepción lanzada cuando el circuito está abierto

    Indica que la API no está disponible y no se deben hacer requests
    """
    pass


class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker

    Previene requests innecesarios a APIs que están fallando
    """

    def __init__(
        self,
        max_failures: int = 5,
        timeout: int = 30,
        name: str = "CircuitBreaker"
    ):
        """
        Inicializa el circuit breaker

        Args:
            max_failures: Máximo de fallos consecutivos antes de abrir circuito
            timeout: Segundos antes de pasar de OPEN → HALF_OPEN
            name: Nombre del circuit breaker para logging
        """
        self.max_failures = max_failures
        self.timeout = timeout
        self.name = name

        # Estado
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.opened_at = None
        self.last_failure_time = None

        # Estadísticas
        self.total_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_rejected = 0  # Calls rechazadas por circuito abierto
        self.times_opened = 0

        logger.debug(
            f"{self.name}: Inicializado "
            f"(max_failures={max_failures}, timeout={timeout}s)"
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función protegida por el circuit breaker

        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función

        Returns:
            Resultado de la función

        Raises:
            CircuitOpenError: Si el circuito está abierto
            Exception: Cualquier excepción lanzada por la función
        """
        self.total_calls += 1

        # Verificar estado del circuito
        if self.state == CircuitState.OPEN:
            # Verificar si ya pasó el timeout
            time_since_open = time.time() - self.opened_at

            if time_since_open >= self.timeout:
                logger.info(
                    f"{self.name}: Timeout alcanzado ({self.timeout}s), "
                    f"cambiando a HALF_OPEN"
                )
                self.state = CircuitState.HALF_OPEN
            else:
                # Circuito sigue abierto
                self.total_rejected += 1
                remaining = self.timeout - time_since_open
                raise CircuitOpenError(
                    f"{self.name}: Circuito abierto. "
                    f"Reintentar en {remaining:.0f}s"
                )

        # Intentar ejecutar la función
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """Registra un éxito"""
        self.total_successes += 1
        self.failures = 0  # Reset failures consecutivos

        if self.state == CircuitState.HALF_OPEN:
            # Éxito en HALF_OPEN → cerrar circuito
            logger.info(
                f"{self.name}: Request exitoso en HALF_OPEN → "
                f"cerrando circuito"
            )
            self.state = CircuitState.CLOSED
            self.successes = 0

        elif self.state == CircuitState.CLOSED:
            self.successes += 1

    def _on_failure(self, exception: Exception):
        """Registra un fallo"""
        self.total_failures += 1
        self.failures += 1
        self.successes = 0
        self.last_failure_time = time.time()

        logger.warning(
            f"{self.name}: Fallo #{self.failures}/{self.max_failures} - {type(exception).__name__}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Fallo en HALF_OPEN → volver a abrir
            logger.error(
                f"{self.name}: Fallo en HALF_OPEN → "
                f"volviendo a OPEN"
            )
            self._open_circuit()

        elif self.state == CircuitState.CLOSED:
            if self.failures >= self.max_failures:
                # Alcanzado máximo de fallos → abrir circuito
                self._open_circuit()

    def _open_circuit(self):
        """Abre el circuito (OPEN)"""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.times_opened += 1

        logger.error(
            f"{self.name}: CIRCUITO ABIERTO "
            f"({self.failures} fallos consecutivos). "
            f"Esperando {self.timeout}s antes de reintentar..."
        )

    def reset(self):
        """Resetea el circuit breaker manualmente"""
        logger.info(f"{self.name}: Reset manual")
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.opened_at = None

    def get_state(self) -> CircuitState:
        """
        Obtiene el estado actual del circuito

        Returns:
            CircuitState actual
        """
        return self.state

    def is_open(self) -> bool:
        """
        Verifica si el circuito está abierto

        Returns:
            True si está abierto (OPEN o HALF_OPEN)
        """
        return self.state in (CircuitState.OPEN, CircuitState.HALF_OPEN)

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del circuit breaker

        Returns:
            Dict con estadísticas
        """
        success_rate = (
            (self.total_successes / self.total_calls * 100)
            if self.total_calls > 0 else 0
        )

        time_in_state = None
        if self.state == CircuitState.OPEN and self.opened_at:
            time_in_state = time.time() - self.opened_at

        return {
            'name': self.name,
            'state': self.state.value,
            'consecutive_failures': self.failures,
            'consecutive_successes': self.successes,
            'total_calls': self.total_calls,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'total_rejected': self.total_rejected,
            'success_rate': round(success_rate, 2),
            'times_opened': self.times_opened,
            'time_in_state_seconds': round(time_in_state, 2) if time_in_state else None,
            'max_failures': self.max_failures,
            'timeout': self.timeout
        }

    def print_stats(self):
        """Imprime estadísticas en consola"""
        stats = self.get_stats()

        print()
        print("="*60)
        print(f"CIRCUIT BREAKER - {stats['name']}")
        print("="*60)
        print(f"Estado:               {stats['state'].upper()}")
        print(f"Fallos consecutivos:  {stats['consecutive_failures']}/{stats['max_failures']}")
        print()
        print(f"Total calls:          {stats['total_calls']}")
        print(f"  Exitosos:           {stats['total_successes']}")
        print(f"  Fallidos:           {stats['total_failures']}")
        print(f"  Rechazados:         {stats['total_rejected']}")
        print(f"Tasa de exito:        {stats['success_rate']}%")
        print()
        print(f"Veces abierto:        {stats['times_opened']}")

        if stats['state'] == 'open' and stats['time_in_state_seconds']:
            remaining = stats['timeout'] - stats['time_in_state_seconds']
            print(f"Tiempo en OPEN:       {stats['time_in_state_seconds']:.0f}s")
            print(f"Reintentar en:        {max(0, remaining):.0f}s")

        print("="*60)
        print()


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()

    # Simular API
    def api_call_success():
        return "OK"

    def api_call_fail():
        raise Exception("API Error")

    breaker = CircuitBreaker(max_failures=3, timeout=5, name="TestAPI")

    # Simular 3 fallos consecutivos → abre circuito
    print("Simulando 3 fallos consecutivos...")
    for i in range(3):
        try:
            breaker.call(api_call_fail)
        except Exception as e:
            print(f"  Fallo #{i+1}: {e}")

    print()

    # Intentar call con circuito abierto
    print("Intentando call con circuito abierto...")
    try:
        breaker.call(api_call_success)
    except CircuitOpenError as e:
        print(f"  Rechazado: {e}")

    print()

    # Esperar timeout
    print(f"Esperando {breaker.timeout}s (timeout)...")
    time.sleep(breaker.timeout)

    print()

    # Intentar de nuevo (debería pasar a HALF_OPEN y funcionar)
    print("Intentando de nuevo tras timeout...")
    try:
        result = breaker.call(api_call_success)
        print(f"  Exito: {result} (circuito cerrado)")
    except Exception as e:
        print(f"  Error: {e}")

    # Mostrar estadísticas
    breaker.print_stats()
