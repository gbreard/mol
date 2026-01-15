# -*- coding: utf-8 -*-
"""
Exportar 200 ofertas NLP a Excel
"""
import sqlite3
import pandas as pd
from datetime import datetime

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
conn = sqlite3.connect(db_path)

# Query con campos principales + originales de ofertas
query = '''
SELECT
    n.id_oferta,
    n.nlp_version,
    o.fecha_publicacion_datetime as fecha_publicacion,
    o.titulo as titulo_original,
    n.titulo_limpio,
    o.descripcion as descripcion_original,
    n.provincia,
    n.localidad,
    n.sector_empresa,
    n.area_funcional,
    n.nivel_seniority,
    n.skills_tecnicas_list,
    n.soft_skills_list,
    n.tecnologias_list,
    n.herramientas_list,
    n.experiencia_min_anios,
    n.experiencia_max_anios,
    n.nivel_educativo,
    n.titulo_requerido,
    n.requerimiento_edad,
    n.requerimiento_sexo,
    n.tareas_explicitas,
    n.modalidad,
    n.jornada_laboral,
    n.salario_min,
    n.salario_max,
    n.moneda,
    n.nlp_extraction_timestamp
FROM ofertas_nlp n
LEFT JOIN ofertas o ON n.id_oferta = o.id_oferta
ORDER BY n.nlp_version DESC, o.fecha_publicacion_datetime DESC
'''

df = pd.read_sql_query(query, conn)
conn.close()

# Mapear valores categoricos
edad_map = {0: 'Sin requisito', 1: '18-25', 2: '25-35', 3: '35-45', 4: '45+', 5: 'Ambiguo'}
sexo_map = {0: 'Sin requisito', 1: 'Masculino', 2: 'Femenino'}

df['requerimiento_edad_texto'] = df['requerimiento_edad'].map(edad_map)
df['requerimiento_sexo_texto'] = df['requerimiento_sexo'].map(sexo_map)

# Reordenar columnas
cols_order = [
    'id_oferta', 'nlp_version', 'fecha_publicacion',
    'titulo_original', 'titulo_limpio',
    'descripcion_original',
    'provincia', 'localidad', 'sector_empresa',
    'area_funcional', 'nivel_seniority',
    'skills_tecnicas_list', 'soft_skills_list', 'tecnologias_list', 'herramientas_list',
    'experiencia_min_anios', 'experiencia_max_anios',
    'nivel_educativo', 'titulo_requerido',
    'requerimiento_edad', 'requerimiento_edad_texto',
    'requerimiento_sexo', 'requerimiento_sexo_texto',
    'tareas_explicitas',
    'modalidad', 'jornada_laboral',
    'salario_min', 'salario_max', 'moneda',
    'nlp_extraction_timestamp'
]

df = df[cols_order]

# Exportar
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = f'D:\\OEDE\\Webscrapping\\exports\\NLP_200_ofertas_{timestamp}.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='NLP_200', index=False)

    # Ajustar anchos de columna
    worksheet = writer.sheets['NLP_200']
    for i, col in enumerate(df.columns):
        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        max_len = min(max_len, 50)  # Limitar ancho maximo
        worksheet.column_dimensions[chr(65 + i) if i < 26 else 'A' + chr(65 + i - 26)].width = max_len

print(f'Exportado: {output_path}')
print(f'Total registros: {len(df)}')
print(f'  - v10.0.0: {len(df[df["nlp_version"] == "10.0.0"])}')
print(f'  - v11.0.0: {len(df[df["nlp_version"] == "11.0.0"])}')
