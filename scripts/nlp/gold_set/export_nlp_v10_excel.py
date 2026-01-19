# -*- coding: utf-8 -*-
"""
Exportar NLP v10.0.0 a Excel para revision manual
==================================================
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"
EXPORTS_PATH = Path(__file__).parent.parent.parent.parent / "exports"

def export_nlp_to_excel():
    """Exporta registros NLP v10.0.0 a Excel."""

    EXPORTS_PATH.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))

    # Query con campos relevantes para revision
    query = """
        SELECT
            n.id_oferta,
            o.titulo as titulo_original,
            n.titulo_limpio,
            o.empresa,
            n.provincia,
            n.localidad,
            n.modalidad,
            n.jornada_laboral,
            n.nivel_seniority,
            n.area_funcional,
            n.experiencia_min_anios,
            n.experiencia_max_anios,
            n.nivel_educativo,
            n.carrera_especifica,
            n.skills_tecnicas_list,
            n.soft_skills_list,
            n.tareas_explicitas,
            n.sector_empresa,
            n.tipo_contrato,
            n.salario_min,
            n.salario_max,
            n.moneda,
            n.beneficios_list,
            n.nlp_version,
            o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.nlp_version = '10.0.0'
        ORDER BY n.id_oferta
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Registros a exportar: {len(df)}")

    # Truncar descripcion para Excel (max 32000 chars)
    df['descripcion'] = df['descripcion'].apply(
        lambda x: x[:5000] + '...' if x and len(x) > 5000 else x
    )

    # Generar nombre archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"NLP_v10_revision_{timestamp}.xlsx"
    filepath = EXPORTS_PATH / filename

    # Exportar a Excel con formato
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='NLP_v10', index=False)

        # Ajustar anchos de columna
        worksheet = writer.sheets['NLP_v10']

        column_widths = {
            'A': 12,  # id_oferta
            'B': 40,  # titulo_original
            'C': 35,  # titulo_limpio
            'D': 25,  # empresa
            'E': 15,  # provincia
            'F': 20,  # localidad
            'G': 12,  # modalidad
            'H': 12,  # jornada
            'I': 15,  # seniority
            'J': 20,  # area_funcional
            'K': 8,   # exp_min
            'L': 8,   # exp_max
            'M': 15,  # educacion
            'N': 30,  # carrera
            'O': 50,  # skills_tecnicas
            'P': 40,  # soft_skills
            'Q': 60,  # tareas
            'R': 20,  # sector
            'S': 15,  # tipo_contrato
            'T': 12,  # salario_min
            'U': 12,  # salario_max
            'V': 8,   # moneda
            'W': 40,  # beneficios
            'X': 10,  # nlp_version
            'Y': 80,  # descripcion
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

    print(f"\nExcel generado: {filepath}")
    print(f"Tamaño: {filepath.stat().st_size / 1024:.1f} KB")

    return filepath

if __name__ == "__main__":
    export_nlp_to_excel()
