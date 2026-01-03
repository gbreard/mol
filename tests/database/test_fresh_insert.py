"""
Test inserción con IDs completamente nuevos
"""

import pandas as pd
import logging
from database.db_manager import DatabaseManager
from database.config import DB_CONFIG

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Cargar CSV
df = pd.read_csv('01_sources/bumeran/data/raw/bumeran_completo_20251030_223956.csv')
print(f"CSV cargado: {len(df):,} ofertas\n")

# Conectar y ver qu IDs existen
db = DatabaseManager(**DB_CONFIG)
db.connect()

# Ver IDs existentes
import sqlite3
cursor = db.cursor
cursor.execute("SELECT id_oferta FROM ofertas ORDER BY id_oferta")
existing_ids = set(row[0] for row in cursor.fetchall())
print(f"IDs existentes en DB: {len(existing_ids)}")
print(f"Primeros 10: {sorted(list(existing_ids))[:10]}\n")

# Filtrar solo ofertas con IDs que NO existen en DB
df_new = df[~df['id_oferta'].isin(existing_ids)].head(10).copy()
print(f"Usando {len(df_new)} ofertas con IDs completamente nuevos:")
print(f"IDs a insertar: {df_new['id_oferta'].tolist()}\n")

# Contar antes
count_before = db.get_ofertas_count()
print(f"Count antes: {count_before}\n")

# Insertar
print("Insertando...")
inserted = db.insert_ofertas(df_new)
print(f"Retorno: {inserted}\n")

# Contar después
count_after = db.get_ofertas_count()
print(f"Count después: {count_after}")
print(f"Diferencia: {count_after - count_before}")

if count_after == count_before + len(df_new):
    print("\n[OK] Inserción funcionó correctamente!")
else:
    print(f"\n[ERROR] Se esperaban {count_before + len(df_new)} pero hay {count_after}")

db.disconnect()
