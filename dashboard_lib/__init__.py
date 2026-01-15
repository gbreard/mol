"""
Dashboard Module - Bumeran Scraping v4.5
=========================================

Módulo con funciones de carga de datos y componentes visuales
para el dashboard operativo.

Componentes:
- data_loaders: Funciones de carga de datos de SQLite
- components: Componentes visuales reutilizables para Plotly Dash

Autor: Claude Code (OEDE)
Fecha: 2025-11-04
Versión: 4.5.0
"""

__version__ = '4.5.0'
__author__ = 'Claude Code (OEDE)'

from . import data_loaders
from . import components

__all__ = ['data_loaders', 'components']
