#!/usr/bin/env python3
"""
Análisis de Casos de Fallo: v4.0 vs v5.0
=========================================

Identifica y analiza ofertas específicas donde v5.0 perdió
información que v4.0 sí extrajo correctamente.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def obtener_ofertas_con_regresion(conn, campo: str, limit: int = 5) -> List[int]:
    """
    Obtiene ofertas donde v4.0 tenía valor en 'campo' pero v5.0 lo perdió

    Args:
        conn: Conexión a DB
        campo: Campo a analizar (ej: "nivel_educativo", "experiencia_min_anios")
        limit: Cantidad de ejemplos

    Returns:
        Lista de id_oferta con regresión en ese campo
    """
    cursor = conn.cursor()

    # Obtener ofertas con ambas versiones
    cursor.execute("""
        SELECT DISTINCT h4.id_oferta,
               h4.extracted_data as v4_data,
               h5.extracted_data as v5_data
        FROM ofertas_nlp_history h4
        JOIN ofertas_nlp_history h5 ON h4.id_oferta = h5.id_oferta
        WHERE h4.nlp_version = 'v4.0.0'
          AND h5.nlp_version = '5.0.0'
          AND h4.is_active = 1
          AND h5.is_active = 1
        LIMIT 100
    """)

    ofertas_regresion = []

    for row in cursor.fetchall():
        id_oferta = row[0]
        v4_data = json.loads(row[1]) if row[1] else {}
        v5_data = json.loads(row[2]) if row[2] else {}

        v4_val = v4_data.get(campo)
        v5_val = v5_data.get(campo)

        # Regresión: v4 tenía valor, v5 NO
        if v4_val is not None and v5_val is None:
            ofertas_regresion.append(id_oferta)

        if len(ofertas_regresion) >= limit:
            break

    return ofertas_regresion


def obtener_datos_completos(conn, id_oferta: int) -> Dict[str, Any]:
    """
    Obtiene descripción original + extracciones v4 y v5

    Args:
        conn: Conexión a DB
        id_oferta: ID de la oferta

    Returns:
        Dict con toda la información
    """
    cursor = conn.cursor()

    # Descripción original
    cursor.execute("""
        SELECT titulo, descripcion, empresa
        FROM ofertas
        WHERE id_oferta = ?
    """, (id_oferta,))

    oferta_row = cursor.fetchone()

    if not oferta_row:
        return None

    # Extracciones v4 y v5
    cursor.execute("""
        SELECT nlp_version, extracted_data, quality_score, confidence_score
        FROM ofertas_nlp_history
        WHERE id_oferta = ? AND is_active = 1
    """, (id_oferta,))

    extracciones = {}
    for row in cursor.fetchall():
        version = row[0]
        extracciones[version] = {
            "extracted_data": json.loads(row[1]) if row[1] else {},
            "quality_score": row[2],
            "confidence_score": row[3]
        }

    return {
        "id_oferta": id_oferta,
        "titulo": oferta_row[0],
        "descripcion": oferta_row[1],
        "empresa": oferta_row[2],
        "v4": extracciones.get("v4.0.0"),
        "v5": extracciones.get("5.0.0")
    }


def analizar_campo_en_oferta(datos: Dict[str, Any], campo: str):
    """
    Analiza un campo específico en una oferta

    Args:
        datos: Datos completos de la oferta
        campo: Campo a analizar
    """
    print(f"\n{'='*80}")
    print(f"OFERTA ID: {datos['id_oferta']}")
    print(f"CAMPO: {campo}")
    print(f"{'='*80}")

    print(f"\nTITULO: {datos['titulo']}")
    print(f"EMPRESA: {datos['empresa']}")

    # Descripción (primeros 500 caracteres)
    desc_preview = datos['descripcion'][:500] + "..." if len(datos['descripcion']) > 500 else datos['descripcion']
    print(f"\nDESCRIPCION (preview):")
    print(desc_preview)

    # Extracciones
    v4_val = datos['v4']['extracted_data'].get(campo) if datos['v4'] else None
    v5_val = datos['v5']['extracted_data'].get(campo) if datos['v5'] else None

    print(f"\n--- COMPARACION DE EXTRACCION ---")
    print(f"v4.0.0: {v4_val}")
    print(f"v5.0.0: {v5_val}")

    # Scores
    if datos['v4'] and datos['v5']:
        print(f"\nQuality Score:")
        print(f"  v4.0: {datos['v4']['quality_score']}")
        print(f"  v5.0: {datos['v5']['quality_score']}")
        print(f"  Delta: {datos['v5']['quality_score'] - datos['v4']['quality_score']:+d}")

        print(f"\nConfidence Score:")
        print(f"  v4.0: {datos['v4']['confidence_score']:.3f}")
        print(f"  v5.0: {datos['v5']['confidence_score']:.3f}")
        print(f"  Delta: {datos['v5']['confidence_score'] - datos['v4']['confidence_score']:+.3f}")

    # Buscar keyword en descripción
    keywords_educacion = ["educacion", "universitario", "secundario", "terciario", "titulo", "carrera"]
    keywords_experiencia = ["experiencia", "años", "año", "anios", "anio", "senior", "junior"]
    keywords_idioma = ["idioma", "ingles", "english", "portugues", "bilingue"]

    if campo in ["nivel_educativo", "estado_educativo", "carrera_especifica"]:
        keywords = keywords_educacion
    elif campo in ["experiencia_min_anios", "experiencia_max_anios"]:
        keywords = keywords_experiencia
    elif campo in ["idioma_principal", "nivel_idioma_principal"]:
        keywords = keywords_idioma
    else:
        keywords = []

    if keywords:
        desc_lower = datos['descripcion'].lower()
        print(f"\nKEYWORDS RELEVANTES EN DESCRIPCION:")
        for kw in keywords:
            if kw in desc_lower:
                # Encontrar contexto
                idx = desc_lower.find(kw)
                start = max(0, idx - 50)
                end = min(len(desc_lower), idx + 50)
                context = datos['descripcion'][start:end]
                print(f"  '{kw}': ...{context}...")


def main():
    print("="*80)
    print("ANALISIS DE CASOS DE FALLO: v4.0 vs v5.0")
    print("="*80)
    print()

    conn = conectar_db()

    # Campos con mayor regresión según el reporte A/B
    campos_criticos = [
        ("nivel_educativo", "Nivel educativo (55% regresión)"),
        ("experiencia_min_anios", "Experiencia mínima (55% regresión)"),
        ("nivel_idioma_principal", "Nivel de idioma (49% regresión)"),
        ("idioma_principal", "Idioma principal (43% regresión)"),
    ]

    for campo, descripcion in campos_criticos:
        print(f"\n{'#'*80}")
        print(f"ANALIZANDO: {descripcion}")
        print(f"{'#'*80}")

        # Obtener 3 casos de regresión para este campo
        ofertas_ids = obtener_ofertas_con_regresion(conn, campo, limit=3)

        if not ofertas_ids:
            print(f"\n[!] No se encontraron casos de regresión para {campo}")
            continue

        print(f"\n[OK] Encontrados {len(ofertas_ids)} casos de regresión")

        for i, id_oferta in enumerate(ofertas_ids, 1):
            datos = obtener_datos_completos(conn, id_oferta)

            if not datos or not datos['v4'] or not datos['v5']:
                continue

            print(f"\n\n--- CASO {i}/{len(ofertas_ids)} ---")
            analizar_campo_en_oferta(datos, campo)

        print("\n" + "="*80)
        input("\nPresiona ENTER para continuar al siguiente campo...")

    conn.close()

    print("\n\n" + "="*80)
    print("ANALISIS COMPLETADO")
    print("="*80)
    print("\nCONCLUSIONES:")
    print("  - Revisa los casos anteriores para identificar patrones")
    print("  - Observa si v5.0 está ignorando información clara en la descripción")
    print("  - Considera si el prompt necesita ser más específico")
    print("  - Evalúa si la post-validación está siendo muy agresiva")


if __name__ == '__main__':
    main()
