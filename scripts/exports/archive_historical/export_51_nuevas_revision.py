# -*- coding: utf-8 -*-
"""
Exporta las 51 ofertas NUEVAS del Gold Set expandido para revisión manual.
"""
import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"
GOLD_SET_100_PATH = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
OUTPUT_DIR = BASE_DIR / "exports"

# Cargar IDs originales (49)
with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
    gold_set_orig = json.load(f)
ids_originales = set(str(item['id_oferta']) for item in gold_set_orig)
print(f"IDs originales (Gold Set v2): {len(ids_originales)}")

# Cargar IDs totales (100)
with open(GOLD_SET_100_PATH, 'r', encoding='utf-8') as f:
    ids_total = json.load(f)
print(f"IDs totales (Gold Set 100): {len(ids_total)}")

# Calcular IDs nuevos
ids_nuevos = [id for id in ids_total if str(id) not in ids_originales]
print(f"IDs NUEVOS para revisión: {len(ids_nuevos)}")

# Conectar BD
conn = sqlite3.connect(str(DB_PATH))

# Query para obtener datos completos
placeholders = ','.join(['?' for _ in ids_nuevos])
query = f"""
    SELECT
        n.id_oferta,
        o.titulo as titulo_original,
        n.titulo_limpio,
        o.empresa,
        o.localizacion as ubicacion_scraping,
        n.provincia,
        n.localidad,
        n.modalidad,
        n.nivel_seniority,
        n.area_funcional,
        n.sector_empresa,
        n.experiencia_min_anios,
        n.experiencia_max_anios,
        n.nivel_educativo,
        n.skills_tecnicas_list,
        n.soft_skills_list,
        n.tareas_explicitas,
        substr(o.descripcion, 1, 800) as descripcion_preview
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
    ORDER BY n.id_oferta
"""

df = pd.read_sql_query(query, conn, params=ids_nuevos)
conn.close()

print(f"\nRegistros obtenidos: {len(df)}")

# Agregar columnas para validación manual
df['NLP_OK'] = ''  # Para marcar si NLP es correcto
df['Comentario'] = ''  # Para notas del revisor

# Reordenar columnas
cols_orden = [
    'id_oferta', 'titulo_original', 'titulo_limpio', 'empresa',
    'ubicacion_scraping', 'provincia', 'localidad', 'modalidad',
    'nivel_seniority', 'area_funcional', 'sector_empresa',
    'experiencia_min_anios', 'experiencia_max_anios', 'nivel_educativo',
    'skills_tecnicas_list', 'soft_skills_list', 'tareas_explicitas',
    'NLP_OK', 'Comentario', 'descripcion_preview'
]
df = df[cols_orden]

# Exportar
OUTPUT_DIR.mkdir(exist_ok=True)
output_file = OUTPUT_DIR / f"51_ofertas_nuevas_revision_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Ofertas_Nuevas', index=False)

    # Hoja de resumen
    resumen = []
    campos = ['provincia', 'localidad', 'modalidad', 'nivel_seniority',
              'area_funcional', 'tareas_explicitas', 'skills_tecnicas_list']
    for campo in campos:
        no_null = df[campo].notna() & (df[campo] != '')
        pct = no_null.sum() / len(df) * 100
        resumen.append({'Campo': campo, 'Completado': f"{pct:.0f}%", 'Count': no_null.sum()})

    df_resumen = pd.DataFrame(resumen)
    df_resumen.to_excel(writer, sheet_name='Cobertura', index=False)

print(f"\n{'='*60}")
print(f"EXCEL GENERADO: {output_file}")
print(f"{'='*60}")
print(f"\nCOBERTURA DE CAMPOS:")
for campo in ['provincia', 'localidad', 'modalidad', 'nivel_seniority',
              'area_funcional', 'tareas_explicitas', 'skills_tecnicas_list']:
    no_null = df[campo].notna() & (df[campo] != '')
    pct = no_null.sum() / len(df) * 100
    print(f"  {campo}: {pct:.0f}% ({no_null.sum()}/{len(df)})")

print(f"\n¡Listo! Revisar columnas NLP_OK y Comentario en el Excel.")
