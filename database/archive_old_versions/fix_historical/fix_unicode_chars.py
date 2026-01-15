#!/usr/bin/env python3
"""
Script para reemplazar caracteres Unicode por equivalentes ASCII
en todos los scripts de la base de datos.
"""

import os
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

# Mapeo de Unicode a ASCII
REPLACEMENTS = {
    '✓': '[OK]',
    '✗': '[ERROR]',
    '⚠': '[WARNING]',
    '📊': '[STATS]',
    '📂': '[FILE]',
    '🤖': '[BOT]',
    '🎯': '[TARGET]',
    '🔗': '[LINK]',
    '🌎': '[WORLD]',
    '📚': '[BOOK]',
    '→': '->',
    '📈': '[CHART]',
    '📝': '[MEMO]',
    '🇦🇷': '[ARG]',
    '🇪🇺': '[EU]',
    '•': '-'
}

def fix_file(filepath):
    """Reemplaza caracteres Unicode en un archivo"""
    print(f"\nProcesando: {filepath.name}")

    # Leer archivo con UTF-8
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    replacements_made = {}

    # Hacer reemplazos
    for unicode_char, ascii_equiv in REPLACEMENTS.items():
        count = content.count(unicode_char)
        if count > 0:
            content = content.replace(unicode_char, ascii_equiv)
            replacements_made[unicode_char] = count

    # Escribir de vuelta si hubo cambios
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Reemplazos realizados:")
        for char, count in replacements_made.items():
            ascii_repr = REPLACEMENTS[char]
            # Evitar imprimir caracteres Unicode, solo mostrar el resultado ASCII
            print(f"    Unicode -> '{ascii_repr}': {count} veces")
        return True
    else:
        print(f"  Sin cambios necesarios")
        return False

def main():
    print("="*70)
    print("CORRECCION DE CARACTERES UNICODE -> ASCII")
    print("="*70)

    base_dir = Path(__file__).parent
    files_modified = 0

    for filename in FILES:
        filepath = base_dir / filename
        if filepath.exists():
            if fix_file(filepath):
                files_modified += 1
        else:
            print(f"\n[WARNING] Archivo no encontrado: {filename}")

    print("\n" + "="*70)
    print(f"COMPLETADO: {files_modified} archivos modificados")
    print("="*70)

if __name__ == '__main__':
    main()
