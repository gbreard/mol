# -*- coding: utf-8 -*-
"""
Revision manual de NLP v10.0.0
==============================
Extrae datos para validacion humana.
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent.parent.parent.parent / "database" / "gold_set_nlp_100_ids.json"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Cargar Gold Set IDs
if GOLD_SET_PATH.exists():
    with open(GOLD_SET_PATH) as f:
        gold_ids = json.load(f)
    print(f"Gold Set IDs cargados: {len(gold_ids)}")
else:
    gold_ids = []
    print("No se encontro gold_set_nlp_100_ids.json")

# Obtener registros NLP v10
c.execute("""
    SELECT n.*, o.titulo, o.empresa, o.descripcion
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.nlp_version = '10.0.0'
    ORDER BY n.id_oferta
""")
rows = c.fetchall()

print(f"\nTotal registros NLP v10.0.0: {len(rows)}")
print("=" * 80)

# Mostrar resumen de cada registro
for i, row in enumerate(rows[:20], 1):  # Primeros 20
    id_oferta = row['id_oferta']
    in_gold = "[GOLD]" if id_oferta in gold_ids else ""

    print(f"\n[{i}] ID: {id_oferta} {in_gold}")
    titulo = row['titulo'] or ''
    print(f"    Titulo original: {titulo[:60]}..." if len(titulo) > 60 else f"    Titulo original: {titulo}")
    print(f"    Titulo limpio: {row['titulo_limpio']}")
    print(f"    Empresa: {row['empresa']}")
    print(f"    Ubicacion: {row['provincia']} / {row['localidad']}")
    print(f"    Modalidad: {row['modalidad']} | Jornada: {row['jornada_laboral']}")
    print(f"    Seniority: {row['nivel_seniority']} | Area: {row['area_funcional']}")
    print(f"    Experiencia: {row['experiencia_min_anios']}-{row['experiencia_max_anios']} anios")
    print(f"    Educacion: {row['nivel_educativo']} | Carrera: {row['carrera_especifica']}")

    # Skills
    skills_tec = row['skills_tecnicas_list']
    if skills_tec:
        try:
            skills_list = json.loads(skills_tec) if skills_tec.startswith('[') else skills_tec.split(',')
            print(f"    Skills tecnicas ({len(skills_list)}): {', '.join(str(s) for s in skills_list[:5])}{'...' if len(skills_list) > 5 else ''}")
        except:
            print(f"    Skills tecnicas: {str(skills_tec)[:50]}...")

    soft = row['soft_skills_list']
    if soft:
        try:
            soft_list = json.loads(soft) if soft.startswith('[') else soft.split(',')
            print(f"    Soft skills ({len(soft_list)}): {', '.join(str(s) for s in soft_list[:5])}{'...' if len(soft_list) > 5 else ''}")
        except:
            print(f"    Soft skills: {str(soft)[:50]}...")

    # Tareas
    tareas = row['tareas_explicitas']
    if tareas:
        try:
            tareas_list = json.loads(tareas) if tareas.startswith('[') else [tareas]
            print(f"    Tareas ({len(tareas_list)}): {tareas_list[0][:50]}..." if tareas_list else "")
        except:
            print(f"    Tareas: {str(tareas)[:50]}...")

print("\n" + "=" * 80)
print(f"\nMostrando 20 de {len(rows)} registros.")

# Estadisticas de campos
print("\n" + "=" * 80)
print("ESTADISTICAS DE COMPLETITUD")
print("=" * 80)

campos_check = [
    'titulo_limpio', 'provincia', 'localidad', 'modalidad',
    'nivel_seniority', 'area_funcional', 'experiencia_min_anios',
    'nivel_educativo', 'skills_tecnicas_list', 'soft_skills_list',
    'tareas_explicitas', 'beneficios_list'
]

for campo in campos_check:
    try:
        c.execute(f"""
            SELECT COUNT(*) FROM ofertas_nlp
            WHERE nlp_version = '10.0.0' AND {campo} IS NOT NULL AND {campo} != '' AND {campo} != '[]'
        """)
        filled = c.fetchone()[0]
        pct = (filled / len(rows) * 100) if rows else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {campo:25} {bar} {filled:3}/{len(rows)} ({pct:.0f}%)")
    except Exception as e:
        print(f"  {campo:25} ERROR: {e}")

conn.close()
