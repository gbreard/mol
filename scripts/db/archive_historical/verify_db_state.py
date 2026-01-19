# -*- coding: utf-8 -*-
"""Verifica estado actual de la base de datos."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

print("ESTADO FINAL DE LA BASE DE DATOS")
print("=" * 60)

# Ofertas scrapeadas
c.execute("SELECT COUNT(*) FROM ofertas")
total = c.fetchone()[0]
print(f"\nOfertas scrapeadas: {total:,} (intactas)")

# NLP por version
c.execute("SELECT nlp_version, COUNT(*) FROM ofertas_nlp GROUP BY nlp_version ORDER BY COUNT(*) DESC")
nlp = c.fetchall()
print(f"\nNLP procesadas:")
for v, cnt in nlp:
    print(f"  {v}: {cnt:,}")
total_nlp = sum(cnt for _, cnt in nlp)
print(f"  TOTAL: {total_nlp:,}")

# Matching
c.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
match = c.fetchone()[0]
print(f"\nMatching ESCO: {match} (limpio para v2.1.1)")

# Backups creados
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%backup%'")
backups = c.fetchall()
print(f"\nTablas de backup:")
for b in backups:
    print(f"  - {b[0]}")

# Ofertas sin NLP (pendientes)
c.execute("""
    SELECT COUNT(*) FROM ofertas o
    LEFT JOIN ofertas_nlp n ON o.aviso_id = n.aviso_id
    WHERE n.aviso_id IS NULL
""")
sin_nlp = c.fetchone()[0]
print(f"\nOfertas sin NLP (pendientes): {sin_nlp:,}")

conn.close()
print("\n" + "=" * 60)
