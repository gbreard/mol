# -*- coding: utf-8 -*-
"""
analizar_errores_gold_set.py - Análisis detallado de los 10 errores
====================================================================

Analiza paso a paso por qué fallan los 10 casos de error del Gold Set 49.
Muestra: skills extraídas, candidatos, resultado vs esperado, diagnóstico.

Uso:
    python analizar_errores_gold_set.py
    python analizar_errores_gold_set.py --verbose
    python analizar_errores_gold_set.py --id 1118026729   # Solo un caso
"""

import sys
import io
import json
import sqlite3
import argparse
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))

from skills_implicit_extractor import SkillsImplicitExtractor
from match_by_skills import SkillsBasedMatcher
from match_ofertas_v3 import MatcherV3


def cargar_errores_gold_set():
    """Carga solo los casos con esco_ok=false del Gold Set."""
    gold_path = BASE_DIR / "database" / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    errores = [caso for caso in gold_set if not caso.get('esco_ok', True)]
    return errores


def cargar_datos_oferta(id_oferta: str, conn):
    """Carga datos NLP de una oferta."""
    cur = conn.execute('''
        SELECT n.*, o.titulo as titulo_original, o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        return dict(row)
    return None


def analizar_caso(caso: dict, conn, extractor, skills_matcher, matcher_v3, verbose: bool = False):
    """Analiza un caso de error en detalle."""
    id_oferta = str(caso['id_oferta'])
    isco_esperado = caso.get('isco_esperado', '?')
    esco_esperado = caso.get('esco_esperado', '?')
    tipo_error = caso.get('tipo_error', 'desconocido')
    comentario = caso.get('comentario', '')

    print("\n" + "=" * 80)
    print(f"ERROR: ID {id_oferta}")
    print("=" * 80)

    # Cargar datos
    datos = cargar_datos_oferta(id_oferta, conn)
    if not datos:
        print(f"  [ERROR] No se encontró en BD")
        return None

    titulo = datos.get('titulo_limpio') or ''
    tareas = datos.get('tareas_explicitas') or ''
    area = datos.get('area_funcional') or ''
    seniority = datos.get('nivel_seniority') or ''

    print(f"\n  TÍTULO: {titulo}")
    print(f"  ÁREA: {area}")
    print(f"  SENIORITY: {seniority}")
    print(f"  TIPO ERROR: {tipo_error}")

    if verbose and tareas:
        print(f"\n  TAREAS: {tareas[:200]}...")

    # PASO 1: Skills extraídas
    print(f"\n  {'─' * 70}")
    print("  PASO 1: SKILLS EXTRAÍDAS")
    print(f"  {'─' * 70}")

    skills = extractor.extract_skills(titulo_limpio=titulo, tareas_explicitas=tareas)

    if skills:
        print(f"  Total: {len(skills)} skills")
        for i, s in enumerate(skills[:8]):
            skill_name = s.get('skill_esco', s.get('skill_label', '?'))
            score = s.get('score', 0)
            origen = s.get('origen', '?')
            print(f"    {i+1}. {skill_name} (score={score:.2f}, origen={origen})")
    else:
        print("  ⚠ NO SE EXTRAJERON SKILLS")

    # PASO 2: Candidatos por skills
    print(f"\n  {'─' * 70}")
    print("  PASO 2: CANDIDATOS POR SKILLS")
    print(f"  {'─' * 70}")

    if skills:
        candidatos_skills = skills_matcher.match(skills, top_n=5)
        if candidatos_skills:
            for i, c in enumerate(candidatos_skills[:5]):
                isco = c.get('isco_code', '?')
                label = c.get('esco_label', '?')
                score = c.get('score', 0)
                matched = c.get('skills_matched', [])
                match_mark = "✓" if isco == isco_esperado else ""
                print(f"    {i+1}. ISCO {isco}: {label[:40]} (score={score:.2f}) {match_mark}")
                if verbose and matched:
                    print(f"       Skills matcheadas: {', '.join(matched[:3])}")
        else:
            print("  ⚠ NO HAY CANDIDATOS POR SKILLS")
    else:
        print("  (sin skills para buscar)")

    # PASO 3: Resultado final del matcher v3
    print(f"\n  {'─' * 70}")
    print("  PASO 3: RESULTADO MATCHER V3")
    print(f"  {'─' * 70}")

    oferta = {
        'titulo_limpio': titulo,
        'tareas_explicitas': tareas,
        'area_funcional': area,
        'nivel_seniority': seniority
    }

    result = matcher_v3.match(oferta)

    print(f"  RESULTADO:  ISCO {result.isco_code}: {result.esco_label}")
    print(f"  ESPERADO:   ISCO {isco_esperado}: {esco_esperado}")
    print(f"  MÉTODO:     {result.metodo}")
    print(f"  SCORE:      {result.score:.3f}")

    if result.isco_code == isco_esperado:
        print(f"  ESTADO:     ✓ CORRECTO (ya no es error)")
    else:
        print(f"  ESTADO:     ✗ SIGUE FALLANDO")

    # Alternativas
    if result.alternativas:
        print(f"\n  Alternativas:")
        for i, alt in enumerate(result.alternativas[:3]):
            isco = alt.get('isco_code', '?')
            label = alt.get('esco_label', '?')
            score = alt.get('score', 0)
            match_mark = "← CORRECTO" if isco == isco_esperado else ""
            print(f"    {i+1}. ISCO {isco}: {label[:40]} (score={score:.3f}) {match_mark}")

    # DIAGNÓSTICO
    print(f"\n  {'─' * 70}")
    print("  DIAGNÓSTICO")
    print(f"  {'─' * 70}")
    print(f"  Comentario Gold Set: {comentario[:100]}...")

    # Analizar por qué falló
    diagnostico = []

    # ¿El ISCO correcto está en las alternativas?
    iscos_alternativas = [alt.get('isco_code') for alt in result.alternativas]
    if isco_esperado in iscos_alternativas:
        pos = iscos_alternativas.index(isco_esperado) + 2  # +2 porque alternativas empieza en 2
        diagnostico.append(f"→ ISCO correcto está en posición {pos} (falta priorizar)")

    # ¿Se extrajeron skills relevantes?
    if not skills:
        diagnostico.append("→ NO se extrajeron skills (revisar extractor)")
    elif len(skills) < 3:
        diagnostico.append(f"→ Pocas skills ({len(skills)}) - puede faltar contexto")

    # ¿El área funcional ayudaría?
    if not area:
        diagnostico.append("→ Sin área funcional (podría ayudar a filtrar)")

    # ¿Es problema de nivel jerárquico?
    if tipo_error == 'nivel_jerarquico':
        diagnostico.append("→ Problema de nivel jerárquico - considerar regla de negocio")

    # ¿Es problema de sector?
    if tipo_error == 'sector_ignorado':
        diagnostico.append("→ Sector ignorado - agregar regla de negocio por sector")

    # ¿Es homonimia?
    if tipo_error == 'homonimia':
        diagnostico.append("→ Término polisémico - necesita desambiguación por contexto")

    if not diagnostico:
        diagnostico.append("→ Revisar manualmente candidatos y scores")

    for d in diagnostico:
        print(f"  {d}")

    return {
        'id_oferta': id_oferta,
        'titulo': titulo,
        'isco_resultado': result.isco_code,
        'isco_esperado': isco_esperado,
        'skills_count': len(skills),
        'es_correcto': result.isco_code == isco_esperado,
        'diagnostico': diagnostico
    }


def main():
    parser = argparse.ArgumentParser(description='Analizar errores del Gold Set')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo detallado')
    parser.add_argument('--id', type=str, default=None, help='Analizar solo un ID específico')
    args = parser.parse_args()

    print("=" * 80)
    print("ANÁLISIS DE ERRORES - GOLD SET 49")
    print("=" * 80)

    # Cargar errores
    errores = cargar_errores_gold_set()
    print(f"\nTotal errores en Gold Set: {len(errores)}")

    if args.id:
        errores = [e for e in errores if str(e['id_oferta']) == args.id]
        if not errores:
            print(f"ID {args.id} no encontrado en errores")
            return

    # Conectar BD
    db_path = BASE_DIR / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Inicializar componentes
    print("\nCargando componentes...")
    extractor = SkillsImplicitExtractor(verbose=False)
    skills_matcher = SkillsBasedMatcher(db_conn=conn, verbose=False)
    matcher_v3 = MatcherV3(db_conn=conn, verbose=False)
    print("  [OK] Componentes cargados")

    # Analizar cada error
    resultados = []
    for caso in errores:
        resultado = analizar_caso(
            caso, conn, extractor, skills_matcher, matcher_v3,
            verbose=args.verbose
        )
        if resultado:
            resultados.append(resultado)

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)

    corregidos = sum(1 for r in resultados if r['es_correcto'])
    siguen_mal = len(resultados) - corregidos

    print(f"\nTotal errores analizados: {len(resultados)}")
    print(f"  Ya corregidos (sin cambios): {corregidos}")
    print(f"  Siguen fallando: {siguen_mal}")

    if siguen_mal > 0:
        print(f"\nCasos que siguen fallando:")
        for r in resultados:
            if not r['es_correcto']:
                print(f"  - {r['id_oferta']}: {r['titulo'][:40]}...")
                print(f"    Resultado: ISCO {r['isco_resultado']} | Esperado: ISCO {r['isco_esperado']}")

    # Cerrar
    matcher_v3.close()
    conn.close()


if __name__ == "__main__":
    main()
