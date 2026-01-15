# -*- coding: utf-8 -*-
"""
04_combinar_scores.py - PASO 4: Combinar Scores y Aplicar Reglas
=================================================================

Combina los resultados de skills (60%) y semántico (40%), aplica reglas
de negocio, y genera el resultado final de matching.

Input:
  - JSON del paso 2 (02_match_skills_*.json)
  - JSON del paso 3 (03_match_semantico_*.json)

Output: JSON con resultado final de matching para cada oferta.

Uso:
    python 04_combinar_scores.py --skills <paso2.json> --semantico <paso3.json>
    python 04_combinar_scores.py --skills ... --semantico ... --alpha 0.7   # 70% skills
    python 04_combinar_scores.py --skills ... --semantico ... --verbose
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Agregar database/ al path
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))


def cargar_json(path: str) -> list:
    """Carga un JSON."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_reglas_negocio() -> dict:
    """Carga reglas de negocio desde config."""
    config_path = BASE_DIR / "config" / "matching_rules_business.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def combinar_candidatos(skills_candidatos: list, semantico_candidatos: list,
                        alpha: float = 0.6) -> list:
    """
    Combina candidatos de skills y semántico.

    Args:
        skills_candidatos: Lista de candidatos por skills
        semantico_candidatos: Lista de candidatos por semántico
        alpha: Peso para skills (default 0.6 = 60%)

    Returns:
        Lista combinada ordenada por score combinado
    """
    beta = 1 - alpha  # Peso semántico

    # Indexar por URI
    scores_por_uri = defaultdict(lambda: {'skills': 0, 'semantico': 0, 'metadata': {}})

    for c in skills_candidatos:
        uri = c.get('occupation_uri', '')
        if uri:
            scores_por_uri[uri]['skills'] = c.get('score', 0)
            scores_por_uri[uri]['metadata'] = {
                'esco_label': c.get('esco_label', ''),
                'isco_code': c.get('isco_code', ''),
                'skills_matched': c.get('skills_matched', [])
            }

    for c in semantico_candidatos:
        uri = c.get('occupation_uri', '')
        if uri:
            scores_por_uri[uri]['semantico'] = c.get('score', 0)
            if not scores_por_uri[uri]['metadata']:
                scores_por_uri[uri]['metadata'] = {
                    'esco_label': c.get('esco_label', ''),
                    'isco_code': c.get('isco_code', '')
                }

    # Calcular score combinado
    combinados = []
    for uri, data in scores_por_uri.items():
        score_skills = data['skills']
        score_semantico = data['semantico']

        # Score combinado
        if score_skills > 0 and score_semantico > 0:
            combined = alpha * score_skills + beta * score_semantico
            metodo = 'combined'
        elif score_skills > 0:
            combined = score_skills * alpha  # Penalizar si no hay semántico
            metodo = 'skills_only'
        else:
            combined = score_semantico * beta  # Penalizar si no hay skills
            metodo = 'semantico_only'

        combinados.append({
            'occupation_uri': uri,
            'esco_label': data['metadata'].get('esco_label', ''),
            'isco_code': data['metadata'].get('isco_code', ''),
            'combined_score': combined,
            'score_skills': score_skills,
            'score_semantico': score_semantico,
            'metodo': metodo,
            'skills_matched': data['metadata'].get('skills_matched', [])
        })

    # Ordenar por score combinado
    combinados.sort(key=lambda x: x['combined_score'], reverse=True)

    return combinados


def aplicar_reglas_negocio(oferta: dict, candidatos: list, reglas: dict) -> tuple:
    """
    Aplica reglas de negocio (bypass, priorización, penalización).

    Returns:
        (candidatos_modificados, regla_aplicada o None)
    """
    if not reglas:
        return candidatos, None

    titulo = (oferta.get('titulo_limpio') or '').lower()
    area = oferta.get('area_funcional', '')
    seniority = oferta.get('nivel_seniority', '')

    # Reglas de forzar ISCO (bypass)
    reglas_forzar = reglas.get('reglas_forzar_isco', {})
    for rule_id, rule in reglas_forzar.items():
        if not isinstance(rule, dict) or not rule.get('activa', False):
            continue

        condicion = rule.get('condicion', {})
        accion = rule.get('accion', {})

        # Verificar condición
        terminos = condicion.get('titulo_contiene_alguno', [])
        if terminos and any(t.lower() in titulo for t in terminos):
            isco_forzado = accion.get('forzar_isco')
            if isco_forzado:
                # Buscar candidato con ese ISCO o priorizar
                for c in candidatos:
                    if c.get('isco_code', '').startswith(isco_forzado):
                        c['combined_score'] *= 1.5  # Boost
                        c['regla_aplicada'] = rule_id
                candidatos.sort(key=lambda x: x['combined_score'], reverse=True)
                return candidatos, rule_id

    return candidatos, None


