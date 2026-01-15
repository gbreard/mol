# -*- coding: utf-8 -*-
"""
02_match_por_skills.py - PASO 2: Match de Ocupaciones por Skills
=================================================================

Busca ocupaciones ESCO que coinciden con las skills extraídas.
Usa match_by_skills.py (v1.0) y la tabla esco_associations.

Input: JSON del paso 1 (01_skills_extraidas_*.json)
Output: JSON con ocupaciones candidatas por skills para cada oferta.

Uso:
    python 02_match_por_skills.py --input exports/matching_optimization/01_skills_extraidas_*.json
    python 02_match_por_skills.py --input ... --top_n 5     # Top 5 candidatos
    python 02_match_por_skills.py --input ... --verbose     # Modo debug
"""

import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

# Agregar database/ al path para importar componentes
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))

from match_by_skills import SkillsBasedMatcher


def cargar_skills_extraidas(input_path: str) -> list:
    """Carga resultados del paso 1."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_por_skills(datos: list, top_n: int = 10, verbose: bool = False) -> list:
    """Busca ocupaciones candidatas para cada oferta según sus skills."""
    db_path = BASE_DIR / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    matcher = SkillsBasedMatcher(
        db_conn=conn,
        top_n=top_n,
        verbose=verbose
    )

    resultados = []
    total = len(datos)

    for i, oferta in enumerate(datos):
        id_oferta = oferta['id_oferta']
        skills = oferta.get('skills', [])
        titulo = oferta.get('titulo_limpio', '')

        if verbose:
            print(f"\n[{i+1}/{total}] {id_oferta}: {titulo[:50]}...")
            print(f"   Skills input: {len(skills)}")

        try:
            if skills:
                candidatos = matcher.match(skills, top_n=top_n)
            else:
                candidatos = []

            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'area_funcional': oferta.get('area_funcional'),
                'nivel_seniority': oferta.get('nivel_seniority'),
                'skills_input_count': len(skills),
                'skills_input': [s.get('skill_esco', s.get('skill_label', '?')) for s in skills[:5]],
                'candidatos_count': len(candidatos),
                'candidatos': candidatos,
                'mejor_candidato': candidatos[0] if candidatos else None
            }

            if verbose and candidatos:
                print(f"   -> {len(candidatos)} ocupaciones candidatas")
                for c in candidatos[:3]:
                    print(f"      - {c.get('esco_label', '?')} (ISCO {c.get('isco_code', '?')}) score={c.get('score', 0):.2f}")

        except Exception as e:
            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'error': str(e),
                'candidatos_count': 0,
                'candidatos': []
            }
            if verbose:
                print(f"   -> ERROR: {e}")

        resultados.append(resultado)

        # Progreso cada 10
        if not verbose and (i + 1) % 10 == 0:
            print(f"Procesadas {i+1}/{total} ofertas...")

    conn.close()
    return resultados


def guardar_resultados(resultados: list, output_path: Path):
    """Guarda resultados en JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en: {output_path}")


def imprimir_resumen(resultados: list):
    """Imprime resumen del matching por skills."""
    total = len(resultados)
    con_candidatos = sum(1 for r in resultados if r.get('candidatos_count', 0) > 0)
    errores = sum(1 for r in resultados if 'error' in r)
    total_candidatos = sum(r.get('candidatos_count', 0) for r in resultados)

    print("\n" + "=" * 60)
    print("RESUMEN MATCH POR SKILLS")
    print("=" * 60)
    print(f"Total ofertas procesadas: {total}")
    print(f"Ofertas con candidatos: {con_candidatos} ({100*con_candidatos/total:.1f}%)")
    print(f"Ofertas sin candidatos: {total - con_candidatos - errores}")
    print(f"Errores: {errores}")
    print(f"Total candidatos generados: {total_candidatos}")
    print(f"Promedio candidatos/oferta: {total_candidatos/total:.1f}")
    print("=" * 60)

    # Distribución de códigos ISCO
    print("\nDistribución por código ISCO (primer dígito):")
    isco_dist = {}
    for r in resultados:
        mejor = r.get('mejor_candidato')
        if mejor:
            isco = mejor.get('isco_code', '?')
            if isco and len(isco) >= 1:
                grupo = isco[0]
                isco_dist[grupo] = isco_dist.get(grupo, 0) + 1

    for grupo in sorted(isco_dist.keys()):
        count = isco_dist[grupo]
        print(f"  ISCO {grupo}xxx: {count} ofertas")

    # Ofertas sin candidatos
    sin_candidatos = [r for r in resultados if r.get('candidatos_count', 0) == 0 and 'error' not in r]
    if sin_candidatos:
        print(f"\nOfertas sin candidatos por skills ({len(sin_candidatos)}):")
        for r in sin_candidatos[:5]:
            print(f"  {r['id_oferta']}: {r.get('titulo_limpio', '')[:50]}...")
            print(f"     Skills input: {r.get('skills_input_count', 0)}")


def main():
    parser = argparse.ArgumentParser(description='Match ocupaciones por skills')
    parser.add_argument('--input', '-i', type=str, required=True, help='JSON del paso 1')
    parser.add_argument('--top_n', type=int, default=10, help='Top N candidatos (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo debug')
    parser.add_argument('--output', '-o', type=str, default=None, help='Archivo de salida')
    args = parser.parse_args()

    print("=" * 60)
    print("PASO 2: MATCH POR SKILLS (Gold Set 100)")
    print("=" * 60)
    print(f"Input: {args.input}")
    print(f"Top N candidatos: {args.top_n}")

    # Cargar datos del paso 1
    print("\nCargando skills extraídas...")
    datos = cargar_skills_extraidas(args.input)
    print(f"Ofertas cargadas: {len(datos)}")

    # Match por skills
    print("\nBuscando ocupaciones por skills...")
    resultados = match_por_skills(
        datos,
        top_n=args.top_n,
        verbose=args.verbose
    )

    # Guardar
    output_dir = BASE_DIR / "exports" / "matching_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"02_match_skills_{timestamp}.json"

    guardar_resultados(resultados, output_path)

    # Resumen
    imprimir_resumen(resultados)

    print(f"\n[OK] Siguiente paso: python 03_match_semantico.py --input {args.input}")


if __name__ == "__main__":
    main()
