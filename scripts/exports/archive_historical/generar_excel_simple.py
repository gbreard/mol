#!/usr/bin/env python3
"""
Generador de Excel Simple para Validación Humana
=================================================

Una sola hoja con:
- Título, Empresa, URL, Descripción Original
- Todas las variables extraídas por v5.1
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    return sqlite3.connect(db_path)


def cargar_ids_ab_test():
    """Carga los IDs del archivo de A/B test"""
    ids_file = Path(__file__).parent / "ids_for_ab_test.txt"
    with open(ids_file, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]


def formatear_lista(valor: Any) -> str:
    """Formatea listas JSON para display en Excel"""
    if valor is None:
        return ""

    if isinstance(valor, list):
        if len(valor) == 0:
            return ""
        return "; ".join([str(item) for item in valor])

    if isinstance(valor, str):
        if valor.startswith('[') and valor.endswith(']'):
            try:
                lista = json.loads(valor)
                if len(lista) == 0:
                    return ""
                return "; ".join([str(item) for item in lista])
            except:
                pass

    return str(valor) if valor else ""


def obtener_datos_oferta(conn, id_oferta: int) -> Dict[str, Any]:
    """Obtiene datos de la oferta con extracción v5.1"""
    cursor = conn.cursor()

    # Datos originales
    cursor.execute("""
        SELECT
            id_oferta,
            titulo,
            empresa,
            descripcion,
            localizacion,
            modalidad_trabajo,
            url_oferta,
            fecha_publicacion_original
        FROM ofertas
        WHERE id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    if not row:
        return None

    oferta = {
        "ID": row[0],
        "Título": row[1],
        "Empresa": row[2],
        "Descripción Original": row[3],
        "Localización": row[4],
        "Modalidad Trabajo": row[5],
        "URL": row[6],
        "Fecha Publicación": row[7]
    }

    # Extracción v5.1
    cursor.execute("""
        SELECT
            extracted_data,
            quality_score
        FROM ofertas_nlp_history
        WHERE id_oferta = ? AND nlp_version = '5.1.0'
        ORDER BY processed_at DESC
        LIMIT 1
    """, (id_oferta,))

    row = cursor.fetchone()
    if row and row[0]:
        extracted = json.loads(row[0])

        # Agregar Quality Score
        oferta["Quality Score"] = row[1]

        # Agregar cada campo extraído
        oferta["Experiencia Min (años)"] = extracted.get("experiencia_min_anios", "")
        oferta["Experiencia Max (años)"] = extracted.get("experiencia_max_anios", "")
        oferta["Nivel Educativo"] = extracted.get("nivel_educativo", "")
        oferta["Estado Educativo"] = extracted.get("estado_educativo", "")
        oferta["Carrera Específica"] = extracted.get("carrera_especifica", "")
        oferta["Idioma Principal"] = extracted.get("idioma_principal", "")
        oferta["Nivel Idioma"] = extracted.get("nivel_idioma_principal", "")
        oferta["Skills Técnicas"] = formatear_lista(extracted.get("skills_tecnicas_list"))
        oferta["Soft Skills"] = formatear_lista(extracted.get("soft_skills_list"))
        oferta["Certificaciones"] = formatear_lista(extracted.get("certificaciones_list"))
        oferta["Salario Min"] = extracted.get("salario_min", "")
        oferta["Salario Max"] = extracted.get("salario_max", "")
        oferta["Moneda"] = extracted.get("moneda", "")
        oferta["Beneficios"] = formatear_lista(extracted.get("beneficios_list"))
        oferta["Requisitos Excluyentes"] = formatear_lista(extracted.get("requisitos_excluyentes_list"))
        oferta["Requisitos Deseables"] = formatear_lista(extracted.get("requisitos_deseables_list"))
        oferta["Jornada Laboral"] = extracted.get("jornada_laboral", "")
        oferta["Horario Flexible"] = extracted.get("horario_flexible", "")

    return oferta


