# -*- coding: utf-8 -*-
"""
Prepare NER Dataset - Prepara dataset etiquetado para entrenamiento NER
========================================================================

Script para seleccionar y preparar ofertas representativas para
etiquetado manual y entrenamiento de modelo NER custom.
"""

import sys
from pathlib import Path
import pandas as pd
import json
import random
from datetime import datetime
import logging
from typing import List, Dict, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NERDatasetPreparer:
    """Preparador de dataset para entrenamiento NER"""

    def __init__(self, consolidated_csv_path: str, output_dir: str = None):
        """
        Inicializa el preparador

        Args:
            consolidated_csv_path: Path al CSV consolidado multi-fuente
            output_dir: Directorio de salida
        """
        self.csv_path = Path(consolidated_csv_path)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = project_root / "02.5_nlp_extraction" / "data" / "ner_training"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        self.selected_samples = None

    def load_data(self):
        """Carga el dataset consolidado"""
        logger.info(f"Cargando dataset: {self.csv_path.name}")

        self.df = pd.read_csv(self.csv_path, encoding='utf-8', low_memory=False)

        logger.info(f"  Total ofertas: {len(self.df):,}")
        logger.info(f"  Fuentes: {self.df['fuente'].nunique() if 'fuente' in self.df.columns else 'N/A'}")

        return self.df

    def analyze_distribution(self):
        """Analiza distribución de datos para sampling"""
        logger.info("\n" + "=" * 70)
        logger.info("ANÁLISIS DE DISTRIBUCIÓN")
        logger.info("=" * 70)

        # Por fuente
        if 'fuente' in self.df.columns:
            logger.info("\nOfertas por fuente:")
            fuente_counts = self.df['fuente'].value_counts()
            for fuente, count in fuente_counts.items():
                pct = (count / len(self.df)) * 100
                logger.info(f"  {fuente}: {count:,} ({pct:.1f}%)")

        # Cobertura de campos NLP
        nlp_fields = {
            'experiencia_min_anios': 'Experiencia',
            'nivel_educativo': 'Educación',
            'idioma_principal': 'Idiomas',
            'skills_tecnicas_list': 'Skills técnicas',
            'soft_skills_list': 'Soft skills'
        }

        logger.info("\nCobertura de campos NLP:")
        for col, label in nlp_fields.items():
            if col in self.df.columns:
                count = self.df[col].notna().sum()
                pct = (count / len(self.df)) * 100
                logger.info(f"  {label}: {count:,} ({pct:.1f}%)")

        # Distribución de longitud de texto
        if 'descripcion' in self.df.columns:
            self.df['text_length'] = self.df['descripcion'].fillna('').str.len()
            logger.info("\nDistribución longitud de texto:")
            logger.info(f"  Media: {self.df['text_length'].mean():.0f} chars")
            logger.info(f"  Mediana: {self.df['text_length'].median():.0f} chars")
            logger.info(f"  Min: {self.df['text_length'].min():.0f} chars")
            logger.info(f"  Max: {self.df['text_length'].max():.0f} chars")

        logger.info("=" * 70)

    def stratified_sample(self, n_samples: int = 500) -> pd.DataFrame:
        """
        Selecciona muestra estratificada representativa

        Args:
            n_samples: Número de muestras a seleccionar

        Returns:
            DataFrame con muestras seleccionadas
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"SELECCIÓN ESTRATIFICADA: {n_samples} MUESTRAS")
        logger.info("=" * 70)

        # Estrategia de sampling:
        # 1. Por fuente (proporcional)
        # 2. Con diversidad de campos NLP (priorizar ofertas con más campos)
        # 3. Con diversidad de longitud de texto

        samples_list = []

        if 'fuente' in self.df.columns:
            fuente_counts = self.df['fuente'].value_counts()

            for fuente in fuente_counts.index:
                # Calcular n proporcional pero con mínimo de 50 muestras por fuente
                fuente_df = self.df[self.df['fuente'] == fuente]
                fuente_pct = len(fuente_df) / len(self.df)
                fuente_n = max(50, int(n_samples * fuente_pct))

                # Si una fuente es muy pequeña, tomar todas
                if len(fuente_df) < fuente_n:
                    fuente_n = len(fuente_df)

                logger.info(f"\nFuente: {fuente}")
                logger.info(f"  Total disponible: {len(fuente_df):,}")
                logger.info(f"  A seleccionar: {fuente_n}")

                # Calcular "riqueza" de cada oferta (cuántos campos NLP tiene)
                fuente_df = fuente_df.copy()
                nlp_cols = ['experiencia_min_anios', 'nivel_educativo', 'idioma_principal',
                           'skills_tecnicas_list', 'soft_skills_list']
                fuente_df['nlp_richness'] = sum(fuente_df[col].notna().astype(int)
                                                for col in nlp_cols if col in fuente_df.columns)

                # Estratificar por riqueza: 40% alta (4-5 campos), 40% media (2-3), 20% baja (0-1)
                high_richness = fuente_df[fuente_df['nlp_richness'] >= 4]
                mid_richness = fuente_df[(fuente_df['nlp_richness'] >= 2) & (fuente_df['nlp_richness'] < 4)]
                low_richness = fuente_df[fuente_df['nlp_richness'] < 2]

                n_high = min(len(high_richness), int(fuente_n * 0.4))
                n_mid = min(len(mid_richness), int(fuente_n * 0.4))
                n_low = min(len(low_richness), fuente_n - n_high - n_mid)

                # Ajustar si alguna categoría no tiene suficientes
                if n_high < int(fuente_n * 0.4):
                    n_mid += int(fuente_n * 0.4) - n_high
                if n_mid > len(mid_richness):
                    n_low += n_mid - len(mid_richness)
                    n_mid = len(mid_richness)

                logger.info(f"  Alta riqueza (4-5 campos): {n_high}")
                logger.info(f"  Media riqueza (2-3 campos): {n_mid}")
                logger.info(f"  Baja riqueza (0-1 campos): {n_low}")

                # Samplear
                if n_high > 0 and len(high_richness) > 0:
                    samples_list.append(high_richness.sample(n=n_high, random_state=42))
                if n_mid > 0 and len(mid_richness) > 0:
                    samples_list.append(mid_richness.sample(n=n_mid, random_state=42))
                if n_low > 0 and len(low_richness) > 0:
                    samples_list.append(low_richness.sample(n=n_low, random_state=42))

        else:
            # Sin columna fuente, samplear aleatoriamente
            logger.info("No hay columna 'fuente', sampling aleatorio")
            samples_list.append(self.df.sample(n=n_samples, random_state=42))

        # Concatenar todas las muestras
        self.selected_samples = pd.concat(samples_list, ignore_index=True)

        # Limitar a n_samples si nos pasamos
        if len(self.selected_samples) > n_samples:
            self.selected_samples = self.selected_samples.sample(n=n_samples, random_state=42)

        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN SELECCIÓN")
        logger.info("=" * 70)
        logger.info(f"Total seleccionadas: {len(self.selected_samples)}")

        if 'fuente' in self.selected_samples.columns:
            logger.info("\nDistribución por fuente:")
            for fuente, count in self.selected_samples['fuente'].value_counts().items():
                logger.info(f"  {fuente}: {count}")

        logger.info("=" * 70)

        return self.selected_samples

    def export_for_annotation(self, df: pd.DataFrame, format: str = 'jsonl'):
        """
        Exporta muestras en formato para anotación

        Args:
            df: DataFrame con muestras
            format: Formato de export ('jsonl' o 'csv')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == 'jsonl':
            # Formato JSONL para anotación con herramientas como Doccano
            output_path = self.output_dir / f"ner_samples_for_annotation_{timestamp}.jsonl"

            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, row in df.iterrows():
                    # Priorizar columnas con descripción
                    text = ''
                    if 'descripcion' in row and pd.notna(row['descripcion']):
                        text = str(row['descripcion'])
                    elif 'description' in row and pd.notna(row['description']):
                        text = str(row['description'])

                    if text:
                        record = {
                            'id': idx,
                            'text': text,
                            'meta': {
                                'fuente': row.get('fuente', ''),
                                'titulo': row.get('titulo', row.get('title', '')),
                                'original_index': int(idx)
                            }
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')

            logger.info(f"\n[EXPORTADO] JSONL: {output_path}")
            logger.info(f"[FORMATO] Compatible con Doccano/Label Studio")

        elif format == 'csv':
            # Formato CSV simple
            output_path = self.output_dir / f"ner_samples_for_annotation_{timestamp}.csv"

            # Seleccionar columnas relevantes
            cols_to_export = ['fuente', 'titulo', 'descripcion']
            if 'title' in df.columns:
                cols_to_export.append('title')
            if 'description' in df.columns:
                cols_to_export.append('description')

            # Agregar campos NLP existentes como referencia
            nlp_cols = ['experiencia_min_anios', 'nivel_educativo', 'idioma_principal',
                       'skills_tecnicas_list', 'soft_skills_list']
            for col in nlp_cols:
                if col in df.columns:
                    cols_to_export.append(col)

            df_export = df[[col for col in cols_to_export if col in df.columns]].copy()
            df_export.to_csv(output_path, index=True, encoding='utf-8')

            logger.info(f"\n[EXPORTADO] CSV: {output_path}")

        logger.info(f"[MUESTRAS] {len(df)}")
        logger.info(f"[TAMAÑO] {output_path.stat().st_size / 1024:.1f} KB")

    def create_iob_template(self):
        """Crea template y ejemplo de formato IOB para anotadores"""

        iob_template = {
            "entity_types": [
                {
                    "label": "YEARS",
                    "description": "Años de experiencia requeridos",
                    "examples": ["3 años", "mínimo 5 años", "2 a 4 años"]
                },
                {
                    "label": "EDUCATION",
                    "description": "Nivel educativo requerido",
                    "examples": ["universitario completo", "secundario", "licenciatura en sistemas"]
                },
                {
                    "label": "SKILL",
                    "description": "Habilidad técnica o herramienta",
                    "examples": ["Python", "SQL", "React", "Django"]
                },
                {
                    "label": "SOFT_SKILL",
                    "description": "Habilidad blanda",
                    "examples": ["trabajo en equipo", "comunicación efectiva", "liderazgo"]
                },
                {
                    "label": "LANGUAGE",
                    "description": "Idioma y nivel",
                    "examples": ["inglés avanzado", "portugués intermedio"]
                },
                {
                    "label": "AREA",
                    "description": "Área de experiencia",
                    "examples": ["desarrollo backend", "administración de redes", "análisis de datos"]
                }
            ],
            "iob_format_example": {
                "text": "Buscamos desarrollador Python con 3 años de experiencia en Django",
                "tokens": ["Buscamos", "desarrollador", "Python", "con", "3", "años", "de", "experiencia", "en", "Django"],
                "labels": ["O", "O", "B-SKILL", "O", "B-YEARS", "I-YEARS", "O", "O", "O", "B-SKILL"]
            },
            "annotation_rules": [
                "B- marca el inicio de una entidad",
                "I- marca la continuación de una entidad",
                "O marca tokens que no son parte de ninguna entidad",
                "Cada token debe tener exactamente una etiqueta",
                "Las entidades multi-token usan B- para la primera palabra e I- para las siguientes"
            ]
        }

        template_path = self.output_dir / "iob_annotation_template.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(iob_template, f, indent=2, ensure_ascii=False)

        logger.info(f"\n[CREADO] Template IOB: {template_path}")

        # Crear también guía de anotación en markdown
        guide_md = """# Guía de Anotación NER para Ofertas Laborales

## Tipos de Entidades

### 1. YEARS - Años de Experiencia
Marca los años de experiencia requeridos en la oferta.

**Ejemplos:**
- "Requerimos **3 años** de experiencia"
- "Mínimo **5 años** en el puesto"
- "Entre **2 a 4 años** trabajando con..."

### 2. EDUCATION - Educación
Marca el nivel educativo o título requerido.

**Ejemplos:**
- "**Universitario completo**"
- "**Licenciatura en Sistemas**"
- "Título **terciario** o universitario"

### 3. SKILL - Habilidad Técnica
Marca tecnologías, herramientas, lenguajes de programación, frameworks.

**Ejemplos:**
- "Experiencia con **Python** y **Django**"
- "Conocimientos de **SQL** y **PostgreSQL**"
- "Manejo de **Docker** y **Kubernetes**"

### 4. SOFT_SKILL - Habilidad Blanda
Marca competencias interpersonales y soft skills.

**Ejemplos:**
- "**Trabajo en equipo**"
- "Excelente **comunicación verbal**"
- "Capacidad de **liderazgo**"

### 5. LANGUAGE - Idioma
Marca idiomas requeridos y su nivel.

**Ejemplos:**
- "**Inglés avanzado**"
- "**Portugués intermedio**"
- "**Bilingüe inglés-español**"

### 6. AREA - Área de Experiencia
Marca áreas o dominios de experiencia laboral.

**Ejemplos:**
- "Experiencia en **desarrollo backend**"
- "Conocimiento de **administración de redes**"
- "Background en **machine learning**"

## Formato IOB

Cada palabra (token) debe etiquetarse con:
- **B-ENTITY**: Comienzo de entidad
- **I-ENTITY**: Continuación de entidad
- **O**: Fuera de entidad (Other)

### Ejemplo Completo

**Texto:**
```
Buscamos desarrollador Python con 3 años de experiencia en Django
```

**Anotación:**
```
Buscamos       O
desarrollador  O
Python         B-SKILL
con            O
3              B-YEARS
años           I-YEARS
de             O
experiencia    O
en             O
Django         B-SKILL
```

## Reglas de Anotación

1. **Multi-palabra**: Si una entidad tiene múltiples palabras, usa B- para la primera e I- para las siguientes
   - "inglés avanzado" → inglés/B-LANGUAGE avanzado/I-LANGUAGE

2. **Contexto**: Incluye modificadores relevantes en la entidad
   - "mínimo 3 años" → mínimo/B-YEARS 3/I-YEARS años/I-YEARS

3. **Listas**: Cada item de una lista es una entidad separada
   - "Python, Java y C++" → Python/B-SKILL ,/O Java/B-SKILL y/O C++/B-SKILL

4. **Ambigüedad**: Si no estás seguro, marca como O

5. **Consistencia**: Mantén el mismo criterio para casos similares

## Herramientas Recomendadas

- **Doccano**: https://github.com/doccano/doccano
- **Label Studio**: https://labelstud.io/
- **Prodigy**: https://prodi.gy/ (pago)

## Proceso de Trabajo

1. Cargar archivo JSONL en herramienta de anotación
2. Anotar entidades según las reglas
3. Revisar consistencia
4. Exportar en formato IOB
5. Validar con script de validación (próximo)
"""

        guide_path = self.output_dir / "ANNOTATION_GUIDE.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_md)

        logger.info(f"[CREADO] Guía de anotación: {guide_path}")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Prepara dataset para entrenamiento NER')

    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path al CSV consolidado (default: autodetectar más reciente)'
    )

    parser.add_argument(
        '--n-samples',
        type=int,
        default=500,
        help='Número de muestras a seleccionar (default: 500)'
    )

    parser.add_argument(
        '--format',
        choices=['jsonl', 'csv', 'both'],
        default='both',
        help='Formato de export (default: both)'
    )

    args = parser.parse_args()

    # Detectar CSV consolidado más reciente si no se especificó
    if args.input is None:
        project_root = Path(__file__).parent.parent.parent
        processed_dir = project_root / "02.5_nlp_extraction" / "data" / "processed"
        pattern = "all_sources_nlp_*.csv"
        files = list(processed_dir.glob(pattern))

        if files:
            args.input = max(files, key=lambda p: p.stat().st_mtime)
            logger.info(f"CSV consolidado autodetectado: {args.input.name}")
        else:
            logger.error("No se encontró CSV consolidado")
            return

    # Crear preparador
    preparer = NERDatasetPreparer(consolidated_csv_path=args.input)

    # Cargar datos
    preparer.load_data()

    # Analizar distribución
    preparer.analyze_distribution()

    # Seleccionar muestra estratificada
    samples = preparer.stratified_sample(n_samples=args.n_samples)

    # Exportar
    if args.format in ['jsonl', 'both']:
        preparer.export_for_annotation(samples, format='jsonl')

    if args.format in ['csv', 'both']:
        preparer.export_for_annotation(samples, format='csv')

    # Crear templates y guías
    preparer.create_iob_template()

    logger.info("\n" + "=" * 70)
    logger.info("¡PREPARACIÓN COMPLETADA!")
    logger.info("=" * 70)
    logger.info(f"\nPróximos pasos:")
    logger.info(f"1. Cargar JSONL en herramienta de anotación (Doccano/Label Studio)")
    logger.info(f"2. Anotar entidades siguiendo ANNOTATION_GUIDE.md")
    logger.info(f"3. Exportar anotaciones en formato IOB")
    logger.info(f"4. Entrenar modelo NER con spaCy")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
