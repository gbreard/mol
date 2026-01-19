# -*- coding: utf-8 -*-
"""
Revision detallada NLP v11 - Muestra casos para revision manual
"""
import sqlite3
import json

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print('=' * 70)
print('REVISION MANUAL NLP v11 - CASOS DETALLADOS')
print('=' * 70)
print()

# Estadisticas resumidas
print('RESUMEN ESTADISTICO:')
print('-' * 40)

cur = conn.execute('''
    SELECT nlp_version, COUNT(*) as cnt
    FROM ofertas_nlp
    GROUP BY nlp_version
''')
for row in cur:
    print(f'  {row["nlp_version"]}: {row["cnt"]} ofertas')
print()

# Solo v11 para analisis
print('ANALISIS DETALLADO OFERTAS v11 (74 registros):')
print('-' * 40)

# 1. Titulo limpio - muestras
print('\n1. TITULO LIMPIO (top 15):')
cur = conn.execute('''
    SELECT titulo_limpio, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND titulo_limpio IS NOT NULL
    GROUP BY titulo_limpio
    ORDER BY cnt DESC
    LIMIT 15
''')
for row in cur:
    print(f'   [{row["cnt"]}] {row["titulo_limpio"]}')

# 2. Sectores
print('\n2. SECTOR EMPRESA (distribucion v11):')
cur = conn.execute('''
    SELECT sector_empresa, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND sector_empresa IS NOT NULL
    GROUP BY sector_empresa
    ORDER BY cnt DESC
    LIMIT 10
''')
for row in cur:
    print(f'   [{row["cnt"]}] {row["sector_empresa"]}')

# 3. Skills tecnicas - ejemplos de listas
print('\n3. SKILLS TECNICAS (5 ejemplos):')
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, skills_tecnicas_list
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
      AND skills_tecnicas_list IS NOT NULL
      AND skills_tecnicas_list != '[]'
    LIMIT 5
''')
for row in cur:
    print(f'   ID {row["id_oferta"]}:')
    print(f'      Titulo: {row["titulo_limpio"]}')
    print(f'      Skills: {row["skills_tecnicas_list"][:100]}...')

# 4. Soft skills - ejemplos
print('\n4. SOFT SKILLS (5 ejemplos):')
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, soft_skills_list
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
      AND soft_skills_list IS NOT NULL
      AND soft_skills_list != '[]'
    LIMIT 5
''')
for row in cur:
    print(f'   ID {row["id_oferta"]}:')
    print(f'      Titulo: {row["titulo_limpio"]}')
    print(f'      Soft skills: {row["soft_skills_list"][:80]}')

# 5. Requerimientos edad (casos con valor != 0)
print('\n5. REQUERIMIENTO EDAD (casos != 0):')
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, requerimiento_edad
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND requerimiento_edad != 0
''')
EDAD_LABELS = {1: '18-25', 2: '25-35', 3: '35-45', 4: '45+', 5: 'Ambiguo'}
count = 0
for row in cur:
    label = EDAD_LABELS.get(row['requerimiento_edad'], '?')
    print(f'   ID {row["id_oferta"]}: {row["titulo_limpio"]} -> Edad: {row["requerimiento_edad"]} ({label})')
    count += 1
if count == 0:
    print('   (Ninguno con requisito de edad)')

# 6. Experiencia - distribucion
print('\n6. EXPERIENCIA MINIMA (distribucion v11):')
cur = conn.execute('''
    SELECT experiencia_min_anios, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
    GROUP BY experiencia_min_anios
    ORDER BY experiencia_min_anios
''')
for row in cur:
    exp = row['experiencia_min_anios'] if row['experiencia_min_anios'] is not None else 'NULL'
    print(f'   {exp} anios: {row["cnt"]} ofertas')

# 7. Nivel educativo
print('\n7. NIVEL EDUCATIVO (v11):')
cur = conn.execute('''
    SELECT nivel_educativo, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
    GROUP BY nivel_educativo
    ORDER BY cnt DESC
''')
for row in cur:
    nivel = row['nivel_educativo'] if row['nivel_educativo'] else 'NULL'
    print(f'   {nivel}: {row["cnt"]}')

# 8. Casos problematicos potenciales
print('\n8. CASOS A REVISAR (potenciales problemas):')

# Sin provincia
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND (provincia IS NULL OR provincia = '')
    LIMIT 5
''')
print('   a) Sin provincia:')
for row in cur:
    print(f'      ID {row["id_oferta"]}: {row["titulo_limpio"]}')

# Sin sector
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND (sector_empresa IS NULL OR sector_empresa = '')
    LIMIT 5
''')
print('   b) Sin sector empresa:')
count = 0
for row in cur:
    print(f'      ID {row["id_oferta"]}: {row["titulo_limpio"]}')
    count += 1
if count == 0:
    print('      (Todos tienen sector)')

# Sin soft skills
cur = conn.execute('''
    SELECT COUNT(*) FROM ofertas_nlp
    WHERE nlp_version = '11.0.0' AND (soft_skills_list IS NULL OR soft_skills_list = '[]')
''')
sin_soft = cur.fetchone()[0]
print(f'   c) Sin soft skills: {sin_soft} ofertas')

# 9. Muestra completa de 3 ofertas
print('\n' + '=' * 70)
print('9. MUESTRA COMPLETA (3 ofertas aleatorias v11):')
print('=' * 70)
cur = conn.execute('''
    SELECT id_oferta, titulo_limpio, provincia, localidad, sector_empresa,
           skills_tecnicas_list, soft_skills_list, tecnologias_list, herramientas_list,
           experiencia_min_anios, experiencia_max_anios, nivel_educativo, titulo_requerido,
           requerimiento_edad, requerimiento_sexo, tareas_explicitas
    FROM ofertas_nlp
    WHERE nlp_version = '11.0.0'
    ORDER BY RANDOM()
    LIMIT 3
''')
for i, row in enumerate(cur, 1):
    print(f'\n--- Oferta {i} (ID: {row["id_oferta"]}) ---')
    print(f'Titulo: {row["titulo_limpio"]}')
    print(f'Ubicacion: {row["localidad"]}, {row["provincia"]}')
    print(f'Sector: {row["sector_empresa"]}')
    print(f'Skills tecnicas: {row["skills_tecnicas_list"]}')
    print(f'Soft skills: {row["soft_skills_list"]}')
    print(f'Tecnologias: {row["tecnologias_list"]}')
    print(f'Herramientas: {row["herramientas_list"]}')
    print(f'Experiencia: {row["experiencia_min_anios"]}-{row["experiencia_max_anios"]} anios')
    print(f'Educacion: {row["nivel_educativo"]} | Titulo: {row["titulo_requerido"]}')
    print(f'Req. edad: {row["requerimiento_edad"]} | Req. sexo: {row["requerimiento_sexo"]}')
    if row["tareas_explicitas"]:
        print(f'Tareas: {row["tareas_explicitas"][:150]}...')

print('\n' + '=' * 70)
print('FIN REVISION MANUAL')
print('=' * 70)

conn.close()
