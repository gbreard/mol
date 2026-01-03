# -*- coding: utf-8 -*-
"""Exportar solo campos NLP del Gold Set"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(exist_ok=True)

# Cargar Gold Set IDs (usar el expandido de 100 si existe)
GOLD_SET_100_PATH = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"

if GOLD_SET_100_PATH.exists():
    with open(GOLD_SET_100_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)
    print(f"Usando Gold Set expandido: {len(ids)} ofertas")
else:
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    ids = [str(item['id_oferta']) for item in gold_set]
    print(f"Usando Gold Set original: {len(ids)} ofertas")

# Conectar BD
conn = sqlite3.connect(str(DB_PATH))
placeholders = ','.join(['?' for _ in ids])

# Query solo campos NLP
query = f"""
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
        n.skills_tecnicas_list,
        n.soft_skills_list,
        n.tareas_explicitas
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
    ORDER BY n.id_oferta
"""

df = pd.read_sql_query(query, conn, params=ids)
conn.close()

# Exportar
output_file = OUTPUT_DIR / f"NLP_Gold_Set_{datetime.now().strftime('%Y%m%d')}.xlsx"
df.to_excel(str(output_file), index=False, sheet_name='NLP_Campos')

print(f"Excel generado: {output_file}")
print(f"Registros: {len(df)}")
print(f"Columnas: {list(df.columns)}")
