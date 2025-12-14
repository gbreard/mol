# -*- coding: utf-8 -*-
"""
Unificar Gold Sets: Matching + NLP
==================================

Usa los mismos 49 casos del Gold Set Matching para crear
el Gold Set NLP con campos v5.
"""

import sqlite3
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
MATCHING_GOLD_SET = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
NLP_GOLD_SET_OUTPUT = PROJECT_ROOT / "tests" / "nlp" / "gold_set.json"


def load_matching_gold_set():
    """Carga el gold set de matching y extrae IDs."""
    with open(MATCHING_GOLD_SET, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def get_nlp_data_for_ids(conn, ids):
    """Obtiene datos NLP para los IDs especificados."""
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(ids))
    query = f"""
        SELECT
            n.id_oferta,
            o.titulo,
            n.area_funcional,
            n.nivel_seniority,
            n.tiene_gente_cargo,
            n.tareas_explicitas,
            n.sector_empresa,
            n.tipo_oferta,
            n.licencia_conducir,
            n.tipo_licencia,
            n.es_tercerizado,
            n.skills_tecnicas_list,
            n.soft_skills_list,
            n.requisitos_excluyentes_list,
            n.beneficios_list
        FROM ofertas_nlp n
        JOIN ofertas o ON CAST(n.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE n.id_oferta IN ({placeholders})
    """

    cursor.execute(query, ids)
    rows = cursor.fetchall()

    results = {}
    for row in rows:
        id_oferta = str(row[0])

        # Parse JSON fields
        skills_tecnicas = []
        soft_skills = []
        tareas = []

        try:
            if row[11]:
                skills_tecnicas = json.loads(row[11]) if isinstance(row[11], str) else []
        except:
            pass

        try:
            if row[12]:
                soft_skills = json.loads(row[12]) if isinstance(row[12], str) else []
        except:
            pass

        try:
            if row[5]:
                tareas = json.loads(row[5]) if isinstance(row[5], str) else []
        except:
            pass

        results[id_oferta] = {
            "titulo": row[1],
            "area_funcional": row[2],
            "nivel_seniority": row[3],
            "tiene_gente_cargo": bool(row[4]) if row[4] is not None else None,
            "tareas_list": tareas[:5] if tareas else None,
            "sector_empresa": row[6],
            "tipo_oferta": row[7],
            "licencia_conducir": bool(row[8]) if row[8] is not None else None,
            "es_tercerizado": bool(row[10]) if row[10] is not None else None,
            "skills_tecnicas_sample": skills_tecnicas[:5] if skills_tecnicas else [],
            "soft_skills_sample": soft_skills[:3] if soft_skills else []
        }

    return results


def generate_unified_gold_set(matching_data, nlp_data):
    """Genera gold set NLP unificado."""
    gold_set = []

    for case in matching_data:
        id_oferta = str(case['id_oferta'])
        nlp = nlp_data.get(id_oferta, {})

        entry = {
            "id_oferta": id_oferta,
            "titulo": nlp.get("titulo", "N/A"),
            "esco_ok": case.get("esco_ok", True),
            "matching_comentario": case.get("comentario", ""),
            "expected": {
                "area_funcional": nlp.get("area_funcional"),
                "nivel_seniority": nlp.get("nivel_seniority"),
                "tiene_gente_cargo": nlp.get("tiene_gente_cargo"),
                "tareas_list": nlp.get("tareas_list"),
                "sector_empresa": nlp.get("sector_empresa"),
                "tipo_oferta": nlp.get("tipo_oferta"),
                "licencia_conducir": nlp.get("licencia_conducir"),
                "es_tercerizado": nlp.get("es_tercerizado"),
                "skills_tecnicas_sample": nlp.get("skills_tecnicas_sample", []),
                "soft_skills_sample": nlp.get("soft_skills_sample", [])
            }
        }
        gold_set.append(entry)

    return gold_set


