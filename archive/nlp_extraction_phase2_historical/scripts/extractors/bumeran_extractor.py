# -*- coding: utf-8 -*-
"""
Bumeran Extractor - Extractor NLP para ofertas de Bumeran
==========================================================

Implementación del extractor para Bumeran usando regex patterns.
Bumeran tiene excelente calidad de descripciones (100% cobertura).
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Agregar path para imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from base_nlp_extractor import BaseNLPExtractor
from patterns.regex_patterns_v3 import (
    ExperienciaPatterns,
    EducacionPatterns,
    IdiomasPatterns,
    SkillsPatterns,
    SalarioPatterns,
    JornadaPatterns
)
from cleaning import TextCleaner, HTMLStripper, EncodingFixer
from smart_inference import SmartInferenceEngine


class BumeranExtractor(BaseNLPExtractor):
    """
    Extractor NLP para ofertas de Bumeran

    Bumeran características:
    - 100% de ofertas tienen descripción
    - Descripciones en español
    - Buena estructura y formato
    - Alto contenido de requisitos
    """

    def __init__(self, version: str = "3.7.0"):
        super().__init__(source_name="bumeran", version=version)

    def _clean_text(self, text: str) -> str:
        """
        Limpia texto antes de procesamiento

        Args:
            text: Texto crudo

        Returns:
            Texto limpio
        """
        if not text:
            return ""

        # 1. Corregir encoding
        text = EncodingFixer.fix_all(text)

        # 2. Limpiar HTML
        text = HTMLStripper.clean_html_full(text)

        # 3. Normalizar texto
        text = TextCleaner.clean_full(text)

        return text

    def extract_experiencia(self, text: str) -> Dict:
        """Extrae información de experiencia laboral"""
        text_clean = self._clean_text(text)

        min_years, max_years = ExperienciaPatterns.extract_years(text_clean)
        area = ExperienciaPatterns.extract_area(text_clean)

        # Calcular confidence
        confidence = 0.0
        if min_years is not None:
            confidence += 0.5
        if max_years is not None:
            confidence += 0.2
        if area is not None:
            confidence += 0.3

        return {
            'experiencia_min_anios': min_years,
            'experiencia_max_anios': max_years,
            'experiencia_area': area,
            'confidence': min(confidence, 1.0)
        }

    def extract_educacion(self, text: str) -> Dict:
        """Extrae información de educación requerida"""
        text_clean = self._clean_text(text)

        nivel = EducacionPatterns.extract_nivel(text_clean)
        estado = EducacionPatterns.extract_estado(text_clean)
        excluyente = EducacionPatterns.is_excluyente(text_clean)

        # Extraer carrera específica (simple por ahora)
        carrera = None
        carreras_comunes = [
            'ingeniería en sistemas', 'ingenieria en sistemas',
            'licenciatura en administración', 'licenciatura en administracion',
            'contador público', 'contador publico',
            'ingeniería industrial', 'ingenieria industrial',
            'licenciatura en economía', 'licenciatura en economia',
            'ingeniería comercial', 'ingenieria comercial',
        ]
        text_lower = text_clean.lower()
        for carrera_pattern in carreras_comunes:
            if carrera_pattern in text_lower:
                carrera = carrera_pattern.title()
                break

        # Calcular confidence
        confidence = 0.0
        if nivel is not None:
            confidence += 0.5
        if estado is not None:
            confidence += 0.2
        if carrera is not None:
            confidence += 0.2
        if excluyente:
            confidence += 0.1

        return {
            'nivel_educativo': nivel,
            'estado_educativo': estado,
            'carrera_especifica': carrera,
            'titulo_excluyente': excluyente if nivel else None,
            'confidence': min(confidence, 1.0)
        }

    def extract_idiomas(self, text: str) -> Dict:
        """Extrae información de idiomas requeridos"""
        text_clean = self._clean_text(text)

        idiomas_list = IdiomasPatterns.extract_idiomas(text_clean)

        # Asignar principal y secundario
        idioma_principal = None
        nivel_principal = None
        idioma_secundario = None
        nivel_secundario = None

        if len(idiomas_list) >= 1:
            idioma_principal, nivel_principal = idiomas_list[0]

        if len(idiomas_list) >= 2:
            idioma_secundario, nivel_secundario = idiomas_list[1]

        # Calcular confidence
        confidence = 0.0
        if idioma_principal:
            confidence += 0.4
        if nivel_principal:
            confidence += 0.3
        if idioma_secundario:
            confidence += 0.2
        if nivel_secundario:
            confidence += 0.1

        return {
            'idioma_principal': idioma_principal,
            'nivel_idioma_principal': nivel_principal,
            'idioma_secundario': idioma_secundario,
            'nivel_idioma_secundario': nivel_secundario,
            'confidence': min(confidence, 1.0)
        }

    def extract_skills(self, text: str) -> Dict:
        """Extrae skills técnicas y blandas"""
        text_clean = self._clean_text(text)

        skills_tecnicas = SkillsPatterns.extract_technical_skills(text_clean)
        soft_skills = SkillsPatterns.extract_soft_skills(text_clean)

        # Por ahora, niveles y certificaciones vacíos (fase 2)
        niveles_skills = []
        certificaciones = []

        # Calcular confidence
        confidence = 0.0
        if skills_tecnicas:
            confidence += 0.5
        if soft_skills:
            confidence += 0.3

        return {
            'skills_tecnicas_list': skills_tecnicas if skills_tecnicas else None,
            'niveles_skills_list': niveles_skills if niveles_skills else None,
            'soft_skills_list': soft_skills if soft_skills else None,
            'certificaciones_list': certificaciones if certificaciones else None,
            'confidence': min(confidence, 1.0)
        }

    def extract_salario(self, text: str) -> Dict:
        """Extrae información de salario/compensación"""
        text_clean = self._clean_text(text)

        # Bumeran generalmente NO publica salarios en descripciones
        # Esta funcionalidad se implementará en fase 2

        return {
            'salario_min': None,
            'salario_max': None,
            'moneda': None,
            'beneficios_list': None,
            'confidence': 0.0
        }

    def extract_requisitos(self, text: str) -> Dict:
        """Extrae requisitos excluyentes y deseables"""
        text_clean = self._clean_text(text)

        # Buscar secciones de requisitos
        requisitos_excluyentes = []
        requisitos_deseables = []

        # Palabras clave para excluyentes
        if 'excluyente' in text_clean.lower():
            # Extraer líneas que contengan "excluyente"
            lines = text_clean.split('\n')
            for line in lines:
                if 'excluyente' in line.lower():
                    requisitos_excluyentes.append(line.strip())

        # Palabras clave para deseables
        if any(kw in text_clean.lower() for kw in ['deseable', 'valorable', 'plus']):
            lines = text_clean.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['deseable', 'valorable', 'plus']):
                    requisitos_deseables.append(line.strip())

        # Calcular confidence
        confidence = 0.0
        if requisitos_excluyentes:
            confidence += 0.5
        if requisitos_deseables:
            confidence += 0.3

        return {
            'requisitos_excluyentes_list': requisitos_excluyentes if requisitos_excluyentes else None,
            'requisitos_deseables_list': requisitos_deseables if requisitos_deseables else None,
            'confidence': min(confidence, 1.0)
        }

    def extract_jornada(self, text: str) -> Dict:
        """Extrae información de jornada y horarios"""
        text_clean = self._clean_text(text)

        jornada = JornadaPatterns.extract_tipo(text_clean)
        flexible = JornadaPatterns.is_flexible(text_clean)

        # Calcular confidence
        confidence = 0.0
        if jornada is not None:
            confidence += 0.6
        if flexible is not None:
            confidence += 0.4

        return {
            'jornada_laboral': jornada,
            'horario_flexible': flexible if flexible else None,
            'confidence': min(confidence, 1.0)
        }

    def extract_all(self, descripcion: str, titulo: str = "") -> Dict:
        """
        Extrae toda la información con v3 + FASE 2 (Smart Inference)

        Args:
            descripcion: Descripción completa de la oferta
            titulo: Título del puesto (opcional)

        Returns:
            Dict con todos los campos extraídos + inferencias
        """
        # 1. Ejecutar extracción base v3 (patrones regex ultra-agresivos)
        v3_result = super().extract_all(descripcion, titulo)

        # 2. Aplicar FASE 2: Smart Inference
        enhanced_result = SmartInferenceEngine.apply_all_inferences(
            v3_result,
            titulo,
            descripcion
        )

        return enhanced_result


# Función helper para uso rápido
def extract_from_bumeran(descripcion: str, titulo: str = "") -> Dict:
    """
    Función helper para extraer rápidamente de una descripción

    Args:
        descripcion: Descripción de la oferta
        titulo: Título del puesto (opcional)

    Returns:
        Dict con campos extraídos
    """
    extractor = BumeranExtractor()
    return extractor.extract_all(descripcion, titulo)


# Ejemplo de uso
if __name__ == "__main__":
    # Descripción de ejemplo
    descripcion_ejemplo = """
    Buscamos Desarrollador Python Senior para sumarse a nuestro equipo de tecnología.

    Requisitos excluyentes:
    - Título universitario en Ingeniería en Sistemas, Licenciatura en Informática o afines (completo)
    - 5+ años de experiencia en desarrollo de software
    - Conocimientos sólidos en Python, Django, PostgreSQL
    - Inglés intermedio/avanzado
    - Experiencia con Git, Docker, AWS

    Requisitos deseables:
    - Conocimientos en React
    - Experiencia liderando equipos
    - Certificaciones en AWS

    Ofrecemos:
    - Full time, horario flexible
    - Trabajo en equipo dinámico
    - Posibilidad de crecimiento profesional
    """

    print("Probando BumeranExtractor")
    print("=" * 70)

    extractor = BumeranExtractor()
    resultado = extractor.extract_all(descripcion_ejemplo, "Desarrollador Python Senior")

    print("\nRESULTADOS:")
    for key, value in resultado.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print(f"Confidence Score: {resultado['nlp_confidence_score']:.2f}")
