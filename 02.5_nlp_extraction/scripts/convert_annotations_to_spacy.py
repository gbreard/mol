# -*- coding: utf-8 -*-
"""
Convert Annotations to spaCy - Convierte anotaciones IOB a formato spaCy
=========================================================================

Script para convertir anotaciones de entidades desde formato IOB/JSONL
al formato de entrenamiento de spaCy.
"""

import sys
from pathlib import Path
import json
import random
from typing import List, Dict, Tuple
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnnotationConverter:
    """Conversor de anotaciones a formato spaCy"""

    def __init__(self, annotations_file: str, output_dir: str = None):
        """
        Inicializa el conversor

        Args:
            annotations_file: Path al archivo de anotaciones (JSONL de Doccano)
            output_dir: Directorio de salida
        """
        self.annotations_file = Path(annotations_file)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.annotations_file.parent / "spacy_format"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.train_data = []
        self.entity_stats = {}

    def load_doccano_jsonl(self) -> List[Dict]:
        """
        Carga anotaciones desde formato JSONL de Doccano

        Formato esperado:
        {
            "id": 123,
            "text": "texto de la oferta...",
            "label": [[start, end, "ENTITY_TYPE"], ...]
        }

        Returns:
            Lista de documentos anotados
        """
        logger.info(f"Cargando anotaciones: {self.annotations_file.name}")

        documents = []

        with open(self.annotations_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    documents.append(doc)

        logger.info(f"  Cargados {len(documents)} documentos anotados")

        return documents

    def load_labelstudio_json(self, json_file: str) -> List[Dict]:
        """
        Carga anotaciones desde formato JSON de Label Studio

        Formato esperado:
        [
            {
                "data": {"text": "..."},
                "annotations": [
                    {
                        "result": [
                            {
                                "value": {"start": 0, "end": 10, "text": "...", "labels": ["ENTITY"]},
                                "from_name": "label",
                                "to_name": "text",
                                "type": "labels"
                            }
                        ]
                    }
                ]
            }
        ]

        Returns:
            Lista de documentos anotados en formato unificado
        """
        logger.info(f"Cargando anotaciones de Label Studio: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []

        for item in data:
            text = item.get('data', {}).get('text', '')
            annotations = item.get('annotations', [])

            if not annotations:
                continue

            # Tomar primera anotación (o combinar si hay múltiples)
            result = annotations[0].get('result', [])

            labels = []
            for annotation in result:
                if annotation.get('type') == 'labels':
                    value = annotation.get('value', {})
                    start = value.get('start')
                    end = value.get('end')
                    label_list = value.get('labels', [])

                    if start is not None and end is not None and label_list:
                        label = label_list[0]
                        labels.append([start, end, label])

            documents.append({
                'id': item.get('id', len(documents)),
                'text': text,
                'label': labels
            })

        logger.info(f"  Cargados {len(documents)} documentos anotados")

        return documents

    def convert_to_spacy_format(self, documents: List[Dict]) -> List[Tuple]:
        """
        Convierte documentos anotados a formato spaCy

        spaCy formato:
        [
            (text, {"entities": [(start, end, label), ...]})
        ]

        Args:
            documents: Lista de documentos con anotaciones

        Returns:
            Lista de tuplas (text, annotations) para spaCy
        """
        logger.info("\n" + "=" * 70)
        logger.info("CONVERSIÓN A FORMATO SPACY")
        logger.info("=" * 70)

        train_data = []
        skipped = 0

        for doc in documents:
            text = doc.get('text', '')
            labels = doc.get('label', [])

            if not text or not labels:
                skipped += 1
                continue

            # Validar y limpiar anotaciones
            valid_labels = []
            for label in labels:
                if len(label) == 3:
                    start, end, entity_type = label

                    # Validar que start < end
                    if start >= end:
                        logger.warning(f"Anotación inválida (start >= end): {label}")
                        continue

                    # Validar que no se superpongan con otras
                    overlap = False
                    for existing_start, existing_end, _ in valid_labels:
                        if not (end <= existing_start or start >= existing_end):
                            logger.warning(f"Anotación se superpone: {label}")
                            overlap = True
                            break

                    if not overlap:
                        valid_labels.append((start, end, entity_type))

                        # Estadísticas
                        if entity_type not in self.entity_stats:
                            self.entity_stats[entity_type] = 0
                        self.entity_stats[entity_type] += 1

            if valid_labels:
                train_data.append((text, {"entities": valid_labels}))

        logger.info(f"\nDocumentos convertidos: {len(train_data)}")
        logger.info(f"Documentos omitidos: {skipped}")

        logger.info("\nEstadísticas de entidades:")
        for entity_type, count in sorted(self.entity_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {entity_type}: {count}")

        logger.info("=" * 70)

        return train_data

    def split_train_dev(self, train_data: List[Tuple], dev_ratio: float = 0.2):
        """
        Divide datos en train y dev sets

        Args:
            train_data: Lista de datos de entrenamiento
            dev_ratio: Proporción para dev set (default: 0.2)

        Returns:
            (train_set, dev_set)
        """
        logger.info(f"\nDividiendo datos: {100*(1-dev_ratio):.0f}% train, {100*dev_ratio:.0f}% dev")

        # Shuffle
        random.shuffle(train_data)

        # Split
        split_idx = int(len(train_data) * (1 - dev_ratio))
        train_set = train_data[:split_idx]
        dev_set = train_data[split_idx:]

        logger.info(f"  Train: {len(train_set)} ejemplos")
        logger.info(f"  Dev: {len(dev_set)} ejemplos")

        return train_set, dev_set

    def save_spacy_format(self, train_data: List[Tuple], output_name: str = "train_data.json"):
        """
        Guarda datos en formato JSON para spaCy

        Args:
            train_data: Lista de datos de entrenamiento
            output_name: Nombre del archivo de salida
        """
        output_path = self.output_dir / output_name

        # Convertir a formato serializable
        serializable_data = []
        for text, annotations in train_data:
            serializable_data.append({
                'text': text,
                'entities': annotations['entities']
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n[GUARDADO] {output_path}")
        logger.info(f"[EJEMPLOS] {len(train_data)}")
        logger.info(f"[TAMAÑO] {output_path.stat().st_size / 1024:.1f} KB")

        return output_path

    def create_label_scheme(self):
        """Crea archivo con esquema de etiquetas para referencia"""
        label_scheme = {
            "entity_types": list(self.entity_stats.keys()),
            "entity_counts": self.entity_stats,
            "description": {
                "YEARS": "Años de experiencia requeridos",
                "EDUCATION": "Nivel educativo o título",
                "SKILL": "Habilidad técnica o herramienta",
                "SOFT_SKILL": "Habilidad blanda",
                "LANGUAGE": "Idioma y nivel",
                "AREA": "Área de experiencia laboral"
            }
        }

        output_path = self.output_dir / "label_scheme.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(label_scheme, f, indent=2, ensure_ascii=False)

        logger.info(f"[GUARDADO] Esquema de etiquetas: {output_path}")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Convierte anotaciones a formato spaCy')

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path al archivo de anotaciones (JSONL de Doccano o JSON de Label Studio)'
    )

    parser.add_argument(
        '--format',
        choices=['doccano', 'labelstudio'],
        default='doccano',
        help='Formato del archivo de entrada (default: doccano)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Directorio de salida (default: mismo directorio que input)'
    )

    parser.add_argument(
        '--dev-ratio',
        type=float,
        default=0.2,
        help='Proporción para dev set (default: 0.2)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Seed para reproducibilidad (default: 42)'
    )

    args = parser.parse_args()

    # Fijar seed
    random.seed(args.seed)

    # Crear conversor
    converter = AnnotationConverter(
        annotations_file=args.input,
        output_dir=args.output_dir
    )

    # Cargar anotaciones según formato
    if args.format == 'doccano':
        documents = converter.load_doccano_jsonl()
    elif args.format == 'labelstudio':
        documents = converter.load_labelstudio_json(args.input)
    else:
        logger.error(f"Formato no soportado: {args.format}")
        return

    if not documents:
        logger.error("No se cargaron documentos anotados")
        return

    # Convertir a formato spaCy
    train_data = converter.convert_to_spacy_format(documents)

    if not train_data:
        logger.error("No se generaron datos de entrenamiento")
        return

    # Dividir en train/dev
    train_set, dev_set = converter.split_train_dev(train_data, dev_ratio=args.dev_ratio)

    # Guardar
    converter.save_spacy_format(train_set, output_name="train_data.json")
    converter.save_spacy_format(dev_set, output_name="dev_data.json")

    # Crear esquema de etiquetas
    converter.create_label_scheme()

    logger.info("\n" + "=" * 70)
    logger.info("¡CONVERSIÓN COMPLETADA!")
    logger.info("=" * 70)
    logger.info(f"\nPróximos pasos:")
    logger.info(f"1. Revisar train_data.json y dev_data.json")
    logger.info(f"2. Ejecutar script de entrenamiento: python train_ner_model.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
