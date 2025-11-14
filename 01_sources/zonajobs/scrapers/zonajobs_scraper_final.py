# -*- coding: utf-8 -*-
"""
Scraper Final de ZonaJobs - VERSIÓN FUNCIONAL
Basado en pruebas exitosas con la API

NOTA: La búsqueda por keyword requiere análisis adicional del formato de filtros.
      Esta versión se enfoca en scrapear todas las ofertas sin filtros de keyword.
"""

import requests
import uuid
import time
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path
import html
import re

# Agregar path para importar incremental_tracker
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
if str(consolidation_scripts) not in sys.path:
    sys.path.insert(0, str(consolidation_scripts))

try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    print(f"[WARN] No se pudo importar IncrementalTracker: {e}")
    print("[WARN] Modo incremental deshabilitado")
    IncrementalTracker = None


class ZonaJobsParser:
    """Parser para datos de ofertas laborales de ZonaJobs"""

    @staticmethod
    def parse_oferta(oferta_raw: Dict) -> Dict:
        """Parsea una oferta laboral del formato crudo de la API"""
        parsed = {
            # IDs
            'id_oferta': oferta_raw.get('id'),
            'id_empresa': oferta_raw.get('idEmpresa'),

            # Información básica
            'titulo': oferta_raw.get('titulo', '').strip(),
            'empresa': oferta_raw.get('empresa', '').strip(),
            'empresa_confidencial': oferta_raw.get('confidencial', False),
            'logo_url': oferta_raw.get('logoURL'),

            # Descripción (limpiar HTML si existe)
            'descripcion': ZonaJobsParser.clean_html(oferta_raw.get('detalle', '')),
            'descripcion_raw': oferta_raw.get('detalle', ''),

            # Ubicación y modalidad
            'localizacion': oferta_raw.get('localizacion', ''),
            'modalidad_trabajo': oferta_raw.get('modalidadTrabajo'),
            'tipo_trabajo': oferta_raw.get('tipoTrabajo'),

            # Fechas
            'fecha_publicacion': oferta_raw.get('fechaPublicacion'),
            'fecha_modificacion': oferta_raw.get('fechaModificado'),

            # Detalles
            'cantidad_vacantes': oferta_raw.get('cantidadVacantes', 1),
            'apto_discapacitado': oferta_raw.get('aptoDiscapacitado', False),

            # URL
            'url_oferta': f"https://www.zonajobs.com.ar/avisos/{oferta_raw.get('id')}",
            'scrapeado_en': datetime.now().isoformat()
        }

        return parsed

    @staticmethod
    def clean_html(text: str) -> str:
        """Limpia HTML de una descripción"""
        if not text:
            return ""

        text = html.unescape(text)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()


