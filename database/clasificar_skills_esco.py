#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
CLASIFICADOR DE SKILLS ESCO: Knowledge vs Competencies/Skills
================================================================================

Proyecto: MOL v2.0 - FASE 1 Tarea 2
Autor: Equipo OEDE + Claude Code
Fecha: 15/11/2025

Objetivo:
---------
Clasificar los 14,247 skills de ESCO en dos categorías:
- KNOWLEDGE: Conocimientos teóricos (anatomía, legislación, sistemas, etc.)
- COMPETENCY: Habilidades/capacidades prácticas (gestionar, operar, analizar, etc.)

Algoritmo de 3 niveles:
-----------------------
1. NIVEL 1 (RDF): Campos skillType y skillReusabilityLevel del RDF ESCO
2. NIVEL 2 (Linguístico): Análisis de estructura del preferred_label_es
   - COMPETENCY: Empieza con verbo infinitivo (gestionar, realizar, etc.)
   - KNOWLEDGE: Sustantivos o frases nominales (anatomía, sistema de, etc.)
3. NIVEL 3 (Keywords): Palabras clave específicas

Salida:
-------
- Agrega columna `skill_category` a tabla esco_skills
- Agrega columna `classification_confidence` (0-100)
- Agrega columna `classification_method` (rdf|linguistic|keyword)

