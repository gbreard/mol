# -*- coding: utf-8 -*-
"""
Text Cleaner - Utilidades de limpieza y normalización de texto
===============================================================

Módulo para limpieza básica de texto antes de extracción NLP.
Incluye normalización de espacios, caracteres especiales, y texto.
"""

import re
import unicodedata
from typing import Optional


class TextCleaner:
    """Limpiador de texto para descripciones de ofertas laborales"""

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        Limpia espacios múltiples, tabs, y saltos de línea excesivos

        Args:
            text: Texto a limpiar

        Returns:
            Texto con espacios normalizados
        """
        if not text:
            return ""

        # Normalizar diferentes tipos de espacios a espacio normal
        text = re.sub(r'[\xa0\u200b\u2009\u200a]', ' ', text)

        # Eliminar tabs y reemplazar por espacio
        text = text.replace('\t', ' ')

        # Eliminar espacios múltiples
        text = re.sub(r' +', ' ', text)

        # Eliminar líneas vacías múltiples (dejar máximo 2 saltos)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Eliminar espacios al inicio/fin de cada línea
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normaliza caracteres Unicode (acentos, símbolos)

        Args:
            text: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not text:
            return ""

        # Normalizar a forma NFD (descomponer acentos)
        text = unicodedata.normalize('NFD', text)

        # Eliminar caracteres de control excepto saltos de línea y tabs
        text = ''.join(
            char for char in text
            if unicodedata.category(char)[0] != 'C' or char in '\n\t'
        )

        # Recomponer a NFC
        text = unicodedata.normalize('NFC', text)

        return text

    @staticmethod
    def remove_special_chars(text: str, keep_basic_punctuation: bool = True) -> str:
        """
        Elimina caracteres especiales manteniendo puntuación básica

        Args:
            text: Texto a limpiar
            keep_basic_punctuation: Si True, mantiene . , ; : ( ) -

        Returns:
            Texto sin caracteres especiales
        """
        if not text:
            return ""

        if keep_basic_punctuation:
            # Mantener letras, números, espacios y puntuación básica
            text = re.sub(r'[^a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9\s.,;:()\-/+%$]', '', text)
        else:
            # Solo letras, números y espacios
            text = re.sub(r'[^a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9\s]', '', text)

        return text

    @staticmethod
    def normalize_bullets(text: str) -> str:
        """
        Normaliza bullets y listas a formato estándar

        Args:
            text: Texto con bullets

        Returns:
            Texto con bullets normalizados
        """
        if not text:
            return ""

        # Reemplazar diferentes tipos de bullets por -
        bullets = r'[•●○◦▪▫■□‣⁃◆◇★☆►▸»›]'
        text = re.sub(f'^\\s*{bullets}\\s*', '- ', text, flags=re.MULTILINE)

        # Normalizar números de lista: "1)", "1.", "1-" -> "1. "
        text = re.sub(r'^(\s*\d+)[.)\-]\s*', r'\1. ', text, flags=re.MULTILINE)

        return text

    @staticmethod
    def remove_urls(text: str) -> str:
        """
        Elimina URLs del texto

        Args:
            text: Texto con URLs

        Returns:
            Texto sin URLs
        """
        if not text:
            return ""

        # Eliminar URLs http/https
        text = re.sub(r'https?://\S+', '', text)

        # Eliminar URLs www
        text = re.sub(r'www\.\S+', '', text)

        return text

    @staticmethod
    def remove_emails(text: str) -> str:
        """
        Elimina emails del texto

        Args:
            text: Texto con emails

        Returns:
            Texto sin emails
        """
        if not text:
            return ""

        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

        return text

    @staticmethod
    def clean_full(
        text: str,
        remove_urls: bool = True,
        remove_emails: bool = True,
        normalize_bullets: bool = True
    ) -> str:
        """
        Limpieza completa aplicando todos los métodos

        Args:
            text: Texto a limpiar
            remove_urls: Si True, elimina URLs
            remove_emails: Si True, elimina emails
            normalize_bullets: Si True, normaliza bullets

        Returns:
            Texto limpio
        """
        if not text:
            return ""

        # 1. Normalizar Unicode
        text = TextCleaner.normalize_unicode(text)

        # 2. Eliminar URLs y emails si requerido
        if remove_urls:
            text = TextCleaner.remove_urls(text)
        if remove_emails:
            text = TextCleaner.remove_emails(text)

        # 3. Normalizar bullets
        if normalize_bullets:
            text = TextCleaner.normalize_bullets(text)

        # 4. Limpiar espacios
        text = TextCleaner.clean_whitespace(text)

        return text


def clean_text_simple(text: Optional[str]) -> str:
    """
    Función helper para limpieza rápida de texto

    Args:
        text: Texto a limpiar (puede ser None)

    Returns:
        Texto limpio o string vacío
    """
    if not text:
        return ""

    return TextCleaner.clean_full(text)


# Ejemplo de uso
if __name__ == "__main__":
    texto_ejemplo = """
    ¡Buscamos Desarrollador Python! 🚀

    • Experiencia: 3+ años
    •  Conocimientos en Django/Flask
    ●    Inglés intermedio


    Contacto: rrhh@empresa.com
    Web: https://www.empresa.com
    """

    print("TEXTO ORIGINAL:")
    print(texto_ejemplo)
    print("\n" + "="*60 + "\n")

    texto_limpio = TextCleaner.clean_full(texto_ejemplo)
    print("TEXTO LIMPIO:")
    print(texto_limpio)
