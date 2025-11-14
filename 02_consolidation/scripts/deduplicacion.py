"""
Detección y manejo de duplicados entre fuentes
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class DeduplicadorOfertas:
    """Detecta y elimina ofertas duplicadas entre fuentes"""

    def __init__(self, similarity_threshold=0.85):
        self.similarity_threshold = similarity_threshold

    def deduplicar(self, df: pd.DataFrame, strategy='keep_first') -> pd.DataFrame:
        """
        Elimina duplicados del DataFrame consolidado

        Args:
            df: DataFrame consolidado
            strategy: 'keep_first', 'keep_last', 'keep_best'

        Returns:
            DataFrame sin duplicados
        """
        logger.info(f"Iniciando deduplicación (ofertas: {len(df)})")

        # 1. Duplicados exactos por unified_id
        df_unique = df.drop_duplicates(subset=['_metadata.unified_id'], keep='first')
        logger.info(f"  Duplicados exactos por ID: {len(df) - len(df_unique)}")

        # 2. Duplicados por similaridad de título + empresa
        df_final = self._deduplicar_por_similitud(df_unique, strategy)

        logger.info(f"Total duplicados removidos: {len(df) - len(df_final)}")
        logger.info(f"Ofertas únicas: {len(df_final)}")

        return df_final

    def _deduplicar_por_similitud(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Detecta duplicados por similitud de texto"""

        # Crear clave compuesta
        df['_temp_key'] = (
            df['informacion_basica.titulo_normalizado'].fillna('') + '|' +
            df['informacion_basica.empresa'].fillna('').str.lower()
        )

        # Agrupar por clave similar
        duplicates_mask = pd.Series([False] * len(df))

        for idx, row in df.iterrows():
            if duplicates_mask[idx]:
                continue

            # Buscar duplicados por similitud
            for idx2 in range(idx + 1, len(df)):
                if duplicates_mask[idx2]:
                    continue

                similarity = self._calcular_similitud(
                    df.loc[idx, '_temp_key'],
                    df.loc[idx2, '_temp_key']
                )

                if similarity >= self.similarity_threshold:
                    duplicates_mask[idx2] = True

        df_unique = df[~duplicates_mask].drop(columns=['_temp_key'])
        return df_unique

    def _calcular_similitud(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos"""
        if pd.isna(text1) or pd.isna(text2):
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()


if __name__ == "__main__":
    print("Módulo de deduplicación - importar desde consolidar_fuentes.py")
