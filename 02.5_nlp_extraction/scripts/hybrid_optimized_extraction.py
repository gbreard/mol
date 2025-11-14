# -*- coding: utf-8 -*-
"""
Optimized Hybrid Extraction - Combina Regex + LLM inteligentemente
===================================================================

Estrategia:
1. Usa Regex para TODOS los campos (rápido)
2. Solo llama LLM si faltan soft_skills o educación (mejores en LLM)
3. Combina resultados priorizando la mejor fuente por campo
"""

import sys
from pathlib import Path
import json
import subprocess
import re
from typing import Dict, Optional
import pandas as pd
import logging
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HybridOptimizedExtractor:
    """Extractor híbrido optimizado (Regex + LLM selectivo)"""

    def __init__(self, model: str = 'llama3'):
        self.model = model
        self.llm_calls = 0
        self.regex_only = 0
        self._verify_ollama()

    def _verify_ollama(self):
        """Verifica Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Ollama no disponible")
            if self.model not in result.stdout:
                raise RuntimeError(f"Modelo {self.model} no disponible")
            logger.info(f"✓ Ollama verificado, modelo: {self.model}")
        except FileNotFoundError:
            raise RuntimeError("Ollama no instalado")

    def needs_llm_enhancement(self, regex_result: Dict) -> bool:
        """
        Decide si necesita LLM para mejorar resultados

        Criterios:
        - Falta soft_skills (LLM es 84% vs Regex 55%)
        - Falta educación (LLM es 54% vs Regex 44%)
        """
        missing_soft_skills = not regex_result.get('soft_skills_list') or pd.isna(regex_result.get('soft_skills_list'))
        missing_education = not regex_result.get('nivel_educativo') or pd.isna(regex_result.get('nivel_educativo'))

        return missing_soft_skills or missing_education

    def call_ollama_selective(self, titulo: str, descripcion: str) -> Dict:
        """Llama a Ollama pero solo pide los campos que faltan"""

        text = f"{titulo}\n\n{descripcion}" if titulo else descripcion
        text = text[:2000]

        prompt = f"""Eres un experto extrayendo información de ofertas laborales en español.

OFERTA LABORAL:
\"\"\"
{text}
\"\"\"

TAREA: Extrae SOLO estos campos (los más importantes):

1. nivel_educativo: Nivel educativo requerido (opciones: "secundario", "terciario", "universitario", "posgrado")
2. soft_skills: Lista de habilidades blandas (ej: ["trabajo en equipo", "liderazgo", "comunicación"])

IMPORTANTE:
- Responde SOLO con JSON válido
- Si no encuentras algo, usa null
- Sé conciso

FORMATO JSON:
{{
    "nivel_educativo": "universitario",
    "soft_skills": ["trabajo en equipo", "liderazgo"]
}}

