#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecutar matching en 50 ofertas REALES de la BD y exportar para revision."""
import sys
import io
sys.path.insert(0, "D:/OEDE/Webscrapping/database")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from match_ofertas_v2 import match_oferta_v2_bge, obtener_ofertas_nlp

DB_PATH = "D:/OEDE/Webscrapping/database/bumeran_scraping.db"
EXPORTS_DIR = Path("D:/OEDE/Webscrapping/exports")

print("=" * 80)
print("MATCHING EN 50 OFERTAS REALES")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)

# Obtener 50 ofertas REALES con NLP
ofertas = obtener_ofertas_nlp(conn, limit=50)
print(f"\nOfertas obtenidas de BD: {len(ofertas)}")

resultados = []

for i, oferta in enumerate(ofertas, 1):
    result = match_oferta_v2_bge(oferta, conn)

    if result:
        esco_code = ""
        if result.esco_uri and "/" in result.esco_uri:
            esco_code = result.esco_uri.split("/")[-1]

        # Obtener alternativas
        alt1 = result.alternativas[0] if len(result.alternativas) > 0 else {}
        alt2 = result.alternativas[1] if len(result.alternativas) > 1 else {}
        alt3 = result.alternativas[2] if len(result.alternativas) > 2 else {}

        resultados.append({
            "num": i,
            "id_oferta": str(oferta["id_oferta"]),
            "titulo": oferta.get("titulo_limpio") or oferta.get("titulo", ""),
            "match_esco": result.esco_label or "",
            "esco_code": esco_code,
            "isco_code": result.isco_code or "",
            "score": round(result.score, 2),
            "metodo": result.metodo or "",
            "alt1_label": alt1.get("esco_label", "")[:40] if alt1 else "",
            "alt1_isco": alt1.get("isco_code", "") if alt1 else "",
            "alt2_label": alt2.get("esco_label", "")[:40] if alt2 else "",
            "alt2_isco": alt2.get("isco_code", "") if alt2 else "",
            "alt3_label": alt3.get("esco_label", "")[:40] if alt3 else "",
            "alt3_isco": alt3.get("isco_code", "") if alt3 else "",
            # Columnas para revision manual
            "CLASIFICACION": "",  # CORRECTO / ACEPTABLE / INCORRECTO
            "PROBLEMA": "",       # Descripcion del problema si hay
        })
    else:
        resultados.append({
            "num": i,
            "id_oferta": str(oferta["id_oferta"]),
            "titulo": oferta.get("titulo_limpio") or oferta.get("titulo", ""),
            "match_esco": "ERROR",
            "esco_code": "",
            "isco_code": "",
            "score": 0,
            "metodo": "error",
            "alt1_label": "",
            "alt1_isco": "",
            "alt2_label": "",
            "alt2_isco": "",
            "alt3_label": "",
            "alt3_isco": "",
            "CLASIFICACION": "",
            "PROBLEMA": "",
        })

conn.close()

# Crear DataFrame
df = pd.DataFrame(resultados)

# Estadisticas
print("\n" + "=" * 60)
print("ESTADISTICAS:")
print("=" * 60)
print(df["metodo"].value_counts().to_string())

# Exportar a Excel
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filepath = EXPORTS_DIR / f"matching_50_reales_{timestamp}.xlsx"

with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Matching', index=False)

    ws = writer.sheets['Matching']
    ws.column_dimensions['A'].width = 5   # num
    ws.column_dimensions['B'].width = 12  # id
    ws.column_dimensions['C'].width = 55  # titulo
    ws.column_dimensions['D'].width = 45  # match_esco
    ws.column_dimensions['E'].width = 12  # esco_code
    ws.column_dimensions['F'].width = 8   # isco_code
    ws.column_dimensions['G'].width = 8   # score
    ws.column_dimensions['H'].width = 35  # metodo
    ws.column_dimensions['I'].width = 35  # alt1_label
    ws.column_dimensions['J'].width = 8   # alt1_isco
    ws.column_dimensions['K'].width = 35  # alt2_label
    ws.column_dimensions['L'].width = 8   # alt2_isco
    ws.column_dimensions['M'].width = 35  # alt3_label
    ws.column_dimensions['N'].width = 8   # alt3_isco
    ws.column_dimensions['O'].width = 15  # CLASIFICACION
    ws.column_dimensions['P'].width = 40  # PROBLEMA

print(f"\nExportado a: {filepath}")
print("\nColumnas para su revision manual:")
print("  - CLASIFICACION: escribir CORRECTO, ACEPTABLE o INCORRECTO")
print("  - PROBLEMA: describir el problema si hay")