================================================================================
"""

import sqlite3
import re
from pathlib import Path
from typing import Tuple, Optional

# ==============================================================================
# CONFIGURACION
# ==============================================================================

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"

# Verbos de acción típicos en competencies (infinitivo español)
VERBOS_COMPETENCY = [
    "gestionar", "realizar", "ejecutar", "llevar a cabo", "proporcionar",
    "facilitar", "ayudar", "supervisar", "coordinar", "dirigir", "planificar",
    "organizar", "controlar", "evaluar", "analizar", "diseñar", "desarrollar",
    "implementar", "mantener", "operar", "manejar", "utilizar", "aplicar",
    "crear", "construir", "elaborar", "producir", "fabricar", "reparar",
    "instalar", "montar", "ensamblar", "ajustar", "calibrar", "medir",
    "inspeccionar", "comprobar", "verificar", "probar", "examinar", "revisar",
    "asesorar", "guiar", "orientar", "capacitar", "formar", "enseñar",
    "comunicar", "informar", "presentar", "negociar", "vender", "comprar",
    "atender", "servir", "cuidar", "asistir", "apoyar", "colaborar",
    "investigar", "estudiar", "observar", "registrar", "documentar", "archivar",
    "preparar", "procesar", "tramitar", "administrar", "clasificar", "ordenar",
    "limpiar", "esterilizar", "desinfectar", "derribar", "tostar", "domar",
    "practicar", "impartir", "reducir", "ocuparse", "mantenerse al día",
]

# Palabras clave típicas en knowledge (sustantivos/conceptos)
KEYWORDS_KNOWLEDGE = [
    "anatomía", "fisiología", "biología", "química", "física", "matemáticas",
    "legislación", "normativa", "reglamento", "ley", "derecho", "código",
    "sistema de", "mecanismo de", "principios de", "teoría de", "conceptos de",
    "historia de", "geografía", "idioma", "lengua", "gramática", "sintaxis",
    "filosofía", "ética", "moral", "estética", "lógica", "metodología",
    "técnica de", "método de", "procedimiento de", "protocolo de",
    "arquitectura", "ingeniería", "medicina", "farmacología", "patología",
    "economía", "finanzas", "contabilidad", "auditoría", "fiscalidad",
    "sociología", "psicología", "antropología", "pedagogía", "didáctica",
    "informática", "programación", "algoritmos", "estructuras de datos",
    "tecnología", "electrónica", "mecánica", "hidráulica", "neumática",
    "geología", "meteorología", "astronomía", "ecología", "botánica", "zoología",
]

# ==============================================================================
# FUNCIONES DE CLASIFICACION
# ==============================================================================

def clasificar_por_estructura_linguistica(label: str) -> Tuple[Optional[str], int, str]:
    """
    Nivel 2: Analiza la estructura lingüística del label.

    Returns:
        (category, confidence, method)
        - category: 'knowledge' | 'competency' | None
        - confidence: 0-100
        - method: descripción del método usado
    """
    label_lower = label.lower().strip()

    # 1. Buscar verbos de acción al inicio (competency)
    for verbo in VERBOS_COMPETENCY:
        if label_lower.startswith(verbo):
            return ("competency", 90, f"linguistic_verb_{verbo}")

    # 2. Buscar keywords de knowledge
    for keyword in KEYWORDS_KNOWLEDGE:
        if keyword in label_lower:
            return ("knowledge", 85, f"linguistic_keyword_{keyword}")

    # 3. Heurística: Si empieza con sustantivo/artículo (knowledge)
    # Artículos y preposiciones comunes al inicio de knowledge
    if re.match(r'^(el |la |los |las |un |una |unos |unas |de |del )', label_lower):
        return ("knowledge", 70, "linguistic_article")

    # 4. Heurística: Si contiene "de" o "del" (suele ser knowledge)
    if " de " in label_lower or " del " in label_lower:
        # Pero no si empieza con verbo (gestión de...)
        if not any(label_lower.startswith(v) for v in VERBOS_COMPETENCY):
            return ("knowledge", 65, "linguistic_preposition")

    # 5. Si no hay indicadores claros, default a competency (mayoría son competencies)
    return ("competency", 50, "linguistic_default")


def clasificar_skill(skill_uri: str, label: str, skill_type_rdf: Optional[str],
                     reuse_level_rdf: Optional[str]) -> Tuple[str, int, str]:
    """
    Clasifica un skill usando algoritmo de 3 niveles.

    Args:
        skill_uri: URI del skill
        label: preferred_label_es
        skill_type_rdf: Valor de skill_type del RDF (si existe)
        reuse_level_rdf: Valor de skill_reusability_level del RDF (si existe)

    Returns:
        (category, confidence, method)
    """

    # NIVEL 1: Datos del RDF (no disponible en este dataset)
    if skill_type_rdf and skill_type_rdf != 'skill':
        # Si ESCO tiene 'knowledge' o 'attitude', usarlo
        if skill_type_rdf == 'knowledge':
            return ("knowledge", 95, "rdf_skill_type")
        elif skill_type_rdf == 'attitude':
            return ("competency", 95, "rdf_skill_type_attitude")

    # NIVEL 2: Análisis lingüístico
    category, confidence, method = clasificar_por_estructura_linguistica(label)

    return (category, confidence, method)


# ==============================================================================
# PROCESAMIENTO PRINCIPAL
# ==============================================================================

def main():
    """Ejecuta la clasificación de todos los skills."""

    print("=" * 80)
    print("CLASIFICADOR DE SKILLS ESCO - Knowledge vs Competencies")
    print("=" * 80)
    print(f"\nConectando a BD: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Verificar si ya existen las columnas
    cursor.execute("PRAGMA table_info(esco_skills)")
    columns = [col[1] for col in cursor.fetchall()]

    if "skill_category" not in columns:
        print("\n[1/4] Agregando columna 'skill_category'...")
        cursor.execute("""
            ALTER TABLE esco_skills
            ADD COLUMN skill_category TEXT
            CHECK (skill_category IN ('knowledge', 'competency'))
        """)
    else:
        print("\n[1/4] Columna 'skill_category' ya existe")

    if "classification_confidence" not in columns:
        print("[2/4] Agregando columna 'classification_confidence'...")
        cursor.execute("""
            ALTER TABLE esco_skills
            ADD COLUMN classification_confidence INTEGER
        """)
    else:
        print("[2/4] Columna 'classification_confidence' ya existe")

    if "classification_method" not in columns:
        print("[3/4] Agregando columna 'classification_method'...")
        cursor.execute("""
            ALTER TABLE esco_skills
            ADD COLUMN classification_method TEXT
        """)
    else:
        print("[3/4] Columna 'classification_method' ya existe")

    conn.commit()

    # 2. Obtener todos los skills
    print("\n[4/4] Clasificando skills...")
    cursor.execute("""
        SELECT skill_uri, preferred_label_es, skill_type, skill_reusability_level
        FROM esco_skills
    """)
    skills = cursor.fetchall()
    total = len(skills)
    print(f"  Total de skills a clasificar: {total:,}")

    # 3. Clasificar cada skill
    stats = {
        "knowledge": 0,
        "competency": 0,
        "confidence_high": 0,  # >= 85
        "confidence_medium": 0,  # 70-84
        "confidence_low": 0,  # < 70
        "methods": {}
    }

    for i, (uri, label, skill_type, reuse_level) in enumerate(skills, 1):
        category, confidence, method = clasificar_skill(uri, label, skill_type, reuse_level)

        # Actualizar BD
        cursor.execute("""
            UPDATE esco_skills
            SET skill_category = ?,
                classification_confidence = ?,
                classification_method = ?
            WHERE skill_uri = ?
        """, (category, confidence, method, uri))

        # Estadísticas
        stats[category] += 1
        if confidence >= 85:
            stats["confidence_high"] += 1
        elif confidence >= 70:
            stats["confidence_medium"] += 1
        else:
            stats["confidence_low"] += 1

        stats["methods"][method] = stats["methods"].get(method, 0) + 1

        # Progress bar
        if i % 1000 == 0 or i == total:
            pct = (i / total) * 100
            print(f"  Progreso: {i:,}/{total:,} ({pct:.1f}%)")

    conn.commit()

    # 4. Reporte final
    print("\n" + "=" * 80)
    print("REPORTE DE CLASIFICACIÓN")
    print("=" * 80)

    print(f"\n1. DISTRIBUCIÓN POR CATEGORÍA:")
    print(f"   - Knowledge:   {stats['knowledge']:,} ({stats['knowledge']/total*100:.1f}%)")
    print(f"   - Competency:  {stats['competency']:,} ({stats['competency']/total*100:.1f}%)")

    print(f"\n2. CONFIANZA DE CLASIFICACIÓN:")
    print(f"   - Alta (≥85%):     {stats['confidence_high']:,} ({stats['confidence_high']/total*100:.1f}%)")
    print(f"   - Media (70-84%):  {stats['confidence_medium']:,} ({stats['confidence_medium']/total*100:.1f}%)")
    print(f"   - Baja (<70%):     {stats['confidence_low']:,} ({stats['confidence_low']/total*100:.1f}%)")

    print(f"\n3. MÉTODOS UTILIZADOS (top 10):")
    sorted_methods = sorted(stats["methods"].items(), key=lambda x: x[1], reverse=True)
    for method, count in sorted_methods[:10]:
        print(f"   - {method:30} {count:,} ({count/total*100:.1f}%)")

    # 5. Validación: ¿Se cumple el objetivo de >90% con confianza >= 85%?
    high_conf_pct = (stats['confidence_high'] / total) * 100
    print(f"\n4. VALIDACIÓN:")
    print(f"   - Objetivo: >90% con confianza ≥85%")
    print(f"   - Resultado: {high_conf_pct:.1f}% con confianza ≥85%")
    if high_conf_pct >= 90:
        print("   ✓ OBJETIVO CUMPLIDO")
    else:
        print(f"   ✗ OBJETIVO NO CUMPLIDO (falta {90 - high_conf_pct:.1f}%)")

    # 6. Ejemplos de cada categoría
    print(f"\n5. EJEMPLOS DE CLASIFICACIÓN:")

    print("\n   KNOWLEDGE:")
    cursor.execute("""
        SELECT preferred_label_es, classification_confidence, classification_method
        FROM esco_skills
        WHERE skill_category = 'knowledge'
        ORDER BY classification_confidence DESC
        LIMIT 5
    """)
    for label, conf, method in cursor.fetchall():
        print(f"     - {label[:60]:60} (conf={conf}%, {method})")

    print("\n   COMPETENCY:")
    cursor.execute("""
        SELECT preferred_label_es, classification_confidence, classification_method
        FROM esco_skills
        WHERE skill_category = 'competency'
        ORDER BY classification_confidence DESC
        LIMIT 5
    """)
    for label, conf, method in cursor.fetchall():
        print(f"     - {label[:60]:60} (conf={conf}%, {method})")

    conn.close()

    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
