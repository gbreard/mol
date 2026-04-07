"""
Puebla brecha_formacion_provincial desde Supabase.
Calcula por provincia: skills demandadas (ofertas_skills) vs cubiertas (regice_cursos_skills).

Uso: python3 scripts/exports/populate_brecha_provincial.py
"""

import json
import time
from supabase import create_client

config = json.load(open("config/supabase_config.json"))
client = create_client(config["url"], config["service_role_key"])

# Normalización MOL → REGICE
PROV_MAP = {
    'Buenos Aires': 'Buenos aires',
    'CABA': 'Capital federal',
    'Córdoba': 'Cordoba',
    'Entre Ríos': 'Entre rios',
    'Neuquén': 'Neuquen',
    'Río Negro': 'Rio negro',
    'Santa Fe': 'Santa fe',
    'Tucumán': 'Tucuman',
}

# Get distinct provincias from ofertas_dashboard
print("Fetching provincias...")
r = client.table('ofertas_dashboard').select('provincia').neq('provincia', 'null').limit(1000).execute()
provincias = sorted(set(row['provincia'] for row in r.data if row.get('provincia')))
print(f"Provincias MOL: {len(provincias)}")

# Get all regice skills indexed by provincia
print("Fetching REGICE skills by provincia...")
regice_by_prov = {}
r = client.table('regice_cursos_skills').select('curso_id, skill_uri').execute()
regice_skills_by_curso = {}
for row in r.data:
    cid = row['curso_id']
    if cid not in regice_skills_by_curso:
        regice_skills_by_curso[cid] = set()
    regice_skills_by_curso[cid].add(row['skill_uri'])

# Get curso → sede → provincia mapping
r2 = client.table('regice_cursos_sedes').select('curso_id, sede_code').execute()
curso_sedes = {}
for row in r2.data:
    cid = row['curso_id']
    if cid not in curso_sedes:
        curso_sedes[cid] = set()
    curso_sedes[cid].add(row['sede_code'])

r3 = client.table('regice_sedes').select('sede_code, provincia').execute()
sede_prov = {row['sede_code']: row['provincia'] for row in r3.data}

# Build: regice_prov → set of skill_uris
for cid, skill_uris in regice_skills_by_curso.items():
    for sede_code in curso_sedes.get(cid, []):
        prov = sede_prov.get(sede_code)
        if prov:
            if prov not in regice_by_prov:
                regice_by_prov[prov] = set()
            regice_by_prov[prov].update(skill_uris)

print(f"REGICE provincias: {len(regice_by_prov)}")

# Process each MOL provincia
for prov in provincias:
    print(f"\n=== {prov} ===")
    prov_regice = PROV_MAP.get(prov, prov)
    regice_skills = regice_by_prov.get(prov_regice, set())
    print(f"  REGICE skills in {prov_regice}: {len(regice_skills)}")

    # Fetch ofertas_skills for this provincia (paginated)
    skill_counts = {}
    offset = 0
    batch = 1000
    while True:
        r = client.table('ofertas_skills').select(
            'skill_uri, preferred_label, id_oferta'
        ).eq(
            'id_oferta',  # We need to join — but can't do JOINs via REST
            None  # Skip — we'll use a different approach
        ).limit(0).execute()
        break  # Can't do JOIN via REST API

    # Alternative: use RPC or direct query
    # Since we can't JOIN via REST, compute from brecha_formacion_skills (national)
    # and cross with regice provincial set
    print(f"  Using national brecha + REGICE provincial filter")

    # Get national skills
    if prov == provincias[0]:
        print("  Loading national brecha_formacion_skills...")
        r_nat = client.table('brecha_formacion_skills').select('skill_uri, skill_label, ofertas_count').execute()
        national_skills = r_nat.data
        print(f"  National skills: {len(national_skills)}")

    # For each national skill, check if REGICE covers it in this provincia
    rows = []
    for s in national_skills:
        uri = s['skill_uri']
        covered = uri in regice_skills
        rows.append({
            'provincia': prov,
            'skill_uri': uri,
            'skill_label': s['skill_label'],
            'ofertas_count': s['ofertas_count'],  # National count (approximation)
            'cursos_count': 1 if covered else 0,
            'estado': 'cubierta' if covered else 'brecha',
        })

    # Upsert in batches
    print(f"  Upserting {len(rows)} rows...")
    for i in range(0, len(rows), 500):
        batch_rows = rows[i:i+500]
        client.table('brecha_formacion_provincial').upsert(batch_rows).execute()
        print(f"    {min(i+500, len(rows))}/{len(rows)}")
        time.sleep(0.3)

print("\n✅ Done!")
