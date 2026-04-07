"""
Puebla brecha_formacion_provincial con datos reales de MOL.
Para cada provincia: cuenta ofertas que piden cada skill, cruza con REGICE.

Uso: python3 scripts/exports/populate_brecha_provincial_v2.py
"""

import json
import time
from collections import defaultdict
from supabase import create_client

config = json.load(open("config/supabase_config.json"))
client = create_client(config["url"], config["service_role_key"])

PROV_MAP = {
    'Buenos Aires': 'Buenos aires', 'CABA': 'Capital federal',
    'Córdoba': 'Cordoba', 'Entre Ríos': 'Entre rios',
    'Neuquén': 'Neuquen', 'Río Negro': 'Rio negro',
    'Santa Fe': 'Santa fe', 'Tucumán': 'Tucuman',
}

BATCH = 1000

def fetch_all_paginated(table, select, filters=None):
    """Fetch all rows from a table with pagination."""
    all_rows = []
    offset = 0
    while True:
        q = client.table(table).select(select).range(offset, offset + BATCH - 1)
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        r = q.execute()
        all_rows.extend(r.data)
        if len(r.data) < BATCH:
            break
        offset += BATCH
    return all_rows

# 1. Build oferta → provincia map
print("Fetching ofertas_dashboard (id_oferta, provincia)...")
ofertas_prov = {}
offset = 0
while True:
    r = client.table('ofertas_dashboard').select('id_oferta, provincia').range(offset, offset + BATCH - 1).execute()
    for row in r.data:
        if row.get('provincia'):
            ofertas_prov[row['id_oferta']] = row['provincia']
    if len(r.data) < BATCH:
        break
    offset += BATCH
print(f"  {len(ofertas_prov)} ofertas con provincia")

# 2. Build skill → {provincia → set(id_oferta)} from ofertas_skills
print("Fetching ofertas_skills (skill_uri, preferred_label, id_oferta)...")
skill_prov_ofertas = defaultdict(lambda: defaultdict(set))
skill_labels = {}
offset = 0
fetched = 0
while True:
    r = client.table('ofertas_skills').select('skill_uri, preferred_label, id_oferta').range(offset, offset + BATCH - 1).execute()
    for row in r.data:
        uri = row.get('skill_uri')
        oferta = row.get('id_oferta')
        if uri and oferta and oferta in ofertas_prov:
            prov = ofertas_prov[oferta]
            skill_prov_ofertas[uri][prov].add(oferta)
            if uri not in skill_labels:
                skill_labels[uri] = row.get('preferred_label', '')
    fetched += len(r.data)
    if fetched % 10000 < BATCH:
        print(f"  {fetched} rows...")
    if len(r.data) < BATCH:
        break
    offset += BATCH
print(f"  {fetched} total, {len(skill_prov_ofertas)} unique skills")

# 3. Build REGICE provincial skill sets
print("Building REGICE provincial skill coverage...")
regice_skills_by_curso = defaultdict(set)
for row in fetch_all_paginated('regice_cursos_skills', 'curso_id, skill_uri'):
    regice_skills_by_curso[row['curso_id']].add(row['skill_uri'])

curso_sedes = defaultdict(set)
for row in fetch_all_paginated('regice_cursos_sedes', 'curso_id, sede_code'):
    curso_sedes[row['curso_id']].add(row['sede_code'])

sede_prov = {}
for row in fetch_all_paginated('regice_sedes', 'sede_code, provincia'):
    sede_prov[row['sede_code']] = row['provincia']

regice_by_prov = defaultdict(set)
for cid, skill_uris in regice_skills_by_curso.items():
    for sede_code in curso_sedes.get(cid, []):
        prov = sede_prov.get(sede_code)
        if prov:
            regice_by_prov[prov].update(skill_uris)

print(f"  REGICE provincias: {len(regice_by_prov)}")
for prov, skills in sorted(regice_by_prov.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"    {prov}: {len(skills)} skills")

# 4. Truncate and insert
print("\nTruncating brecha_formacion_provincial...")
client.table('brecha_formacion_provincial').delete().neq('provincia', '').execute()
time.sleep(1)

# 5. For each MOL provincia, compute brecha
provincias_mol = sorted(set(ofertas_prov.values()))
print(f"\nProcessing {len(provincias_mol)} provincias...")

for prov in provincias_mol:
    prov_regice = PROV_MAP.get(prov, prov)
    regice_skills = regice_by_prov.get(prov_regice, set())

    rows = []
    for uri, prov_ofertas in skill_prov_ofertas.items():
        if prov not in prov_ofertas:
            continue
        count = len(prov_ofertas[prov])
        covered = uri in regice_skills
        rows.append({
            'provincia': prov,
            'skill_uri': uri,
            'skill_label': skill_labels.get(uri, ''),
            'ofertas_count': count,
            'cursos_count': 1 if covered else 0,
            'estado': 'cubierta' if covered else 'brecha',
        })

    # Sort by ofertas_count DESC, keep top 500 per provincia
    rows.sort(key=lambda x: -x['ofertas_count'])
    rows = rows[:500]

    print(f"  {prov}: {len(rows)} skills ({sum(1 for r in rows if r['estado']=='cubierta')} cubiertas)")

    for i in range(0, len(rows), 500):
        client.table('brecha_formacion_provincial').upsert(rows[i:i+500]).execute()
        time.sleep(0.3)

print("\n✅ Done!")
