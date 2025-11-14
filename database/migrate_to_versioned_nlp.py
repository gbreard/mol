#!/usr/bin/env python3
"""
Script de Migración: Sistema de Versionado NLP
==============================================

Migra datos existentes de ofertas_nlp a ofertas_nlp_history
preservando versiones v3.7.0 y v4.0.0.

Uso:
    python migrate_to_versioned_nlp.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def ejecutar_migracion(conn):
    """Ejecuta archivo SQL de migración"""
    sql_path = Path(__file__).parent / "migrations" / "add_nlp_history.sql"

    print(f"[1/3] Ejecutando migración SQL: {sql_path.name}")

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()

    print("      [OK] Tabla ofertas_nlp_history creada")
    print("      [OK] Indices creados")


def migrar_datos_existentes(conn):
    """Migra datos de ofertas_nlp a ofertas_nlp_history"""
    cursor = conn.cursor()

    # Verificar si ya existen datos migrados
    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp_history")
    existing = cursor.fetchone()[0]

    if existing > 0:
        print(f"\n[2/3] [!] Ya existen {existing:,} registros en ofertas_nlp_history")
        response = input("      ¿Continuar de todos modos? (s/n): ")
        if response.lower() != 's':
            print("      Migración cancelada")
            return

    print(f"\n[2/3] Migrando datos de ofertas_nlp...")

    # Contar registros a migrar
    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
    total = cursor.fetchone()[0]
    print(f"      Total registros a migrar: {total:,}")

    # Migrar registros
    cursor.execute("""
        SELECT
            id_oferta,
            nlp_version,
            nlp_extraction_timestamp,
            nlp_confidence_score,
            experiencia_min_anios,
            experiencia_max_anios,
            nivel_educativo,
            estado_educativo,
            carrera_especifica,
            idioma_principal,
            nivel_idioma_principal,
            skills_tecnicas_list,
            soft_skills_list,
            certificaciones_list,
            salario_min,
            salario_max,
            moneda,
            beneficios_list,
            requisitos_excluyentes_list,
            requisitos_deseables_list,
            jornada_laboral,
            horario_flexible
        FROM ofertas_nlp
    """)

    registros = cursor.fetchall()
    migrados = 0

    for reg in registros:
        id_oferta = reg[0]
        nlp_version = reg[1] or "3.7.0"  # Default si NULL
        timestamp = reg[2] or datetime.now().isoformat()
        confidence = reg[3] or 0.5

        # Construir JSON con datos extraídos
        extracted_data = {
            "experiencia_min_anios": reg[4],
            "experiencia_max_anios": reg[5],
            "nivel_educativo": reg[6],
            "estado_educativo": reg[7],
            "carrera_especifica": reg[8],
            "idioma_principal": reg[9],
            "nivel_idioma_principal": reg[10],
            "skills_tecnicas_list": reg[11],
            "soft_skills_list": reg[12],
            "certificaciones_list": reg[13],
            "salario_min": reg[14],
            "salario_max": reg[15],
            "moneda": reg[16],
            "beneficios_list": reg[17],
            "requisitos_excluyentes_list": reg[18],
            "requisitos_deseables_list": reg[19],
            "jornada_laboral": reg[20],
            "horario_flexible": reg[21]
        }

        # Calcular quality score (número de campos no-null)
        quality_score = sum(1 for v in extracted_data.values() if v is not None)

        # Determinar método de extracción
        if nlp_version == "4.0.0":
            extraction_method = "hybrid_v4"
        else:
            extraction_method = "regex_v3"

        # Insertar en history
        cursor.execute("""
            INSERT INTO ofertas_nlp_history (
                id_oferta,
                nlp_version,
                processed_at,
                extracted_data,
                quality_score,
                confidence_score,
                processing_time_ms,
                is_active,
                extraction_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_oferta,
            nlp_version,
            timestamp,
            json.dumps(extracted_data, ensure_ascii=False),
            quality_score,
            confidence,
            None,  # No tenemos tiempo de procesamiento histórico
            1,     # Marcar como activa (es la versión actual)
            extraction_method
        ))

        migrados += 1

        if migrados % 1000 == 0:
            print(f"      Migrados: {migrados:,}/{total:,}")
            conn.commit()

    conn.commit()
    print(f"      [OK] {migrados:,} registros migrados exitosamente")


def generar_reporte(conn):
    """Genera reporte de migración"""
    cursor = conn.cursor()

    print(f"\n[3/3] Generando reporte...")

    # Total por versión
    cursor.execute("""
        SELECT nlp_version, COUNT(*), AVG(quality_score), AVG(confidence_score)
        FROM ofertas_nlp_history
        GROUP BY nlp_version
        ORDER BY nlp_version
    """)

    print("\n" + "="*70)
    print("REPORTE DE MIGRACIÓN")
    print("="*70)

    for row in cursor.fetchall():
        version, count, avg_quality, avg_confidence = row
        print(f"\nVersión {version}:")
        print(f"  Registros:     {count:,}")
        print(f"  Quality avg:   {avg_quality:.2f}/7")
        print(f"  Confidence:    {avg_confidence:.2f}")

    # Total general
    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp_history")
    total = cursor.fetchone()[0]

    print(f"\n{'='*70}")
    print(f"TOTAL MIGRADO: {total:,} registros")
    print(f"{'='*70}\n")

    # Verificar ofertas sin NLP en history
    cursor.execute("""
        SELECT COUNT(*)
        FROM ofertas o
        WHERE NOT EXISTS (
            SELECT 1 FROM ofertas_nlp_history h
            WHERE h.id_oferta = o.id_oferta
        )
    """)
    sin_nlp = cursor.fetchone()[0]

    if sin_nlp > 0:
        print(f"[!] {sin_nlp:,} ofertas AUN sin datos NLP")
    else:
        print("[OK] Todas las ofertas tienen datos NLP migrados")


def main():
    print("="*70)
    print("MIGRACIÓN A SISTEMA DE VERSIONADO NLP")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Conectar a DB
        conn = conectar_db()
        print(f"[OK] Conectado a base de datos\n")

        # Ejecutar migración
        ejecutar_migracion(conn)

        # Migrar datos
        migrar_datos_existentes(conn)

        # Reporte
        generar_reporte(conn)

        conn.close()

        print("\n[OK] Migracion completada exitosamente")
        print("\nProximos pasos:")
        print("  1. Verificar datos con: SELECT * FROM ofertas_nlp_history LIMIT 10;")
        print("  2. Continuar con FASE 2: Generador de Contexto RAG")

    except Exception as e:
        print(f"\n[ERROR] ERROR durante migracion: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
