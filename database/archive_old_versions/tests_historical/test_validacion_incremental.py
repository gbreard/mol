#!/usr/bin/env python3
"""
Test de validacion incremental - Re-ejecuta NLP sobre casos especificos
para verificar mejoras en el prompt v6.2
"""

import sys
import sqlite3
import json
from pathlib import Path

# Agregar paths para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "02.5_nlp_extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"))

from process_nlp_from_db_v6 import NLPExtractorV6


def test_ofertas_validacion():
    """Ejecuta NLP sobre las ofertas de validacion"""

    db_path = Path(__file__).parent / "bumeran_scraping.db"
    extractor = NLPExtractorV6(str(db_path), verbose=True)

    # IDs a testear - ofertas representativas
    # 2163782: Analista de Investigacion (consultora arearh) - probar empresa_publicadora
    # 2154549: Contador Auditoria - probar nivel_educativo universitario
    test_ids = ["2163782", "2154549"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    results = {}

    for id_oferta in test_ids:
        print(f"\n{'='*60}")
        print(f"Procesando: {id_oferta}")
        print('='*60)

        # Obtener datos de la oferta
        cursor = conn.execute("""
            SELECT id_oferta, titulo, descripcion
            FROM ofertas
            WHERE id_oferta = ?
        """, (id_oferta,))

        row = cursor.fetchone()
        if not row:
            print(f"ERROR: No se encontro oferta {id_oferta}")
            continue

        titulo = row['titulo']
        descripcion = row['descripcion']

        print(f"Titulo: {titulo}")
        print(f"Descripcion: {descripcion[:200] if descripcion else 'SIN DESCRIPCION'}...")

        # Ejecutar extraccion NLP
        try:
            result = extractor.process_oferta(id_oferta, descripcion, titulo)
            results[id_oferta] = {
                'titulo': titulo,
                'extraccion': result,
                'status': 'OK'
            }

            # Mostrar campos criticos
            print("\n--- CAMPOS CRITICOS ---")
            campos_criticos = [
                'skills_tecnicas_list',
                'responsabilidades_list',
                'empresa_publicadora',
                'empresa_contratante',
                'nivel_educativo',
                'estado_educativo',
                'carrera_especifica',
                'nivel_seniority',
                'indexacion_salarial'
            ]

            for campo in campos_criticos:
                valor = result.get(campo, 'NO EXTRAIDO')
                print(f"  {campo}: {valor}")

        except Exception as e:
            print(f"ERROR: {e}")
            results[id_oferta] = {'status': 'ERROR', 'error': str(e)}

    conn.close()

    # Guardar resultados
    output_file = Path(__file__).parent / "test_validacion_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n\nResultados guardados en: {output_file}")
    return results


if __name__ == "__main__":
    test_ofertas_validacion()
