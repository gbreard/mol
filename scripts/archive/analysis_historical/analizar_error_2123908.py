# -*- coding: utf-8 -*-
"""Analizar por qué el LLM puso 10 años de experiencia en 2123908"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

# Ver descripcion completa
c.execute('SELECT descripcion FROM ofertas WHERE id_oferta = 2123908')
desc = c.fetchone()[0]

print("DESCRIPCION COMPLETA:")
print(desc)
print()
print("=" * 60)
print("ANALISIS:")
print("=" * 60)

# Buscar posibles fuentes del '10'
if '10' in desc:
    print("- Contiene el numero 10 en el texto")
    idx = desc.find('10')
    print(f"  Contexto: ...{desc[max(0,idx-30):idx+30]}...")
else:
    print("- NO contiene el numero 10 en el texto")

# Buscar frases de poca experiencia
frases_sin_exp = ['poca experiencia', 'primeros trabajos', 'sin experiencia',
                  'no requiere experiencia', 'no es necesaria experiencia',
                  'con o sin experiencia']
print()
print("Frases que indican SIN experiencia:")
for frase in frases_sin_exp:
    if frase.lower() in desc.lower():
        print(f"  [DETECTADO] '{frase}'")
    else:
        print(f"  [ ] '{frase}'")

conn.close()
