#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-ejecutar matching con nuevas reglas y exportar revision actualizada."""
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
print("REVISION MATCHING v2 - Con Reglas R16-R22")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)

# Obtener 50 ofertas con NLP
ofertas = obtener_ofertas_nlp(conn, limit=50)
print(f"\nOfertas obtenidas: {len(ofertas)}")

resultados = []

for i, oferta in enumerate(ofertas, 1):
    result = match_oferta_v2_bge(oferta, conn)

    if result:
        esco_code = ""
        if result.esco_uri and "/" in result.esco_uri:
            esco_code = result.esco_uri.split("/")[-1]

        resultados.append({
            "num": i,
            "id_oferta": str(oferta["id_oferta"]),
            "titulo": oferta.get("titulo", "")[:60],
            "match_esco": (result.esco_label or "")[:50],
            "esco_code": esco_code,
            "isco_code": result.isco_code or "",
            "score": round(result.score, 2),
            "metodo": result.metodo or "",
            "status": result.status or ""
        })

conn.close()

# Crear DataFrame
df = pd.DataFrame(resultados)

# Estadisticas por metodo
print("\n" + "=" * 60)
print("ESTADISTICAS POR METODO:")
print("=" * 60)
print(df["metodo"].value_counts().to_string())

# Contar cuantas reglas de negocio se aplicaron
reglas_aplicadas = df[df["metodo"].str.contains("regla_negocio", na=False)]
print(f"\nTotal reglas de negocio aplicadas: {len(reglas_aplicadas)}")

# Detallar cada regla
if len(reglas_aplicadas) > 0:
    print("\nDetalle reglas:")
    for _, row in reglas_aplicadas.iterrows():
        print(f"  - ID {row['id_oferta']}: {row['titulo'][:40]}...")
        print(f"    -> {row['match_esco']} ({row['metodo']})")

# Exportar a Excel
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filepath = EXPORTS_DIR / f"matching_revision_v2_{timestamp}.xlsx"

with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Matching', index=False)

    ws = writer.sheets['Matching']
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 60
    ws.column_dimensions['D'].width = 50
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 8
    ws.column_dimensions['G'].width = 8
    ws.column_dimensions['H'].width = 35
    ws.column_dimensions['I'].width = 12

print(f"\nExportado a: {filepath}")
print("\nRevise el Excel para clasificar manualmente como CORRECTO/ACEPTABLE/INCORRECTO")
