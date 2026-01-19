#!/usr/bin/env python3
"""
Script de Comparación A/B: NLP v4.0 vs v5.0
==========================================

Compara extracciones de v4.0 y v5.0 en las mismas ofertas
para evaluar mejoras y decidir activación.

Uso:
    python compare_nlp_versions.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def obtener_ofertas_con_ambas_versiones(conn, limit: int = None) -> List[int]:
    """
    Obtiene IDs de ofertas que tienen extracción en v4.0 Y v5.0

    Args:
        conn: Conexión a DB
        limit: Limitar cantidad de ofertas (None = todas)

    Returns:
        Lista de id_oferta que tienen ambas versiones
    """
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT h4.id_oferta
        FROM ofertas_nlp_history h4
        JOIN ofertas_nlp_history h5 ON h4.id_oferta = h5.id_oferta
        WHERE h4.nlp_version = 'v4.0.0'
          AND h5.nlp_version = '5.0.0'
          AND h4.is_active = 1
          AND h5.is_active = 1
        ORDER BY h4.id_oferta
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def obtener_extraccion(conn, id_oferta: int, version: str) -> Dict[str, Any]:
    """
    Obtiene datos de extracción de una oferta en una versión específica

    Args:
        conn: Conexión a DB
        id_oferta: ID de la oferta
        version: Versión NLP (ej: "4.0.0" o "5.0.0")

    Returns:
        Dict con datos de la extracción
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            extracted_data,
            quality_score,
            confidence_score,
            processing_time_ms,
            processed_at
        FROM ofertas_nlp_history
        WHERE id_oferta = ? AND nlp_version = ? AND is_active = 1
    """, (id_oferta, version))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        "extracted_data": json.loads(row[0]) if row[0] else {},
        "quality_score": row[1],
        "confidence_score": row[2],
        "processing_time_ms": row[3],
        "processed_at": row[4]
    }


def comparar_campo(v4_val: Any, v5_val: Any, campo: str) -> Dict[str, Any]:
    """
    Compara un campo específico entre v4 y v5

    Returns:
        Dict con análisis de la comparación
    """
    ambos_null = v4_val is None and v5_val is None
    ambos_llenos = v4_val is not None and v5_val is not None

    if ambos_null:
        return {"status": "igual", "tipo": "ambos_null"}

    if v4_val is None and v5_val is not None:
        return {"status": "mejora_v5", "tipo": "v5_agrego", "nuevo": v5_val}

    if v4_val is not None and v5_val is None:
        return {"status": "regresion_v5", "tipo": "v5_perdio", "perdido": v4_val}

    # Ambos tienen valor
    if v4_val == v5_val:
        return {"status": "igual", "tipo": "mismo_valor", "valor": v4_val}
    else:
        return {
            "status": "diferente",
            "tipo": "valores_distintos",
            "v4": v4_val,
            "v5": v5_val
        }


def analizar_comparacion(
    id_oferta: int,
    v4_data: Dict[str, Any],
    v5_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analiza diferencias entre extracciones v4 y v5 de una oferta

    Returns:
        Dict con análisis detallado
    """
    # Campos a comparar
    campos = [
        "experiencia_min_anios", "experiencia_max_anios",
        "nivel_educativo", "estado_educativo", "carrera_especifica",
        "idioma_principal", "nivel_idioma_principal",
        "skills_tecnicas_list", "soft_skills_list", "certificaciones_list",
        "salario_min", "salario_max", "moneda",
        "beneficios_list", "requisitos_excluyentes_list", "requisitos_deseables_list",
        "jornada_laboral", "horario_flexible"
    ]

    comparaciones = {}
    stats = {
        "campos_iguales": 0,
        "campos_mejora_v5": 0,
        "campos_regresion_v5": 0,
        "campos_diferentes": 0
    }

    for campo in campos:
        v4_val = v4_data["extracted_data"].get(campo)
        v5_val = v5_data["extracted_data"].get(campo)

        comp = comparar_campo(v4_val, v5_val, campo)
        comparaciones[campo] = comp

        if comp["status"] == "igual":
            stats["campos_iguales"] += 1
        elif comp["status"] == "mejora_v5":
            stats["campos_mejora_v5"] += 1
        elif comp["status"] == "regresion_v5":
            stats["campos_regresion_v5"] += 1
        elif comp["status"] == "diferente":
            stats["campos_diferentes"] += 1

    # Comparar métricas
    delta_quality = v5_data["quality_score"] - v4_data["quality_score"]
    delta_confidence = v5_data["confidence_score"] - v4_data["confidence_score"]

    return {
        "id_oferta": id_oferta,
        "comparaciones": comparaciones,
        "stats": stats,
        "metricas": {
            "v4_quality": v4_data["quality_score"],
            "v5_quality": v5_data["quality_score"],
            "delta_quality": delta_quality,
            "v4_confidence": v4_data["confidence_score"],
            "v5_confidence": v5_data["confidence_score"],
            "delta_confidence": delta_confidence,
            "v4_time_ms": v4_data["processing_time_ms"],
            "v5_time_ms": v5_data["processing_time_ms"]
        }
    }


