#!/usr/bin/env python3
"""
Test de mejoras en regex_patterns_v2
=====================================
Compara parseo v1 vs v2 en ofertas mal parseadas
"""

import sys
import sqlite3
from pathlib import Path

# Agregar rutas al path
sys.path.insert(0, str(Path(__file__).parent.parent / '02.5_nlp_extraction' / 'scripts'))

# Importar ambas versiones
from patterns import regex_patterns as v1
from patterns import regex_patterns_v2 as v2


def test_oferta(id_oferta, titulo, descripcion):
    """Prueba una oferta con ambas versiones de patrones"""

    print('='*80)
    print(f'OFERTA ID: {id_oferta}')
    print(f'TITULO: {titulo}')
    print('='*80)
    print()

    # Preview de descripción
    print('DESCRIPCION (primeros 300 chars):')
    print(descripcion[:300])
    print('...\n')

    # TEST V1 (Original)
    print('--- VERSION 1 (ORIGINAL) ---')
    exp_v1 = v1.ExperienciaPatterns.extract_years(descripcion)
    edu_v1 = v1.EducacionPatterns.extract_nivel(descripcion)
    jornada_v1 = v1.JornadaPatterns.extract_tipo(descripcion)
    skills_tec_v1 = v1.SkillsPatterns.extract_technical_skills(descripcion)

    print(f'Experiencia: {exp_v1}')
    print(f'Educación: {edu_v1}')
    print(f'Jornada: {jornada_v1}')
    print(f'Skills técnicas: {skills_tec_v1[:3] if skills_tec_v1 else None}')  # Mostrar solo 3

    score_v1 = sum([
        1 if exp_v1[0] is not None else 0,
        1 if edu_v1 is not None else 0,
        1 if jornada_v1 is not None else 0,
        1 if skills_tec_v1 else 0
    ])
    print(f'SCORE V1: {score_v1}/4')
    print()

    # TEST V2 (Mejorado)
    print('--- VERSION 2 (MEJORADO) ---')
    exp_v2 = v2.ExperienciaPatterns.extract_years(descripcion)
    edu_v2 = v2.EducacionPatterns.extract_nivel(descripcion)
    carrera_v2 = v2.EducacionPatterns.extract_carrera(descripcion)
    jornada_v2 = v2.JornadaPatterns.extract_tipo(descripcion)
    horario_v2 = v2.JornadaPatterns.extract_horario(descripcion)
    dias_v2 = v2.JornadaPatterns.extract_dias(descripcion)
    skills_tec_v2 = v2.SkillsPatterns.extract_technical_skills(descripcion)

    print(f'Experiencia: {exp_v2}')
    print(f'Educación: {edu_v2}')
    print(f'Carrera: {carrera_v2}')
    print(f'Jornada: {jornada_v2}')
    print(f'Horario: {horario_v2}')
    print(f'Días: {dias_v2}')
    print(f'Skills técnicas: {skills_tec_v2[:5] if skills_tec_v2 else None}')

    score_v2 = sum([
        1 if exp_v2[0] is not None else 0,
        1 if edu_v2 is not None else 0,
        1 if jornada_v2 is not None else 0,
        1 if horario_v2 is not None else 0,
        1 if skills_tec_v2 else 0
    ])
    print(f'SCORE V2: {score_v2}/5')
    print()

    # Comparación
    mejora = score_v2 - score_v1
    if mejora > 0:
        print(f'[+] MEJORA: +{mejora} campos detectados')
    elif mejora == 0:
        print('[=] Sin cambios')
    else:
        print(f'[-] REGRESION: {mejora} campos')

    print()
    print()

    return score_v1, score_v2


def main():
    """Ejecuta pruebas sobre ofertas mal parseadas"""

    db_path = Path(__file__).parent / 'bumeran_scraping.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print('='*80)
    print('TEST DE MEJORAS - regex_patterns_v2')
    print('='*80)
    print()

    # Obtener top 10 ofertas con peor score
    cursor.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
             CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
             CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) as score_actual
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.descripcion IS NOT NULL
        ORDER BY score_actual ASC, LENGTH(o.descripcion) DESC
        LIMIT 10
    ''')

    ofertas = cursor.fetchall()
    print(f'Analizando {len(ofertas)} ofertas con peor parseo...\n')

    scores_v1 = []
    scores_v2 = []

    for oferta in ofertas:
        id_oferta, titulo, descripcion, score_actual = oferta
        score_v1, score_v2 = test_oferta(id_oferta, titulo, descripcion)
        scores_v1.append(score_v1)
        scores_v2.append(score_v2)

    conn.close()

    # Resumen final
    print('='*80)
    print('RESUMEN COMPARATIVO')
    print('='*80)
    print()

    avg_v1 = sum(scores_v1) / len(scores_v1)
    avg_v2 = sum(scores_v2) / len(scores_v2)

    print(f'Promedio V1 (original): {avg_v1:.2f}/4')
    print(f'Promedio V2 (mejorado): {avg_v2:.2f}/5')
    print()

    mejora_pct = ((avg_v2 / 5) - (avg_v1 / 4)) * 100
    print(f'Mejora porcentual: {mejora_pct:+.1f}%')
    print()

    ofertas_mejoradas = sum(1 for v1, v2 in zip(scores_v1, scores_v2) if v2 > v1)
    print(f'Ofertas con mejora: {ofertas_mejoradas}/{len(ofertas)} ({ofertas_mejoradas/len(ofertas)*100:.0f}%)')


if __name__ == '__main__':
    main()
