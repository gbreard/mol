# -*- coding: utf-8 -*-
"""
Regex Patterns v4 - Arquitectura Anti-Alucinación
==================================================

VERSION: 4.0
FECHA: 2025-11-27
OBJETIVO: Capa 0 del pipeline - extraer 60-70% de campos con 100% precisión

Hereda todo de v3 y agrega 7 clases nuevas:
- EdadPatterns: edad con tolerancia a espacios
- LicenciaPatterns: licencia de conducir + categoría
- ContratacionPatterns: contratación inmediata
- IndexacionPatterns: indexación salarial IPC
- EmpresaPatterns: detectar consultoras vs empresa directa
- HeaderPatterns: extraer datos del header "Clave: valor"
- BeneficiosPatterns: obra social, ART, etc.
- ViajesPatterns: disponibilidad de viajes
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Importar todas las clases de v3
from regex_patterns_v3 import (
    ExperienciaPatterns,
    EducacionPatterns,
    IdiomasPatterns,
    SkillsPatterns,
    SalarioPatterns,
    JornadaPatterns
)


# =============================================================================
# NUEVAS CLASES v4
# =============================================================================

class EdadPatterns:
    """Extrae edad con tolerancia a espacios: '1 8 y 3 5' → (18, 35)"""

    # Patrones para edad con posibles espacios
    PAT_EDADES_ENTRE = re.compile(
        r'entre\s+(\d[\d ]*)\s*y\s+(\d[\d ]*)\s*años',
        flags=re.I
    )

    PAT_EDADES_DE_A = re.compile(
        r'de\s+(\d[\d ]*)\s*a\s+(\d[\d ]*)\s*años',
        flags=re.I
    )

    PAT_EDAD_MINIMA = re.compile(
        r'(?:mayor|mínimo|minimo|desde)\s+(?:de\s+)?(\d[\d ]*)\s*años',
        flags=re.I
    )

    PAT_EDAD_MAXIMA = re.compile(
        r'(?:menor|máximo|maximo|hasta)\s+(?:de\s+)?(\d[\d ]*)\s*años',
        flags=re.I
    )

    @staticmethod
    def extraer_edades(texto: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae rango de edad con tolerancia a espacios.
        "entre 1 8 y 3 5 años" → (18, 35)
        """
        # Buscar rango "entre X y Y"
        m = EdadPatterns.PAT_EDADES_ENTRE.search(texto)
        if m:
            edad_min = int(m.group(1).replace(" ", ""))
            edad_max = int(m.group(2).replace(" ", ""))
            return edad_min, edad_max

        # Buscar rango "de X a Y"
        m = EdadPatterns.PAT_EDADES_DE_A.search(texto)
        if m:
            edad_min = int(m.group(1).replace(" ", ""))
            edad_max = int(m.group(2).replace(" ", ""))
            return edad_min, edad_max

        # Buscar solo mínimo o máximo
        edad_min = None
        edad_max = None

        m = EdadPatterns.PAT_EDAD_MINIMA.search(texto)
        if m:
            edad_min = int(m.group(1).replace(" ", ""))

        m = EdadPatterns.PAT_EDAD_MAXIMA.search(texto)
        if m:
            edad_max = int(m.group(1).replace(" ", ""))

        return edad_min, edad_max


