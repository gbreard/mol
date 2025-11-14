# -*- coding: utf-8 -*-
"""
Integrate NLP with ESCO - Integración de dataset NLP con clasificación ESCO
===========================================================================

Script para clasificar ofertas procesadas con NLP usando taxonomía ESCO/ISCO.
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import re
import unicodedata
from difflib import SequenceMatcher
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextNormalizer:
    """Normalizador de texto para matching"""

    STOPWORDS = {
        'el', 'la', 'los', 'las', 'de', 'del', 'y', 'e', 'o', 'u',
        'un', 'una', 'unos', 'unas', 'para', 'por', 'con', 'sin',
        'en', 'a', 'al', 'sobre', 'entre', 'desde', 'hasta', 'sr', 'sra'
    }

    @staticmethod
    def normalize(text):
        """Normaliza texto para matching"""
        if pd.isna(text) or not text:
            return ""

        # Minúsculas
        text = text.lower().strip()

        # Remover acentos
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])

        # Remover caracteres especiales
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def tokenize_clean(text):
        """Tokeniza y remueve stopwords"""
        tokens = TextNormalizer.normalize(text).split()
        tokens_clean = [t for t in tokens if t not in TextNormalizer.STOPWORDS and len(t) > 2]
        return tokens_clean


class ESCOMatcher:
    """Matcher de títulos de trabajo con ocupaciones ESCO"""

    def __init__(self, esco_path: str):
        """
        Inicializa matcher

        Args:
            esco_path: Path al archivo JSON de ESCO
        """
        self.esco_path = Path(esco_path)
        self.ocupaciones = None
        self.ocupaciones_normalized = None

        logger.info(f"Cargando ESCO desde: {self.esco_path}")
        self._load_esco()

    def _load_esco(self):
        """Carga taxonomía ESCO"""
        with open(self.esco_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Procesar según estructura del archivo
        if isinstance(data, list):
            self.ocupaciones = data
        elif isinstance(data, dict):
            # Dict de UUIDs -> ocupaciones
            self.ocupaciones = list(data.values())

        logger.info(f"Cargadas {len(self.ocupaciones)} ocupaciones ESCO")

        # Normalizar títulos para matching
        self._normalize_esco_titles()

    def _normalize_esco_titles(self):
        """Normaliza títulos ESCO para matching rápido"""
        self.ocupaciones_normalized = []

        for ocu in self.ocupaciones:
            # Obtener título (priorizar español)
            titulo = ocu.get('label_es', '') or ocu.get('label_en', '') or ocu.get('preferredLabel', {}).get('es', '')

            if titulo:
                self.ocupaciones_normalized.append({
                    'uri': ocu.get('uri', ''),
                    'codigo_esco': ocu.get('uri', '').split('/')[-1] if ocu.get('uri') else '',
                    'titulo_original': titulo,
                    'titulo_normalizado': TextNormalizer.normalize(titulo),
                    'tokens': TextNormalizer.tokenize_clean(titulo),
                    'isco_code': ocu.get('codigo_isco_4d', ocu.get('isco', ocu.get('codigo_isco', ''))),
                    'data': ocu
                })

        logger.info(f"Normalizadas {len(self.ocupaciones_normalized)} ocupaciones")

    def match_title(self, job_title: str, threshold: float = 0.6):
        """
        Hace matching de título de trabajo con ESCO

        Args:
            job_title: Título del puesto
            threshold: Umbral de similitud (0-1)

        Returns:
            Dict con mejor match o None
        """
        if not job_title:
            return None

        job_title_norm = TextNormalizer.normalize(job_title)
        job_tokens = set(TextNormalizer.tokenize_clean(job_title))

        best_match = None
        best_score = 0.0

        for ocu in self.ocupaciones_normalized:
            # Similitud de secuencia
            seq_score = SequenceMatcher(None, job_title_norm, ocu['titulo_normalizado']).ratio()

            # Jaccard de tokens
            ocu_tokens = set(ocu['tokens'])
            if job_tokens and ocu_tokens:
                jaccard = len(job_tokens & ocu_tokens) / len(job_tokens | ocu_tokens)
            else:
                jaccard = 0.0

            # Score combinado
            score = (seq_score * 0.6) + (jaccard * 0.4)

            if score > best_score:
                best_score = score
                best_match = ocu

        if best_score >= threshold:
            return {
                'ocupacion_esco_uri': best_match['uri'],
                'ocupacion_esco_codigo': best_match['codigo_esco'],
                'ocupacion_esco_label': best_match['titulo_original'],
                'isco_code': best_match['isco_code'],
                'similarity_score': round(best_score, 3),
                'matching_method': 'sequence_jaccard',
                'matching_threshold': threshold
            }

        return None


class ESCOIntegrator:
    """Integrador de dataset NLP con ESCO"""

    def __init__(self, nlp_dataset_path: str, esco_data_path: str, output_dir: str = None):
        """
        Inicializa integrador

        Args:
            nlp_dataset_path: Path al CSV con NLP procesado
            esco_data_path: Path al JSON de ESCO
            output_dir: Directorio de salida
        """
        self.nlp_path = Path(nlp_dataset_path)
        self.esco_path = Path(esco_data_path)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.nlp_path.parent

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.matcher = ESCOMatcher(esco_data_path)
        self.df = None

    def load_nlp_dataset(self):
        """Carga dataset NLP"""
        logger.info(f"Cargando dataset NLP: {self.nlp_path.name}")

        self.df = pd.read_csv(self.nlp_path, encoding='utf-8', low_memory=False)

        logger.info(f"  Cargadas {len(self.df):,} ofertas")
        logger.info(f"  Columnas: {len(self.df.columns)}")

        return self.df

    def match_all(self, titulo_col: str = 'titulo', threshold: float = 0.6):
        """
        Hace matching de todas las ofertas

        Args:
            titulo_col: Nombre de columna con título
            threshold: Umbral de similitud

        Returns:
            DataFrame con ESCO agregado
        """
        logger.info("=" * 70)
        logger.info("MATCHING CON ESCO")
        logger.info("=" * 70)
        logger.info(f"Columna título: {titulo_col}")
        logger.info(f"Threshold: {threshold}")
        logger.info("")

        # Verificar columna
        if titulo_col not in self.df.columns:
            logger.error(f"Columna '{titulo_col}' no encontrada")
            return self.df

        results = []

        for idx, row in self.df.iterrows():
            if idx % 500 == 0 and idx > 0:
                logger.info(f"  Procesadas {idx:,}/{len(self.df):,} ofertas...")

            titulo = row.get(titulo_col, '')
            match_result = self.matcher.match_title(titulo, threshold=threshold)

            results.append(match_result if match_result else {})

        # Convertir a DataFrame
        df_esco = pd.DataFrame(results)

        # Concatenar con original
        df_enriched = pd.concat([self.df, df_esco], axis=1)

        # Estadísticas
        matched = df_esco['ocupacion_esco_uri'].notna().sum() if 'ocupacion_esco_uri' in df_esco.columns else 0
        pct = (matched / len(df_esco)) * 100 if len(df_esco) > 0 else 0

        logger.info("")
        logger.info("=" * 70)
        logger.info("RESULTADOS MATCHING")
        logger.info("=" * 70)
        logger.info(f"Total ofertas: {len(df_esco):,}")
        logger.info(f"Matched con ESCO: {matched:,} ({pct:.1f}%)")

        if matched > 0:
            avg_sim = df_esco[df_esco['ocupacion_esco_uri'].notna()]['similarity_score'].mean()
            logger.info(f"Similitud promedio: {avg_sim:.3f}")

            # Top ISCO codes
            if 'isco_code' in df_esco.columns:
                logger.info("\nTop 10 códigos ISCO:")
                top_isco = df_esco['isco_code'].value_counts().head(10)
                for isco, count in top_isco.items():
                    logger.info(f"  {isco}: {count:,} ofertas")

        logger.info("=" * 70)

        return df_enriched

    def save_results(self, df: pd.DataFrame, base_filename: str = None):
        """Guarda resultados"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"nlp_esco_enriched_{timestamp}"

        # CSV
        csv_path = self.output_dir / f"{base_filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"\n[GUARDADO] CSV: {csv_path}")
        logger.info(f"[TAMAÑO] {csv_path.stat().st_size / (1024*1024):.1f} MB")

        # Estadísticas
        stats_path = self.output_dir / f"{base_filename}_stats.json"
        stats = {
            'total_ofertas': len(df),
            'matched_esco': int(df['ocupacion_esco_uri'].notna().sum()) if 'ocupacion_esco_uri' in df.columns else 0,
            'matching_threshold': float(df['matching_threshold'].iloc[0]) if 'matching_threshold' in df.columns and len(df) > 0 else 0.0,
            'avg_similarity': float(df['similarity_score'].mean()) if 'similarity_score' in df.columns else 0.0,
            'timestamp': datetime.now().isoformat()
        }

        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info(f"[GUARDADO] Stats: {stats_path}")

        return csv_path


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Integra dataset NLP con ESCO')

    parser.add_argument(
        '--nlp-dataset',
        type=str,
        default=None,
        help='Path al CSV NLP (default: autodetectar más reciente)'
    )

    parser.add_argument(
        '--esco-data',
        type=str,
        default=r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json",
        help='Path al JSON ESCO'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.6,
        help='Umbral de similitud (default: 0.6)'
    )

    parser.add_argument(
        '--titulo-col',
        type=str,
        default='titulo',
        help='Nombre de columna con título (default: titulo)'
    )

    args = parser.parse_args()

    # Detectar dataset NLP más reciente si no se especificó
    if args.nlp_dataset is None:
        project_root = Path(__file__).parent.parent.parent
        processed_dir = project_root / "02.5_nlp_extraction" / "data" / "processed"
        pattern = "all_sources_nlp_*.csv"
        files = list(processed_dir.glob(pattern))

        if files:
            args.nlp_dataset = max(files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Dataset NLP autodetectado: {args.nlp_dataset.name}")
        else:
            logger.error("No se encontró dataset NLP")
            return

    # Crear integrador
    integrator = ESCOIntegrator(
        nlp_dataset_path=args.nlp_dataset,
        esco_data_path=args.esco_data
    )

    # Cargar datos
    integrator.load_nlp_dataset()

    # Matching
    df_enriched = integrator.match_all(
        titulo_col=args.titulo_col,
        threshold=args.threshold
    )

    # Guardar
    integrator.save_results(df_enriched)

    logger.info("\n¡Integración completada!")


if __name__ == "__main__":
    main()
