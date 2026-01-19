#!/usr/bin/env python3
"""
Script para cargar códigos INDEC de provincias argentinas
==========================================================

Crea la tabla indec_provincias y la pobla con los 24 códigos oficiales.

Uso:
    python populate_indec_provincias.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Códigos INDEC oficiales de las 24 provincias argentinas
PROVINCIAS_INDEC = {
    "02": {
        "nombre_oficial": "Ciudad Autónoma de Buenos Aires",
        "nombre_comun": "CABA",
        "variantes": ["Capital Federal", "Ciudad de Buenos Aires", "Buenos Aires Capital", "C.A.B.A."]
    },
    "06": {
        "nombre_oficial": "Buenos Aires",
        "nombre_comun": "Buenos Aires",
        "variantes": ["Provincia de Buenos Aires", "Bs. As.", "Bs As", "Pcia. Bs. As.", "Prov. Buenos Aires"]
    },
    "10": {
        "nombre_oficial": "Catamarca",
        "nombre_comun": "Catamarca",
        "variantes": []
    },
    "14": {
        "nombre_oficial": "Córdoba",
        "nombre_comun": "Córdoba",
        "variantes": ["Cordoba"]
    },
    "18": {
        "nombre_oficial": "Corrientes",
        "nombre_comun": "Corrientes",
        "variantes": []
    },
    "22": {
        "nombre_oficial": "Chaco",
        "nombre_comun": "Chaco",
        "variantes": []
    },
    "26": {
        "nombre_oficial": "Chubut",
        "nombre_comun": "Chubut",
        "variantes": []
    },
    "30": {
        "nombre_oficial": "Entre Ríos",
        "nombre_comun": "Entre Ríos",
        "variantes": ["Entre Rios"]
    },
    "34": {
        "nombre_oficial": "Formosa",
        "nombre_comun": "Formosa",
        "variantes": []
    },
    "38": {
        "nombre_oficial": "Jujuy",
        "nombre_comun": "Jujuy",
        "variantes": []
    },
    "42": {
        "nombre_oficial": "La Pampa",
        "nombre_comun": "La Pampa",
        "variantes": []
    },
    "46": {
        "nombre_oficial": "La Rioja",
        "nombre_comun": "La Rioja",
        "variantes": []
    },
    "50": {
        "nombre_oficial": "Mendoza",
        "nombre_comun": "Mendoza",
        "variantes": []
    },
    "54": {
        "nombre_oficial": "Misiones",
        "nombre_comun": "Misiones",
        "variantes": []
    },
    "58": {
        "nombre_oficial": "Neuquén",
        "nombre_comun": "Neuquén",
        "variantes": ["Neuquen"]
    },
    "62": {
        "nombre_oficial": "Río Negro",
        "nombre_comun": "Río Negro",
        "variantes": ["Rio Negro"]
    },
    "66": {
        "nombre_oficial": "Salta",
        "nombre_comun": "Salta",
        "variantes": []
    },
    "70": {
        "nombre_oficial": "San Juan",
        "nombre_comun": "San Juan",
        "variantes": []
    },
    "74": {
        "nombre_oficial": "San Luis",
        "nombre_comun": "San Luis",
        "variantes": []
    },
    "78": {
        "nombre_oficial": "Santa Cruz",
        "nombre_comun": "Santa Cruz",
        "variantes": []
    },
    "82": {
        "nombre_oficial": "Santa Fe",
        "nombre_comun": "Santa Fe",
        "variantes": []
    },
    "86": {
        "nombre_oficial": "Santiago del Estero",
        "nombre_comun": "Santiago del Estero",
        "variantes": []
    },
    "90": {
        "nombre_oficial": "Tucumán",
        "nombre_comun": "Tucumán",
        "variantes": ["Tucuman"]
    },
    "94": {
        "nombre_oficial": "Tierra del Fuego",
        "nombre_comun": "Tierra del Fuego",
        "variantes": ["Tierra del Fuego, Antártida e Islas del Atlántico Sur", "TDF"]
    }
}


def create_table(cursor):
    """Crea la tabla indec_provincias si no existe"""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indec_provincias (
            codigo_provincia TEXT PRIMARY KEY,
            nombre_oficial TEXT NOT NULL,
            nombre_comun TEXT NOT NULL,
            variantes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("[OK] Tabla indec_provincias creada")


def populate_provincias(cursor):
    """Inserta las 24 provincias en la tabla"""

    inserted = 0
    updated = 0

    for codigo, data in PROVINCIAS_INDEC.items():
        # Convertir variantes a JSON string
        variantes_json = json.dumps(data["variantes"], ensure_ascii=False)

        # Intentar insertar, si ya existe actualizar
        try:
            cursor.execute("""
                INSERT INTO indec_provincias (codigo_provincia, nombre_oficial, nombre_comun, variantes)
                VALUES (?, ?, ?, ?)
            """, (codigo, data["nombre_oficial"], data["nombre_comun"], variantes_json))
            inserted += 1
        except sqlite3.IntegrityError:
            # Ya existe, actualizar
            cursor.execute("""
                UPDATE indec_provincias
                SET nombre_oficial = ?,
                    nombre_comun = ?,
                    variantes = ?
                WHERE codigo_provincia = ?
            """, (data["nombre_oficial"], data["nombre_comun"], variantes_json, codigo))
            updated += 1

    return inserted, updated


def validate_data(cursor):
    """Valida que se cargaron las 24 provincias correctamente"""

    cursor.execute("SELECT COUNT(*) FROM indec_provincias")
    total = cursor.fetchone()[0]

    if total != 24:
        raise ValueError(f"Error: Se esperaban 24 provincias pero hay {total}")

    print(f"[OK] Validacion exitosa: {total} provincias cargadas")

    # Mostrar muestra
    cursor.execute("""
        SELECT codigo_provincia, nombre_comun, variantes
        FROM indec_provincias
        ORDER BY codigo_provincia
        LIMIT 5
    """)

    print("\nMuestra de provincias cargadas:")
    print("-" * 70)
    for codigo, nombre, variantes_json in cursor.fetchall():
        variantes = json.loads(variantes_json)
        var_str = f" (variantes: {len(variantes)})" if variantes else ""
        print(f"  {codigo}: {nombre}{var_str}")


def main():
    """Ejecuta el proceso de carga"""

    print("=" * 70)
    print("CARGA DE PROVINCIAS INDEC")
    print("=" * 70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Provincias a cargar: {len(PROVINCIAS_INDEC)}\n")

    # Conectar a BD
    db_path = Path(__file__).parent / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Crear tabla
        create_table(cursor)

        # Poblar datos
        print("\nCargando provincias...")
        inserted, updated = populate_provincias(cursor)
        print(f"  Insertadas: {inserted}")
        print(f"  Actualizadas: {updated}")

        # Commit
        conn.commit()
        print("\n[OK] Datos guardados en BD")

        # Validar
        print("\nValidando...")
        validate_data(cursor)

        print("\n" + "=" * 70)
        print("CARGA COMPLETADA EXITOSAMENTE")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {str(e)}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