class LicenciaPatterns:
    """Detecta licencia de conducir + categoría"""

    PAT_REGISTRO_CON_CATEGORIA = re.compile(
        r'(?:registro|licencia|carnet)\s+(?:de\s+)?conducir.*?categor[ií]a\s*([A-Z][\d]?)',
        flags=re.I
    )

    PAT_CATEGORIA_PRIMERO = re.compile(
        r'categor[ií]a\s*([A-Z][\d]?).*?(?:registro|licencia|carnet)',
        flags=re.I
    )

    PAT_REGISTRO_SIMPLE = re.compile(
        r'(?:registro|licencia|carnet)\s+(?:de\s+)?conducir',
        flags=re.I
    )

    # Categorías conocidas
    PAT_CATEGORIA_SUELTA = re.compile(
        r'\b(A1|A2|A3|B1|B2|C1|C2|D1|D2|E1|E2|E3)\b',
        flags=re.I
    )

    @staticmethod
    def extraer_registro(texto: str) -> Tuple[bool, str]:
        """
        Detecta si requiere licencia y qué categoría.
        Returns: (requiere_licencia, categoria)
        """
        # Buscar registro con categoría explícita
        m = LicenciaPatterns.PAT_REGISTRO_CON_CATEGORIA.search(texto)
        if m:
            categoria = m.group(1).upper().replace(" ", "")
            return True, categoria

        # Buscar categoría antes del registro
        m = LicenciaPatterns.PAT_CATEGORIA_PRIMERO.search(texto)
        if m:
            categoria = m.group(1).upper().replace(" ", "")
            return True, categoria

        # Buscar registro simple (sin categoría)
        if LicenciaPatterns.PAT_REGISTRO_SIMPLE.search(texto):
            # Intentar encontrar categoría suelta cerca
            m = LicenciaPatterns.PAT_CATEGORIA_SUELTA.search(texto)
            if m:
                return True, m.group(1).upper()
            return True, ""

        return False, ""


class ContratacionPatterns:
    """Detecta contratación inmediata y otros estados"""

    PATRONES_INMEDIATA = [
        r'contrataci[óo]n(?:\s+es)?\s+inmediata',
        r'incorporaci[óo]n\s+inmediata',
        r'ingreso\s+inmediato',
        r'inicio\s+inmediato',
        r'disponibilidad\s+inmediata',
        r'comenzar\s+(?:de\s+)?inmediato',
        r'empezar\s+(?:de\s+)?inmediato',
    ]

    @staticmethod
    def es_inmediata(texto: str) -> bool:
        """Detecta si es contratación inmediata"""
        texto_lower = texto.lower()
        for patron in ContratacionPatterns.PATRONES_INMEDIATA:
            if re.search(patron, texto_lower):
                return True
        return False


class IndexacionPatterns:
    """Detecta indexación salarial (IPC, paritarias, etc.)"""

    PAT_IPC = re.compile(r'[ií]ndice\s+(?:de\s+)?(?:precios|ipc)', flags=re.I)
    PAT_PARITARIAS = re.compile(r'paritarias?', flags=re.I)
    PAT_INFLACION = re.compile(r'ajust[ea].*inflaci[óo]n', flags=re.I)
    PAT_FRECUENCIA = re.compile(r'cada\s+(\d+)\s+mes(?:es)?', flags=re.I)
    PAT_TRIMESTRAL = re.compile(r'trimestral(?:mente)?', flags=re.I)
    PAT_SEMESTRAL = re.compile(r'semestral(?:mente)?', flags=re.I)

    @staticmethod
    def extraer_indexacion(texto: str) -> Dict[str, Any]:
        """
        Detecta indexación salarial.
        Returns: {"tiene": bool, "indice": str|None, "frecuencia_meses": int|None}
        """
        texto_lower = texto.lower()

        # Detectar tipo de índice
        indice = None
        if IndexacionPatterns.PAT_IPC.search(texto):
            indice = "IPC"
        elif IndexacionPatterns.PAT_PARITARIAS.search(texto):
            indice = "Paritarias"
        elif IndexacionPatterns.PAT_INFLACION.search(texto):
            indice = "Inflación"

        if not indice:
            return {"tiene": False, "indice": None, "frecuencia_meses": None}

        # Detectar frecuencia
        frecuencia = None
        m = IndexacionPatterns.PAT_FRECUENCIA.search(texto_lower)
        if m:
            frecuencia = int(m.group(1))
        elif IndexacionPatterns.PAT_TRIMESTRAL.search(texto_lower):
            frecuencia = 3
        elif IndexacionPatterns.PAT_SEMESTRAL.search(texto_lower):
            frecuencia = 6

        return {"tiene": True, "indice": indice, "frecuencia_meses": frecuencia}


