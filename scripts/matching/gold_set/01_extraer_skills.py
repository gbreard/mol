# -*- coding: utf-8 -*-
"""
01_extraer_skills.py - PASO 1: Extracción de Skills
====================================================

Extrae skills ESCO implícitas desde título + tareas para el Gold Set 100.
Usa skills_implicit_extractor.py (v2.0) con embeddings BGE-M3.

Output: JSON con skills extraídas por oferta para revisar y optimizar.

Uso:
    python 01_extraer_skills.py                    # Procesa Gold Set 100
    python 01_extraer_skills.py --limit 10         # Solo 10 ofertas
    python 01_extraer_skills.py --verbose          # Modo debug
    python 01_extraer_skills.py --threshold 0.5    # Cambiar umbral
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

from skills_implicit_extractor import SkillsImplicitExtractor


def cargar_gold_set_ids() -> list:
    """Carga IDs del Gold Set NLP 100."""
    gold_set_path = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
    with open(gold_set_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_datos_nlp(ids: list) -> list:
    """Carga datos NLP de las ofertas del Gold Set."""
    db_path = BASE_DIR / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Buscar también IDs derivados (multi-perfil)
    all_ids = list(ids)
    cursor = conn.cursor()
    for id_base in ids:
        cursor.execute(
            "SELECT id_oferta FROM ofertas_nlp WHERE id_oferta LIKE ? AND id_oferta != ?",
            (f"{id_base}_%", id_base)
        )
        derivados = [row[0] for row in cursor.fetchall()]
        all_ids.extend(derivados)

    placeholders = ','.join(['?' for _ in all_ids])
    query = f"""
        SELECT
            n.id_oferta,
            n.titulo_limpio,
            n.tareas_explicitas,
            n.area_funcional,
            n.nivel_seniority,
            o.titulo as titulo_original
        FROM ofertas_nlp n
        LEFT JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
        ORDER BY n.id_oferta
    """

    cursor.execute(query, all_ids)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def extraer_skills(ofertas: list, threshold: float = 0.55, top_k: int = 5, verbose: bool = False) -> list:
    """Extrae skills para cada oferta usando SkillsImplicitExtractor."""
    extractor = SkillsImplicitExtractor(
        threshold=threshold,
        top_k=top_k,
        verbose=verbose
    )

    resultados = []
    total = len(ofertas)

    for i, oferta in enumerate(ofertas):
        id_oferta = oferta['id_oferta']
        titulo = oferta.get('titulo_limpio') or ''
        tareas = oferta.get('tareas_explicitas') or ''

        if verbose:
            print(f"\n[{i+1}/{total}] {id_oferta}: {titulo[:50]}...")

        try:
            skills = extractor.extract_skills(
                titulo_limpio=titulo,
                tareas_explicitas=tareas
            )

            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'tareas_explicitas': tareas[:200] + '...' if len(tareas) > 200 else tareas,
                'area_funcional': oferta.get('area_funcional'),
                'nivel_seniority': oferta.get('nivel_seniority'),
                'skills_count': len(skills),
                'skills': skills
            }

            if verbose:
                print(f"   -> {len(skills)} skills extraídas")
                for s in skills[:3]:
                    print(f"      - {s.get('skill_esco', s.get('skill_label', '?'))} ({s.get('score', 0):.2f})")

        except Exception as e:
            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'error': str(e),
                'skills_count': 0,
                'skills': []
            }
            if verbose:
                print(f"   -> ERROR: {e}")

        resultados.append(resultado)

        # Progreso cada 10
        if not verbose and (i + 1) % 10 == 0:
            print(f"Procesadas {i+1}/{total} ofertas...")

    return resultados


def guardar_resultados(resultados: list, output_path: Path):
    """Guarda resultados en JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en: {output_path}")


def imprimir_resumen(resultados: list):
    """Imprime resumen de la extracción."""
    total = len(resultados)
    con_skills = sum(1 for r in resultados if r.get('skills_count', 0) > 0)
    errores = sum(1 for r in resultados if 'error' in r)
    total_skills = sum(r.get('skills_count', 0) for r in resultados)

    print("\n" + "=" * 60)
    print("RESUMEN EXTRACCIÓN DE SKILLS")
    print("=" * 60)
    print(f"Total ofertas procesadas: {total}")
    print(f"Ofertas con skills: {con_skills} ({100*con_skills/total:.1f}%)")
    print(f"Ofertas sin skills: {total - con_skills - errores}")
    print(f"Errores: {errores}")
    print(f"Total skills extraídas: {total_skills}")
    print(f"Promedio skills/oferta: {total_skills/total:.1f}")
    print("=" * 60)

    # Top ofertas con más skills
    print("\nTop 5 ofertas con más skills:")
    top = sorted(resultados, key=lambda x: x.get('skills_count', 0), reverse=True)[:5]
    for r in top:
        print(f"  {r['id_oferta']}: {r.get('skills_count', 0)} skills - {r.get('titulo_limpio', '')[:40]}...")

    # Ofertas sin skills (para investigar)
    sin_skills = [r for r in resultados if r.get('skills_count', 0) == 0 and 'error' not in r]
    if sin_skills:
        print(f"\nOfertas sin skills ({len(sin_skills)}):")
        for r in sin_skills[:5]:
            print(f"  {r['id_oferta']}: {r.get('titulo_limpio', '')[:50]}...")


def main():
    parser = argparse.ArgumentParser(description='Extraer skills del Gold Set 100')
    parser.add_argument('--limit', type=int, default=None, help='Limitar a N ofertas')
    parser.add_argument('--threshold', type=float, default=0.55, help='Umbral de similitud (default: 0.55)')
    parser.add_argument('--top_k', type=int, default=5, help='Top K skills por texto (default: 5)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo debug')
    parser.add_argument('--output', type=str, default=None, help='Archivo de salida')
    args = parser.parse_args()

    print("=" * 60)
    print("PASO 1: EXTRACCIÓN DE SKILLS (Gold Set 100)")
    print("=" * 60)
    print(f"Umbral similitud: {args.threshold}")
    print(f"Top K: {args.top_k}")

    # Cargar datos
    print("\nCargando Gold Set...")
    ids = cargar_gold_set_ids()
    print(f"IDs en Gold Set: {len(ids)}")

    if args.limit:
        ids = ids[:args.limit]
        print(f"Limitado a: {len(ids)} ofertas")

    print("\nCargando datos NLP de BD...")
    ofertas = cargar_datos_nlp(ids)
    print(f"Ofertas cargadas: {len(ofertas)} (incluye derivados multi-perfil)")

    # Extraer skills
    print("\nExtrayendo skills...")
    resultados = extraer_skills(
        ofertas,
        threshold=args.threshold,
        top_k=args.top_k,
        verbose=args.verbose
    )

    # Guardar
    output_dir = BASE_DIR / "exports" / "matching_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"01_skills_extraidas_{timestamp}.json"

    guardar_resultados(resultados, output_path)

    # Resumen
    imprimir_resumen(resultados)

    print(f"\n[OK] Siguiente paso: python 02_match_por_skills.py --input {output_path}")


if __name__ == "__main__":
    main()
