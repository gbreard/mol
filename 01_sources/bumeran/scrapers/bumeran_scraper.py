"""
Bumeran Scraper - API REST
============================

Scraper para Bumeran.com.ar usando su API interna.

Descubrimiento:
- Endpoint: POST https://www.bumeran.com.ar/api/avisos/searchV2
- Headers: x-site-id: "BMAR", x-pre-session-token: UUID
- Ofertas disponibles: ~12,000
- Campos: 40+

Uso:
    scraper = BumeranScraper()
    ofertas = scraper.scrapear_todo(max_paginas=10)
    scraper.save_to_csv(ofertas, "bumeran_ofertas.csv")
"""

import requests
import pandas as pd
import json
import time
import uuid
import sys
import html
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log
)
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar path para importar incremental_tracker
# Ruta: scrapers -> bumeran -> 01_sources -> Webscrapping (root)
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
if str(consolidation_scripts) not in sys.path:
    sys.path.insert(0, str(consolidation_scripts))

try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    # Si no encuentra el módulo, crear un dummy tracker
    logger.warning(f"No se pudo importar IncrementalTracker: {e}")
    logger.warning("Modo incremental deshabilitado")
    IncrementalTracker = None

# Importar schemas de validación
try:
    from bumeran_schemas import validar_respuesta_api, BumeranOfertaAPI
except ImportError as e:
    logger.warning(f"No se pudieron importar schemas de validación: {e}")
    logger.warning("Validación de schema deshabilitada")
    validar_respuesta_api = None
    BumeranOfertaAPI = None

# Importar sistema de métricas
try:
    from scraping_metrics import ScrapingMetrics
except ImportError as e:
    logger.warning(f"No se pudo importar ScrapingMetrics: {e}")
    logger.warning("Métricas de performance deshabilitadas")
    ScrapingMetrics = None

# Importar optimizaciones de Fase 3
try:
    from adaptive_rate_limiter import AdaptiveRateLimiter
except ImportError as e:
    logger.warning(f"No se pudo importar AdaptiveRateLimiter: {e}")
    logger.warning("Rate limiting adaptativo deshabilitado")
    AdaptiveRateLimiter = None

try:
    from circuit_breaker import CircuitBreaker, CircuitOpenError
except ImportError as e:
    logger.warning(f"No se pudo importar CircuitBreaker: {e}")
    logger.warning("Circuit breaker deshabilitado")
    CircuitBreaker = None
    CircuitOpenError = Exception  # Fallback

try:
    from alert_manager import AlertManager, AlertLevel
except ImportError as e:
    logger.warning(f"No se pudo importar AlertManager: {e}")
    logger.warning("Sistema de alertas deshabilitado")
    AlertManager = None
    AlertLevel = None


# ===== FUNCIONES HELPER PARA PROCESAMIENTO DE DATOS =====

def normalizar_fecha_iso(fecha_str: str) -> Dict[str, Optional[str]]:
    """
    Convierte fecha de formato DD-MM-YYYY a ISO 8601 con timezone Argentina

    Args:
        fecha_str: Fecha en formato "DD-MM-YYYY" o "DD-MM-YYYY HH:MM"

    Returns:
        Dict con:
        - fecha_iso: "YYYY-MM-DD"
        - fecha_datetime_iso: "YYYY-MM-DDTHH:MM:SS-03:00"
        - fecha_original: Input original
    """
    if not fecha_str or pd.isna(fecha_str):
        return {
            'fecha_iso': None,
            'fecha_datetime_iso': None,
            'fecha_original': fecha_str
        }

    try:
        # Timezone de Argentina (UTC-3)
        tz_argentina = timezone(timedelta(hours=-3))

        # Separar fecha y hora si existe
        parts = fecha_str.strip().split(' ')
        fecha_part = parts[0]
        hora_part = parts[1] if len(parts) > 1 else "00:00"

        # Parsear fecha DD-MM-YYYY
        day, month, year = fecha_part.split('-')

        # Parsear hora HH:MM (si existe)
        if ':' in hora_part:
            hour, minute = hora_part.split(':')
        else:
            hour, minute = "00", "00"

        # Crear datetime con timezone
        dt = datetime(
            int(year), int(month), int(day),
            int(hour), int(minute), 0,
            tzinfo=tz_argentina
        )

        return {
            'fecha_iso': dt.strftime('%Y-%m-%d'),
            'fecha_datetime_iso': dt.isoformat(),
            'fecha_original': fecha_str
        }

    except Exception as e:
        logger.debug(f"Error normalizando fecha '{fecha_str}': {e}")
        return {
            'fecha_iso': None,
            'fecha_datetime_iso': None,
            'fecha_original': fecha_str
        }


