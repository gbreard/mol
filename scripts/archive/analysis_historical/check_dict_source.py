#!/usr/bin/env python3
import json
import os

# Verificar archivo origen
json_path = r'D:\Trabajos en PY\EPH-ESCO\07_esco_data\diccionario_normalizacion_arg_esco.json'

print("=" * 70)
print("VERIFICACION DICCIONARIO ARG-ESCO")
print("=" * 70)

print(f"\nArchivo: {json_path}")
print(f"Existe: {os.path.exists(json_path)}")

if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total terminos en JSON: {len(data)}")

    print("\nPrimeros 10 terminos:")
    for i, k in enumerate(list(data.keys())[:10], 1):
        print(f"  {i}. {k}")

    # Ver estructura de un termino
    primer_termino = list(data.keys())[0]
    print(f"\nEstructura del primer termino '{primer_termino}':")
    print(f"  {data[primer_termino]}")

    # Verificar cuantos estan en DB
    import sqlite3
    conn = sqlite3.connect('bumeran_scraping.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM diccionario_arg_esco')
    db_count = cursor.fetchone()[0]
    conn.close()

    print(f"\nTerminos en DB: {db_count}")
    print(f"Faltantes: {len(data) - db_count}")
else:
    print("ERROR: Archivo no encontrado")
