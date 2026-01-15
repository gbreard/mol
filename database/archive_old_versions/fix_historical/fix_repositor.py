# -*- coding: utf-8 -*-
import sqlite3

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
c = sqlite3.connect(db_path)

# Check ALL entries for repositor (case insensitive)
print('TODAS LAS ENTRADAS REPOSITOR:')
sql_all = """SELECT id, termino_argentino, isco_target, esco_preferred_label
FROM diccionario_arg_esco WHERE termino_argentino LIKE '%repositor%' COLLATE NOCASE"""
for row in c.execute(sql_all).fetchall():
    print(f'  {row}')

# Update ALL entries
sql_update = """UPDATE diccionario_arg_esco
SET isco_target = '5223', esco_preferred_label = 'Reponedor de tienda'
WHERE termino_argentino LIKE '%repositor%' COLLATE NOCASE"""
c.execute(sql_update)
c.commit()

print('\nDESPUES DE UPDATE:')
for row in c.execute(sql_all).fetchall():
    print(f'  {row}')

c.close()
print('\nOK: Diccionario actualizado')
