# -*- coding: utf-8 -*-
"""
Regex Patterns v3 - ULTRA-AGRESIVO para alcanzar 95% de efectividad
===================================================================

VERSION: 3.0
FECHA: 2025-11-01
OBJETIVO: Aumentar de 37.6% a 65-70% de efectividad

Cambios principales respecto a v2:
- Experiencia: Detección SIN años específicos (asignar exp = 1)
- Experiencia: Inferencia desde adjetivos ("amplia experiencia" = 5+ años)
- Educación: Detección por profesión ("Abogado" → universitario completo)
- Educación: "Matrícula habilitante" → profesional
- Jornada: Horarios sin "hs" (9 a 18, 17 a 01)
- Idiomas: Detección implícita ("bilingual" → inglés avanzado)
- Idiomas: Sin nivel → asumir intermedio
- Skills: 200+ oficios argentinos nuevos
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ExperienciaPatterns:
    """Patrones para detectar experiencia laboral - ULTRA-AGRESIVO v3"""

    # Patrones para años específicos de experiencia
    ANIOS_EXPERIENCIA = [
        # "3+ años", "3 + años"
        r'(\d+)\s*\+\s*(?:años?|anios?)',

        # "mínimo/mínima 3 años" - con género
        r'(?:mínim[oa]s?|minim[oa]s?|al menos|como mínim[oa]?|como minim[oa]?)\s*(\d+)\s*(?:años?|anios?)',

        # "3 a 5 años", "entre 3 y 5 años", "de 3 a 5 años"
        r'(?:entre|de)\s*(\d+)\s*(?:a|y)\s*(\d+)\s*(?:años?|anios?)',

        # "3 años de experiencia"
        r'(\d+)\s*(?:años?|anios?)\s+de\s+experiencia',

        # "experiencia de 3 años"
        r'experiencia\s+de\s+(\d+)\s*(?:años?|anios?)',

        # "experiencia: 3 años", "experiencia requerida: 3 años"
        r'experiencia\s*(?:requerida|necesaria)?:\s*(\d+)\s*(?:años?|anios?)',

        # "se requieren 3 años"
        r'se\s+requieren?\s+(\d+)\s*(?:años?|anios?)',

        # "con 3 años de experiencia"
        r'con\s+(\d+)\s*(?:años?|anios?)\s+de\s+experiencia',
    ]

    # NUEVO v3: Patrones de experiencia SIN años específicos
    EXPERIENCIA_SIN_ANIOS = [
        # "experiencia previa", "experiencia comprobada"
        r'\bexperiencia\s+(?:previa|comprobada|demostrable|sólida|solida|confirmada)\b',

        # "con experiencia en/como"
        r'\bcon\s+experiencia\s+(?:en|como|de)\b',

        # "se valorará/requiere experiencia"
        r'\b(?:se\s+)?(?:valorará?|requiere|necesita|busca)\s+experiencia\b',

        # "experiencia en el área/rubro/sector"
        r'\bexperiencia\s+en\s+(?:el\s+)?(?:área|rubro|sector|puesto)\b',

        # "tener experiencia", "poseer experiencia"
        r'\b(?:tener|poseer|contar\s+con)\s+experiencia\b',
    ]

    # FASE 2.7: Experiencia implícita (asignar 1 año por defecto)
    EXPERIENCIA_IMPLICITA = [
        r'\bacredit[ae]n?\s+experiencia\b',          # "acrediten experiencia"
        r'\bexperimentad[oa]s?\b',                    # "experimentado/a"
        r'\bcon\s+conocimiento\b',                    # "con conocimiento"
        r'\borientamos\s+(?:la\s+)?búsqueda\b',      # "orientamos la búsqueda"
        r'\bpersona[s]?\s+con\s+experiencia\b',       # "personas con experiencia"
        r'\brequerimos\s+experiencia\b',              # "requerimos experiencia"
        r'\bnecesaria\s+experiencia\b',               # "necesaria experiencia"
    ]

    # NUEVO v3: Inferencia de experiencia desde adjetivos
    EXPERIENCIA_DESCRIPTIVA = {
        # Mucha experiencia → 5+ años
        'amplia': 5,
        'vasta': 5,
        'extensa': 5,
        'sólida': 3,
        'solida': 3,
        'significativa': 3,

        # Poca experiencia → 0-1 años
        'poca': 0,
        'inicial': 0,
        'básica': 0,
        'basica': 0,
    }

    # Niveles en título
    NIVELES_TITULO = {
        r'\b(?:trainee|pasante|becario)\b': (0, 0),
        r'\bjunior\b': (0, 2),
        r'\b(?:semi\s*senior|semi-senior|ssr)\b': (2, 5),
        r'\b(?:senior|sr\.?)\b': (5, None),
        r'\b(?:lead|líder|lider|team\s+lead)\b': (7, None),
        r'\b(?:manager|gerente|jefe)\b': (10, None),
    }

    @staticmethod
    def extract_years(text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae años de experiencia (min, max) - VERSION ULTRA-AGRESIVA v3

        Returns:
            (min_years, max_years) o (None, None)
        """
        text_lower = text.lower()

        # 1. Buscar años específicos
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

        # 2. NUEVO v3: Inferir de nivel en título
        for pattern, (min_exp, max_exp) in ExperienciaPatterns.NIVELES_TITULO.items():
            if re.search(pattern, text_lower):
                return (min_exp, max_exp)

        # 3. NUEVO v3: Inferir de adjetivos descriptivos
        for adjetivo, anios in ExperienciaPatterns.EXPERIENCIA_DESCRIPTIVA.items():
            pattern = rf'\b{adjetivo}\s+experiencia\b'
            if re.search(pattern, text_lower):
                return (anios, None)

        # 4. NUEVO v3: Experiencia mencionada SIN años → Asumir 1 año
        for pattern in ExperienciaPatterns.EXPERIENCIA_SIN_ANIOS:
            if re.search(pattern, text_lower):
                return (1, None)

        # 5. FASE 2.7: Si no se encontraron años, buscar experiencia implícita
        for pattern in ExperienciaPatterns.EXPERIENCIA_IMPLICITA:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return (1, None)  # Asignar 1 año mínimo por defecto

        return (None, None)

    @staticmethod
    def extract_area(text: str) -> Optional[str]:
        """Extrae área de experiencia"""
        text_lower = text.lower()

        AREA_PATTERNS = [
            r'experiencia\s+(?:en|con)\s+([^.,;:\n]{5,50})',
            r'(?:conocimientos?|experiencia)\s+(?:previos?\s+)?(?:en|de)\s+([^.,;:\n]{5,50})',
        ]

        for pattern in AREA_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                area = match.group(1).strip()
                if len(area) > 5:
                    return area

        return None


