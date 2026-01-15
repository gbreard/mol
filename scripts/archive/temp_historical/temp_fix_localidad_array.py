#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige localidades que son arrays JSON"""
import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Buscar localidades que son arrays (empiezan con [)
cursor.execute("SELECT id_oferta, localidad FROM ofertas_nlp WHERE localidad LIKE '[%'")

rows = cursor.fetchall()
print(f"Localidades como array: {len(rows)}")

corregidas = 0
for id_oferta, localidad in rows:
    try:
        lista = json.loads(localidad)
        if isinstance(lista, list) and lista:
            nuevo_valor = lista[0]
            cursor.execute("UPDATE ofertas_nlp SET localidad = ? WHERE id_oferta = ?", (nuevo_valor, id_oferta))
            print(f"  {id_oferta}: {localidad[:50]} -> {nuevo_valor}")
            corregidas += 1
    except Exception as e:
        print(f"  Error {id_oferta}: {e}")

conn.commit()
conn.close()
print(f"\nCorregidas: {corregidas}")
