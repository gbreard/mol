# -*- coding: utf-8 -*-
"""
Hybrid Extraction Test - Prueba enfoque híbrido (Regex + LLM)
==============================================================

Compara 4 enfoques:
1. Regex (Fase 1)
2. NER (Fase 2)
3. LLM directo (Ollama)
4. Híbrido (Regex + LLM para gaps)
"""

import sys
from pathlib import Path
import json
import subprocess
import re
from typing import Dict, List, Optional
import pandas as pd
import logging
from datetime import datetime
from tqdm import tqdm
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaDirectExtractor:
    """Extractor directo usando Ollama (sin NER)"""

    def __init__(self, model: str = 'llama3'):
        self.model = model
        self._verify_ollama()

    def _verify_ollama(self):
        """Verifica que Ollama esté disponible"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Ollama no está disponible")

            if self.model not in result.stdout:
                logger.warning(f"Modelo {self.model} no encontrado")
                raise RuntimeError(f"Modelo {self.model} no disponible")

            logger.info(f"✓ Ollama verificado, modelo: {self.model}")
        except FileNotFoundError:
            raise RuntimeError("Ollama no está instalado")

    def create_extraction_prompt(self, titulo: str, descripcion: str) -> str:
        """Crea prompt para extracción directa"""

        text = f"{titulo}\n\n{descripcion}" if titulo else descripcion
        text = text[:2000]  # Limitar tamaño

        prompt = f"""Eres un experto extrayendo información de ofertas laborales en español.

OFERTA LABORAL:
\"\"\"
{text}
\"\"\"

TAREA: Extrae la siguiente información. Si no encuentras algo, usa null.

CAMPOS A EXTRAER:
1. experiencia_anios: Años mínimos de experiencia requeridos (solo número, ej: 3)
2. nivel_educativo: Nivel educativo (opciones: "secundario", "terciario", "universitario", "posgrado")
3. titulo_requerido: Título académico específico requerido (ej: "Ingeniería en Sistemas")
4. skills_tecnicas: Lista de habilidades técnicas (ej: ["Python", "SQL", "AWS"])
5. soft_skills: Lista de habilidades blandas (ej: ["trabajo en equipo", "liderazgo"])
6. idiomas: Idioma principal con nivel (ej: "inglés avanzado")
7. area_experiencia: Área de experiencia requerida (ej: "desarrollo backend")

IMPORTANTE:
- Responde SOLO con JSON válido
- No agregues explicaciones
- Usa null si no encuentras el campo
- Skills deben ser listas

FORMATO JSON:
{{
    "experiencia_anios": 3,
    "nivel_educativo": "universitario",
    "titulo_requerido": "Ingeniería en Sistemas",
    "skills_tecnicas": ["Python", "Django", "PostgreSQL"],
    "soft_skills": ["trabajo en equipo", "comunicación"],
    "idiomas": "inglés intermedio",
    "area_experiencia": "desarrollo web"
}}

