# -*- coding: utf-8 -*-
"""
Clean Hybrid Results - Limpia y consolida resultados de extracción híbrida
===========================================================================

Problemas a resolver:
1. Soft skills en formato lista Python ['skill1', 'skill2']
2. 103 columnas (muchas redundantes)
3. Columnas duplicadas (regex, hybrid, final)
4. Campos intermedios innecesarios
"""

import sys
from pathlib import Path
import pandas as pd
import ast
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HybridDataCleaner:
    """Limpiador de datos híbridos"""

    def __init__(self, input_csv: str, output_csv: str = None):
        self.input_csv = Path(input_csv)

        if output_csv:
            self.output_csv = Path(output_csv)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.output_csv = self.input_csv.parent / f"all_sources_clean_{timestamp}.csv"

    def parse_python_list(self, value):
        """
        Convierte strings de listas Python a strings normales

        Ejemplos:
        "['comunicación', 'liderazgo']" -> "comunicación, liderazgo"
        "trabajo en equipo" -> "trabajo en equipo"
        """
        if pd.isna(value):
            return None

        value_str = str(value).strip()

        # Si es una lista Python (empieza con [)
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                # Intentar parsear como lista Python
                parsed = ast.literal_eval(value_str)
                if isinstance(parsed, list):
                    # Filtrar valores None/vacíos y unir
                    cleaned = [str(item).strip() for item in parsed if item and str(item).strip()]
                    return ', '.join(cleaned) if cleaned else None
            except:
                # Si falla, intentar limpieza manual
                # Remover [ ] y comillas
                cleaned = value_str.strip('[]').replace("'", "").replace('"', '')
                return cleaned if cleaned else None

        # Si ya es un string normal, devolver como está
        return value_str if value_str else None

    def clean_soft_skills(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia columna de soft skills"""
        logger.info("\n1. Limpiando soft skills...")

        # Aplicar limpieza
        df['soft_skills_clean'] = df['final_soft_skills_list'].apply(self.parse_python_list)

        # Estadísticas
        before = df['final_soft_skills_list'].notna().sum()
        after = df['soft_skills_clean'].notna().sum()

        logger.info(f"   Antes: {before:,} ofertas con soft skills")
        logger.info(f"   Después: {after:,} ofertas con soft skills")

        # Mostrar ejemplos
        logger.info("\n   Ejemplos de limpieza:")
        samples = df[df['soft_skills_clean'].notna()][['final_soft_skills_list', 'soft_skills_clean']].head(5)
        for idx, row in samples.iterrows():
            original = str(row['final_soft_skills_list'])[:60]
            cleaned = str(row['soft_skills_clean'])[:60]
            logger.info(f"     Antes: {original}")
            logger.info(f"     Después: {cleaned}\n")

        return df

    def clean_skills_tecnicas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia columna de skills técnicas"""
        logger.info("\n2. Limpiando skills técnicas...")

        # skills_tecnicas_list puede tener el mismo problema
        if 'skills_tecnicas_list' in df.columns:
            df['skills_tecnicas_clean'] = df['skills_tecnicas_list'].apply(self.parse_python_list)

            before = df['skills_tecnicas_list'].notna().sum()
            after = df['skills_tecnicas_clean'].notna().sum()

            logger.info(f"   Antes: {before:,} ofertas con skills técnicas")
            logger.info(f"   Después: {after:,} ofertas con skills técnicas")

        return df

    def select_final_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Selecciona solo las columnas finales necesarias"""
        logger.info("\n3. Seleccionando columnas finales...")

        # Columnas base esenciales
        base_cols = [
            'id_aviso', 'fecha_publicacion', 'fuente', 'titulo', 'descripcion',
            'empresa', 'ubicacion', 'tipo_contrato', 'modalidad', 'salario'
        ]

        # Columnas de extracción NLP (limpias)
        nlp_cols = [
            # Experiencia
            'experiencia_min_anios',
            'experiencia_max_anios',
            'experiencia_areas_list',

            # Educación
            'final_nivel_educativo',  # Usa el final (híbrido)
            'estado_educativo',
            'titulo_requerido',

            # Skills
            'soft_skills_clean',  # Nueva columna limpia
            'skills_tecnicas_clean',  # Nueva columna limpia

            # Idiomas
            'idioma_principal',
            'nivel_idioma_principal',
            'idioma_secundario',

            # Otros
            'area_experiencia',
            'certificaciones_list',
            'beneficios_list',
            'responsabilidades_list',
            'sector_industria'
        ]

        # Metadata del proceso
        meta_cols = [
            'hybrid_method',  # regex_only o regex+llm
            'hybrid_llm_called'  # True/False
        ]

        # Seleccionar solo columnas que existan
        all_cols = base_cols + nlp_cols + meta_cols
        existing_cols = [col for col in all_cols if col in df.columns]

        df_clean = df[existing_cols].copy()

        logger.info(f"   Columnas originales: {len(df.columns)}")
        logger.info(f"   Columnas finales: {len(df_clean.columns)}")
        logger.info(f"   Reducción: {len(df.columns) - len(df_clean.columns)} columnas eliminadas")

        return df_clean

    def normalize_education(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza valores de educación"""
        logger.info("\n4. Normalizando educación...")

        if 'final_nivel_educativo' in df.columns:
            # Mapeo de variantes a valores estándar
            education_mapping = {
                'secundario': 'secundario',
                'secundaria': 'secundario',
                'terciario': 'terciario',
                'terciaria': 'terciario',
                'universitario': 'universitario',
                'universitaria': 'universitario',
                'grado': 'universitario',
                'licenciatura': 'universitario',
                'posgrado': 'posgrado',
                'postgrado': 'posgrado',
                'maestría': 'posgrado',
                'maestria': 'posgrado',
                'doctorado': 'posgrado'
            }

            # Normalizar
            original_values = df['final_nivel_educativo'].value_counts()

            df['final_nivel_educativo'] = df['final_nivel_educativo'].astype(str).str.lower().map(
                education_mapping
            )

            normalized_values = df['final_nivel_educativo'].value_counts()

            logger.info(f"   Valores normalizados:")
            for nivel, count in normalized_values.items():
                logger.info(f"     {nivel}: {count:,}")

        return df

    def add_summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega columnas de estadísticas resumen"""
        logger.info("\n5. Agregando estadísticas resumen...")

        # Conteo de soft skills
        if 'soft_skills_clean' in df.columns:
            df['soft_skills_count'] = df['soft_skills_clean'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) else 0
            )

        # Conteo de skills técnicas
        if 'skills_tecnicas_clean' in df.columns:
            df['skills_tecnicas_count'] = df['skills_tecnicas_clean'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) else 0
            )

        # Flag de oferta completa (tiene todos los campos principales)
        df['is_complete'] = (
            df['final_nivel_educativo'].notna() &
            df['soft_skills_clean'].notna() &
            df['experiencia_min_anios'].notna()
        )

        complete_count = df['is_complete'].sum()
        logger.info(f"   Ofertas completas: {complete_count:,} ({100*complete_count/len(df):.1f}%)")

        return df

    def clean_all(self) -> pd.DataFrame:
        """Ejecuta toda la limpieza"""
        logger.info("=" * 70)
        logger.info("LIMPIEZA DE DATOS HÍBRIDOS")
        logger.info("=" * 70)

        # Cargar datos
        logger.info(f"\nCargando: {self.input_csv.name}")
        df = pd.read_csv(self.input_csv, low_memory=False)
        logger.info(f"  Filas: {len(df):,}")
        logger.info(f"  Columnas: {len(df.columns)}")

        # Aplicar limpiezas
        df = self.clean_soft_skills(df)
        df = self.clean_skills_tecnicas(df)
        df = self.normalize_education(df)
        df = self.add_summary_stats(df)
        df_clean = self.select_final_columns(df)

        # Guardar
        logger.info("\n" + "=" * 70)
        logger.info("GUARDANDO DATOS LIMPIOS")
        logger.info("=" * 70)
        df_clean.to_csv(self.output_csv, index=False)
        logger.info(f"\n✓ Guardado: {self.output_csv}")
        logger.info(f"  Tamaño: {self.output_csv.stat().st_size / 1024 / 1024:.1f} MB")

        # Resumen final
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN FINAL")
        logger.info("=" * 70)
        logger.info(f"Ofertas totales: {len(df_clean):,}")
        logger.info(f"Columnas: {len(df_clean.columns)}")

        # Cobertura por campo
        logger.info("\nCOBERTURA POR CAMPO:")
        key_fields = [
            'soft_skills_clean',
            'skills_tecnicas_clean',
            'final_nivel_educativo',
            'experiencia_min_anios',
            'idioma_principal'
        ]

        for field in key_fields:
            if field in df_clean.columns:
                coverage = df_clean[field].notna().sum()
                pct = 100 * coverage / len(df_clean)
                logger.info(f"  {field}: {coverage:,} ({pct:.1f}%)")

        logger.info("=" * 70)

        return df_clean


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Limpia datos híbridos')
    parser.add_argument(
        '--input',
        type=str,
        default=r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_hybrid_20251027_141056.csv',
        help='CSV de entrada (con datos híbridos)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='CSV de salida (opcional)'
    )

    args = parser.parse_args()

    try:
        cleaner = HybridDataCleaner(
            input_csv=args.input,
            output_csv=args.output
        )

        df_clean = cleaner.clean_all()

        logger.info("\n¡Limpieza completada! ✓")

    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
