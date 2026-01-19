#!/usr/bin/env python3
"""
Script para modificar dashboard_scraping_v4.py
Agrega la pestaña de Calidad de Parseo NLP
"""

# Leer el archivo
with open('dashboard_scraping_v4.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar donde insertar la función (después de cargar_metricas_scraping)
insert_func_at = None
for i, line in enumerate(lines):
    if 'def cargar_metricas_scraping():' in line:
        # Buscar el final de esta función (siguiente def o línea que no está indentada)
        for j in range(i+1, len(lines)):
            if lines[j].startswith('def ') or (lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('#')):
                insert_func_at = j
                break
        break

# Función a insertar
nueva_funcion = '''
def cargar_calidad_parseo():
    """Calcula calidad de parseo NLP"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        o.id_oferta,
        o.titulo,
        SUBSTR(o.descripcion, 1, 200) as desc_preview,
        LENGTH(o.descripcion) as desc_length,
        DATE(o.scrapeado_en) as fecha_scraping,
        -- Score: suma de campos parseados (0-7)
        (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
         CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
         CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) as score_calidad,
        -- Desglose individual
        CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END as tiene_exp,
        CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END as tiene_edu,
        CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END as tiene_soft,
        CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END as tiene_tec,
        CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END as tiene_idioma,
        CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END as tiene_salario,
        CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END as tiene_jornada
    FROM ofertas o
    LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
    WHERE o.descripcion IS NOT NULL
    ORDER BY o.scrapeado_en DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convertir fecha
    df['fecha_scraping'] = pd.to_datetime(df['fecha_scraping'])

    # Calcular rangos de longitud
    df['rango_longitud'] = pd.cut(
        df['desc_length'],
        bins=[0, 500, 1000, 2000, 5000, 999999],
        labels=['Muy corta (0-500)', 'Corta (500-1K)', 'Media (1-2K)', 'Larga (2-5K)', 'Muy larga (5K+)']
    )

    return df

'''

# Insertar la función
if insert_func_at:
    lines.insert(insert_func_at, nueva_funcion)
    print(f'[OK] Funcion cargar_calidad_parseo() insertada en linea {insert_func_at}')

# Buscar y agregar el tab (buscar dcc.Tab(label='🗂️ Explorador de Tablas'...)
for i, line in enumerate(lines):
    if "dcc.Tab(label='🗂️ Explorador de Tablas'" in line:
        # Insertar ANTES de esta línea
        lines.insert(i, "                dcc.Tab(label='🧠 Calidad Parseo NLP', value='tab-parseo-nlp'),\n")
        print(f'[OK] Tab agregado en linea {i}')
        break

# Cambiar puerto 8051 a 8052
for i, line in enumerate(lines):
    if '8051' in line:
        lines[i] = line.replace('8051', '8052')
        print(f'[OK] Puerto cambiado a 8052 en linea {i}')

# Guardar
with open('dashboard_scraping_v4.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('\n[COMPLETADO] Modificaciones completadas en dashboard_scraping_v4.py')
print('[ATENCION] Aun falta agregar el contenido del tab tab-parseo-nlp en la seccion de callbacks')