class ZonaJobsScraperFinal:
    """Scraper funcional de ZonaJobs"""

    BASE_URL = "https://www.zonajobs.com.ar"
    API_SEARCH = f"{BASE_URL}/api/avisos/searchHomeV2"

    def __init__(self, delay_between_requests: float = 2.0):
        self.session = requests.Session()
        self.delay = delay_between_requests
        self.parser = ZonaJobsParser()

        # Directorio de datos
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._setup_session()

    def _setup_session(self):
        """Configura la sesión con headers y cookies"""
        self.pre_session_token = str(uuid.uuid4())

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'es-AR',
            'Referer': self.BASE_URL + '/',
            'Origin': self.BASE_URL,
            'x-site-id': 'ZJAR',
            'x-pre-session-token': self.pre_session_token
        })

        # Obtener cookies
        print("[INIT] Obteniendo cookies...")
        try:
            self.session.get(self.BASE_URL, timeout=10)
            print(f"[INIT] Cookies: OK ({len(self.session.cookies)})")
        except Exception as e:
            print(f"[WARN] Error obteniendo cookies: {e}")

    def scrapear_todo(
        self,
        max_paginas: int = 10,
        max_resultados: Optional[int] = None,
        incremental: bool = True
    ) -> List[Dict]:
        """
        Scrapea todas las ofertas disponibles sin filtros

        Args:
            max_paginas: Máximo de páginas a scrapear (None = ilimitado)
            max_resultados: Máximo de resultados totales
            incremental: Si True, solo trae ofertas nuevas (default: True)

        Returns:
            Lista de ofertas parseadas
        """

        ofertas_parseadas = []
        page = 0

        print("\n" + "=" * 80)
        print("SCRAPING ZONAJOBS - TODAS LAS OFERTAS")
        print("=" * 80)
        print(f"Max paginas: {max_paginas if max_paginas else 'Ilimitado'}")
        print(f"Max resultados: {max_resultados or 'Ilimitado'}")
        print(f"Modo: {'Incremental' if incremental else 'Full'}")
        print("=" * 80 + "\n")

        # Inicializar tracker si modo incremental
        tracker = None
        existing_ids = set()
        if incremental:
            if IncrementalTracker is None:
                print("[WARN] IncrementalTracker no disponible, ejecutando en modo full")
                incremental = False
            else:
                tracker = IncrementalTracker(source='zonajobs')
                existing_ids = tracker.load_scraped_ids()
                if existing_ids:
                    print(f"[INCREMENTAL] {len(existing_ids):,} IDs ya scrapeados")
                else:
                    print("[INCREMENTAL] Primera ejecución: scrapeando TODO")

        while max_paginas is None or page < max_paginas:
            print(f"\n[PAGINA {page + 1}/{max_paginas if max_paginas else '?'}]")

            # Payload sin filtros (funciona)
            payload = {
                "filterData": {
                    "filtros": [],
                    "tipoDetalle": "full",
                    "busquedaExtendida": False
                },
                "page": page,
                "pageSize": 22,
                "sort": "RECIENTES"
            }

            try:
                headers = self.session.headers.copy()
                headers['Content-Type'] = 'application/json'

                response = self.session.post(
                    self.API_SEARCH,
                    json=payload,
                    headers=headers,
                    timeout=15
                )

                response.raise_for_status()
                data = response.json()

                # Extraer ofertas
                ofertas_raw = data.get('avisos', [])

                if not ofertas_raw:
                    print("[INFO] No hay mas ofertas")
                    break

                print(f"[OK] Encontradas {len(ofertas_raw)} ofertas")

                # Parsear y filtrar ofertas
                ofertas_pagina = []
                ofertas_nuevas_pagina = []

                for oferta_raw in ofertas_raw:
                    oferta_parseada = self.parser.parse_oferta(oferta_raw)
                    ofertas_pagina.append(oferta_parseada)

                    # Filtrar si modo incremental
                    if incremental and existing_ids:
                        if str(oferta_parseada['id_oferta']) not in existing_ids:
                            ofertas_nuevas_pagina.append(oferta_parseada)
                    else:
                        ofertas_nuevas_pagina.append(oferta_parseada)

                # Agregar ofertas (nuevas o todas según modo)
                if incremental and existing_ids:
                    ofertas_parseadas.extend(ofertas_nuevas_pagina)
                    print(f"[INCREMENTAL] {len(ofertas_nuevas_pagina)}/{len(ofertas_pagina)} ofertas nuevas")

                    # Si no hay ofertas nuevas, terminar (asume orden por fecha)
                    if not ofertas_nuevas_pagina and page > 2:
                        print("[INFO] No hay ofertas nuevas, finalizando")
                        break
                else:
                    ofertas_parseadas.extend(ofertas_nuevas_pagina)

                # Verificar límite
                if max_resultados and len(ofertas_parseadas) >= max_resultados:
                    ofertas_parseadas = ofertas_parseadas[:max_resultados]
                    print(f"\n[INFO] Alcanzado limite de {max_resultados} resultados")
                    break

                page += 1
                time.sleep(self.delay)

            except Exception as e:
                print(f"[ERROR] {e}")
                break

        print(f"\n[COMPLETADO] Total de ofertas: {len(ofertas_parseadas)}")

        # Actualizar tracking si modo incremental
        if incremental and tracker and ofertas_parseadas:
            new_ids = {str(o['id_oferta']) for o in ofertas_parseadas if o.get('id_oferta')}
            tracker.merge_scraped_ids(new_ids)

        return ofertas_parseadas

    def filtrar_local(self, ofertas: List[Dict], keyword: str = "") -> List[Dict]:
        """
        Filtra ofertas localmente por keyword

        Args:
            ofertas: Lista de ofertas
            keyword: Palabra clave a buscar

        Returns:
            Ofertas filtradas
        """
        if not keyword:
            return ofertas

        keyword_lower = keyword.lower()
        filtradas = []

        for oferta in ofertas:
            titulo = oferta.get('titulo', '').lower()
            desc = oferta.get('descripcion', '').lower()

            if keyword_lower in titulo or keyword_lower in desc:
                filtradas.append(oferta)

        print(f"\n[FILTER] Filtradas {len(filtradas)} de {len(ofertas)} ofertas con keyword '{keyword}'")
        return filtradas

    def save_to_json(self, ofertas: List[Dict], filename: str):
        """Guarda ofertas en JSON"""
        filepath = self.data_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] JSON: {filepath}")

    def save_to_csv(self, ofertas: List[Dict], filename: str):
        """Guarda ofertas en CSV"""
        filepath = self.data_dir / filename

        df = pd.DataFrame(ofertas)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

        print(f"[SAVE] CSV: {filepath}")

    def save_to_excel(self, ofertas: List[Dict], filename: str):
        """Guarda ofertas en Excel"""
        filepath = self.data_dir / filename

        df = pd.DataFrame(ofertas)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ofertas', index=False)

        print(f"[SAVE] Excel: {filepath}")

    def print_resumen(self, ofertas: List[Dict]):
        """Imprime resumen de ofertas"""
        if not ofertas:
            print("\n[WARN] No hay ofertas para resumir")
            return

        df = pd.DataFrame(ofertas)

        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total de ofertas: {len(ofertas)}")
        print(f"Empresas unicas: {df['empresa'].nunique()}")

        print("\nModalidades de trabajo:")
        if 'modalidad_trabajo' in df.columns:
            for modalidad, count in df['modalidad_trabajo'].value_counts().head().items():
                print(f"  - {modalidad}: {count}")

        print("\nTipos de trabajo:")
        if 'tipo_trabajo' in df.columns:
            for tipo, count in df['tipo_trabajo'].value_counts().head().items():
                print(f"  - {tipo}: {count}")

        print("\nTop 10 empresas:")
        for empresa, count in df['empresa'].value_counts().head(10).items():
            print(f"  - {empresa}: {count} ofertas")

        print("=" * 80)