def main():
    print("=" * 70)
    print("GENERADOR DE EXCEL SIMPLE PARA VALIDACIÓN HUMANA")
    print("=" * 70)
    print()

    conn = conectar_db()

    print("[1/3] Cargando IDs del A/B test...")
    ids_ab_test = cargar_ids_ab_test()
    print(f"      {len(ids_ab_test)} ofertas en el conjunto de test")

    print()
    print("[2/3] Extrayendo datos de ofertas...")
    ofertas = []

    for i, id_oferta in enumerate(ids_ab_test, 1):
        if i % 10 == 0:
            print(f"      Procesadas: {i}/{len(ids_ab_test)}")

        datos = obtener_datos_oferta(conn, id_oferta)
        if datos:
            ofertas.append(datos)

    conn.close()

    print(f"      [OK] {len(ofertas)} ofertas con datos v5.1")

    print()
    print("[3/3] Generando Excel...")

    # Crear DataFrame con orden específico de columnas
    columnas_orden = [
        "ID",
        "Título",
        "Empresa",
        "URL",
        "Localización",
        "Modalidad Trabajo",
        "Fecha Publicación",
        "Descripción Original",
        "Quality Score",
        "Experiencia Min (años)",
        "Experiencia Max (años)",
        "Nivel Educativo",
        "Estado Educativo",
        "Carrera Específica",
        "Idioma Principal",
        "Nivel Idioma",
        "Skills Técnicas",
        "Soft Skills",
        "Certificaciones",
        "Salario Min",
        "Salario Max",
        "Moneda",
        "Beneficios",
        "Requisitos Excluyentes",
        "Requisitos Deseables",
        "Jornada Laboral",
        "Horario Flexible"
    ]

    df = pd.DataFrame(ofertas)

    # Reordenar columnas
    columnas_presentes = [col for col in columnas_orden if col in df.columns]
    df = df[columnas_presentes]

    # Guardar Excel
    output_file = Path(__file__).parent / "validacion_humana_simple.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Validación', index=False)

        # Ajustar anchos de columna
        worksheet = writer.sheets['Validación']

        # Anchos específicos para columnas importantes
        anchos_columnas = {
            'A': 8,   # ID
            'B': 40,  # Título
            'C': 25,  # Empresa
            'D': 50,  # URL
            'E': 20,  # Localización
            'F': 15,  # Modalidad
            'G': 15,  # Fecha
            'H': 80,  # Descripción (MUY ANCHA)
            'I': 10,  # Quality Score
        }

        for col_letter, width in anchos_columnas.items():
            worksheet.column_dimensions[col_letter].width = width

        # Para las demás columnas (variables extraídas), ancho moderado
        for i, col in enumerate(columnas_presentes[9:], start=10):  # Desde columna J
            col_letter = chr(64 + i)  # A=65, entonces 65+i para J,K,L...
            if i <= 26:
                worksheet.column_dimensions[col_letter].width = 30
            else:
                # Para columnas AA, AB, etc
                col_letter = 'A' + chr(64 + (i - 26))
                worksheet.column_dimensions[col_letter].width = 30

        # Congelar primera fila (encabezados)
        worksheet.freeze_panes = 'A2'

    print(f"      [OK] Archivo generado: {output_file}")

    print()
    print("=" * 70)
    print("EXCEL DE VALIDACIÓN GENERADO EXITOSAMENTE")
    print("=" * 70)
    print()
    print(f"Ofertas incluidas: {len(ofertas)}")
    print(f"Archivo: {output_file.name}")
    print()
    print("Estructura del archivo:")
    print("  - UNA SOLA HOJA: 'Validación'")
    print("  - Columnas básicas: ID, Título, Empresa, URL, Descripción Original")
    print("  - Columnas extraídas: Todas las variables parseadas por v5.1")
    print()
    print("Uso:")
    print("  1. Abre el archivo en Excel")
    print("  2. Lee la columna 'Descripción Original'")
    print("  3. Verifica las variables extraídas en las columnas siguientes")
    print("  4. Anota observaciones directamente en el Excel si es necesario")
    print()


if __name__ == '__main__':
    main()
