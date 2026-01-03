#!/usr/bin/env python3
"""
Test de carga de diccionarios consolidados
==========================================

Verifica que skills_database.json v2.0 y oficios_arg.json cargan correctamente.
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "02.5_nlp_extraction" / "scripts" / "patterns"))

from regex_patterns_v4 import extract_all


def test_carga_diccionarios():
    """Test principal de carga"""

    print("=" * 60)
    print("TEST: Carga de Diccionarios Consolidados")
    print("=" * 60)

    # Texto de prueba con skills de todas las nuevas categorias
    texto_test = """
    Buscamos desarrollador con experiencia en Mercado Libre y Rappi.
    Conocimientos de Python, React, Docker y AWS.
    Manejo de facturacion electronica, AFIP y liquidacion de sueldos.
    Experiencia en picking y WMS para logistica.
    Barista con conocimientos de mise en place.
    Se requiere electricista con carnet de autoelevador.
    Trabajo en equipo y comunicacion efectiva.
    """

    resultado = extract_all(texto_test, "Desarrollador Full Stack")

    skills_tecnicas = resultado.get("skills_tecnicas_regex", [])
    soft_skills = resultado.get("soft_skills_regex", [])

    print(f"\n[SKILLS TECNICAS] ({len(skills_tecnicas)} encontradas):")
    for s in skills_tecnicas:
        print(f"  - {s}")

    print(f"\n[SOFT SKILLS] ({len(soft_skills)} encontradas):")
    for s in soft_skills:
        print(f"  - {s}")

    # Verificar que se detectan las nuevas categorias
    print("\n" + "-" * 60)
    print("VERIFICACION por categoria:")
    print("-" * 60)

    skills_lower = [s.lower() for s in skills_tecnicas]

    categorias_esperadas = {
        "plataformas_latam": ["mercado libre", "rappi"],
        "skills_logistica": ["picking", "wms"],
        "skills_contables": ["afip", "liquidacion de sueldos", "facturacion electronica"],
        "skills_gastronomia": ["barista", "mise en place"],
        "oficios": ["electricista"],
        "certificaciones_arg": ["carnet de autoelevador", "autoelevador"],
    }

    resultados = {}
    for categoria, esperados in categorias_esperadas.items():
        encontrados = [e for e in esperados if any(e in s for s in skills_lower)]
        resultados[categoria] = len(encontrados) > 0
        status = "[OK]" if resultados[categoria] else "[FALTA]"
        print(f"  {status} {categoria}: {encontrados if encontrados else 'ninguno'}")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Skills tecnicas extraidas: {len(skills_tecnicas)}")
    print(f"Soft skills extraidas: {len(soft_skills)}")
    print(f"Categorias detectadas: {sum(resultados.values())}/{len(resultados)}")

    success = len(skills_tecnicas) >= 5 and sum(resultados.values()) >= 4
    print(f"\n{'>>> TEST PASADO <<<' if success else '>>> TEST FALLIDO <<<'}")

    return success


if __name__ == "__main__":
    test_carga_diccionarios()