def limpiar_texto_html(texto: str) -> str:
    """
    Limpia HTML entities y normaliza espacios en blanco

    Args:
        texto: Texto con posibles HTML entities (&nbsp;, &#x1f50e;, etc.)

    Returns:
        Texto limpio y normalizado
    """
    if not texto or pd.isna(texto):
        return texto

    try:
        # 1. Decodificar HTML entities (&nbsp; → espacio, &#x1f50e; → 🔎, etc.)
        texto_limpio = html.unescape(str(texto))

        # 2. Normalizar múltiples espacios a uno solo
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)

        # 3. Eliminar espacios al inicio y final
        texto_limpio = texto_limpio.strip()

        return texto_limpio

    except Exception as e:
        logger.debug(f"Error limpiando texto HTML: {e}")
        return texto


# ===== FUNCIONES HELPER PARA RETRY LOGIC =====

def _should_retry_response(response: Optional[requests.Response]) -> bool:
    """
    Determina si una respuesta HTTP debe ser reintentada

    Args:
        response: Respuesta de requests (o None si hubo excepción)

    Returns:
        True si debe reintentar, False si no
    """
    if response is None:
        return True  # Reintentar si no hay respuesta

    # Reintentar solo en errores transitorios del servidor
    retriable_statuses = {
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504   # Gateway Timeout
    }

    should_retry = response.status_code in retriable_statuses

    if should_retry:
        logger.warning(f"Status {response.status_code} - Se reintentará")

    return should_retry


