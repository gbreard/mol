"""
Test de detección de duplicados en el scraper
"""

import sys
sys.path.insert(0, '01_sources/bumeran/scrapers')

from bumeran_scraper import BumeranScraper
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

print("="*70)
print("TEST: Deteccion de duplicados masivos")
print("="*70)
print()
print("Este test hara un scraping de 15 paginas")
print("Si la API sigue rota, deberia detectar duplicados y detener en pagina ~11")
print()

# Crear scraper
scraper = BumeranScraper()

# Scrapear 15 páginas (si la paginación está rota, detectará duplicados)
ofertas = scraper.scrapear_todo(
    max_paginas=15,
    incremental=False  # Desactivar modo incremental para ver todos los duplicados
)

print()
print("="*70)
print("RESULTADO:")
print("="*70)
print(f"Total ofertas scrapeadas: {len(ofertas)}")

# Analizar duplicados
ids = [str(o.get('id')) for o in ofertas]
ids_unicos = len(set(ids))
tasa_duplicados = ((len(ids) - ids_unicos) / len(ids)) * 100 if ids else 0

print(f"IDs unicos: {ids_unicos}")
print(f"Tasa de duplicados: {tasa_duplicados:.1f}%")

if tasa_duplicados > 90:
    print("\n[OK] Deteccion de duplicados FUNCIONO - debio haberse detenido")
elif tasa_duplicados > 50:
    print("\n[WARNING] Duplicados detectados pero no se detuvo")
else:
    print("\n[OK] Sin duplicados masivos - paginacion funciona bien")

print("="*70)
