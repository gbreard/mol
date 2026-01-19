#!/usr/bin/env python3
"""
Script para procesar las 50 ofertas del archivo ids_for_ab_test.txt
"""
import sys
import sqlite3
from pathlib import Path

# Importar el extractor híbrido
sys.path.insert(0, str(Path(__file__).parent))
from process_nlp_from_db_v5 import NLPExtractorV5

def main():
    # Leer IDs del archivo
    ids_file = Path(__file__).parent / "ids_for_ab_test.txt"
    with open(ids_file, 'r') as f:
        ids = [int(line.strip()) for line in f if line.strip()]

    print(f"=" * 70)
    print(f"PROCESANDO {len(ids)} OFERTAS PARA COMPARACIÓN A/B")
    print(f"=" * 70)
    print()

    # Conectar a la DB para obtener descripciones
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear extractor
    extractor = NLPExtractorV5()

    # Procesar ofertas una por una
    success = 0
    errors = 0

    for i, id_oferta in enumerate(ids, 1):
        print(f"[{i}/{len(ids)}] Procesando {id_oferta}... ", end='', flush=True)
        try:
            # Obtener descripción y título de la DB
            cursor.execute("SELECT titulo, descripcion FROM ofertas WHERE id_oferta = ?", (id_oferta,))
            row = cursor.fetchone()

            if not row or not row[1]:
                print("ERROR: Sin descripción")
                errors += 1
                continue

            titulo = row[0]
            descripcion = row[1]

            # Procesar con el extractor (v5.1 requiere titulo para inferencias)
            result = extractor.process_oferta(id_oferta, descripcion, titulo)

            if result and result.get("extracted_data"):
                # Guardar en DB
                extractor.save_to_history(result)
                print("OK")
                success += 1
            else:
                print("ERROR")
                errors += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    conn.close()

    print()
    print(f"=" * 70)
    print(f"RESULTADO:")
    print(f"  Éxitos: {success}/{len(ids)} ({success/len(ids)*100:.1f}%)")
    print(f"  Errores: {errors}")
    print(f"=" * 70)

    return 0 if success >= len(ids) * 0.95 else 1

if __name__ == '__main__':
    sys.exit(main())
