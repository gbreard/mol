#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check a specific offer's raw and NLP data."""

import sqlite3
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_oferta(id_oferta):
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))

    # Datos raw del scraping
    print("=" * 70)
    print(f"OFERTA: {id_oferta}")
    print("=" * 70)

    print("\n--- DATOS RAW (tabla ofertas) ---")
    cur = conn.execute(
        'SELECT titulo, descripcion, localizacion, empresa FROM ofertas WHERE id_oferta = ?',
        (id_oferta,)
    )
    row = cur.fetchone()
    if row:
        print(f"Titulo: {row[0]}")
        print(f"Empresa: {row[3]}")
        print(f"Localizacion: {row[2]}")
        desc = row[1] or "(vacio)"
        print(f"Descripcion:\n{desc[:800]}...")
    else:
        print("No encontrado en tabla ofertas")

    print("\n--- DATOS NLP (tabla ofertas_nlp) ---")
    cur = conn.execute('''
        SELECT titulo_limpio, provincia, localidad, sector_empresa,
               tareas_explicitas, skills_tecnicas_list, soft_skills_list,
               experiencia_min_anios, experiencia_max_anios,
               area_funcional, nivel_seniority, nivel_educativo,
               modalidad, tipo_oferta
        FROM ofertas_nlp WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        print(f"titulo_limpio: {row[0]}")
        print(f"provincia: {row[1]}")
        print(f"localidad: {row[2]}")
        print(f"sector_empresa: {row[3]}")
        print(f"tareas_explicitas: {row[4]}")
        print(f"skills_tecnicas_list: {row[5]}")
        print(f"soft_skills_list: {row[6]}")
        print(f"experiencia: {row[7]} - {row[8]} anios")
        print(f"area_funcional: {row[9]}")
        print(f"nivel_seniority: {row[10]}")
        print(f"nivel_educativo: {row[11]}")
        print(f"modalidad: {row[12]}")
        print(f"tipo_oferta: {row[13]}")
    else:
        print("No encontrado en tabla ofertas_nlp")

    conn.close()

if __name__ == "__main__":
    id_oferta = sys.argv[1] if len(sys.argv) > 1 else "1118028201"
    check_oferta(id_oferta)
