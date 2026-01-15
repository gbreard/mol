import sqlite3
from match_ofertas_v3 import MatcherV3

conn = sqlite3.connect('bumeran_scraping.db')
matcher = MatcherV3(db_conn=conn, verbose=True)

ids = ['1118026729', '1118027276', '2162667', '1118018461', '1117995368']
esperados = ['4321', '3322', '1412', '2359', '3240']

for id_o, esp in zip(ids, esperados):
    cur = conn.execute('SELECT titulo_limpio, tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?', (id_o,))
    row = cur.fetchone()
    if row:
        titulo = row[0] or ""
        tareas = row[1] or ""
        print(f"\n{'='*60}")
        print(f"ID: {id_o}")
        print(f"Titulo: {titulo}")
        print(f"Tareas: {tareas[:80]}...")
        print(f"Esperado: {esp}")

        result = matcher.match({'titulo_limpio': titulo, 'tareas_explicitas': tareas})
        print(f"Resultado: ISCO={result.isco_code}, Metodo={result.metodo}")

        if result.isco_code == esp[:4]:
            print(">>> OK")
        else:
            print(f">>> FALLO (esperado {esp})")

matcher.close()
conn.close()
