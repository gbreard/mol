import sqlite3
from pathlib import Path

DB_PATH = Path('database/bumeran_scraping.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Total ofertas
cursor.execute('SELECT COUNT(*) FROM ofertas')
total = cursor.fetchone()[0]
print(f'Total ofertas en BD: {total:,}')

# Ultimas fechas de scraping
print('\nUltimas fechas de scraping:')
cursor.execute('''
    SELECT DATE(scrapeado_en) as fecha, COUNT(*) as count
    FROM ofertas
    GROUP BY DATE(scrapeado_en)
    ORDER BY fecha DESC
    LIMIT 5
''')

for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]:,} ofertas')

conn.close()
