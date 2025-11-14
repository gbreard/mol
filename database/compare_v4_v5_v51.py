#!/usr/bin/env python3
"""
Comparación A/B: v4.0 vs v5.0 vs v5.1
======================================

Compara las 3 versiones de NLP en las ofertas del A/B test.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any

def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    return sqlite3.connect(db_path)

def cargar_ids_ab_test():
    """Carga los IDs del archivo de A/B test"""
    ids_file = Path(__file__).parent / "ids_for_ab_test.txt"
    with open(ids_file, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]

def obtener_extraccion(conn, id_oferta: int, version: str) -> Dict[str, Any]:
    """Obtiene extracción de una oferta en una versión específica"""
    cursor = conn.cursor()

    # Buscar en todas las versiones, incluyendo inactivas para v5.1
    cursor.execute("""
        SELECT
            extracted_data,
            quality_score,
            confidence_score,
            processing_time_ms
        FROM ofertas_nlp_history
        WHERE id_oferta = ? AND nlp_version = ?
        ORDER BY processed_at DESC
        LIMIT 1
    """, (id_oferta, version))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        "extracted_data": json.loads(row[0]) if row[0] else {},
        "quality_score": row[1],
        "confidence_score": row[2],
        "processing_time_ms": row[3]
    }

def calcular_campos_llenos(data: Dict[str, Any]) -> int:
    """Cuenta campos con valor (no null)"""
    campos = [
        "experiencia_min_anios", "experiencia_max_anios",
        "nivel_educativo", "estado_educativo", "carrera_especifica",
        "idioma_principal", "nivel_idioma_principal",
        "skills_tecnicas_list", "soft_skills_list", "certificaciones_list",
        "salario_min", "salario_max", "moneda",
        "beneficios_list", "requisitos_excluyentes_list", "requisitos_deseables_list",
        "jornada_laboral", "horario_flexible"
    ]

    return sum(1 for campo in campos if data.get(campo) is not None)

def main():
    print("=" * 80)
    print("COMPARACIÓN A/B: v4.0 vs v5.0 vs v5.1")
    print("=" * 80)
    print()

    conn = conectar_db()
    ids_ab_test = cargar_ids_ab_test()

    print(f"Total ofertas en A/B test: {len(ids_ab_test)}")
    print()

    # Recopilar datos
    resultados = []

    for id_oferta in ids_ab_test:
        v4 = obtener_extraccion(conn, id_oferta, "v4.0.0")
        v5 = obtener_extraccion(conn, id_oferta, "5.0.0")
        v51 = obtener_extraccion(conn, id_oferta, "5.1.0")

        if v4 or v5 or v51:  # Al menos una versión existe
            resultados.append({
                "id_oferta": id_oferta,
                "v4": v4,
                "v5": v5,
                "v51": v51
            })

    # ESTADÍSTICAS DE COBERTURA
    print("=" * 80)
    print("COBERTURA POR VERSIÓN")
    print("=" * 80)

    ofertas_v4 = sum(1 for r in resultados if r["v4"])
    ofertas_v5 = sum(1 for r in resultados if r["v5"])
    ofertas_v51 = sum(1 for r in resultados if r["v51"])

    print(f"v4.0:  {ofertas_v4}/{len(ids_ab_test)} ofertas ({ofertas_v4/len(ids_ab_test)*100:.1f}%)")
    print(f"v5.0:  {ofertas_v5}/{len(ids_ab_test)} ofertas ({ofertas_v5/len(ids_ab_test)*100:.1f}%)")
    print(f"v5.1:  {ofertas_v51}/{len(ids_ab_test)} ofertas ({ofertas_v51/len(ids_ab_test)*100:.1f}%)")

    # COMPARACIÓN QUALITY SCORE
    print()
    print("=" * 80)
    print("QUALITY SCORE (Campos Completados)")
    print("=" * 80)

    # Filtrar solo ofertas con v5.1
    ofertas_con_v51 = [r for r in resultados if r["v51"]]

    if not ofertas_con_v51:
        print("[!] No hay ofertas con v5.1 para comparar")
        conn.close()
        return

    print(f"\nOfertas con v5.1: {len(ofertas_con_v51)}")
    print()

    # Calcular promedios
    avg_v4 = sum(r["v4"]["quality_score"] for r in ofertas_con_v51 if r["v4"]) / len([r for r in ofertas_con_v51 if r["v4"]])
    avg_v5 = sum(r["v5"]["quality_score"] for r in ofertas_con_v51 if r["v5"]) / len([r for r in ofertas_con_v51 if r["v5"]])
    avg_v51 = sum(r["v51"]["quality_score"] for r in ofertas_con_v51) / len(ofertas_con_v51)

    print(f"Quality Score Promedio:")
    print(f"  v4.0:  {avg_v4:.2f} campos")
    print(f"  v5.0:  {avg_v5:.2f} campos")
    print(f"  v5.1:  {avg_v51:.2f} campos")
    print()
    print(f"Deltas:")
    print(f"  v5.1 vs v4.0:  {avg_v51 - avg_v4:+.2f} campos ({(avg_v51/avg_v4-1)*100:+.1f}%)")
    print(f"  v5.1 vs v5.0:  {avg_v51 - avg_v5:+.2f} campos ({(avg_v51/avg_v5-1)*100:+.1f}%)")
    print(f"  v5.0 vs v4.0:  {avg_v5 - avg_v4:+.2f} campos ({(avg_v5/avg_v4-1)*100:+.1f}%)")

    # COMPARACIÓN CONFIDENCE SCORE
    print()
    print("=" * 80)
    print("CONFIDENCE SCORE")
    print("=" * 80)

    avg_conf_v4 = sum(r["v4"]["confidence_score"] for r in ofertas_con_v51 if r["v4"]) / len([r for r in ofertas_con_v51 if r["v4"]])
    avg_conf_v5 = sum(r["v5"]["confidence_score"] for r in ofertas_con_v51 if r["v5"]) / len([r for r in ofertas_con_v51 if r["v5"]])
    avg_conf_v51 = sum(r["v51"]["confidence_score"] for r in ofertas_con_v51) / len(ofertas_con_v51)

    print(f"\nConfidence Score Promedio:")
    print(f"  v4.0:  {avg_conf_v4:.3f}")
    print(f"  v5.0:  {avg_conf_v5:.3f}")
    print(f"  v5.1:  {avg_conf_v51:.3f}")
    print()
    print(f"Deltas:")
    print(f"  v5.1 vs v4.0:  {avg_conf_v51 - avg_conf_v4:+.3f}")
    print(f"  v5.1 vs v5.0:  {avg_conf_v51 - avg_conf_v5:+.3f}")

    # ANÁLISIS CAMPO POR CAMPO
    print()
    print("=" * 80)
    print("ANÁLISIS POR CAMPO (ofertas con v5.1)")
    print("=" * 80)

    campos = [
        "experiencia_min_anios", "experiencia_max_anios",
        "nivel_educativo", "estado_educativo", "carrera_especifica",
        "idioma_principal", "nivel_idioma_principal",
        "skills_tecnicas_list", "soft_skills_list", "certificaciones_list",
        "salario_min", "salario_max", "moneda",
        "beneficios_list", "requisitos_excluyentes_list", "requisitos_deseables_list",
        "jornada_laboral", "horario_flexible"
    ]

    print(f"\n{'Campo':<30} {'v4.0':>8} {'v5.0':>8} {'v5.1':>8} {'Delta v5.1-v4':>15}")
    print("-" * 80)

    for campo in campos:
        count_v4 = sum(1 for r in ofertas_con_v51 if r["v4"] and r["v4"]["extracted_data"].get(campo) is not None)
        count_v5 = sum(1 for r in ofertas_con_v51 if r["v5"] and r["v5"]["extracted_data"].get(campo) is not None)
        count_v51 = sum(1 for r in ofertas_con_v51 if r["v51"]["extracted_data"].get(campo) is not None)

        delta = count_v51 - count_v4

        print(f"{campo:<30} {count_v4:>8} {count_v5:>8} {count_v51:>8} {delta:>+12}")

    # DECISIÓN
    print()
    print("=" * 80)
    print("RECOMENDACIÓN")
    print("=" * 80)
    print()

    mejora_vs_v4 = avg_v51 > avg_v4
    mejora_vs_v5 = avg_v51 > avg_v5

    if mejora_vs_v4 and mejora_vs_v5:
        print("[OK] v5.1 SUPERA a v4.0 y v5.0")
        print(f"    - Quality Score: {avg_v51:.2f} (vs {avg_v4:.2f} en v4.0)")
        print(f"    - Mejora: {(avg_v51/avg_v4-1)*100:+.1f}%")
        print()
        print("DECISIÓN: Activar v5.1 en producción")
    elif mejora_vs_v5 and not mejora_vs_v4:
        print("[~] v5.1 SUPERA a v5.0 pero NO alcanza v4.0")
        print(f"    - Quality Score v5.1: {avg_v51:.2f}")
        print(f"    - Quality Score v4.0: {avg_v4:.2f}")
        print(f"    - Gap: {avg_v4 - avg_v51:.2f} campos")
        print()
        print("DECISIÓN: Analizar casos específicos antes de activar")
    else:
        print("[✗] v5.1 NO supera versiones anteriores")
        print()
        print("DECISIÓN: NO activar v5.1 - requiere más ajustes")

    print("=" * 80)

    conn.close()

if __name__ == '__main__':
    main()
