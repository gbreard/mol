#!/usr/bin/env python3
"""
Test de extracción de skills con diccionario (skills_database.json)
===================================================================

Verifica que ahora se extraen skills técnicas usando el diccionario.
Caso crítico: ID 1117982053 (Angular Senior, 12 tecnologías esperadas)
"""

import sys
import sqlite3
from pathlib import Path

# Agregar paths al sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "02.5_nlp_extraction" / "scripts" / "patterns"))
sys.path.insert(0, str(project_root / "database"))

from regex_patterns_v4 import extract_all


def get_oferta_from_db(oferta_id: int) -> dict:
    """Obtiene una oferta de la BD"""
    db_path = project_root / "database" / "bumeran_scraping.db"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_oferta as id, titulo, empresa, descripcion
        FROM ofertas
        WHERE id_oferta = ?
    """, (oferta_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def test_skills_extraction(oferta_id: int = 1117982053):
    """Test principal de extracción de skills"""

    print("=" * 70)
    print("TEST: Extracción de Skills con Diccionario (skills_database.json)")
    print("=" * 70)

    # Obtener oferta
    oferta = get_oferta_from_db(oferta_id)

    if not oferta:
        print(f"ERROR: No se encontró oferta con ID {oferta_id}")
        return False

    print(f"\n[OFERTA] ID: {oferta['id']}")
    print(f"[TITULO] {oferta['titulo']}")
    print(f"[EMPRESA] {oferta['empresa']}")
    print(f"[DESCRIPCION] {oferta['descripcion'][:200]}...")

    # Extraer con regex v4 (ahora incluye skills)
    print("\n" + "-" * 70)
    print("EXTRACCIÓN con extract_all() (regex_patterns_v4)")
    print("-" * 70)

    resultado = extract_all(
        texto=oferta['descripcion'] or "",
        titulo=oferta['titulo'] or "",
        empresa=oferta['empresa'] or ""
    )

    # Mostrar skills extraídas
    skills_tecnicas = resultado.get("skills_tecnicas_regex", [])
    soft_skills = resultado.get("soft_skills_regex", [])

    print(f"\n[SKILLS TÉCNICAS] ({len(skills_tecnicas)} encontradas):")
    for skill in skills_tecnicas:
        print(f"  - {skill}")

    print(f"\n[SOFT SKILLS] ({len(soft_skills)} encontradas):")
    for skill in soft_skills:
        print(f"  - {skill}")

    # Verificar tecnologías esperadas para ID 1117982053 (Angular Senior)
    tecnologias_esperadas = [
        "angular", "typescript", "javascript", "html", "css",
        "git", "rest", "agile", "scrum"
    ]

    print("\n" + "-" * 70)
    print("VERIFICACIÓN de tecnologías esperadas")
    print("-" * 70)

    skills_lower = [s.lower() for s in skills_tecnicas]
    encontradas = []
    faltantes = []

    for tech in tecnologias_esperadas:
        if any(tech in s for s in skills_lower):
            encontradas.append(tech)
            print(f"  [OK] {tech}")
        else:
            faltantes.append(tech)
            print(f"  [FALTA] {tech}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Skills técnicas extraídas: {len(skills_tecnicas)}")
    print(f"Soft skills extraídas: {len(soft_skills)}")
    print(f"Tecnologías esperadas encontradas: {len(encontradas)}/{len(tecnologias_esperadas)}")

    if faltantes:
        print(f"Faltantes: {', '.join(faltantes)}")

    # Resultado
    success = len(skills_tecnicas) >= 3
    print(f"\n{'>>> TEST PASADO <<<' if success else '>>> TEST FALLIDO <<<'}")

    return success


def test_multiple_ofertas():
    """Test con múltiples ofertas de diferentes sectores"""

    print("\n" + "=" * 70)
    print("TEST: Múltiples ofertas")
    print("=" * 70)

    # IDs de prueba (si existen)
    test_ids = [
        1117982053,  # Angular Senior (IT)
        1117984105,  # Gerente Ventas (Comercial)
        1118027243,  # (otro caso)
    ]

    db_path = project_root / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener algunas ofertas
    cursor.execute("""
        SELECT id_oferta as id, titulo, descripcion
        FROM ofertas
        WHERE id_oferta IN (?, ?, ?)
        OR titulo LIKE '%python%'
        OR titulo LIKE '%react%'
        OR titulo LIKE '%desarrollador%'
        LIMIT 5
    """, tuple(test_ids))

    ofertas = cursor.fetchall()
    conn.close()

    total_skills = 0

    for oferta in ofertas:
        resultado = extract_all(
            texto=oferta['descripcion'] or "",
            titulo=oferta['titulo'] or ""
        )

        skills = resultado.get("skills_tecnicas_regex", [])
        total_skills += len(skills)

        print(f"\n[{oferta['id']}] {oferta['titulo'][:50]}")
        print(f"  Skills: {len(skills)} -> {skills[:5]}{'...' if len(skills) > 5 else ''}")

    print(f"\n[TOTAL] {total_skills} skills extraídas de {len(ofertas)} ofertas")


if __name__ == "__main__":
    # Test principal
    test_skills_extraction()

    # Test múltiple
    test_multiple_ofertas()
