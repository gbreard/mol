# -*- coding: utf-8 -*-
"""
ESCO Hybrid Matcher - Fuzzy + LLM + Embeddings
===============================================

Matcher híbrido inteligente que combina lo mejor de cada método:
- Fuzzy (rápido) cuando score ≥ 80 (alta confianza)
- LLM (preciso) cuando fuzzy < 70 (baja confianza)
- Combinación inteligente para casos medios (70-79)
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import logging
from tqdm import tqdm
import unicodedata
import re
from difflib import SequenceMatcher

# Sentence transformers para embeddings
from sentence_transformers import SentenceTransformer, util
import torch

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextNormalizer:
    """Normalizador de texto"""

    @staticmethod
    def normalize(text):
        if pd.isna(text) or not text:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class ESCOHybridMatcher:
    """Matcher híbrido que combina Fuzzy + Embeddings + LLM"""

    def __init__(self, esco_path: str):
        """
        Inicializa matcher híbrido

        Args:
            esco_path: Path al JSON de ESCO
        """
        self.esco_path = Path(esco_path)
        self.ocupaciones = []
        self.esco_dict = {}

        # Modelos
        self.embedding_model = None
        self.esco_embeddings = None

        logger.info("=" * 80)
        logger.info("ESCO HYBRID MATCHER")
        logger.info("=" * 80)

        self._load_esco()
        self._load_embedding_model()

    def _load_esco(self):
        """Carga taxonomía ESCO"""
        logger.info(f"\n[1/2] Cargando ESCO: {self.esco_path.name}")

        with open(self.esco_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

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
            self.esco_dict = data
        else:
            self.ocupaciones = data

        logger.info(f"  OK: {len(self.ocupaciones):,} ocupaciones cargadas")

    def _load_embedding_model(self):
        """Carga modelo de embeddings"""
        logger.info(f"\n[2/2] Cargando modelo embeddings...")

        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # Generar embeddings de ESCO
        textos = []
        for ocu in self.ocupaciones:
            label = ocu.get('label_es', '')
            if not label:
                label = ocu.get('label_en', '')

            # Incluir alt_labels
            alt_labels = ocu.get('alt_labels', [])
            if alt_labels:
                alt_text = ' | '.join(alt_labels[:2])
                texto = f"{label} | {alt_text}"
            else:
                texto = label

            textos.append(texto)

        logger.info(f"  Generando embeddings...")
        self.esco_embeddings = self.embedding_model.encode(
            textos,
            convert_to_tensor=True,
            show_progress_bar=False,
            batch_size=32
        )

        logger.info(f"  OK: Embeddings listos")

    def fuzzy_match(self, titulo: str, threshold: float = 0.6):
        """
        Matching fuzzy básico

        Returns:
            dict con mejor match o None
        """
        if not titulo:
            return None

        titulo_norm = TextNormalizer.normalize(titulo)
        best_match = None
        best_score = 0.0

        for ocu in self.ocupaciones:
            label = ocu.get('label_es', '')
            if not label:
                label = ocu.get('label_en', '')

            label_norm = TextNormalizer.normalize(label)

            # SequenceMatcher
            score = SequenceMatcher(None, titulo_norm, label_norm).ratio()

            # Jaccard
            titulo_tokens = set(titulo_norm.split())
            label_tokens = set(label_norm.split())
            if titulo_tokens and label_tokens:
                jaccard = len(titulo_tokens & label_tokens) / len(titulo_tokens | label_tokens)
                score = (score * 0.6) + (jaccard * 0.4)

            if score > best_score:
                best_score = score
                best_match = ocu

        if best_score >= threshold:
            return {
                'esco_id': best_match['esco_id'],
                'esco_label': best_match['label_es'],
                'isco_code': best_match['isco_code'],
                'score': round(best_score, 4),
                'method': 'fuzzy'
            }

        return None

    def embedding_match(self, titulo: str, threshold: float = 0.5, top_k: int = 3):
        """
        Matching con embeddings

        Returns:
            list de matches
        """
        if not titulo:
            return []

        titulo_embedding = self.embedding_model.encode(titulo, convert_to_tensor=True)
        cos_scores = util.cos_sim(titulo_embedding, self.esco_embeddings)[0]

        top_results = torch.topk(cos_scores, k=min(top_k, len(cos_scores)))

        matches = []
        for score, idx in zip(top_results.values, top_results.indices):
            score_val = float(score)
            if score_val >= threshold:
                ocu = self.ocupaciones[int(idx)]
                matches.append({
                    'esco_id': ocu['esco_id'],
                    'esco_label': ocu['label_es'],
                    'isco_code': ocu['isco_code'],
                    'score': round(score_val, 4),
                    'method': 'embeddings'
                })

        return matches

    def llm_match(self, titulo: str, descripcion: str, top_candidates: list):
        """
        Matching con LLM (Ollama)

        Args:
            titulo: Título de la oferta
            descripcion: Descripción completa (opcional)
            top_candidates: Top 5 candidatos de fuzzy/embeddings

        Returns:
            dict con match seleccionado por LLM
        """
        import subprocess

        if not top_candidates:
            return None

        # Preparar prompt
        candidatos_text = "\n".join([
            f"{i+1}. {c['esco_label']} (ISCO: {c['isco_code']})"
            for i, c in enumerate(top_candidates[:5])
        ])

        desc_snippet = descripcion[:500] if descripcion and not pd.isna(descripcion) else ""

        prompt = f"""Eres un experto en clasificación ocupacional según taxonomía ESCO.