class EducacionPatterns:
    """Patrones para detectar educación requerida - ULTRA-AGRESIVO v3"""

    # Niveles educativos expandidos
    NIVELES = {
        'secundario': [
            r'\bsecundari[oa]s?\s+complet[oa]s?\b',
            r'\bestudios?\s+secundari[oa]s?\s+complet[oa]s?\b',
            r'\bbachiller\b',
            r'\bestudiante\s+secundari[oa]\b',
        ],
        'terciario': [
            r'\btercia?ri[oa]s?\s+complet[oa]s?\b',
            r'\bestudios?\s+tercia?ri[oa]s?\s+complet[oa]s?\b',
            r'\btécnico\s+(?:superior)?\b',
            r'\btecnico\s+(?:superior)?\b',
        ],
        'universitario': [
            r'\buniversitari[oa]s?\s+complet[oa]s?\b',
            r'\bestudios?\s+universitari[oa]s?\s+complet[oa]s?\b',
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

    # NUEVO v3: Profesiones que implican universitario completo
    PROFESIONES_UNIVERSITARIAS = [
        r'\babogad[oa]\/[oa]\b',
        r'\babogad[oa]\b',
        r'\bingeni?er[oa]\/[oa]\b',
        r'\bingeni?er[oa]\b',
        r'\bcontador\s+público\b',
        r'\bcontador\s+publico\b',
        r'\bcontadora?\b',
        r'\bmédico\/a\b',
        r'\bmedico\/a\b',
        r'\bmédico\b',
        r'\bmedico\b',
        r'\barquitecto\/a\b',
        r'\barquitecto\b',
        r'\blicenciad[oa]\/[oa]\b',
        r'\blicenciad[oa]\b',
        r'\bpsicólogo\/a\b',
        r'\bpsicologo\/a\b',
        # FASE 2.6: Más patrones de profesiones con contexto
        r'(?:abogad[oa]|ingeni?er[oa]|médico|medico|contador|arquitecto|licenciad[oa])\/[oa]\s+(?:con|recibid)',
        r'profesional\s+(?:recibid|graduad)[oa]',
        r'título\s+(?:profesional|habilitante)',
        r'titulo\s+(?:profesional|habilitante)',
    ]

    # NUEVO v3: Matrícula profesional
    MATRICULA_PATTERNS = [
        r'\bmatrícula\s+(?:habilitante|profesional|al\s+día|vigente)\b',
        r'\bmatriculado\/a\b',
        r'\btítulo\s+habilitante\b',
        r'\btitulo\s+habilitante\b',
    ]

    # Estados educativos expandidos
    ESTADOS = {
        'completo': [
            r'\bcomplet[oa]s?\b',
            r'\bgraduado\b',
            r'\bfinalizado\b',
            r'\brecibid[oa]\b',
            r'\begresad[oa]\b',
            # FASE 2.6: Más variantes de graduado
            r'\brecién\s+recibid[oa][s]?\b',
            r'\brecien\s+recibid[oa][s]?\b',
            r'\bgraduado[s]?\s+(?:universitario[s]?|terciario[s]?)\b',
            r'\bprofesional\s+recibid[oa]\b',
        ],
        'en_curso': [
            r'\ben\s+curso\b',
            r'\bestudiando\b',
            r'\bcursando\b',
            r'\bestudiante\s+(?:de|en)\b',
            r'\bavanzad[oa]\b',
            r'\búltimo\s+año\b',
            r'\bultimo\s+año\b',
            # FASE 2.6: Estudiantes avanzados
            r'\bestudiante[s]?\s+(?:avanzado[s]?|de\s+últimos?\s+años?)\b',
            r'\bestudiante[s]?\s+(?:avanzado[s]?|de\s+ultimos?\s+años?)\b',
        ],
        'incompleto': [
            r'\bincomplete\b',
        ],
        # FASE 2.6: Estado ambiguo (estudiantes o graduados) - acepta ambos
        'ambiguo': [
            r'\bestudiante[s]?\s+(?:o|y|\/)\s+graduado[s]?\b',
            r'\bgraduado[s]?\s+(?:o|y|\/)\s+estudiante[s]?\b',
        ],
    }

    # Patrón para extraer carrera específica (expandido)
    CARRERA_PATTERN = r'(?:estudiante|cursando|carrera|licenciatura|ingeniería|ingenieria|graduad[oa])\s+(?:de|en|la\s+carrera\s+de)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-záéíóúñA-ZÁÉÍÓÚÑ]+){0,4})'

    # Excluyente
    EXCLUYENTE = [
        r'\bexcluyente\b',
        r'\bobligatorio\b',
        r'\bindispensable\b',
        r'\brequisito\b',
        r'\bmandatorio\b',
    ]

    @staticmethod
    def extract_nivel(text: str) -> Optional[str]:
        """Extrae nivel educativo más alto mencionado - v3 ULTRA-AGRESIVO"""
        text_lower = text.lower()

        # NUEVO v3: Detectar profesiones → universitario completo
        for pattern in EducacionPatterns.PROFESIONES_UNIVERSITARIAS:
            if re.search(pattern, text_lower):
                return 'universitario'

        # NUEVO v3: Detectar matrícula → universitario completo
        for pattern in EducacionPatterns.MATRICULA_PATTERNS:
            if re.search(pattern, text_lower):
                return 'universitario'

        # Buscar niveles en orden de prioridad
        for nivel in ['posgrado', 'universitario', 'terciario', 'secundario']:
            for pattern in EducacionPatterns.NIVELES[nivel]:
                if re.search(pattern, text_lower):
                    return nivel

        return None

    @staticmethod
    def extract_estado(text: str) -> Optional[str]:
        """Extrae estado educativo"""
        text_lower = text.lower()

        # FASE 2.6: Priorizar 'ambiguo' primero (estudiantes o graduados)
        # Retornar 'en_curso' como default más conservador
        if 'ambiguo' in EducacionPatterns.ESTADOS:
            for pattern in EducacionPatterns.ESTADOS['ambiguo']:
                if re.search(pattern, text_lower):
                    return 'en_curso'  # Más conservador - acepta estudiantes

        for estado, patterns in EducacionPatterns.ESTADOS.items():
            if estado == 'ambiguo':  # Ya chequeado arriba
                continue
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return estado

        return None

    @staticmethod
    def extract_carrera(text: str) -> Optional[str]:
        """Extrae carrera específica mencionada"""
        match = re.search(EducacionPatterns.CARRERA_PATTERN, text, re.IGNORECASE)
        if match:
            carrera = match.group(1).strip()
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
    """Patrones para detectar idiomas requeridos - ULTRA-AGRESIVO v3"""

    # Idiomas comunes
    IDIOMAS = {
        'ingles': [
            r'\binglé?s\b',
            r'\benglish\b',
            r'\bing\b',  # NUEVO: Abreviatura
        ],
        'portugues': [
            r'\bportugué?s\b',
            r'\bportuguese\b',
        ],
        'aleman': [
            r'\balemá?n\b',
            r'\bgerman\b',
        ],
        'frances': [
            r'\bfrancé?s\b',
            r'\bfrench\b',
        ],
        'italiano': [
            r'\bitaliano\b',
            r'\bitalian\b',
        ],
    }

    # Niveles expandidos
    NIVELES = {
        'basico': [
            r'\bbá?sico\b',
            r'\bbasic\b',
            r'\belementary\b',
            r'\bprincipiante\b',
        ],
        'intermedio': [
            r'\bintermedio\b',
            r'\bintermediate\b',
        ],
        'avanzado': [
            r'\bavanzado\b',
            r'\badvanced\b',
            r'\bfluent\b',
            r'\bfluido\b',
        ],
        'nativo': [
            r'\bnativo\b',
            r'\bnative\b',
        ],
        'bilingue': [
            r'\bbilingü?e\b',
            r'\bbilingual\b',
        ],
    }

    # NUEVO v3: Implícitos
    IMPLICITOS = [
        # Si encuentra estas palabras, asumir inglés avanzado
        (r'\bbilingual\b', 'ingles', 'avanzado'),
        (r'\bbilingüe\b', 'ingles', 'avanzado'),
        (r'\binternational\b', 'ingles', 'intermedio'),
        (r'\bmultinacional\b', 'ingles', 'intermedio'),
        (r'\bglobal\b', 'ingles', 'intermedio'),
    ]

    @staticmethod
    def extract_idiomas(text: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extrae idiomas y niveles - VERSION ULTRA-AGRESIVA v3

        Returns:
            Lista de tuplas (idioma, nivel)
        """
        text_lower = text.lower()
        idiomas_encontrados = []

        # 1. NUEVO v3: Detectar idiomas implícitos
        for pattern, idioma, nivel in IdiomasPatterns.IMPLICITOS:
            if re.search(pattern, text_lower):
                idiomas_encontrados.append((idioma, nivel))

        # 2. Buscar idiomas explícitos
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

                        # NUEVO v3: Si no encontró nivel, asumir intermedio
                        if nivel is None:
                            nivel = 'intermedio'

                        idiomas_encontrados.append((idioma, nivel))
                        break

        # Deduplicar manteniendo orden
        return list(dict.fromkeys(idiomas_encontrados))


class SkillsPatterns:
    """Patrones para detectar skills técnicas - ULTRA-EXPANDIDO v3"""

    _skills_db = None
    _technical_patterns = None
    _soft_patterns = None
    _oficios_patterns = None

    # FASE 2.7: Soft skills adicionales
    SOFT_SKILLS_EXPANDED = [
        # Perfil comercial
        'perfil comercial', 'orientación comercial', 'orientacion comercial',
        'vocación comercial', 'vocacion comercial',

        # Habilidades de venta/negociación
        'capacidad de negociación', 'capacidad de negociacion',
        'habilidad de negociación', 'habilidad de negociacion',
        'cierre de venta', 'cierre de ventas',

        # Presentación personal
        'buena presencia', 'excelente presencia',
        'buena dicción', 'diccion clara',

        # Autonomía
        'trabajo independiente', 'capacidad de trabajar solo',
        'autonomía', 'autonomia', 'autónomo', 'autonomo',

        # Organización
        'organizado', 'organizada', 'organizacion',
        'planificación', 'planificacion',

        # Compromiso
        'comprometido', 'comprometida', 'compromiso',
        'responsabilidad', 'responsable',
    ]

    @classmethod
    def _load_skills_database(cls):
        """Carga la base de datos de skills desde JSON (ubicación: config/skills_database.json)"""
        if cls._skills_db is None:
            # Ruta al config/ en la raíz del proyecto (4 niveles arriba desde patterns/)
            config_dir = Path(__file__).parent.parent.parent.parent / "config"
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
                    escaped = re.escape(skill).replace(r'\ ', r'\s+')
                    cls._soft_patterns.append(escaped)

            # NUEVO v3: MASIVA expansión de oficios argentinos (200+ términos)
            cls._oficios_patterns = [
                # === CONSTRUCCIÓN Y MANTENIMIENTO ===
                r'\brefrigeración(?:\s+industrial)?\b',
                r'\belectricidad\b',
                r'\belectricista\b',
                r'\bsoldadura\b',
                r'\bsoldador\b',
                r'\bcarpintería\b',
                r'\bcarpintero\b',
                r'\bplomería\b',
                r'\bplomero\b',
                r'\bgasista\b',
                r'\bgas\s+natural\b',
                r'\balbañilería\b',
                r'\balbañil\b',
                r'\bpintura\b',
                r'\bpintor\b',
                r'\byeso\b',
                r'\byesero\b',
                r'\bcolocación\s+de\s+pisos\b',
                r'\bcolocador\b',
                r'\bherrería\b',
                r'\bherrero\b',
                r'\btornería\b',
                r'\btornero\b',
                r'\bmecánica\s+(?:automotriz|industrial)?\b',
                r'\bmecanica\s+(?:automotriz|industrial)?\b',
                r'\bmecánico\b',
                r'\bmecanico\b',
                r'\bmantenimiento\s+(?:industrial|edilicio|general)\b',

                # === SERVICIOS GENERALES ===
                r'\batención\s+al\s+cliente\b',
                r'\batencion\s+al\s+cliente\b',
                r'\bventas?\b',
                r'\bvendedor\b',
                r'\bcajero?a?\b',
                r'\breposición\b',
                r'\breposicion\b',
                r'\breponedor\b',
                r'\blimpieza\s+(?:industrial|profunda)?\b',
                r'\bseguridad\b',
                r'\bvigilancia\b',
                r'\bguardia\s+de\s+seguridad\b',
                r'\bportería\b',
                r'\bportero\b',
                r'\bsereno\b',
                r'\bjardinería\b',
                r'\bjardineria\b',
                r'\bjardinero\b',

                # === LOGÍSTICA Y TRANSPORTE ===
                r'\blogística\b',
                r'\blogistica\b',
                r'\balmacén\b',
                r'\balmacen\b',
                r'\balmacenero\b',
                r'\bdeposito\b',
                r'\bdepósito\b',
                r'\boperación\s+de\s+maquinaria\b',
                r'\bmanejo\s+de\s+montacargas\b',
                r'\bmontacargas\b',
                r'\bautoelevador\b',
                r'\bchofer\b',
                r'\bconductor\b',
                r'\brepartidor\b',
                r'\bdelivery\b',
                r'\bmensajería\b',
                r'\bmensajeria\b',
                r'\bcadete\b',

                # === GASTRONOMÍA ===
                r'\bcocina\b',
                r'\bcocinero\b',
                r'\bchef\b',
                r'\bpastelería\b',
                r'\bpasteleria\b',
                r'\bpanadería\b',
                r'\bpanaderia\b',
                r'\bbarista\b',
                r'\bbartender\b',
                r'\bmozo\b',
                r'\bcamarero\b',
                r'\bmaitre\b',

                # === SALUD ===
                r'\benfermería\b',
                r'\benfermeria\b',
                r'\benfermero\b',
                r'\bauxiliar\s+de\s+enfermería\b',
                r'\bcuidado\s+de\s+(?:adultos\s+mayores|ancianos|pacientes)\b',
                r'\bcuidador\b',
                r'\basistente\s+geriátrico\b',
                r'\basistente\s+geriatrico\b',

                # === BELLEZA Y ESTÉTICA ===
                r'\bpeluquería\b',
                r'\bpeluqueria\b',
                r'\bpeluquero\b',
                r'\bestética\b',
                r'\bestetica\b',
                r'\bmanicura\b',
                r'\bpedicura\b',
                r'\bmaquillaje\b',
                r'\bmaquillador\b',

                # === ADMINISTRACIÓN Y OFICINA ===
                r'\badministración\b',
                r'\badministracion\b',
                r'\bsecretariado\b',
                r'\bsecretaria\b',
                r'\brecepción\b',
                r'\brecepcion\b',
                r'\brecepcionista\b',
                r'\basistente\s+administrativo\b',
                r'\bdata\s+entry\b',
                r'\bcarga\s+de\s+datos\b',
                r'\barchivo\b',

                # === CONTABILIDAD Y FINANZAS ===
                r'\bcontabilidad\b',
                r'\bliquidación\s+de\s+sueldos\b',
                r'\bliquidacion\s+de\s+sueldos\b',
                r'\bimpuestos\b',
                r'\bart\b',  # ARTs
                r'\bnómina\b',
                r'\bnomina\b',
                r'\btesorería\b',
                r'\btesoreria\b',

                # === RECURSOS HUMANOS ===
                r'\bselección\s+de\s+personal\b',
                r'\bseleccion\s+de\s+personal\b',
                r'\breclutamiento\b',
                r'\bcapacitación\b',
                r'\bcapacitacion\b',
                r'\brelaciones\s+laborales\b',

                # === MARKETING Y VENTAS ===
                r'\bmarketing\s+digital\b',
                r'\bredes\s+sociales\b',
                r'\bcommunity\s+manager\b',
                r'\bseo\b',
                r'\bsem\b',
                r'\bgoogle\s+analytics\b',
                r'\bgoogle\s+ads\b',
                r'\bfacebook\s+ads\b',

                # === TECNOLOGÍA (Básicos) ===
                r'\bsoporte\s+técnico\b',
                r'\bsoporte\s+tecnico\b',
                r'\bmesa\s+de\s+ayuda\b',
                r'\bhelp\s+desk\b',
                r'\breparación\s+de\s+(?:pc|computadoras)\b',
                r'\breparacion\s+de\s+(?:pc|computadoras)\b',
                r'\bredes\s+(?:informáticas|informaticas)\b',

                # === PRODUCCIÓN ===
                r'\boperario\s+de\s+(?:producción|maquina|linea)\b',
                r'\boperario\s+de\s+(?:produccion|maquina|linea)\b',
                r'\bcontrol\s+de\s+calidad\b',
                r'\binspección\b',
                r'\binspeccion\b',
                r'\bensamblaje\b',
                r'\bembalaje\b',
                r'\bpacking\b',
            ]

    @classmethod
    def extract_technical_skills(cls, text: str) -> List[str]:
        """Extrae skills técnicas - ULTRA-EXPANDIDO v3"""
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

        # NUEVO v3: Oficios expandidos masivamente
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
        """Extrae soft skills"""
        if cls._soft_patterns is None:
            cls._load_skills_database()

        text_lower = text.lower()
        skills = []

        # Skills del JSON
        for pattern in cls._soft_patterns:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    skills.append(match.group(0))
            except re.error:
                continue

        # FASE 2.7: Añadir skills expandidas
        for skill in cls.SOFT_SKILLS_EXPANDED:
            if skill in text_lower:
                # Capitalizar correctamente
                skill_capitalized = skill.title()
                if skill_capitalized not in skills:
                    skills.append(skill_capitalized)

        return list(dict.fromkeys(skills))


class SalarioPatterns:
    """Patrones para detectar salario - SIN CAMBIOS (Bumeran no publica salarios)"""

    MONTOS = [
        r'\$\s*(\d{1,3}(?:[.,]\d{3})*(?:[kK])?)',
        r'(USD|ARS|EUR|BRL)\s+(\d{1,3}(?:[.,]\d{3})*)',
        r'(?:salario|sueldo|remuneraci[oó]n):\s*\$?\s*(\d{1,3}(?:[.,]\d{3})*)',
    ]

    @staticmethod
    def extract_montos(text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Extrae salario (min, max, moneda)"""
        text_lower = text.lower()
        montos_encontrados = []
        moneda = 'ARS'

        for pattern in SalarioPatterns.MONTOS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()

                    if len(groups) == 2 and groups[0] in ['USD', 'ARS', 'EUR', 'BRL']:
                        moneda = groups[0].upper()
                        monto_str = groups[1]
                    else:
                        monto_str = groups[0]

                    monto_str = monto_str.replace('.', '').replace(',', '')

                    if monto_str.endswith('k') or monto_str.endswith('K'):
                        monto = float(monto_str[:-1]) * 1000
                    else:
                        monto = float(monto_str)

                    montos_encontrados.append(monto)
                except (ValueError, IndexError):
                    continue

        if not montos_encontrados:
            return (None, None, None)

        if len(montos_encontrados) >= 2:
            return (min(montos_encontrados), max(montos_encontrados), moneda)
        else:
            return (montos_encontrados[0], None, moneda)


class JornadaPatterns:
    """Patrones para detectar jornada laboral - ULTRA-EXPANDIDO v3"""

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

    # Días de la semana
    DIAS_SEMANA = [
        r'lunes\s+a\s+viernes',
        r'lunes\s+a\s+sábados?',
        r'de\s+lunes\s+a\s+(?:viernes|sábado|sabado|domingo)',
        r'lun\.?\s*a\s*vie\.?',
    ]

    # NUEVO v3: Horarios expandidos SIN "hs" obligatorio
    HORARIOS = [
        # "de 9 a 18hs", "9 a 18 hs", "de 9 a 18"
        r'de\s+(\d{1,2}(?::\d{2})?)\s*(?:a|hasta|hs?\s+a)\s+(\d{1,2}(?::\d{2})?)\s*hs?',
        r'(\d{1,2})\s*a\s*(\d{1,2})\s*hs?',
        # "9:00 a 18:00"
        r'(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})',
        # NUEVO v3: "horario de 9 a 18" (SIN hs)
        r'horario\s*(?:de)?\s*(\d{1,2}(?::\d{2})?)\s*(?:a|hasta|-)\s*(\d{1,2}(?::\d{2})?)',
        # NUEVO v3: "17 a 01" (sin hs)
        r'\b(\d{1,2})\s*a\s*(\d{1,2})\b',
    ]

    # Turnos
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
        """Extrae tipo de jornada"""
        text_lower = text.lower()

        for tipo, patterns in JornadaPatterns.TIPOS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return tipo

        # Si tiene horario específico, asumir full_time
        if JornadaPatterns.extract_horario(text):
            return 'full_time'

        return None

    @staticmethod
    def extract_horario(text: str) -> Optional[str]:
        """Extrae horario específico - ULTRA-AGRESIVO v3"""
        text_lower = text.lower()

        for pattern in JornadaPatterns.HORARIOS:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)

        return None

    @staticmethod
    def extract_dias(text: str) -> Optional[str]:
        """Extrae días de trabajo"""
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
