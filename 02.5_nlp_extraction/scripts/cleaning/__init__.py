# -*- coding: utf-8 -*-
"""
Cleaning Package - Módulos de limpieza de texto
===============================================

Paquete con utilidades para limpieza y normalización de texto
antes de extracción NLP.
"""

from .text_cleaner import TextCleaner, clean_text_simple
from .html_stripper import HTMLStripper, strip_html
from .encoding_fixer import EncodingFixer, fix_encoding

__all__ = [
    'TextCleaner',
    'clean_text_simple',
    'HTMLStripper',
    'strip_html',
    'EncodingFixer',
    'fix_encoding',
]
