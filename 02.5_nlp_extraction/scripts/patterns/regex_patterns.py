# -*- coding: utf-8 -*-
"""
Regex Patterns - Patrones de expresiones regulares para extracción NLP
======================================================================

Módulo con patrones regex organizados por categoría para extraer
información estructurada de descripciones de ofertas laborales.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ExperienciaPatterns:
    """Patrones para detectar experiencia laboral"""

    # Patrones para años de experiencia
    ANIOS_EXPERIENCIA = [
        # "3+ años", "mínimo 3 años"
        r'(\d+)\+\s*(?:años?|anios?)',
        # "mínimo 3 años", "al menos 3 años"
        r'(?:mínimo|minimo|al menos|como mínimo|como minimo)\s*(\d+)\s*(?:años?|anios?)',
        # "3 a 5 años", "entre 3 y 5 años", "de 3 a 5 años"
        r'(?:entre|de)\s*(\d+)\s*(?:a|y)\s*(\d+)\s*(?:años?|anios?)',
        # "experiencia: 3 años", "3 años de experiencia"
        r'(\d+)\s*(?:años?|anios?)\s+de\s+experiencia',
        # "experiencia de 3 años"
        r'experiencia\s+de\s+(\d+)\s*(?:años?|anios?)',
    ]

    # Patrones para área de experiencia
    AREA_EXPERIENCIA = [
        r'experiencia\s+(?:en|con)\s+([^.,;:\n]{5,50})',
        r'(?:conocimientos?|experiencia)\s+(?:previos?\s+)?(?:en|de)\s+([^.,;:\n]{5,50})',
    ]

    @staticmethod
    def extract_years(text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae años de experiencia (min, max)

        Returns:
            (min_years, max_years) o (None, None)
        """
        text_lower = text.lower()

        # Buscar rangos "3 a 5 años"
        for pattern in ExperienciaPatterns.ANIOS_EXPERIENCIA:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:  # Rango
                    try:
                        return (int(groups[0]), int(groups[1]))
                    except ValueError:
                        pass
                elif len(groups) >= 1 and groups[0]:  # Mínimo
                    try:
                        return (int(groups[0]), None)
                    except ValueError:
                        pass

        # Inferir de nivel: Senior = 5+, Semi-senior = 3+, Junior = 0-2
        if re.search(r'\b(senior|ssr|sr\.?)\b', text_lower):
            return (5, None)
        elif re.search(r'\b(semi\s*senior|semi-senior)\b', text_lower):
            return (3, None)
        elif re.search(r'\bjunior\b', text_lower):
            return (0, 2)

        return (None, None)

    @staticmethod
    def extract_area(text: str) -> Optional[str]:
        """Extrae área de experiencia"""
        text_lower = text.lower()

        for pattern in ExperienciaPatterns.AREA_EXPERIENCIA:
            match = re.search(pattern, text_lower)
            if match:
                area = match.group(1).strip()
                if len(area) > 5:  # Mínimo 5 caracteres para ser válido
                    return area

        return None


