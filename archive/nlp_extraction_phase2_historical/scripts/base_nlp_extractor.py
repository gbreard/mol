# -*- coding: utf-8 -*-
"""
Base NLP Extractor - Clase abstracta para extractores
=====================================================

Define la interfaz común para todos los extractores de cada fuente.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class BaseNLPExtractor(ABC):
    """
    Clase base abstracta para extractores NLP de cada fuente

    Cada fuente (Bumeran, ZonaJobs, Indeed, etc.) debe implementar
    su propio extractor heredando de esta clase.
    """

    def __init__(self, source_name: str, version: str = "1.0.0"):
        """
        Inicializa el extractor

        Args:
            source_name: Nombre de la fuente (ej: 'bumeran', 'zonajobs')
            version: Versión del extractor
        """
        self.source_name = source_name
        self.version = version

    @abstractmethod
    def extract_experiencia(self, text: str) -> Dict:
        """
        Extrae información de experiencia laboral

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - experiencia_min_anios: int o None
                - experiencia_max_anios: int o None
                - experiencia_area: str o None
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_educacion(self, text: str) -> Dict:
        """
        Extrae información de educación requerida

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - nivel_educativo: str o None (secundario, terciario, universitario, posgrado)
                - estado_educativo: str o None (completo, en_curso, incompleto)
                - carrera_especifica: str o None
                - titulo_excluyente: bool
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_idiomas(self, text: str) -> Dict:
        """
        Extrae información de idiomas requeridos

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - idioma_principal: str o None
                - nivel_idioma_principal: str o None (basico, intermedio, avanzado, nativo)
                - idioma_secundario: str o None
                - nivel_idioma_secundario: str o None
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_skills(self, text: str) -> Dict:
        """
        Extrae skills técnicas y blandas

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - skills_tecnicas_list: List[str]
                - niveles_skills_list: List[str]
                - soft_skills_list: List[str]
                - certificaciones_list: List[str]
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_salario(self, text: str) -> Dict:
        """
        Extrae información de salario/compensación

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - salario_min: float o None
                - salario_max: float o None
                - moneda: str o None (ARS, USD, etc)
                - beneficios_list: List[str]
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_requisitos(self, text: str) -> Dict:
        """
        Extrae requisitos excluyentes y deseables

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - requisitos_excluyentes_list: List[str]
                - requisitos_deseables_list: List[str]
                - confidence: float (0-1)
        """
        pass

    @abstractmethod
    def extract_jornada(self, text: str) -> Dict:
        """
        Extrae información de jornada y horarios

        Args:
            text: Texto de la descripción

        Returns:
            Dict con:
                - jornada_laboral: str o None (full_time, part_time, etc)
                - horario_flexible: bool o None
                - confidence: float (0-1)
        """
        pass

    def extract_all(self, descripcion: str, titulo: str = "") -> Dict:
        """
        Extrae toda la información de una oferta

        Args:
            descripcion: Descripción completa de la oferta
            titulo: Título del puesto (opcional, puede tener info adicional)

        Returns:
            Dict con todos los campos extraídos
        """
        # Combinar título y descripción para análisis
        texto_completo = f"{titulo}\n\n{descripcion}" if titulo else descripcion

        # Extraer cada categoría
        experiencia = self.extract_experiencia(texto_completo)
        educacion = self.extract_educacion(texto_completo)
        idiomas = self.extract_idiomas(texto_completo)
        skills = self.extract_skills(texto_completo)
        salario = self.extract_salario(texto_completo)
        requisitos = self.extract_requisitos(texto_completo)
        jornada = self.extract_jornada(texto_completo)

        # Calcular confidence promedio
        confidences = [
            experiencia.get('confidence', 0),
            educacion.get('confidence', 0),
            idiomas.get('confidence', 0),
            skills.get('confidence', 0),
            salario.get('confidence', 0),
            requisitos.get('confidence', 0),
            jornada.get('confidence', 0),
        ]
        avg_confidence = sum(confidences) / len(confidences)

        # Consolidar resultado
        resultado = {
            **{k: v for k, v in experiencia.items() if k != 'confidence'},
            **{k: v for k, v in educacion.items() if k != 'confidence'},
            **{k: v for k, v in idiomas.items() if k != 'confidence'},
            **{k: v for k, v in skills.items() if k != 'confidence'},
            **{k: v for k, v in salario.items() if k != 'confidence'},
            **{k: v for k, v in requisitos.items() if k != 'confidence'},
            **{k: v for k, v in jornada.items() if k != 'confidence'},
            'nlp_extraction_timestamp': datetime.now().isoformat(),
            'nlp_version': self.version,
            'nlp_confidence_score': round(avg_confidence, 3)
        }

        return resultado

    def process_dataframe(
        self,
        df: pd.DataFrame,
        descripcion_col: str,
        titulo_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Procesa un DataFrame completo de ofertas

        Args:
            df: DataFrame con ofertas
            descripcion_col: Nombre de columna con descripción
            titulo_col: Nombre de columna con título (opcional)

        Returns:
            DataFrame con columnas NLP agregadas
        """
        print(f"\n[{self.source_name.upper()}] Procesando {len(df)} ofertas...")

        resultados = []

        for idx, row in df.iterrows():
            if idx % 100 == 0 and idx > 0:
                print(f"  Procesadas {idx}/{len(df)} ofertas...")

            descripcion = row.get(descripcion_col, "")
            titulo = row.get(titulo_col, "") if titulo_col else ""

            try:
                extracted = self.extract_all(descripcion, titulo)
                resultados.append(extracted)
            except Exception as e:
                print(f"  [ERROR] Oferta {idx}: {e}")
                # Agregar resultado vacío con error
                resultados.append({
                    'nlp_extraction_timestamp': datetime.now().isoformat(),
                    'nlp_version': self.version,
                    'nlp_confidence_score': 0.0,
                    'nlp_error': str(e)
                })

        # Convertir a DataFrame y combinar
        df_extracted = pd.DataFrame(resultados)
        df_result = pd.concat([df, df_extracted], axis=1)

        print(f"[{self.source_name.upper()}] Completado. {len(df_result)} ofertas procesadas.\n")

        return df_result

    def get_extraction_stats(self, df: pd.DataFrame) -> Dict:
        """
        Genera estadísticas de extracción

        Args:
            df: DataFrame con resultados de extracción

        Returns:
            Dict con estadísticas
        """
        stats = {
            'total_ofertas': len(df),
            'avg_confidence': df['nlp_confidence_score'].mean() if 'nlp_confidence_score' in df.columns else 0,
            'ofertas_con_experiencia': df['experiencia_min_anios'].notna().sum() if 'experiencia_min_anios' in df.columns else 0,
            'ofertas_con_educacion': df['nivel_educativo'].notna().sum() if 'nivel_educativo' in df.columns else 0,
            'ofertas_con_idiomas': df['idioma_principal'].notna().sum() if 'idioma_principal' in df.columns else 0,
            'ofertas_con_salario': df['salario_min'].notna().sum() if 'salario_min' in df.columns else 0,
        }

        return stats