class BumeranScraper:
    """Scraper para Bumeran.com.ar usando API REST"""

    def __init__(self, delay_between_requests: float = 2.0):
        """
        Inicializa el scraper

        Args:
            delay_between_requests: Segundos entre requests (default: 2.0)
        """
        self.base_url = "https://www.bumeran.com.ar/api/avisos/searchV2"
        self.delay = delay_between_requests
        self.session = requests.Session()

        # Directorio de datos
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generar session token único
        self.session_token = str(uuid.uuid4())

        # Headers necesarios
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Content-Type': 'application/json',
            'Referer': 'https://www.bumeran.com.ar/empleos-busqueda-ofertas.html',
            'Origin': 'https://www.bumeran.com.ar',
            'x-site-id': 'BMAR',  # Bumeran Argentina
            'x-pre-session-token': self.session_token
        }

        # Inicializar optimizaciones de Fase 3
        # Rate limiter adaptativo (reemplaza delay fijo)
        if AdaptiveRateLimiter is not None:
            self.rate_limiter = AdaptiveRateLimiter(
                initial_delay=delay_between_requests,
                min_delay=0.5,
                max_delay=10.0
            )
            logger.info("Rate limiter adaptativo habilitado (0.5s - 10.0s)")
        else:
            self.rate_limiter = None

        # Circuit breaker (protege contra fallos consecutivos)
        if CircuitBreaker is not None:
            self.circuit_breaker = CircuitBreaker(
                max_failures=5,
                timeout=30,
                name="BumeranAPI"
            )
            logger.info("Circuit breaker habilitado (max_failures=5, timeout=30s)")
        else:
            self.circuit_breaker = None

        # Alert manager (alertas de problemas)
        if AlertManager is not None:
            self.alert_manager = AlertManager(
                email_enabled=False,  # Por ahora solo consola
                enable_console_output=True
            )
            logger.info("Sistema de alertas habilitado")
        else:
            self.alert_manager = None

        # Guardar último total disponible en API (para métricas de cobertura)
        self.last_total_disponible = 0

        logger.info(f"Scraper inicializado con session token: {self.session_token}")
        logger.info(f"Delay inicial entre requests: {self.delay}s")

    def _hacer_request_api(
        self,
        payload: Dict,
        timeout: int = 30
    ) -> requests.Response:
        """
        Función interna para hacer request a la API (usada por circuit breaker)

        Args:
            payload: Datos del request POST
            timeout: Timeout en segundos

        Returns:
            Response de requests
        """
        return self.session.post(
            self.base_url,
            json=payload,
            headers=self.headers,
            timeout=timeout
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=(
            retry_if_exception_type((
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException
            )) |
            retry_if_result(_should_retry_response)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def scrapear_pagina(
        self,
        page: int = 0,
        page_size: int = 20,
        query: Optional[str] = None,
        sort: str = "FECHA"
    ) -> requests.Response:
        """
        Scrapea una página de ofertas con retry automático + circuit breaker

        Args:
            page: Número de página (0-indexed)
            page_size: Ofertas por página (default: 20, max: 100)
            query: Búsqueda por keyword (opcional)
            sort: Ordenamiento (RELEVANTES, FECHA, etc.)

        Returns:
            Response de requests (retry automático + circuit breaker)
        """
        payload = {
            "pageSize": page_size,
            "page": page,
            "sort": sort
        }

        if query:
            payload["query"] = query

        logger.info(f"Scrapeando página {page} (pageSize={page_size})")

        # Hacer request con circuit breaker (si está habilitado)
        try:
            if self.circuit_breaker is not None:
                response = self.circuit_breaker.call(
                    self._hacer_request_api,
                    payload=payload,
                    timeout=30
                )
            else:
                response = self._hacer_request_api(payload=payload, timeout=30)

        except CircuitOpenError as e:
            # Circuito abierto, API no disponible
            logger.error(f"  Circuit breaker ABIERTO: {e}")
            # Crear response dummy con error para que retry lo maneje
            response = requests.Response()
            response.status_code = 503
            response._content = b'{"error": "Circuit breaker open"}'
            return response

        # Reportar resultado al rate limiter adaptativo (si está habilitado)
        if self.rate_limiter is not None:
            if response.status_code == 200:
                self.rate_limiter.on_success()
            elif response.status_code == 429:
                self.rate_limiter.on_rate_limit()
                logger.warning(f"  Rate limit (429) - Delay adaptado a {self.rate_limiter.get_delay():.2f}s")
            elif response.status_code >= 500:
                self.rate_limiter.on_error()

        # Log de resultados
        if response.status_code == 200:
            data = response.json()
            logger.info(f"  OK - {len(data.get('content', []))} ofertas | Total: {data.get('total', 0)}")
        else:
            logger.error(f"  Error - Status code: {response.status_code}")
            logger.error(f"  Response: {response.text[:200]}")

        return response

    def scrapear_todo(
        self,
        max_paginas: int = 10,
        max_resultados: Optional[int] = None,
        page_size: int = 20,
        query: Optional[str] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """
        Scrapea múltiples páginas de ofertas

        Args:
            max_paginas: Máximo de páginas a scrapear (None = ilimitado)
            max_resultados: Máximo de ofertas totales (None = ilimitado)
            page_size: Ofertas por página (default: 20)
            query: Búsqueda por keyword (opcional)
            incremental: Si True, solo trae ofertas nuevas (default: True)

        Returns:
            Lista de ofertas
        """
        logger.info("="*70)
        logger.info("INICIANDO SCRAPING DE BUMERAN")
        logger.info("="*70)
        logger.info(f"Parametros:")
        logger.info(f"  Max paginas: {max_paginas if max_paginas else 'Ilimitado'}")
        logger.info(f"  Max resultados: {max_resultados or 'Ilimitado'}")
        logger.info(f"  Page size: {page_size}")
        logger.info(f"  Query: {query or 'Todas las ofertas'}")
        logger.info(f"  Modo: {'Incremental' if incremental else 'Full'}")
        logger.info("")

        # Inicializar sistema de métricas (Fase 2)
        metrics = None
        if ScrapingMetrics is not None:
            metrics = ScrapingMetrics()
            metrics.start()
            logger.info("Sistema de métricas activado")

        # Limpiar alertas previas
        if self.alert_manager is not None:
            self.alert_manager.clear_alerts()

        # Inicializar tracker si modo incremental
        tracker = None
        existing_ids = set()
        if incremental:
            if IncrementalTracker is None:
                logger.warning("IncrementalTracker no disponible, ejecutando en modo full")
                incremental = False
            else:
                tracker = IncrementalTracker(source='bumeran')
                existing_ids = tracker.load_scraped_ids()
                if existing_ids:
                    logger.info(f"Modo incremental: {len(existing_ids):,} IDs ya scrapeados")
                else:
                    logger.info("Primera ejecución: scrapeando TODO")

        todas_ofertas = []
        page = 0

        # Si max_paginas es None, calcular el máximo necesario
        if max_paginas is None:
            # Hacer request inicial para obtener total
            initial_response = self.scrapear_pagina(page=0, page_size=page_size, query=query)
            if initial_response.status_code == 200:
                initial_data = initial_response.json()
                total_disponible = initial_data.get('total', 0)
                self.last_total_disponible = total_disponible  # Guardar para métricas de cobertura
                max_paginas = (total_disponible // page_size) + 1
                logger.info(f"Total disponible: {total_disponible:,} ofertas ({max_paginas} páginas)")
            else:
                logger.error("No se pudo obtener información inicial de la API")
                max_paginas = 1

        while page < max_paginas:
            # Iniciar tracking de página (métricas)
            if metrics:
                metrics.page_start()

            # Scrapear página (con retry automático + circuit breaker)
            try:
                response = self.scrapear_pagina(
                    page=page,
                    page_size=page_size,
                    query=query
                )
            except Exception as e:
                logger.error(f"Error crítico en página {page}: {e}")
                if metrics:
                    metrics.page_end(failed=True)
                    metrics.add_error('scraping', f"Página {page} falló: {str(e)}", {'page': page})
                if self.alert_manager:
                    self.alert_manager.add_alert(
                        AlertLevel.ERROR,
                        f"Error crítico scrapeando página {page}: {str(e)}",
                        {'page': page, 'error': str(e)}
                    )
                break

            # Verificar respuesta exitosa
            if response.status_code != 200:
                logger.error(f"Error en página {page} - Status {response.status_code}")
                if metrics:
                    metrics.page_end(failed=True)
                    metrics.add_error('http', f"Status {response.status_code} en página {page}", {'page': page, 'status': response.status_code})
                if self.alert_manager:
                    self.alert_manager.add_alert(
                        AlertLevel.ERROR,
                        f"Error HTTP {response.status_code} en página {page}",
                        {'page': page, 'status_code': response.status_code}
                    )
                break

            data = response.json()

            if not data or not data.get('content'):
                logger.warning("No hay más ofertas disponibles")
                if metrics:
                    metrics.page_end(failed=True)
                break

            # Validar schema de la respuesta (si está disponible)
            validation_rate = 100.0  # Default
            if validar_respuesta_api is not None:
                validation_result = validar_respuesta_api(data)
                validation_rate = validation_result.tasa_exito
                logger.info(f"  Validación: {validation_result.ofertas_validas}/{validation_result.total_ofertas} ofertas válidas ({validation_rate:.1f}%)")

                # Advertir si hay problemas de validación
                if not validation_result.success:
                    logger.warning(f"  ALERTA: Tasa de validación baja ({validation_rate:.1f}%)")
                    for error in validation_result.errores[:3]:  # Mostrar primeros 3 errores
                        logger.warning(f"    - {error}")

                    if metrics:
                        metrics.add_warning('validation', f"Tasa de validación baja en página {page}: {validation_rate:.1f}%", {'page': page, 'rate': validation_rate})

                # Advertir si el schema de la API puede haber cambiado
                if validation_rate < 50.0:
                    logger.error(f"  CRÍTICO: >50% de ofertas inválidas. ¿Cambió el schema de la API?")
                    if metrics:
                        metrics.add_error('validation', f"Tasa de validación crítica en página {page}: {validation_rate:.1f}%", {'page': page, 'rate': validation_rate})

            # Agregar ofertas
            ofertas_pagina = data['content']

            # Filtrar ofertas nuevas si modo incremental
            ofertas_nuevas_count = 0
            if incremental and existing_ids:
                ofertas_nuevas = [
                    o for o in ofertas_pagina
                    if str(o.get('id')) not in existing_ids
                ]
                ofertas_nuevas_count = len(ofertas_nuevas)

                if ofertas_nuevas:
                    todas_ofertas.extend(ofertas_nuevas)
                    logger.info(f"  Página {page}: {ofertas_nuevas_count}/{len(ofertas_pagina)} ofertas nuevas")
                else:
                    logger.info(f"  Página {page}: 0/{len(ofertas_pagina)} ofertas nuevas (todas ya scrapeadas)")

                # Registrar métricas de página exitosa
                if metrics:
                    metrics.page_end(
                        offers_count=len(ofertas_pagina),
                        new_offers=ofertas_nuevas_count,
                        validation_rate=validation_rate,
                        failed=False
                    )

                # Si no hay ofertas nuevas en esta página, es posible que no haya más
                # (asume que las ofertas están ordenadas por fecha, más nuevas primero)
                if not ofertas_nuevas and page > 2:
                    logger.info("No se encontraron ofertas nuevas en esta página. Finalizando.")
                    break
            else:
                todas_ofertas.extend(ofertas_pagina)
                logger.info(f"  Página {page}: {len(ofertas_pagina)} ofertas")
                ofertas_nuevas_count = len(ofertas_pagina)

                # Registrar métricas de página exitosa
                if metrics:
                    metrics.page_end(
                        offers_count=len(ofertas_pagina),
                        new_offers=ofertas_nuevas_count,
                        validation_rate=validation_rate,
                        failed=False
                    )

            # VALIDACION CRITICA: Detectar duplicados masivos (paginación rota)
            if len(todas_ofertas) > 40:  # Solo verificar después de 2+ páginas
                ids_unicos = len(set([str(o.get('id')) for o in todas_ofertas]))
                ids_totales = len(todas_ofertas)
                tasa_duplicados = ((ids_totales - ids_unicos) / ids_totales) * 100

                # Alertar si hay muchos duplicados
                if tasa_duplicados > 50.0 and page > 5:
                    logger.warning(f"ALERTA: Alta tasa de duplicados detectada: {tasa_duplicados:.1f}%")
                    logger.warning(f"  IDs unicos: {ids_unicos}, Total ofertas: {ids_totales}")

                    if self.alert_manager:
                        self.alert_manager.add_alert(
                            AlertLevel.WARNING,
                            f"Alta tasa de duplicados: {tasa_duplicados:.1f}%",
                            {'ids_unicos': ids_unicos, 'total': ids_totales, 'page': page}
                        )

                # DETENER si paginación está rota (>90% duplicados después de varias páginas)
                if tasa_duplicados > 90.0 and page > 10:
                    logger.error(f"CRITICO: Paginacion rota detectada!")
                    logger.error(f"  Pagina {page}: {tasa_duplicados:.1f}% duplicados ({ids_unicos} IDs unicos de {ids_totales} ofertas)")
                    logger.error(f"  La API esta devolviendo las mismas ofertas en todas las paginas")
                    logger.error(f"  DETENIENDO scraping para evitar data inutil")

                    if metrics:
                        metrics.add_error(
                            'pagination',
                            f"Paginacion rota: {tasa_duplicados:.1f}% duplicados en pagina {page}",
                            {'ids_unicos': ids_unicos, 'total': ids_totales, 'page': page, 'tasa_duplicados': tasa_duplicados}
                        )

                    if self.alert_manager:
                        self.alert_manager.add_alert(
                            AlertLevel.CRITICAL,
                            f"Paginacion rota: {tasa_duplicados:.1f}% duplicados",
                            {'ids_unicos': ids_unicos, 'total': ids_totales, 'page': page}
                        )

                    # Filtrar duplicados antes de retornar
                    ids_vistos = set()
                    todas_ofertas_unicas = []
                    for oferta in todas_ofertas:
                        id_oferta = str(oferta.get('id'))
                        if id_oferta not in ids_vistos:
                            ids_vistos.add(id_oferta)
                            todas_ofertas_unicas.append(oferta)

                    todas_ofertas = todas_ofertas_unicas
                    logger.info(f"Ofertas unicas despues de deduplicacion: {len(todas_ofertas)}")
                    break

            # Verificar límite de resultados
            if max_resultados and len(todas_ofertas) >= max_resultados:
                todas_ofertas = todas_ofertas[:max_resultados]
                logger.info(f"Alcanzado limite de {max_resultados} ofertas")
                break

            # Verificar si hay más páginas
            total_disponible = data.get('total', 0)
            ofertas_scrapeadas = (page + 1) * page_size

            if ofertas_scrapeadas >= total_disponible:
                logger.info("Scrapeadas todas las ofertas disponibles")
                break

            page += 1

            # Rate limiting adaptativo (o fijo si no está disponible)
            if page < max_paginas:
                if self.rate_limiter is not None:
                    delay = self.rate_limiter.get_delay()
                    logger.debug(f"Esperando {delay:.2f}s (adaptativo)...")
                    self.rate_limiter.wait()
                else:
                    logger.debug(f"Esperando {self.delay}s...")
                    time.sleep(self.delay)

        logger.info("")
        logger.info("="*70)
        logger.info(f"SCRAPING COMPLETADO: {len(todas_ofertas)} ofertas")
        logger.info("="*70)

        # Actualizar tracking si modo incremental
        if incremental and tracker and todas_ofertas:
            new_ids = {str(o.get('id')) for o in todas_ofertas if o.get('id')}
            tracker.merge_scraped_ids(new_ids)

        # ========== FASE 3: REPORTES Y ALERTAS ==========

        # 1. Finalizar y mostrar métricas de performance
        if metrics:
            metrics.end()
            print()
            metrics.print_report()

            # Guardar métricas en JSON
            metrics_file = self.data_dir.parent / "metrics" / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            metrics.save_report(metrics_file)
            logger.info(f"Métricas guardadas en: {metrics_file}")

        # 2. Mostrar estadísticas del circuit breaker
        if self.circuit_breaker is not None:
            self.circuit_breaker.print_stats()

        # 3. Mostrar estadísticas del rate limiter
        if self.rate_limiter is not None:
            self.rate_limiter.print_stats()

        # 4. Verificar y enviar alertas
        if self.alert_manager is not None:
            # Verificar métricas
            if metrics:
                metrics_report = metrics.get_report()
                self.alert_manager.check_metrics(metrics_report)

            # Verificar circuit breaker
            if self.circuit_breaker is not None:
                breaker_stats = self.circuit_breaker.get_stats()
                self.alert_manager.check_circuit_breaker(breaker_stats)

            # Verificar rate limiter
            if self.rate_limiter is not None:
                limiter_stats = self.rate_limiter.get_stats()
                self.alert_manager.check_rate_limiter(limiter_stats)

            # Enviar todas las alertas
            self.alert_manager.send_alerts()

        return todas_ofertas

    def procesar_ofertas(self, ofertas_raw: List[Dict]) -> pd.DataFrame:
        """
        Procesa ofertas crudas a DataFrame estructurado

        Args:
            ofertas_raw: Lista de ofertas de la API

        Returns:
            DataFrame con ofertas procesadas
        """
        logger.info("Procesando ofertas...")

        ofertas_procesadas = []

        for oferta in ofertas_raw:
            # Normalizar fechas (DD-MM-YYYY → ISO 8601)
            fecha_pub_dict = normalizar_fecha_iso(oferta.get('fechaPublicacion'))
            fecha_hora_pub_dict = normalizar_fecha_iso(oferta.get('fechaHoraPublicacion'))
            fecha_mod_dict = normalizar_fecha_iso(oferta.get('fechaModificado'))

            procesada = {
                # IDs
                'id_oferta': oferta.get('id'),
                'id_empresa': oferta.get('idEmpresa'),

                # Información básica (con limpieza HTML)
                'titulo': limpiar_texto_html(oferta.get('titulo')),
                'empresa': limpiar_texto_html(oferta.get('empresa')),
                'descripcion': limpiar_texto_html(oferta.get('detalle')),
                'confidencial': oferta.get('confidencial'),

                # Ubicación y modalidad
                'localizacion': limpiar_texto_html(oferta.get('localizacion')),
                'modalidad_trabajo': oferta.get('modalidadTrabajo'),
                'tipo_trabajo': oferta.get('tipoTrabajo'),

                # Fechas (formato original + ISO 8601)
                'fecha_publicacion_original': fecha_pub_dict['fecha_original'],
                'fecha_publicacion_iso': fecha_pub_dict['fecha_iso'],
                'fecha_publicacion_datetime': fecha_pub_dict['fecha_datetime_iso'],

                'fecha_hora_publicacion_original': fecha_hora_pub_dict['fecha_original'],
                'fecha_hora_publicacion_iso': fecha_hora_pub_dict['fecha_iso'],
                'fecha_hora_publicacion_datetime': fecha_hora_pub_dict['fecha_datetime_iso'],

                'fecha_modificado_original': fecha_mod_dict['fecha_original'],
                'fecha_modificado_iso': fecha_mod_dict['fecha_iso'],
                'fecha_modificado_datetime': fecha_mod_dict['fecha_datetime_iso'],

                # Detalles
                'cantidad_vacantes': oferta.get('cantidadVacantes'),
                'apto_discapacitado': oferta.get('aptoDiscapacitado'),

                # Categorización
                'id_area': oferta.get('idArea'),
                'id_subarea': oferta.get('idSubarea'),
                'id_pais': oferta.get('idPais'),

                # Empresa
                'logo_url': oferta.get('logoURL'),
                'empresa_validada': oferta.get('validada'),
                'empresa_pro': oferta.get('empresaPro'),
                'promedio_empresa': oferta.get('promedioEmpresa'),

                # Plan
                'plan_publicacion_id': oferta.get('planPublicacion', {}).get('id') if oferta.get('planPublicacion') else None,
                'plan_publicacion_nombre': oferta.get('planPublicacion', {}).get('nombre') if oferta.get('planPublicacion') else None,

                # Otros
                'portal': oferta.get('portal'),
                'tipo_aviso': oferta.get('tipoAviso'),
                'tiene_preguntas': oferta.get('tienePreguntas'),
                'salario_obligatorio': oferta.get('salarioObligatorio'),
                'alta_revision_perfiles': oferta.get('altaRevisionPerfiles'),
                'guardado': oferta.get('guardado'),
                'gptw_url': oferta.get('gptwUrl'),

                # Metadata
                'url_oferta': f"https://www.bumeran.com.ar/empleos/{oferta.get('id')}.html" if oferta.get('id') else None,
                'scrapeado_en': datetime.now().isoformat()
            }

            # ============================================================
            # VALIDACIÓN DE CALIDAD DE DATOS (Agregado 2025-11-03)
            # ============================================================
            # Validar que la oferta tenga campos críticos completos
            campos_criticos_vacios = []

            if not procesada.get('titulo') or str(procesada.get('titulo')).strip() == '':
                campos_criticos_vacios.append('titulo')
            if not procesada.get('descripcion') or str(procesada.get('descripcion')).strip() == '':
                campos_criticos_vacios.append('descripcion')
            if not procesada.get('empresa') or str(procesada.get('empresa')).strip() == '':
                campos_criticos_vacios.append('empresa')
            if not procesada.get('modalidad_trabajo'):
                campos_criticos_vacios.append('modalidad_trabajo')
            if not procesada.get('tipo_trabajo'):
                campos_criticos_vacios.append('tipo_trabajo')
            if not procesada.get('id_empresa'):
                campos_criticos_vacios.append('id_empresa')

            # Rechazar oferta si faltan campos críticos
            if campos_criticos_vacios:
                logger.warning(
                    f"⚠️ Oferta {procesada['id_oferta']} RECHAZADA - "
                    f"Campos críticos vacíos: {', '.join(campos_criticos_vacios)}"
                )
                continue  # Skip esta oferta

            # Si pasa todas las validaciones, agregar a lista
            ofertas_procesadas.append(procesada)

        # Estadísticas de procesamiento
        ofertas_rechazadas = len(ofertas_raw) - len(ofertas_procesadas)

        if ofertas_rechazadas > 0:
            logger.warning(
                f"⚠️ {ofertas_rechazadas} de {len(ofertas_raw)} ofertas rechazadas "
                f"por falta de campos críticos ({ofertas_rechazadas/len(ofertas_raw)*100:.1f}%)"
            )

        df = pd.DataFrame(ofertas_procesadas)
        logger.info(
            f"✓ {len(df)} ofertas procesadas con {len(df.columns)} campos "
            f"(de {len(ofertas_raw)} scrapeadas)"
        )

        return df

    def save_to_csv(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en CSV"""
        df = self.procesar_ofertas(ofertas)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"bumeran_ofertas_{timestamp}.csv"
        else:
            filename = self.data_dir / filename

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Guardado CSV: {filename}")
        return str(filename)

    def save_to_json(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"bumeran_ofertas_{timestamp}.json"
        else:
            filename = self.data_dir / filename

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, indent=2, ensure_ascii=False)

        logger.info(f"Guardado JSON: {filename}")
        return str(filename)

    def save_to_excel(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en Excel"""
        df = self.procesar_ofertas(ofertas)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"bumeran_ofertas_{timestamp}.xlsx"
        else:
            filename = self.data_dir / filename

        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Guardado Excel: {filename}")
        return str(filename)

    def save_all_formats(self, ofertas: List[Dict], base_filename: str = None):
        """Guarda ofertas en todos los formatos"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"bumeran_ofertas_{timestamp}"

        logger.info("Guardando en todos los formatos...")

        csv_file = self.save_to_csv(ofertas, f"{base_filename}.csv")
        json_file = self.save_to_json(ofertas, f"{base_filename}.json")
        excel_file = self.save_to_excel(ofertas, f"{base_filename}.xlsx")

        return {
            'csv': csv_file,
            'json': json_file,
            'excel': excel_file
        }

    def filtrar_local(self, ofertas: List[Dict], keyword: str) -> List[Dict]:
        """
        Filtra ofertas localmente por keyword

        Args:
            ofertas: Lista de ofertas
            keyword: Palabra clave a buscar

        Returns:
            Ofertas filtradas
        """
        keyword_lower = keyword.lower()
        filtradas = []

        for oferta in ofertas:
            titulo = (oferta.get('titulo') or '').lower()
            descripcion = (oferta.get('detalle') or '').lower()

            if keyword_lower in titulo or keyword_lower in descripcion:
                filtradas.append(oferta)

        logger.info(f"Filtradas {len(filtradas)}/{len(ofertas)} ofertas con keyword '{keyword}'")
        return filtradas


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("BUMERAN SCRAPER")
    print("="*70)
    print("\nEjemplo de uso:\n")

    # Crear scraper
    scraper = BumeranScraper(delay_between_requests=2.0)

    # Opción 1: Scrapear primeras 100 ofertas
    print("\n[EJEMPLO 1] Scrapeando primeras 100 ofertas...")
    ofertas = scraper.scrapear_todo(max_paginas=5, max_resultados=100)

    # Guardar en todos los formatos
    if ofertas:
        files = scraper.save_all_formats(ofertas)
        print(f"\nArchivos guardados:")
        for fmt, filepath in files.items():
            print(f"  {fmt.upper()}: {filepath}")

    # Opción 2: Búsqueda específica
    print("\n\n[EJEMPLO 2] Buscando ofertas de 'python'...")
    ofertas_python = scraper.scrapear_todo(
        max_paginas=2,
        max_resultados=50,
        query="python"
    )

    if ofertas_python:
        scraper.save_to_csv(ofertas_python, "../data/raw/bumeran_python.csv")

    print("\n" + "="*70)
    print("Ejemplos completados!")
    print("="*70)


if __name__ == "__main__":
    main()
