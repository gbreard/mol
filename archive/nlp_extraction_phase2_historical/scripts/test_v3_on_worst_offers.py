#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test v3 Patterns on Worst Performing Offers
============================================

Tests the ultra-aggressive v3 patterns on the 10 worst-performing offers
to validate improvements before full re-processing.
"""

import sys
from pathlib import Path
import sqlite3

# Add path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from extractors.bumeran_extractor import BumeranExtractor


def get_worst_offers(db_path: str, limit: int = 10):
    """
    Get worst-performing offers from database

    Args:
        db_path: Path to SQLite database
        limit: Number of worst offers to retrieve

    Returns:
        List of tuples (id, titulo, descripcion, nlp_confidence_score)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            n.nlp_confidence_score
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE o.descripcion IS NOT NULL
          AND o.descripcion != ''
        ORDER BY COALESCE(n.nlp_confidence_score, 0) ASC
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    conn.close()

    return results


def calculate_score_breakdown(result: dict) -> dict:
    """
    Calculate detailed score breakdown

    Args:
        result: Extraction result dictionary

    Returns:
        Dictionary with field scores
    """
    scores = {}

    # Experiencia
    if result.get('experiencia_min_anios') is not None:
        scores['experiencia'] = 1
    else:
        scores['experiencia'] = 0

    # Educacion
    if result.get('nivel_educativo') is not None:
        scores['educacion'] = 1
    else:
        scores['educacion'] = 0

    # Idiomas
    if result.get('idioma_principal') is not None:
        scores['idiomas'] = 1
    else:
        scores['idiomas'] = 0

    # Jornada
    if result.get('jornada_laboral') is not None:
        scores['jornada'] = 1
    else:
        scores['jornada'] = 0

    # Skills técnicas
    skills_tec = result.get('skills_tecnicas_list')
    if skills_tec:
        if isinstance(skills_tec, str):
            try:
                skills_tec_list = eval(skills_tec) if skills_tec != '[]' else []
            except:
                skills_tec_list = []
        elif isinstance(skills_tec, list):
            skills_tec_list = skills_tec
        else:
            skills_tec_list = []

        if len(skills_tec_list) > 0:
            scores['skills_tecnicas'] = 1
        else:
            scores['skills_tecnicas'] = 0
    else:
        scores['skills_tecnicas'] = 0

    # Soft skills
    soft_skills = result.get('soft_skills_list')
    if soft_skills:
        if isinstance(soft_skills, str):
            try:
                soft_skills_list = eval(soft_skills) if soft_skills != '[]' else []
            except:
                soft_skills_list = []
        elif isinstance(soft_skills, list):
            soft_skills_list = soft_skills
        else:
            soft_skills_list = []

        if len(soft_skills_list) > 0:
            scores['soft_skills'] = 1
        else:
            scores['soft_skills'] = 0
    else:
        scores['soft_skills'] = 0

    # Salario (siempre 0 para Bumeran)
    scores['salario'] = 0

    # Total
    scores['total'] = sum(scores.values())
    scores['score'] = scores['total'] / 7.0

    return scores


