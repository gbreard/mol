#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script temporal para ejecutar scraping semanal"""
import sys
from pathlib import Path

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent / '01_sources' / 'bumeran' / 'scrapers'))
sys.path.insert(0, str(Path(__file__).parent / 'database'))

from bumeran_scraper import BumeranScraper
from db_manager import DatabaseManager

print('='*70)
print('SCRAPING SEMANAL - BUMERAN')
print('='*70)

# Inicializar scraper
scraper = BumeranScraper(delay_between_requests=1.5)

# Scrapear (modo incremental)
ofertas = scraper.scrapear_todo(
    max_paginas=None,  # Sin límite
    page_size=100,     # Máximo por página
    incremental=True   # Solo nuevas
)

print(f'\nTotal ofertas scrapeadas: {len(ofertas):,}')

# Guardar en BD
if ofertas:
    df = scraper.procesar_ofertas(ofertas)

    if not df.empty:
        with DatabaseManager('database/bumeran_scraping.db') as db:
            n = db.insert_ofertas(df)
            print(f'Ofertas insertadas en BD: {n:,}')
    else:
        print('DataFrame vacío después de procesar')
else:
    print('No se obtuvieron ofertas nuevas')

print('='*70)
print('Scraping completado')
print('='*70)