class EmpresaPatterns:
    """Detecta si es consultora vs empresa directa"""

    CONSULTORAS_CONOCIDAS = [
        # Grandes consultoras internacionales
        'randstad', 'manpower', 'adecco', 'kelly services', 'robert half',
        # Consultoras argentinas conocidas
        'ghidini', 'grupo sel', 'zivot', 'vocare', 'sesa select',
        'auren', 'bdo', 'pwc', 'deloitte', 'kpmg', 'ernst', 'ey ',
        # Palabras clave genéricas
        'consultora', 'selectora', 'reclutamiento', 'headhunter',
        'recruiting', 'staffing', 'recursos humanos', 'rrhh',
        'selección de personal', 'seleccion de personal',
        'búsqueda ejecutiva', 'busqueda ejecutiva',
        # Portales (cuando publican ellos)
        'zonajobs', 'bumeran', 'computrabajo',
    ]

    # Patrones que indican que hay una empresa cliente
    PATRONES_CLIENTE = [
        r'para\s+(?:importante|reconocida)\s+empresa',
        r'cliente\s+(?:del\s+)?(?:rubro|sector)',
        r'búsqueda\s+(?:para|de)\s+(?:nuestro\s+)?cliente',
        r'busqueda\s+(?:para|de)\s+(?:nuestro\s+)?cliente',
        r'empresa\s+(?:líder|lider)\s+(?:del|en)',
    ]

    @staticmethod
    def detectar_consultora(texto: str, empresa: str) -> Optional[str]:
        """
        Detecta si la empresa que publica es consultora.
        Returns: nombre de la consultora si detecta, None si es empresa directa
        """
        texto_combined = (texto + " " + empresa).lower()

        # Buscar consultoras conocidas
        for consultora in EmpresaPatterns.CONSULTORAS_CONOCIDAS:
            if consultora in texto_combined:
                return empresa  # Retorna el nombre original

        # Buscar patrones que indican cliente
        for patron in EmpresaPatterns.PATRONES_CLIENTE:
            if re.search(patron, texto_combined):
                return empresa

        return None  # Es empresa directa

    @staticmethod
    def extraer_empresa_cliente(texto: str) -> Optional[str]:
        """Intenta extraer el nombre de la empresa cliente si es consultora"""
        patrones = [
            r'para\s+(?:la\s+)?empresa\s+([A-Z][A-Za-z0-9\s&]+?)(?:\.|,|$)',
            r'cliente:\s*([A-Z][A-Za-z0-9\s&]+?)(?:\.|,|$)',
            r'para\s+([A-Z][A-Za-z0-9\s&]{3,30})\s+(?:en|ubicada)',
        ]
        for patron in patrones:
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None


class HeaderPatterns:
    """Extrae datos del header tipo 'Clave: valor'"""

    PAT_HEADER = re.compile(
        r'^(?P<clave>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+):\s*(?P<valor>.+)$',
        flags=re.M
    )

    # Claves conocidas y su normalización
    CLAVES_NORMALIZADAS = {
        'empresa': 'empresa',
        'compañía': 'empresa',
        'compania': 'empresa',
        'ubicación': 'ubicacion',
        'ubicacion': 'ubicacion',
        'localidad': 'ubicacion',
        'zona': 'ubicacion',
        'modalidad': 'modalidad',
        'tipo de trabajo': 'tipo_trabajo',
        'tipo': 'tipo_trabajo',
        'jornada': 'jornada',
        'horario': 'horario',
        'salario': 'salario',
        'sueldo': 'salario',
        'remuneración': 'salario',
        'remuneracion': 'salario',
        'fecha': 'fecha',
        'publicado': 'fecha',
    }

    @staticmethod
    def extraer_encabezado(texto: str) -> Dict[str, str]:
        """
        Extrae datos del header tipo 'Clave: valor'
        Returns: dict con claves normalizadas
        """
        resultados = {}
        for m in HeaderPatterns.PAT_HEADER.finditer(texto):
            clave_raw = m.group("clave").strip().lower()
            valor = m.group("valor").strip()

            # Normalizar clave
            clave_norm = HeaderPatterns.CLAVES_NORMALIZADAS.get(clave_raw, clave_raw)

            # Evitar sobrescribir si ya existe
            if clave_norm not in resultados:
                resultados[clave_norm] = valor

        return resultados


