# -*- coding: utf-8 -*-
"""
config_loader.py
================
Carga configuración externalizada desde archivos JSON.

Permite modificar parámetros de matching sin tocar código Python.

Estructura de archivos:
    config/matching_config.json     - Pesos, thresholds, búsqueda
    config/matching_rules.json      - Reglas de familias funcionales
    config/niveles_jerarquicos.json - Niveles jerárquicos
    config/normalizacion_boost.json - Boost argentino

USO:
    from config_loader import get_config, get_matching_rules, get_niveles, get_boost_config

    # Obtener valor específico
    peso_titulo = get_config('pesos.titulo')  # 0.50

    # Obtener reglas de matching
    rules = get_matching_rules()

    # Obtener niveles jerárquicos
    niveles = get_niveles()
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Any, Optional

# Paths de configuración
CONFIG_DIR = Path(__file__).parent.parent / 'config'
MATCHING_CONFIG_PATH = CONFIG_DIR / 'matching_config.json'
MATCHING_RULES_PATH = CONFIG_DIR / 'matching_rules.json'
NIVELES_PATH = CONFIG_DIR / 'niveles_jerarquicos.json'
BOOST_PATH = CONFIG_DIR / 'normalizacion_boost.json'


# Cache de configuraciones
_config_cache = {}


def _load_json(path: Path) -> dict:
    """Carga un archivo JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _get_nested(data: dict, key_path: str, default: Any = None) -> Any:
    """
    Obtiene valor anidado usando notación de punto.

    Ejemplo: _get_nested(data, 'pesos.titulo') -> data['pesos']['titulo']
    """
    keys = key_path.split('.')
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def reload_config():
    """Recarga toda la configuración desde disco."""
    global _config_cache
    _config_cache = {}
    get_matching_config.cache_clear()
    get_matching_rules.cache_clear()
    get_niveles_config.cache_clear()
    get_boost_config.cache_clear()


@lru_cache(maxsize=1)
def get_matching_config() -> dict:
    """Carga configuración principal de matching."""
    return _load_json(MATCHING_CONFIG_PATH)


@lru_cache(maxsize=1)
def get_matching_rules() -> dict:
    """Carga reglas de matching."""
    return _load_json(MATCHING_RULES_PATH)


@lru_cache(maxsize=1)
def get_niveles_config() -> dict:
    """Carga configuración de niveles jerárquicos."""
    return _load_json(NIVELES_PATH)


@lru_cache(maxsize=1)
def get_boost_config() -> dict:
    """Carga configuración de boost argentino."""
    return _load_json(BOOST_PATH)


def get_config(key_path: str, default: Any = None) -> Any:
    """
    Obtiene un valor de configuración usando notación de punto.

    Args:
        key_path: Ruta al valor (ej: 'pesos.titulo', 'thresholds.confirmado_score')
        default: Valor por defecto si no existe

    Returns:
        Valor de configuración

    Examples:
        >>> get_config('pesos.titulo')
        0.50
        >>> get_config('thresholds.confirmado_score')
        0.60
        >>> get_config('busqueda.top_k_candidatos')
        10
    """
    config = get_matching_config()
    return _get_nested(config, key_path, default)


def get_pesos(coverage_level: str = 'normal') -> dict:
    """
    Obtiene pesos según nivel de coverage.

    Args:
        coverage_level: 'alta', 'media', 'baja' o 'normal' (usa alta)

    Returns:
        Dict con pesos {titulo, skills, descripcion}
    """
    config = get_matching_config()

    if coverage_level == 'normal' or coverage_level == 'alta':
        pesos_cfg = config.get('pesos_dinamicos', {}).get('coverage_alta', {})
    elif coverage_level == 'media':
        pesos_cfg = config.get('pesos_dinamicos', {}).get('coverage_media', {})
    else:  # baja
        pesos_cfg = config.get('pesos_dinamicos', {}).get('coverage_baja', {})

    return {
        'titulo': pesos_cfg.get('titulo', 0.50),
        'skills': pesos_cfg.get('skills', 0.40),
        'descripcion': pesos_cfg.get('descripcion', 0.10)
    }


def get_thresholds() -> dict:
    """
    Obtiene todos los thresholds de matching.

    Returns:
        Dict con thresholds
    """
    config = get_matching_config()
    return config.get('thresholds', {})


def get_familia_keywords(familia: str, tipo: str = 'oferta') -> list:
    """
    Obtiene keywords de una familia funcional.

    Args:
        familia: Nombre de la familia (ej: 'admin_contable', 'comercial_ventas')
        tipo: 'oferta' o 'esco'

    Returns:
        Lista de keywords
    """
    rules = get_matching_rules()
    familias = rules.get('familias', {})

    if familia not in familias:
        return []

    familia_cfg = familias[familia]

    if tipo == 'oferta':
        return familia_cfg.get('keywords_oferta', [])
    else:
        return familia_cfg.get('keywords_esco', [])


def get_reglas_penalizacion() -> dict:
    """
    Obtiene todas las reglas de penalización.

    Returns:
        Dict con reglas {nombre: {condiciones, penalizacion, never_confirm}}
    """
    rules = get_matching_rules()
    return rules.get('reglas', {})


def get_nivel_keywords(nivel: str) -> list:
    """
    Obtiene keywords de un nivel jerárquico.

    Args:
        nivel: Nombre del nivel (ej: 'director', 'gerente', 'asistente')

    Returns:
        Lista de keywords
    """
    config = get_niveles_config()
    niveles = config.get('niveles', {})

    if nivel not in niveles:
        return []

    return niveles[nivel].get('keywords', [])


