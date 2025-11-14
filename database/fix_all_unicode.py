#!/usr/bin/env python3
"""
Script para encontrar y reemplazar TODOS los caracteres Unicode en los archivos.
"""

import os
import re
from pathlib import Path

# Archivos a procesar
FILES = [
    'fix_encoding_db.py',
    'create_tables_nlp_esco.py',
    'populate_esco_from_rdf.py',
    'populate_dictionaries.py',
    'migrate_nlp_csv_to_db.py',
    'match_ofertas_to_esco.py'
]

def fix_unicode_in_file(filepath):
    """Reemplaza TODOS los caracteres Unicode especiales por ASCII"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Reemplazar cualquier caracter Unicode fuera del rango ASCII
    # Esto incluye todos los emojis, símbolos especiales, etc.
    def replace_unicode(match):
        char = match.group(0)
        code = ord(char)

        # Mapa de reemplazos conocidos
        replacements = {
            '\u2713': '[OK]',       # ✓
            '\u2717': '[ERROR]',    # ✗
            '\u26a0': '[WARNING]',  # ⚠
            '\U0001f4ca': '[STATS]', # 📊
            '\U0001f4c2': '[FILE]',  # 📂
            '\U0001f916': '[BOT]',   # 🤖
            '\U0001f3af': '[TARGET]',# 🎯
            '\U0001f517': '[LINK]',  # 🔗
            '\U0001f30e': '[WORLD]', # 🌎
            '\U0001f4da': '[BOOK]',  # 📚
            '\u2192': '->',         # →
            '\U0001f4c8': '[CHART]', # 📈
            '\U0001f4dd': '[MEMO]',  # 📝
            '\U0001f1e6': '[A]',     # 🇦 (Regional A)
            '\U0001f1f7': '[R]',     # 🇷 (Regional R)
            '\U0001f1ea': '[E]',     # 🇪 (Regional E)
            '\U0001f1fa': '[U]',     # 🇺 (Regional U)
            '\u2022': '-',          # •
            '\u2299': '(x)',        # ⊙
        }

        if char in replacements:
            return replacements[char]

        # Para otros caracteres Unicode, usar representación simple
        if code > 127:
            return f'[U+{code:04X}]'

        return char

    # Patrón para encontrar todos los caracteres no-ASCII
    pattern = re.compile(r'[^\x00-\x7F]')
    content = pattern.sub(replace_unicode, content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False

def main():
    print("="*70)
    print("REEMPLAZO COMPLETO DE CARACTERES UNICODE")
    print("="*70)

    base_dir = Path(__file__).parent
    modified_count = 0

    for filename in FILES:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"\nProcesando: {filename}")
            if fix_unicode_in_file(filepath):
                print(f"  -> Modificado")
                modified_count += 1
            else:
                print(f"  -> Sin cambios")
        else:
            print(f"\n[WARNING] No encontrado: {filename}")

    print("\n" + "="*70)
    print(f"COMPLETADO: {modified_count} archivos modificados")
    print("="*70)

if __name__ == '__main__':
    main()
