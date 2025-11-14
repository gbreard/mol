#!/usr/bin/env python3
"""
Verificar mejoras en NLP v2
"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Verificar métricas de calidad
cursor.execute('''
    SELECT
        COUNT(*) as total,
        AVG(CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) as score_promedio,
        SUM(CASE WHEN (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) < 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_mal_parseadas,
        SUM(CASE WHEN (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
            CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_bien_parseadas
    FROM ofertas o
    LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
''')

result = cursor.fetchone()
total, score_promedio, pct_mal, pct_bien = result

print('=' * 70)
print('METRICAS DE CALIDAD NLP - POST IMPLEMENTACION V2')
print('=' * 70)
print()
print(f'Total ofertas:           {total:,}')
print(f'Score promedio:          {score_promedio:.2f}/7 ({score_promedio/7*100:.1f}%)')
print(f'Mal parseadas (< 2):     {pct_mal:.1f}%')
print(f'Bien parseadas (>= 4):   {pct_bien:.1f}%')
print()

# Verificar versión del NLP
cursor.execute('SELECT nlp_version, COUNT(*) FROM ofertas_nlp GROUP BY nlp_version')
versions = cursor.fetchall()
print('VERSIONES NLP EN LA BASE:')
for version, count in versions:
    print(f'  Version {version}: {count:,} ofertas')
print()

# Comparar con métricas anteriores
print('COMPARACION CON V1:')
print('  Antes (v1):')
print('    - Score promedio: 2.14/7 (30.6%)')
print('    - Mal parseadas:  35.0%')
print('    - Bien parseadas: 15.0%')
print()
print('  Ahora (v2):')
print(f'    - Score promedio: {score_promedio:.2f}/7 ({score_promedio/7*100:.1f}%)')
print(f'    - Mal parseadas:  {pct_mal:.1f}%')
print(f'    - Bien parseadas: {pct_bien:.1f}%')
print()
print('  MEJORA:')
mejora_score = (score_promedio/7*100) - 30.6
mejora_mal = 35.0 - pct_mal
mejora_bien = pct_bien - 15.0
print(f'    - Score:          {mejora_score:+.1f}%')
print(f'    - Mal parseadas:  {mejora_mal:+.1f}% (reduccion)')
print(f'    - Bien parseadas: {mejora_bien:+.1f}% (aumento)')

conn.close()
