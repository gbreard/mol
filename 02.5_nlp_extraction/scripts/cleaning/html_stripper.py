# -*- coding: utf-8 -*-
"""
HTML Stripper - Limpieza de HTML y Markdown
============================================

Módulo para eliminar tags HTML, markdown y formateo web de textos.
"""

import re
import html
from typing import Optional


class HTMLStripper:
    """Eliminador de HTML y markdown de textos"""

    @staticmethod
    def unescape_html(text: str) -> str:
        """
        Decodifica entidades HTML (&amp; -> &, &lt; -> <, etc.)

        Args:
            text: Texto con entidades HTML

        Returns:
            Texto decodificado
        """
        if not text:
            return ""

        return html.unescape(text)

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Elimina tags HTML manteniendo el contenido

        Args:
            text: Texto con HTML

        Returns:
            Texto sin tags HTML
        """
        if not text:
            return ""

        # Convertir <br>, <br/>, <br /> a saltos de línea
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

        # Convertir </p>, </div>, </li> a saltos de línea
        text = re.sub(r'</(p|div|li|h[1-6])>', '\n\n', text, flags=re.IGNORECASE)

        # Eliminar todos los demás tags HTML
        text = re.sub(r'<[^>]+>', '', text)

        return text

    @staticmethod
    def remove_html_comments(text: str) -> str:
        """
        Elimina comentarios HTML <!-- -->

        Args:
            text: Texto con comentarios

        Returns:
            Texto sin comentarios
        """
        if not text:
            return ""

        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        return text

    @staticmethod
    def remove_css_style(text: str) -> str:
        """
        Elimina bloques <style> y atributos style

        Args:
            text: Texto con CSS

        Returns:
            Texto sin CSS
        """
        if not text:
            return ""

        # Eliminar bloques <style>...</style>
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Eliminar atributos style="..."
        text = re.sub(r'\sstyle="[^"]*"', '', text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def remove_javascript(text: str) -> str:
        """
        Elimina bloques <script>

        Args:
            text: Texto con JavaScript

        Returns:
            Texto sin JavaScript
        """
        if not text:
            return ""

        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

        return text

    @staticmethod
    def remove_markdown(text: str) -> str:
        """
        Elimina formateo markdown básico

        Args:
            text: Texto con markdown

        Returns:
            Texto sin markdown
        """
        if not text:
            return ""

        # Eliminar links markdown: [texto](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Eliminar negrita/cursiva: **texto** o *texto*
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)

        # Eliminar negrita/cursiva: __texto__ o _texto_
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # Eliminar headers markdown: ## Titulo
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        # Eliminar código inline: `código`
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Eliminar bloques de código: ```código```
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        return text

    @staticmethod
    def clean_html_full(text: str) -> str:
        """
        Limpieza completa de HTML/CSS/JS

        Args:
            text: Texto con HTML

        Returns:
            Texto limpio
        """
        if not text:
            return ""

        # 1. Decodificar entidades HTML
        text = HTMLStripper.unescape_html(text)

        # 2. Eliminar JavaScript
        text = HTMLStripper.remove_javascript(text)

        # 3. Eliminar CSS
        text = HTMLStripper.remove_css_style(text)

        # 4. Eliminar comentarios
        text = HTMLStripper.remove_html_comments(text)

        # 5. Eliminar tags HTML
        text = HTMLStripper.remove_html_tags(text)

        # 6. Eliminar markdown
        text = HTMLStripper.remove_markdown(text)

        return text


def strip_html(text: Optional[str]) -> str:
    """
    Función helper para limpieza rápida de HTML

    Args:
        text: Texto con HTML (puede ser None)

    Returns:
        Texto limpio o string vacío
    """
    if not text:
        return ""

    return HTMLStripper.clean_html_full(text)


# Ejemplo de uso
if __name__ == "__main__":
    html_ejemplo = """
    <div class="job-description">
        <h2>Buscamos Desarrollador Python</h2>
        <p><strong>Requisitos:</strong></p>
        <ul>
            <li>3+ años de experiencia</li>
            <li>Conocimientos en <em>Django</em> o Flask</li>
            <li>Inglés intermedio</li>
        </ul>
        <br/>
        <p>Contacto: <a href="mailto:rrhh@empresa.com">rrhh@empresa.com</a></p>
        <!-- Comentario interno -->
        <style>.hidden { display: none; }</style>
    </div>
    """

    markdown_ejemplo = """
    ## Buscamos Desarrollador Python

    **Requisitos:**
    - 3+ años de experiencia
    - Conocimientos en *Django* o Flask
    - Inglés intermedio

    [Aplicar aquí](https://empresa.com/apply)

    Código de ejemplo:
    ```python
    print("Hello World")
    ```
    """

    print("HTML ORIGINAL:")
    print(html_ejemplo)
    print("\n" + "="*60 + "\n")

    html_limpio = HTMLStripper.clean_html_full(html_ejemplo)
    print("HTML LIMPIO:")
    print(html_limpio)

    print("\n" + "="*60 + "\n")
    print("MARKDOWN ORIGINAL:")
    print(markdown_ejemplo)
    print("\n" + "="*60 + "\n")

    markdown_limpio = HTMLStripper.clean_html_full(markdown_ejemplo)
    print("MARKDOWN LIMPIO:")
    print(markdown_limpio)
