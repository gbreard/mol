# -*- coding: utf-8 -*-
"""
Indeed Extractor - Extractor NLP para ofertas de Indeed (Bilingüe ES/EN)
========================================================================

Implementación del extractor para Indeed con soporte bilingüe.
Indeed tiene descripciones mixtas en español e inglés.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import re

# Agregar path para imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from base_nlp_extractor import BaseNLPExtractor
from patterns.regex_patterns import (
    ExperienciaPatterns,
    EducacionPatterns,
    IdiomasPatterns,
    SkillsPatterns,
    SalarioPatterns,
    JornadaPatterns
)
from cleaning import TextCleaner, HTMLStripper, EncodingFixer


class IndeedBilingualPatterns:
    """Patrones adicionales en inglés para Indeed"""

    # Experiencia en inglés
    YEARS_EXPERIENCE_EN = [
        r'(\d+)\+\s*years?',
        r'(?:minimum|at least)\s*(\d+)\s*years?',
        r'(\d+)\s*to\s*(\d+)\s*years?',
        r'(\d+)\s*years?\s+(?:of\s+)?experience',
    ]

    # Educación en inglés
    EDUCATION_LEVELS_EN = {
        'secundario': [r'\bhigh\s+school\b', r'\bsecondary\b'],
        'terciario': [r'\btechnical\s+(?:degree|diploma)\b', r'\bassociate\b'],
        'universitario': [r'\bbachelor[\'s]?\b', r'\bundergraduate\b', r'\bdegree\b'],
        'posgrado': [r'\bmaster[\'s]?\b', r'\bphd\b', r'\bdoctorate\b', r'\bgraduate\b'],
    }

    EDUCATION_STATUS_EN = {
        'completo': [r'\bcompleted\b', r'\bgraduated\b'],
        'en_curso': [r'\bin\s+progress\b', r'\bcurrently\s+studying\b'],
    }

    # Idiomas en inglés
    LANGUAGES_EN = {
        'ingles': [r'\benglish\b'],
        'espanol': [r'\bspanish\b'],
        'portugues': [r'\bportuguese\b'],
        'aleman': [r'\bgerman\b'],
        'frances': [r'\bfrench\b'],
    }

    LANGUAGE_LEVELS_EN = {
        'basico': [r'\bbasic\b', r'\belementary\b'],
        'intermedio': [r'\bintermediate\b'],
        'avanzado': [r'\badvanced\b', r'\bfluent\b', r'\bproficient\b'],
        'nativo': [r'\bnative\b'],
        'bilingue': [r'\bbilingual\b'],
    }

    # Jornada en inglés
    WORK_TYPE_EN = {
        'full_time': [r'\bfull\s*time\b', r'\bfull-time\b'],
        'part_time': [r'\bpart\s*time\b', r'\bpart-time\b'],
        'freelance': [r'\bfreelance\b', r'\bcontractor\b'],
        'temporal': [r'\btemporary\b', r'\btemp\b'],
        'pasantia': [r'\binternship\b', r'\bintern\b'],
    }


class IndeedExtractor(BaseNLPExtractor):
    """
    Extractor NLP para ofertas de Indeed con soporte bilingüe

    Indeed características:
    - 100% de ofertas tienen descripción
    - Descripciones mixtas: español e inglés
    - Formato variado (internacional)
    - Necesita patrones bilingües
    """

    def __init__(self, version: str = "1.0.0"):
        super().__init__(source_name="indeed", version=version)

    def _clean_text(self, text: str) -> str:
        """Limpia texto antes de procesamiento"""
        if not text:
            return ""

        text = EncodingFixer.fix_all(text)
        text = HTMLStripper.clean_html_full(text)
        text = TextCleaner.clean_full(text)

        return text

    def _detect_language(self, text: str) -> str:
        """
        Detecta idioma predominante del texto

        Returns:
            'es' o 'en'
        """
        text_lower = text.lower()

        # Palabras clave en español
        spanish_keywords = ['experiencia', 'requisitos', 'años', 'conocimientos', 'empresa', 'trabajo']
        spanish_count = sum(1 for kw in spanish_keywords if kw in text_lower)

        # Palabras clave en inglés
        english_keywords = ['experience', 'requirements', 'years', 'knowledge', 'company', 'work']
        english_count = sum(1 for kw in english_keywords if kw in text_lower)

        return 'es' if spanish_count >= english_count else 'en'

    def extract_experiencia(self, text: str) -> Dict:
        """Extrae información de experiencia laboral (bilingüe)"""
        text_clean = self._clean_text(text)
        lang = self._detect_language(text_clean)

        # Intentar primero con patrones español
        min_years, max_years = ExperienciaPatterns.extract_years(text_clean)

        # Si no encontró y el texto está en inglés, probar patrones inglés
        if min_years is None and lang == 'en':
            text_lower = text_clean.lower()
            for pattern in IndeedBilingualPatterns.YEARS_EXPERIENCE_EN:
                match = re.search(pattern, text_lower)
                if match:
                    groups = match.groups()
                    if len(groups) == 2 and groups[1]:
                        try:
                            min_years, max_years = int(groups[0]), int(groups[1])
                            break
                        except ValueError:
                            pass
                    elif len(groups) >= 1 and groups[0]:
                        try:
                            min_years = int(groups[0])
                            break
                        except ValueError:
                            pass

        # Área (funciona igual en ambos idiomas generalmente)
        area = ExperienciaPatterns.extract_area(text_clean)

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
        """Extrae información de educación requerida (bilingüe)"""
        text_clean = self._clean_text(text)
        lang = self._detect_language(text_clean)

        # Intentar español primero
        nivel = EducacionPatterns.extract_nivel(text_clean)
        estado = EducacionPatterns.extract_estado(text_clean)
        excluyente = EducacionPatterns.is_excluyente(text_clean)

        # Si no encontró y está en inglés, probar patrones inglés
        if nivel is None and lang == 'en':
            text_lower = text_clean.lower()
            for nivel_name, patterns in IndeedBilingualPatterns.EDUCATION_LEVELS_EN.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        nivel = nivel_name
                        break
                if nivel:
                    break

        if estado is None and lang == 'en':
            text_lower = text_clean.lower()
            for estado_name, patterns in IndeedBilingualPatterns.EDUCATION_STATUS_EN.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        estado = estado_name
                        break
                if estado:
                    break

        # Carrera específica
        carrera = None
        carreras = [
            'ingeniería en sistemas', 'ingenieria en sistemas',
            'computer science', 'systems engineering',
            'licenciatura en administración', 'business administration',
        ]
        text_lower = text_clean.lower()
        for carrera_pattern in carreras:
            if carrera_pattern in text_lower:
                carrera = carrera_pattern.title()
                break

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
        """Extrae información de idiomas requeridos (bilingüe)"""
        text_clean = self._clean_text(text)
        lang = self._detect_language(text_clean)

        # Español primero
        idiomas_list = IdiomasPatterns.extract_idiomas(text_clean)

        # Si no encontró y está en inglés, probar patrones inglés
        if not idiomas_list and lang == 'en':
            text_lower = text_clean.lower()
            for idioma, patterns in IndeedBilingualPatterns.LANGUAGES_EN.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        # Buscar nivel cerca
                        nivel = None
                        for nivel_name, nivel_patterns in IndeedBilingualPatterns.LANGUAGE_LEVELS_EN.items():
                            for nivel_pattern in nivel_patterns:
                                # Buscar nivel en ventana de ±50 chars
                                match = re.search(pattern, text_lower)
                                if match:
                                    start = max(0, match.start() - 50)
                                    end = min(len(text_lower), match.end() + 50)
                                    contexto = text_lower[start:end]
                                    if re.search(nivel_pattern, contexto):
                                        nivel = nivel_name
                                        break
                            if nivel:
                                break
                        idiomas_list.append((idioma, nivel))
                        break

        # Asignar principal y secundario
        idioma_principal = None
        nivel_principal = None
        idioma_secundario = None
        nivel_secundario = None

        if len(idiomas_list) >= 1:
            idioma_principal, nivel_principal = idiomas_list[0]

        if len(idiomas_list) >= 2:
            idioma_secundario, nivel_secundario = idiomas_list[1]

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

        niveles_skills = []
        certificaciones = []

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

        # Fase 2
        return {
            'salario_min': None,
            'salario_max': None,
            'moneda': None,
            'beneficios_list': None,
            'confidence': 0.0
        }

    def extract_requisitos(self, text: str) -> Dict:
        """Extrae requisitos excluyentes y deseables (bilingüe)"""
        text_clean = self._clean_text(text)

        requisitos_excluyentes = []
        requisitos_deseables = []

        # Español
        if any(kw in text_clean.lower() for kw in ['excluyente', 'obligatorio', 'indispensable']):
            lines = text_clean.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['excluyente', 'obligatorio', 'indispensable']) and len(line.strip()) > 15:
                    requisitos_excluyentes.append(line.strip())

        if any(kw in text_clean.lower() for kw in ['deseable', 'valorable', 'plus']):
            lines = text_clean.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['deseable', 'valorable', 'plus']) and len(line.strip()) > 15:
                    requisitos_deseables.append(line.strip())

        # Inglés
        if any(kw in text_clean.lower() for kw in ['required', 'must have', 'mandatory']):
            lines = text_clean.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['required', 'must have', 'mandatory']) and len(line.strip()) > 15:
                    requisitos_excluyentes.append(line.strip())

        if any(kw in text_clean.lower() for kw in ['preferred', 'nice to have', 'bonus']):
            lines = text_clean.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['preferred', 'nice to have', 'bonus']) and len(line.strip()) > 15:
                    requisitos_deseables.append(line.strip())

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
        """Extrae información de jornada y horarios (bilingüe)"""
        text_clean = self._clean_text(text)
        lang = self._detect_language(text_clean)

        # Español primero
        jornada = JornadaPatterns.extract_tipo(text_clean)
        flexible = JornadaPatterns.is_flexible(text_clean)

        # Inglés
        if jornada is None and lang == 'en':
            text_lower = text_clean.lower()
            for tipo, patterns in IndeedBilingualPatterns.WORK_TYPE_EN.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        jornada = tipo
                        break
                if jornada:
                    break

        if not flexible and re.search(r'flexible\s+(?:schedule|hours)', text_clean.lower()):
            flexible = True

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


# Ejemplo de uso
if __name__ == "__main__":
    # Descripción en inglés
    descripcion_en = """
    Senior Python Developer

    We are looking for an experienced Python Developer to join our team.

    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 5+ years of experience in software development
    - Strong knowledge of Python, Django, PostgreSQL
    - Fluent English required
    - Experience with AWS

    Preferred:
    - Knowledge of React
    - Experience leading teams

    Full-time position with flexible hours.
    """

    print("Probando IndeedExtractor (inglés)")
    print("=" * 70)

    extractor = IndeedExtractor()
    resultado = extractor.extract_all(descripcion_en, "Senior Python Developer")

    print("\nRESULTADOS:")
    for key, value in resultado.items():
        if value:
            print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print(f"Confidence Score: {resultado['nlp_confidence_score']:.2f}")
