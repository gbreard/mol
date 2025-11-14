# -*- coding: utf-8 -*-
"""
Consolidate NLP Sources - Consolida resultados NLP de múltiples fuentes
=======================================================================

Script para consolidar los resultados de extracción NLP de todas las fuentes
en un único archivo multi-fuente.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLPSourcesConsolidator:
    """Consolidador de resultados NLP de múltiples fuentes"""

    def __init__(self, processed_dir: str = None):
        """
        Inicializa el consolidador

        Args:
            processed_dir: Directorio con archivos procesados
        """
        project_root = Path(__file__).parent.parent.parent

        if processed_dir:
            self.processed_dir = Path(processed_dir)
        else:
            self.processed_dir = project_root / "02.5_nlp_extraction" / "data" / "processed"

        self.output_dir = self.processed_dir

    def get_latest_files(self) -> dict:
        """
        Obtiene los archivos más recientes de cada fuente

        Returns:
            Dict con {fuente: filepath}
        """
        sources = ['bumeran', 'zonajobs', 'indeed']
        latest_files = {}

        for source in sources:
            pattern = f"{source}_nlp_*.csv"
            files = list(self.processed_dir.glob(pattern))

            if files:
                # Ordenar por fecha de modificación y tomar el más reciente
                latest_file = max(files, key=lambda p: p.stat().st_mtime)
                latest_files[source] = latest_file

        return latest_files

    def add_source_column(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Agrega columna con nombre de fuente

        Args:
            df: DataFrame
            source: Nombre de la fuente

        Returns:
            DataFrame con columna 'fuente'
        """
        df['fuente'] = source
        return df

    def consolidate_all(self, save: bool = True) -> pd.DataFrame:
        """
        Consolida todas las fuentes en un solo DataFrame

        Args:
            save: Si True, guarda el resultado

        Returns:
            DataFrame consolidado
        """
        logger.info("=" * 70)
        logger.info("CONSOLIDANDO FUENTES NLP")
        logger.info("=" * 70)

        # Obtener archivos
        latest_files = self.get_latest_files()

        if not latest_files:
            logger.error("No se encontraron archivos procesados")
            return pd.DataFrame()

        logger.info(f"Archivos encontrados: {len(latest_files)}")

        # Cargar y consolidar
        dfs = []

        for source, filepath in latest_files.items():
            logger.info(f"\nCargando {source}: {filepath.name}")

            try:
                df = pd.read_csv(filepath, encoding='utf-8', low_memory=False)
                df = self.add_source_column(df, source)
                dfs.append(df)

                logger.info(f"  - {len(df):,} ofertas")

            except Exception as e:
                logger.error(f"Error cargando {source}: {e}")
                continue

        if not dfs:
            logger.error("No se pudo cargar ningún archivo")
            return pd.DataFrame()

        # Concatenar
        df_consolidated = pd.concat(dfs, ignore_index=True)

        logger.info("\n" + "=" * 70)
        logger.info("RESULTADO CONSOLIDADO")
        logger.info("=" * 70)
        logger.info(f"Total ofertas: {len(df_consolidated):,}")
        logger.info(f"Fuentes: {df_consolidated['fuente'].nunique()}")

        # Estadísticas por fuente
        logger.info("\nOfertas por fuente:")
        for fuente, count in df_consolidated['fuente'].value_counts().items():
            logger.info(f"  - {fuente}: {count:,}")

        # Estadísticas NLP
        logger.info("\nEstadísticas NLP globales:")

        if 'nlp_confidence_score' in df_consolidated.columns:
            avg_conf = df_consolidated['nlp_confidence_score'].mean()
            logger.info(f"  Confidence promedio: {avg_conf:.3f}")

        if 'experiencia_min_anios' in df_consolidated.columns:
            con_exp = df_consolidated['experiencia_min_anios'].notna().sum()
            pct_exp = (con_exp / len(df_consolidated)) * 100
            logger.info(f"  Ofertas con experiencia: {con_exp:,} ({pct_exp:.1f}%)")

        if 'nivel_educativo' in df_consolidated.columns:
            con_edu = df_consolidated['nivel_educativo'].notna().sum()
            pct_edu = (con_edu / len(df_consolidated)) * 100
            logger.info(f"  Ofertas con educación: {con_edu:,} ({pct_edu:.1f}%)")

        if 'idioma_principal' in df_consolidated.columns:
            con_idioma = df_consolidated['idioma_principal'].notna().sum()
            pct_idioma = (con_idioma / len(df_consolidated)) * 100
            logger.info(f"  Ofertas con idiomas: {con_idioma:,} ({pct_idioma:.1f}%)")

        if 'skills_tecnicas_list' in df_consolidated.columns:
            con_skills = df_consolidated['skills_tecnicas_list'].notna().sum()
            pct_skills = (con_skills / len(df_consolidated)) * 100
            logger.info(f"  Ofertas con skills: {con_skills:,} ({pct_skills:.1f}%)")

        # Guardar si es requerido
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"all_sources_nlp_{timestamp}.csv"
            output_path = self.output_dir / filename

            df_consolidated.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"\n[GUARDADO] {output_path}")
            logger.info(f"[TAMAÑO] {output_path.stat().st_size / (1024*1024):.1f} MB")

        logger.info("=" * 70)

        return df_consolidated

    def generate_quality_report(self, df: pd.DataFrame):
        """
        Genera reporte de calidad de extracción

        Args:
            df: DataFrame consolidado
        """
        logger.info("\n" + "=" * 70)
        logger.info("REPORTE DE CALIDAD")
        logger.info("=" * 70)

        # Campos NLP
        nlp_fields = [
            'experiencia_min_anios',
            'nivel_educativo',
            'idioma_principal',
            'skills_tecnicas_list',
            'soft_skills_list',
            'jornada_laboral'
        ]

        logger.info("\nCobertura por campo:")
        for field in nlp_fields:
            if field in df.columns:
                count = df[field].notna().sum()
                pct = (count / len(df)) * 100
                logger.info(f"  {field}: {count:,} ({pct:.1f}%)")

        # Por fuente
        if 'fuente' in df.columns:
            logger.info("\nConfidence por fuente:")
            for fuente in df['fuente'].unique():
                df_fuente = df[df['fuente'] == fuente]
                if 'nlp_confidence_score' in df_fuente.columns:
                    avg = df_fuente['nlp_confidence_score'].mean()
                    logger.info(f"  {fuente}: {avg:.3f}")

        logger.info("=" * 70)


def main():
    """Función principal"""
    logger.info("\nConsolidador de Fuentes NLP\n")

    consolidator = NLPSourcesConsolidator()

    # Consolidar
    df = consolidator.consolidate_all(save=True)

    # Reporte de calidad
    if not df.empty:
        consolidator.generate_quality_report(df)

    logger.info("\n¡Consolidación completada!")


if __name__ == "__main__":
    main()
