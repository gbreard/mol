# -*- coding: utf-8 -*-
"""
Auto-annotate with Ollama - Anota automáticamente usando LLM local (Ollama)
===========================================================================

Usa modelos LLM locales vía Ollama para generar anotaciones NER sin costo.
"""

import sys
from pathlib import Path
import json
import subprocess
import re
from typing import List, Dict
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaAnnotator:
    """Anotador automático usando Ollama (LLM local)"""

    def __init__(
        self,
        samples_jsonl: str,
        output_jsonl: str,
        model: str = 'llama3'
    ):
        """
        Inicializa el anotador Ollama

        Args:
            samples_jsonl: Path al JSONL con muestras
            output_jsonl: Path de salida
            model: Modelo de Ollama a usar (default: llama3)
        """
        self.samples_jsonl = Path(samples_jsonl)
        self.output_jsonl = Path(output_jsonl)
        self.model = model

        # Verificar Ollama
        self._verify_ollama()

    def _verify_ollama(self):
        """Verifica que Ollama esté instalado y el modelo disponible"""
        try:
            # Verificar Ollama
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Ollama no está instalado o no funciona")

            # Verificar que el modelo existe
            if self.model not in result.stdout:
                logger.warning(f"Modelo '{self.model}' no encontrado")
                logger.info("\nModelos disponibles:")
                logger.info(result.stdout)

                # Sugerir descargar si no existe
                response = input(f"\n¿Descargar modelo {self.model}? (s/n): ")
                if response.lower() == 's':
                    logger.info(f"Descargando {self.model}...")
                    subprocess.run(['ollama', 'pull', self.model])
                else:
                    raise RuntimeError(f"Modelo {self.model} no disponible")

            logger.info(f"✓ Ollama verificado, usando modelo: {self.model}")

        except FileNotFoundError:
            logger.error("Ollama no está instalado")
            logger.info("\nInstalar Ollama:")
            logger.info("  Windows/Mac: https://ollama.com/download")
            logger.info("  Linux: curl -fsSL https://ollama.com/install.sh | sh")
            raise

    def create_annotation_prompt(self, text: str) -> str:
        """
        Crea prompt optimizado para Ollama

        Args:
            text: Texto de la oferta laboral

        Returns:
            Prompt formateado
        """
        prompt = f"""Eres un experto en NER para ofertas laborales. Tu tarea es identificar entidades y devolver solo el TEXTO exacto de cada entidad, NO los índices.

ENTIDADES A DETECTAR:
1. YEARS: Años de experiencia (ej: "3 años", "mínimo 5 años", "2 a 4 años")
2. EDUCATION: Nivel educativo o título (ej: "universitario completo", "licenciatura en sistemas", "secundario")
3. SKILL: Habilidades técnicas (ej: "Python", "Django", "SQL", "JavaScript", "Excel")
4. SOFT_SKILL: Habilidades blandas (ej: "trabajo en equipo", "liderazgo", "comunicación")
5. LANGUAGE: Idiomas con nivel (ej: "inglés avanzado", "portugués intermedio")
6. AREA: Área de experiencia (ej: "desarrollo backend", "análisis de datos", "contabilidad")

TEXTO DE LA OFERTA:
\"\"\"
{text[:1000]}
\"\"\"

INSTRUCCIONES:
- Identifica TODAS las entidades relevantes
- Devuelve solo el texto exacto que aparece en la oferta
- NO inventes entidades que no existan
- Responde SOLO con JSON, sin explicaciones

FORMATO JSON:
{{"entities": [{{"text": "Python", "label": "SKILL"}}, {{"text": "3 años", "label": "YEARS"}}, ...]}}

JSON:"""

        return prompt

    def call_ollama(self, prompt: str) -> str:
        """
        Llama a Ollama con el prompt

        Args:
            prompt: Prompt a enviar

        Returns:
            Respuesta del modelo
        """
        try:
            # Llamar a Ollama via subprocess
            result = subprocess.run(
                ['ollama', 'run', self.model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60  # 60 segundos timeout
            )

            if result.returncode != 0:
                logger.warning(f"Ollama error: {result.stderr}")
                return ""

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.warning("Timeout esperando respuesta de Ollama")
            return ""
        except Exception as e:
            logger.warning(f"Error llamando Ollama: {e}")
            return ""

    def parse_json_response(self, response: str, original_text: str) -> List[Dict]:
        """
        Parsea la respuesta JSON del modelo y calcula posiciones

        Args:
            response: Respuesta del modelo
            original_text: Texto original para buscar posiciones

        Returns:
            Lista de entidades con posiciones
        """
        try:
            # Extraer JSON si viene con texto adicional
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            # Intentar encontrar JSON con regex si no está limpio
            json_match = re.search(r'\{.*"entities".*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            # Parsear
            result = json.loads(response)
            entities = result.get('entities', [])

            # Validar formato y encontrar posiciones
            valid_entities = []
            for ent in entities:
                if 'text' not in ent or 'label' not in ent:
                    continue

                entity_text = ent['text'].strip()
                if not entity_text:
                    continue

                # Buscar texto en el documento original
                # Buscar case-insensitive
                text_lower = original_text.lower()
                entity_lower = entity_text.lower()

                pos = text_lower.find(entity_lower)
                if pos != -1:
                    # Encontrado - usar posición del texto original
                    valid_entities.append({
                        'text': entity_text,
                        'label': ent['label'],
                        'start': pos,
                        'end': pos + len(entity_text)
                    })
                else:
                    # No encontrado exactamente, intentar palabras similares
                    # Por ahora skip, pero podríamos hacer fuzzy match
                    pass

            return valid_entities

        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}")
            logger.debug(f"Respuesta: {response[:200]}")
            return []
        except Exception as e:
            logger.warning(f"Error procesando respuesta: {e}")
            return []

    def annotate_with_ollama(self, text: str) -> List[Dict]:
        """
        Anota un texto usando Ollama

        Args:
            text: Texto a anotar

        Returns:
            Lista de entidades anotadas
        """
        # Crear prompt
        prompt = self.create_annotation_prompt(text)

        # Llamar Ollama
        response = self.call_ollama(prompt)

        if not response:
            return []

        # Parsear respuesta y encontrar posiciones
        entities = self.parse_json_response(response, text)

        return entities

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
        Anota todas las muestras con Ollama

        Args:
            limit: Límite de muestras a procesar (None = todas)
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"ANOTACIÓN AUTOMÁTICA CON OLLAMA ({self.model})")
        logger.info("=" * 70)

        # Cargar muestras
        samples = self.load_samples()

        if limit:
            samples = samples[:limit]
            logger.info(f"Limitando a {limit} muestras (modo test)")

        logger.info(f"Total muestras a anotar: {len(samples)}")
        logger.info(f"Modelo: {self.model}")
        logger.info("")

        annotated_samples = []
        stats = {
            'total': len(samples),
            'success': 0,
            'failed': 0,
            'entities_total': 0
        }

        # Usar tqdm para barra de progreso
        for sample in tqdm(samples, desc="Anotando"):
            try:
                # Anotar con Ollama
                entities = self.annotate_with_ollama(sample['text'])

                # Convertir formato
                labels = [[e['start'], e['end'], e['label']] for e in entities]

                annotated = {
                    'id': sample['id'],
                    'text': sample['text'],
                    'label': labels,
                    'meta': sample.get('meta', {})
                }

                # Metadata
                annotated['meta']['ollama_annotated'] = True
                annotated['meta']['ollama_model'] = self.model
                annotated['meta']['entities_count'] = len(labels)

                annotated_samples.append(annotated)

                if len(labels) > 0:
                    stats['success'] += 1
                    stats['entities_total'] += len(labels)
                else:
                    stats['failed'] += 1

            except Exception as e:
                logger.warning(f"Error anotando muestra {sample['id']}: {e}")
                stats['failed'] += 1

            # Guardar progreso cada 50 muestras
            if len(annotated_samples) % 50 == 0:
                self._save_progress(annotated_samples)

        # Guardar final
        with open(self.output_jsonl, 'w', encoding='utf-8') as f:
            for sample in annotated_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info("\n" + "=" * 70)
        logger.info("RESULTADOS")
        logger.info("=" * 70)
        logger.info(f"Procesadas: {len(annotated_samples)}/{stats['total']}")
        logger.info(f"Con entidades: {stats['success']}")
        logger.info(f"Sin entidades: {stats['failed']}")
        logger.info(f"Total entidades: {stats['entities_total']}")
        if stats['success'] > 0:
            logger.info(f"Promedio por muestra: {stats['entities_total']/stats['success']:.1f}")
        logger.info(f"\n[GUARDADO] {self.output_jsonl}")
        logger.info("=" * 70)

        logger.info("\n💰 COSTO: $0 (modelo local)")
        logger.info(f"⚡ Tiempo: ~{len(samples)*3/60:.0f} minutos estimados")

    def _save_progress(self, samples: List[Dict]):
        """Guarda progreso intermedio"""
        progress_path = self.output_jsonl.parent / f"{self.output_jsonl.stem}_progress.jsonl"
        with open(progress_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Anota automáticamente con Ollama (LLM local)')

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
        '--model',
        type=str,
        default='llama3',
        help='Modelo de Ollama (default: llama3). Opciones: llama3, deepseek-r1:14b, gpt-oss:20b, deepseek-r1:32b'
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
        args.output_jsonl = samples_path.parent / f"{samples_path.stem}_ollama_annotated.jsonl"

    # Crear anotador
    try:
        annotator = OllamaAnnotator(
            samples_jsonl=args.samples_jsonl,
            output_jsonl=args.output_jsonl,
            model=args.model
        )

        # Anotar
        annotator.auto_annotate_all(limit=args.limit)

        logger.info("\n¡Anotación automática completada! 🎉")
        logger.info("\nPróximos pasos:")
        logger.info("1. Revisar calidad (sample de 20-30 ofertas)")
        logger.info("2. Continuar con convert_annotations_to_spacy.py")
        logger.info("3. Entrenar modelo NER")

    except Exception as e:
        logger.error(f"\nError: {e}")
        logger.info("\nSoluciones:")
        logger.info("- Verificar que Ollama esté corriendo: ollama list")
        logger.info("- Descargar modelo: ollama pull llama3")
        logger.info("- Probar otro modelo: --model deepseek-r1:14b")
        sys.exit(1)


if __name__ == "__main__":
    main()
