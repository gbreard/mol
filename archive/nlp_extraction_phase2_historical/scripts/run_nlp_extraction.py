# -*- coding: utf-8 -*-
"""
Run NLP Extraction - Script para procesar datasets completos
============================================================

Script principal para ejecutar extracción NLP en datasets de cada fuente.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse
import logging

# Agregar paths
project_root = Path(__file__).parent.parent.parent
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from extractors.bumeran_extractor import BumeranExtractor
from extractors.zonajobs_extractor import ZonaJobsExtractor
from extractors.indeed_extractor import IndeedExtractor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLPExtractionRunner:
    """Ejecutor de extracción NLP para múltiples fuentes"""

    def __init__(self, output_dir: str = None):
        """
        Inicializa el runner

        Args:
            output_dir: Directorio para guardar resultados
        """
        self.project_root = project_root
        self.sources_dir = self.project_root / "01_sources"

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.project_root / "02.5_nlp_extraction" / "data" / "processed"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configuración de fuentes
        self.sources_config = {
            'bumeran': {
                'extractor': BumeranExtractor(),
                'raw_dir': self.sources_dir / 'bumeran' / 'data' / 'raw',
                'descripcion_col': 'descripcion',
                'titulo_col': 'titulo',
                'latest_file_pattern': 'bumeran_full_*.csv',
            },
            'zonajobs': {
                'extractor': ZonaJobsExtractor(),
                'raw_dir': self.sources_dir / 'zonajobs' / 'data' / 'raw',
                'descripcion_col': 'descripcion',
                'titulo_col': 'titulo',
                'latest_file_pattern': 'zonajobs_consolidacion_*.csv',
            },
            'indeed': {
                'extractor': IndeedExtractor(),
                'raw_dir': self.sources_dir / 'indeed' / 'data' / 'raw',
                'descripcion_col': 'description',
                'titulo_col': 'title',
                'latest_file_pattern': 'indeed_consolidacion.json',
            }
        }

    def get_latest_file(self, source: str) -> Path:
        """
        Obtiene el archivo más reciente de una fuente

        Args:
            source: Nombre de la fuente

        Returns:
            Path al archivo más reciente
        """
        config = self.sources_config[source]
        raw_dir = config['raw_dir']
        pattern = config['latest_file_pattern']

        # Buscar archivos que coincidan con el patrón
        files = list(raw_dir.glob(pattern))

        if not files:
            raise FileNotFoundError(f"No se encontraron archivos para {source} en {raw_dir}")

        # Ordenar por fecha de modificación y tomar el más reciente
        latest_file = max(files, key=lambda p: p.stat().st_mtime)

        return latest_file

    def load_data(self, source: str, filepath: Path = None, limit: int = None) -> pd.DataFrame:
        """
        Carga datos de una fuente

        Args:
            source: Nombre de la fuente
            filepath: Path al archivo (None = autodetectar)
            limit: Límite de filas a cargar (None = todas)

        Returns:
            DataFrame con los datos
        """
        if filepath is None:
            filepath = self.get_latest_file(source)

        logger.info(f"Cargando datos de {source}: {filepath.name}")

        # Cargar según formato
        if filepath.suffix == '.csv':
            df = pd.read_csv(filepath, nrows=limit, encoding='utf-8-sig')
        elif filepath.suffix == '.json':
            df = pd.read_json(filepath, lines=False)
            if limit:
                df = df.head(limit)
        else:
            raise ValueError(f"Formato no soportado: {filepath.suffix}")

        logger.info(f"  Cargadas {len(df)} ofertas")

        return df

    def process_source(
        self,
        source: str,
        filepath: Path = None,
        limit: int = None,
        save: bool = True
    ) -> pd.DataFrame:
        """
        Procesa una fuente completa

        Args:
            source: Nombre de la fuente
            filepath: Path al archivo (None = autodetectar)
            limit: Límite de filas a procesar (None = todas)
            save: Si True, guarda el resultado

        Returns:
            DataFrame con resultados NLP
        """
        logger.info("=" * 70)
        logger.info(f"PROCESANDO FUENTE: {source.upper()}")
        logger.info("=" * 70)

        # Verificar que la fuente exista
        if source not in self.sources_config:
            raise ValueError(f"Fuente '{source}' no configurada. Disponibles: {list(self.sources_config.keys())}")

        config = self.sources_config[source]

        # Cargar datos
        df = self.load_data(source, filepath, limit)

        # Verificar que las columnas existan
        desc_col = config['descripcion_col']
        titulo_col = config['titulo_col']

        if desc_col not in df.columns:
            logger.error(f"Columna '{desc_col}' no encontrada en {source}")
            logger.error(f"Columnas disponibles: {list(df.columns)}")
            raise ValueError(f"Columna '{desc_col}' no encontrada")

        # Procesar con extractor
        extractor = config['extractor']
        df_result = extractor.process_dataframe(
            df,
            descripcion_col=desc_col,
            titulo_col=titulo_col if titulo_col in df.columns else None
        )

        # Estadísticas
        stats = extractor.get_extraction_stats(df_result)
        logger.info("\nESTADÍSTICAS DE EXTRACCIÓN:")
        for key, value in stats.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")

        # Guardar si es requerido
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{source}_nlp_{timestamp}.csv"
            output_path = self.output_dir / filename

            # Forzar UTF-8 en output para evitar problemas de encoding
            df_result.to_csv(output_path, index=False, encoding='utf-8', errors='replace')
            logger.info(f"\nRESULTADO GUARDADO: {output_path}")

        logger.info("=" * 70)

        return df_result

    def process_all_sources(self, limit: int = None):
        """
        Procesa todas las fuentes disponibles

        Args:
            limit: Límite de filas por fuente (None = todas)
        """
        logger.info("\n" + "=" * 70)
        logger.info("PROCESANDO TODAS LAS FUENTES")
        logger.info("=" * 70 + "\n")

        results = {}

        for source in self.sources_config.keys():
            try:
                df_result = self.process_source(source, limit=limit)
                results[source] = df_result
            except Exception as e:
                logger.error(f"Error procesando {source}: {e}")
                continue

        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN FINAL")
        logger.info("=" * 70)

        for source, df in results.items():
            if 'nlp_confidence_score' in df.columns:
                avg_confidence = df['nlp_confidence_score'].mean()
                logger.info(f"{source}: {len(df)} ofertas - Confidence promedio: {avg_confidence:.2f}")

        return results


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Ejecuta extracción NLP en ofertas laborales'
    )

    parser.add_argument(
        '--source',
        choices=['bumeran', 'zonajobs', 'indeed', 'all'],
        default='all',
        help='Fuente a procesar (default: all)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de ofertas a procesar (default: todas)'
    )

    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Path a archivo específico (default: autodetectar más reciente)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Directorio de salida (default: 02.5_nlp_extraction/data/processed)'
    )

    args = parser.parse_args()

    # Crear runner
    runner = NLPExtractionRunner(output_dir=args.output_dir)

    # Procesar
    if args.source == 'all':
        runner.process_all_sources(limit=args.limit)
    else:
        filepath = Path(args.file) if args.file else None
        runner.process_source(args.source, filepath=filepath, limit=args.limit)

    logger.info("\n¡Procesamiento completado!")


if __name__ == "__main__":
    main()
