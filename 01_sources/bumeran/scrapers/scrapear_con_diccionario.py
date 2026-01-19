"""
Scraper de Bumeran usando diccionario de búsquedas
==================================================

Bumeran requiere keywords específicas para acceder a más de 20 ofertas.
Este script itera por un diccionario de búsquedas y consolida resultados.
"""

import json
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import time
from bumeran_scraper import BumeranScraper
import logging

# Agregar paths para imports
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
config_scripts = project_root / "config" / "scraping"

for path in [consolidation_scripts, config_scripts]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar tracker e keywords_loader
try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    logger.warning(f"No se pudo importar IncrementalTracker: {e}")
    logger.warning("Modo incremental deshabilitado")
    IncrementalTracker = None

try:
    from keywords_loader import load_keywords, get_available_strategies
except ImportError as e:
    logger.warning(f"No se pudo importar keywords_loader: {e}")
    logger.warning("Usando diccionario local como fallback")
    load_keywords = None
    get_available_strategies = None

try:
    from date_filter import filter_by_date_window
except ImportError as e:
    logger.warning(f"No se pudo importar date_filter: {e}")
    logger.warning("Filtrado por fecha deshabilitado")
    filter_by_date_window = None


class BumeranMultiSearch:
    """Scraper multi-keyword para Bumeran"""

    def __init__(self, delay_between_requests=1.5, delay_between_keywords=3.0):
        """
        Args:
            delay_between_requests: Delay entre páginas (default: 1.5s)
            delay_between_keywords: Delay entre keywords (default: 3s)
        """
        self.scraper = BumeranScraper(delay_between_requests)
        self.delay_keywords = delay_between_keywords
        # Diccionario local como fallback (legacy)
        self.keywords_config_path = Path(__file__).parent.parent / "config" / "search_keywords.json"
        # Total de ofertas disponibles en la API (capturado durante scraping)
        self.last_total_api = 0

    def cargar_keywords(self, estrategia="general"):
        """
        Carga keywords desde el diccionario maestro centralizado

        Args:
            estrategia: Nombre de la estrategia (maxima, completa, general, tecnologia, etc.)

        Returns:
            Lista de keywords
        """
        # Intentar usar diccionario maestro centralizado
        if load_keywords is not None:
            try:
                keywords = load_keywords(estrategia)
                logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}' (diccionario MAESTRO)")
                return keywords
            except Exception as e:
                logger.warning(f"Error cargando diccionario maestro: {e}")
                logger.warning("Usando diccionario local como fallback")

        # Fallback a diccionario local (legacy)
        if self.keywords_config_path.exists():
            with open(self.keywords_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if estrategia not in config['estrategias']:
                raise ValueError(f"Estrategia '{estrategia}' no encontrada. Disponibles: {list(config['estrategias'].keys())}")

            keywords = config['estrategias'][estrategia]['keywords']
            logger.info(f"Cargadas {len(keywords)} keywords de estrategia '{estrategia}' (diccionario LOCAL)")
            return keywords

        # Si no hay diccionarios disponibles, error
        raise FileNotFoundError("No se pudo cargar el diccionario de keywords (ni maestro ni local)")

    def scrapear_multiples_keywords(
        self,
        keywords=None,
        estrategia="maxima",
        max_paginas_por_keyword=10,
        max_resultados_por_keyword=None,
        page_size=20,
        incremental=True,
        date_window_days=7
    ):
        """
        Scrapea múltiples keywords y consolida resultados

        Args:
            keywords: Lista de keywords (None = usar estrategia)
            estrategia: Estrategia a usar si keywords=None (default: "maxima" para primera ejecución)
            max_paginas_por_keyword: Páginas por keyword (default: 10, optimizado para ventana temporal)
            max_resultados_por_keyword: Resultados por keyword (default: None = ilimitado)
            page_size: Ofertas por página (default: 20)
            incremental: Si True, solo trae ofertas nuevas (default: True)
            date_window_days: Ventana temporal en días (default: 7, 0=sin filtro)

        Returns:
            DataFrame consolidado sin duplicados, filtrado por fecha
        """
        # Cargar keywords
        if keywords is None:
            keywords = self.cargar_keywords(estrategia)

        logger.info("="*70)
        logger.info("SCRAPING MULTI-KEYWORD - BUMERAN")
        logger.info("="*70)
        logger.info(f"Keywords a scrapear: {len(keywords)}")
        logger.info(f"Max paginas por keyword: {max_paginas_por_keyword}")
        logger.info(f"Max resultados por keyword: {max_resultados_por_keyword or 'Ilimitado'}")
        logger.info(f"Page size: {page_size}")
        logger.info(f"Delay entre keywords: {self.delay_keywords}s")
        logger.info(f"Modo: {'Incremental' if incremental else 'Full'}")
        logger.info(f"Ventana temporal: {date_window_days} días" if date_window_days > 0 else "Ventana temporal: deshabilitada")
        logger.info("")

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
                logger.info("")

        todas_ofertas = []
        estadisticas = {
            'keywords_procesadas': 0,
            'keywords_exitosas': 0,
            'keywords_sin_resultados': 0,
            'ofertas_totales_brutas': 0,
            'ofertas_despues_dedup': 0
        }

        # Scrapear cada keyword
        for i, keyword in enumerate(keywords, 1):
            logger.info(f"\n[{i}/{len(keywords)}] Scrapeando keyword: '{keyword}'")

            try:
                ofertas = self.scraper.scrapear_todo(
                    max_paginas=max_paginas_por_keyword,
                    max_resultados=max_resultados_por_keyword,
                    page_size=page_size,
                    query=keyword if keyword else None,  # Si keyword vacía, None (búsqueda sin filtro)
                    incremental=False  # Deduplicación se hace acá
                )

                # FIX #1: VALIDACION ANTI-DUPLICADOS POR KEYWORD
                # Detecta si la API está devolviendo las mismas ofertas en todas las páginas
                if ofertas and len(ofertas) > 40:  # Solo validar si hay suficientes datos
                    ids_keyword = [str(o.get('id_oferta', o.get('id', ''))) for o in ofertas]
                    ids_unicos = len(set(ids_keyword))
                    ids_totales = len(ids_keyword)
                    tasa_duplicados = ((ids_totales - ids_unicos) / ids_totales) * 100 if ids_totales > 0 else 0

                    # ALERTA: Duplicados anormales (paginación rota de la API)
                    if tasa_duplicados > 80.0:
                        logger.warning(f"  [ALERTA] Keyword '{keyword}' tiene {tasa_duplicados:.1f}% duplicados")
                        logger.warning(f"    IDs unicos: {ids_unicos}, Total scrapeado: {ids_totales}")
                        logger.warning(f"    Probable paginacion rota de la API - Filtrando duplicados...")

                        # Filtrar duplicados ANTES de agregar a la lista (ahorra memoria y tiempo)
                        ids_vistos = set()
                        ofertas_limpias = []
                        for oferta in ofertas:
                            id_oferta = str(oferta.get('id_oferta', oferta.get('id', '')))
                            if id_oferta and id_oferta not in ids_vistos:
                                ids_vistos.add(id_oferta)
                                ofertas_limpias.append(oferta)

                        ofertas = ofertas_limpias
                        logger.info(f"    [OK] Filtrado: {len(ofertas)} ofertas unicas de {ids_totales} scrapeadas")

                        # Registrar estadística de paginación rota
                        estadisticas.setdefault('keywords_con_paginacion_rota', 0)
                        estadisticas['keywords_con_paginacion_rota'] += 1

                if ofertas:
                    # Capturar total_api de la primera búsqueda exitosa (para métricas de cobertura)
                    if self.last_total_api == 0 and hasattr(self.scraper, 'last_total_disponible'):
                        self.last_total_api = self.scraper.last_total_disponible
                        logger.info(f"  [Métricas] Total disponible en API: {self.last_total_api:,} ofertas")

                    # Agregar keyword usada a cada oferta
                    for oferta in ofertas:
                        oferta['keyword_busqueda'] = keyword if keyword else '(sin filtro)'

                    todas_ofertas.extend(ofertas)
                    estadisticas['keywords_exitosas'] += 1
                    logger.info(f"  OK - {len(ofertas)} ofertas encontradas")
                else:
                    estadisticas['keywords_sin_resultados'] += 1
                    logger.warning(f"  WARNING - Sin resultados")

                estadisticas['keywords_procesadas'] += 1

            except Exception as e:
                logger.error(f"  ERROR - {e}")
                continue

            # Delay entre keywords (excepto última)
            if i < len(keywords):
                logger.debug(f"  Esperando {self.delay_keywords}s antes de siguiente keyword...")
                time.sleep(self.delay_keywords)

        # Consolidar y deduplicar
        logger.info("\n" + "="*70)
        logger.info("CONSOLIDANDO RESULTADOS")
        logger.info("="*70)

        estadisticas['ofertas_totales_brutas'] = len(todas_ofertas)
        logger.info(f"Ofertas totales (con duplicados): {estadisticas['ofertas_totales_brutas']}")

        if not todas_ofertas:
            logger.warning("No se encontraron ofertas")
            return pd.DataFrame()

        # Convertir a DataFrame
        df = pd.DataFrame(todas_ofertas)

        # Deduplicar por id (puede aparecer en múltiples keywords)
        df_dedup = df.drop_duplicates(subset='id', keep='first')
        estadisticas['ofertas_despues_dedup'] = len(df_dedup)

        duplicados_removidos = estadisticas['ofertas_totales_brutas'] - estadisticas['ofertas_despues_dedup']
        logger.info(f"Ofertas únicas (sin duplicados): {estadisticas['ofertas_despues_dedup']}")
        logger.info(f"Duplicados removidos: {duplicados_removidos}")

        # Aplicar filtro de fecha si está habilitado
        df_filtered = df_dedup
        if date_window_days > 0 and filter_by_date_window is not None:
            logger.info(f"\nAplicando filtro temporal: últimos {date_window_days} días")
            df_filtered = filter_by_date_window(
                df_dedup,
                date_column='fecha_publicacion',
                days=date_window_days,
                verbose=True
            )
            estadisticas['ofertas_despues_filtro_fecha'] = len(df_filtered)
        elif date_window_days > 0:
            logger.warning("Filtro de fecha deshabilitado (date_filter no importado)")
        else:
            logger.info("Filtro de fecha deshabilitado (date_window_days=0)")

        # Filtrar ofertas nuevas si modo incremental
        df_final = df_filtered
        if incremental and tracker and existing_ids:
            logger.info("\nFiltrando ofertas nuevas (modo incremental)...")

            # Filtrar ofertas que NO están en existing_ids
            df_final = df_dedup[~df_dedup['id'].astype(str).isin(existing_ids)]

            ofertas_ya_existentes = len(df_dedup) - len(df_final)
            logger.info(f"Ofertas ya scrapeadas anteriormente: {ofertas_ya_existentes}")
            logger.info(f"Ofertas NUEVAS: {len(df_final)}")

            estadisticas['ofertas_ya_existentes'] = ofertas_ya_existentes
            estadisticas['ofertas_nuevas'] = len(df_final)

            # Actualizar tracking con IDs nuevos
            if not df_final.empty:
                new_ids = set(df_final['id'].astype(str))
                tracker.merge_scraped_ids(new_ids)
        elif incremental and tracker:
            # Primera ejecución: todas son nuevas
            logger.info("\nPrimera ejecución: todas las ofertas son nuevas")
            if not df_final.empty:
                new_ids = set(df_final['id'].astype(str))
                tracker.merge_scraped_ids(new_ids)

        # Estadísticas finales
        logger.info("\n" + "="*70)
        logger.info("ESTADISTICAS FINALES")
        logger.info("="*70)
        for key, value in estadisticas.items():
            logger.info(f"  {key}: {value}")

        logger.info("\nKeywords más productivas:")
        if 'keyword_busqueda' in df_final.columns:
            top_keywords = df_final['keyword_busqueda'].value_counts().head(10)
            for keyword, count in top_keywords.items():
                logger.info(f"  - '{keyword}': {count} ofertas")

        # FIX #3: METRICAS DE CALIDAD Y ALERTAS
        logger.info("\n" + "="*70)
        logger.info("METRICAS DE CALIDAD")
        logger.info("="*70)

        # Calcular eficiencia de deduplicación
        eficiencia = (estadisticas['ofertas_despues_dedup'] / estadisticas['ofertas_totales_brutas'] * 100) if estadisticas['ofertas_totales_brutas'] > 0 else 0
        logger.info(f"  Eficiencia de deduplicacion: {eficiencia:.2f}%")

        # ALERTA CRITICA: Eficiencia muy baja
        if eficiencia < 10.0 and estadisticas['ofertas_totales_brutas'] > 100:
            logger.error("  [CRITICO] Eficiencia <10% indica problema con paginacion o keywords")
            logger.error("  [CRITICO] Recomendacion: Revisar estrategia de scraping")

            # Mostrar keywords más problemáticas (con más duplicados)
            if 'keyword_busqueda' in df.columns:
                logger.error("\n  Keywords con MENOR eficiencia (mas duplicados):")
                keyword_counts = df.groupby('keyword_busqueda')['id'].count()
                keyword_uniques = df.groupby('keyword_busqueda')['id'].nunique()
                keyword_efficiency = (keyword_uniques / keyword_counts * 100).sort_values()

                for kw, eff in keyword_efficiency.head(10).items():
                    total = keyword_counts[kw]
                    unicos = keyword_uniques[kw]
                    logger.error(f"    '{kw}': {eff:.1f}% eficiencia ({unicos} unicos de {total} totales)")

        # Promedio de ofertas únicas por keyword
        avg_por_keyword = estadisticas['ofertas_despues_dedup'] / estadisticas['keywords_exitosas'] if estadisticas['keywords_exitosas'] > 0 else 0
        logger.info(f"  Promedio ofertas unicas por keyword: {avg_por_keyword:.1f}")

        # Ratio de overlap entre keywords
        overlap_ratio = (estadisticas['ofertas_totales_brutas'] - estadisticas['ofertas_despues_dedup']) / estadisticas['ofertas_totales_brutas'] * 100 if estadisticas['ofertas_totales_brutas'] > 0 else 0
        logger.info(f"  Ratio de overlap entre keywords: {overlap_ratio:.1f}%")

        if overlap_ratio > 80.0:
            logger.warning("  [ALERTA] Alto overlap (>80%) - Keywords muy redundantes o paginacion rota")

        # Keywords con paginación rota detectadas
        if estadisticas.get('keywords_con_paginacion_rota', 0) > 0:
            pct_rotas = (estadisticas['keywords_con_paginacion_rota'] / estadisticas['keywords_procesadas'] * 100) if estadisticas['keywords_procesadas'] > 0 else 0
            logger.warning(f"  [ALERTA] {estadisticas['keywords_con_paginacion_rota']} keywords con paginacion rota ({pct_rotas:.1f}%)")

        return df_final

    def guardar_metricas_cobertura(self, total_scrapeado: int) -> Optional[str]:
        """
        Guarda métricas de cobertura del scraping en archivo JSON.

        Args:
            total_scrapeado: Total de ofertas scrapeadas en esta ejecución

        Returns:
            Path del archivo JSON generado, o None si no se pudo guardar
        """
        try:
            # Directorio de métricas
            metrics_dir = Path(__file__).parent.parent / "data" / "metrics"
            metrics_dir.mkdir(parents=True, exist_ok=True)

            # Generar timestamp
            timestamp = datetime.now()
            filename = f"cobertura_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = metrics_dir / filename

            # Calcular métricas
            total_api = self.last_total_api or 0
            cobertura_pct = (total_scrapeado / total_api * 100) if total_api > 0 else 0
            ofertas_faltantes = max(0, total_api - total_scrapeado)

            # Determinar estado
            if cobertura_pct >= 90:
                estado = "EXCELENTE"
            elif cobertura_pct >= 70:
                estado = "BUENO"
            elif cobertura_pct >= 50:
                estado = "ACEPTABLE"
            else:
                estado = "CRITICO"

            # Construir objeto de métricas
            metricas = {
                "total_api": total_api,
                "total_scrapeado": total_scrapeado,
                "cobertura_pct": cobertura_pct,
                "ofertas_faltantes": ofertas_faltantes,
                "estado": estado,
                "timestamp": timestamp.isoformat()
            }

            # Guardar JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metricas, f, indent=2, ensure_ascii=False)

            logger.info(f"\nMétricas de cobertura guardadas en: {filepath}")
            logger.info(f"  Total API: {total_api:,} | Scrapeado: {total_scrapeado:,} | Cobertura: {cobertura_pct:.1f}% | Estado: {estado}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Error guardando métricas de cobertura: {e}")
            return None

    def guardar_resultados(self, df, base_filename=None):
        """Guarda resultados consolidados en todos los formatos"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"bumeran_multi_{timestamp}"

        logger.info("\nGuardando resultados...")

        # Usar métodos del scraper para guardar
        ofertas_list = df.to_dict('records')

        files = self.scraper.save_all_formats(ofertas_list, base_filename)

        logger.info("Archivos guardados:")
        for fmt, filepath in files.items():
            logger.info(f"  {fmt.upper()}: {filepath}")

        # Guardar métricas de cobertura automáticamente
        self.guardar_metricas_cobertura(total_scrapeado=len(df))

        return files


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("BUMERAN - SCRAPER MULTI-KEYWORD")
    print("="*70)
    print("\nEstrategias disponibles:")
    print("  - maxima: ~100 keywords (primera ejecución completa)")
    print("  - completa: ~55 keywords (incremental balanceada)")
    print("  - general: ~30 keywords (quick mix)")
    print("  - minima: ~4 keywords (testing)")
    print("")

    # Crear scraper
    multi_scraper = BumeranMultiSearch(
        delay_between_requests=1.5,
        delay_between_keywords=3.0
    )

    # Scrapear con estrategia "minima" para testing
    print("[EJEMPLO] Usando estrategia 'minima' (4 keywords para test)")
    print("Con ventana temporal de 7 días")
    print("")

    df_ofertas = multi_scraper.scrapear_multiples_keywords(
        estrategia="minima",
        max_paginas_por_keyword=1,  # FIX #2: API de Bumeran tiene paginación rota con keywords (devuelve siempre las mismas 20 ofertas)
        page_size=20,
        incremental=False,  # Full para testing
        date_window_days=7  # Últimos 7 días
    )

    # Guardar resultados
    if not df_ofertas.empty:
        files = multi_scraper.guardar_resultados(df_ofertas)
        print("\n" + "="*70)
        print("SCRAPING COMPLETADO EXITOSAMENTE")
        print("="*70)
    else:
        print("\nNo se encontraron ofertas")


if __name__ == "__main__":
    main()
