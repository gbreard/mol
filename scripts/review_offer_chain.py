"""
Revisar ofertas UNO POR UNO - Cadena completa del pipeline.

Este script presenta cada oferta con TODOS sus datos para que Claude
pueda revisar la cadena completa: Scraping → NLP → Skills → Matching

Uso:
    python scripts/review_offer_chain.py --id 1118027834
    python scripts/review_offer_chain.py --pendientes --limit 10
    python scripts/review_offer_chain.py --errores

Version: 1.0
Fecha: 2026-01-14
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Path setup
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "database"))

DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


def get_offer_full_chain(conn: sqlite3.Connection, id_oferta: str) -> Dict:
    """
    Obtiene TODOS los datos de una oferta para revision completa.

    Returns:
        Dict con: scraping, nlp, skills, matching
    """
    result = {
        "id_oferta": id_oferta,
        "scraping": None,
        "nlp": None,
        "skills": [],
        "matching": None
    }

    # 1. DATOS SCRAPING (input original)
    cursor = conn.execute("""
        SELECT
            id_oferta,
            titulo,
            empresa,
            localizacion,
            descripcion,
            fecha_publicacion_original,
            modalidad_trabajo,
            portal
        FROM ofertas
        WHERE id_oferta = ?
    """, (id_oferta,))
    row = cursor.fetchone()
    if row:
        result["scraping"] = {
            "titulo_original": row[1],
            "empresa": row[2],
            "ubicacion_scrapeada": row[3],
            "descripcion": row[4][:500] + "..." if row[4] and len(row[4]) > 500 else row[4],
            "descripcion_completa": row[4],
            "fecha_publicacion": row[5],
            "modalidad_scrapeada": row[6],
            "source": row[7]
        }

    # 2. EXTRACCION NLP
    cursor = conn.execute("""
        SELECT
            titulo_limpio,
            provincia,
            localidad,
            sector_empresa,
            area_funcional,
            nivel_seniority,
            modalidad,
            tareas_explicitas,
            experiencia_min_anios,
            experiencia_max_anios,
            nivel_educativo,
            titulo_requerido,
            requerimiento_edad,
            requerimiento_sexo,
            tiene_gente_cargo,
            skills_tecnicas_list,
            soft_skills_list,
            tecnologias_list,
            herramientas_list
        FROM ofertas_nlp
        WHERE id_oferta = ?
    """, (id_oferta,))
    row = cursor.fetchone()
    if row:
        result["nlp"] = {
            "titulo_limpio": row[0],
            "provincia": row[1],
            "localidad": row[2],
            "sector_empresa": row[3],
            "area_funcional": row[4],
            "nivel_seniority": row[5],
            "modalidad": row[6],
            "tareas_explicitas": row[7][:300] + "..." if row[7] and len(row[7]) > 300 else row[7],
            "experiencia_min_anios": row[8],
            "experiencia_max_anios": row[9],
            "nivel_educativo": row[10],
            "titulo_requerido": row[11],
            "requerimiento_edad": row[12],
            "requerimiento_sexo": row[13],
            "tiene_gente_cargo": row[14],
            "skills_tecnicas_list": row[15],
            "soft_skills_list": row[16],
            "tecnologias_list": row[17],
            "herramientas_list": row[18]
        }

    # 3. SKILLS IMPLICITAS (derivadas)
    cursor = conn.execute("""
        SELECT
            esco_skill_label,
            match_score,
            skill_tipo_fuente,
            esco_skill_type,
            skill_mencionado,
            source_classification
        FROM ofertas_esco_skills_detalle
        WHERE id_oferta = ?
        ORDER BY match_score DESC
    """, (id_oferta,))
    for row in cursor.fetchall():
        result["skills"].append({
            "skill": row[0],
            "score": row[1],
            "origen": row[2],
            "tipo": row[3],
            "skill_mencionado": row[4],
            "clasificacion": row[5]
        })

    # 4. MATCHING ESCO
    cursor = conn.execute("""
        SELECT
            isco_code,
            esco_occupation_label,
            occupation_match_score,
            occupation_match_method,
            skills_matcheados_esco,
            estado_validacion,
            notas_revision,
            score_final_ponderado,
            confidence_score
        FROM ofertas_esco_matching
        WHERE id_oferta = ?
    """, (id_oferta,))
    row = cursor.fetchone()
    if row:
        result["matching"] = {
            "isco_code": row[0],
            "esco_label": row[1],
            "match_score": row[2],
            "match_method": row[3],
            "skills_matched": row[4],
            "estado_validacion": row[5],
            "notas_revision": row[6],
            "score_final": row[7],
            "confidence": row[8]
        }

    return result


def format_offer_for_review(data: Dict) -> str:
    """
    Formatea los datos de una oferta para revision humana/Claude.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"OFERTA ID: {data['id_oferta']}")
    lines.append("=" * 70)

    # 1. SCRAPING
    lines.append("\n### 1. DATOS SCRAPING (input original)")
    lines.append("-" * 50)
    if data["scraping"]:
        s = data["scraping"]
        lines.append(f"Titulo original: {s['titulo_original']}")
        lines.append(f"Empresa: {s['empresa']}")
        lines.append(f"Ubicacion scrapeada: {s['ubicacion_scrapeada']}")
        lines.append(f"Modalidad scrapeada: {s['modalidad_scrapeada']}")
        lines.append(f"Source: {s['source']}")
        lines.append(f"\nDescripcion (primeros 500 chars):")
        lines.append(f"  {s['descripcion']}")
    else:
        lines.append("  [NO HAY DATOS DE SCRAPING]")

    # 2. NLP
    lines.append("\n### 2. EXTRACCION NLP (lo que Qwen extrajo)")
    lines.append("-" * 50)
    if data["nlp"]:
        n = data["nlp"]
        lines.append(f"titulo_limpio: {n['titulo_limpio']}")
        lines.append(f"provincia: {n['provincia']}")
        lines.append(f"localidad: {n['localidad']}")
        lines.append(f"sector_empresa: {n['sector_empresa']}")
        lines.append(f"area_funcional: {n['area_funcional']}")
        lines.append(f"nivel_seniority: {n['nivel_seniority']}")
        lines.append(f"modalidad: {n['modalidad']}")
        lines.append(f"experiencia: {n['experiencia_min_anios']}-{n['experiencia_max_anios']} anios")
        lines.append(f"nivel_educativo: {n['nivel_educativo']}")
        lines.append(f"titulo_requerido: {n['titulo_requerido']}")
        lines.append(f"tiene_gente_cargo: {n['tiene_gente_cargo']}")
        lines.append(f"\ntareas_explicitas:")
        lines.append(f"  {n['tareas_explicitas']}")
        lines.append(f"\nskills_tecnicas (LLM): {n['skills_tecnicas_list']}")
        lines.append(f"soft_skills (LLM): {n['soft_skills_list']}")
        lines.append(f"tecnologias (LLM): {n['tecnologias_list']}")
        lines.append(f"herramientas (LLM): {n['herramientas_list']}")
    else:
        lines.append("  [NO HAY DATOS NLP]")

    # 3. SKILLS
    lines.append("\n### 3. SKILLS IMPLICITAS (derivadas de tareas+titulo)")
    lines.append("-" * 50)
    if data["skills"]:
        lines.append(f"Total skills extraidas: {len(data['skills'])}")
        lines.append("\nTop 10 skills:")
        for i, sk in enumerate(data["skills"][:10], 1):
            score = sk['score'] if sk['score'] else 0
            lines.append(f"  {i}. {sk['skill']} (score={score:.2f}, tipo={sk.get('tipo', 'N/A')})")
            lines.append(f"     Mencionado: {sk.get('skill_mencionado', 'N/A')}")
    else:
        lines.append("  [NO HAY SKILLS EXTRAIDAS]")

    # 4. MATCHING
    lines.append("\n### 4. MATCHING ESCO (resultado final)")
    lines.append("-" * 50)
    if data["matching"]:
        m = data["matching"]
        lines.append(f"ISCO asignado: {m['isco_code']}")
        lines.append(f"ESCO label: {m['esco_label']}")
        lines.append(f"match_score: {m['match_score']}")
        lines.append(f"match_method: {m['match_method']}")
        lines.append(f"estado_validacion: {m['estado_validacion']}")
        if m["notas_revision"]:
            lines.append(f"notas_revision: {m['notas_revision']}")
    else:
        lines.append("  [NO HAY MATCHING]")

    # Seccion de diagnostico
    lines.append("\n" + "=" * 70)
    lines.append("PREGUNTAS PARA DIAGNOSTICO:")
    lines.append("=" * 70)
    lines.append("""
1. SCRAPING: ¿Los datos originales estan completos?
   [ ] OK  [ ] Incompleto  [ ] Error

2. NLP - Titulo limpio: ¿Se limpio correctamente?
   [ ] OK  [ ] Falta limpiar algo  [ ] Se elimino de mas

3. NLP - Ubicacion: ¿Provincia y localidad correctas?
   [ ] OK  [ ] Provincia incorrecta  [ ] Localidad incorrecta

4. NLP - Seniority: ¿El nivel es correcto para el puesto?
   [ ] OK  [ ] Deberia ser otro  [ ] Falta inferir

5. NLP - Area funcional: ¿Es el area correcta?
   [ ] OK  [ ] Deberia ser otra  [ ] Falta inferir

6. NLP - Tareas: ¿Se extrajeron correctamente?
   [ ] OK  [ ] Faltan tareas importantes  [ ] Hay tareas erroneas

7. SKILLS: ¿Son coherentes con titulo y tareas?
   [ ] OK  [ ] Faltan skills obvias  [ ] Hay skills que no corresponden

8. MATCHING: ¿El ISCO asignado es correcto?
   [ ] OK  [ ] Deberia ser ISCO ____  [ ] No deberia tener match
""")

    return "\n".join(lines)


