# -*- coding: utf-8 -*-
"""
Auto-annotate with LLM - Anota automáticamente usando LLM (GPT-4/Claude)
=========================================================================

Usa un LLM para generar anotaciones NER automáticamente sin intervención humana.
"""

import sys
from pathlib import Path
import json
import os
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMAnnotator:
    """Anotador automático usando LLM"""

    def __init__(self, samples_jsonl: str, output_jsonl: str, llm_provider: str = 'openai'):
        """
        Inicializa el anotador LLM

        Args:
            samples_jsonl: Path al JSONL con muestras
            output_jsonl: Path de salida
            llm_provider: 'openai' o 'anthropic'
        """
        self.samples_jsonl = Path(samples_jsonl)
        self.output_jsonl = Path(output_jsonl)
        self.llm_provider = llm_provider

        # Inicializar cliente LLM
        self._init_llm_client()

    def _init_llm_client(self):
        """Inicializa cliente del LLM"""
        if self.llm_provider == 'openai':
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                self.model = 'gpt-4-turbo-preview'
                logger.info(f"✓ Cliente OpenAI inicializado (modelo: {self.model})")
            except Exception as e:
                logger.error(f"Error inicializando OpenAI: {e}")
                logger.info("Instalar: pip install openai")
                logger.info("Configurar: export OPENAI_API_KEY=sk-...")
                raise

        elif self.llm_provider == 'anthropic':
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                self.model = 'claude-3-sonnet-20240229'
                logger.info(f"✓ Cliente Anthropic inicializado (modelo: {self.model})")
            except Exception as e:
                logger.error(f"Error inicializando Anthropic: {e}")
                logger.info("Instalar: pip install anthropic")
                logger.info("Configurar: export ANTHROPIC_API_KEY=sk-ant-...")
                raise

    def create_annotation_prompt(self, text: str) -> str:
        """
        Crea prompt para el LLM

        Args:
            text: Texto de la oferta laboral

        Returns:
            Prompt formateado
        """
        prompt = f"""Eres un experto en análisis de ofertas laborales. Tu tarea es identificar y etiquetar entidades específicas en el siguiente texto de una oferta de trabajo.

TIPOS DE ENTIDADES:
1. YEARS: Años de experiencia requeridos (ej: "3 años", "mínimo 5 años")
2. EDUCATION: Nivel educativo o título (ej: "universitario completo", "licenciatura en sistemas")
3. SKILL: Habilidades técnicas (ej: "Python", "Django", "SQL", "AWS")
4. SOFT_SKILL: Habilidades blandas (ej: "trabajo en equipo", "liderazgo")
5. LANGUAGE: Idiomas (ej: "inglés avanzado", "portugués intermedio")
6. AREA: Área de experiencia (ej: "desarrollo backend", "análisis de datos")

TEXTO DE LA OFERTA:
```
{text}
```

INSTRUCCIONES:
1. Identifica TODAS las entidades de los tipos mencionados
2. Para cada entidad, indica:
   - Posición de inicio (índice de carácter)
   - Posición de fin (índice de carácter)
   - Tipo de entidad
   - Texto exacto

3. Devuelve SOLO un JSON válido en este formato:
{{
  "entities": [
    {{"start": 50, "end": 57, "label": "SKILL", "text": "Python"}},
    {{"start": 120, "end": 127, "label": "YEARS", "text": "3 años"}},
    ...
  ]
}}

NO agregues explicaciones, solo el JSON."""

        return prompt

    def annotate_with_llm(self, text: str) -> List[Dict]:
        """
        Anota un texto usando el LLM

        Args:
            text: Texto a anotar

        Returns:
            Lista de entidades anotadas
        """
        prompt = self.create_annotation_prompt(text)

        try:
            if self.llm_provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en NER para ofertas laborales. Respondes solo con JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                content = response.choices[0].message.content

            elif self.llm_provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text

            # Parsear JSON
            # Extraer JSON si viene con ```json ... ```
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            result = json.loads(content)
            entities = result.get('entities', [])

            return entities

        except Exception as e:
            logger.warning(f"Error anotando con LLM: {e}")
            return []

    def load_samples(self) -> List[Dict]:
        """Carga las muestras del JSONL"""
        samples = []
        with open(self.samples_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples

    def auto_annotate_all(self, limit: int = None):
        """
        Anota todas las muestras con LLM

        Args:
            limit: Límite de muestras a procesar (None = todas)
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"ANOTACIÓN AUTOMÁTICA CON LLM ({self.llm_provider.upper()})")
        logger.info("=" * 70)

        # Cargar muestras
        samples = self.load_samples()

        if limit:
            samples = samples[:limit]
            logger.info(f"Limitando a {limit} muestras (modo test)")

        logger.info(f"Total muestras a anotar: {len(samples)}")
        logger.info("")

        annotated_samples = []
        stats = {
            'total': len(samples),
            'success': 0,
            'failed': 0,
            'entities_total': 0
        }

        for i, sample in enumerate(samples, 1):
            logger.info(f"Procesando {i}/{len(samples)}... ", end='')

            try:
                # Anotar con LLM
                entities = self.annotate_with_llm(sample['text'])

                # Convertir formato
                labels = [[e['start'], e['end'], e['label']] for e in entities]

                annotated = {
                    'id': sample['id'],
                    'text': sample['text'],
                    'label': labels,
                    'meta': sample.get('meta', {})
                }

                # Metadata
                annotated['meta']['llm_annotated'] = True
                annotated['meta']['llm_provider'] = self.llm_provider
                annotated['meta']['entities_count'] = len(labels)

                annotated_samples.append(annotated)

                stats['success'] += 1
                stats['entities_total'] += len(labels)

                logger.info(f"✓ {len(labels)} entidades")

            except Exception as e:
                logger.info(f"✗ Error: {e}")
                stats['failed'] += 1

            # Guardar progreso cada 50 muestras
            if i % 50 == 0:
                self._save_progress(annotated_samples)

        # Guardar final
        with open(self.output_jsonl, 'w', encoding='utf-8') as f:
            for sample in annotated_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info("\n" + "=" * 70)
        logger.info("RESULTADOS")
        logger.info("=" * 70)
        logger.info(f"Exitosas: {stats['success']}/{stats['total']}")
        logger.info(f"Fallidas: {stats['failed']}")
        logger.info(f"Total entidades: {stats['entities_total']}")
        logger.info(f"Promedio por muestra: {stats['entities_total']/stats['success']:.1f}")
        logger.info(f"\n[GUARDADO] {self.output_jsonl}")
        logger.info("=" * 70)

        # Estimación de costo
        if self.llm_provider == 'openai':
            # GPT-4 Turbo: ~$0.01/1K tokens input, ~$0.03/1K tokens output
            avg_tokens_per_sample = 1500  # estimación
            total_tokens = avg_tokens_per_sample * stats['success']
            estimated_cost = (total_tokens / 1000) * 0.02
            logger.info(f"\n💰 Costo estimado: ${estimated_cost:.2f} USD")

    def _save_progress(self, samples: List[Dict]):
        """Guarda progreso intermedio"""
        progress_path = self.output_jsonl.parent / f"{self.output_jsonl.stem}_progress.jsonl"
        with open(progress_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Anota automáticamente con LLM')

    parser.add_argument(
        '--samples-jsonl',
        type=str,
        default=r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\ner_training\ner_samples_for_annotation_20251027_101013.jsonl',
        help='Path al JSONL con muestras'
    )

    parser.add_argument(
        '--output-jsonl',
        type=str,
        default=None,
        help='Path de salida'
    )

    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic'],
        default='openai',
        help='Proveedor LLM (default: openai)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de muestras (para testing)'
    )

    args = parser.parse_args()

    if args.output_jsonl is None:
        samples_path = Path(args.samples_jsonl)
        args.output_jsonl = samples_path.parent / f"{samples_path.stem}_llm_annotated.jsonl"

    # Crear anotador
    annotator = LLMAnnotator(
        samples_jsonl=args.samples_jsonl,
        output_jsonl=args.output_jsonl,
        llm_provider=args.provider
    )

    # Anotar
    annotator.auto_annotate_all(limit=args.limit)

    logger.info("\n¡Anotación automática completada! 🎉")
    logger.info("\nPróximos pasos:")
    logger.info("1. Revisar calidad de anotaciones (sample de 20-30 ofertas)")
    logger.info("2. Si calidad >90%, usar directamente para training")
    logger.info("3. Si calidad 70-90%, revisar y corregir errores")
    logger.info("4. Continuar con convert_annotations_to_spacy.py")


if __name__ == "__main__":
    main()
