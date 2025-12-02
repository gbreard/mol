#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_for_validation.py
========================
Exporta datos unificados de las 3 tablas principales para la validación humana.

JOIN: ofertas + ofertas_nlp + ofertas_esco_matching

Output: CSV con campos relevantes para validar matching ESCO
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"
OUTPUT_PATH = Path(__file__).parent / "ofertas_validacion_esco.csv"

def main():
    print("=" * 70)
    print("EXPORTAR DATOS PARA VALIDACIÓN HUMANA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query unificada con los campos más relevantes
    print("\n[1] Ejecutando query unificada...")
    cursor.execute("""
        SELECT
            -- Identificadores
            o.id_oferta,
            o.url_oferta,

            -- Datos de la oferta (para contexto)
            o.titulo,
            o.empresa,
            o.localizacion,
            o.provincia_normalizada,
            o.modalidad_trabajo,
            SUBSTR(o.descripcion, 1, 500) as descripcion_corta,

            -- Datos NLP extraídos
            n.skills_tecnicas_list,
            n.soft_skills_list,
            n.experiencia_min_anios,
            n.experiencia_max_anios,
            n.nivel_educativo,
            n.carrera_especifica,
            n.nlp_version,

            -- Matching ESCO (lo que se valida)
            m.esco_occupation_uri,
            m.esco_occupation_label,
            m.isco_code,
            m.isco_nivel1,
            m.isco_nivel2,

            -- Scores del matching
            m.score_titulo,
            m.score_skills,
            m.score_descripcion,
            m.score_final_ponderado,

            -- Skills matched
            m.skills_oferta_json,
            m.skills_matched_essential,
            m.skills_matched_optional,
            m.skills_cobertura,

            -- Estado actual
            m.match_confirmado,
            m.requiere_revision,

            -- Validación previa (si existe)
            v.score_humano,
            v.comentario as comentario_validacion,
            v.validador,
            v.timestamp_validacion

        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        LEFT JOIN validacion_humana v ON o.id_oferta = v.id_oferta
        ORDER BY
            CASE WHEN m.requiere_revision = 1 THEN 0 ELSE 1 END,
            m.score_final_ponderado ASC
    """)

    rows = cursor.fetchall()
    print(f"    Registros obtenidos: {len(rows):,}")

    # Exportar a CSV
    print(f"\n[2] Exportando a: {OUTPUT_PATH}")

    # Obtener nombres de columnas
    columns = [description[0] for description in cursor.description]

    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)

        for row in rows:
            writer.writerow(list(row))

    # Estadísticas
    print("\n[3] Estadísticas del export:")

    # Contar por estado
    cursor.execute("""
        SELECT
            SUM(CASE WHEN m.match_confirmado = 1 THEN 1 ELSE 0 END) as confirmados,
            SUM(CASE WHEN m.requiere_revision = 1 THEN 1 ELSE 0 END) as revision,
            SUM(CASE WHEN v.score_humano IS NOT NULL THEN 1 ELSE 0 END) as ya_validados
        FROM ofertas o
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        LEFT JOIN validacion_humana v ON o.id_oferta = v.id_oferta
    """)
    stats = cursor.fetchone()

    print(f"    Confirmados automáticamente: {stats['confirmados']:,}")
    print(f"    Requieren revisión:          {stats['revision']:,}")
    print(f"    Ya validados por humano:     {stats['ya_validados'] or 0:,}")

    # Tamaño del archivo
    file_size = OUTPUT_PATH.stat().st_size / 1024 / 1024
    print(f"\n    Archivo generado: {file_size:.2f} MB")

    print("\n" + "=" * 70)
    print(f"[OK] Export completado: {OUTPUT_PATH}")
    print("=" * 70)

    conn.close()


if __name__ == '__main__':
    main()
