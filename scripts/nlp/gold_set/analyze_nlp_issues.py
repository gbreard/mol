# -*- coding: utf-8 -*-
"""
Analisis de problemas sistematicos en NLP v10.0.0
=================================================
"""
import sqlite3
import json
from pathlib import Path
from collections import Counter

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT n.*, o.titulo, o.empresa
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.nlp_version = '10.0.0'
""")
rows = c.fetchall()

print("=" * 70)
print("ANALISIS DE PROBLEMAS SISTEMATICOS - NLP v10.0.0")
print(f"Total registros: {len(rows)}")
print("=" * 70)

# 1. Skills con formato dict vs string
print("\n1. FORMATO DE SKILLS")
print("-" * 70)
skills_dict_format = 0
skills_clean_format = 0
for row in rows:
    skills = row['skills_tecnicas_list']
    if skills:
        if "{'valor'" in skills or '{"valor"' in skills:
            skills_dict_format += 1
        else:
            skills_clean_format += 1

print(f"   Con formato dict (necesita normalizar): {skills_dict_format}")
print(f"   Con formato limpio: {skills_clean_format}")

# 2. Localidad como array
print("\n2. LOCALIDAD COMO ARRAY")
print("-" * 70)
localidad_array = []
for row in rows:
    loc = row['localidad']
    if loc and loc.startswith('['):
        localidad_array.append((row['id_oferta'], loc))

print(f"   Registros con localidad como array: {len(localidad_array)}")
for id_oferta, loc in localidad_array[:5]:
    print(f"   - ID {id_oferta}: {loc[:50]}...")

# 3. Experiencia sospechosa
print("\n3. EXPERIENCIA SOSPECHOSA (>10 anios)")
print("-" * 70)
exp_alta = []
for row in rows:
    exp_min = row['experiencia_min_anios']
    if exp_min and exp_min > 10:
        exp_alta.append((row['id_oferta'], row['titulo'], exp_min))

print(f"   Registros con experiencia > 10 anios: {len(exp_alta)}")
for id_oferta, titulo, exp in exp_alta:
    print(f"   - ID {id_oferta}: {titulo[:40]}... -> {exp} anios")

# 4. Area funcional por titulo
print("\n4. AREAS FUNCIONALES ASIGNADAS")
print("-" * 70)
areas = Counter()
for row in rows:
    area = row['area_funcional']
    if area:
        areas[area] += 1

for area, count in areas.most_common(15):
    print(f"   {area}: {count}")

# 5. Seniority distribution
print("\n5. DISTRIBUCION DE SENIORITY")
print("-" * 70)
seniority = Counter()
for row in rows:
    sen = row['nivel_seniority']
    if sen:
        seniority[sen] += 1

for sen, count in seniority.most_common():
    print(f"   {sen}: {count}")

# 6. Carrera especifica sospechosa (texto largo)
print("\n6. CARRERA ESPECIFICA SOSPECHOSA")
print("-" * 70)
carrera_problemas = []
for row in rows:
    carrera = row['carrera_especifica']
    if carrera and len(carrera) > 50:
        carrera_problemas.append((row['id_oferta'], carrera[:80]))

print(f"   Registros con carrera > 50 chars: {len(carrera_problemas)}")
for id_oferta, carrera in carrera_problemas[:5]:
    print(f"   - ID {id_oferta}: {carrera}...")

# 7. Campos NULL en Gold Set
print("\n7. CAMPOS CLAVE VACIOS")
print("-" * 70)
campos_clave = ['titulo_limpio', 'provincia', 'modalidad', 'nivel_seniority',
                'area_funcional', 'skills_tecnicas_list']
for campo in campos_clave:
    c.execute(f"""
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE nlp_version = '10.0.0' AND ({campo} IS NULL OR {campo} = '')
    """)
    vacios = c.fetchone()[0]
    if vacios > 0:
        pct = vacios / len(rows) * 100
        print(f"   {campo}: {vacios} vacios ({pct:.1f}%)")

# 8. Modalidad distribucion
print("\n8. DISTRIBUCION DE MODALIDAD")
print("-" * 70)
modalidades = Counter()
for row in rows:
    mod = row['modalidad']
    modalidades[mod or 'NULL'] += 1

for mod, count in modalidades.most_common():
    print(f"   {mod}: {count}")

# 9. Nivel educativo
print("\n9. NIVEL EDUCATIVO")
print("-" * 70)
educacion = Counter()
for row in rows:
    edu = row['nivel_educativo']
    educacion[edu or 'NULL'] += 1

for edu, count in educacion.most_common():
    print(f"   {edu}: {count}")

# 10. Jornada laboral
print("\n10. JORNADA LABORAL")
print("-" * 70)
jornadas = Counter()
for row in rows:
    jor = row['jornada_laboral']
    jornadas[jor or 'NULL'] += 1

for jor, count in jornadas.most_common():
    print(f"   {jor}: {count}")

conn.close()
print("\n" + "=" * 70)
