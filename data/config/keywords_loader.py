"""
Helper para cargar keywords del diccionario maestro
====================================================

Función utilitaria para que todos los scrapers carguen keywords
del mismo diccionario centralizado.
"""

import json
from pathlib import Path
from typing import List


def load_keywords(estrategia: str = "general") -> List[str]:
    """
    Carga keywords desde el diccionario maestro

    Args:
        estrategia: Nombre de la estrategia
            - 'maxima': ~70 keywords (primera ejecución)
            - 'completa': ~40 keywords (normal)
            - 'general': ~20 keywords (rápido)
            - 'tecnologia': ~25 keywords IT
            - 'minima': 4 keywords (testing)
            - etc.

    Returns:
        Lista de keywords

    Examples:
        >>> keywords = load_keywords('general')
        >>> print(len(keywords))
        20
    """
    # Ubicación del diccionario maestro
    config_path = Path(__file__).parent / "master_keywords.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró el diccionario maestro en: {config_path}"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if estrategia not in config['estrategias']:
        available = list(config['estrategias'].keys())
        raise ValueError(
            f"Estrategia '{estrategia}' no encontrada. "
            f"Disponibles: {available}"
        )

    keywords = config['estrategias'][estrategia]['keywords']
    return keywords


def get_available_strategies() -> dict:
    """
    Obtiene todas las estrategias disponibles

    Returns:
        Dict con estrategias y sus descripciones
    """
    config_path = Path(__file__).parent / "master_keywords.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    strategies = {}
    for name, data in config['estrategias'].items():
        strategies[name] = {
            'descripcion': data['descripcion'],
            'cantidad_keywords': len(data['keywords'])
        }

    return strategies


def get_keywords_by_category(categoria: str) -> List[str]:
    """
    Obtiene keywords de una categoría específica

    Args:
        categoria: Nombre de la categoría (ej: 'IT_Tecnologia', 'Salud')

    Returns:
        Lista de keywords de esa categoría
    """
    config_path = Path(__file__).parent / "master_keywords.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if categoria not in config['categorias']:
        available = list(config['categorias'].keys())
        raise ValueError(
            f"Categoría '{categoria}' no encontrada. "
            f"Disponibles: {available}"
        )

    return config['categorias'][categoria]


if __name__ == "__main__":
    # Ejemplos de uso
    print("=== ESTRATEGIAS DISPONIBLES ===")
    strategies = get_available_strategies()
    for name, info in strategies.items():
        print(f"{name:25} - {info['cantidad_keywords']:2} keywords - {info['descripcion']}")

    print("\n=== EJEMPLO: Cargando estrategia 'general' ===")
    keywords = load_keywords('general')
    print(f"Keywords cargadas: {len(keywords)}")
    print(f"Primeras 10: {keywords[:10]}")
