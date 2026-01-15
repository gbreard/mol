# -*- coding: utf-8 -*-
"""
ESCO Semantic Matcher con Embeddings
=====================================

Matcher semántico de ofertas laborales con taxonomía ESCO usando embeddings.
Utiliza sentence-transformers para capturar similitud semántica real.

Ventajas vs fuzzy matching:
- Entiende "Desarrollador" == "Ingeniero de software"
- Funciona con jerga argentina vs español formal ESCO
- ~20x más rápido que LLM
- Score de similitud más preciso
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import logging
from tqdm import tqdm
import numpy as np

# Sentence transformers
from sentence_transformers import SentenceTransformer, util

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESCOSemanticMatcher:
    """Matcher semántico basado en embeddings"""

    def __init__(self, esco_path: str, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Inicializa matcher semántico

        Args:
            esco_path: Path al JSON de ESCO
            model_name: Modelo de sentence-transformers a usar
        """
        self.esco_path = Path(esco_path)
        self.model_name = model_name
        self.model = None
        self.ocupaciones = []
        self.esco_embeddings = None
        self.esco_labels = []

        logger.info("=" * 80)
        logger.info("ESCO SEMANTIC MATCHER - Embeddings")
        logger.info("=" * 80)

        # Cargar modelo
        self._load_model()

        # Cargar ESCO
        self._load_esco()

        # Generar embeddings
        self._generate_esco_embeddings()

    def _load_model(self):
        """Carga modelo de sentence-transformers"""
        logger.info(f"\n[1/3] Cargando modelo: {self.model_name}")
        logger.info("  (Primera vez puede tardar ~1 min descargando)")

        self.model = SentenceTransformer(self.model_name)

        logger.info(f"  ✓ Modelo cargado")
        logger.info(f"  Dimensión embeddings: {self.model.get_sentence_embedding_dimension()}")

    def _load_esco(self):
        """Carga taxonomía ESCO"""
        logger.info(f"\n[2/3] Cargando taxonomía ESCO: {self.esco_path.name}")

        with open(self.esco_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convertir a lista
        if isinstance(data, dict):
            self.ocupaciones = [
                {
                    'esco_id': k,
                    'uri': v.get('uri', ''),
                    'label_es': v.get('label_es', ''),
                    'label_en': v.get('label_en', ''),
                    'isco_code': v.get('codigo_isco_4d', v.get('codigo_isco', '')),
                    'alt_labels': v.get('alt_labels_es', [])
                }
                for k, v in data.items()
            ]
        else:
            self.ocupaciones = data

        logger.info(f"  ✓ Cargadas {len(self.ocupaciones):,} ocupaciones ESCO")

    def _generate_esco_embeddings(self):
        """Genera embeddings para todas las ocupaciones ESCO"""
        logger.info(f"\n[3/3] Generando embeddings para ESCO...")

        # Preparar textos para embedding
        # Incluimos label principal + labels alternativos
        self.esco_labels = []
        textos_para_embedding = []

        for ocu in self.ocupaciones:
            label = ocu.get('label_es', '')
            if not label:
                label = ocu.get('label_en', '')

            # Combinar con alt_labels para mejor matching
            alt_labels = ocu.get('alt_labels', [])
            if alt_labels:
                # Tomar solo los primeros 3 alt_labels
                alt_text = ' | '.join(alt_labels[:3])
                texto_completo = f"{label} | {alt_text}"
            else:
                texto_completo = label

            textos_para_embedding.append(texto_completo)
            self.esco_labels.append(label)

        # Generar embeddings (batch para eficiencia)
        logger.info(f"  Procesando {len(textos_para_embedding):,} textos...")
        self.esco_embeddings = self.model.encode(
            textos_para_embedding,
            convert_to_tensor=True,
            show_progress_bar=True,
            batch_size=32
        )

        logger.info(f"  ✓ Embeddings generados")
        logger.info(f"  Shape: {self.esco_embeddings.shape}")

    def match_titulo(self, titulo: str, top_k: int = 1, threshold: float = 0.5):
        """
        Hace matching semántico de un título con ESCO

        Args:
            titulo: Título del puesto
            top_k: Cantidad de mejores matches a retornar
            threshold: Umbral mínimo de similitud (0-1)

        Returns:
            Lista de matches ordenados por similitud
        """
        if not titulo or pd.isna(titulo):
            return []

        # Generar embedding del título
        titulo_embedding = self.model.encode(titulo, convert_to_tensor=True)

        # Calcular similitud coseno con todos los ESCO
        cos_scores = util.cos_sim(titulo_embedding, self.esco_embeddings)[0]

        # Obtener top_k mejores matches
        top_results = np.argsort(cos_scores.cpu().numpy())[::-1][:top_k]

        matches = []
        for idx in top_results:
            score = float(cos_scores[idx])

            if score >= threshold:
                ocu = self.ocupaciones[idx]
                matches.append({
                    'esco_id': ocu['esco_id'],
                    'esco_uri': ocu['uri'],
                    'esco_label': self.esco_labels[idx],
                    'isco_code': ocu['isco_code'],
                    'similarity_score': round(score, 4),
                    'matching_method': 'semantic_embeddings'
                })

        return matches

    def match_dataframe(self, df: pd.DataFrame, titulo_col: str = 'titulo', threshold: float = 0.5):
        """
        Hace matching para un DataFrame completo

        Args:
            df: DataFrame con ofertas
            titulo_col: Nombre de columna con título
            threshold: Umbral de similitud

        Returns:
            DataFrame con nuevas columnas de matching semántico
        """
        logger.info("\n" + "=" * 80)
        logger.info("MATCHING SEMÁNTICO DE OFERTAS")
        logger.info("=" * 80)
        logger.info(f"Ofertas a procesar: {len(df):,}")
        logger.info(f"Columna título: '{titulo_col}'")
        logger.info(f"Threshold: {threshold}")

        results = []

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando ofertas"):
            titulo = row.get(titulo_col, '')

            # Matching
            matches = self.match_titulo(titulo, top_k=3, threshold=threshold)

            if matches:
                best_match = matches[0]

                result = {
                    'semantic_esco_id': best_match['esco_id'],
                    'semantic_esco_label': best_match['esco_label'],
                    'semantic_isco_code': best_match['isco_code'],
                    'semantic_similarity': best_match['similarity_score'],
                    'semantic_method': 'embeddings',
                    'semantic_match_2': matches[1]['esco_label'] if len(matches) > 1 else None,
                    'semantic_similarity_2': matches[1]['similarity_score'] if len(matches) > 1 else None,
                    'semantic_match_3': matches[2]['esco_label'] if len(matches) > 2 else None,
                    'semantic_similarity_3': matches[2]['similarity_score'] if len(matches) > 2 else None
                }
            else:
                result = {
                    'semantic_esco_id': None,
                    'semantic_esco_label': None,
                    'semantic_isco_code': None,
                    'semantic_similarity': 0.0,
                    'semantic_method': 'no_match',
                    'semantic_match_2': None,
                    'semantic_similarity_2': None,
                    'semantic_match_3': None,
                    'semantic_similarity_3': None
                }

            results.append(result)

        # Crear DataFrame con resultados
        df_results = pd.DataFrame(results)

        # Concatenar con original
        df_enriched = pd.concat([df.reset_index(drop=True), df_results], axis=1)

        # Estadísticas
        matched = df_results['semantic_esco_id'].notna().sum()
        pct = (matched / len(df)) * 100

        logger.info("\n" + "=" * 80)
        logger.info("RESULTADOS")
        logger.info("=" * 80)
        logger.info(f"Total ofertas: {len(df):,}")
        logger.info(f"Matched: {matched:,} ({pct:.1f}%)")

        if matched > 0:
            avg_sim = df_results[df_results['semantic_esco_id'].notna()]['semantic_similarity'].mean()
            logger.info(f"Similitud promedio: {avg_sim:.3f}")

            # Distribución de confianza
            high_conf = (df_results['semantic_similarity'] >= 0.8).sum()
            med_conf = ((df_results['semantic_similarity'] >= 0.6) & (df_results['semantic_similarity'] < 0.8)).sum()
            low_conf = ((df_results['semantic_similarity'] > 0) & (df_results['semantic_similarity'] < 0.6)).sum()

            logger.info(f"\nDistribución por confianza:")
            logger.info(f"  Alta (≥0.8):   {high_conf:>4,} ({high_conf/len(df)*100:>5.1f}%)")
            logger.info(f"  Media (0.6-0.8): {med_conf:>4,} ({med_conf/len(df)*100:>5.1f}%)")
            logger.info(f"  Baja (<0.6):     {low_conf:>4,} ({low_conf/len(df)*100:>5.1f}%)")

        logger.info("=" * 80)

        return df_enriched


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Matcher semántico ESCO con embeddings')

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path al CSV de ofertas'
    )

    parser.add_argument(
        '--esco-data',
        type=str,
        default=r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json",
        help='Path al JSON de ESCO'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Umbral de similitud (default: 0.5)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path de salida (default: auto)'
    )

    args = parser.parse_args()

    # Crear matcher
    matcher = ESCOSemanticMatcher(esco_path=args.esco_data)

    # Cargar ofertas
    logger.info(f"\nCargando ofertas: {Path(args.input).name}")
    df = pd.read_csv(args.input, encoding='utf-8', low_memory=False)
    logger.info(f"  ✓ {len(df):,} ofertas cargadas")

    # Matching
    df_enriched = matcher.match_dataframe(df, threshold=args.threshold)

    # Guardar
    if args.output is None:
        input_path = Path(args.input)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = input_path.parent / f"{input_path.stem}_semantic_{timestamp}.csv"
    else:
        output_path = Path(args.output)

    df_enriched.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"\n[GUARDADO] {output_path}")
    logger.info(f"[TAMAÑO] {output_path.stat().st_size / (1024*1024):.1f} MB")
    logger.info(f"[COLUMNAS] {len(df_enriched.columns)}")

    logger.info("\n✅ Proceso completado!")


if __name__ == "__main__":
    main()
