# -*- coding: utf-8 -*-
"""
Expandir Gold Set NLP de 49 a 100 ofertas
==========================================
Selecciona 51 ofertas adicionales representativas y genera Excel.
"""
import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).parent.parent.parent.parent  # Subir a raíz del proyecto
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"
OUTPUT_DIR = BASE_DIR / "exports"

# Cargar Gold Set actual (49)
with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
ids_actuales = set(str(item['id_oferta']) for item in gold_set)
print(f"Gold Set actual: {len(ids_actuales)} ofertas")

# Conectar BD
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Seleccionar 51 ofertas adicionales con criterios de variedad
# Incluir ofertas con NLP parcial (al menos titulo_limpio o descripcion)
query = """
    SELECT
        n.id_oferta,
        o.titulo,
        n.area_funcional,
        n.provincia,
        n.modalidad,
        n.nivel_seniority
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE o.descripcion IS NOT NULL
    AND LENGTH(o.descripcion) > 200
    AND n.id_oferta NOT IN ({})
    ORDER BY
        CASE WHEN n.provincia IS NOT NULL THEN 0 ELSE 1 END,
        CASE WHEN n.modalidad IS NOT NULL THEN 0 ELSE 1 END,
        RANDOM()
""".format(','.join(['?' for _ in ids_actuales]))

cursor.execute(query, list(ids_actuales))
candidatos = cursor.fetchall()
print(f"Candidatos disponibles: {len(candidatos)}")

# Seleccionar 51 con variedad de áreas
seleccionados = []
areas_count = {}

for row in candidatos:
    id_oferta, titulo, area, provincia, modalidad, seniority = row
    area = area or "Sin area"

    # Limitar por área para variedad (max 15 por área, sin limite para "Sin area")
    max_por_area = 20 if area == "Sin area" else 10
    if areas_count.get(area, 0) < max_por_area:
        seleccionados.append({
            'id_oferta': str(id_oferta),
            'titulo': titulo,
            'area_funcional': area,
            'provincia': provincia,
            'modalidad': modalidad,
            'nivel_seniority': seniority
        })
        areas_count[area] = areas_count.get(area, 0) + 1

    if len(seleccionados) >= 51:
        break

print(f"\nSeleccionados: {len(seleccionados)} ofertas adicionales")
print(f"Distribución por área: {areas_count}")

# IDs totales (49 + 51 = 100)
ids_nuevos = [s['id_oferta'] for s in seleccionados]
ids_total = list(ids_actuales) + ids_nuevos
print(f"\nTotal Gold Set expandido: {len(ids_total)} ofertas")

# Generar Excel con las 100 ofertas
placeholders = ','.join(['?' for _ in ids_total])
placeholders_orig = ','.join([f"'{i}'" for i in ids_actuales])

query_export = f"""
    SELECT
        n.id_oferta,
        o.titulo as titulo_original,
        n.titulo_limpio,
        o.localizacion as ubicacion_scraping,
        n.provincia,
        n.localidad,
        n.modalidad,
        n.nivel_seniority,
        n.area_funcional,
        n.experiencia_min_anios,
        n.experiencia_max_anios,
        n.tiene_gente_cargo,
        n.sector_empresa,
        n.nivel_educativo,
        n.titulo_requerido,
        n.requisito_edad_min,
        n.requisito_edad_max,
        n.requisito_sexo,
        n.skills_tecnicas_list,
        n.soft_skills_list,
        n.tecnologias_list,
        n.herramientas_list,
        n.tareas_explicitas,
        CASE WHEN n.id_oferta IN ({placeholders_orig}) THEN 'original' ELSE 'nuevo' END as origen_gold_set
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
    ORDER BY origen_gold_set, n.id_oferta
"""

df = pd.read_sql_query(query_export, conn, params=ids_total)
conn.close()

# Exportar
output_file = OUTPUT_DIR / f"NLP_Gold_Set_100_{datetime.now().strftime('%Y%m%d')}.xlsx"
df.to_excel(str(output_file), index=False, sheet_name='NLP_100_Ofertas')

print(f"\n{'='*60}")
print(f"Excel generado: {output_file}")
print(f"Total registros: {len(df)}")
print(f"Columnas: {len(df.columns)}")

# Estadísticas de cobertura
print(f"\n{'='*60}")
print("COBERTURA DE CAMPOS:")
campos_clave = ['provincia', 'localidad', 'modalidad', 'nivel_seniority',
                'area_funcional', 'experiencia_min_anios', 'titulo_limpio',
                'skills_tecnicas_list', 'sector_empresa', 'nivel_educativo']
for campo in campos_clave:
    if campo in df.columns:
        vacios = df[campo].isna().sum() + (df[campo] == '').sum()
        pct = (len(df) - vacios) / len(df) * 100
        print(f"  {campo}: {pct:.0f}%")
