#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database/bumeran_scraping.db')
c = conn.cursor()

# Total ofertas
c.execute('SELECT COUNT(*) FROM ofertas')
total = c.fetchone()[0]
print(f"Total ofertas en BD: {total:,}")

# Ofertas hoy
c.execute("SELECT COUNT(*) FROM ofertas WHERE scrapeado_en >= '2025-12-06'")
hoy = c.fetchone()[0]
print(f"Ofertas scrapeadas hoy (2025-12-06): {hoy:,}")

# Ofertas nuevas (insertadas hoy vs tracking previo)
c.execute("SELECT COUNT(*) FROM ofertas WHERE scrapeado_en >= '2025-12-06T21:35:00'")
nuevas = c.fetchone()[0]
print(f"Ofertas nuevas (desde 21:35): {nuevas:,}")

# Tracking file
import json
try:
    with open('data/tracking/bumeran_scraped_ids.json', 'r') as f:
        data = json.load(f)
    print(f"IDs en tracking: {len(data.get('scraped_ids', {})):,}")
    print(f"Ultima actualizacion: {data.get('last_update', 'N/A')}")
except Exception as e:
    print(f"Error leyendo tracking: {e}")

conn.close()
