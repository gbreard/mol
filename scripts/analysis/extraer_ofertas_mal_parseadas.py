#!/usr/bin/env python3
"""
Extrae ejemplos de ofertas mal parseadas para análisis manual
Identifica patrones y genera reporte de mejoras necesarias
"""

import sqlite3
import json
from pathlib import Path

def extraer_ofertas_mal_parseadas(limit=10):
    """Extrae ofertas con peor parseo para análisis"""

    db_path = Path(__file__).parent / 'bumeran_scraping.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print('='*80)
    print('EXTRACCION DE OFERTAS MAL PARSEADAS PARA ANALISIS')
    print('='*80)

    # Extraer ofertas con score más bajo
    cursor.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            DATE(o.scrapeado_en) as fecha_scraping,
            LENGTH(o.descripcion) as desc_length,
            -- Score de calidad
            (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
             CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
             CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) as score_calidad,
            -- Datos NLP parseados
            n.experiencia_min_anios,
            n.nivel_educativo,
            n.soft_skills_list,
            n.skills_tecnicas_list,
            n.idioma_principal,
            n.salario_min,
            n.salario_max,
            n.jornada_laboral
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.descripcion IS NOT NULL
        ORDER BY score_calidad ASC, LENGTH(o.descripcion) DESC
        LIMIT ?
    ''', (limit,))

    ofertas = cursor.fetchall()

    print(f'\nAnalizando {len(ofertas)} ofertas con peor parseo...\n')

    # Crear reporte detallado
    reporte_path = Path(__file__).parent / 'REPORTE_OFERTAS_MAL_PARSEADAS.txt'

    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write('='*80 + '\n')
        f.write('REPORTE: OFERTAS MAL PARSEADAS - ANALISIS PARA MEJORA DEL EXTRACTOR NLP\n')
        f.write('='*80 + '\n\n')

        for idx, oferta in enumerate(ofertas, 1):
            (id_oferta, titulo, descripcion, fecha, desc_length, score,
             exp_min, nivel_edu, soft_skills, skills_tec, idioma,
             sal_min, sal_max, jornada) = oferta

            f.write(f'\n{"="*80}\n')
            f.write(f'OFERTA #{idx} - ID: {id_oferta}\n')
            f.write(f'{"="*80}\n\n')

            f.write(f'SCORE DE CALIDAD: {score}/7\n')
            f.write(f'Fecha scraping: {fecha}\n')
            f.write(f'Longitud descripción: {desc_length} caracteres\n\n')

            f.write(f'TITULO:\n{titulo}\n\n')

            f.write(f'DATOS PARSEADOS:\n')
            f.write(f'  - Experiencia mínima: {exp_min if exp_min else "NO PARSEADO"}\n')
            f.write(f'  - Nivel educativo: {nivel_edu if nivel_edu else "NO PARSEADO"}\n')
            f.write(f'  - Soft skills: {soft_skills if soft_skills and soft_skills != "[]" else "NO PARSEADO"}\n')
            f.write(f'  - Skills técnicas: {skills_tec if skills_tec and skills_tec != "[]" else "NO PARSEADO"}\n')
            f.write(f'  - Idioma: {idioma if idioma else "NO PARSEADO"}\n')
            f.write(f'  - Salario: {sal_min if sal_min else "NO PARSEADO"} - {sal_max if sal_max else "NO PARSEADO"}\n')
            f.write(f'  - Jornada: {jornada if jornada else "NO PARSEADO"}\n\n')

            f.write(f'DESCRIPCION COMPLETA:\n')
            f.write('-'*80 + '\n')
            f.write(descripcion)
            f.write('\n' + '-'*80 + '\n\n')

            # Análisis de patrones potenciales
            f.write('ANALISIS DE PATRONES DETECTADOS:\n')
            desc_lower = descripcion.lower()

            # Buscar menciones de experiencia
            if any(word in desc_lower for word in ['años', 'año', 'experiencia', 'senior', 'junior', 'ssr']):
                f.write('  ✓ Mención de EXPERIENCIA encontrada en texto\n')

            # Buscar menciones de educación
            if any(word in desc_lower for word in ['universitario', 'secundario', 'terciario', 'título', 'carrera', 'graduado']):
                f.write('  ✓ Mención de EDUCACION encontrada en texto\n')

            # Buscar menciones de skills
            if any(word in desc_lower for word in ['python', 'java', 'sql', 'excel', 'office', 'inglés', 'comunicación']):
                f.write('  ✓ Mención de SKILLS encontrada en texto\n')

            # Buscar menciones de salario
            if any(word in desc_lower for word in ['$', 'pesos', 'salario', 'sueldo', 'remuneración']):
                f.write('  ✓ Mención de SALARIO encontrada en texto\n')

            # Buscar menciones de jornada
            if any(word in desc_lower for word in ['full time', 'part time', 'medio tiempo', 'jornada completa', 'horario']):
                f.write('  ✓ Mención de JORNADA encontrada en texto\n')

            f.write('\n')

            # Separador entre ofertas
            f.write('\n' + '='*80 + '\n')
            f.write('='*80 + '\n\n')

    conn.close()

    print(f'[OK] Reporte generado: {reporte_path}')
    print(f'\nArchivo creado con {len(ofertas)} ofertas para análisis manual.')
    print('Revisar el archivo para identificar patrones y mejorar el extractor NLP.')

    return reporte_path


if __name__ == '__main__':
    extraer_ofertas_mal_parseadas(limit=10)
