"""
Test de Mejoras Fase 3 - Optimizaciones
========================================

Verifica que las 3 optimizaciones de Fase 3 funcionen correctamente:
1. Rate limiting adaptativo
2. Circuit breaker
3. Sistema de alertas

Uso:
    python test_fase3_mejoras.py
"""

import sys
import time
from pathlib import Path

# Asegurar que podemos importar los módulos
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("TEST FASE 3 - OPTIMIZACIONES")
print("="*70)
print()

# =====================================================================
# TEST 1: Adaptive Rate Limiter
# =====================================================================

print("TEST 1: Adaptive Rate Limiter")
print("-" * 70)

try:
    from adaptive_rate_limiter import AdaptiveRateLimiter

    # Crear limiter
    limiter = AdaptiveRateLimiter(
        initial_delay=2.0,
        min_delay=0.5,
        max_delay=10.0,
        success_threshold=5,
        error_threshold=3
    )

    print(f"[OK] Importacion exitosa")
    print(f"  Delay inicial: {limiter.get_delay()}s")

    # Test 1.1: Successes reducen delay
    print("\n1.1. Testing: 5 éxitos consecutivos deberían reducir delay")
    for i in range(5):
        limiter.on_success()

    delay_after_success = limiter.get_delay()
    print(f"  Delay después de 5 éxitos: {delay_after_success:.2f}s")

    if delay_after_success < 2.0:
        print("  [OK] PASS: Delay reducido correctamente")
    else:
        print("  [FAIL] FAIL: Delay no se redujo")
        sys.exit(1)

    # Test 1.2: Rate limit aumenta delay
    print("\n1.2. Testing: 429 (rate limit) debería aumentar delay")
    delay_before = limiter.get_delay()
    limiter.on_rate_limit()
    delay_after_429 = limiter.get_delay()

    print(f"  Delay antes: {delay_before:.2f}s -> después: {delay_after_429:.2f}s")

    if delay_after_429 > delay_before:
        print("  [OK] PASS: Delay aumentado en rate limit")
    else:
        print("  [FAIL] FAIL: Delay no aumentó")
        sys.exit(1)

    # Test 1.3: Errores consecutivos aumentan delay
    print("\n1.3. Testing: 3 errores consecutivos deberían aumentar delay")
    limiter.reset_to_initial()  # Reset
    delay_before = limiter.get_delay()

    for i in range(3):
        limiter.on_error()

    delay_after_errors = limiter.get_delay()
    print(f"  Delay antes: {delay_before:.2f}s -> después: {delay_after_errors:.2f}s")

    if delay_after_errors > delay_before:
        print("  [OK] PASS: Delay aumentado tras errores")
    else:
        print("  [FAIL] FAIL: Delay no aumentó")
        sys.exit(1)

    # Test 1.4: Stats
    print("\n1.4. Testing: Estadísticas")
    stats = limiter.get_stats()

    if stats['total_requests'] > 0 and stats['current_delay'] > 0:
        print("  [OK] PASS: Estadísticas generadas correctamente")
        print(f"    Total requests: {stats['total_requests']}")
        print(f"    Delay actual: {stats['current_delay']}s")
    else:
        print("  [FAIL] FAIL: Estadísticas incorrectas")
        sys.exit(1)

    print("\n[PASS] TEST 1 COMPLETADO: Adaptive Rate Limiter OK")