OFERTA LABORAL:
Título: {titulo}
Descripción: {desc_snippet}

OCUPACIONES ESCO CANDIDATAS:
{candidatos_text}

TAREA:
Identifica cuál ocupación ESCO corresponde mejor a esta oferta.
Considera el contexto completo de la oferta, no solo palabras clave.

Responde SOLO con el número (1-5) de la mejor opción.
Formato: [NUMERO]

Respuesta:"""

        try:
            # Llamar a Ollama
            result = subprocess.run(
                ['ollama', 'run', 'llama3', prompt],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )

            response = result.stdout.strip()

            # Extraer número
            import re
            match = re.search(r'\[?(\d+)\]?', response)
            if match:
                selected = int(match.group(1)) - 1
                if 0 <= selected < len(top_candidates):
                    match_result = top_candidates[selected].copy()
                    match_result['method'] = 'llm'
                    match_result['llm_response'] = response
                    return match_result

            # Si falla, retornar el primero
            return top_candidates[0]

        except Exception as e:
            logger.warning(f"LLM falló: {e}, usando primer candidato")
            return top_candidates[0]

    def hybrid_match(self, titulo: str, descripcion: str = None):
        """
        Matching híbrido inteligente

        Estrategia:
        1. Fuzzy score >= 80 → Usar fuzzy (alta confianza)
        2. Fuzzy score < 70 → Usar LLM con top 5 de embeddings
        3. Fuzzy 70-79 → Combinar fuzzy + embeddings, validar con LLM si difieren

        Returns:
            dict con mejor match
        """
        # Paso 1: Fuzzy
        fuzzy_result = self.fuzzy_match(titulo, threshold=0.5)

        if fuzzy_result and fuzzy_result['score'] >= 0.8:
            # Alta confianza en fuzzy, usar directamente
            fuzzy_result['confidence'] = 'alta'
            fuzzy_result['strategy'] = 'fuzzy_only'
            return fuzzy_result

        # Paso 2: Embeddings para obtener candidatos
        embedding_results = self.embedding_match(titulo, threshold=0.5, top_k=5)

        if not embedding_results:
            # Sin resultados, usar fuzzy si existe
            if fuzzy_result:
                fuzzy_result['confidence'] = 'baja'
                fuzzy_result['strategy'] = 'fuzzy_fallback'
                return fuzzy_result
            return None

        # Caso: Fuzzy < 70 (baja confianza)
        if not fuzzy_result or fuzzy_result['score'] < 0.7:
            # Usar LLM con top candidatos
            llm_result = self.llm_match(titulo, descripcion, embedding_results)
            if llm_result:
                llm_result['confidence'] = 'media'
                llm_result['strategy'] = 'llm_with_embeddings'
                return llm_result

            # Fallback a embeddings
            embedding_results[0]['confidence'] = 'media'
            embedding_results[0]['strategy'] = 'embeddings_only'
            return embedding_results[0]

        # Caso: Fuzzy 70-79 (media confianza)
        # Verificar si fuzzy y embeddings coinciden
        top_embedding = embedding_results[0]

        if fuzzy_result['esco_id'] == top_embedding['esco_id']:
            # Coinciden, reforzar confianza
            fuzzy_result['confidence'] = 'alta'
            fuzzy_result['strategy'] = 'fuzzy_embedding_agree'
            return fuzzy_result
        else:
            # Difieren, usar LLM para desempatar
            all_candidates = [fuzzy_result] + embedding_results[:4]
            llm_result = self.llm_match(titulo, descripcion, all_candidates)
            if llm_result:
                llm_result['confidence'] = 'media'
                llm_result['strategy'] = 'llm_tiebreaker'
                return llm_result

            # Fallback a fuzzy
            fuzzy_result['confidence'] = 'media'
            fuzzy_result['strategy'] = 'fuzzy_preferred'
            return fuzzy_result

    def match_dataframe(self, df: pd.DataFrame, titulo_col: str = 'titulo', desc_col: str = 'descripcion'):
        """
        Procesa DataFrame completo con matching híbrido

        Args:
            df: DataFrame con ofertas
            titulo_col: Columna con título
            desc_col: Columna con descripción (opcional)

        Returns:
            DataFrame enriquecido
        """
        logger.info("\n" + "=" * 80)
        logger.info("MATCHING HÍBRIDO")
        logger.info("=" * 80)
        logger.info(f"Ofertas: {len(df):,}")
        logger.info(f"Estrategia: Fuzzy (≥80) → LLM (<70) → Combinado (70-79)")

        results = []
        stats = {
            'fuzzy_only': 0,
            'llm_with_embeddings': 0,
            'llm_tiebreaker': 0,
            'embeddings_only': 0,
            'fuzzy_embedding_agree': 0,
            'fuzzy_preferred': 0,
            'fuzzy_fallback': 0
        }

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando"):
            titulo = row.get(titulo_col, '')
            descripcion = row.get(desc_col, '') if desc_col in df.columns else None

            match_result = self.hybrid_match(titulo, descripcion)

            if match_result:
                strategy = match_result.get('strategy', 'unknown')
                stats[strategy] = stats.get(strategy, 0) + 1

                result = {
                    'hybrid_esco_id': match_result['esco_id'],
                    'hybrid_esco_label': match_result['esco_label'],
                    'hybrid_isco_code': match_result['isco_code'],
                    'hybrid_score': match_result['score'],
                    'hybrid_confidence': match_result.get('confidence', 'media'),
                    'hybrid_strategy': strategy,
                    'hybrid_method': match_result.get('method', 'hybrid')
                }
            else:
                result = {
                    'hybrid_esco_id': None,
                    'hybrid_esco_label': None,
                    'hybrid_isco_code': None,
                    'hybrid_score': 0.0,
                    'hybrid_confidence': 'sin_match',
                    'hybrid_strategy': 'no_match',
                    'hybrid_method': None
                }

            results.append(result)

        df_results = pd.DataFrame(results)
        df_enriched = pd.concat([df.reset_index(drop=True), df_results], axis=1)

        # Estadísticas
        matched = df_results['hybrid_esco_id'].notna().sum()
        pct = (matched / len(df)) * 100

        logger.info("\n" + "=" * 80)
        logger.info("RESULTADOS")
        logger.info("=" * 80)
        logger.info(f"Matched: {matched:,} ({pct:.1f}%)")

        if matched > 0:
            logger.info(f"\nEstrategias utilizadas:")
            for strategy, count in stats.items():
                if count > 0:
                    pct_s = (count / len(df)) * 100
                    logger.info(f"  {strategy:>25s}: {count:>4,} ({pct_s:>5.1f}%)")

            # Confianza
            conf_dist = df_results['hybrid_confidence'].value_counts()
            logger.info(f"\nDistribución confianza:")
            for conf, count in conf_dist.items():
                pct_c = (count / len(df)) * 100
                logger.info(f"  {conf:>15s}: {count:>4,} ({pct_c:>5.1f}%)")

        logger.info("=" * 80)

        return df_enriched


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Matcher híbrido ESCO')

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='CSV de ofertas'
    )

    parser.add_argument(
        '--esco-data',
        type=str,
        default=r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json",
        help='JSON ESCO'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='CSV salida'
    )

    args = parser.parse_args()

    # Crear matcher
    matcher = ESCOHybridMatcher(esco_path=args.esco_data)

    # Cargar ofertas
    logger.info(f"\nCargando: {Path(args.input).name}")
    df = pd.read_csv(args.input, encoding='utf-8', low_memory=False)
    logger.info(f"  OK: {len(df):,} ofertas")

    # Matching
    df_enriched = matcher.match_dataframe(df)

    # Guardar
    if args.output is None:
        input_path = Path(args.input)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = input_path.parent / f"{input_path.stem}_hybrid_{timestamp}.csv"
    else:
        output_path = Path(args.output)

    df_enriched.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"\n[GUARDADO] {output_path}")
    logger.info(f"[COLUMNAS] {len(df_enriched.columns)}")

    logger.info("\nProceso completado!")


if __name__ == "__main__":
    main()
