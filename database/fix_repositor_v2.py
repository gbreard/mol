# -*- coding: utf-8 -*-
"""Corregir diccionario: Repositor -> ISCO 9334 / reponedor/reponedora."""
import sqlite3

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
c = sqlite3.connect(db_path)

print('ANTES - Entradas para repositor:')
sql = "SELECT id, termino_argentino, isco_target, esco_preferred_label FROM diccionario_arg_esco WHERE termino_argentino LIKE '%repositor%' COLLATE NOCASE"
for row in c.execute(sql).fetchall():
    print(f'  {row}')

# Corregir a ISCO 9334 y label "reponedor/reponedora" (el label correcto de ESCO)
sql_update = """UPDATE diccionario_arg_esco
SET isco_target = '9334', esco_preferred_label = 'reponedor/reponedora'
WHERE termino_argentino LIKE '%repositor%' COLLATE NOCASE"""
c.execute(sql_update)
c.commit()

print('\nDESPUES - Entradas corregidas:')
for row in c.execute(sql).fetchall():
    print(f'  {row}')

c.close()
print('\nOK: Diccionario actualizado con ISCO 9334 (correcto para repositor)')