def combinar_resultados(skills_data: list, semantico_data: list,
                        alpha: float = 0.6, verbose: bool = False) -> list:
    """Combina resultados de ambos pasos para cada oferta."""
    reglas = cargar_reglas_negocio()

    # Indexar por id_oferta
    skills_por_id = {r['id_oferta']: r for r in skills_data}
    semantico_por_id = {r['id_oferta']: r for r in semantico_data}

    # Combinar
    all_ids = set(skills_por_id.keys()) | set(semantico_por_id.keys())
    resultados = []
    total = len(all_ids)

    for i, id_oferta in enumerate(sorted(all_ids)):
        skills_oferta = skills_por_id.get(id_oferta, {})
        semantico_oferta = semantico_por_id.get(id_oferta, {})

        titulo = skills_oferta.get('titulo_limpio') or semantico_oferta.get('titulo_limpio', '')

        if verbose:
            print(f"\n[{i+1}/{total}] {id_oferta}: {titulo[:50]}...")

        try:
            # Obtener candidatos de cada método
            skills_cands = skills_oferta.get('candidatos', [])
            semantico_cands = semantico_oferta.get('candidatos', [])

            # Combinar
            candidatos = combinar_candidatos(skills_cands, semantico_cands, alpha)

            # Aplicar reglas de negocio
            oferta_info = {
                'titulo_limpio': titulo,
                'area_funcional': skills_oferta.get('area_funcional'),
                'nivel_seniority': skills_oferta.get('nivel_seniority')
            }
            candidatos, regla = aplicar_reglas_negocio(oferta_info, candidatos, reglas)

            mejor = candidatos[0] if candidatos else None

            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'area_funcional': oferta_info['area_funcional'],
                'nivel_seniority': oferta_info['nivel_seniority'],
                'candidatos_skills': len(skills_cands),
                'candidatos_semantico': len(semantico_cands),
                'candidatos_combinados': len(candidatos),
                'resultado_final': mejor,
                'alternativas': candidatos[1:4] if len(candidatos) > 1 else [],
                'regla_aplicada': regla
            }

            if verbose and mejor:
                print(f"   -> {mejor.get('esco_label', '?')} (ISCO {mejor.get('isco_code', '?')})")
                print(f"      Score: {mejor.get('combined_score', 0):.3f} (skills={mejor.get('score_skills', 0):.2f}, sem={mejor.get('score_semantico', 0):.3f})")
                if regla:
                    print(f"      Regla aplicada: {regla}")

        except Exception as e:
            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'error': str(e),
                'resultado_final': None
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


def imprimir_resumen(resultados: list, alpha: float):
    """Imprime resumen del matching combinado."""
    total = len(resultados)
    con_resultado = sum(1 for r in resultados if r.get('resultado_final'))
    errores = sum(1 for r in resultados if 'error' in r)

    print("\n" + "=" * 60)
    print(f"RESUMEN MATCHING COMBINADO (alpha={alpha})")
    print("=" * 60)
    print(f"Total ofertas: {total}")
    print(f"Con resultado: {con_resultado} ({100*con_resultado/total:.1f}%)")
    print(f"Sin resultado: {total - con_resultado - errores}")
    print(f"Errores: {errores}")

    # Por método
    metodo_dist = defaultdict(int)
    for r in resultados:
        rf = r.get('resultado_final')
        if rf:
            metodo_dist[rf.get('metodo', 'unknown')] += 1

    print("\nDistribución por método:")
    for metodo, count in sorted(metodo_dist.items(), key=lambda x: -x[1]):
        print(f"  {metodo}: {count} ({100*count/con_resultado:.1f}%)")

    # Reglas aplicadas
    con_regla = [r for r in resultados if r.get('regla_aplicada')]
    if con_regla:
        print(f"\nOfertas con regla de negocio: {len(con_regla)}")

    # Distribución ISCO
    print("\nDistribución por ISCO:")
    isco_dist = defaultdict(int)
    for r in resultados:
        rf = r.get('resultado_final')
        if rf:
            isco = rf.get('isco_code', '?')
            if isco and len(isco) >= 1:
                isco_dist[isco[0]] += 1

    for grupo in sorted(isco_dist.keys()):
        count = isco_dist[grupo]
        print(f"  ISCO {grupo}xxx: {count}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Combinar scores de matching')
    parser.add_argument('--skills', '-s', type=str, required=True, help='JSON del paso 2')
    parser.add_argument('--semantico', '-m', type=str, required=True, help='JSON del paso 3')
    parser.add_argument('--alpha', type=float, default=0.6, help='Peso skills (default: 0.6)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo debug')
    parser.add_argument('--output', '-o', type=str, default=None, help='Archivo de salida')
    args = parser.parse_args()

    print("=" * 60)
    print("PASO 4: COMBINAR SCORES (Gold Set 100)")
    print("=" * 60)
    print(f"Input skills: {args.skills}")
    print(f"Input semántico: {args.semantico}")
    print(f"Alpha (peso skills): {args.alpha}")
    print(f"Beta (peso semántico): {1 - args.alpha}")

    # Cargar datos
    print("\nCargando datos...")
    skills_data = cargar_json(args.skills)
    semantico_data = cargar_json(args.semantico)
    print(f"Ofertas skills: {len(skills_data)}")
    print(f"Ofertas semántico: {len(semantico_data)}")

    # Combinar
    print("\nCombinando scores...")
    resultados = combinar_resultados(
        skills_data,
        semantico_data,
        alpha=args.alpha,
        verbose=args.verbose
    )

    # Guardar
    output_dir = BASE_DIR / "exports" / "matching_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"04_resultado_final_{timestamp}.json"

    guardar_resultados(resultados, output_path)

    # Resumen
    imprimir_resumen(resultados, args.alpha)

    print(f"\n[OK] Siguiente paso: python export_matching_excel.py --input {output_path}")


if __name__ == "__main__":
    main()
