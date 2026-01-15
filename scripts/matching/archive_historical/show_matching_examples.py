#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOL-54: Mostrar ejemplos concretos del matching
"""

import sqlite3
import json
import struct
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def parse_score(value):
    """Convierte score que puede ser float, bytes o None."""
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
    """Parse JSON que puede estar doblemente codificado"""
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

def get_nlp_skills(cursor, id_oferta):
    """Obtiene skills de NLP para una oferta"""
    cursor.execute("""
        SELECT resultado_capa1_verificado
        FROM validacion_v7
        WHERE id_oferta = ?
    """, (str(id_oferta),))
    row = cursor.fetchone()
    if not row or not row[0]:
        return [], []

    try:
        data = json.loads(row[0])
        skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
        skills_soft = parse_nested_json(data.get('soft_skills_list'))
        return skills_tec, skills_soft
    except:
        return [], []

def show_confirmed(cursor, limit=5):
    """Muestra ofertas CONFIRMADAS (score > 0.75)"""
    print("=" * 80)
    print("1. OFERTAS CONFIRMADAS (score > 0.75)")
    print("=" * 80)

    cursor.execute("""
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label,
               m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.match_confirmado = 1
        ORDER BY m.score_final_ponderado DESC
        LIMIT ?
    """, (limit,))

    for i, row in enumerate(cursor.fetchall(), 1):
        id_oferta, titulo, esco, score_final, score_tit, score_sk, score_desc = row
        score_final = parse_score(score_final)
        score_tit = parse_score(score_tit)
        score_sk = parse_score(score_sk)
        score_desc = parse_score(score_desc)

        skills_tec, skills_soft = get_nlp_skills(cursor, id_oferta)

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo: {titulo[:70]}...")
        print(f"    ESCO: {esco[:60]}...")
        print(f"    Score Final: {score_final:.3f}")
        print(f"    - Titulo (50%): {score_tit:.3f}")
        print(f"    - Skills (40%): {score_sk:.3f}")
        print(f"    - Descripcion (10%): {score_desc:.3f}")
        print(f"    Skills Tecnicos: {skills_tec[:5] if skills_tec else '[VACIO]'}")
        print(f"    Skills Blandos: {skills_soft[:3] if skills_soft else '[VACIO]'}")

def show_rejected(cursor, limit=5):
    """Muestra ofertas RECHAZADAS (score < 0.50)"""
    print("\n" + "=" * 80)
    print("2. OFERTAS RECHAZADAS (score < 0.50)")
    print("=" * 80)

    cursor.execute("""
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label,
               m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.match_confirmado = 0 AND m.requiere_revision = 0
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    for i, row in enumerate(cursor.fetchall(), 1):
        id_oferta, titulo, esco, score_final, score_tit, score_sk, score_desc = row
        score_final = parse_score(score_final)
        score_tit = parse_score(score_tit)
        score_sk = parse_score(score_sk)
        score_desc = parse_score(score_desc)

        skills_tec, skills_soft = get_nlp_skills(cursor, id_oferta)

        # Analizar por que fue rechazado
        razones = []
        if score_tit < 0.5:
            razones.append("titulo_bajo")
        if score_sk < 0.3:
            razones.append("skills_bajo")
        if not skills_tec and not skills_soft:
            razones.append("sin_skills_nlp")
        if len(titulo) < 20:
            razones.append("titulo_corto")

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo: {titulo[:70]}...")
        print(f"    ESCO: {esco[:60] if esco else '[SIN MATCH]'}...")
        print(f"    Score Final: {score_final:.3f}")
        print(f"    - Titulo (50%): {score_tit:.3f}")
        print(f"    - Skills (40%): {score_sk:.3f}")
        print(f"    - Descripcion (10%): {score_desc:.3f}")
        print(f"    Skills Tecnicos: {skills_tec[:3] if skills_tec else '[VACIO]'}")
        print(f"    Skills Blandos: {skills_soft[:3] if skills_soft else '[VACIO]'}")
        print(f"    Razon rechazo: {', '.join(razones) if razones else 'score_general_bajo'}")

