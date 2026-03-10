"""
ZonaJobs Scraper v2 - Keyword Strategy via searchV2
====================================================

ZonaJobs (Navent/Bumeran) tiene paginación rota en su API: el parámetro
`page` es ignorado y siempre devuelve las mismas 20 ofertas.

Estrategia: usar `query` keyword para obtener distintos conjuntos de
20 ofertas cada uno, deduplicar por id_oferta.

Con 1,072 keywords: ~4,975 ofertas únicas (~45% de las 10,901 reportadas).
Tiempo: ~9 minutos por corrida.

Uso:
    scraper = ZonaJobsScraper()
    ofertas = scraper.scrapear_todo(estrategia='exhaustiva')
"""

import requests
import uuid
import json
import time
import html
import re
import logging
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONSOLIDATION_SCRIPTS = PROJECT_ROOT / "02_consolidation" / "scripts"
CONFIG_SCRAPING = PROJECT_ROOT / "config" / "scraping"

for path in [CONSOLIDATION_SCRIPTS, CONFIG_SCRAPING]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from incremental_tracker import IncrementalTracker
except ImportError:
    logger.warning("IncrementalTracker no disponible - modo incremental deshabilitado")
    IncrementalTracker = None

try:
    from keywords_loader import load_keywords
except ImportError:
    logger.warning("keywords_loader no disponible - usando carga directa")
    load_keywords = None


# =====================================================================
# UTILIDADES (compartidas con Bumeran - mismo formato Navent)
# =====================================================================

def limpiar_texto_html(texto: str) -> str:
    """Limpia HTML de una descripción"""
    if not texto:
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r'<br\s*/?>', '\n', texto, flags=re.IGNORECASE)
    texto = re.sub(r'</p>', '\n\n', texto, flags=re.IGNORECASE)
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    texto = re.sub(r' +', ' ', texto)
    return texto.strip()


def normalizar_fecha_iso(fecha_str: str) -> dict:
    """
    Normaliza fecha del formato Navent (DD-MM-YYYY HH:MM:SS) a ISO 8601.
    Asume timezone Argentina (UTC-3).
    """
    if not fecha_str:
        return {
            'fecha_original': None,
            'fecha_iso': None,
            'fecha_datetime_iso': None
        }

    result = {
        'fecha_original': fecha_str,
        'fecha_iso': None,
        'fecha_datetime_iso': None
    }

    try:
        # Formato: DD-MM-YYYY HH:MM:SS o DD-MM-YYYY
        if ' ' in fecha_str:
            dt = datetime.strptime(fecha_str, '%d-%m-%Y %H:%M:%S')
        else:
            dt = datetime.strptime(fecha_str, '%d-%m-%Y')

        # Agregar timezone Argentina (UTC-3)
        tz_arg = timezone(timedelta(hours=-3))
        dt_arg = dt.replace(tzinfo=tz_arg)

        result['fecha_iso'] = dt_arg.strftime('%Y-%m-%d')
        result['fecha_datetime_iso'] = dt_arg.isoformat()
    except (ValueError, TypeError):
        pass

    return result


# =====================================================================
# SCRAPER
# =====================================================================

