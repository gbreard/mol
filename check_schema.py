import sqlite3

conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(ofertas)')

print('\nCampos de la tabla ofertas:')
print('='*60)
for row in cursor.fetchall():
    print(f'{row[1]:<30} {row[2]:<15}')
conn.close()
