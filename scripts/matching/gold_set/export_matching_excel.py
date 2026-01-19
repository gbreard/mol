# -*- coding: utf-8 -*-
"""
export_matching_excel.py - Exportar Matching a Excel para Validación
=====================================================================

Exporta los resultados del matching a Excel con todas las columnas
necesarias para validación manual.

Input: JSON del paso 4 (04_resultado_final_*.json)
Output: Excel con:
  - ID, título, área, seniority
  - Skills extraídas
  - Ocupación resultado (ISCO + label)
  - Alternativas
  - Columna vacía para "ocupación esperada" (validación manual)

Uso:
    python export_matching_excel.py --input exports/matching_optimization/04_resultado_final_*.json
    python export_matching_excel.py --input ... --output mi_archivo.xlsx
"""

import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent.parent


def cargar_resultados(input_path: str) -> list:
    """Carga resultados del paso 4."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_skills_originales(skills_path: str = None) -> dict:
    """Carga skills del paso 1 si está disponible."""
    if skills_path:
        try:
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {r['id_oferta']: r.get('skills', []) for r in data}
        except:
            pass
    return {}


def generar_dataframe(resultados: list, skills_dict: dict = None) -> pd.DataFrame:
    """Genera DataFrame para Excel."""
    rows = []

    for r in resultados:
        id_oferta = r['id_oferta']
        rf = r.get('resultado_final') or {}
        alts = r.get('alternativas', [])

        # Skills (del paso 1 si disponible)
        if skills_dict and id_oferta in skills_dict:
            skills_list = skills_dict[id_oferta]
            skills_str = "; ".join([
                s.get('skill_esco', s.get('skill_label', '?'))
                for s in skills_list[:10]
            ])
        else:
            skills_str = "; ".join(rf.get('skills_matched', [])[:10])

        # Alternativas
        alt1 = alts[0] if len(alts) > 0 else {}
        alt2 = alts[1] if len(alts) > 1 else {}
        alt3 = alts[2] if len(alts) > 2 else {}

        row = {
            'id_oferta': id_oferta,
            'titulo_limpio': r.get('titulo_limpio', ''),
            'area_funcional': r.get('area_funcional', ''),
            'nivel_seniority': r.get('nivel_seniority', ''),

            # Resultado
            'isco_resultado': rf.get('isco_code', ''),
            'ocupacion_resultado': rf.get('esco_label', ''),
            'score_combinado': rf.get('combined_score', ''),
            'score_skills': rf.get('score_skills', ''),
            'score_semantico': rf.get('score_semantico', ''),
            'metodo': rf.get('metodo', ''),

            # Skills extraídas
            'skills_extraidas': skills_str,

            # Alternativas
            'alt1_isco': alt1.get('isco_code', ''),
            'alt1_ocupacion': alt1.get('esco_label', ''),
            'alt1_score': alt1.get('combined_score', ''),

            'alt2_isco': alt2.get('isco_code', ''),
            'alt2_ocupacion': alt2.get('esco_label', ''),

            'alt3_isco': alt3.get('isco_code', ''),
            'alt3_ocupacion': alt3.get('esco_label', ''),

            # Regla aplicada
            'regla_negocio': r.get('regla_aplicada', ''),

            # Para validación manual
            'isco_esperado': '',
            'ocupacion_esperada': '',
            'es_correcto': '',
            'comentarios': ''
        }

        rows.append(row)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description='Exportar matching a Excel')
    parser.add_argument('--input', '-i', type=str, required=True, help='JSON del paso 4')
    parser.add_argument('--skills', '-s', type=str, default=None, help='JSON del paso 1 (opcional)')
    parser.add_argument('--output', '-o', type=str, default=None, help='Archivo de salida')
    args = parser.parse_args()

    print("=" * 60)
    print("EXPORTAR MATCHING A EXCEL")
    print("=" * 60)
    print(f"Input: {args.input}")

    # Cargar datos
    print("\nCargando resultados...")
    resultados = cargar_resultados(args.input)
    print(f"Ofertas cargadas: {len(resultados)}")

    # Cargar skills si disponible
    skills_dict = {}
    if args.skills:
        print(f"Cargando skills de: {args.skills}")
        skills_dict = cargar_skills_originales(args.skills)
        print(f"Skills para {len(skills_dict)} ofertas")

    # Generar DataFrame
    print("\nGenerando Excel...")
    df = generar_dataframe(resultados, skills_dict)

    # Guardar
    output_dir = BASE_DIR / "exports" / "matching_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"Matching_Gold_Set_100_{timestamp}.xlsx"

    # Exportar con formato
    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Matching_Resultados', index=False)

        # Ajustar anchos de columna
        worksheet = writer.sheets['Matching_Resultados']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            max_len = min(max_len, 50)  # Máximo 50 caracteres
            worksheet.column_dimensions[chr(65 + idx) if idx < 26 else 'A' + chr(65 + idx - 26)].width = max_len

    print(f"\nExcel generado: {output_path}")
    print(f"Registros: {len(df)}")
    print(f"Columnas: {len(df.columns)}")

    # Resumen
    print("\n" + "=" * 60)
    print("COLUMNAS PARA VALIDACIÓN")
    print("=" * 60)
    print("- isco_resultado / ocupacion_resultado: Lo que predijo el sistema")
    print("- isco_esperado / ocupacion_esperada: Completar manualmente")
    print("- es_correcto: Marcar SI/NO")
    print("- comentarios: Notas adicionales")
    print("=" * 60)


if __name__ == "__main__":
    main()
