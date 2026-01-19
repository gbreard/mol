# -*- coding: utf-8 -*-
"""
Train NER Model - Entrena modelo NER custom con spaCy
======================================================

Script para entrenar un modelo NER personalizado usando spaCy con
datos anotados de ofertas laborales.
"""

import sys
from pathlib import Path
import json
import random
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import logging
from datetime import datetime
from typing import List, Tuple, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NERModelTrainer:
    """Entrenador de modelo NER custom"""

    def __init__(
        self,
        train_data_path: str,
        dev_data_path: str = None,
        output_dir: str = None,
        base_model: str = None
    ):
        """
        Inicializa el entrenador

        Args:
            train_data_path: Path al archivo JSON con datos de entrenamiento
            dev_data_path: Path al archivo JSON con datos de validación
            output_dir: Directorio para guardar el modelo entrenado
            base_model: Modelo base de spaCy (default: es_core_news_sm)
        """
        self.train_data_path = Path(train_data_path)
        self.dev_data_path = Path(dev_data_path) if dev_data_path else None

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = project_root / "02.5_nlp_extraction" / "models" / "ner_model"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_model = base_model or "es_core_news_sm"

        self.nlp = None
        self.train_examples = []
        self.dev_examples = []
        self.entity_types = set()

    def load_training_data(self) -> List[Example]:
        """
        Carga datos de entrenamiento desde JSON

        Returns:
            Lista de Examples de spaCy
        """
        logger.info(f"Cargando datos de entrenamiento: {self.train_data_path.name}")

        with open(self.train_data_path, 'r', encoding='utf-8') as f:
            train_data = json.load(f)

        logger.info(f"  Cargados {len(train_data)} ejemplos")

        return train_data

    def load_dev_data(self) -> List[Example]:
        """Carga datos de validación desde JSON"""
        if not self.dev_data_path or not self.dev_data_path.exists():
            logger.warning("No hay datos de validación")
            return []

        logger.info(f"Cargando datos de validación: {self.dev_data_path.name}")

        with open(self.dev_data_path, 'r', encoding='utf-8') as f:
            dev_data = json.load(f)

        logger.info(f"  Cargados {len(dev_data)} ejemplos")

        return dev_data

    def initialize_model(self):
        """Inicializa modelo spaCy (blank o desde base)"""
        logger.info("\n" + "=" * 70)
        logger.info("INICIALIZANDO MODELO")
        logger.info("=" * 70)

        try:
            # Intentar cargar modelo base
            logger.info(f"Intentando cargar modelo base: {self.base_model}")
            self.nlp = spacy.load(self.base_model)
            logger.info(f"  ✓ Modelo base cargado: {self.base_model}")

            # Verificar si ya tiene NER
            if "ner" not in self.nlp.pipe_names:
                ner = self.nlp.add_pipe("ner", last=True)
                logger.info("  ✓ Componente NER agregado")
            else:
                ner = self.nlp.get_pipe("ner")
                logger.info("  ✓ Componente NER existente encontrado")

        except OSError:
            # Si no existe el modelo base, crear uno blank
            logger.warning(f"  ✗ Modelo base '{self.base_model}' no encontrado")
            logger.info("  Creando modelo blank en español...")

            self.nlp = spacy.blank("es")
            ner = self.nlp.add_pipe("ner", last=True)
            logger.info("  ✓ Modelo blank creado")

        # Agregar tipos de entidades
        train_data = self.load_training_data()

        for item in train_data:
            for start, end, label in item['entities']:
                # Skip None or empty labels
                if label and label.strip():
                    self.entity_types.add(label)
                    ner.add_label(label)

        logger.info(f"\nTipos de entidades agregados: {len(self.entity_types)}")
        # Filter out None before sorting
        valid_entity_types = [et for et in self.entity_types if et is not None]
        for entity_type in sorted(valid_entity_types):
            logger.info(f"  - {entity_type}")

        logger.info("=" * 70)

    def create_examples(self, data: List[Dict]) -> List[Example]:
        """
        Crea Examples de spaCy desde datos cargados

        Args:
            data: Lista de dicts con text y entities

        Returns:
            Lista de Examples
        """
        examples = []

        for item in data:
            text = item['text']
            entities = item['entities']

            # Crear doc de ejemplo
            doc = self.nlp.make_doc(text)

            # Crear ejemplo con anotaciones
            example = Example.from_dict(doc, {"entities": entities})
            examples.append(example)

        return examples

    def train(
        self,
        n_iter: int = 30,
        batch_size: int = 8,
        dropout: float = 0.3,
        learn_rate: float = 0.001
    ):
        """
        Entrena el modelo NER

        Args:
            n_iter: Número de iteraciones de entrenamiento
            batch_size: Tamaño de batch
            dropout: Tasa de dropout
            learn_rate: Learning rate inicial
        """
        logger.info("\n" + "=" * 70)
        logger.info("ENTRENAMIENTO DEL MODELO NER")
        logger.info("=" * 70)
        logger.info(f"Iteraciones: {n_iter}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Dropout: {dropout}")
        logger.info(f"Learning rate: {learn_rate}")
        logger.info("")

        # Cargar datos
        train_data = self.load_training_data()
        dev_data = self.load_dev_data() if self.dev_data_path else []

        # Crear examples
        self.train_examples = self.create_examples(train_data)
        self.dev_examples = self.create_examples(dev_data) if dev_data else []

        logger.info(f"Ejemplos de entrenamiento: {len(self.train_examples)}")
        logger.info(f"Ejemplos de validación: {len(self.dev_examples)}")
        logger.info("")

        # Deshabilitar otros pipes durante entrenamiento
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            # Inicializar optimizer
            optimizer = self.nlp.create_optimizer()
            optimizer.learn_rate = learn_rate

            # Training loop
            for iteration in range(n_iter):
                random.shuffle(self.train_examples)

                losses = {}
                batches = minibatch(self.train_examples, size=compounding(4.0, batch_size, 1.001))

                for batch in batches:
                    self.nlp.update(
                        batch,
                        drop=dropout,
                        losses=losses,
                        sgd=optimizer
                    )

                # Evaluar en dev set
                if self.dev_examples and (iteration + 1) % 5 == 0:
                    scores = self.nlp.evaluate(self.dev_examples)
                    logger.info(
                        f"Iter {iteration + 1:3d} | "
                        f"Loss: {losses.get('ner', 0):.4f} | "
                        f"P: {scores['ents_p']:.3f} | "
                        f"R: {scores['ents_r']:.3f} | "
                        f"F: {scores['ents_f']:.3f}"
                    )
                else:
                    logger.info(
                        f"Iter {iteration + 1:3d} | "
                        f"Loss: {losses.get('ner', 0):.4f}"
                    )

        logger.info("\n" + "=" * 70)
        logger.info("ENTRENAMIENTO COMPLETADO")
        logger.info("=" * 70)

    def evaluate(self):
        """Evalúa el modelo en el dev set"""
        if not self.dev_examples:
            logger.warning("No hay datos de validación para evaluar")
            return

        logger.info("\n" + "=" * 70)
        logger.info("EVALUACIÓN FINAL")
        logger.info("=" * 70)

        scores = self.nlp.evaluate(self.dev_examples)

        logger.info(f"\nMétricas generales:")
        logger.info(f"  Precision: {scores['ents_p']:.3f}")
        logger.info(f"  Recall: {scores['ents_r']:.3f}")
        logger.info(f"  F-score: {scores['ents_f']:.3f}")

        # Métricas por entidad
        logger.info(f"\nMétricas por tipo de entidad:")
        for entity_type in sorted(self.entity_types):
            key = f"ents_per_type.{entity_type}"
            if key in scores:
                type_scores = scores[key]
                logger.info(f"  {entity_type}:")
                logger.info(f"    P: {type_scores.get('p', 0):.3f}")
                logger.info(f"    R: {type_scores.get('r', 0):.3f}")
                logger.info(f"    F: {type_scores.get('f', 0):.3f}")

        logger.info("=" * 70)

        return scores

    def save_model(self):
        """Guarda el modelo entrenado"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.output_dir / f"model_{timestamp}"

        self.nlp.to_disk(model_path)

        logger.info(f"\n[GUARDADO] Modelo: {model_path}")

        # Guardar metadata
        metadata = {
            "timestamp": timestamp,
            "entity_types": list(self.entity_types),
            "train_examples": len(self.train_examples),
            "dev_examples": len(self.dev_examples),
            "base_model": self.base_model
        }

        metadata_path = model_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"[GUARDADO] Metadata: {metadata_path}")

        # Crear symlink al último modelo
        latest_link = self.output_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()

        try:
            latest_link.symlink_to(model_path.name, target_is_directory=True)
            logger.info(f"[ENLACE] {latest_link} -> {model_path.name}")
        except OSError:
            # En Windows puede fallar sin permisos de admin
            logger.warning("No se pudo crear symlink 'latest' (requiere permisos de admin en Windows)")

        return model_path

    def test_model(self, test_texts: List[str] = None):
        """
        Prueba el modelo con textos de ejemplo

        Args:
            test_texts: Lista de textos para probar (None = usar ejemplos default)
        """
        if test_texts is None:
            test_texts = [
                "Buscamos desarrollador Python con mínimo 3 años de experiencia en Django y React.",
                "Requisitos: título universitario en Sistemas, inglés avanzado, conocimientos de AWS.",
                "Se requiere profesional con experiencia en análisis de datos, dominio de SQL y Python.",
                "Pasantía para estudiantes de ingeniería con interés en machine learning."
            ]

        logger.info("\n" + "=" * 70)
        logger.info("PRUEBA DEL MODELO")
        logger.info("=" * 70)

        for i, text in enumerate(test_texts, 1):
            logger.info(f"\nEjemplo {i}:")
            logger.info(f"Texto: {text}")

            doc = self.nlp(text)

            if doc.ents:
                logger.info("Entidades detectadas:")
                for ent in doc.ents:
                    logger.info(f"  [{ent.label_}] {ent.text} (pos: {ent.start_char}-{ent.end_char})")
            else:
                logger.info("  (no se detectaron entidades)")

        logger.info("=" * 70)


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Entrena modelo NER custom con spaCy')

    parser.add_argument(
        '--train-data',
        type=str,
        required=True,
        help='Path al archivo JSON con datos de entrenamiento'
    )

    parser.add_argument(
        '--dev-data',
        type=str,
        default=None,
        help='Path al archivo JSON con datos de validación'
    )

    parser.add_argument(
        '--base-model',
        type=str,
        default='es_core_news_sm',
        help='Modelo base de spaCy (default: es_core_news_sm)'
    )

    parser.add_argument(
        '--n-iter',
        type=int,
        default=30,
        help='Número de iteraciones de entrenamiento (default: 30)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=8,
        help='Tamaño de batch (default: 8)'
    )

    parser.add_argument(
        '--dropout',
        type=float,
        default=0.3,
        help='Tasa de dropout (default: 0.3)'
    )

    parser.add_argument(
        '--learn-rate',
        type=float,
        default=0.001,
        help='Learning rate inicial (default: 0.001)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Directorio de salida para el modelo'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Seed para reproducibilidad (default: 42)'
    )

    args = parser.parse_args()

    # Fijar seeds
    random.seed(args.seed)
    spacy.util.fix_random_seed(args.seed)

    # Crear entrenador
    trainer = NERModelTrainer(
        train_data_path=args.train_data,
        dev_data_path=args.dev_data,
        output_dir=args.output_dir,
        base_model=args.base_model
    )

    # Inicializar modelo
    trainer.initialize_model()

    # Entrenar
    trainer.train(
        n_iter=args.n_iter,
        batch_size=args.batch_size,
        dropout=args.dropout,
        learn_rate=args.learn_rate
    )

    # Evaluar
    if args.dev_data:
        trainer.evaluate()

    # Guardar
    model_path = trainer.save_model()

    # Probar
    trainer.test_model()

    logger.info("\n" + "=" * 70)
    logger.info("¡PROCESO COMPLETADO!")
    logger.info("=" * 70)
    logger.info(f"\nModelo guardado en: {model_path}")
    logger.info(f"\nPróximos pasos:")
    logger.info(f"1. Cargar modelo: nlp = spacy.load('{model_path}')")
    logger.info(f"2. Implementar extractores NER que usen este modelo")
    logger.info(f"3. Procesar dataset completo con NER")
    logger.info(f"4. Comparar resultados con Fase 1 (Regex)")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