def main():
    """Función principal de ejemplo"""

    scraper = ZonaJobsScraperFinal(delay_between_requests=2.0)

    # Scrapear primeras 5 páginas (110 ofertas aprox)
    print("\nScrapeando ofertas de ZonaJobs...")
    ofertas = scraper.scrapear_todo(max_paginas=5, max_resultados=100)

    if ofertas:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar todas las ofertas
        scraper.save_to_json(ofertas, f"zonajobs_todas_{timestamp}.json")
        scraper.save_to_csv(ofertas, f"zonajobs_todas_{timestamp}.csv")
        scraper.save_to_excel(ofertas, f"zonajobs_todas_{timestamp}.xlsx")

        # Mostrar resumen
        scraper.print_resumen(ofertas)

        # Filtrar localmente por Python
        print("\n\nFiltrando ofertas con 'python'...")
        python_jobs = scraper.filtrar_local(ofertas, "python")

        if python_jobs:
            scraper.save_to_json(python_jobs, f"zonajobs_python_{timestamp}.json")
            scraper.print_resumen(python_jobs)

        # Filtrar localmente por Remoto
        print("\n\nFiltrando ofertas remotas...")
        remote_jobs = [o for o in ofertas if o.get('modalidad_trabajo') == 'Remoto']

        if remote_jobs:
            scraper.save_to_json(remote_jobs, f"zonajobs_remoto_{timestamp}.json")
            scraper.print_resumen(remote_jobs)

    else:
        print("\n[ERROR] No se obtuvieron ofertas")


if __name__ == "__main__":
    main()
