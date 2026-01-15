#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
create_validacion_pipeline_table.py
====================================
Crea la tabla validacion_pipeline para feedback estructurado del pipeline.

Permite evaluar cada etapa por separado:
- Scraping (datos crudos)
- NLP (extraccion)
- ESCO (matching)

Con flags de errores especificos para diagnostico.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"


def main():
    print("=" * 70)
    print("CREAR TABLA validacion_pipeline")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si la tabla ya existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='validacion_pipeline'
    """)
    existe = cursor.fetchone()

    if existe:
        print("\n[!] La tabla validacion_pipeline ya existe")
        cursor.execute("SELECT COUNT(*) FROM validacion_pipeline")
        count = cursor.fetchone()[0]
        print(f"    Registros existentes: {count:,}")
    else:
        print("\n[1] Creando tabla validacion_pipeline...")
        cursor.execute("""
            CREATE TABLE validacion_pipeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_oferta TEXT NOT NULL,

                -- Evaluacion por etapa (1-5 cada una)
                score_scraping INTEGER CHECK(score_scraping BETWEEN 1 AND 5),
                score_nlp INTEGER CHECK(score_nlp BETWEEN 1 AND 5),
                score_esco INTEGER CHECK(score_esco BETWEEN 1 AND 5),

                -- Flags de error especificos (SCRAPING)
                error_descripcion_incompleta INTEGER DEFAULT 0,
                error_datos_corruptos INTEGER DEFAULT 0,

                -- Flags de error especificos (NLP)
                error_skills_incorrectos INTEGER DEFAULT 0,
                error_educacion_incorrecta INTEGER DEFAULT 0,
                error_experiencia_incorrecta INTEGER DEFAULT 0,
                error_idiomas_incorrectos INTEGER DEFAULT 0,
                error_salario_incorrecto INTEGER DEFAULT 0,

                -- Flags de error especificos (ESCO)
                error_ocupacion_incorrecta INTEGER DEFAULT 0,
                error_skills_esco_no_matchean INTEGER DEFAULT 0,

                -- Sugerencia de correccion
                ocupacion_esco_sugerida TEXT,
                comentario TEXT,

                -- Metadatos
                validador TEXT DEFAULT 'anonimo',
                timestamp_validacion TEXT DEFAULT (datetime('now')),
                nlp_version_evaluada TEXT,
                matching_version_evaluada TEXT,

                FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
            )
        """)
        print("    [OK] Tabla creada")

        # Crear indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validacion_pipeline_id_oferta
            ON validacion_pipeline(id_oferta)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validacion_pipeline_validador
            ON validacion_pipeline(validador)
        """)
        print("    [OK] Indices creados")

    conn.commit()

    # Mostrar schema
    print("\n[2] Schema de validacion_pipeline:")
    cursor.execute("PRAGMA table_info(validacion_pipeline)")
    for row in cursor.fetchall():
        print(f"    {row[1]:<30} {row[2]}")

    # Estadisticas si hay datos
    cursor.execute("SELECT COUNT(*) FROM validacion_pipeline")
    total = cursor.fetchone()[0]
    if total > 0:
        print(f"\n[3] Estadisticas:")
        cursor.execute("""
            SELECT validador, COUNT(*) as n
            FROM validacion_pipeline
            GROUP BY validador
        """)
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]} validaciones")

    print("\n" + "=" * 70)
    print("[OK] Tabla lista para usar")
    print("=" * 70)
    conn.close()


if __name__ == '__main__':
    main()