class EducacionPatterns:
    """Patrones para detectar educación requerida"""

    # Niveles educativos
    NIVELES = {
        'secundario': [
            r'\bsecundari[oa]\s+complet[oa]\b',
            r'\bbachiller\b',
            r'\bestudiante\s+secundari[oa]\b',
        ],
        'terciario': [
            r'\btercia?ri[oa]\s+complet[oa]\b',
            r'\btécnico\s+(?:superior)?\b',
            r'\btecnico\s+(?:superior)?\b',
        ],
        'universitario': [
            r'\buniversitari[oa]\s+complet[oa]\b',
            r'\blicenciatura\b',
            r'\bingeniería\b',
            r'\bingenieria\b',
            r'\btítulo\s+universitario\b',
            r'\btitulo\s+universitario\b',
            r'\bgraduado\b',
        ],
        'posgrado': [
            r'\bposgrado\b',
            r'\bpost\s*grado\b',
            r'\bmaestrí?a\b',
            r'\bmaster\b',
            r'\bdoctorado\b',
            r'\bphd\b',
        ]
    }

    # Estado educativo
    ESTADOS = {
        'completo': [r'\bcomplet[oa]\b', r'\bgraduado\b', r'\bfinalizado\b'],
        'en_curso': [r'\ben\s+curso\b', r'\bestudiando\b', r'\bcursando\b'],
        'incompleto': [r'\bincomplete\b', r'\bavanzado\b'],
    }

    # Excluyente
    EXCLUYENTE = [
        r'\bexcluyente\b',
        r'\bobligatorio\b',
        r'\bindispensable\b',
        r'\bresquisito\b',
    ]

    @staticmethod
    def extract_nivel(text: str) -> Optional[str]:
        """Extrae nivel educativo más alto mencionado"""
        text_lower = text.lower()

        # Orden de prioridad: posgrado > universitario > terciario > secundario
        for nivel in ['posgrado', 'universitario', 'terciario', 'secundario']:
            for pattern in EducacionPatterns.NIVELES[nivel]:
                if re.search(pattern, text_lower):
                    return nivel

        return None

    @staticmethod
    def extract_estado(text: str) -> Optional[str]:
        """Extrae estado educativo"""
        text_lower = text.lower()

        for estado, patterns in EducacionPatterns.ESTADOS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return estado

        return None

    @staticmethod
    def is_excluyente(text: str) -> bool:
        """Determina si el título es excluyente"""
        text_lower = text.lower()

        for pattern in EducacionPatterns.EXCLUYENTE:
            if re.search(pattern, text_lower):
                return True

        return False