class BeneficiosPatterns:
    """Extrae beneficios específicos estructurados"""

    PAT_OBRA_SOCIAL = re.compile(
        r'[Oo]bra\s+[Ss]ocial\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ \.]+?)(?:,|\.|;|$|\n)',
        flags=re.I
    )

    PAT_ART = re.compile(
        r'\bART\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ \.]+?)(?:,|\.|;|$|\n)',
        flags=re.I
    )

    PAT_PREPAGA = re.compile(
        r'[Pp]repaga\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ \.]+?)(?:,|\.|;|$|\n)',
        flags=re.I
    )

    # Keywords de beneficios (detectar presencia, no extraer nombre)
    BENEFICIOS_KEYWORDS = {
        'capacitacion': ['capacitación', 'capacitacion', 'formación', 'formacion', 'cursos'],
        'cochera': ['cochera', 'estacionamiento', 'parking'],
        'comedor': ['comedor', 'almuerzo', 'vianda', 'refrigerio'],
        'gimnasio': ['gimnasio', 'gym'],
        'prepaga': ['prepaga', 'cobertura médica', 'cobertura medica'],
        'bono': ['bono', 'bonus', 'premio'],
        'aguinaldo': ['aguinaldo', 'sac'],
        'vacaciones': ['vacaciones adicionales', 'días extra', 'dias extra'],
        'home_office': ['home office', 'trabajo remoto', 'teletrabajo', 'híbrido', 'hibrido'],
        'flexibilidad': ['horario flexible', 'flexibilidad horaria'],
    }

    @staticmethod
    def extraer_obra_social(texto: str) -> str:
        """Extrae nombre de obra social"""
        m = BeneficiosPatterns.PAT_OBRA_SOCIAL.search(texto)
        return m.group(1).strip() if m else ""

    @staticmethod
    def extraer_art(texto: str) -> str:
        """Extrae nombre de ART"""
        m = BeneficiosPatterns.PAT_ART.search(texto)
        return m.group(1).strip() if m else ""

    @staticmethod
    def extraer_prepaga(texto: str) -> str:
        """Extrae nombre de prepaga"""
        m = BeneficiosPatterns.PAT_PREPAGA.search(texto)
        return m.group(1).strip() if m else ""

    @staticmethod
    def detectar_beneficios(texto: str) -> List[str]:
        """Detecta qué beneficios se mencionan (sin extraer nombres específicos)"""
        texto_lower = texto.lower()
        beneficios = []

        for beneficio, keywords in BeneficiosPatterns.BENEFICIOS_KEYWORDS.items():
            for kw in keywords:
                if kw in texto_lower:
                    beneficios.append(beneficio)
                    break

        return beneficios


class ViajesPatterns:
    """Detecta disponibilidad de viajes"""

    PATRONES_VIAJES = [
        r'disponibilidad\s+(?:para\s+)?viaj(?:ar|es)',
        r'viaj(?:ar|es)\s+(?:al\s+)?interior',
        r'viaj(?:ar|es)\s+(?:al\s+)?exterior',
        r'movilidad\s+(?:propia|geográfica|geografica)',
        r'trabajo\s+(?:en\s+)?(?:ruta|viaje)',
    ]

    PAT_FRECUENCIA = re.compile(
        r'viaj(?:ar|es).*?(\d+)%',
        flags=re.I
    )

    @staticmethod
    def requiere_viajes(texto: str) -> Tuple[bool, Optional[int]]:
        """
        Detecta si requiere disponibilidad para viajar.
        Returns: (requiere_viajes, porcentaje_tiempo)
        """
        texto_lower = texto.lower()

        for patron in ViajesPatterns.PATRONES_VIAJES:
            if re.search(patron, texto_lower):
                # Intentar extraer porcentaje
                m = ViajesPatterns.PAT_FRECUENCIA.search(texto)
                porcentaje = int(m.group(1)) if m else None
                return True, porcentaje

        return False, None


# =============================================================================
# CLASE PARA MÉTRICA DE COVERAGE (NUEVO v4.1)
# =============================================================================

