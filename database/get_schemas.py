import sqlite3
conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

print('=== OFERTAS ===')
cursor.execute('PRAGMA table_info(ofertas)')
for row in cursor.fetchall():
    print(row)

print('\n=== OFERTAS_NLP ===')
cursor.execute('PRAGMA table_info(ofertas_nlp)')
for row in cursor.fetchall():
    print(row)

print('\n=== OFERTAS_ESCO_MATCHING ===')
cursor.execute('PRAGMA table_info(ofertas_esco_matching)')
for row in cursor.fetchall():
    print(row)

print('\n=== ESCO_OCCUPATIONS ===')
cursor.execute('PRAGMA table_info(esco_occupations)')
for row in cursor.fetchall():
    print(row)

print('\n=== ESCO_ASSOCIATIONS ===')
cursor.execute('PRAGMA table_info(esco_associations)')
for row in cursor.fetchall():
    print(row)

conn.close()
