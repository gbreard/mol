import sqlite3
from skills_implicit_extractor import SkillsImplicitExtractor

conn = sqlite3.connect('bumeran_scraping.db')
extractor = SkillsImplicitExtractor(verbose=False)

# Gold Set IDs
gold_ids = [
    '1118026700', '1118026729', '1118027243', '1118027261', '1118027276',
    '1118027662', '1118027834', '1118027941', '1118028027', '1118028038',
    '1118028201', '1118028376', '1118028657', '1118028681', '1118028828',
    '1118028833', '1118028887', '1118028891', '2162667', '1118022146',
    '1118025212', '1117984105', '1117960588', '1118009739', '1118000814',
    '1118020225', '1118003709', '1118017586', '1118025956', '2164100',
    '2165052', '2165301', '1116898892', '1118023904', '1117980907',
    '1117990944', '1117961954', '1117982053', '1118018461', '1118018714',
    '1118031991', '1116884561', '1117995368', '2170124', '1117975249',
    '1118028777', '1117977340', '1118028048', '1118009703'
]

total_skills = 0
counts = []
ejemplos = []

for id_o in gold_ids:
    cur = conn.execute('SELECT titulo_limpio, tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?', (id_o,))
    row = cur.fetchone()
    if row:
        titulo = row[0] or ""
        tareas = row[1] or ""

        skills = extractor.extract_skills(titulo_limpio=titulo, tareas_explicitas=tareas)
        count = len(skills)
        counts.append(count)
        total_skills += count

        if len(ejemplos) < 3:
            ejemplos.append({
                'titulo': titulo[:40],
                'count': count,
                'skills': [s['skill_esco'][:30] for s in skills[:5]]
            })

conn.close()

print(f"Total ofertas analizadas: {len(counts)}")
print(f"Total skills extraidas: {total_skills}")
print(f"Promedio por oferta: {total_skills/len(counts):.1f}")
print(f"Minimo: {min(counts)}")
print(f"Maximo: {max(counts)}")
print(f"Mediana: {sorted(counts)[len(counts)//2]}")

print("\nDistribucion:")
for rango in [(0,5), (6,10), (11,20), (21,50), (51,100)]:
    cnt = len([c for c in counts if rango[0] <= c <= rango[1]])
    print(f"  {rango[0]}-{rango[1]} skills: {cnt} ofertas ({100*cnt/len(counts):.0f}%)")

print("\nEjemplos:")
for e in ejemplos:
    print(f"\n  {e['titulo']}...")
    print(f"  Skills ({e['count']}): {e['skills']}")