class IdiomasPatterns:
    """Patrones para detectar idiomas requeridos"""

    # Idiomas comunes
    IDIOMAS = {
        'ingles': [r'\binglé?s\b', r'\benglish\b'],
        'portugues': [r'\bportugué?s\b', r'\bportuguese\b'],
        'aleman': [r'\balemá?n\b', r'\bgerman\b'],
        'frances': [r'\bfrancé?s\b', r'\bfrench\b'],
        'italiano': [r'\bitaliano\b', r'\bitalian\b'],
    }

    # Niveles
    NIVELES = {
        'basico': [r'\bbá?sico\b', r'\bbasic\b', r'\belementary\b'],
        'intermedio': [r'\bintermedio\b', r'\bintermediate\b'],
        'avanzado': [r'\bavanzado\b', r'\badvanced\b', r'\bfluent\b'],
        'nativo': [r'\bnativo\b', r'\bnative\b'],
        'bilingue': [r'\bbilingü?e\b', r'\bbilingual\b'],
    }

    @staticmethod
    def extract_idiomas(text: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extrae idiomas y niveles

        Returns:
            Lista de tuplas (idioma, nivel)
        """
        text_lower = text.lower()
        idiomas_encontrados = []

        for idioma, patterns in IdiomasPatterns.IDIOMAS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Buscar nivel cerca del idioma (±50 chars)
                    match = re.search(pattern, text_lower)
                    if match:
                        start = max(0, match.start() - 50)
                        end = min(len(text_lower), match.end() + 50)
                        contexto = text_lower[start:end]

                        nivel = None
                        for nivel_name, nivel_patterns in IdiomasPatterns.NIVELES.items():
                            for nivel_pattern in nivel_patterns:
                                if re.search(nivel_pattern, contexto):
                                    nivel = nivel_name
                                    break
                            if nivel:
                                break

                        idiomas_encontrados.append((idioma, nivel))
                        break

        return idiomas_encontrados


class SkillsPatterns:
    """Patrones para detectar skills técnicas - Carga desde JSON"""

    _skills_db = None
    _technical_patterns = None
    _soft_patterns = None

    @classmethod
    def _load_skills_database(cls):
        """Carga la base de datos de skills desde JSON"""
        if cls._skills_db is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
            skills_file = config_dir / "skills_database.json"

            with open(skills_file, 'r', encoding='utf-8') as f:
                cls._skills_db = json.load(f)

            # Construir lista de patrones técnicos
            cls._technical_patterns = []
            for categoria, data in cls._skills_db['categorias'].items():
                for skill in data['skills']:
                    cls._technical_patterns.append(rf'\b{skill}\b')

            # Construir lista de patrones soft skills
            cls._soft_patterns = []
            for categoria, skills_list in cls._skills_db['soft_skills_expanded'].items():
                for skill in skills_list:
                    # Escapar caracteres especiales y crear pattern
                    escaped = re.escape(skill).replace(r'\ ', r'\s+')
                    cls._soft_patterns.append(escaped)

    @classmethod
    def extract_technical_skills(cls, text: str) -> List[str]:
        """Extrae skills técnicas (215 skills)"""
        if cls._technical_patterns is None:
            cls._load_skills_database()

        text_lower = text.lower()
        skills = []

        for pattern in cls._technical_patterns:
            try:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                skills.extend(matches)
            except re.error:
                # Skip patrones problemáticos
                continue

        # Deduplicar manteniendo orden
        return list(dict.fromkeys(skills))

    @classmethod
    def extract_soft_skills(cls, text: str) -> List[str]:
        """Extrae soft skills (expandido)"""
        if cls._soft_patterns is None:
            cls._load_skills_database()

        text_lower = text.lower()
        skills = []

        for pattern in cls._soft_patterns:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    skills.append(match.group(0))
            except re.error:
                # Skip patrones problemáticos
                continue

        return list(dict.fromkeys(skills))


class SalarioPatterns:
    """Patrones para detectar salario"""

    # Patrones de montos
    MONTOS = [
        # "$100.000", "$100000", "$100K"
        r'\$\s*(\d{1,3}(?:[.,]\d{3})*(?:[kK])?)',
        # "USD 1000", "ARS 150000"
        r'(USD|ARS|EUR|BRL)\s+(\d{1,3}(?:[.,]\d{3})*)',
        # "salario: 100000"
        r'(?:salario|sueldo|remuneraci[oó]n):\s*\$?\s*(\d{1,3}(?:[.,]\d{3})*)',
    ]

    @staticmethod
    def extract_montos(text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Extrae salario (min, max, moneda)

        Returns:
            (min_amount, max_amount, currency)
        """
        # Por ahora retornamos None, a implementar en próxima iteración
        return (None, None, None)


class JornadaPatterns:
    """Patrones para detectar jornada laboral"""

    TIPOS = {
        'full_time': [r'\bfull\s*time\b', r'\btiempo\s+completo\b', r'\b8\s*hs?\b', r'\b40\s*hs?\b'],
        'part_time': [r'\bpart\s*time\b', r'\bmedio\s+tiempo\b', r'\b4\s*hs?\b'],
        'por_proyecto': [r'\bpor\s+proyecto\b', r'\bproyecto\s+a\s+proyecto\b'],
        'freelance': [r'\bfreelance\b', r'\baut[oó]nomo\b'],
        'temporal': [r'\btemporal\b', r'\bcontrato\s+temporario\b'],
        'pasantia': [r'\bpasant[íi]a\b', r'\binternship\b'],
    }

    FLEXIBLE = [
        r'horario\s+flexible',
        r'flexibilidad\s+horaria',
        r'flexible\s+schedule',
    ]

    @staticmethod
    def extract_tipo(text: str) -> Optional[str]:
        """Extrae tipo de jornada"""
        text_lower = text.lower()

        for tipo, patterns in JornadaPatterns.TIPOS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return tipo

        return None

    @staticmethod
    def is_flexible(text: str) -> bool:
        """Determina si el horario es flexible"""
        text_lower = text.lower()

        for pattern in JornadaPatterns.FLEXIBLE:
            if re.search(pattern, text_lower):
                return True

        return False
