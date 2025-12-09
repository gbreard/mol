#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOL-54: Analizar por que algunas ofertas no tienen skills extraidos
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

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

    print("=" * 90)
    print("ANALISIS: POR QUE ALGUNAS OFERTAS NO TIENEN SKILLS EXTRAIDOS?")
    print("=" * 90)

    # 1. Ofertas SIN skills tecnicos
    print("\n" + "=" * 90)
    print("1. OFERTAS SIN SKILLS TECNICOS (5 ejemplos)")
    print("=" * 90)

    cursor.execute("""
        SELECT
            v.id_oferta, o.titulo, COALESCE(o.descripcion_utf8, o.descripcion) as desc_text,
            v.resultado_capa1_verificado
        FROM validacion_v7 v
        JOIN ofertas o ON CAST(v.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
        ORDER BY RANDOM()
    """)

    sin_skills = []
    con_skills = []

    for row in cursor.fetchall():
        id_oferta, titulo, descripcion, nlp_json = row

        skills_tec = []
        skills_soft = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))
            except:
                pass

        oferta = {
            'id': id_oferta,
            'titulo': titulo,
            'descripcion': descripcion or '',
            'skills_tec': skills_tec,
            'skills_soft': skills_soft
        }

        if not skills_tec:
            sin_skills.append(oferta)
        else:
            con_skills.append(oferta)

    # Mostrar 5 SIN skills
    for i, oferta in enumerate(sin_skills[:5], 1):
        print(f"\n{'-' * 90}")
        print(f"[{i}] ID: {oferta['id']}")
        print(f"TITULO: {oferta['titulo']}")
        print(f"\nDESCRIPCION (primeros 600 chars):")
        desc = oferta['descripcion'][:600].replace('\n', ' ').replace('\r', '')
        print(f"  {desc}...")
        print(f"\nSKILLS EXTRAIDOS:")
        print(f"  - Tecnicos: {oferta['skills_tec'] if oferta['skills_tec'] else '[NINGUNO]'}")
        print(f"  - Blandos: {oferta['skills_soft'][:3] if oferta['skills_soft'] else '[NINGUNO]'}")

        # Buscar keywords de skills en la descripcion
        desc_lower = oferta['descripcion'].lower()
        keywords_tech = ['excel', 'word', 'python', 'java', 'sql', 'sap', 'erp', 'crm',
                        'photoshop', 'autocad', 'office', 'linux', 'windows', 'aws',
                        'angular', 'react', 'node', 'docker', 'kubernetes', 'git',
                        'javascript', 'typescript', 'c#', 'c++', '.net', 'php', 'ruby',
                        'tableau', 'power bi', 'salesforce', 'oracle', 'mysql', 'mongodb',
                        'jira', 'trello', 'slack', 'teams', 'zoom', 'google', 'microsoft',
                        'ingles', 'portugues', 'manejo de', 'conocimiento de', 'experiencia en']

        encontrados = []
        for kw in keywords_tech:
            if kw in desc_lower:
                encontrados.append(kw)

        if encontrados:
            print(f"\n  [!] KEYWORDS DETECTADOS EN DESCRIPCION (no extraidos):")
            print(f"      {encontrados}")
            print(f"  --> PROBLEMA: NLP no capturo estos skills")
        else:
            print(f"\n  [OK] No se detectan keywords tecnicos obvios en descripcion")
            print(f"  --> La oferta probablemente NO tiene skills tecnicos explicitos")

    # 2. Ofertas CON skills tecnicos
    print("\n" + "=" * 90)
    print("2. OFERTAS CON SKILLS TECNICOS (5 ejemplos)")
    print("=" * 90)

    for i, oferta in enumerate(con_skills[:5], 1):
        print(f"\n{'-' * 90}")
        print(f"[{i}] ID: {oferta['id']}")
        print(f"TITULO: {oferta['titulo']}")
        print(f"\nDESCRIPCION (primeros 600 chars):")
        desc = oferta['descripcion'][:600].replace('\n', ' ').replace('\r', '')
        print(f"  {desc}...")
        print(f"\nSKILLS EXTRAIDOS:")
        print(f"  - Tecnicos ({len(oferta['skills_tec'])}): {oferta['skills_tec']}")
        print(f"  - Blandos ({len(oferta['skills_soft'])}): {oferta['skills_soft'][:5] if len(oferta['skills_soft']) > 5 else oferta['skills_soft']}")

    # 3. Estadisticas
    print("\n" + "=" * 90)
    print("3. ESTADISTICAS")
    print("=" * 90)

    total = len(sin_skills) + len(con_skills)
    print(f"\nTotal ofertas NLP v8.0: {total}")
    print(f"  - Sin skills tecnicos: {len(sin_skills)} ({len(sin_skills)/total*100:.1f}%)")
    print(f"  - Con skills tecnicos: {len(con_skills)} ({len(con_skills)/total*100:.1f}%)")

    # Analizar cuantas SIN skills tienen keywords detectables
    sin_skills_con_keywords = 0
    for oferta in sin_skills:
        desc_lower = oferta['descripcion'].lower()
        keywords_tech = ['excel', 'word', 'python', 'java', 'sql', 'sap', 'erp',
                        'photoshop', 'autocad', 'office', 'linux', 'manejo de',
                        'conocimiento de', 'experiencia en', 'dominio de']
        if any(kw in desc_lower for kw in keywords_tech):
            sin_skills_con_keywords += 1

    print(f"\nDe las {len(sin_skills)} ofertas SIN skills tecnicos:")
    print(f"  - Con keywords detectables en descripcion: {sin_skills_con_keywords} ({sin_skills_con_keywords/len(sin_skills)*100:.1f}%)")
    print(f"  - Sin keywords detectables: {len(sin_skills) - sin_skills_con_keywords} ({(len(sin_skills) - sin_skills_con_keywords)/len(sin_skills)*100:.1f}%)")

    print("\n" + "=" * 90)
    print("CONCLUSION")
    print("=" * 90)
    if sin_skills_con_keywords > len(sin_skills) * 0.3:
        print(f"\n  [!] {sin_skills_con_keywords}/{len(sin_skills)} ofertas tienen keywords pero NLP no los extrajo")
        print(f"  --> PROBLEMA DEL NLP: Hay skills en las descripciones que no se capturan")
        print(f"  --> Accion: Revisar prompts de extraccion")
    else:
        print(f"\n  [OK] La mayoria de ofertas sin skills realmente no tienen skills tecnicos")
        print(f"  --> Las ofertas son de posiciones que no requieren skills tecnicos especificos")
        print(f"  --> El NLP funciona correctamente")

    conn.close()

if __name__ == "__main__":
    main()