class StructureDetector:
    """
    Detecta secciones estructuradas en ofertas de empleo y cuenta items esperados.
    Se usa para calcular la métrica de coverage: items_extraidos / items_esperados.

    VERSION: 4.1
    FECHA: 2025-11-27
    """

    # Patrones para detectar headers de sección (case insensitive)
    SECCIONES = {
        'requisitos': [
            r'requisitos?\s*(?:excluyentes?|del\s+puesto)?\s*:',
            r'requerimientos?\s*:',
            r'perfil\s+(?:buscado|requerido)\s*:',
            r'buscamos\s+(?:personas?|profesionales?)\s+(?:con|que)\s*:',
            r'experiencia\s+y\s+conocimientos?\s*:',
        ],
        'responsabilidades': [
            r'responsabilidades?\s*:',
            r'funciones?\s*(?:principales?)?\s*:',
            r'tareas?\s*(?:principales?)?\s*:',
            r'actividades?\s*:',
            r'(?:tus|sus)\s+principales?\s+(?:tareas?|funciones?|responsabilidades?)\s*:',
            r'(?:el|la)\s+(?:candidato|persona)\s+(?:deber[aá]|tendr[aá])\s*:',
        ],
        'beneficios': [
            r'beneficios?\s*:',
            r'(?:te\s+)?ofrecemos?\s*:',
            r'(?:qu[eé]\s+)?te\s+ofrecemos?\s*:',
            r'condiciones?\s*:',
            r'paquete\s+de\s+beneficios?\s*:',
        ],
        'skills': [
            r'(?:skills?|habilidades?|competencias?)\s*(?:t[eé]cnicas?)?\s*:',
            r'conocimientos?\s*(?:t[eé]cnicos?)?\s*:',
            r'tecnolog[ií]as?\s*(?:requeridas?)?\s*:',
            r'stack\s+tecnol[oó]gico\s*:',
        ],
    }

    # Patrones para detectar bullets
    PAT_BULLET = re.compile(
        r'^[\s]*[-•●○►✓✔☑⬤★▪▸➤➢→]\s+(.+)$',
        re.MULTILINE
    )

    # Patrón alternativo: líneas numeradas (1., 2., etc.)
    PAT_NUMERADO = re.compile(
        r'^[\s]*\d+[.)]\s+(.+)$',
        re.MULTILINE
    )

    # Patrón para detectar cualquier header (sección siguiente)
    PAT_CUALQUIER_HEADER = re.compile(
        r'^[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]+:\s*$',
        re.MULTILINE
    )

    @staticmethod
    def encontrar_seccion(texto: str, seccion: str) -> tuple:
        """
        Encuentra el inicio y fin de una sección en el texto.

        Args:
            texto: Texto completo de la oferta
            seccion: Nombre de la sección ('requisitos', 'responsabilidades', etc.)

        Returns:
            (inicio, fin) - índices del texto, o (None, None) si no se encuentra
        """
        if seccion not in StructureDetector.SECCIONES:
            return None, None

        texto_lower = texto.lower()
        inicio = None

        # Buscar el header de la sección
        for patron in StructureDetector.SECCIONES[seccion]:
            m = re.search(patron, texto_lower)
            if m:
                inicio = m.end()
                break

        if inicio is None:
            return None, None

        # Buscar el fin (siguiente header o fin de texto)
        fin = len(texto)

        # Buscar cualquier otro header de sección que marque el fin
        for otra_seccion, patrones in StructureDetector.SECCIONES.items():
            if otra_seccion == seccion:
                continue
            for patron in patrones:
                m = re.search(patron, texto_lower[inicio:])
                if m:
                    posible_fin = inicio + m.start()
                    if posible_fin < fin:
                        fin = posible_fin

        # También buscar headers genéricos
        m = StructureDetector.PAT_CUALQUIER_HEADER.search(texto[inicio:])
        if m:
            posible_fin = inicio + m.start()
            if posible_fin < fin:
                fin = posible_fin

        return inicio, fin

    @staticmethod
    def contar_items_seccion(texto: str, seccion: str) -> int:
        """
        Cuenta bullets/items dentro de una sección específica.

        Args:
            texto: Texto completo de la oferta
            seccion: Nombre de la sección

        Returns:
            Número de items detectados en la sección
        """
        inicio, fin = StructureDetector.encontrar_seccion(texto, seccion)

        if inicio is None:
            return 0

        fragmento = texto[inicio:fin]

        # Contar bullets
        bullets = StructureDetector.PAT_BULLET.findall(fragmento)

        # Contar items numerados
        numerados = StructureDetector.PAT_NUMERADO.findall(fragmento)

        # Retornar el mayor de los dos (algunas ofertas usan ambos formatos)
        return max(len(bullets), len(numerados))

    @staticmethod
    def detectar_estructura(texto: str) -> Dict[str, Any]:
        """
        Detecta la estructura completa del aviso y cuenta items esperados por campo.

        Args:
            texto: Texto completo de la oferta

        Returns:
            Dict con conteos por campo y total esperado:
            {
                'requisitos_esperados': int,
                'responsabilidades_esperadas': int,
                'beneficios_esperados': int,
                'skills_esperados': int,
                'total_items_esperados': int,
                'tiene_estructura': bool
            }
        """
        requisitos = StructureDetector.contar_items_seccion(texto, 'requisitos')
        responsabilidades = StructureDetector.contar_items_seccion(texto, 'responsabilidades')
        beneficios = StructureDetector.contar_items_seccion(texto, 'beneficios')
        skills = StructureDetector.contar_items_seccion(texto, 'skills')

        total = requisitos + responsabilidades + beneficios + skills
        tiene_estructura = total > 0

        return {
            'requisitos_esperados': requisitos,
            'responsabilidades_esperadas': responsabilidades,
            'beneficios_esperados': beneficios,
            'skills_esperados': skills,
            'total_items_esperados': total,
            'tiene_estructura': tiene_estructura
        }

    @staticmethod
    def calcular_coverage(items_extraidos: int, items_esperados: int) -> float:
        """
        Calcula el score de coverage.

        Args:
            items_extraidos: Cantidad de items extraídos por el LLM
            items_esperados: Cantidad de items esperados según estructura

        Returns:
            Score entre 0.0 y 1.0 (puede ser > 1.0 si extrae más de lo esperado)
        """
        if items_esperados == 0:
            # Si no hay estructura detectada, retornar 1.0 (no penalizar)
            return 1.0

        return round(items_extraidos / items_esperados, 2)


