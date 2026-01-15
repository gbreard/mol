#!/usr/bin/env python3
"""
Script para exportar ubicaciones ambiguas para validación manual
================================================================

Identifica las 50 ubicaciones más ambiguas en la BD y las exporta
a CSV para revisión manual.

Criterios de ambigüedad:
- Buenos Aires ambiguo (ciudad vs provincia)
- Abreviaturas no estándar (Cap Fed, CABA, Bs As)
- Múltiples comas en formato
- Sin provincia normalizada
- Localidad igual a provincia

Uso:
    python export_ambiguous_locations.py
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime


def export_ambiguous_locations(db_path, output_csv="ubicaciones_ambiguas_validacion.csv", limit=50):
    """
    Exporta ubicaciones ambiguas para validación manual

    Args:
        db_path: Ruta a la base de datos
        output_csv: Archivo CSV de salida
        limit: Número de ubicaciones a exportar
    """
    print("=" * 70)
    print("EXPORTACION DE UBICACIONES AMBIGUAS")
    print("=" * 70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base de datos: {db_path}")
    print(f"Ubicaciones a exportar: {limit}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query para identificar ubicaciones ambiguas
    query = """
    WITH ubicaciones_stats AS (
        SELECT
            localizacion AS ubicacion_original,
            provincia_normalizada,
            codigo_provincia_indec,
            localidad_normalizada,
            COUNT(*) as cantidad_ofertas,
            MIN(id_oferta) as ejemplo_id_oferta
        FROM ofertas
        WHERE localizacion IS NOT NULL
        GROUP BY localizacion, provincia_normalizada, codigo_provincia_indec, localidad_normalizada
    ),

    ubicaciones_con_ambiguedad AS (
        SELECT
            *,
            -- Score de ambigüedad (0-100)
            (
                -- Buenos Aires ambiguo (+40 puntos)
                CASE
                    WHEN ubicacion_original LIKE '%Buenos Aires%'
                         AND ubicacion_original NOT LIKE '%Ciudad%'
                         AND ubicacion_original NOT LIKE '%CABA%'
                         AND provincia_normalizada = 'Buenos Aires'
                    THEN 40
                    ELSE 0
                END
                +
                -- Abreviaturas (+30 puntos)
                CASE
                    WHEN ubicacion_original LIKE '%Cap%Fed%' OR
                         ubicacion_original LIKE '%CABA%' OR
                         ubicacion_original LIKE '%Bs%As%' OR
                         ubicacion_original LIKE '%C.A.B.A.%'
                    THEN 30
                    ELSE 0
                END
                +
                -- Múltiples comas (+20 puntos)
                CASE
                    WHEN LENGTH(ubicacion_original) - LENGTH(REPLACE(ubicacion_original, ',', '')) > 1
                    THEN 20
                    ELSE 0
                END
                +
                -- Sin provincia normalizada (+50 puntos - MUY AMBIGUO)
                CASE
                    WHEN provincia_normalizada IS NULL
                    THEN 50
                    ELSE 0
                END
                +
                -- Localidad igual a provincia (+15 puntos)
                CASE
                    WHEN localidad_normalizada = provincia_normalizada
                    THEN 15
                    ELSE 0
                END
            ) AS score_ambiguedad

        FROM ubicaciones_stats
    )

    SELECT
        ubicacion_original,
        provincia_normalizada,
        codigo_provincia_indec,
        localidad_normalizada,
        cantidad_ofertas,
        ejemplo_id_oferta,
        score_ambiguedad,
        -- Clasificación de ambigüedad
        CASE
            WHEN score_ambiguedad >= 50 THEN 'CRITICA'
            WHEN score_ambiguedad >= 30 THEN 'ALTA'
            WHEN score_ambiguedad >= 15 THEN 'MEDIA'
            ELSE 'BAJA'
        END as nivel_ambiguedad

    FROM ubicaciones_con_ambiguedad
    WHERE score_ambiguedad > 0
    ORDER BY
        score_ambiguedad DESC,
        cantidad_ofertas DESC
    LIMIT ?
    """

    cursor.execute(query, (limit,))
    ubicaciones = cursor.fetchall()

    if len(ubicaciones) == 0:
        print("[INFO] No se encontraron ubicaciones ambiguas")
        conn.close()
        return

    print(f"[OK] {len(ubicaciones)} ubicaciones ambiguas identificadas\n")

    # Estadísticas por nivel de ambigüedad
    from collections import Counter
    niveles = Counter([u[7] for u in ubicaciones])
    print("Distribución por nivel de ambigüedad:")
    for nivel in ['CRITICA', 'ALTA', 'MEDIA', 'BAJA']:
        count = niveles.get(nivel, 0)
        if count > 0:
            print(f"  - {nivel}: {count} ubicaciones")

    # Exportar a CSV
    output_path = Path(db_path).parent / output_csv

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "ubicacion_original",
            "provincia_normalizada_actual",
            "codigo_provincia_actual",
            "localidad_normalizada_actual",
            "cantidad_ofertas",
            "ejemplo_id_oferta",
            "score_ambiguedad",
            "nivel_ambiguedad",
            # Columnas para validación manual:
            "provincia_normalizada_CORRECTA",
            "codigo_provincia_CORRECTO",
            "localidad_normalizada_CORRECTA",
            "comentarios"
        ])

        # Datos
        for ub in ubicaciones:
            writer.writerow(list(ub) + ["", "", "", ""])

    conn.close()

    print(f"\n[OK] Ubicaciones exportadas a: {output_path}")
    print("\nPROXIMOS PASOS:")
    print("1. Abrir archivo CSV con Excel")
    print("2. Para cada ubicación:")
    print("   - Revisar ejemplo_id_oferta en BD")
    print("   - Leer descripción completa de la oferta")
    print("   - Verificar si provincia/localidad son correctas")
    print("   - Completar columnas '*_CORRECTA' si hay error")
    print("3. Guardar CSV con correcciones")
    print("4. Ejecutar: python apply_location_corrections.py")

    # Tabla de referencia rápida
    print("\n" + "=" * 70)
    print("TABLA DE REFERENCIA - CODIGOS INDEC")
    print("=" * 70)
    print("\nCódigo | Provincia                        | Variantes comunes")
    print("-" * 70)
    print("  02   | Ciudad de Buenos Aires           | CABA, Cap Fed, Capital")
    print("  06   | Buenos Aires                     | Bs As, Pcia Bs As, GBA")
    print("  14   | Córdoba                          | Cordoba (sin tilde)")
    print("  82   | Santa Fe                         | Sta Fe")
    print("  90   | Tucumán                          | Tucuman (sin tilde)")
    print("  58   | Neuquén                          | Neuquen (sin tilde)")
    print("  30   | Entre Ríos                       | Entre Rios (sin tilde)")
    print("  62   | Río Negro                        | Rio Negro (sin tilde)")
    print("  94   | Tierra del Fuego                 | TDF")
    print("\nVer tabla completa en: database/populate_indec_provincias.py")

    print("\n" + "=" * 70)
    print("EXPORTACION COMPLETADA")
    print("=" * 70)


def main():
    """Ejecuta la exportación"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    export_ambiguous_locations(str(db_path), limit=50)


if __name__ == "__main__":
    main()