def print_coverage_report(gold_set):
    """Imprime reporte de cobertura."""
    total = len(gold_set)

    campos_v5 = ["area_funcional", "nivel_seniority", "tiene_gente_cargo",
                 "sector_empresa", "tipo_oferta", "licencia_conducir", "es_tercerizado"]

    print("\n## COBERTURA DE CAMPOS NLP Schema v5")
    print("-" * 60)

    for campo in campos_v5:
        con_valor = sum(1 for g in gold_set if g["expected"].get(campo) is not None)

        # Ejemplos
        ejemplos = []
        for g in gold_set:
            val = g["expected"].get(campo)
            if val is not None and str(val) not in [str(e) for e in ejemplos]:
                ejemplos.append(val)
            if len(ejemplos) >= 3:
                break

        ejemplos_str = ", ".join([str(e)[:15] for e in ejemplos])
        status = "OK" if con_valor > 0 else "PENDIENTE"
        print(f"  {campo:25} | {con_valor:>2}/{total} | [{status}] {ejemplos_str}")

    # Skills (legacy)
    print("\n## CAMPOS LEGACY (siempre disponibles)")
    print("-" * 60)

    skills_count = sum(1 for g in gold_set if g["expected"].get("skills_tecnicas_sample"))
    soft_count = sum(1 for g in gold_set if g["expected"].get("soft_skills_sample"))

    print(f"  skills_tecnicas_sample    | {skills_count:>2}/{total}")
    print(f"  soft_skills_sample        | {soft_count:>2}/{total}")


def print_examples(gold_set, n=5):
    """Imprime ejemplos."""
    print(f"\n## {n} EJEMPLOS DE EXTRACCION")
    print("-" * 80)

    for i, g in enumerate(gold_set[:n]):
        print(f"\n[{i+1}] ID: {g['id_oferta']}")
        print(f"    Título: {g['titulo'][:50]}...")
        exp = g['expected']
        if exp.get('area_funcional'):
            print(f"    area_funcional: {exp['area_funcional']}")
        if exp.get('nivel_seniority'):
            print(f"    nivel_seniority: {exp['nivel_seniority']}")
        if exp.get('tipo_oferta'):
            print(f"    tipo_oferta: {exp['tipo_oferta']}")
        if exp.get('tiene_gente_cargo') is not None:
            print(f"    tiene_gente_cargo: {exp['tiene_gente_cargo']}")
        if exp.get('skills_tecnicas_sample'):
            print(f"    skills_tecnicas: {exp['skills_tecnicas_sample'][:3]}")


def main():
    print("=" * 70)
    print("UNIFICACION DE GOLD SETS: MATCHING + NLP")
    print("=" * 70)

    # 1. Cargar gold set matching
    print("\n[1] Cargando Gold Set Matching...")
    matching_data = load_matching_gold_set()
    ids = [str(case['id_oferta']) for case in matching_data]
    print(f"    {len(ids)} casos encontrados")

    # Mostrar IDs
    print(f"\n## IDs del Gold Set ({len(ids)} total):")
    print(" ".join(ids))

    # 2. Obtener datos NLP
    print("\n[2] Obteniendo datos NLP de BD...")
    conn = sqlite3.connect(DB_PATH)
    nlp_data = get_nlp_data_for_ids(conn, ids)
    conn.close()
    print(f"    {len(nlp_data)} ofertas con datos NLP")

    # 3. Generar gold set unificado
    print("\n[3] Generando Gold Set NLP unificado...")
    gold_set = generate_unified_gold_set(matching_data, nlp_data)

    # 4. Guardar
    with open(NLP_GOLD_SET_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(gold_set, f, indent=2, ensure_ascii=False)
    print(f"    Guardado en: {NLP_GOLD_SET_OUTPUT}")

    # 5. Reporte
    print_coverage_report(gold_set)
    print_examples(gold_set)

    print("\n" + "=" * 70)
    print(f"RESULTADO: {len(gold_set)} casos en Gold Set NLP unificado")
    print("=" * 70)

    return gold_set


if __name__ == "__main__":
    main()
