# -*- coding: utf-8 -*-
"""
Auto-annotate with Regex - Pre-anota usando resultados de Fase 1
================================================================

Convierte los resultados de extracción Regex (Fase 1) en anotaciones
NER para reducir trabajo manual de anotación.
"""

import sys
from pathlib import Path
import pandas as pd
import json
import re
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RegexToNERAnnotator:
    """Convierte resultados Regex a anotaciones NER"""

    def __init__(self, phase1_csv: str, samples_jsonl: str, output_jsonl: str):
        """
        Inicializa el anotador automático

        Args:
            phase1_csv: CSV con resultados de Fase 1
            samples_jsonl: JSONL con las 500 muestras seleccionadas
            output_jsonl: Archivo de salida con pre-anotaciones
        """
        self.phase1_csv = Path(phase1_csv)
        self.samples_jsonl = Path(samples_jsonl)
        self.output_jsonl = Path(output_jsonl)

    def load_data(self):
        """Carga los datos"""
        logger.info(f"Cargando Fase 1: {self.phase1_csv.name}")
        self.df_phase1 = pd.read_csv(self.phase1_csv, encoding='utf-8', low_memory=False)

        logger.info(f"Cargando muestras: {self.samples_jsonl.name}")
        self.samples = []
        with open(self.samples_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

        logger.info(f"  Fase 1: {len(self.df_phase1):,} ofertas")
        logger.info(f"  Muestras: {len(self.samples)} ofertas")

    def find_entity_positions(self, text: str, search_text: str) -> List[Tuple[int, int]]:
        """
        Encuentra todas las posiciones de un texto en el documento

        Args:
            text: Texto completo
            search_text: Texto a buscar

        Returns:
            Lista de tuplas (start, end)
        """
        if not search_text or pd.isna(search_text):
            return []

        positions = []
        search_lower = str(search_text).lower()
        text_lower = text.lower()

        # Buscar todas las ocurrencias
        start = 0
        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(search_text)))
            start = pos + 1

        return positions

    def extract_skills_positions(self, text: str, skills_list: str) -> List[Tuple[int, int, str]]:
        """
        Extrae posiciones de skills técnicas

        Args:
            text: Texto completo
            skills_list: Lista de skills separadas por coma

        Returns:
            Lista de tuplas (start, end, label)
        """
        if not skills_list or pd.isna(skills_list):
            return []

        positions = []
        skills = [s.strip() for s in str(skills_list).split(',')]

        for skill in skills:
            if skill:
                for start, end in self.find_entity_positions(text, skill):
                    positions.append((start, end, 'SKILL'))

        return positions

    def extract_soft_skills_positions(self, text: str, soft_skills_list: str) -> List[Tuple[int, int, str]]:
        """Extrae posiciones de soft skills"""
        if not soft_skills_list or pd.isna(soft_skills_list):
            return []

        positions = []
        skills = [s.strip() for s in str(soft_skills_list).split(',')]

        for skill in skills:
            if skill:
                for start, end in self.find_entity_positions(text, skill):
                    positions.append((start, end, 'SOFT_SKILL'))

        return positions

    def extract_years_positions(self, text: str, min_years: int, max_years: int = None) -> List[Tuple[int, int, str]]:
        """
        Extrae posiciones de años de experiencia

        Args:
            text: Texto completo
            min_years: Años mínimos extraídos por Fase 1
            max_years: Años máximos (si hay rango)

        Returns:
            Lista de tuplas (start, end, label)
        """
        if pd.isna(min_years):
            return []

        positions = []
        text_lower = text.lower()

        # Patrones comunes para años
        patterns = [
            rf'{min_years}\+?\s*años?',
            rf'{min_years}\s*años?',
            rf'mínimo\s+{min_years}\s*años?',
            rf'{min_years}\s*a\s*{max_years}\s*años?' if max_years else None
        ]

        for pattern in patterns:
            if pattern:
                for match in re.finditer(pattern, text_lower):
                    positions.append((match.start(), match.end(), 'YEARS'))

        return positions

    def extract_education_positions(self, text: str, nivel: str, titulo: str = None) -> List[Tuple[int, int, str]]:
        """Extrae posiciones de educación"""
        if not nivel or pd.isna(nivel):
            return []

        positions = []

        # Buscar nivel educativo
        nivel_patterns = {
            'universitario': [r'universitario\s+completo', r'título\s+universitario', r'licenciatura', r'ingeniería'],
            'terciario': [r'terciario', r'técnico\s+superior'],
            'secundario': [r'secundario\s+completo', r'bachiller'],
            'posgrado': [r'posgrado', r'maestría', r'master', r'doctorado']
        }

        if nivel in nivel_patterns:
            for pattern in nivel_patterns[nivel]:
                for match in re.finditer(pattern, text.lower()):
                    positions.append((match.start(), match.end(), 'EDUCATION'))

        # Buscar título específico
        if titulo and not pd.isna(titulo):
            titulos = [t.strip() for t in str(titulo).split(';')]
            for tit in titulos[:2]:  # Máximo 2 títulos
                if tit:
                    for start, end in self.find_entity_positions(text, tit):
                        positions.append((start, end, 'EDUCATION'))

        return positions

    def extract_language_positions(self, text: str, idioma: str, nivel: str = None) -> List[Tuple[int, int, str]]:
        """Extrae posiciones de idiomas"""
        if not idioma or pd.isna(idioma):
            return []

        positions = []

        # Buscar idioma + nivel
        if nivel and not pd.isna(nivel):
            search_texts = [
                f"{idioma} {nivel}",
                f"{nivel} {idioma}",
                idioma
            ]
        else:
            search_texts = [idioma]

        for search in search_texts:
            for start, end in self.find_entity_positions(text, search):
                positions.append((start, end, 'LANGUAGE'))
                break  # Solo la primera ocurrencia

        return positions

    def merge_overlapping_entities(self, entities: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        """
        Resuelve solapamientos de entidades (toma la más larga)

        Args:
            entities: Lista de (start, end, label)

        Returns:
            Lista sin solapamientos
        """
        if not entities:
            return []

        # Ordenar por posición
        sorted_entities = sorted(entities, key=lambda x: (x[0], -(x[1] - x[0])))

        non_overlapping = []
        for entity in sorted_entities:
            start, end, label = entity

            # Verificar si solapa con alguna existente
            overlaps = False
            for existing_start, existing_end, _ in non_overlapping:
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break

            if not overlaps:
                non_overlapping.append(entity)

        return sorted(non_overlapping, key=lambda x: x[0])

    def annotate_sample(self, sample: Dict, phase1_row: pd.Series) -> Dict:
        """
        Anota una muestra usando datos de Fase 1

        Args:
            sample: Muestra JSONL original
            phase1_row: Fila correspondiente de Fase 1

        Returns:
            Muestra con anotaciones
        """
        text = sample['text']
        entities = []

        # YEARS - Experiencia
        if 'experiencia_min_anios' in phase1_row.index:
            min_years = phase1_row['experiencia_min_anios']
            max_years = phase1_row.get('experiencia_max_anios')
            entities.extend(self.extract_years_positions(text, min_years, max_years))

        # EDUCATION - Educación
        if 'nivel_educativo' in phase1_row.index:
            nivel = phase1_row['nivel_educativo']
            titulo = phase1_row.get('titulo_requerido')
            entities.extend(self.extract_education_positions(text, nivel, titulo))

        # SKILL - Skills técnicas
        if 'skills_tecnicas_list' in phase1_row.index:
            skills = phase1_row['skills_tecnicas_list']
            entities.extend(self.extract_skills_positions(text, skills))

        # SOFT_SKILL - Soft skills
        if 'soft_skills_list' in phase1_row.index:
            soft_skills = phase1_row['soft_skills_list']
            entities.extend(self.extract_soft_skills_positions(text, soft_skills))

        # LANGUAGE - Idiomas
        if 'idioma_principal' in phase1_row.index:
            idioma = phase1_row['idioma_principal']
            nivel = phase1_row.get('nivel_idioma_principal')
            entities.extend(self.extract_language_positions(text, idioma, nivel))

        # Resolver solapamientos
        entities = self.merge_overlapping_entities(entities)

        # Formatear para Doccano
        annotated = {
            'id': sample['id'],
            'text': text,
            'label': [[start, end, label] for start, end, label in entities],
            'meta': sample.get('meta', {})
        }

        # Agregar info de pre-anotación
        annotated['meta']['pre_annotated'] = True
        annotated['meta']['entities_count'] = len(entities)

        return annotated

    def auto_annotate_all(self):
        """Pre-anota todas las muestras"""
        logger.info("\n" + "=" * 70)
        logger.info("PRE-ANOTACIÓN AUTOMÁTICA CON FASE 1")
        logger.info("=" * 70)

        annotated_samples = []
        stats = {
            'total': len(self.samples),
            'annotated': 0,
            'empty': 0,
            'entities_total': 0
        }

        for sample in self.samples:
            sample_id = sample['id']

            # Buscar fila correspondiente en Fase 1
            if sample_id < len(self.df_phase1):
                phase1_row = self.df_phase1.iloc[sample_id]

                # Anotar
                annotated = self.annotate_sample(sample, phase1_row)

                if annotated['label']:
                    stats['annotated'] += 1
                    stats['entities_total'] += len(annotated['label'])
                else:
                    stats['empty'] += 1

                annotated_samples.append(annotated)

        # Guardar
        with open(self.output_jsonl, 'w', encoding='utf-8') as f:
            for sample in annotated_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info(f"\n✓ Pre-anotadas: {stats['annotated']}/{stats['total']} muestras")
        logger.info(f"  Sin anotaciones: {stats['empty']}")
        logger.info(f"  Total entidades: {stats['entities_total']}")
        logger.info(f"  Promedio por muestra: {stats['entities_total']/stats['annotated']:.1f}")
        logger.info(f"\n[GUARDADO] {self.output_jsonl}")
        logger.info("=" * 70)

        logger.info("\n📝 PRÓXIMOS PASOS:")
        logger.info("1. Cargar archivo pre-anotado en Doccano/Label Studio")
        logger.info("2. Revisar y corregir anotaciones (mucho más rápido que desde cero)")
        logger.info("3. Exportar anotaciones corregidas")
        logger.info("4. Continuar con entrenamiento NER")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Pre-anota muestras usando Fase 1')

    parser.add_argument(
        '--phase1-csv',
        type=str,
        default=r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_nlp_20251025_141134.csv',
        help='Path al CSV de Fase 1'
    )

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
        help='Path de salida (default: samples_pre_annotated.jsonl)'
    )

    args = parser.parse_args()

    if args.output_jsonl is None:
        samples_path = Path(args.samples_jsonl)
        args.output_jsonl = samples_path.parent / f"{samples_path.stem}_pre_annotated.jsonl"

    # Crear anotador
    annotator = RegexToNERAnnotator(
        phase1_csv=args.phase1_csv,
        samples_jsonl=args.samples_jsonl,
        output_jsonl=args.output_jsonl
    )

    # Cargar datos
    annotator.load_data()

    # Pre-anotar
    annotator.auto_annotate_all()

    logger.info("\n¡Pre-anotación completada! 🎉")
    logger.info(f"\nTiempo de revisión estimado: 2-4 horas (vs 8-16 horas desde cero)")


if __name__ == "__main__":
    main()
