# -*- coding: utf-8 -*-
"""
Regex Patterns v2 - MEJORADO para ofertas argentinas
====================================================

VERSION: 2.0
FECHA: 2025-11-01
MEJORAS: Género, plural, horarios específicos, carreras, oficios

Cambios principales respecto a v1:
- Experiencia: Agregado soporte para género (mínima/mínimo)
- Educación: Agregado soporte para plural (secundarios/secundario)
- Educación: Agregado detección de "Estudiante de [carrera]"
- Jornada: Agregado horarios específicos (9 a 18hs)
- Jornada: Agregado días de semana (Lunes a viernes)
- Salario: Implementada función de extracción
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ExperienciaPatterns:
    """Patrones para detectar experiencia laboral - MEJORADOS"""

    # Patrones para años de experiencia - VERSION MEJORADA
    ANIOS_EXPERIENCIA = [
        # "3+ años", "3 + años"
        r'(\d+)\s*\+\s*(?:años?|anios?)',

        # "mínimo/mínima 3 años" - AGREGADO GÉNERO
        r'(?:mínim[oa]s?|minim[oa]s?|al menos|como mínim[oa]?|como minim[oa]?)\s*(\d+)\s*(?:años?|anios?)',

        # "3 a 5 años", "entre 3 y 5 años", "de 3 a 5 años"
        r'(?:entre|de)\s*(\d+)\s*(?:a|y)\s*(\d+)\s*(?:años?|anios?)',

        # "3 años de experiencia"
        r'(\d+)\s*(?:años?|anios?)\s+de\s+experiencia',

        # "experiencia de 3 años"
        r'experiencia\s+de\s+(\d+)\s*(?:años?|anios?)',

        # NUEVOS: "experiencia: 3 años", "experiencia requerida: 3 años"
        r'experiencia\s*(?:requerida|necesaria)?:\s*(\d+)\s*(?:años?|anios?)',

        # NUEVO: "se requieren 3 años"
        r'se\s+requieren?\s+(\d+)\s*(?:años?|anios?)',

        # NUEVO: "con 3 años de experiencia"
        r'con\s+(\d+)\s*(?:años?|anios?)\s+de\s+experiencia',
    ]

    # Patrones para área de experiencia
    AREA_EXPERIENCIA = [
        r'experiencia\s+(?:en|con)\s+([^.,;:\n]{5,50})',
        r'(?:conocimientos?|experiencia)\s+(?:previos?\s+)?(?:en|de)\s+([^.,;:\n]{5,50})',
    ]

    @staticmethod
    def extract_years(text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae años de experiencia (min, max) - VERSION MEJORADA

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
                    except (ValueError, TypeError):
                        pass
                elif len(groups) >= 1 and groups[0]:  # Mínimo
                    try:
                        return (int(groups[0]), None)
                    except (ValueError, TypeError):
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
    """Patrones para detectar educación requerida - MEJORADOS"""

    # Niveles educativos - VERSION MEJORADA CON PLURAL Y "ESTUDIOS"
    NIVELES = {
        'secundario': [
            # ORIGINAL
            r'\bsecundari[oa]\s+complet[oa]\b',
            # NUEVO: Plural
            r'\bsecundari[oa]s\s+complet[oa]s\b',
            # NUEVO: Con "estudios"
            r'\bestudios?\s+secundari[oa]s?\s+complet[oa]s?\b',
            # Original
            r'\bbachiller\b',
            r'\bestudiante\s+secundari[oa]\b',
        ],
        'terciario': [
            # ORIGINAL
            r'\btercia?ri[oa]\s+complet[oa]\b',
            # NUEVO: Plural
            r'\btercia?ri[oa]s\s+complet[oa]s\b',
            # NUEVO: Con "estudios"
            r'\bestudios?\s+tercia?ri[oa]s?\s+complet[oa]s?\b',
            # Original
            r'\btécnico\s+(?:superior)?\b',
            r'\btecnico\s+(?:superior)?\b',
        ],
        'universitario': [
            # ORIGINAL
            r'\buniversitari[oa]\s+complet[oa]\b',
            # NUEVO: Plural
            r'\buniversitari[oa]s\s+complet[oa]s\b',
            # NUEVO: Con "estudios"
            r'\bestudios?\s+universitari[oa]s?\s+complet[oa]s?\b',
            # Original
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

    # Estado educativo - VERSION MEJORADA
    ESTADOS = {
        'completo': [r'\bcomplet[oa]s?\b', r'\bgraduado\b', r'\bfinalizado\b'],
        'en_curso': [
            r'\ben\s+curso\b',
            r'\bestudiando\b',
            r'\bcursando\b',
            # NUEVO: "estudiante de"
            r'\bestudiante\s+(?:de|en)\b',
        ],
        'incompleto': [r'\bincomplete\b', r'\bavanzado\b'],
    }

    # NUEVO: Patrón para extraer carrera específica
    CARRERA_PATTERN = r'(?:estudiante|cursando|carrera|licenciatura|ingeniería|ingenieria)\s+(?:de|en|la\s+carrera\s+de)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-záéíóúñA-ZÁÉÍÓÚÑ]+){0,3})'

    # Excluyente
    EXCLUYENTE = [
        r'\bexcluyente\b',
        r'\bobligatorio\b',
        r'\bindispensable\b',
        r'\brequisito\b',
    ]

    @staticmethod
    def extract_nivel(text: str) -> Optional[str]:
        """Extrae nivel educativo más alto mencionado - MEJORADO"""
        text_lower = text.lower()

        # Orden de prioridad: posgrado > universitario > terciario > secundario
        for nivel in ['posgrado', 'universitario', 'terciario', 'secundario']:
            for pattern in EducacionPatterns.NIVELES[nivel]:
                if re.search(pattern, text_lower):
                    return nivel

        return None

    @staticmethod
    def extract_estado(text: str) -> Optional[str]:
        """Extrae estado educativo - MEJORADO"""
        text_lower = text.lower()

        for estado, patterns in EducacionPatterns.ESTADOS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return estado

        return None

    @staticmethod
    def extract_carrera(text: str) -> Optional[str]:
        """NUEVO: Extrae carrera específica mencionada"""
        match = re.search(EducacionPatterns.CARRERA_PATTERN, text, re.IGNORECASE)
        if match:
            carrera = match.group(1).strip()
            # Filtrar carreras muy cortas (probablemente falsos positivos)
            if len(carrera) > 4:
                return carrera
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
    """Patrones para detectar idiomas requeridos - SIN CAMBIOS"""

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
    """Patrones para detectar skills técnicas - EXPANDIDO CON OFICIOS"""

    _skills_db = None
    _technical_patterns = None
    _soft_patterns = None
    _oficios_patterns = None

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
                    cls._technical_patterns.append(rf'\b{re.escape(skill)}\b')

            # Construir lista de patrones soft skills
            cls._soft_patterns = []
            for categoria, skills_list in cls._skills_db['soft_skills_expanded'].items():
                for skill in skills_list:
                    # Escapar caracteres especiales y crear pattern
                    escaped = re.escape(skill).replace(r'\ ', r'\s+')
                    cls._soft_patterns.append(escaped)

            # NUEVO: Patrones de oficios y habilidades técnicas básicas
            cls._oficios_patterns = [
                # Oficios técnicos
                r'\brefrigeración(?:\s+industrial)?\b',
                r'\belectricidad\b',
                r'\bsoldadura\b',
                r'\bcarpintería\b',
                r'\bplomería\b',
                r'\balbañilería\b',
                r'\bmecánica\b',
                r'\bmecanica\b',
                # Atención y servicios
                r'\batención\s+al\s+cliente\b',
                r'\bventas?\b',
                r'\bcajero?a?\b',
                r'\breposición\b',
                r'\breposicion\b',
                # Operación y logística
                r'\boperación\s+de\s+maquinaria\b',
                r'\bmanejo\s+de\s+montacargas\b',
                r'\blogística\b',
                r'\blogistica\b',
                r'\balmacén\b',
                r'\balmacen\b',
            ]

    @classmethod
    def extract_technical_skills(cls, text: str) -> List[str]:
        """Extrae skills técnicas (215 skills) - MEJORADO"""
        if cls._technical_patterns is None:
            cls._load_skills_database()

        text_lower = text.lower()
        skills = []

        # Skills del JSON
        for pattern in cls._technical_patterns:
            try:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                skills.extend(matches)
            except re.error:
                continue

        # NUEVO: Oficios y skills técnicas básicas
        for pattern in cls._oficios_patterns:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    skills.append(match.group(0))
            except re.error:
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
                continue

        return list(dict.fromkeys(skills))


class SalarioPatterns:
    """Patrones para detectar salario - IMPLEMENTADO"""

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
        Extrae salario (min, max, moneda) - IMPLEMENTADO

        Returns:
            (min_amount, max_amount, currency)
        """
        text_lower = text.lower()
        montos_encontrados = []
        moneda = 'ARS'  # Por defecto pesos argentinos

        for pattern in SalarioPatterns.MONTOS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()

                    # Si el patrón captura moneda (USD, ARS, etc.)
                    if len(groups) == 2 and groups[0] in ['USD', 'ARS', 'EUR', 'BRL']:
                        moneda = groups[0].upper()
                        monto_str = groups[1]
                    else:
                        monto_str = groups[0]

                    # Limpiar y convertir
                    monto_str = monto_str.replace('.', '').replace(',', '')

                    # Manejar "K" (miles)
                    if monto_str.endswith('k') or monto_str.endswith('K'):
                        monto = float(monto_str[:-1]) * 1000
                    else:
                        monto = float(monto_str)

                    montos_encontrados.append(monto)
                except (ValueError, IndexError):
                    continue

        if not montos_encontrados:
            return (None, None, None)

        # Si hay un rango, retornar min y max
        if len(montos_encontrados) >= 2:
            return (min(montos_encontrados), max(montos_encontrados), moneda)
        else:
            # Solo un monto encontrado
            return (montos_encontrados[0], None, moneda)


