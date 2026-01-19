# -*- coding: utf-8 -*-
"""
Base NER Extractor - Extractor base usando modelo NER entrenado
================================================================

Clase base para extracción de información usando modelo NER custom
entrenado con spaCy.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import spacy
from abc import ABC, abstractmethod
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseNERExtractor(ABC):
    """Clase base para extractores NER"""

    def __init__(self, model_path: str = None):
        """
        Inicializa el extractor NER

        Args:
            model_path: Path al modelo NER entrenado (None = usar latest)
        """
        self.model_path = self._resolve_model_path(model_path)
        self.nlp = None
        self.entity_types = []

        # Cargar modelo
        self._load_model()

    def _resolve_model_path(self, model_path: str = None) -> Path:
        """
        Resuelve el path al modelo NER

        Args:
            model_path: Path especificado (None = buscar latest)

        Returns:
            Path al modelo
        """
        if model_path:
            return Path(model_path)

        # Buscar latest model
        project_root = Path(__file__).parent.parent.parent.parent
        models_dir = project_root / "02.5_nlp_extraction" / "models" / "ner_model"

        # Intentar symlink 'latest'
        latest_link = models_dir / "latest"
        if latest_link.exists():
            return latest_link

        # Buscar último modelo por timestamp
        model_dirs = [d for d in models_dir.glob("model_*") if d.is_dir()]
        if model_dirs:
            return max(model_dirs, key=lambda p: p.name)

        raise FileNotFoundError(f"No se encontró modelo NER en {models_dir}")

    def _load_model(self):
        """Carga el modelo NER de spaCy"""
        logger.info(f"Cargando modelo NER: {self.model_path.name}")

        try:
            self.nlp = spacy.load(self.model_path)

            # Verificar que tiene componente NER
            if "ner" not in self.nlp.pipe_names:
                raise ValueError("El modelo no tiene componente NER")

            # Obtener tipos de entidades
            ner = self.nlp.get_pipe("ner")
            self.entity_types = list(ner.labels)

            logger.info(f"  ✓ Modelo cargado con {len(self.entity_types)} tipos de entidades")
            logger.info(f"  Entidades: {', '.join(self.entity_types)}")

        except Exception as e:
            logger.error(f"Error cargando modelo NER: {e}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extrae entidades del texto usando NER

        Args:
            text: Texto a analizar

        Returns:
            Dict con entidades agrupadas por tipo
        """
        if not text or pd.isna(text):
            return {}

        # Procesar con NER
        doc = self.nlp(str(text))

        # Agrupar entidades por tipo
        entities_by_type = {entity_type: [] for entity_type in self.entity_types}

        for ent in doc.ents:
            entities_by_type[ent.label_].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'label': ent.label_
            })

        return entities_by_type

    def process_years_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo YEARS para extraer años de experiencia

        Args:
            entities: Lista de entidades YEARS

        Returns:
            Dict con experiencia_min_anios, experiencia_max_anios
        """
        if not entities:
            return {}

        # Extraer números de las entidades
        years = []
        for ent in entities:
            text = ent['text'].lower()

            # Buscar números
            import re
            numbers = re.findall(r'\d+', text)
            years.extend([int(n) for n in numbers])

        if not years:
            return {}

        # Si hay un solo número, es mínimo
        if len(years) == 1:
            return {
                'experiencia_min_anios': years[0],
                'experiencia_max_anios': None
            }

        # Si hay múltiples, tomar min y max
        return {
            'experiencia_min_anios': min(years),
            'experiencia_max_anios': max(years)
        }

    def process_education_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo EDUCATION

        Args:
            entities: Lista de entidades EDUCATION

        Returns:
            Dict con nivel_educativo, titulo_requerido
        """
        if not entities:
            return {}

        # Tomar primera entidad (más prominente)
        first_edu = entities[0]['text'].lower()

        # Mapear a niveles
        nivel = None
        if any(word in first_edu for word in ['posgrado', 'maestr', 'master', 'doctorado', 'phd']):
            nivel = 'posgrado'
        elif any(word in first_edu for word in ['universitar', 'licenciatura', 'ingenier', 'graduado']):
            nivel = 'universitario'
        elif any(word in first_edu for word in ['tercia', 'tecnic']):
            nivel = 'terciario'
        elif any(word in first_edu for word in ['secundar', 'bachiller']):
            nivel = 'secundario'

        result = {}
        if nivel:
            result['nivel_educativo'] = nivel

        # Tomar todos los títulos mencionados
        titulos = [ent['text'] for ent in entities]
        if titulos:
            result['titulo_requerido'] = '; '.join(titulos[:3])  # Máximo 3

        return result

    def process_skill_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo SKILL (técnicas)

        Args:
            entities: Lista de entidades SKILL

        Returns:
            Dict con skills_tecnicas_list
        """
        if not entities:
            return {}

        # Extraer textos únicos
        skills = list(set(ent['text'] for ent in entities))

        return {
            'skills_tecnicas_list': ', '.join(skills),
            'skills_tecnicas_count': len(skills)
        }

    def process_soft_skill_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo SOFT_SKILL

        Args:
            entities: Lista de entidades SOFT_SKILL

        Returns:
            Dict con soft_skills_list
        """
        if not entities:
            return {}

        # Extraer textos únicos
        soft_skills = list(set(ent['text'] for ent in entities))

        return {
            'soft_skills_list': ', '.join(soft_skills),
            'soft_skills_count': len(soft_skills)
        }

    def process_language_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo LANGUAGE

        Args:
            entities: Lista de entidades LANGUAGE

        Returns:
            Dict con idioma_principal, nivel_idioma_principal, idiomas_list
        """
        if not entities:
            return {}

        result = {}

        # Tomar primer idioma como principal
        if entities:
            first_lang = entities[0]['text'].lower()

            # Extraer idioma
            idioma = None
            if 'ingl' in first_lang:
                idioma = 'ingles'
            elif 'portugu' in first_lang:
                idioma = 'portugues'
            elif 'alem' in first_lang:
                idioma = 'aleman'
            elif 'franc' in first_lang:
                idioma = 'frances'
            elif 'italian' in first_lang:
                idioma = 'italiano'

            if idioma:
                result['idioma_principal'] = idioma

            # Extraer nivel
            nivel = None
            if any(word in first_lang for word in ['avanzado', 'advanced', 'fluent', 'fluido']):
                nivel = 'avanzado'
            elif any(word in first_lang for word in ['intermedio', 'intermediate']):
                nivel = 'intermedio'
            elif any(word in first_lang for word in ['basico', 'basic', 'elementary']):
                nivel = 'basico'
            elif any(word in first_lang for word in ['nativo', 'native', 'bilingu']):
                nivel = 'nativo'

            if nivel:
                result['nivel_idioma_principal'] = nivel

        # Todos los idiomas
        idiomas = [ent['text'] for ent in entities]
        if idiomas:
            result['idiomas_list'] = '; '.join(idiomas)

        return result

    def process_area_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Procesa entidades de tipo AREA

        Args:
            entities: Lista de entidades AREA

        Returns:
            Dict con area_experiencia
        """
        if not entities:
            return {}

        # Tomar primera área mencionada
        return {
            'area_experiencia': entities[0]['text']
        }

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae toda la información estructurada del texto

        Args:
            text: Texto de la oferta

        Returns:
            Dict con campos extraídos
        """
        # Extraer entidades
        entities_by_type = self.extract_entities(text)

        # Procesar cada tipo de entidad
        result = {}

        # YEARS → experiencia
        if 'YEARS' in entities_by_type:
            result.update(self.process_years_entities(entities_by_type['YEARS']))

        # EDUCATION → educación
        if 'EDUCATION' in entities_by_type:
            result.update(self.process_education_entities(entities_by_type['EDUCATION']))

        # SKILL → skills técnicas
        if 'SKILL' in entities_by_type:
            result.update(self.process_skill_entities(entities_by_type['SKILL']))

        # SOFT_SKILL → soft skills
        if 'SOFT_SKILL' in entities_by_type:
            result.update(self.process_soft_skill_entities(entities_by_type['SOFT_SKILL']))

        # LANGUAGE → idiomas
        if 'LANGUAGE' in entities_by_type:
            result.update(self.process_language_entities(entities_by_type['LANGUAGE']))

        # AREA → área de experiencia
        if 'AREA' in entities_by_type:
            result.update(self.process_area_entities(entities_by_type['AREA']))

        # Calcular confidence score basado en cuántas entidades se detectaron
        total_entity_types = len([k for k in entities_by_type if entities_by_type[k]])
        confidence = min(1.0, total_entity_types / 6.0)  # 6 tipos de entidades
        result['ner_confidence_score'] = round(confidence, 3)

        return result

    def process_dataframe(
        self,
        df: pd.DataFrame,
        descripcion_col: str = 'descripcion',
        titulo_col: str = None
    ) -> pd.DataFrame:
        """
        Procesa un DataFrame completo

        Args:
            df: DataFrame con ofertas
            descripcion_col: Nombre de columna con descripción
            titulo_col: Nombre de columna con título (opcional)

        Returns:
            DataFrame con campos NER agregados
        """
        logger.info(f"\nProcesando {len(df):,} ofertas con NER...")

        results = []

        for idx, row in df.iterrows():
            if idx % 100 == 0 and idx > 0:
                logger.info(f"  Procesadas {idx:,}/{len(df):,} ofertas...")

            # Combinar título y descripción
            text = ''
            if titulo_col and titulo_col in df.columns and pd.notna(row.get(titulo_col)):
                text = str(row[titulo_col]) + '\n\n'

            if descripcion_col in df.columns and pd.notna(row.get(descripcion_col)):
                text += str(row[descripcion_col])

            # Extraer con NER
            extracted = self.extract_from_text(text) if text else {}
            results.append(extracted)

        # Convertir a DataFrame
        df_results = pd.DataFrame(results)

        # Agregar timestamp
        df_results['ner_processed_at'] = datetime.now().isoformat()
        df_results['ner_model'] = self.model_path.name

        # Concatenar con original
        df_enriched = pd.concat([df, df_results], axis=1)

        logger.info(f"✓ Procesamiento NER completado\n")

        return df_enriched

    def get_extraction_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula estadísticas de extracción NER

        Args:
            df: DataFrame procesado

        Returns:
            Dict con estadísticas
        """
        stats = {
            'total_ofertas': len(df),
            'model_path': str(self.model_path)
        }

        # Estadísticas por campo
        ner_fields = [
            'experiencia_min_anios',
            'nivel_educativo',
            'idioma_principal',
            'skills_tecnicas_list',
            'soft_skills_list',
            'area_experiencia',
            'ner_confidence_score'
        ]

        for field in ner_fields:
            if field in df.columns:
                count = df[field].notna().sum()
                pct = (count / len(df)) * 100
                stats[f'{field}_count'] = int(count)
                stats[f'{field}_coverage_pct'] = round(pct, 1)

        # Confidence promedio
        if 'ner_confidence_score' in df.columns:
            stats['avg_confidence'] = round(df['ner_confidence_score'].mean(), 3)

        return stats


def main():
    """Función de prueba"""
    # Texto de ejemplo
    test_text = """
    Estamos buscando un desarrollador Python senior con mínimo 5 años de experiencia
    en desarrollo backend. Requisitos: título universitario en Sistemas o Ingeniería,
    conocimientos avanzados de Django, Flask, PostgreSQL, Docker y AWS.

    Se requiere inglés avanzado y excelentes habilidades de trabajo en equipo.
    La persona debe tener experiencia previa en desarrollo de APIs REST y microservicios.
    """

    logger.info("=" * 70)
    logger.info("PRUEBA BASE NER EXTRACTOR")
    logger.info("=" * 70)

    try:
        extractor = BaseNERExtractor()

        result = extractor.extract_from_text(test_text)

        logger.info("\nCampos extraídos:")
        for key, value in result.items():
            logger.info(f"  {key}: {value}")

    except FileNotFoundError as e:
        logger.error(f"\n{e}")
        logger.info("\nPara usar este extractor, primero debes:")
        logger.info("1. Anotar 500 ofertas siguiendo ANNOTATION_GUIDE.md")
        logger.info("2. Convertir anotaciones: python convert_annotations_to_spacy.py")
        logger.info("3. Entrenar modelo: python train_ner_model.py")

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
