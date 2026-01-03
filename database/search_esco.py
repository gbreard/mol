# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r'D:\OEDE\Webscrapping\database\bumeran_scraping.db')

print("Buscando 'repon' en ESCO:")
for row in conn.execute("SELECT preferred_label_es, occupation_uri, isco_code FROM esco_occupations WHERE preferred_label_es LIKE ?", ('%repon%',)).fetchall():
    print(f"  {row[2]} | {row[0]}")

print("\nBuscando 'repos' en ESCO:")
for row in conn.execute("SELECT preferred_label_es, occupation_uri, isco_code FROM esco_occupations WHERE preferred_label_es LIKE ?", ('%repos%',)).fetchall():
    print(f"  {row[2]} | {row[0]}")

print("\nOcupaciones con ISCO 5223:")
for row in conn.execute("SELECT preferred_label_es, occupation_uri, isco_code FROM esco_occupations WHERE isco_code = '5223' ORDER BY preferred_label_es").fetchall():
    print(f"  {row[2]} | {row[0]}")

conn.close()
