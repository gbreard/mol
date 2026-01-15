#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check ISCO subdivisions in ESCO occupations"""
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Total ocupaciones
cursor.execute('SELECT COUNT(*) FROM esco_occupations')
print(f'Total ocupaciones ESCO: {cursor.fetchone()[0]:,}')

# Ver estructura de ISCO codes
print('\n=== TOP 20 ISCO CODES POR CANTIDAD ===')
cursor.execute('''
    SELECT isco_code, COUNT(*) as n
    FROM esco_occupations
    WHERE isco_code IS NOT NULL
    GROUP BY isco_code
    ORDER BY n DESC
    LIMIT 20
''')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} ocupaciones')

# Ver ejemplo de subdivisiones
print('\n=== EJEMPLO: Subdivisiones de C5223 (Dependientes de tiendas) ===')
cursor.execute('''
    SELECT isco_code, preferred_label_es
    FROM esco_occupations
    WHERE isco_code = 'C5223'
    ORDER BY preferred_label_es
    LIMIT 20
''')
for row in cursor.fetchall():
    print(f'  {row[1][:70]}')

# Ver si hay esco_code (más granular)
print('\n=== ESCO_CODE (código específico) ===')
cursor.execute('''
    SELECT esco_code, isco_code, preferred_label_es
    FROM esco_occupations
    WHERE esco_code IS NOT NULL
    LIMIT 10
''')
for row in cursor.fetchall():
    esco = row[0] if row[0] else 'NULL'
    print(f'  ESCO: {esco:20} | ISCO: {row[1]} | {row[2][:35]}')

# Estadísticas de niveles ISCO
print('\n=== DISTRIBUCIÓN POR NIVEL ISCO ===')
cursor.execute('''
    SELECT
        SUBSTR(isco_code, 2, 1) as nivel1,
        COUNT(*) as n
    FROM esco_occupations
    WHERE isco_code IS NOT NULL
    GROUP BY nivel1
    ORDER BY nivel1
''')
for row in cursor.fetchall():
    print(f'  Nivel 1 = {row[0]}: {row[1]:,} ocupaciones')

# Ver si las URIs tienen subdivisiones
print('\n=== ESTRUCTURA DE URIs (muestra) ===')
cursor.execute('''
    SELECT occupation_uri, isco_code, preferred_label_es
    FROM esco_occupations
    WHERE isco_code = 'C5223'
    LIMIT 5
''')
for row in cursor.fetchall():
    uri_uuid = row[0].split('/')[-1]
    print(f'  UUID: {uri_uuid[:20]}... | {row[2][:50]}')

conn.close()