except ImportError as e:
    print(f"[FAIL] FAIL: No se pudo importar AdaptiveRateLimiter: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] FAIL: Error en test de AdaptiveRateLimiter: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print()

# =====================================================================
# TEST 2: Circuit Breaker
# =====================================================================

print("TEST 2: Circuit Breaker")
print("-" * 70)

try:
    from circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState

    # Test 2.1: Estado inicial CLOSED
    print("2.1. Testing: Estado inicial debe ser CLOSED")
    breaker = CircuitBreaker(max_failures=3, timeout=2, name="TestAPI")

    if breaker.get_state() == CircuitState.CLOSED:
        print("  [OK] PASS: Estado inicial CLOSED")
    else:
        print(f"  [FAIL] FAIL: Estado inicial incorrecto: {breaker.get_state()}")
        sys.exit(1)

    # Test 2.2: Función exitosa no abre circuito
    print("\n2.2. Testing: Función exitosa no abre circuito")

    def successful_func():
        return "OK"

    result = breaker.call(successful_func)

    if result == "OK" and breaker.get_state() == CircuitState.CLOSED:
        print("  [OK] PASS: Función exitosa, circuito cerrado")
    else:
        print("  [FAIL] FAIL: Circuito no se mantuvo cerrado")
        sys.exit(1)

    # Test 2.3: Fallos consecutivos abren circuito
    print("\n2.3. Testing: 3 fallos consecutivos deberían abrir circuito")

    def failing_func():
        raise Exception("API Error")

    # Provocar 3 fallos
    for i in range(3):
        try:
            breaker.call(failing_func)
        except Exception:
            pass  # Esperamos que falle

    if breaker.get_state() == CircuitState.OPEN:
        print("  [OK] PASS: Circuito abierto tras 3 fallos")
    else:
        print(f"  [FAIL] FAIL: Circuito no se abrió, estado: {breaker.get_state()}")
        sys.exit(1)

    # Test 2.4: Circuito abierto rechaza requests
    print("\n2.4. Testing: Circuito abierto rechaza nuevos requests")

    try:
        breaker.call(successful_func)
        print("  [FAIL] FAIL: No lanzó CircuitOpenError")
        sys.exit(1)
    except CircuitOpenError as e:
        print(f"  [OK] PASS: CircuitOpenError lanzado: {e}")

    # Test 2.5: Timeout pasa a HALF_OPEN
    print("\n2.5. Testing: Timeout debería pasar a HALF_OPEN")
    print(f"  Esperando {breaker.timeout}s (timeout)...")
    time.sleep(breaker.timeout + 0.5)

    try:
        result = breaker.call(successful_func)
        if breaker.get_state() == CircuitState.CLOSED:
            print("  [OK] PASS: Circuito recuperado a CLOSED tras éxito en HALF_OPEN")
        else:
            print(f"  [FAIL] FAIL: Estado incorrecto: {breaker.get_state()}")
            sys.exit(1)
    except CircuitOpenError:
        print("  [FAIL] FAIL: Circuito sigue abierto después del timeout")
        sys.exit(1)

    # Test 2.6: Stats
    print("\n2.6. Testing: Estadísticas")
    stats = breaker.get_stats()

    if stats['total_calls'] > 0 and stats['times_opened'] > 0:
        print("  [OK] PASS: Estadísticas generadas correctamente")
        print(f"    Total calls: {stats['total_calls']}")
        print(f"    Veces abierto: {stats['times_opened']}")
        print(f"    Estado: {stats['state']}")
    else:
        print("  [FAIL] FAIL: Estadísticas incorrectas")
        sys.exit(1)

    print("\n[PASS] TEST 2 COMPLETADO: Circuit Breaker OK")

except ImportError as e:
    print(f"[FAIL] FAIL: No se pudo importar CircuitBreaker: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] FAIL: Error en test de CircuitBreaker: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print()

# =====================================================================
# TEST 3: Alert Manager
# =====================================================================

print("TEST 3: Alert Manager")
print("-" * 70)

try:
    from alert_manager import AlertManager, AlertLevel

    # Test 3.1: Crear alertas de diferentes niveles
    print("3.1. Testing: Creación de alertas")
    alert_mgr = AlertManager(email_enabled=False, enable_console_output=False)

    alert_mgr.add_alert(AlertLevel.INFO, "Test info message")
    alert_mgr.add_alert(AlertLevel.WARNING, "Test warning message")
    alert_mgr.add_alert(AlertLevel.ERROR, "Test error message")
    alert_mgr.add_alert(AlertLevel.CRITICAL, "Test critical message")

    if len(alert_mgr.alerts) == 4:
        print("  [OK] PASS: 4 alertas creadas correctamente")
    else:
        print(f"  [FAIL] FAIL: Esperaba 4 alertas, obtuvo {len(alert_mgr.alerts)}")
        sys.exit(1)

    # Test 3.2: Filtrar por nivel
    print("\n3.2. Testing: Filtrado por nivel")
    critical_alerts = alert_mgr.get_alerts_by_level(AlertLevel.CRITICAL)

    if len(critical_alerts) == 1:
        print("  [OK] PASS: Filtrado por nivel funciona")
    else:
        print(f"  [FAIL] FAIL: Esperaba 1 alerta CRITICAL, obtuvo {len(critical_alerts)}")
        sys.exit(1)

    # Test 3.3: has_alerts
    print("\n3.3. Testing: has_alerts()")

    if alert_mgr.has_alerts(min_level=AlertLevel.WARNING):
        print("  [OK] PASS: Detecta alertas >= WARNING")
    else:
        print("  [FAIL] FAIL: No detectó alertas WARNING+")
        sys.exit(1)

    # Test 3.4: check_metrics genera alertas
    print("\n3.4. Testing: check_metrics() genera alertas")
    alert_mgr.clear_alerts()

    bad_metrics = {
        'pages_scraped': 2,
        'pages_total': 10,
        'success_rate': 20.0,  # Muy bajo < 50%
        'validation_rate_avg': 65.0,  # Bajo < 80%
        'errors_count': 5,
        'offers_total': 0  # Sin ofertas
    }

    alert_mgr.check_metrics(bad_metrics)

    if alert_mgr.has_alerts(min_level=AlertLevel.WARNING):
        print(f"  [OK] PASS: check_metrics() generó {len(alert_mgr.alerts)} alertas")
        for alert in alert_mgr.alerts[:3]:  # Mostrar primeras 3
            print(f"    - [{alert['level']}] {alert['message']}")
    else:
        print("  [FAIL] FAIL: check_metrics() no generó alertas")
        sys.exit(1)

    # Test 3.5: check_circuit_breaker
    print("\n3.5. Testing: check_circuit_breaker() genera alertas")
    alert_mgr.clear_alerts()

    breaker_stats_open = {
        'state': 'open',
        'consecutive_failures': 5,
        'times_opened': 1
    }

    alert_mgr.check_circuit_breaker(breaker_stats_open)

    if alert_mgr.has_alerts(min_level=AlertLevel.CRITICAL):
        print("  [OK] PASS: Circuit breaker abierto genera alerta CRITICAL")
    else:
        print("  [FAIL] FAIL: No se generó alerta para circuit breaker abierto")
        sys.exit(1)

    # Test 3.6: check_rate_limiter
    print("\n3.6. Testing: check_rate_limiter() genera alertas")
    alert_mgr.clear_alerts()

    limiter_stats_maxed = {
        'current_delay': 10.0,
        'max_delay': 10.0,
        'total_rate_limits': 8  # > 5
    }

    alert_mgr.check_rate_limiter(limiter_stats_maxed)

    if len(alert_mgr.alerts) >= 2:  # Debería generar 2 warnings
        print("  [OK] PASS: Rate limiter en max delay genera alertas")
    else:
        print(f"  [FAIL] FAIL: Esperaba >= 2 alertas, obtuvo {len(alert_mgr.alerts)}")
        sys.exit(1)

    print("\n[PASS] TEST 3 COMPLETADO: Alert Manager OK")

except ImportError as e:
    print(f"[FAIL] FAIL: No se pudo importar AlertManager: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] FAIL: Error en test de AlertManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print()

# =====================================================================
# TEST 4: Integración con Scraper
# =====================================================================

print("TEST 4: Integración con Scraper")
print("-" * 70)

try:
    from bumeran_scraper import BumeranScraper

    print("4.1. Testing: Scraper inicializa con optimizaciones Fase 3")

    scraper = BumeranScraper(delay_between_requests=1.0)

    # Verificar que se inicializaron los componentes
    has_rate_limiter = scraper.rate_limiter is not None
    has_circuit_breaker = scraper.circuit_breaker is not None
    has_alert_manager = scraper.alert_manager is not None

    print(f"  Rate Limiter: {'[OK]' if has_rate_limiter else '[FAIL]'}")
    print(f"  Circuit Breaker: {'[OK]' if has_circuit_breaker else '[FAIL]'}")
    print(f"  Alert Manager: {'[OK]' if has_alert_manager else '[FAIL]'}")

    if has_rate_limiter and has_circuit_breaker and has_alert_manager:
        print("  [OK] PASS: Todas las optimizaciones inicializadas")
    else:
        print("  [FAIL] FAIL: Faltan componentes de Fase 3")
        sys.exit(1)

    # Test 4.2: Scraping real (limitado)
    print("\n4.2. Testing: Scraping real con optimizaciones")
    print("  Scrapeando 1 página (20 ofertas)...")

    ofertas = scraper.scrapear_todo(
        max_paginas=1,
        max_resultados=20,
        incremental=False
    )

    if len(ofertas) > 0:
        print(f"  [OK] PASS: Scraping exitoso - {len(ofertas)} ofertas")
    else:
        print("  [FAIL] FAIL: No se scrapearon ofertas")
        sys.exit(1)

    # Verificar que rate limiter registró requests
    if has_rate_limiter:
        stats = scraper.rate_limiter.get_stats()
        if stats['total_requests'] > 0:
            print(f"  [OK] PASS: Rate limiter registró {stats['total_requests']} requests")
        else:
            print("  [WARN] WARNING: Rate limiter no registró requests")

    # Verificar que circuit breaker registró calls
    if has_circuit_breaker:
        stats = scraper.circuit_breaker.get_stats()
        if stats['total_calls'] > 0:
            print(f"  [OK] PASS: Circuit breaker registró {stats['total_calls']} calls")
        else:
            print("  [WARN] WARNING: Circuit breaker no registró calls")

    print("\n[PASS] TEST 4 COMPLETADO: Integración OK")

except ImportError as e:
    print(f"[FAIL] FAIL: No se pudo importar BumeranScraper: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] FAIL: Error en test de integración: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =====================================================================
# RESUMEN FINAL
# =====================================================================

print()
print("="*70)
print("RESUMEN DE TESTS")
print("="*70)
print()
print("[PASS] TEST 1: Adaptive Rate Limiter - OK")
print("[PASS] TEST 2: Circuit Breaker - OK")
print("[PASS] TEST 3: Alert Manager - OK")
print("[PASS] TEST 4: Integración con Scraper - OK")
print()
print("="*70)
print(" TODAS LAS OPTIMIZACIONES DE FASE 3 FUNCIONAN ")
print("="*70)
print()
print("Componentes verificados:")
print("  [OK] AdaptiveRateLimiter: Ajusta delay automáticamente")
print("  [OK] CircuitBreaker: Protege contra fallos consecutivos")
print("  [OK] AlertManager: Detecta y reporta problemas")
print("  [OK] Integración: Todo funciona junto en el scraper")
print()
print("La Fase 3 está COMPLETA y lista para producción! ")
print()
