#!/usr/bin/env python3
"""Check ofertas statistics"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

print('=== OFERTAS TOTALES ===')
cursor.execute('SELECT COUNT(*) FROM ofertas')
print(f'Total en tabla ofertas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM ofertas_esco_matching')
print(f'Total con matching ESCO: {cursor.fetchone()[0]}')

print('\n=== OFERTAS POR FECHA DE SCRAPING ===')
cursor.execute("""
    SELECT DATE(scrapeado_en) as fecha, COUNT(*) as n
    FROM ofertas
    GROUP BY DATE(scrapeado_en)
    ORDER BY fecha DESC
    LIMIT 15
""")
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} ofertas')

print('\n=== OFERTAS SIN MATCHING ===')
cursor.execute("""
    SELECT COUNT(*) FROM ofertas o
    WHERE NOT EXISTS (
        SELECT 1 FROM ofertas_esco_matching m
        WHERE CAST(o.id_oferta AS TEXT) = m.id_oferta
    )
""")
sin_matching = cursor.fetchone()[0]
print(f'Ofertas sin matching: {sin_matching}')

if sin_matching > 0:
    print('\n=== MUESTRA DE OFERTAS SIN MATCHING ===')
    cursor.execute("""
        SELECT o.id_oferta, o.titulo, DATE(o.scrapeado_en)
        FROM ofertas o
        WHERE NOT EXISTS (
            SELECT 1 FROM ofertas_esco_matching m
            WHERE CAST(o.id_oferta AS TEXT) = m.id_oferta
        )
        ORDER BY o.scrapeado_en DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1][:50]}... ({row[2]})')

conn.close()