def generar_reporte_completo(conn, limit: int = None):
    """
    Genera reporte A/B completo entre v4.0 y v5.0

    Args:
        conn: Conexión a DB
        limit: Limitar ofertas a analizar (None = todas)
    """
    print("=" * 80)
    print("COMPARACIÓN A/B: NLP v4.0 vs v5.0")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Obtener ofertas con ambas versiones
    print("[1/4] Buscando ofertas con v4.0 Y v5.0...")
    ofertas_ids = obtener_ofertas_con_ambas_versiones(conn, limit=limit)

    if not ofertas_ids:
        print("[!] No hay ofertas con ambas versiones para comparar")
        return

    print(f"      Total ofertas a comparar: {len(ofertas_ids):,}")
    print()

    # Analizar cada oferta
    print("[2/4] Analizando extracciones...")
    analisis = []

    for i, id_oferta in enumerate(ofertas_ids, 1):
        v4_data = obtener_extraccion(conn, id_oferta, "v4.0.0")
        v5_data = obtener_extraccion(conn, id_oferta, "5.0.0")

        if not v4_data or not v5_data:
            continue

        analisis_oferta = analizar_comparacion(id_oferta, v4_data, v5_data)
        analisis.append(analisis_oferta)

        if i % 10 == 0:
            print(f"      Analizadas: {i}/{len(ofertas_ids)}")

    print(f"      [OK] {len(analisis):,} ofertas analizadas")
    print()

    # Agregar estadísticas globales
    print("[3/4] Calculando estadísticas globales...")

    total_campos_iguales = sum(a["stats"]["campos_iguales"] for a in analisis)
    total_mejoras_v5 = sum(a["stats"]["campos_mejora_v5"] for a in analisis)
    total_regresiones_v5 = sum(a["stats"]["campos_regresion_v5"] for a in analisis)
    total_diferentes = sum(a["stats"]["campos_diferentes"] for a in analisis)

    avg_delta_quality = sum(a["metricas"]["delta_quality"] for a in analisis) / len(analisis)
    avg_delta_confidence = sum(a["metricas"]["delta_confidence"] for a in analisis) / len(analisis)

    ofertas_mejoraron = sum(1 for a in analisis if a["metricas"]["delta_quality"] > 0)
    ofertas_empeoraron = sum(1 for a in analisis if a["metricas"]["delta_quality"] < 0)
    ofertas_igual = sum(1 for a in analisis if a["metricas"]["delta_quality"] == 0)

    # Tiempo promedio
    v4_times = [a["metricas"]["v4_time_ms"] for a in analisis if a["metricas"]["v4_time_ms"]]
    v5_times = [a["metricas"]["v5_time_ms"] for a in analisis if a["metricas"]["v5_time_ms"]]

    avg_v4_time = sum(v4_times) / len(v4_times) if v4_times else 0
    avg_v5_time = sum(v5_times) / len(v5_times) if v5_times else 0

    print()
    print("=" * 80)
    print("RESULTADOS DE LA COMPARACIÓN A/B")
    print("=" * 80)

    print(f"\n[RESUMEN GENERAL]")
    print(f"   Ofertas comparadas:        {len(analisis):,}")
    print()

    print(f"[CAMBIOS EN QUALITY SCORE]:")
    print(f"   Mejoraron con v5.0:        {ofertas_mejoraron:,} ({ofertas_mejoraron/len(analisis)*100:.1f}%)")
    print(f"   Empeoraron con v5.0:       {ofertas_empeoraron:,} ({ofertas_empeoraron/len(analisis)*100:.1f}%)")
    print(f"   Sin cambios:               {ofertas_igual:,} ({ofertas_igual/len(analisis)*100:.1f}%)")
    print(f"   Delta promedio:            {avg_delta_quality:+.2f} campos")
    print()

    print(f"[CAMBIOS POR CAMPO]:")
    total_campos = len(analisis) * 18  # 18 campos comparados
    print(f"   Campos sin cambios:        {total_campos_iguales:,} ({total_campos_iguales/total_campos*100:.1f}%)")
    print(f"   Campos mejorados (v5):     {total_mejoras_v5:,} ({total_mejoras_v5/total_campos*100:.1f}%)")
    print(f"   Campos perdidos (v5):      {total_regresiones_v5:,} ({total_regresiones_v5/total_campos*100:.1f}%)")
    print(f"   Campos con valores distintos: {total_diferentes:,} ({total_diferentes/total_campos*100:.1f}%)")
    print()

    print(f"[PERFORMANCE]:")
    print(f"   Tiempo promedio v4.0:      {avg_v4_time:,.0f}ms")
    print(f"   Tiempo promedio v5.0:      {avg_v5_time:,.0f}ms")
    if avg_v4_time > 0:
        print(f"   Delta tiempo:              {avg_v5_time - avg_v4_time:+,.0f}ms ({(avg_v5_time/avg_v4_time-1)*100:+.1f}%)")
    else:
        print(f"   Delta tiempo:              +{avg_v5_time:,.0f}ms (v4.0 sin datos de tiempo)")
    print()

    print(f"[CONFIDENCE SCORE]:")
    print(f"   Delta promedio:            {avg_delta_confidence:+.3f}")
    print()

    # Detalles de campos mejorados
    print("[4/4] Analizando campos más mejorados...")
    campos_mejoras = defaultdict(int)
    campos_perdidas = defaultdict(int)

    for a in analisis:
        for campo, comp in a["comparaciones"].items():
            if comp["status"] == "mejora_v5":
                campos_mejoras[campo] += 1
            elif comp["status"] == "regresion_v5":
                campos_perdidas[campo] += 1

    print()
    print("[TOP 10 CAMPOS MAS MEJORADOS CON v5.0]:")
    for campo, count in sorted(campos_mejoras.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / len(analisis) * 100
        print(f"   {campo:30} {count:4} ofertas ({pct:5.1f}%)")

    if campos_perdidas:
        print()
        print("[!] CAMPOS CON REGRESIONES EN v5.0:")
        for campo, count in sorted(campos_perdidas.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(analisis) * 100
            print(f"   {campo:30} {count:4} ofertas ({pct:5.1f}%)")

    print()
    print("=" * 80)

    # Decisión
    if ofertas_mejoraron > ofertas_empeoraron * 2 and total_mejoras_v5 > total_regresiones_v5:
        print("[OK] RECOMENDACION: Activar v5.0 en produccion")
        print("   v5.0 muestra mejoras significativas en quality y nuevos campos extraídos")
    elif ofertas_mejoraron > ofertas_empeoraron:
        print("[!] RECOMENDACION: Activar v5.0 con monitoreo")
        print("   v5.0 muestra mejoras, pero revisar campos con regresiones")
    else:
        print("[X] RECOMENDACION: NO activar v5.0 todavia")
        print("   v5.0 necesita ajustes antes de activación en producción")

    print("=" * 80)
    print()


def main():
    try:
        conn = conectar_db()
        print("[OK] Conectado a base de datos\n")

        # Generar reporte completo (primeras 100 ofertas para empezar)
        generar_reporte_completo(conn, limit=None)

        conn.close()

        print("\n[OK] Comparación completada exitosamente")
        print("\nPróximos pasos:")
        print("  1. Revisar métricas de mejora y regresiones")
        print("  2. Si OK, ejecutar rollout gradual (FASE 6)")
        print("  3. Monitorear quality_score en producción")

    except Exception as e:
        print(f"\n[ERROR] Error durante comparación: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