JSON:"""

        try:
            result = subprocess.run(
                ['ollama', 'run', self.model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=15  # Timeout más corto
            )

            if result.returncode != 0:
                return {}

            response = result.stdout.strip()

            # Parsear JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            result_data = json.loads(response)

            # Normalizar
            normalized = {}

            if result_data.get('nivel_educativo'):
                normalized['nivel_educativo'] = result_data['nivel_educativo']

            if result_data.get('soft_skills') and isinstance(result_data['soft_skills'], list):
                soft_skills = [s for s in result_data['soft_skills'] if s]
                if soft_skills:
                    normalized['soft_skills_list'] = ', '.join(soft_skills)
                    normalized['soft_skills_count'] = len(soft_skills)

            return normalized

        except Exception as e:
            logger.debug(f"Error LLM: {e}")
            return {}

    def extract_hybrid(self, row: pd.Series) -> Dict:
        """
        Extracción híbrida optimizada

        Args:
            row: Fila del DataFrame con resultados de Regex ya aplicados

        Returns:
            Dict con campos mejorados
        """
        # Extraer campos actuales de Regex
        regex_result = {
            'experiencia_min_anios': row.get('experiencia_min_anios'),
            'nivel_educativo': row.get('nivel_educativo'),
            'skills_tecnicas_list': row.get('skills_tecnicas_list'),
            'soft_skills_list': row.get('soft_skills_list'),
            'idioma_principal': row.get('idioma_principal')
        }

        # Decidir si necesita LLM
        if not self.needs_llm_enhancement(regex_result):
            # Regex suficiente
            self.regex_only += 1
            return {
                'hybrid_method': 'regex_only',
                'hybrid_llm_called': False
            }

        # Necesita LLM para mejorar
        self.llm_calls += 1

        titulo = row.get('titulo', '')
        descripcion = row.get('descripcion', '')

        llm_result = self.call_ollama_selective(titulo, descripcion)

        # Combinar: LLM solo llena gaps
        combined = {
            'hybrid_method': 'regex+llm',
            'hybrid_llm_called': True
        }

        # Educación: LLM si Regex no tiene
        if llm_result.get('nivel_educativo') and not regex_result.get('nivel_educativo'):
            combined['hybrid_nivel_educativo'] = llm_result['nivel_educativo']

        # Soft skills: Priorizar LLM (es mejor)
        if llm_result.get('soft_skills_list'):
            combined['hybrid_soft_skills_list'] = llm_result['soft_skills_list']
            combined['hybrid_soft_skills_count'] = llm_result.get('soft_skills_count', 0)

        return combined

    def process_dataframe(
        self,
        df: pd.DataFrame,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Procesa DataFrame con extracción híbrida optimizada

        Args:
            df: DataFrame con resultados de Regex (Fase 1)
            limit: Límite de ofertas (None = todas)

        Returns:
            DataFrame enriquecido con campos híbridos
        """
        logger.info("\n" + "=" * 70)
        logger.info("EXTRACCIÓN HÍBRIDA OPTIMIZADA (Regex + LLM)")
        logger.info("=" * 70)

        if limit:
            df = df.head(limit)
            logger.info(f"Limitando a {limit} ofertas (modo test)")

        logger.info(f"Total ofertas: {len(df):,}")

        # Estimar cuántas necesitarán LLM
        missing_soft = df['soft_skills_list'].isna().sum()
        missing_edu = df['nivel_educativo'].isna().sum()
        estimated_llm_calls = max(missing_soft, missing_edu)

        logger.info(f"\nEstimación:")
        logger.info(f"  Ofertas sin soft_skills: {missing_soft:,}")
        logger.info(f"  Ofertas sin educación: {missing_edu:,}")
        logger.info(f"  Llamadas LLM estimadas: ~{estimated_llm_calls:,}")
        logger.info(f"  Tiempo estimado: ~{estimated_llm_calls * 2.5 / 3600:.1f} horas\n")

        results = []

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracción híbrida"):
            hybrid_result = self.extract_hybrid(row)
            results.append(hybrid_result)

            # Log cada 500
            if (idx + 1) % 500 == 0:
                logger.info(f"  Progreso: {idx+1:,}/{len(df):,} | LLM calls: {self.llm_calls:,} | Regex only: {self.regex_only:,}")

        # Agregar resultados híbridos al DataFrame
        df_hybrid = pd.DataFrame(results)
        df_enriched = pd.concat([df, df_hybrid], axis=1)

        # Crear campos finales combinados
        # FIX: Usar pd.notna() porque NaN or "string" = NaN (no funciona el or con NaN)
        df_enriched['final_nivel_educativo'] = df_enriched.apply(
            lambda row: row.get('hybrid_nivel_educativo') if pd.notna(row.get('hybrid_nivel_educativo')) else row.get('nivel_educativo'),
            axis=1
        )

        df_enriched['final_soft_skills_list'] = df_enriched.apply(
            lambda row: row.get('hybrid_soft_skills_list') if pd.notna(row.get('hybrid_soft_skills_list')) else row.get('soft_skills_list'),
            axis=1
        )

        logger.info("\n" + "=" * 70)
        logger.info("RESULTADOS")
        logger.info("=" * 70)
        logger.info(f"Ofertas procesadas: {len(df):,}")
        logger.info(f"LLM llamadas: {self.llm_calls:,} ({100*self.llm_calls/len(df):.1f}%)")
        logger.info(f"Solo Regex: {self.regex_only:,} ({100*self.regex_only/len(df):.1f}%)")
        logger.info(f"Tiempo real: {self.llm_calls * 2.5 / 60:.1f} minutos")

        # Comparar cobertura
        logger.info("\nCOBERTURA MEJORADA:")
        logger.info(f"  Educación:")
        logger.info(f"    Regex: {df['nivel_educativo'].notna().sum()} ({100*df['nivel_educativo'].notna().sum()/len(df):.1f}%)")
        logger.info(f"    Híbrido: {df_enriched['final_nivel_educativo'].notna().sum()} ({100*df_enriched['final_nivel_educativo'].notna().sum()/len(df):.1f}%)")

        logger.info(f"  Soft Skills:")
        logger.info(f"    Regex: {df['soft_skills_list'].notna().sum()} ({100*df['soft_skills_list'].notna().sum()/len(df):.1f}%)")
        logger.info(f"    Híbrido: {df_enriched['final_soft_skills_list'].notna().sum()} ({100*df_enriched['final_soft_skills_list'].notna().sum()/len(df):.1f}%)")

        logger.info("=" * 70)

        return df_enriched


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Extracción híbrida optimizada')
    parser.add_argument('--input', type=str,
                       default=r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_nlp_20251025_141134.csv',
                       help='CSV de entrada (con Regex aplicado)')
    parser.add_argument('--output', type=str, default=None, help='CSV de salida')
    parser.add_argument('--model', type=str, default='llama3', help='Modelo Ollama')
    parser.add_argument('--limit', type=int, default=None, help='Límite de ofertas (test)')

    args = parser.parse_args()

    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'../data/processed/all_sources_hybrid_{timestamp}.csv'

    try:
        # Cargar datos
        logger.info("Cargando datos...")
        df = pd.read_csv(args.input, low_memory=False)
        logger.info(f"  Cargadas {len(df):,} ofertas")

        # Crear extractor
        extractor = HybridOptimizedExtractor(model=args.model)

        # Procesar
        df_hybrid = extractor.process_dataframe(df, limit=args.limit)

        # Guardar
        df_hybrid.to_csv(args.output, index=False)
        logger.info(f"\n✓ Guardado: {args.output}")

        logger.info("\n¡Extracción híbrida completada! 🎉")

    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