class JornadaPatterns:
    """Patrones para detectar jornada laboral - EXPANDIDO CON HORARIOS"""

    TIPOS = {
        'full_time': [
            r'\bfull\s*time\b',
            r'\btiempo\s+completo\b',
            r'\bjornada\s+completa\b',
            r'\b8\s*hs?\b',
            r'\b40\s*hs?\b'
        ],
        'part_time': [
            r'\bpart\s*time\b',
            r'\bmedio\s+tiempo\b',
            r'\b4\s*hs?\b'
        ],
        'por_proyecto': [
            r'\bpor\s+proyecto\b',
            r'\bproyecto\s+a\s+proyecto\b'
        ],
        'freelance': [
            r'\bfreelance\b',
            r'\baut[oó]nomo\b'
        ],
        'temporal': [
            r'\btemporal\b',
            r'\bcontrato\s+temporario\b'
        ],
        'pasantia': [
            r'\bpasant[íi]a\b',
            r'\binternship\b'
        ],
    }

    # NUEVO: Patrones para días de la semana
    DIAS_SEMANA = [
        r'lunes\s+a\s+viernes',
        r'lunes\s+a\s+sábados?',
        r'de\s+lunes\s+a\s+(?:viernes|sábado|sabado|domingo)',
        r'lun\.?\s*a\s*vie\.?',
    ]

    # NUEVO: Patrones para horarios específicos
    HORARIOS = [
        # "de 9 a 18hs", "9 a 18 hs", "de 9 a 18"
        r'de\s+(\d{1,2}(?::\d{2})?)\s*(?:a|hasta|hs?\s+a)\s+(\d{1,2}(?::\d{2})?)\s*hs?',
        r'(\d{1,2})\s*a\s*(\d{1,2})\s*hs?',
        # "9:00 a 18:00"
        r'(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})',
    ]

    # NUEVO: Patrones para turnos
    TURNOS = [
        r'turno\s+(mañana|tarde|noche|rotativos?)',
    ]

    FLEXIBLE = [
        r'horario\s+flexible',
        r'flexibilidad\s+horaria',
        r'flexible\s+schedule',
    ]

    @staticmethod
    def extract_tipo(text: str) -> Optional[str]:
        """Extrae tipo de jornada - MEJORADO"""
        text_lower = text.lower()

        # Buscar tipo de jornada
        for tipo, patterns in JornadaPatterns.TIPOS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return tipo

        # NUEVO: Si tiene horario específico, asumir full_time
        if JornadaPatterns.extract_horario(text):
            return 'full_time'

        return None

    @staticmethod
    def extract_horario(text: str) -> Optional[str]:
        """NUEVO: Extrae horario específico si está mencionado"""
        text_lower = text.lower()

        for pattern in JornadaPatterns.HORARIOS:
            match = re.search(pattern, text_lower)
            if match:
                # Retornar el horario encontrado
                return match.group(0)

        return None

    @staticmethod
    def extract_dias(text: str) -> Optional[str]:
        """NUEVO: Extrae días de trabajo si están mencionados"""
        text_lower = text.lower()

        for pattern in JornadaPatterns.DIAS_SEMANA:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)

        return None

    @staticmethod
    def is_flexible(text: str) -> bool:
        """Determina si el horario es flexible"""
        text_lower = text.lower()

        for pattern in JornadaPatterns.FLEXIBLE:
            if re.search(pattern, text_lower):
                return True

        return False
