# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'database')
from match_ofertas_v3 import MatcherV3
import sqlite3

# Cargar gold set manual
with open('database/gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)

conn = sqlite3.connect('database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row
matcher = MatcherV3(db_conn=conn, verbose=False)

errores = []
for caso in gold_set:
    id_oferta = caso['id_oferta']
    isco_esperado = caso.get('isco_esperado', '')

    if not isco_esperado:
        continue

    # Cargar datos NLP
    cur = conn.execute('SELECT * FROM ofertas_nlp WHERE id_oferta = ?', (str(id_oferta),))
    row = cur.fetchone()
    if not row:
        continue

    oferta = {
        'titulo_limpio': row['titulo_limpio'] or '',
        'tareas_explicitas': row['tareas_explicitas'] or '',
        'area_funcional': row['area_funcional'] or '',
        'nivel_seniority': row['nivel_seniority'] or ''
    }

    result = matcher.match(oferta)

    if result.isco_code != isco_esperado:
        errores.append({
            'id': id_oferta,
            'titulo': row['titulo_limpio'][:50] if row['titulo_limpio'] else '',
            'esperado': isco_esperado,
            'obtenido': result.isco_code,
            'esco': result.esco_label[:40] if result.esco_label else ''
        })

matcher.close()
conn.close()

print(f'Errores encontrados: {len(errores)}')
for e in errores:
    print(f"  ID {e['id']}: {e['titulo']}")
    print(f"    Esperado: {e['esperado']}, Obtenido: {e['obtenido']} ({e['esco']})")