def get_offers_with_errors(conn: sqlite3.Connection, limit: int = 10) -> List[str]:
    """Obtiene IDs de ofertas con errores detectados."""
    cursor = conn.execute("""
        SELECT DISTINCT m.id_oferta
        FROM ofertas_esco_matching m
        WHERE m.estado_validacion IN ('error_detectado', 'en_revision')
           OR m.occupation_match_score < 0.5
           OR m.isco_code IS NULL
        LIMIT ?
    """, (limit,))
    return [row[0] for row in cursor.fetchall()]


def get_pending_offers(conn: sqlite3.Connection, limit: int = 10) -> List[str]:
    """Obtiene IDs de ofertas pendientes de revision."""
    cursor = conn.execute("""
        SELECT DISTINCT m.id_oferta
        FROM ofertas_esco_matching m
        WHERE m.estado_validacion = 'pendiente'
           OR m.estado_validacion IS NULL
        LIMIT ?
    """, (limit,))
    return [row[0] for row in cursor.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="Revisar ofertas - Cadena completa")
    parser.add_argument("--id", type=str, help="ID de oferta especifica")
    parser.add_argument("--ids", type=str, help="IDs separados por coma")
    parser.add_argument("--errores", action="store_true", help="Mostrar ofertas con errores")
    parser.add_argument("--pendientes", action="store_true", help="Mostrar ofertas pendientes")
    parser.add_argument("--limit", type=int, default=10, help="Limite de ofertas")
    parser.add_argument("--json", action="store_true", help="Output en JSON")

    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))

    # Determinar que ofertas revisar
    if args.id:
        offer_ids = [args.id]
    elif args.ids:
        offer_ids = args.ids.split(",")
    elif args.errores:
        offer_ids = get_offers_with_errors(conn, args.limit)
        print(f"Encontradas {len(offer_ids)} ofertas con errores\n")
    elif args.pendientes:
        offer_ids = get_pending_offers(conn, args.limit)
        print(f"Encontradas {len(offer_ids)} ofertas pendientes\n")
    else:
        print("Uso: --id <ID> | --ids <IDs> | --errores | --pendientes")
        sys.exit(1)

    # Revisar cada oferta
    for i, id_oferta in enumerate(offer_ids, 1):
        data = get_offer_full_chain(conn, id_oferta)

        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n[{i}/{len(offer_ids)}]")
            print(format_offer_for_review(data))

            if i < len(offer_ids) and sys.stdin.isatty():
                print("\n" + "=" * 70)
                print("Presiona Enter para ver la siguiente oferta, o Ctrl+C para salir")
                print("=" * 70)
                try:
                    input()
                except KeyboardInterrupt:
                    print("\nSaliendo...")
                    break

    conn.close()


if __name__ == "__main__":
    main()