def test_v3_patterns(db_path: str, num_offers: int = 10):
    """
    Test v3 patterns on worst-performing offers

    Args:
        db_path: Path to SQLite database
        num_offers: Number of offers to test
    """
    print("=" * 80)
    print("TEST DE PATRONES V3 EN OFERTAS MAL PARSEADAS")
    print("=" * 80)
    print()

    # Get worst offers
    print(f"Obteniendo las {num_offers} ofertas peor parseadas...")
    offers = get_worst_offers(db_path, num_offers)
    print(f"Ofertas obtenidas: {len(offers)}")
    print()

    # Initialize extractor
    extractor = BumeranExtractor(version="3.0.0")

    # Test each offer
    improvements = []

    for i, (offer_id, titulo, descripcion, old_score) in enumerate(offers, 1):
        print("-" * 80)
        print(f"OFERTA {i}/{len(offers)} - ID: {offer_id}")
        print("-" * 80)
        print(f"Titulo: {titulo[:80]}...")
        print(f"Score Anterior (v2): {old_score if old_score else 0.0:.2f}")
        print()

        # Extract with v3
        result = extractor.extract_all(descripcion, titulo)
        scores = calculate_score_breakdown(result)
        new_score = result.get('nlp_confidence_score', 0.0)

        print(f"Score Nuevo (v3): {new_score:.2f}")
        print()

        # Show field breakdown
        print("Desglose por campo:")
        print(f"  Experiencia:      {scores['experiencia']}/1  ", end="")
        if scores['experiencia']:
            print(f"[{result.get('experiencia_min_anios')} años]")
        else:
            print("[NO DETECTADO]")

        print(f"  Educacion:        {scores['educacion']}/1  ", end="")
        if scores['educacion']:
            print(f"[{result.get('nivel_educativo')}]")
        else:
            print("[NO DETECTADO]")

        print(f"  Idiomas:          {scores['idiomas']}/1  ", end="")
        if scores['idiomas']:
            print(f"[{result.get('idioma_principal')}]")
        else:
            print("[NO DETECTADO]")

        print(f"  Jornada:          {scores['jornada']}/1  ", end="")
        if scores['jornada']:
            print(f"[{result.get('jornada_laboral')}]")
        else:
            print("[NO DETECTADO]")

        print(f"  Skills Tecnicas:  {scores['skills_tecnicas']}/1  ", end="")
        if scores['skills_tecnicas']:
            skills_raw = result.get('skills_tecnicas_list', '[]')
            if isinstance(skills_raw, str):
                try:
                    skills = eval(skills_raw) if skills_raw != '[]' else []
                except:
                    skills = []
            elif isinstance(skills_raw, list):
                skills = skills_raw
            else:
                skills = []
            print(f"[{len(skills)} skills]")
        else:
            print("[NO DETECTADO]")

        print(f"  Soft Skills:      {scores['soft_skills']}/1  ", end="")
        if scores['soft_skills']:
            skills_raw = result.get('soft_skills_list', '[]')
            if isinstance(skills_raw, str):
                try:
                    skills = eval(skills_raw) if skills_raw != '[]' else []
                except:
                    skills = []
            elif isinstance(skills_raw, list):
                skills = skills_raw
            else:
                skills = []
            print(f"[{len(skills)} skills]")
        else:
            print("[NO DETECTADO]")

        print(f"  Salario:          {scores['salario']}/1  [N/A para Bumeran]")

        print()
        print(f"Total: {scores['total']}/7 ({scores['score']:.1%})")

        # Calculate improvement
        old = old_score if old_score else 0.0
        improvement = new_score - old
        print(f"Mejora: {improvement:+.2f} ({improvement/7*100:+.1f}%)")

        improvements.append(improvement)
        print()

    # Summary
    print("=" * 80)
    print("RESUMEN DE MEJORAS")
    print("=" * 80)
    print()

    avg_improvement = sum(improvements) / len(improvements) if improvements else 0
    print(f"Mejora promedio: {avg_improvement:+.2f} puntos ({avg_improvement/7*100:+.1f}%)")
    print(f"Mejor mejora: {max(improvements):+.2f} puntos")
    print(f"Peor mejora: {min(improvements):+.2f} puntos")
    print()

    # Count by improvement level
    zero_improvement = sum(1 for imp in improvements if imp == 0)
    small_improvement = sum(1 for imp in improvements if 0 < imp < 1)
    medium_improvement = sum(1 for imp in improvements if 1 <= imp < 3)
    large_improvement = sum(1 for imp in improvements if imp >= 3)

    print("Distribucion de mejoras:")
    print(f"  Sin mejora (0):        {zero_improvement}/{len(improvements)}")
    print(f"  Mejora pequeña (<1):   {small_improvement}/{len(improvements)}")
    print(f"  Mejora media (1-3):    {medium_improvement}/{len(improvements)}")
    print(f"  Mejora grande (>=3):   {large_improvement}/{len(improvements)}")
    print()

    # Success rate
    success_rate = (len(improvements) - zero_improvement) / len(improvements) * 100
    print(f"Tasa de exito: {success_rate:.1f}% ({len(improvements) - zero_improvement}/{len(improvements)} ofertas mejoradas)")
    print()

    # Recommendation
    if avg_improvement >= 1.5:
        print("RECOMENDACION: Excelentes resultados. Proceder con re-procesamiento completo.")
    elif avg_improvement >= 0.5:
        print("RECOMENDACION: Resultados positivos. Considerar re-procesamiento.")
    else:
        print("RECOMENDACION: Mejoras limitadas. Revisar patrones antes de re-procesamiento.")

    print()
    print("=" * 80)


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    test_v3_patterns(str(db_path), num_offers=10)