def get_nivel_valor(nivel: str) -> float:
    """
    Obtiene valor numérico de un nivel jerárquico.

    Args:
        nivel: Nombre del nivel

    Returns:
        Valor numérico (mayor = más alto)
    """
    config = get_niveles_config()
    niveles = config.get('niveles', {})

    if nivel not in niveles:
        return 2.0  # default medio

    return niveles[nivel].get('valor', 2.0)


def get_penalizacion_nivel(diferencia: float) -> float:
    """
    Obtiene penalización según diferencia de niveles.

    Args:
        diferencia: Diferencia absoluta entre niveles

    Returns:
        Penalización a aplicar (valor negativo)
    """
    config = get_niveles_config()
    penalizaciones = config.get('penalizaciones', {})

    if diferencia >= penalizaciones.get('severa', {}).get('diferencia_minima', 2.5):
        return penalizaciones.get('severa', {}).get('valor', -0.25)
    elif diferencia >= penalizaciones.get('moderada', {}).get('diferencia_minima', 1.5):
        return penalizaciones.get('moderada', {}).get('valor', -0.12)
    elif diferencia >= penalizaciones.get('leve', {}).get('diferencia_minima', 1.0):
        return penalizaciones.get('leve', {}).get('valor', -0.05)

    return 0.0


def get_boost_isco(tipo: str) -> float:
    """
    Obtiene valor de boost ISCO.

    Args:
        tipo: 'exact_isco', 'isco_group', 'wrong_isco'

    Returns:
        Valor de boost/penalización
    """
    config = get_boost_config()

    if tipo in ('exact_isco', 'isco_group'):
        return config.get('boost', {}).get(tipo, {}).get('valor', 0.0)
    elif tipo == 'wrong_isco':
        return config.get('penalizacion', {}).get(tipo, {}).get('valor', 0.0)

    return 0.0


def get_excepciones_no_gerente() -> dict:
    """
    Obtiene excepciones que contienen 'manager' pero no son gerentes.

    Returns:
        Dict {termino: nivel_correcto}
    """
    config = get_niveles_config()
    excepciones = config.get('excepciones_no_gerente', {})
    # Filtrar el comentario
    return {k: v for k, v in excepciones.items() if not k.startswith('_')}


def get_isco_keywords() -> dict:
    """
    Obtiene mapeo keywords->grupos ISCO permitidos.

    Returns:
        Dict {nombre_grupo: {keywords: [], isco_permitidos: []}}
    """
    config = get_matching_config()
    return config.get('isco_keywords', {}).get('grupos', {})


# Funciones de validación
def validate_config():
    """
    Valida que todos los archivos de configuración existen y son válidos.

    Returns:
        Dict con resultado de validación
    """
    results = {}

    configs = [
        ('matching_config', MATCHING_CONFIG_PATH),
        ('matching_rules', MATCHING_RULES_PATH),
        ('niveles_jerarquicos', NIVELES_PATH),
        ('normalizacion_boost', BOOST_PATH)
    ]

    for name, path in configs:
        try:
            data = _load_json(path)
            results[name] = {
                'status': 'ok',
                'version': data.get('_meta', {}).get('version', 'unknown'),
                'path': str(path)
            }
        except FileNotFoundError:
            results[name] = {
                'status': 'missing',
                'path': str(path)
            }
        except json.JSONDecodeError as e:
            results[name] = {
                'status': 'invalid_json',
                'error': str(e),
                'path': str(path)
            }

    return results


# Test
if __name__ == '__main__':
    print("=" * 60)
    print("CONFIG LOADER TEST")
    print("=" * 60)

    # Validar configuración
    print("\n[VALIDACION]")
    validation = validate_config()
    for name, result in validation.items():
        status = result['status']
        version = result.get('version', 'N/A')
        print(f"  {name}: {status} (v{version})")

    # Test valores específicos
    print("\n[VALORES DE CONFIGURACION]")
    print(f"  pesos.titulo: {get_config('pesos.titulo')}")
    print(f"  pesos.skills: {get_config('pesos.skills')}")
    print(f"  thresholds.confirmado_score: {get_config('thresholds.confirmado_score')}")
    print(f"  busqueda.top_k_candidatos: {get_config('busqueda.top_k_candidatos')}")

    # Test pesos dinámicos
    print("\n[PESOS DINAMICOS]")
    for level in ['alta', 'media', 'baja']:
        pesos = get_pesos(level)
        print(f"  coverage_{level}: titulo={pesos['titulo']}, skills={pesos['skills']}")

    # Test familias
    print("\n[FAMILIAS FUNCIONALES]")
    familias = get_matching_rules().get('familias', {})
    print(f"  Total familias: {len(familias)}")
    for familia in list(familias.keys())[:3]:
        keywords = get_familia_keywords(familia)
        print(f"  {familia}: {len(keywords)} keywords")

    # Test niveles
    print("\n[NIVELES JERARQUICOS]")
    for nivel in ['director', 'gerente', 'asistente', 'operario']:
        valor = get_nivel_valor(nivel)
        keywords = get_nivel_keywords(nivel)
        print(f"  {nivel}: valor={valor}, keywords={len(keywords)}")

    # Test boost
    print("\n[BOOST ARGENTINO]")
    print(f"  exact_isco: {get_boost_isco('exact_isco')}")
    print(f"  isco_group: {get_boost_isco('isco_group')}")
    print(f"  wrong_isco: {get_boost_isco('wrong_isco')}")

    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    print("=" * 60)
