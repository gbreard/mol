#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normaliza tareas_explicitas de JSON a texto plano.
JSON: [{"valor": "x", "texto_original": "y"}, ...] -> "x; y; ..."
"""

import sqlite3
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(__file__).parent.parent

with open(base / 'database/gold_set_nlp_100_ids.json', 'r', encoding='utf-8') as f:
    ids = json.load(f)

conn = sqlite3.connect(base / 'database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
placeholders = ','.join(['?' for _ in ids])

# Obtener tareas en formato JSON
c.execute(f'''
    SELECT id_oferta, tareas_explicitas
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
      AND tareas_explicitas LIKE '[{{%'
''', ids)

rows = c.fetchall()
print(f"Ofertas con tareas JSON: {len(rows)}")

updates = []
for row in rows:
    id_oferta = row['id_oferta']
    tareas_json = row['tareas_explicitas']

    try:
        tareas_list = json.loads(tareas_json)
        # Extraer valores
        tareas_texto = []
        for t in tareas_list:
            if isinstance(t, dict):
                # Preferir 'valor' sobre 'texto_original'
                valor = t.get('valor') or t.get('texto_original') or str(t)
                if valor and len(valor) > 3:
                    tareas_texto.append(valor.strip())
            elif isinstance(t, str) and len(t) > 3:
                tareas_texto.append(t.strip())

        # Unir con punto y coma
        tareas_final = "; ".join(tareas_texto[:10])  # Max 10 tareas

        if tareas_final:
            updates.append((tareas_final, str(id_oferta)))

    except json.JSONDecodeError as e:
        print(f"  ERROR parsing [{id_oferta}]: {e}")

print(f"Actualizando {len(updates)} registros...")

c.executemany('''
    UPDATE ofertas_nlp
    SET tareas_explicitas = ?
    WHERE id_oferta = ?
''', updates)
conn.commit()

# Verificar resultado
print("\nEJEMPLOS DESPUES DE NORMALIZACION:")
c.execute(f'''
    SELECT id_oferta, tareas_explicitas
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
      AND tareas_explicitas IS NOT NULL
      AND tareas_explicitas != ''
    LIMIT 5
''', ids)

for row in c.fetchall():
    tareas = row['tareas_explicitas'][:150]
    print(f"  [{row['id_oferta']}] {tareas}...")

conn.close()
print("\n[OK] Normalizacion completada")
