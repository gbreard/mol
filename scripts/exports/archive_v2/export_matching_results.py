#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exporta resultados del matching a Excel para revision.
"""
import sys
sys.path.insert(0, 'D:/OEDE/Webscrapping/database')
sys.path.insert(0, 'D:/OEDE/Webscrapping')

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

from match_ofertas_v2 import (
    load_all_configs,
    get_semantic_matcher,
    match_oferta_v2_bge,
    obtener_ofertas_nlp
)

DB_PATH = Path("D:/OEDE/Webscrapping/database/bumeran_scraping.db")
EXPORTS_DIR = Path("D:/OEDE/Webscrapping/exports")


def exportar_matching_excel(limit: int = 50):
    """Ejecuta matching y exporta a Excel."""

    print(f"Conectando a BD...")
    conn = sqlite3.connect(str(DB_PATH))

    print(f"Cargando modelo BGE-M3...")
    matcher = get_semantic_matcher()
    matcher.load()

    config = load_all_configs()

    print(f"Obteniendo ofertas...")
    ofertas = obtener_ofertas_nlp(conn, limit=limit)
    print(f"Ofertas a procesar: {len(ofertas)}")

    resultados = []

    for i, oferta in enumerate(ofertas):
        result = match_oferta_v2_bge(oferta, conn, config)

        # Extraer alternativas
        alt1 = result.alternativas[0] if len(result.alternativas) > 0 else {}
        alt2 = result.alternativas[1] if len(result.alternativas) > 1 else {}
        alt3 = result.alternativas[2] if len(result.alternativas) > 2 else {}

        # Extraer codigo ESCO del URI (formato: .../occupation/xxxx.x)
        def extraer_esco_code(uri):
            if uri and "/" in uri:
                return uri.split("/")[-1]
            return ""

        resultados.append({
            "id_oferta": oferta["id_oferta"],
            "titulo": oferta.get("titulo", "")[:80],
            "titulo_limpio": oferta.get("titulo_limpio", "")[:80],
            "area_funcional": oferta.get("area_funcional"),
            "nivel_seniority": oferta.get("nivel_seniority"),
            "sector_empresa": oferta.get("sector_empresa"),
            "nlp_version": oferta.get("nlp_version"),
            "status": result.status,
            "esco_label": result.esco_label,
            "esco_code": extraer_esco_code(result.esco_uri),
            "isco_code": result.isco_code,
            "score": round(result.score, 4) if result.score else None,
            "metodo": result.metodo,
            "alt1_label": alt1.get("label", "")[:50] if alt1 else "",
            "alt1_esco": extraer_esco_code(alt1.get("esco_uri", "")) if alt1 else "",
            "alt1_isco": alt1.get("isco_code", "") if alt1 else "",
            "alt1_score": round(alt1.get("score", 0), 3) if alt1 else None,
            "alt2_label": alt2.get("label", "")[:50] if alt2 else "",
            "alt2_esco": extraer_esco_code(alt2.get("esco_uri", "")) if alt2 else "",
            "alt2_isco": alt2.get("isco_code", "") if alt2 else "",
            "alt2_score": round(alt2.get("score", 0), 3) if alt2 else None,
            "alt3_label": alt3.get("label", "")[:50] if alt3 else "",
            "alt3_esco": extraer_esco_code(alt3.get("esco_uri", "")) if alt3 else "",
            "alt3_isco": alt3.get("isco_code", "") if alt3 else "",
            "alt3_score": round(alt3.get("score", 0), 3) if alt3 else None,
        })

        if (i + 1) % 10 == 0:
            print(f"  Procesadas: {i + 1}/{len(ofertas)}")

    conn.close()

    # Crear DataFrame
    df = pd.DataFrame(resultados)

    # Exportar a Excel
    EXPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = EXPORTS_DIR / f"matching_results_{timestamp}.xlsx"

    # Crear Excel con formato
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Matching', index=False)

        # Ajustar anchos de columna
        worksheet = writer.sheets['Matching']
        worksheet.column_dimensions['A'].width = 12  # id_oferta
        worksheet.column_dimensions['B'].width = 50  # titulo
        worksheet.column_dimensions['C'].width = 50  # titulo_limpio
        worksheet.column_dimensions['D'].width = 18  # area_funcional
        worksheet.column_dimensions['E'].width = 14  # seniority
        worksheet.column_dimensions['F'].width = 15  # sector
        worksheet.column_dimensions['G'].width = 10  # nlp_version
        worksheet.column_dimensions['H'].width = 10  # status
        worksheet.column_dimensions['I'].width = 55  # esco_label
        worksheet.column_dimensions['J'].width = 10  # isco_code
        worksheet.column_dimensions['K'].width = 8   # score
        worksheet.column_dimensions['L'].width = 25  # metodo
        worksheet.column_dimensions['M'].width = 40  # alt1
        worksheet.column_dimensions['N'].width = 8   # alt1_score
        worksheet.column_dimensions['O'].width = 40  # alt2
        worksheet.column_dimensions['P'].width = 8   # alt2_score
        worksheet.column_dimensions['Q'].width = 40  # alt3
        worksheet.column_dimensions['R'].width = 8   # alt3_score

    print(f"\nExportado a: {filepath}")
    print(f"Total filas: {len(df)}")

    # Resumen
    print(f"\nResumen:")
    print(df['status'].value_counts().to_string())
    print(f"\nMetodos:")
    print(df['metodo'].value_counts().to_string())

    return filepath


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Numero de ofertas")
    args = parser.parse_args()

    exportar_matching_excel(args.limit)
