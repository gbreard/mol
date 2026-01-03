#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOL-54: Ejemplos SOLO de ofertas con NLP v8.0
"""

import sqlite3
import json
import struct
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def parse_score(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0

def parse_nested_json(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed] if parsed else []
        except:
            return [value] if value else []
    return []

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("EJEMPLOS SOLO DE OFERTAS CON NLP v8.0")
    print("=" * 80)

    # 1. TOP 5 score mas alto CON NLP v8.0
    print("\n" + "=" * 80)
    print("1. TOP 5 SCORE MAS ALTO (con NLP v8.0)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            v.id_oferta, o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion,
            v.resultado_capa1_verificado
        FROM validacion_v7 v
        JOIN ofertas o ON CAST(v.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
        ORDER BY m.score_final_ponderado DESC
        LIMIT 5
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        id_oferta, titulo, esco, score_final, score_tit, score_sk, score_desc, nlp_json = row
        score_final = parse_score(score_final)
        score_tit = parse_score(score_tit)
        score_sk = parse_score(score_sk)
        score_desc = parse_score(score_desc)

        skills_tec = []
        skills_soft = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))
            except:
                pass

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo: {titulo[:65]}")
        print(f"    ESCO:   {esco[:65] if esco else '[SIN MATCH]'}")
        print(f"    Score Final: {score_final:.3f}")
        print(f"      - Titulo (50%): {score_tit:.3f}")
        print(f"      - Skills (40%): {score_sk:.3f}")
        print(f"      - Desc (10%):   {score_desc:.3f}")
        print(f"    Skills Tecnicos ({len(skills_tec)}): {skills_tec if skills_tec else '[VACIO]'}")
        print(f"    Skills Blandos ({len(skills_soft)}): {skills_soft[:5] if skills_soft else '[VACIO]'}")

        # Evaluar si tiene sentido
        match_ok = "?"
        if esco and titulo:
            titulo_lower = titulo.lower()
            esco_lower = esco.lower() if esco else ""
            # Heuristica simple
            if any(word in esco_lower for word in titulo_lower.split()[:2]):
                match_ok = "SI - palabras clave coinciden"
            elif score_final > 0.7:
                match_ok = "PROBABLE - score alto"
            else:
                match_ok = "REVISAR - no hay coincidencia obvia"
        print(f"    Match tiene sentido: {match_ok}")

    # 2. BOTTOM 5 score mas bajo CON NLP v8.0
    print("\n" + "=" * 80)
    print("2. BOTTOM 5 SCORE MAS BAJO (con NLP v8.0)")
    print("=" * 80)

    cursor.execute("""
        SELECT
            v.id_oferta, o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion,
            v.resultado_capa1_verificado
        FROM validacion_v7 v
        JOIN ofertas o ON CAST(v.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0' AND m.score_final_ponderado IS NOT NULL
        ORDER BY m.score_final_ponderado ASC
        LIMIT 5
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        id_oferta, titulo, esco, score_final, score_tit, score_sk, score_desc, nlp_json = row
        score_final = parse_score(score_final)
        score_tit = parse_score(score_tit)
        score_sk = parse_score(score_sk)
        score_desc = parse_score(score_desc)

        skills_tec = []
        skills_soft = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))
            except:
                pass

        # Analizar por que bajo
        razones = []
        if score_tit < 0.5:
            razones.append(f"titulo_bajo({score_tit:.2f})")
        if score_sk < 0.4:
            razones.append(f"skills_bajo({score_sk:.2f})")
        if not skills_tec and not skills_soft:
            razones.append("sin_skills_extraidos")
        elif skills_tec or skills_soft:
            razones.append("tiene_skills_pero_mal_match")

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo: {titulo[:65]}")
        print(f"    ESCO:   {esco[:65] if esco else '[SIN MATCH]'}")
        print(f"    Score Final: {score_final:.3f}")
        print(f"      - Titulo (50%): {score_tit:.3f}")
        print(f"      - Skills (40%): {score_sk:.3f}")
        print(f"      - Desc (10%):   {score_desc:.3f}")
        print(f"    Skills Tecnicos ({len(skills_tec)}): {skills_tec if skills_tec else '[VACIO]'}")
        print(f"    Skills Blandos ({len(skills_soft)}): {skills_soft[:5] if skills_soft else '[VACIO]'}")
        print(f"    Por que bajo: {', '.join(razones) if razones else 'desconocido'}")

    # 3. Estadisticas de las 121 con NLP v8.0
    print("\n" + "=" * 80)
    print("3. ESTADISTICAS DE LAS 121 CON NLP v8.0")
    print("=" * 80)

    # Contar skills
    cursor.execute("""
        SELECT v.resultado_capa1_verificado, m.score_final_ponderado
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
    """)

    total = 0
    con_skills_tec = 0
    con_skills_soft = 0
    scores = []
    total_skills_tec = 0
    total_skills_soft = 0

    for row in cursor.fetchall():
        total += 1
        nlp_json, score = row

        if score:
            scores.append(parse_score(score))

        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))

                if skills_tec:
                    con_skills_tec += 1
                    total_skills_tec += len(skills_tec)
                if skills_soft:
                    con_skills_soft += 1
                    total_skills_soft += len(skills_soft)
            except:
                pass

    print(f"\nTotal ofertas con NLP v8.0: {total}")
    print(f"\nSkills Tecnicos:")
    print(f"  - Con skills: {con_skills_tec}/{total} ({con_skills_tec/total*100:.1f}%)")
    print(f"  - Sin skills: {total - con_skills_tec}/{total} ({(total-con_skills_tec)/total*100:.1f}%)")
    if con_skills_tec > 0:
        print(f"  - Promedio cuando hay: {total_skills_tec/con_skills_tec:.1f} skills")

    print(f"\nSkills Blandos:")
    print(f"  - Con skills: {con_skills_soft}/{total} ({con_skills_soft/total*100:.1f}%)")
    print(f"  - Sin skills: {total - con_skills_soft}/{total} ({(total-con_skills_soft)/total*100:.1f}%)")
    if con_skills_soft > 0:
        print(f"  - Promedio cuando hay: {total_skills_soft/con_skills_soft:.1f} skills")

    if scores:
        print(f"\nScores de Matching (solo las {len(scores)} con match):")
        print(f"  - Promedio: {sum(scores)/len(scores):.3f}")
        print(f"  - Minimo:   {min(scores):.3f}")
        print(f"  - Maximo:   {max(scores):.3f}")

        # Distribucion
        confirmados = sum(1 for s in scores if s > 0.75)
        revision = sum(1 for s in scores if 0.5 <= s <= 0.75)
        rechazados = sum(1 for s in scores if s < 0.5)

        print(f"\nDistribucion de las {len(scores)} ofertas con NLP v8.0:")
        print(f"  - Confirmados (>0.75): {confirmados} ({confirmados/len(scores)*100:.1f}%)")
        print(f"  - Revision (0.50-0.75): {revision} ({revision/len(scores)*100:.1f}%)")
        print(f"  - Rechazados (<0.50): {rechazados} ({rechazados/len(scores)*100:.1f}%)")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