def show_revision(cursor, limit=5):
    """Muestra ofertas en REVISION (score 0.50-0.75)"""
    print("\n" + "=" * 80)
    print("3. OFERTAS EN REVISION (score 0.50-0.75)")
    print("=" * 80)

    cursor.execute("""
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label,
               m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.requiere_revision = 1
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    for i, row in enumerate(cursor.fetchall(), 1):
        id_oferta, titulo, esco, score_final, score_tit, score_sk, score_desc = row
        score_final = parse_score(score_final)
        score_tit = parse_score(score_tit)
        score_sk = parse_score(score_sk)
        score_desc = parse_score(score_desc)

        skills_tec, skills_soft = get_nlp_skills(cursor, id_oferta)

        # Que le falta para ser confirmada
        falta = []
        if score_tit < 0.7:
            falta.append(f"mejorar_titulo ({score_tit:.2f} < 0.70)")
        if score_sk < 0.6:
            falta.append(f"mejorar_skills ({score_sk:.2f} < 0.60)")
        if not skills_tec:
            falta.append("extraer_skills_tecnicos")

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo: {titulo[:70]}...")
        print(f"    ESCO: {esco[:60]}...")
        print(f"    Score Final: {score_final:.3f}")
        print(f"    - Titulo (50%): {score_tit:.3f}")
        print(f"    - Skills (40%): {score_sk:.3f}")
        print(f"    - Descripcion (10%): {score_desc:.3f}")
        print(f"    Skills Tecnicos: {skills_tec[:3] if skills_tec else '[VACIO]'}")
        print(f"    Skills Blandos: {skills_soft[:3] if skills_soft else '[VACIO]'}")
        print(f"    Que le falta: {', '.join(falta) if falta else 'cercano al umbral'}")

def show_nlp_stats(cursor):
    """Muestra estadisticas de NLP"""
    print("\n" + "=" * 80)
    print("4. ESTADISTICAS NLP")
    print("=" * 80)

    # Total ofertas con NLP v8.0
    cursor.execute("SELECT COUNT(*) FROM validacion_v7 WHERE nlp_version = '8.0.0'")
    total_nlp = cursor.fetchone()[0]

    # Contar skills
    cursor.execute("SELECT resultado_capa1_verificado FROM validacion_v7 WHERE nlp_version = '8.0.0'")

    sin_skills_tec = 0
    sin_skills_soft = 0
    total_skills_tec = 0
    total_skills_soft = 0
    count = 0

    for row in cursor.fetchall():
        count += 1
        if row[0]:
            try:
                data = json.loads(row[0])
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))

                if not skills_tec:
                    sin_skills_tec += 1
                else:
                    total_skills_tec += len(skills_tec)

                if not skills_soft:
                    sin_skills_soft += 1
                else:
                    total_skills_soft += len(skills_soft)
            except:
                sin_skills_tec += 1
                sin_skills_soft += 1
        else:
            sin_skills_tec += 1
            sin_skills_soft += 1

    con_skills_tec = count - sin_skills_tec
    con_skills_soft = count - sin_skills_soft

    print(f"\nTotal ofertas con NLP v8.0: {total_nlp}")
    print(f"\nSkills Tecnicos:")
    print(f"  - Con skills: {con_skills_tec} ({con_skills_tec/count*100:.1f}%)")
    print(f"  - Sin skills: {sin_skills_tec} ({sin_skills_tec/count*100:.1f}%)")
    print(f"  - Promedio por oferta (cuando hay): {total_skills_tec/con_skills_tec:.1f}" if con_skills_tec else "  - N/A")

    print(f"\nSkills Blandos:")
    print(f"  - Con skills: {con_skills_soft} ({con_skills_soft/count*100:.1f}%)")
    print(f"  - Sin skills: {sin_skills_soft} ({sin_skills_soft/count*100:.1f}%)")
    print(f"  - Promedio por oferta (cuando hay): {total_skills_soft/con_skills_soft:.1f}" if con_skills_soft else "  - N/A")

    print(f"\nPromedio total skills por oferta: {(total_skills_tec + total_skills_soft)/count:.1f}")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    show_confirmed(cursor, 5)
    show_rejected(cursor, 5)
    show_revision(cursor, 5)
    show_nlp_stats(cursor)

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
