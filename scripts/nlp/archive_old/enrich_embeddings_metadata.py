# -*- coding: utf-8 -*-
"""
Enriquece la metadata de embeddings con códigos ISCO desde la BD.
"""
import json
import sqlite3
from pathlib import Path

EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"
DB_PATH = Path(__file__).parent / "bumeran_scraping.db"

def main():
    # Cargar metadata actual
    meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    print(f"Total registros en metadata: {len(meta)}")

    # Conectar a DB y obtener ISCOs
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Crear mapeo URI -> ISCO
    cursor.execute('SELECT occupation_uri, isco_code FROM esco_occupations')
    uri_to_isco = {}
    for row in cursor.fetchall():
        uri, isco = row
        uri_to_isco[uri] = isco

    conn.close()
    print(f"Ocupaciones en DB: {len(uri_to_isco)}")

    # Enriquecer metadata
    enriquecidos = 0
    for m in meta:
        uri = m.get('uri', '')
        if uri in uri_to_isco:
            m['isco_code'] = uri_to_isco[uri]
            enriquecidos += 1
        else:
            m['isco_code'] = ''

    print(f"Enriquecidos con ISCO: {enriquecidos}")
    print(f"Sin ISCO: {len(meta) - enriquecidos}")

    # Guardar
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\nMetadata actualizada. Primeros 5 registros:")
    for m in meta[:5]:
        isco = m.get('isco_code', 'N/A')
        label = m.get('label', 'N/A')[:50]
        print(f"  ISCO: {isco}, Label: {label}")

if __name__ == "__main__":
    main()
