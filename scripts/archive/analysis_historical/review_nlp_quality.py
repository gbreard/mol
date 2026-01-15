# -*- coding: utf-8 -*-
"""
Revision manual de calidad NLP v11
"""
import sqlite3
import json
import sys

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    db_path = os.path.join(project_dir, 'database', 'bumeran_scraping.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print('=== REVISION MANUAL NLP v11 - 200 OFERTAS ===')
    print()

    # 1. Conteo por version
    cur = conn.execute('''
        SELECT nlp_version, COUNT(*) as cnt
        FROM ofertas_nlp
        GROUP BY nlp_version
    ''')
    print('1. DISTRIBUCION POR VERSION:')
    for row in cur:
        print(f'   {row["nlp_version"]}: {row["cnt"]} ofertas')
    print()

    # 2. Campos geograficos
    print('2. CAMPOS GEOGRAFICOS:')
    cur = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN provincia IS NOT NULL AND provincia != '' THEN 1 ELSE 0 END) as con_provincia,
            SUM(CASE WHEN localidad IS NOT NULL AND localidad != '' THEN 1 ELSE 0 END) as con_localidad
        FROM ofertas_nlp
    ''')
    row = cur.fetchone()
    total = row["total"]
    print(f'   Provincia: {row["con_provincia"]}/{total} ({100*row["con_provincia"]/total:.1f}%)')
    print(f'   Localidad: {row["con_localidad"]}/{total} ({100*row["con_localidad"]/total:.1f}%)')

    # Top provincias
    print('   Top provincias:')
    cur = conn.execute('''
        SELECT provincia, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE provincia IS NOT NULL AND provincia != ''
        GROUP BY provincia
        ORDER BY cnt DESC
        LIMIT 5
    ''')
    for row in cur:
        print(f'      - {row["provincia"]}: {row["cnt"]}')
    print()

    # 3. Sector empresa
    print('3. SECTOR EMPRESA:')
    cur = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN sector_empresa IS NOT NULL AND sector_empresa != '' THEN 1 ELSE 0 END) as con_sector
        FROM ofertas_nlp
    ''')
    row = cur.fetchone()
    total = row["total"]
    print(f'   Con sector: {row["con_sector"]}/{total} ({100*row["con_sector"]/total:.1f}%)')

    # Top sectores
    print('   Top sectores:')
    cur = conn.execute('''
        SELECT sector_empresa, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE sector_empresa IS NOT NULL AND sector_empresa != ''
        GROUP BY sector_empresa
        ORDER BY cnt DESC
        LIMIT 8
    ''')
    for row in cur:
        print(f'      - {row["sector_empresa"]}: {row["cnt"]}')
    print()

    # 4. Skills (solo v11)
    print('4. SKILLS (ofertas v11):')
    cur = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN skills_tecnicas_list IS NOT NULL AND skills_tecnicas_list != '[]' AND skills_tecnicas_list != '' THEN 1 ELSE 0 END) as con_skills_tec,
            SUM(CASE WHEN soft_skills_list IS NOT NULL AND soft_skills_list != '[]' AND soft_skills_list != '' THEN 1 ELSE 0 END) as con_soft_skills,
            SUM(CASE WHEN tecnologias_list IS NOT NULL AND tecnologias_list != '[]' AND tecnologias_list != '' THEN 1 ELSE 0 END) as con_tech
        FROM ofertas_nlp
        WHERE nlp_version = '11.0.0'
    ''')
    row = cur.fetchone()
    total = row['total']
    if total > 0:
        print(f'   Skills tecnicas: {row["con_skills_tec"]}/{total} ({100*row["con_skills_tec"]/total:.1f}%)')
        print(f'   Soft skills: {row["con_soft_skills"]}/{total} ({100*row["con_soft_skills"]/total:.1f}%)')
        print(f'   Tecnologias: {row["con_tech"]}/{total} ({100*row["con_tech"]/total:.1f}%)')
    print()

    # 5. Educacion
    print('5. NIVEL EDUCATIVO:')
    cur = conn.execute('''
        SELECT nivel_educativo, COUNT(*) as cnt
        FROM ofertas_nlp
        GROUP BY nivel_educativo
        ORDER BY cnt DESC
    ''')
    for row in cur:
        nivel = row['nivel_educativo'] if row['nivel_educativo'] else 'NULL'
        print(f'   - {nivel}: {row["cnt"]}')
    print()

    # 6. Experiencia
    print('6. EXPERIENCIA:')
    cur = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) as con_exp_min,
            AVG(CASE WHEN experiencia_min_anios IS NOT NULL THEN experiencia_min_anios END) as avg_exp_min,
            MAX(experiencia_min_anios) as max_exp_min
        FROM ofertas_nlp
    ''')
    row = cur.fetchone()
    print(f'   Con experiencia minima: {row["con_exp_min"]}/{row["total"]}')
    if row['avg_exp_min']:
        print(f'   Promedio exp. minima: {row["avg_exp_min"]:.1f} anios')
    if row['max_exp_min']:
        print(f'   Maximo exp. minima: {row["max_exp_min"]} anios')
    print()

    # 7. Campos categoricos (solo v11)
    print('7. CAMPOS CATEGORICOS (v11):')
    cur = conn.execute('''
        SELECT requerimiento_edad, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE nlp_version = '11.0.0'
        GROUP BY requerimiento_edad
        ORDER BY requerimiento_edad
    ''')
    print('   Requerimiento edad:')
    EDAD_LABELS = {0: 'Sin requisito', 1: '18-25', 2: '25-35', 3: '35-45', 4: '45+', 5: 'Ambiguo', None: 'NULL'}
    for row in cur:
        label = EDAD_LABELS.get(row['requerimiento_edad'], str(row['requerimiento_edad']))
        print(f'      {row["requerimiento_edad"]} ({label}): {row["cnt"]}')

    cur = conn.execute('''
        SELECT requerimiento_sexo, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE nlp_version = '11.0.0'
        GROUP BY requerimiento_sexo
        ORDER BY requerimiento_sexo
    ''')
    print('   Requerimiento sexo:')
    SEXO_LABELS = {0: 'Sin requisito', 1: 'Masculino', 2: 'Femenino', None: 'NULL'}
    for row in cur:
        label = SEXO_LABELS.get(row['requerimiento_sexo'], str(row['requerimiento_sexo']))
        print(f'      {row["requerimiento_sexo"]} ({label}): {row["cnt"]}')
    print()

    # 8. Titulo ocupacion
    print('8. TITULO OCUPACION (muestras v11):')
    cur = conn.execute('''
        SELECT titulo_ocupacion, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE nlp_version = '11.0.0' AND titulo_ocupacion IS NOT NULL
        GROUP BY titulo_ocupacion
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    for row in cur:
        print(f'   - {row["titulo_ocupacion"]}: {row["cnt"]}')
    print()

    # 9. Casos para revisar (potenciales errores)
    print('9. CASOS A REVISAR (potenciales errores):')

    # Ofertas sin provincia
    cur = conn.execute('''
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE nlp_version = '11.0.0' AND (provincia IS NULL OR provincia = '')
    ''')
    sin_prov = cur.fetchone()[0]
    print(f'   Sin provincia: {sin_prov}')

    # Ofertas sin skills tecnicas
    cur = conn.execute('''
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE nlp_version = '11.0.0' AND (skills_tecnicas_list IS NULL OR skills_tecnicas_list = '[]')
    ''')
    sin_skills = cur.fetchone()[0]
    print(f'   Sin skills tecnicas: {sin_skills}')

    # Ofertas con experiencia > 10
    cur = conn.execute('''
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE experiencia_min_anios > 10
    ''')
    exp_alta = cur.fetchone()[0]
    print(f'   Experiencia > 10 anios (revisar): {exp_alta}')

    print()
    print('=' * 50)

    # 10. Muestra detallada de 5 ofertas v11
    print('10. MUESTRA DETALLADA (5 ofertas v11):')
    print()
    cur = conn.execute('''
        SELECT id_oferta, titulo_ocupacion, provincia, localidad, sector_empresa,
               skills_tecnicas_list, soft_skills_list, tecnologias_list,
               experiencia_min_anios, nivel_educativo, requerimiento_edad, requerimiento_sexo
        FROM ofertas_nlp
        WHERE nlp_version = '11.0.0'
        ORDER BY RANDOM()
        LIMIT 5
    ''')
    for i, row in enumerate(cur, 1):
        print(f'--- Oferta {i} (ID: {row["id_oferta"]}) ---')
        print(f'   Titulo: {row["titulo_ocupacion"]}')
        print(f'   Ubicacion: {row["localidad"]}, {row["provincia"]}')
        print(f'   Sector: {row["sector_empresa"]}')
        print(f'   Skills tec: {row["skills_tecnicas_list"]}')
        print(f'   Soft skills: {row["soft_skills_list"]}')
        print(f'   Tecnologias: {row["tecnologias_list"]}')
        print(f'   Experiencia: {row["experiencia_min_anios"]} anios')
        print(f'   Educacion: {row["nivel_educativo"]}')
        print(f'   Req. edad: {row["requerimiento_edad"]}, Req. sexo: {row["requerimiento_sexo"]}')
        print()

    conn.close()

if __name__ == '__main__':
    main()
