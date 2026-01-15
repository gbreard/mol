# -*- coding: utf-8 -*-
"""
Generar Gold Set NLP v2 - Desde ofertas CON datos NLP existentes
================================================================

Selecciona 20 ofertas que YA tienen datos NLP y genera el gold set.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
OUTPUT_PATH = Path(__file__).parent.parent / "tests" / "nlp" / "gold_set.json"

def get_offers_with_nlp_data(conn, limit=20):
    """Obtiene ofertas con datos NLP existentes, variando por área funcional."""
    cursor = conn.cursor()

    # Get offers with NLP data, diverse by area_funcional
    query = """
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
        WHERE n.skills_tecnicas_list IS NOT NULL
          AND LENGTH(n.skills_tecnicas_list) > 5
        ORDER BY RANDOM()
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    results = []
    for row in rows:
        # Parse JSON fields
        skills_tecnicas = []
        soft_skills = []
        requisitos = []
        beneficios = []
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
            if row[13]:
                requisitos = json.loads(row[13]) if isinstance(row[13], str) else []
        except:
            pass

        try:
            if row[14]:
                beneficios = json.loads(row[14]) if isinstance(row[14], str) else []
        except:
            pass

        try:
            if row[5]:
                tareas = json.loads(row[5]) if isinstance(row[5], str) else []
        except:
            pass

        # Determine category from titulo
        titulo_lower = row[1].lower() if row[1] else ""
        if any(kw in titulo_lower for kw in ["vendedor", "ventas", "comercial", "promotor"]):
            categoria = "ventas"
        elif any(kw in titulo_lower for kw in ["desarrollador", "programador", "sistemas", "it", "software", "devops"]):
            categoria = "it"
        elif any(kw in titulo_lower for kw in ["administrativo", "asistente", "rrhh", "contador", "contable", "recepcion"]):
            categoria = "admin"
        elif any(kw in titulo_lower for kw in ["operario", "produccion", "logistica", "deposito", "tecnico", "mantenimiento"]):
            categoria = "produccion"
        else:
            categoria = "otro"

        results.append({
            "id_oferta": str(row[0]),
            "titulo": row[1],
            "categoria": categoria,
            "expected": {
                "area_funcional": row[2],
                "nivel_seniority": row[3],
                "tiene_gente_cargo": bool(row[4]) if row[4] is not None else None,
                "tareas_list": tareas[:3] if tareas else None,
                "sector_empresa": row[6],
                "tipo_oferta": row[7],
                "licencia_conducir": bool(row[8]) if row[8] is not None else None,
                "es_tercerizado": bool(row[10]) if row[10] is not None else None,
                "skills_tecnicas_sample": skills_tecnicas[:5] if skills_tecnicas else [],
                "soft_skills_sample": soft_skills[:3] if soft_skills else [],
                "beneficios_sample": beneficios[:3] if beneficios else []
            }
        })

    return results


def main():
    conn = sqlite3.connect(DB_PATH)

    print("=" * 70)
    print("GENERANDO GOLD SET NLP v2 - Desde datos existentes")
    print("=" * 70)

    gold_set = get_offers_with_nlp_data(conn, limit=20)

    conn.close()

    # Save gold set
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(gold_set, f, indent=2, ensure_ascii=False)

    print(f"\nTotal ofertas: {len(gold_set)}")

    # Show by category
    by_cat = {}
    for g in gold_set:
        cat = g["categoria"]
        by_cat[cat] = by_cat.get(cat, 0) + 1

    print("\nPor categoria:")
    for cat, count in sorted(by_cat.items()):
        print(f"  {cat}: {count}")

    # Coverage report
    print("\n## COBERTURA POR CAMPO")
    print("-" * 60)

    campos_v5 = ["area_funcional", "nivel_seniority", "tiene_gente_cargo",
                 "sector_empresa", "tipo_oferta", "licencia_conducir", "es_tercerizado"]

    campos_legacy = ["skills_tecnicas_sample", "soft_skills_sample", "beneficios_sample"]

    print("\nCampos NLP Schema v5:")
    for campo in campos_v5:
        con_valor = sum(1 for g in gold_set if g["expected"].get(campo) is not None)

        # Get sample values
        ejemplos = []
        for g in gold_set:
            val = g["expected"].get(campo)
            if val is not None and str(val) not in [str(e) for e in ejemplos]:
                ejemplos.append(val)
            if len(ejemplos) >= 3:
                break

        ejemplos_str = ", ".join([str(e)[:15] for e in ejemplos])
        print(f"  {campo:25} | {con_valor:>2}/{len(gold_set)} | {ejemplos_str}")

    print("\nCampos Legacy (siempre disponibles):")
    for campo in campos_legacy:
        con_valor = sum(1 for g in gold_set if g["expected"].get(campo))
        print(f"  {campo:25} | {con_valor:>2}/{len(gold_set)}")

    print(f"\nGold set guardado en: {OUTPUT_PATH}")

    # Show sample entries
    print("\n## MUESTRA (primeras 3 ofertas)")
    print("-" * 60)
    for i, g in enumerate(gold_set[:3]):
        print(f"\n[{i+1}] {g['id_oferta']}: {g['titulo'][:50]}...")
        print(f"    Categoria: {g['categoria']}")
        exp = g['expected']
        if exp.get('area_funcional'):
            print(f"    area_funcional: {exp['area_funcional']}")
        if exp.get('nivel_seniority'):
            print(f"    nivel_seniority: {exp['nivel_seniority']}")
        if exp.get('skills_tecnicas_sample'):
            print(f"    skills_tecnicas: {exp['skills_tecnicas_sample'][:3]}")

    return gold_set


if __name__ == "__main__":
    main()
