#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nivel_jerarquico.py
===================
Detecta nivel jerárquico en títulos de ofertas laborales y labels ESCO.
Aplica penalizaciones cuando hay incompatibilidad de niveles.

VERSION: v1.1 (2025-12-09) - Integración con config_loader

Integración con match_ofertas_multicriteria.py v8.4:
- Detecta nivel jerárquico del título de la oferta
- Detecta nivel jerárquico del label ESCO candidato
- Penaliza si hay diferencia significativa de niveles
- Carga configuración desde config/niveles_jerarquicos.json si disponible
"""

import re
from typing import Optional, Tuple

# Intentar cargar configuración externalizada
try:
    from config_loader import (
        get_niveles_config,
        get_nivel_valor as _get_nivel_valor_config,
        get_nivel_keywords as _get_nivel_keywords_config,
        get_penalizacion_nivel as _get_penalizacion_nivel_config,
        get_excepciones_no_gerente
    )
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False

# Definición de niveles jerárquicos con palabras clave
# Se carga desde config si disponible, sino usa valores hardcodeados
if CONFIG_LOADER_AVAILABLE:
    _niveles_config = get_niveles_config().get('niveles', {})
    NIVELES_KEYWORDS = {
        nivel: data.get('keywords', [])
        for nivel, data in _niveles_config.items()
    }
    JERARQUIA_NUMERICA = {
        nivel: data.get('valor', 2)
        for nivel, data in _niveles_config.items()
    }
    _pen_config = get_niveles_config().get('penalizaciones', {})
    PENALIZACION_SEVERA = _pen_config.get('severa', {}).get('valor', -0.25)
    PENALIZACION_MODERADA = _pen_config.get('moderada', {}).get('valor', -0.12)
    PENALIZACION_LEVE = _pen_config.get('leve', {}).get('valor', -0.05)
    _EXCEPCIONES_NO_GERENTE = get_excepciones_no_gerente()
else:
    # Fallback a valores hardcodeados
    NIVELES_KEYWORDS = {
        'director': [
            'director', 'directora', 'ceo', 'cfo', 'cto', 'coo', 'cio',
            'chief', 'presidente', 'presidenta', 'vp', 'vicepresidente'
        ],
        'gerente': [
            'gerente', 'gerenta', 'manager', 'gerencial', 'general manager',
            'country manager', 'regional manager'
        ],
        'jefe': [
            'jefe', 'jefa', 'head of', 'head', 'responsable de area',
            'lider de equipo', 'team lead', 'team leader'
        ],
        'supervisor': [
            'supervisor', 'supervisora', 'encargado', 'encargada',
            'capataz', 'responsable'
        ],
        'coordinador': [
            'coordinador', 'coordinadora', 'coord.'
        ],
        'ejecutivo': [
            'ejecutivo', 'ejecutiva', 'account executive', 'key account',
            'ejecutivo de cuentas', 'ejecutiva de cuentas'
        ],
        'especialista': [
            'especialista', 'senior', 'sr.', 'sr ', 'ssr', 'semi senior',
            'profesional', 'experto', 'experta'
        ],
        'analista': [
            'analista', 'analyst'
        ],
        'representante': [
            'representante', 'rep.', 'agente', 'promotor', 'promotora',
            'asesor comercial', 'asesora comercial', 'vendedor', 'vendedora'
        ],
        'tecnico': [
            'tecnico', 'tecnica', 'tecnologo', 'tecnologa', 'technician'
        ],
        'asistente': [
            'asistente', 'auxiliar', 'ayudante', 'junior', 'jr.', 'jr ',
            'trainee', 'pasante', 'practicante', 'administrativo', 'administrativa'
        ],
        'operario': [
            'operario', 'operaria', 'operador', 'operadora', 'peon',
            'obrero', 'obrera', 'mozo', 'moza', 'repositor', 'repositora'
        ]
    }

    # Jerarquía numérica (mayor número = más alto nivel)
    JERARQUIA_NUMERICA = {
        'director': 6,
        'gerente': 5,
        'jefe': 4,
        'supervisor': 3.5,
        'coordinador': 3,
        'ejecutivo': 2.5,
        'especialista': 2.5,
        'analista': 2,
        'representante': 1.5,
        'tecnico': 1.5,
        'asistente': 1,
        'operario': 0.5
    }

    # Penalizaciones por diferencia de nivel
    PENALIZACION_SEVERA = -0.25    # Diferencia >= 2 niveles
    PENALIZACION_MODERADA = -0.12  # Diferencia >= 1 nivel
    PENALIZACION_LEVE = -0.05      # Diferencia >= 0.5 niveles

    # Excepciones no disponibles sin config
    _EXCEPCIONES_NO_GERENTE = {}


def detectar_nivel_jerarquico(texto: str) -> Optional[str]:
    """
    Detecta el nivel jerárquico de un texto (título de oferta o label ESCO).

    Args:
        texto: Título de oferta o label ESCO

    Returns:
        Nivel jerárquico detectado o None si no se detecta

    Ejemplos:
        "Gerente de Ventas" -> "gerente"
        "Ejecutivo de Cuentas Senior" -> "ejecutivo"
        "Analista de Sistemas" -> "analista"
        "Operario de Producción" -> "operario"
    """
    if not texto:
        return None

    texto_lower = texto.lower()

    # EXCEPCIONES ESPECIALES: términos que NO indican nivel gerencial
    # Se cargan desde config si disponible, sino usa lógica hardcodeada
    if _EXCEPCIONES_NO_GERENTE:
        # Usar excepciones desde config
        for excepcion, nivel_correcto in _EXCEPCIONES_NO_GERENTE.items():
            if excepcion in texto_lower:
                return nivel_correcto
    else:
        # Fallback a lógica hardcodeada
        excepciones_no_gerente = [
            'community manager',
            'social media manager',
            'content manager',
            'account manager',
            'project manager',
            'product manager',
            'case manager',
        ]

        for excepcion in excepciones_no_gerente:
            if excepcion in texto_lower:
                if 'community' in texto_lower or 'social media' in texto_lower or 'content' in texto_lower:
                    return 'especialista'
                elif 'account manager' in texto_lower:
                    return 'ejecutivo'
                elif 'project' in texto_lower or 'product' in texto_lower:
                    return 'coordinador'
                else:
                    return 'especialista'

    # Buscar en orden de especificidad (primero los más específicos)
    for nivel, keywords in NIVELES_KEYWORDS.items():
        for keyword in keywords:
            # Buscar como palabra completa
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, texto_lower):
                return nivel

    return None


def calcular_penalizacion_nivel(nivel_titulo: Optional[str],
                                 nivel_esco: Optional[str]) -> Tuple[float, str]:
    """
    Calcula la penalización por incompatibilidad de niveles jerárquicos.

    Args:
        nivel_titulo: Nivel detectado en el título de la oferta
        nivel_esco: Nivel detectado en el label ESCO

    Returns:
        Tuple de (penalizacion, razon)
        - penalizacion: Valor negativo a sumar al score (0 si no hay penalización)
        - razon: Descripción de la penalización aplicada

    Ejemplos:
        ("gerente", "operario") -> (-0.25, "nivel_severo: gerente vs operario")
        ("ejecutivo", "director") -> (-0.12, "nivel_moderado: ejecutivo vs director")
        ("analista", "analista") -> (0.0, None)
    """
    # Si no detectamos nivel en alguno, no penalizamos
    if nivel_titulo is None or nivel_esco is None:
        return 0.0, None

    # Obtener valores numéricos
    valor_titulo = JERARQUIA_NUMERICA.get(nivel_titulo, 2)
    valor_esco = JERARQUIA_NUMERICA.get(nivel_esco, 2)

    # Calcular diferencia absoluta
    diferencia = abs(valor_titulo - valor_esco)

    # Determinar penalización
    if diferencia >= 2.5:
        return PENALIZACION_SEVERA, f"nivel_severo:{nivel_titulo}->{nivel_esco}(diff={diferencia:.1f})"
    elif diferencia >= 1.5:
        return PENALIZACION_MODERADA, f"nivel_moderado:{nivel_titulo}->{nivel_esco}(diff={diferencia:.1f})"
    elif diferencia >= 1:
        return PENALIZACION_LEVE, f"nivel_leve:{nivel_titulo}->{nivel_esco}(diff={diferencia:.1f})"

    return 0.0, None


def aplicar_penalizacion_nivel_candidatos(titulo: str,
                                           candidatos: list) -> list:
    """
    Aplica penalización de nivel jerárquico a lista de candidatos ESCO.

    Args:
        titulo: Título de la oferta laboral
        candidatos: Lista de candidatos ESCO del PASO 1

    Returns:
        Lista de candidatos con penalización aplicada y reordenada
    """
    nivel_titulo = detectar_nivel_jerarquico(titulo)

    if nivel_titulo is None:
        return candidatos  # Sin cambios si no detectamos nivel

    candidatos_penalizados = []
    for cand in candidatos:
        cand_copy = cand.copy()

        # Detectar nivel en el label ESCO
        esco_label = cand.get('label', '') or cand.get('occupation_label', '')
        nivel_esco = detectar_nivel_jerarquico(esco_label)

        # Calcular penalización
        penalizacion, razon = calcular_penalizacion_nivel(nivel_titulo, nivel_esco)

        if penalizacion != 0:
            cand_copy['similarity_score'] = cand_copy.get('similarity_score', 0) + penalizacion
            cand_copy['nivel_penalizacion'] = penalizacion
            cand_copy['nivel_penalizacion_razon'] = razon
            cand_copy['nivel_titulo'] = nivel_titulo
            cand_copy['nivel_esco'] = nivel_esco

        candidatos_penalizados.append(cand_copy)

    # Reordenar por score
    candidatos_penalizados.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

    return candidatos_penalizados


def get_stats():
    """Retorna estadísticas de la configuración."""
    return {
        'config_loader_activo': CONFIG_LOADER_AVAILABLE,
        'niveles_definidos': len(NIVELES_KEYWORDS),
        'keywords_total': sum(len(kw) for kw in NIVELES_KEYWORDS.values()),
        'excepciones_no_gerente': len(_EXCEPCIONES_NO_GERENTE),
        'penalizacion_severa': PENALIZACION_SEVERA,
        'penalizacion_moderada': PENALIZACION_MODERADA,
        'penalizacion_leve': PENALIZACION_LEVE
    }


# Test standalone
if __name__ == '__main__':
    print("=" * 60)
    print("TEST: nivel_jerarquico.py")
    print("=" * 60)

    stats = get_stats()
    print(f"\nConfiguracion:")
    print(f"  Niveles definidos: {stats['niveles_definidos']}")
    print(f"  Keywords totales: {stats['keywords_total']}")
    print(f"  Penalizaciones: severa={stats['penalizacion_severa']}, "
          f"moderada={stats['penalizacion_moderada']}, leve={stats['penalizacion_leve']}")

    # Test cases - títulos de ofertas
    test_titulos = [
        "Gerente de Ventas",
        "Ejecutivo/a Comercial de Cuentas",
        "Community Manager",
        "Analista de Sistemas Senior",
        "Operario de Producción",
        "Director Comercial",
        "Representante de Ventas",
        "Asistente Administrativo",
        "Supervisor de Limpieza",
        "Jefe de Compras"
    ]

    print("\n" + "-" * 60)
    print("DETECCION DE NIVEL EN TITULOS:")
    print("-" * 60)

    for titulo in test_titulos:
        nivel = detectar_nivel_jerarquico(titulo)
        valor = JERARQUIA_NUMERICA.get(nivel, '?') if nivel else '?'
        print(f"  '{titulo}' -> {nivel} (valor={valor})")

    # Test de compatibilidad
    print("\n" + "-" * 60)
    print("TEST DE PENALIZACION:")
    print("-" * 60)

    test_pares = [
        ("Ejecutivo Comercial", "Director comercial"),           # Debería penalizar
        ("Gerente de Ventas", "Representante técnico de ventas"), # Debería penalizar
        ("Community Manager", "Gerente de camping"),             # Debería penalizar
        ("Analista de Datos", "Analista de negocios"),           # OK, mismo nivel
        ("Supervisor de Limpieza", "Supervisor de servicio"),    # OK, mismo nivel
    ]

    for titulo, esco in test_pares:
        nivel_t = detectar_nivel_jerarquico(titulo)
        nivel_e = detectar_nivel_jerarquico(esco)
        pen, razon = calcular_penalizacion_nivel(nivel_t, nivel_e)

        print(f"\n  Titulo: '{titulo}' -> {nivel_t}")
        print(f"  ESCO:   '{esco}' -> {nivel_e}")
        print(f"  Penalizacion: {pen:.2f}" + (f" ({razon})" if razon else " (OK)"))
