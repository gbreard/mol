# -*- coding: utf-8 -*-
"""Verificar resultados Gold Set 100 post-reprocesamiento."""
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
db_path = BASE_DIR / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# Cargar IDs
with open(BASE_DIR / "database" / "gold_set_nlp_100_ids.json") as f:
    ids = json.load(f)

placeholders = ','.join(['?'] * len(ids))

print("=" * 60)
print("VERIFICACION GOLD SET 100 - POST GAPS")
print("=" * 60)

# 1. Versiones
cur = conn.execute(f'''
    SELECT nlp_version, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    GROUP BY nlp_version
''', ids)
print("\n1. VERSIONES NLP:")
for row in cur:
    print(f"   {row['nlp_version']}: {row['cnt']} ofertas")

# 2. Provincias
cur = conn.execute(f'''
    SELECT provincia, COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    GROUP BY provincia
    ORDER BY cnt DESC
''', ids)
print("\n2. DISTRIBUCION PROVINCIAS:")
for row in cur:
    print(f"   {row['provincia']}: {row['cnt']}")

# 3. Verificar CABA especificamente
cur = conn.execute(f'''
    SELECT COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders}) AND provincia = 'CABA'
''', ids)
caba_count = cur.fetchone()['cnt']
print(f"\n3. OFERTAS EN CABA: {caba_count}")

# 4. Verificar localidades con sufijos sucios
cur = conn.execute(f'''
    SELECT COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    AND (localidad LIKE '%, CABA' OR localidad LIKE '%, Capital Federal' OR localidad LIKE '% CABA')
''', ids)
sufijos_sucios = cur.fetchone()['cnt']
print(f"\n4. LOCALIDADES CON SUFIJOS SUCIOS: {sufijos_sucios} (debe ser 0)")

# 5. Ejemplos CABA
cur = conn.execute(f'''
    SELECT id_oferta, provincia, localidad, titulo_limpio
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders}) AND provincia = 'CABA'
    LIMIT 10
''', ids)
print("\n5. EJEMPLOS PROVINCIA=CABA:")
for row in cur:
    print(f"   ID {row['id_oferta']}: loc={row['localidad']}, titulo={row['titulo_limpio'][:40]}...")

# 6. Verificar que no hay "Capital Federal" como provincia
cur = conn.execute(f'''
    SELECT COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders}) AND provincia = 'Capital Federal'
''', ids)
cf_count = cur.fetchone()['cnt']
print(f"\n6. OFERTAS CON provincia='Capital Federal': {cf_count} (debe ser 0)")

# 7. Verificar min/max coherentes
cur = conn.execute(f'''
    SELECT COUNT(*) as cnt
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    AND experiencia_min_anios IS NOT NULL
    AND experiencia_max_anios IS NOT NULL
    AND experiencia_min_anios > experiencia_max_anios
''', ids)
exp_incoherente = cur.fetchone()['cnt']
print(f"\n7. OFERTAS CON exp_min > exp_max: {exp_incoherente} (debe ser 0)")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
all_ok = (sufijos_sucios == 0 and cf_count == 0 and exp_incoherente == 0)
print(f"   Todas las validaciones OK: {'SI' if all_ok else 'NO'}")

conn.close()
