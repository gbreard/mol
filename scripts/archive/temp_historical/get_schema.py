# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect("database/bumeran_scraping.db")
cur = conn.execute("PRAGMA table_info(ofertas_nlp)")
for row in cur.fetchall():
    print(row[1])
conn.close()
