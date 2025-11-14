# -*- coding: utf-8 -*-
"""
Encoding Fixer - Normalización de encoding y caracteres
========================================================

Módulo para detectar y corregir problemas de encoding,
especialmente con textos scrapeados de diferentes fuentes.
"""

import re
from typing import Optional


class EncodingFixer:
    """Corrector de problemas de encoding en textos"""

    # Mapeo de caracteres mal codificados comunes (encoding issues)
    ENCODING_FIXES = {
        # Windows-1252 mal interpretado como UTF-8 - vocales con tilde
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ãº': 'ú',
        'Ã±': 'ñ',
        'Ã¼': 'ü',
        # Byte 0xC2 solo (eliminar)
        'Â': '',
    }

    @staticmethod
    def fix_encoding_issues(text: str) -> str:
        """
        Corrige problemas comunes de encoding

        Args:
            text: Texto con problemas de encoding

        Returns:
            Texto con encoding corregido
        """
        if not text:
            return ""

        for wrong, correct in EncodingFixer.ENCODING_FIXES.items():
            text = text.replace(wrong, correct)

        return text

    @staticmethod
    def normalize_quotes(text: str) -> str:
        """
        Normaliza diferentes tipos de comillas a estándar

        Args:
            text: Texto con diferentes comillas

        Returns:
            Texto con comillas normalizadas
        """
        if not text:
            return ""

        # Comillas dobles -> "
        text = re.sub(r'[""„‟«»]', '"', text)

        # Comillas simples -> '
        text = re.sub(r'[''‚‛‹›]', "'", text)

        return text

    @staticmethod
    def normalize_dashes(text: str) -> str:
        """
        Normaliza diferentes tipos de guiones

        Args:
            text: Texto con diferentes guiones

        Returns:
            Texto con guiones normalizados
        """
        if not text:
            return ""

        # Em dash, en dash -> guion normal
        text = re.sub(r'[—–]', '-', text)

        # Múltiples guiones -> uno solo
        text = re.sub(r'-{2,}', '-', text)

        return text

    @staticmethod
    def normalize_spaces(text: str) -> str:
        """
        Normaliza diferentes tipos de espacios a espacio normal

        Args:
            text: Texto con diferentes espacios

        Returns:
            Texto con espacios normalizados
        """
        if not text:
            return ""

        # Non-breaking spaces y otros -> espacio normal
        text = re.sub(r'[\xa0\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000]', ' ', text)

        return text

    @staticmethod
    def remove_zero_width_chars(text: str) -> str:
        """
        Elimina caracteres de ancho cero y caracteres invisibles

        Args:
            text: Texto con caracteres invisibles

        Returns:
            Texto sin caracteres invisibles
        """
        if not text:
            return ""

        # Zero-width characters
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)

        # Byte Order Mark (BOM)
        text = text.replace('\ufeff', '')

        return text

    @staticmethod
    def ensure_utf8(text: str) -> str:
        """
        Asegura que el texto esté en UTF-8 válido

        Args:
            text: Texto a validar

        Returns:
            Texto UTF-8 válido
        """
        if not text:
            return ""

        try:
            # Intentar encodear/decodear para limpiar caracteres inválidos
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            # Si falla, eliminar caracteres no-ASCII problemáticos
            text = ''.join(char for char in text if ord(char) < 128 or ord(char) >= 160)

        return text

    @staticmethod
    def fix_all(text: str) -> str:
        """
        Aplica todas las correcciones de encoding

        Args:
            text: Texto a corregir

        Returns:
            Texto con todas las correcciones aplicadas
        """
        if not text:
            return ""

        # 1. Asegurar UTF-8 válido
        text = EncodingFixer.ensure_utf8(text)

        # 2. Corregir problemas comunes de encoding
        text = EncodingFixer.fix_encoding_issues(text)

        # 3. Eliminar caracteres invisibles
        text = EncodingFixer.remove_zero_width_chars(text)

        # 4. Normalizar espacios
        text = EncodingFixer.normalize_spaces(text)

        # 5. Normalizar comillas
        text = EncodingFixer.normalize_quotes(text)

        # 6. Normalizar guiones
        text = EncodingFixer.normalize_dashes(text)

        return text


def fix_encoding(text: Optional[str]) -> str:
    """
    Función helper para corrección rápida de encoding

    Args:
        text: Texto a corregir (puede ser None)

    Returns:
        Texto corregido o string vacío
    """
    if not text:
        return ""

    return EncodingFixer.fix_all(text)


# Ejemplo de uso
if __name__ == "__main__":
    texto_problematico = """
    Â¡Buscamos desarrollador con experienciÃ¡ en Python!

    Requisitos:
    â€¢ 3+ aÃ±os de experiencia
    â€" Conocimientos en DjangoÂ
    â€œInglÃ©sâ€ intermedio

    SalarioÂ°: $100â€"150k
    """

    print("TEXTO CON PROBLEMAS DE ENCODING:")
    print(texto_problematico)
    print("\n" + "="*60 + "\n")

    texto_corregido = EncodingFixer.fix_all(texto_problematico)
    print("TEXTO CORREGIDO:")
    print(texto_corregido)