class ZonaJobsScraper:
    """Scraper de ZonaJobs via API searchV2 + keywords"""

    BASE_URL = "https://www.zonajobs.com.ar"
    API_ENDPOINT = f"{BASE_URL}/api/avisos/searchV2"

    def __init__(self, delay_between_requests: float = 0.5):
        """
        Args:
            delay_between_requests: Delay entre requests (default: 0.5s)
        """
        self.delay = delay_between_requests
        self.session = None
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _init_session(self):
        """Inicializa sesión HTTP con headers ZonaJobs"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "es-AR,es;q=0.9",
            "x-site-id": "ZJAR",
            "x-pre-session-token": str(uuid.uuid4()),
            "Referer": f"{self.BASE_URL}/",
            "Origin": self.BASE_URL
        })
        # Obtener cookies de sesión
        try:
            self.session.get(self.BASE_URL, timeout=10)
            logger.info("Sesión ZonaJobs inicializada")
        except Exception as e:
            logger.warning(f"No se pudieron obtener cookies: {e}")

    def _search(self, query: str = None) -> dict:
        """
        Ejecuta búsqueda en la API searchV2.

        Args:
            query: Keyword de búsqueda (None = sin filtro, solo 20 ofertas)

        Returns:
            Dict con keys: content (list), total (int), filters (list)
        """
        payload = {
            "filterData": {
                "filtros": [],
                "tipoDetalle": "full",
                "busquedaExtendida": False
            },
            "page": 0,
            "pageSize": 20,
            "sort": "RECIENTES"
        }
        if query:
            payload["query"] = query

        try:
            r = self.session.post(self.API_ENDPOINT, json=payload, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request (query='{query}'): {e}")
            return {"content": [], "total": 0}

    def _procesar_oferta(self, oferta_raw: dict) -> dict:
        """
        Procesa oferta cruda de la API al formato de la tabla `ofertas`.
        Usa el mismo mapping que Bumeran (mismo platform Navent).
        """
        # Normalizar fechas
        fecha_pub = normalizar_fecha_iso(oferta_raw.get('fechaPublicacion'))
        fecha_hora_pub = normalizar_fecha_iso(oferta_raw.get('fechaHoraPublicacion'))
        fecha_mod = normalizar_fecha_iso(oferta_raw.get('fechaModificado'))

        return {
            # IDs
            'id_oferta': oferta_raw.get('id'),
            'id_empresa': oferta_raw.get('idEmpresa'),

            # Información básica
            'titulo': limpiar_texto_html(oferta_raw.get('titulo')),
            'empresa': limpiar_texto_html(oferta_raw.get('empresa')),
            'descripcion': limpiar_texto_html(oferta_raw.get('detalle')),
            'confidencial': 1 if oferta_raw.get('confidencial') else 0,

            # Ubicación y modalidad
            'localizacion': limpiar_texto_html(oferta_raw.get('localizacion')),
            'modalidad_trabajo': oferta_raw.get('modalidadTrabajo'),
            'tipo_trabajo': oferta_raw.get('tipoTrabajo'),

            # Fechas
            'fecha_publicacion_original': fecha_pub['fecha_original'],
            'fecha_publicacion_iso': fecha_pub['fecha_iso'],
            'fecha_publicacion_datetime': fecha_pub['fecha_datetime_iso'],

            'fecha_hora_publicacion_original': fecha_hora_pub['fecha_original'],
            'fecha_hora_publicacion_iso': fecha_hora_pub['fecha_iso'],
            'fecha_hora_publicacion_datetime': fecha_hora_pub['fecha_datetime_iso'],

            'fecha_modificado_original': fecha_mod['fecha_original'],
            'fecha_modificado_iso': fecha_mod['fecha_iso'],
            'fecha_modificado_datetime': fecha_mod['fecha_datetime_iso'],

            # Detalles
            'cantidad_vacantes': oferta_raw.get('cantidadVacantes'),
            'apto_discapacitado': 1 if oferta_raw.get('aptoDiscapacitado') else 0,

            # Categorización
            'id_area': oferta_raw.get('idArea'),
            'id_subarea': oferta_raw.get('idSubarea'),
            'id_pais': oferta_raw.get('idPais'),

            # Empresa
            'logo_url': oferta_raw.get('logoURL'),
            'empresa_validada': 1 if oferta_raw.get('validada') else 0,
            'empresa_pro': 1 if oferta_raw.get('empresaPro') else 0,
            'promedio_empresa': oferta_raw.get('promedioEmpresa'),

            # Plan
            'plan_publicacion_id': (oferta_raw.get('planPublicacion') or {}).get('id'),
            'plan_publicacion_nombre': (oferta_raw.get('planPublicacion') or {}).get('nombre'),

            # Otros
            'portal': 'zonajobs',  # SIEMPRE zonajobs (no usar el campo de la API)
            'tipo_aviso': oferta_raw.get('tipoAviso'),
            'tiene_preguntas': 1 if oferta_raw.get('tienePreguntas') else 0,
            'salario_obligatorio': 1 if oferta_raw.get('salarioObligatorio') else 0,
            'alta_revision_perfiles': 1 if oferta_raw.get('altaRevisionPerfiles') else 0,
            'guardado': None,
            'gptw_url': oferta_raw.get('gptwUrl'),

            # Metadata
            'url_oferta': f"https://www.zonajobs.com.ar/aviso/{oferta_raw.get('id')}",
            'scrapeado_en': datetime.now().isoformat()
        }

    def _cargar_keywords(self, estrategia: str) -> list:
        """Carga keywords del diccionario maestro"""
        if load_keywords is not None:
            try:
                keywords = load_keywords(estrategia)
                return [k for k in keywords if k.strip()]
            except Exception as e:
                logger.warning(f"Error con keywords_loader: {e}")

        # Fallback: cargar directo
        kw_file = CONFIG_SCRAPING / "master_keywords.json"
        if kw_file.exists():
            data = json.load(open(kw_file, 'r', encoding='utf-8'))
            if estrategia in data['estrategias']:
                keywords = data['estrategias'][estrategia]['keywords']
                return [k for k in keywords if k.strip()]

        raise FileNotFoundError("No se pudo cargar el diccionario de keywords")

    def scrapear_todo(
        self,
        estrategia: str = 'exhaustiva',
        incremental: bool = True
    ) -> List[Dict]:
        """
        Scrapea ZonaJobs usando keywords via searchV2.

        NOTA: La API ignora paginación, así que solo obtenemos 20 ofertas
        por keyword. Con ~1,000 keywords, obtenemos ~5,000 únicas.

        Args:
            estrategia: Estrategia de keywords (default: 'exhaustiva', ~1,072 kw)
            incremental: Si True, omite ofertas ya conocidas

        Returns:
            Lista de ofertas procesadas (formato tabla `ofertas`)
        """
        self._init_session()
        keywords = self._cargar_keywords(estrategia)
        logger.info(f"Estrategia '{estrategia}': {len(keywords)} keywords")

        # Tracker incremental
        tracker = None
        if incremental and IncrementalTracker is not None:
            try:
                tracker = IncrementalTracker(portal='zonajobs')
                logger.info(f"Modo incremental: {tracker.get_known_count()} IDs conocidos")
            except Exception as e:
                logger.warning(f"Error inicializando tracker: {e}")
                tracker = None

        all_offers = {}  # id -> oferta procesada
        errors = 0
        skipped_known = 0
        start_time = time.time()

        for i, kw in enumerate(keywords):
            try:
                data = self._search(query=kw)
                content = data.get('content', [])

                new_count = 0
                for raw_offer in content:
                    oid = raw_offer.get('id')
                    if not oid:
                        continue

                    # Deduplicar en esta corrida
                    if oid in all_offers:
                        continue

                    # Filtro incremental
                    if tracker and tracker.is_known(oid):
                        skipped_known += 1
                        continue

                    # Validar campos críticos
                    titulo = raw_offer.get('titulo', '').strip()
                    detalle = raw_offer.get('detalle', '').strip()
                    if not titulo or not detalle:
                        continue

                    oferta = self._procesar_oferta(raw_offer)
                    all_offers[oid] = oferta
                    new_count += 1

                if (i + 1) % 50 == 0 or i == len(keywords) - 1:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"[{i+1}/{len(keywords)}] "
                        f"Únicas: {len(all_offers)} | "
                        f"Errores: {errors} | "
                        f"Conocidas omitidas: {skipped_known} | "
                        f"Tiempo: {elapsed:.0f}s"
                    )

                time.sleep(self.delay)

            except Exception as e:
                errors += 1
                logger.error(f"Error en keyword '{kw}': {e}")
                time.sleep(2)  # Backoff en error

        # Registrar IDs nuevos en tracker
        if tracker:
            new_ids = list(all_offers.keys())
            tracker.mark_as_known(new_ids)
            logger.info(f"Registrados {len(new_ids)} IDs nuevos en tracker")

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"SCRAPING ZONAJOBS COMPLETADO")
        logger.info(f"  Estrategia: {estrategia} ({len(keywords)} keywords)")
        logger.info(f"  Ofertas únicas: {len(all_offers)}")
        logger.info(f"  Conocidas omitidas: {skipped_known}")
        logger.info(f"  Errores: {errors}")
        logger.info(f"  Tiempo: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        logger.info("=" * 60)

        return list(all_offers.values())


# =====================================================================
# CLI
# =====================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ZonaJobs Scraper v2")
    parser.add_argument('--estrategia', default='exhaustiva',
                       help='Estrategia de keywords (default: exhaustiva)')
    parser.add_argument('--no-incremental', action='store_true',
                       help='Desactivar modo incremental')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay entre requests (default: 0.5s)')
    parser.add_argument('--save-json', action='store_true',
                       help='Guardar resultados en JSON')
    args = parser.parse_args()

    scraper = ZonaJobsScraper(delay_between_requests=args.delay)
    ofertas = scraper.scrapear_todo(
        estrategia=args.estrategia,
        incremental=not args.no_incremental
    )

    if args.save_json and ofertas:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile = scraper.data_dir / f"zonajobs_{timestamp}.json"
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, indent=2, ensure_ascii=False)
        logger.info(f"Guardado: {outfile}")

    print(f"\nTotal ofertas: {len(ofertas)}")