JSON:"""

        return prompt

    def call_ollama(self, prompt: str) -> str:
        """Llama a Ollama"""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            if result.returncode != 0:
                logger.warning(f"Ollama error: {result.stderr}")
                return ""

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.warning("Timeout esperando Ollama")
            return ""
        except Exception as e:
            logger.warning(f"Error llamando Ollama: {e}")
            return ""

    def parse_json_response(self, response: str) -> Dict:
        """Parsea respuesta JSON de Ollama"""
        try:
            # Extraer JSON si viene con texto adicional
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            # Buscar JSON con regex
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            result = json.loads(response)
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Error procesando respuesta: {e}")
            return {}

    def extract(self, titulo: str, descripcion: str) -> Dict:
        """Extrae información de una oferta"""
        prompt = self.create_extraction_prompt(titulo, descripcion)
        response = self.call_ollama(prompt)

        if not response:
            return {}

        result = self.parse_json_response(response)

        # Normalizar formato
        normalized = {}

        if result.get('experiencia_anios'):
            normalized['experiencia_min_anios'] = result['experiencia_anios']

        if result.get('nivel_educativo'):
            normalized['nivel_educativo'] = result['nivel_educativo']

        if result.get('titulo_requerido'):
            normalized['titulo_requerido'] = result['titulo_requerido']

        if result.get('skills_tecnicas') and isinstance(result['skills_tecnicas'], list):
            # Filter out None values
            skills = [s for s in result['skills_tecnicas'] if s]
            if skills:
                normalized['skills_tecnicas_list'] = ', '.join(skills)
                normalized['skills_tecnicas_count'] = len(skills)

        if result.get('soft_skills') and isinstance(result['soft_skills'], list):
            # Filter out None values
            soft_skills = [s for s in result['soft_skills'] if s]
            if soft_skills:
                normalized['soft_skills_list'] = ', '.join(soft_skills)
                normalized['soft_skills_count'] = len(soft_skills)

        if result.get('idiomas'):
            normalized['idioma_principal'] = result['idiomas']

        if result.get('area_experiencia'):
            normalized['area_experiencia'] = result['area_experiencia']

        return normalized


def compare_extraction_methods(sample_size: int = 100):
    """Compara los 4 métodos de extracción"""

    logger.info("\n" + "=" * 70)
    logger.info("PRUEBA DE EXTRACCIÓN HÍBRIDA")
    logger.info("=" * 70)

    # Cargar datos con resultados de Fase 1 (Regex) y Fase 2 (NER)
    logger.info("\n1. Cargando dataset con Regex y NER...")
    df_full = pd.read_csv(
        r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_ner_20251027_130824.csv',
        low_memory=False
    )

    # Seleccionar muestra aleatoria con ofertas que tengan descripción
    df_with_desc = df_full[df_full['descripcion'].notna() & (df_full['descripcion'].str.len() > 100)]

    if len(df_with_desc) < sample_size:
        logger.warning(f"Solo hay {len(df_with_desc)} ofertas con descripción, usando todas")
        sample_size = len(df_with_desc)

    sample_indices = random.sample(range(len(df_with_desc)), sample_size)
    df_sample = df_with_desc.iloc[sample_indices].copy()

    logger.info(f"   Muestra: {len(df_sample)} ofertas con descripción")

    # Inicializar extractor LLM
    logger.info("\n2. Inicializando extractor LLM (Ollama)...")
    llm_extractor = OllamaDirectExtractor(model='llama3')

    # Procesar muestra con LLM
    logger.info(f"\n3. Extrayendo con LLM ({len(df_sample)} ofertas)...")
    logger.info("   Esto tomará ~5 minutos...\n")

    llm_results = []

    for idx, row in tqdm(df_sample.iterrows(), total=len(df_sample), desc="Extracción LLM"):
        titulo = row.get('titulo', '')
        descripcion = row.get('descripcion', '')

        llm_result = llm_extractor.extract(titulo, descripcion)
        llm_results.append(llm_result)

    # Agregar resultados LLM al DataFrame
    df_llm = pd.DataFrame(llm_results)

    # Renombrar columnas para distinguir
    for col in df_llm.columns:
        df_sample[f'llm_{col}'] = df_llm[col].values

    logger.info("\n✓ Extracción LLM completada\n")

    # Comparar resultados
    logger.info("=" * 70)
    logger.info("COMPARACIÓN DE MÉTODOS")
    logger.info("=" * 70)

    results = {
        'Método': [],
        'Experiencia': [],
        'Educación': [],
        'Skills Técnicas': [],
        'Soft Skills': [],
        'Idiomas': []
    }

    # Fase 1: Regex
    results['Método'].append('Fase 1 (Regex)')
    results['Experiencia'].append(df_sample['experiencia_min_anios'].notna().sum())
    results['Educación'].append(df_sample['nivel_educativo'].notna().sum())
    results['Skills Técnicas'].append(df_sample['skills_tecnicas_list'].notna().sum())
    results['Soft Skills'].append(df_sample['soft_skills_list'].notna().sum())
    results['Idiomas'].append(df_sample['idioma_principal'].notna().sum())

    # Fase 2: NER
    results['Método'].append('Fase 2 (NER)')
    results['Experiencia'].append(df_sample['experiencia_min_anios.1'].notna().sum() if 'experiencia_min_anios.1' in df_sample else 0)
    results['Educación'].append(df_sample['nivel_educativo.1'].notna().sum() if 'nivel_educativo.1' in df_sample else 0)
    results['Skills Técnicas'].append(df_sample['skills_tecnicas_list.1'].notna().sum() if 'skills_tecnicas_list.1' in df_sample else 0)
    results['Soft Skills'].append(df_sample['soft_skills_list.1'].notna().sum() if 'soft_skills_list.1' in df_sample else 0)
    results['Idiomas'].append(df_sample['idioma_principal.1'].notna().sum() if 'idioma_principal.1' in df_sample else 0)

    # Fase 3: LLM directo
    results['Método'].append('Fase 3 (LLM)')
    results['Experiencia'].append(df_sample['llm_experiencia_min_anios'].notna().sum() if 'llm_experiencia_min_anios' in df_sample else 0)
    results['Educación'].append(df_sample['llm_nivel_educativo'].notna().sum() if 'llm_nivel_educativo' in df_sample else 0)
    results['Skills Técnicas'].append(df_sample['llm_skills_tecnicas_list'].notna().sum() if 'llm_skills_tecnicas_list' in df_sample else 0)
    results['Soft Skills'].append(df_sample['llm_soft_skills_list'].notna().sum() if 'llm_soft_skills_list' in df_sample else 0)
    results['Idiomas'].append(df_sample['llm_idioma_principal'].notna().sum() if 'llm_idioma_principal' in df_sample else 0)

    # Crear tabla de resultados
    df_results = pd.DataFrame(results)

    # Calcular porcentajes
    for col in df_results.columns[1:]:
        df_results[f'{col} %'] = (df_results[col] / len(df_sample) * 100).round(1)

    print("\nCOBERTURA (cantidad de ofertas con información extraída):")
    print("=" * 80)
    print(df_results.to_string(index=False))
    print("=" * 80)

    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'../data/ner_training/hybrid_test_{timestamp}.csv'
    df_sample.to_csv(output_path, index=False)
    logger.info(f"\n✓ Resultados guardados: {output_path}")

    # Guardar comparación
    comparison_path = f'../data/ner_training/comparison_{timestamp}.csv'
    df_results.to_csv(comparison_path, index=False)
    logger.info(f"✓ Comparación guardada: {comparison_path}")

    return df_sample, df_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Prueba de extracción híbrida')
    parser.add_argument('--sample-size', type=int, default=100, help='Tamaño de muestra')

    args = parser.parse_args()

    try:
        df_sample, df_results = compare_extraction_methods(sample_size=args.sample_size)

        logger.info("\n" + "=" * 70)
        logger.info("PRUEBA COMPLETADA")
        logger.info("=" * 70)
        logger.info("\nPróximos pasos:")
        logger.info("1. Revisar resultados en archivos CSV generados")
        logger.info("2. Si LLM > Regex, considerar enfoque híbrido")
        logger.info("3. Si Regex > LLM, continuar con Fase 1 (Regex)")

    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
