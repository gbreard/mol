"""
Test inserción de ofertas con logging detallado
"""

import pandas as pd
import logging
from database.db_manager import DatabaseManager
from database.config import DB_CONFIG

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Cargar CSV
csv_path = '01_sources/bumeran/data/raw/bumeran_completo_20251030_223956.csv'
print(f"Cargando CSV: {csv_path}")
df = pd.read_csv(csv_path)
print(f"CSV cargado: {len(df):,} ofertas")
print(f"Columnas en CSV: {list(df.columns)}")
print()

# Tomar solo 50 ofertas para test
df_test = df.head(50).copy()
print(f"Usando {len(df_test)} ofertas para test")
print()

# Conectar a DB
print("Conectando a database...")
db = DatabaseManager(**DB_CONFIG)
db.connect()

# Contar ofertas antes
count_before = db.get_ofertas_count()
print(f"Ofertas antes de inserción: {count_before:,}")
print()

# Insertar
print("Insertando ofertas...")
try:
    inserted = db.insert_ofertas(df_test)
    print(f"Retorno de insert_ofertas(): {inserted}")
except Exception as e:
    print(f"ERROR durante inserción: {e}")
    import traceback
    traceback.print_exc()

print()

# Contar ofertas después
count_after = db.get_ofertas_count()
print(f"Ofertas después de inserción: {count_after:,}")
print(f"Diferencia: {count_after - count_before}")

# Desconectar
db.disconnect()

print("\n[OK] Test completado")