# =============================================================================
# FUNCIÓN PRINCIPAL: EXTRAER TODO
# =============================================================================

def extract_all(texto: str, titulo: str = "", empresa: str = "") -> Dict[str, Any]:
    """
    Ejecuta TODAS las clases de regex y devuelve un JSON completo.
    Esta es la función principal de la Capa 0.

    Args:
        texto: Descripción de la oferta
        titulo: Título del puesto
        empresa: Nombre de la empresa

    Returns:
        Dict con todos los campos extraídos por regex
    """
    texto_completo = f"{titulo}\n{texto}"

    # 1. Header
    header = HeaderPatterns.extraer_encabezado(texto)

    # 2. Experiencia (v3)
    exp_min, exp_max = ExperienciaPatterns.extract_years(texto_completo)
    exp_area = ExperienciaPatterns.extract_area(texto_completo)

    # 3. Educación (v3)
    nivel_edu = EducacionPatterns.extract_nivel(texto_completo)
    estado_edu = EducacionPatterns.extract_estado(texto_completo)
    carrera = EducacionPatterns.extract_carrera(texto_completo)
    titulo_excl = EducacionPatterns.is_excluyente(texto_completo)

    # 4. Idiomas (v3)
    idiomas = IdiomasPatterns.extract_idiomas(texto_completo)
    idioma_principal = idiomas[0] if idiomas else (None, None)
    idioma_secundario = idiomas[1] if len(idiomas) > 1 else (None, None)

    # 5. Salario (v3)
    salario_min, salario_max, moneda = SalarioPatterns.extract_montos(texto_completo)

    # 6. Jornada (v3)
    jornada = JornadaPatterns.extract_tipo(texto_completo)
    horario = JornadaPatterns.extract_horario(texto_completo)
    dias = JornadaPatterns.extract_dias(texto_completo)
    flexible = JornadaPatterns.is_flexible(texto_completo)

    # 7. Edad (NUEVO v4)
    edad_min, edad_max = EdadPatterns.extraer_edades(texto_completo)

    # 8. Licencia (NUEVO v4)
    licencia_req, licencia_cat = LicenciaPatterns.extraer_registro(texto_completo)

    # 9. Contratación inmediata (NUEVO v4)
    contratacion_inm = ContratacionPatterns.es_inmediata(texto_completo)

    # 10. Indexación (NUEVO v4)
    indexacion = IndexacionPatterns.extraer_indexacion(texto_completo)

    # 11. Empresa/Consultora (NUEVO v4)
    es_consultora = EmpresaPatterns.detectar_consultora(texto_completo, empresa)
    empresa_cliente = EmpresaPatterns.extraer_empresa_cliente(texto_completo) if es_consultora else None

    # 12. Beneficios estructurados (NUEVO v4)
    obra_social = BeneficiosPatterns.extraer_obra_social(texto_completo)
    art = BeneficiosPatterns.extraer_art(texto_completo)
    prepaga = BeneficiosPatterns.extraer_prepaga(texto_completo)
    beneficios_detectados = BeneficiosPatterns.detectar_beneficios(texto_completo)

    # 13. Viajes (NUEVO v4)
    viajes_req, viajes_pct = ViajesPatterns.requiere_viajes(texto_completo)

    # 14. Seniority del título (v3)
    seniority = None
    for pattern, (min_exp, _) in ExperienciaPatterns.NIVELES_TITULO.items():
        if re.search(pattern, titulo.lower()):
            if min_exp == 0:
                seniority = "trainee" if "trainee" in titulo.lower() else "junior"
            elif min_exp <= 2:
                seniority = "semi-senior"
            elif min_exp <= 5:
                seniority = "senior"
            else:
                seniority = "lead/manager"
            break

    return {
        # === CAMPOS DE v3 ===
        "experiencia_min_anios": exp_min,
        "experiencia_max_anios": exp_max,
        "experiencia_area": exp_area,
        "nivel_educativo": nivel_edu,
        "estado_educativo": estado_edu,
        "carrera_especifica": carrera,
        "titulo_excluyente": titulo_excl,
        "idioma_principal": idioma_principal[0],
        "nivel_idioma_principal": idioma_principal[1],
        "idioma_secundario": idioma_secundario[0],
        "nivel_idioma_secundario": idioma_secundario[1],
        "salario_min": salario_min,
        "salario_max": salario_max,
        "moneda": moneda,
        "jornada_laboral": jornada,
        "horario_especifico": horario,
        "dias_laborales": dias,
        "horario_flexible": flexible,
        "nivel_seniority": seniority,

        # === CAMPOS NUEVOS v4 ===
        "edad_min": edad_min,
        "edad_max": edad_max,
        "licencia_conducir_requerida": licencia_req,
        "licencia_conducir_categoria": licencia_cat,
        "contratacion_inmediata": contratacion_inm,
        "indexacion_salarial": indexacion,
        "empresa_publicadora": es_consultora,
        "empresa_contratante": empresa_cliente if es_consultora else empresa,
        "obra_social": obra_social,
        "art": art,
        "prepaga": prepaga,
        "beneficios_detectados": beneficios_detectados,
        "disponibilidad_viajes": viajes_req,
        "viajes_porcentaje": viajes_pct,

        # === HEADER (si existe) ===
        "header_empresa": header.get("empresa"),
        "header_ubicacion": header.get("ubicacion"),
        "header_modalidad": header.get("modalidad"),
        "header_salario": header.get("salario"),
    }


# =============================================================================
# TEST RÁPIDO
# =============================================================================

if __name__ == "__main__":
    # Test con texto de ejemplo
    texto_test = """
    Empresa: Club Náutico San Isidro
    Ubicación: San Isidro, Buenos Aires
    Modalidad: Presencial

    Buscamos Operario de Mantenimiento General para contratación inmediata.

    Requisitos:
    - Edad entre 2 5 y 4 5 años
    - Registro de conducir categoría B1
    - Experiencia mínimo 2 años en mantenimiento edilicio
    - Secundario completo

    Ofrecemos:
    - Obra Social OSDE
    - ART Prevención
    - Horario flexible de 8 a 17hs
    - Ajuste por índice IPC cada 3 meses
    """

    resultado = extract_all(texto_test, "Operario de Mantenimiento General")

    print("=== RESULTADO EXTRACCIÓN v4 ===")
    for campo, valor in resultado.items():
        if valor:
            print(f"  {campo}: {valor}")
