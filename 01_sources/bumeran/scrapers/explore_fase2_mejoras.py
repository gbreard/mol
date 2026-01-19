"""
Test de Mejoras Críticas - Fase 2
==================================

Verifica que todas las mejoras implementadas en la Fase 2 funcionen correctamente:
1. Normalización de fechas ISO 8601
2. Limpieza de HTML entities
3. Sistema de métricas de performance

Uso:
    python test_fase2_mejoras.py
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "02_consolidation" / "scripts"))

# ===== TEST 1: NORMALIZACIÓN DE FECHAS =====

def test_normalizacion_fechas():
    """Verifica que las fechas se normalicen correctamente"""
    logger.info("="*70)
    logger.info("TEST 1: Normalización de fechas ISO 8601")
    logger.info("="*70)

    from bumeran_scraper import normalizar_fecha_iso

    # Test 1: Fecha sin hora
    result = normalizar_fecha_iso("30-10-2025")
    assert result['fecha_iso'] == "2025-10-30", f"❌ Fecha ISO incorrecta: {result['fecha_iso']}"
    assert result['fecha_datetime_iso'].startswith("2025-10-30T00:00:00-03:00"), f"❌ Datetime incorrecto"
    logger.info(f"✅ Fecha sin hora: '30-10-2025' → '{result['fecha_iso']}'")

    # Test 2: Fecha con hora
    result = normalizar_fecha_iso("30-10-2025 14:30")
    assert result['fecha_iso'] == "2025-10-30", f"❌ Fecha ISO incorrecta"
    assert "14:30:00" in result['fecha_datetime_iso'], f"❌ Hora no preservada"
    logger.info(f"✅ Fecha con hora: '30-10-2025 14:30' → '{result['fecha_datetime_iso']}'")

    # Test 3: Fecha None
    result = normalizar_fecha_iso(None)
    assert result['fecha_iso'] is None, f"❌ None debería retornar None"
    logger.info(f"✅ Fecha None manejada correctamente")

    # Test 4: Timezone Argentina (UTC-3)
    result = normalizar_fecha_iso("01-01-2025")
    assert "-03:00" in result['fecha_datetime_iso'], f"❌ Timezone incorrecto"
    logger.info(f"✅ Timezone Argentina (-03:00) aplicado")

    logger.info("")
    logger.info("✅ NORMALIZACIÓN DE FECHAS FUNCIONA CORRECTAMENTE")
    return True


# ===== TEST 2: LIMPIEZA DE HTML =====

def test_limpieza_html():
    """Verifica que la limpieza de HTML funcione"""
    logger.info("")
    logger.info("="*70)
    logger.info("TEST 2: Limpieza de HTML entities")
    logger.info("="*70)

    from bumeran_scraper import limpiar_texto_html

    # Test 1: &nbsp;
    texto = "Buscamos&nbsp;desarrollador&nbsp;Python"
    limpio = limpiar_texto_html(texto)
    assert "  " not in limpio, f"❌ Múltiples espacios no eliminados"
    assert limpio == "Buscamos desarrollador Python", f"❌ Resultado incorrecto: {limpio}"
    logger.info(f"✅ &nbsp; → espacio: '{texto}' → '{limpio}'")

    # Test 2: HTML entities numéricos
    texto = "&#x1f50e;&#x20;Búsqueda"
    limpio = limpiar_texto_html(texto)
    assert limpio.startswith("🔎"), f"❌ HTML entity no decodificado: {limpio}"
    logger.info(f"✅ HTML numeric entity: '&#x1f50e;' → '🔎'")

    # Test 3: Múltiples espacios y saltos de línea
    texto = "Texto   con    espacios\n\n\nmúltiples"
    limpio = limpiar_texto_html(texto)
    assert "  " not in limpio, f"❌ Múltiples espacios persisten"
    logger.info(f"✅ Espacios normalizados: '{texto}' → '{limpio}'")

    # Test 4: None y vacío
    assert limpiar_texto_html(None) is None, f"❌ None no manejado"
    assert limpiar_texto_html("") == "", f"❌ String vacío no manejado"
    logger.info(f"✅ None y vacío manejados correctamente")

    logger.info("")
    logger.info("✅ LIMPIEZA DE HTML FUNCIONA CORRECTAMENTE")
    return True


# ===== TEST 3: SISTEMA DE MÉTRICAS =====

def test_metricas():
    """Verifica que el sistema de métricas funcione"""
    logger.info("")
    logger.info("="*70)
    logger.info("TEST 3: Sistema de métricas de performance")
    logger.info("="*70)

    from scraping_metrics import ScrapingMetrics
    import time

    metrics = ScrapingMetrics()

    # Test 1: Ciclo completo
    metrics.start()
    logger.info("✅ metrics.start() ejecutado")

    # Simular 2 páginas exitosas
    for i in range(2):
        metrics.page_start()
        time.sleep(0.1)  # Simular scraping
        metrics.page_end(
            offers_count=20,
            new_offers=15,
            validation_rate=98.5
        )

    # Simular 1 página fallida
    metrics.page_start()
    time.sleep(0.05)
    metrics.page_end(failed=True)

    metrics.end()
    logger.info("✅ metrics.end() ejecutado")

    # Verificar reporte
    report = metrics.get_report()

    assert report['pages_scraped'] == 2, f"❌ Páginas scrapeadas incorrectas"
    assert report['pages_failed'] == 1, f"❌ Páginas fallidas incorrectas"
    assert report['offers_total'] == 40, f"❌ Ofertas totales incorrectas: {report['offers_total']}"
    assert report['offers_new'] == 30, f"❌ Ofertas nuevas incorrectas"
    assert report['offers_duplicates'] == 10, f"❌ Duplicados incorrectos"
    assert report['validation_rate_avg'] == 98.5, f"❌ Tasa validación incorrecta"

    logger.info(f"✅ Páginas: {report['pages_scraped']} exitosas, {report['pages_failed']} fallidas")
    logger.info(f"✅ Ofertas: {report['offers_total']} total, {report['offers_new']} nuevas")
    logger.info(f"✅ Validación: {report['validation_rate_avg']}% promedio")
    logger.info(f"✅ Tiempo total: {report['total_time_formatted']}")

    # Test 2: Errores y warnings
    metrics.add_error("connection", "Timeout en API")
    metrics.add_warning("validation", "Tasa baja en página 5")

    report = metrics.get_report()
    assert report['errors_count'] == 1, f"❌ Errores no registrados"
    assert report['warnings_count'] == 1, f"❌ Warnings no registrados"
    logger.info(f"✅ Errores y warnings registrados correctamente")

    # Test 3: Imprimir reporte
    logger.info("")
    logger.info("✅ Imprimiendo reporte completo:")
    metrics.print_report()

    logger.info("✅ SISTEMA DE MÉTRICAS FUNCIONA CORRECTAMENTE")
    return True


# ===== TEST 4: INTEGRACIÓN COMPLETA =====

def test_integracion_scraping():
    """Test de integración: scraping real con todas las mejoras"""
    logger.info("")
    logger.info("="*70)
    logger.info("TEST 4: Integración completa (scraping real)")
    logger.info("="*70)

    from bumeran_scraper import BumeranScraper

    scraper = BumeranScraper()

    # Hacer un request de prueba (solo 1 página)
    logger.info("Scrapeando 1 página de prueba con keyword 'python'...")

    ofertas = scraper.scrapear_todo(
        max_paginas=1,
        page_size=10,
        query="python",
        incremental=False  # Modo full para test
    )

    logger.info(f"✅ Scraping completado: {len(ofertas)} ofertas")

    # Procesar ofertas
    df = scraper.procesar_ofertas(ofertas)

    # Verificar nuevas columnas de fechas ISO
    columnas_fechas = [
        'fecha_publicacion_original',
        'fecha_publicacion_iso',
        'fecha_publicacion_datetime'
    ]

    for col in columnas_fechas:
        if col not in df.columns:
            raise AssertionError(f"❌ Columna {col} no encontrada")

    logger.info(f"✅ Columnas de fechas ISO presentes: {columnas_fechas}")

    # Verificar formato ISO
    fecha_iso = df['fecha_publicacion_iso'].iloc[0]
    if fecha_iso and '-' in fecha_iso:
        # Debe ser YYYY-MM-DD
        parts = fecha_iso.split('-')
        if len(parts[0]) != 4:
            raise AssertionError(f"❌ Formato ISO incorrecto: {fecha_iso}")

    logger.info(f"✅ Formato ISO 8601 verificado: {fecha_iso}")

    # Verificar limpieza de HTML en títulos
    titulo = df['titulo'].iloc[0]
    if titulo:
        # No debería tener &nbsp; ni HTML entities sin procesar
        if '&nbsp;' in titulo or '&#' in titulo:
            logger.warning(f"⚠️ HTML entities sin limpiar en título: {titulo}")
        else:
            logger.info(f"✅ Título limpio: '{titulo[:50]}...'")

    logger.info("")
    logger.info("✅ INTEGRACIÓN COMPLETA FUNCIONA CORRECTAMENTE")
    return True


# ===== MAIN =====

def main():
    """Ejecuta todos los tests"""
    logger.info("")
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + " "*20 + "TEST DE MEJORAS FASE 2" + " "*26 + "║")
    logger.info("╚" + "="*68 + "╝")
    logger.info("")

    tests = [
        ("Normalización Fechas", test_normalizacion_fechas),
        ("Limpieza HTML", test_limpieza_html),
        ("Sistema Métricas", test_metricas),
        ("Integración Completa", test_integracion_scraping)
    ]

    resultados = {}

    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados[nombre] = resultado
        except Exception as e:
            logger.error(f"")
            logger.error(f"❌ ERROR EJECUTANDO TEST '{nombre}': {e}")
            logger.error(f"")
            import traceback
            traceback.print_exc()
            resultados[nombre] = False

    # Resumen
    logger.info("")
    logger.info("="*70)
    logger.info("RESUMEN DE TESTS")
    logger.info("="*70)

    total = len(resultados)
    exitosos = sum(1 for r in resultados.values() if r)
    fallidos = total - exitosos

    for nombre, resultado in resultados.items():
        estado = "✅ PASS" if resultado else "❌ FAIL"
        logger.info(f"  {estado}  {nombre}")

    logger.info("")
    logger.info(f"Total: {exitosos}/{total} tests exitosos")

    if fallidos == 0:
        logger.info("")
        logger.info("╔" + "="*68 + "╗")
        logger.info("║" + " "*10 + "🎉 TODAS LAS MEJORAS DE FASE 2 FUNCIONAN 🎉" + " "*15 + "║")
        logger.info("╚" + "="*68 + "╝")
        logger.info("")
        return 0
    else:
        logger.error("")
        logger.error(f"❌ {fallidos} test(s) fallaron")
        logger.error("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
