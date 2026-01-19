#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostico de casos problematicos de matching.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'D:/OEDE/Webscrapping/database')
sys.path.insert(0, 'D:/OEDE/Webscrapping')

import sqlite3
import json
from pathlib import Path

# Importar componentes del matching
from match_ofertas_v2 import (
    load_all_configs,
    get_semantic_matcher,
    construir_query_semantica,
    obtener_filtros_isco,
    nivel_3_scoring_bge,
    match_oferta_v2_bge
)

DB_PATH = Path("D:/OEDE/Webscrapping/database/bumeran_scraping.db")


def diagnosticar_oferta(id_oferta: str, conn):
    """Diagnostica el matching de una oferta específica."""
    config = load_all_configs()

    # Obtener datos de la oferta
    cur = conn.execute("""
        SELECT
            o.id_oferta, o.titulo,
            n.titulo_limpio, n.area_funcional, n.nivel_seniority,
            n.skills_tecnicas_list, n.tareas_explicitas, n.mision_rol,
            n.tiene_gente_cargo, n.sector_empresa, n.nlp_version
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))

    row = cur.fetchone()
    if not row:
        print(f"Oferta {id_oferta} no encontrada")
        return

    oferta = {
        "id_oferta": row[0],
        "titulo": row[1],
        "titulo_limpio": row[2],
        "area_funcional": row[3],
        "nivel_seniority": row[4],
        "skills_tecnicas_list": row[5],
        "tareas_explicitas": row[6],
        "mision_rol": row[7],
        "tiene_gente_cargo": row[8],
        "sector_empresa": row[9],
        "nlp_version": row[10]
    }

    print("=" * 70)
    print(f"DIAGNÓSTICO OFERTA: {id_oferta}")
    print("=" * 70)

    print("\n[DATOS NLP]")
    print(f"  Titulo: {oferta['titulo']}")
    print(f"  Titulo limpio: {oferta['titulo_limpio']}")
    print(f"  Area funcional: {oferta['area_funcional']}")
    print(f"  Seniority: {oferta['nivel_seniority']}")
    print(f"  Tiene gente cargo: {oferta['tiene_gente_cargo']}")
    print(f"  Sector: {oferta['sector_empresa']}")
    print(f"  NLP Version: {oferta['nlp_version']}")

    # Skills
    skills = oferta.get('skills_tecnicas_list')
    if skills:
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except:
                skills = [skills]
        print(f"  Skills: {skills[:5] if skills else 'NULL'}")
    else:
        print(f"  Skills: NULL")

    # Tareas
    tareas = oferta.get('tareas_explicitas')
    if tareas:
        print(f"  Tareas: {tareas[:200]}...")
    else:
        print(f"  Tareas: NULL")

    print("\n[QUERY SEMANTICA]")
    query = construir_query_semantica(oferta)
    print(f"  {query[:300]}...")

    print("\n[FILTROS ISCO]")
    isco_filter = obtener_filtros_isco(oferta, config)
    print(f"  {isco_filter}")

    print("\n[TOP 10 CANDIDATOS BGE-M3]")
    matcher = get_semantic_matcher()
    matcher.load()

    resultados = matcher.search(query, top_k=10, isco_filter=None)  # Sin filtro primero

    for i, r in enumerate(resultados, 1):
        in_filter = "[OK]" if not isco_filter or any(r['isco_code'].startswith(p) for p in isco_filter) else "[XX]"
        print(f"  {i}. {in_filter} {r['label'][:50]}")
        print(f"       ISCO: {r['isco_code']} | Score: {r['score']:.4f}")

    print("\n[TOP 5 CON FILTRO ISCO]")
    if isco_filter:
        resultados_filtrados = matcher.search(query, top_k=5, isco_filter=isco_filter)
        for i, r in enumerate(resultados_filtrados, 1):
            print(f"  {i}. {r['label'][:50]}")
            print(f"       ISCO: {r['isco_code']} | Score: {r['score']:.4f}")
    else:
        print("  (Sin filtro ISCO aplicado)")

    print("\n[RESULTADO FINAL MATCHING]")
    result = match_oferta_v2_bge(oferta, conn, config)
    print(f"  Status: {result.status}")
    print(f"  ESCO Label: {result.esco_label}")
    print(f"  ISCO Code: {result.isco_code}")
    print(f"  Score: {result.score}")
    print(f"  Método: {result.metodo}")
    if result.alternativas:
        print(f"  Alternativas:")
        for alt in result.alternativas[:3]:
            print(f"    - {alt.get('label', 'N/A')[:40]} (score: {alt.get('score', 0):.3f})")


def buscar_ofertas_vendedor_auto(conn):
    """Busca ofertas de vendedores de autos."""
    cur = conn.execute("""
        SELECT DISTINCT o.id_oferta, o.titulo
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.titulo LIKE '%vendedor%'
          AND (o.titulo LIKE '%auto%' OR o.titulo LIKE '%vehic%' OR o.titulo LIKE '%coche%')
        LIMIT 5
    """)
    return cur.fetchall()


def buscar_ofertas_mantenimiento(conn):
    """Busca ofertas de operarios de mantenimiento."""
    cur = conn.execute("""
        SELECT DISTINCT o.id_oferta, o.titulo
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.titulo LIKE '%operario%'
          AND o.titulo LIKE '%manten%'
        LIMIT 5
    """)
    return cur.fetchall()


def main():
    conn = sqlite3.connect(str(DB_PATH))

    print("=" * 70)
    print("BUSCANDO CASOS PROBLEMÁTICOS")
    print("=" * 70)

    # Buscar vendedores de autos
    print("\nOfertas 'Vendedor Auto':")
    ofertas_auto = buscar_ofertas_vendedor_auto(conn)
    for id_of, titulo in ofertas_auto:
        print(f"  - {id_of}: {titulo[:60]}")

    # Buscar operarios mantenimiento
    print("\nOfertas 'Operario Mantenimiento':")
    ofertas_mant = buscar_ofertas_mantenimiento(conn)
    for id_of, titulo in ofertas_mant:
        print(f"  - {id_of}: {titulo[:60]}")

    # Diagnosticar primer caso de cada tipo
    if ofertas_auto:
        print("\n")
        diagnosticar_oferta(ofertas_auto[0][0], conn)

    if ofertas_mant:
        print("\n")
        diagnosticar_oferta(ofertas_mant[0][0], conn)

    conn.close()


if __name__ == "__main__":
    main()
