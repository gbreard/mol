# -*- coding: utf-8 -*-
"""Debug limpieza de titulo."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from limpiar_titulos import limpiar_titulo, cargar_config
import re

config = cargar_config()

conn = sqlite3.connect(Path(__file__).parent.parent / "database" / "bumeran_scraping.db")
c = conn.cursor()
c.execute("SELECT titulo FROM ofertas WHERE id_oferta = 2170124")
row = c.fetchone()
titulo = row[0]
print(f"Titulo DB: [{titulo}]")

# Aplicar limpieza paso a paso
t = titulo

# Paso 3 - zonas_ubicaciones
print("\n=== ZONAS_UBICACIONES ===")
for patron_info in config.get("zonas_ubicaciones", {}).get("patrones", []):
    patron = patron_info.get("patron", "")
    if patron:
        match = re.search(patron, t, flags=re.IGNORECASE)
        if match:
            print(f"MATCH patron: {patron}")
            print(f"  Matched: [{match.group()}]")
        t_new = re.sub(patron, "", t, flags=re.IGNORECASE)
        if t_new != t:
            print(f"  Cambio: [{t}] -> [{t_new}]")
        t = t_new

print(f"\nFinal zonas: [{t}]")

# Paso 3b - localidades_final
print("\n=== LOCALIDADES_FINAL ===")
localidades = config.get("localidades_final", {}).get("lista", [])
for localidad in localidades:
    patron = rf'\s*[-–—]\s*{re.escape(localidad)}$'
    match = re.search(patron, t, flags=re.IGNORECASE)
    if match:
        print(f"MATCH localidad: {localidad}")
        print(f"  Matched: [{match.group()}]")
    t_new = re.sub(patron, "", t, flags=re.IGNORECASE)
    if t_new != t:
        print(f"  Cambio: [{t}] -> [{t_new}]")
    t = t_new

print(f"\nFinal localidades: [{t}]")

# Resultado final
resultado = limpiar_titulo(titulo, config)
print(f"\n=== RESULTADO FINAL ===")
print(f"Original: [{titulo}]")
print(f"Limpio:   [{resultado}]")
