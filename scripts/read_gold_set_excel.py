# -*- coding: utf-8 -*-
"""Script para leer y analizar el Excel de validación Gold Set."""

import pandas as pd
import json
import sys
import io
from pathlib import Path

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def sanitize_name(name):
    """Sanitiza nombre para usar como filename."""
    return name.replace(' ', '_').replace('/', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

def main():
    excel_path = Path("D:/OEDE/Webscrapping/docs/MOL_Gold_Set_49_Ofertas_Validacion (15-12).xlsx")
    output_dir = Path("D:/OEDE/Webscrapping/scripts/excel_exports")
    output_dir.mkdir(exist_ok=True)

    if not excel_path.exists():
        print(f"ERROR: No existe {excel_path}")
        return

    # Leer el Excel
    xls = pd.ExcelFile(excel_path)

    print("=" * 80)
    print("ANALISIS DEL EXCEL DE VALIDACION GOLD SET")
    print("=" * 80)
    print(f"\nHojas encontradas ({len(xls.sheet_names)}):")
    for i, s in enumerate(xls.sheet_names, 1):
        print(f"  {i:2d}. {s}")

    # Exportar cada hoja a JSON
    all_sheets = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        safe_name = sanitize_name(sheet)
        json_path = output_dir / f"{safe_name}.json"

        # Convertir a dict y manejar NaN
        records = df.where(pd.notnull(df), None).to_dict(orient='records')
        all_sheets[sheet] = {
            "filas": len(df),
            "columnas": list(df.columns),
            "data": records
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[{sheet}] -> {len(df)} filas, {len(df.columns)} cols -> {json_path.name}")

    # Guardar resumen completo
    summary_path = output_dir / "_summary.json"
    summary = {sheet: {"filas": info["filas"], "columnas": info["columnas"]} for sheet, info in all_sheets.items()}
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n\nResumen guardado en: {summary_path}")
    print(f"JSONs exportados a: {output_dir}")

if __name__ == "__main__":
    main()
