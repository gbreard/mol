#!/usr/bin/env python3
"""
Generador de Excel para Validación Humana
==========================================

Genera un archivo Excel con las ofertas del A/B test para validación manual.
Incluye descripción original y todas las variables extraídas por v4.0 y v5.1
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    return sqlite3.connect(db_path)


def cargar_ids_ab_test():
    """Carga los IDs del archivo de A/B test"""
    ids_file = Path(__file__).parent / "ids_for_ab_test.txt"
    with open(ids_file, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]


def obtener_datos_oferta(conn, id_oferta: int) -> Dict[str, Any]:
    """
    Obtiene todos los datos de una oferta: original + extracciones v4 y v5.1
    """
    cursor = conn.cursor()

    # Datos originales de la oferta
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

    oferta_data = {
        "id_oferta": row[0],
        "titulo": row[1],
        "empresa": row[2],
        "descripcion": row[3],
        "localizacion": row[4],
        "modalidad_trabajo": row[5],
        "url_oferta": row[6],
        "fecha_publicacion": row[7]
    }

    # Extracciones v4.0 y v5.1
    cursor.execute("""
        SELECT
            nlp_version,
            extracted_data,
            quality_score,
            confidence_score
        FROM ofertas_nlp_history
        WHERE id_oferta = ?
        ORDER BY processed_at DESC
    """, (id_oferta,))

    extracciones = {}
    for row in cursor.fetchall():
        version = row[0]
        extracciones[version] = {
            "data": json.loads(row[1]) if row[1] else {},
            "quality_score": row[2],
            "confidence_score": row[3]
        }

    oferta_data["v4"] = extracciones.get("v4.0.0")
    oferta_data["v51"] = extracciones.get("5.1.0")

    return oferta_data


def formatear_lista(valor: Any) -> str:
    """Formatea listas JSON para display"""
    if valor is None:
        return ""

    if isinstance(valor, str):
        if valor.startswith('[') and valor.endswith(']'):
            try:
                lista = json.loads(valor)
                if len(lista) == 0:
                    return ""
                return ", ".join([str(item) for item in lista])
            except:
                pass

    return str(valor) if valor else ""


def generar_excel(ofertas: List[Dict[str, Any]], output_file: Path):
    """
    Genera el Excel con múltiples hojas
    """

    # Campos a comparar
    campos = [
        ("experiencia_min_anios", "Exp Min (años)"),
        ("experiencia_max_anios", "Exp Max (años)"),
        ("nivel_educativo", "Nivel Educativo"),
        ("estado_educativo", "Estado Educativo"),
        ("carrera_especifica", "Carrera"),
        ("idioma_principal", "Idioma"),
        ("nivel_idioma_principal", "Nivel Idioma"),
        ("skills_tecnicas_list", "Skills Técnicas"),
        ("soft_skills_list", "Soft Skills"),
        ("certificaciones_list", "Certificaciones"),
        ("salario_min", "Salario Min"),
        ("salario_max", "Salario Max"),
        ("moneda", "Moneda"),
        ("beneficios_list", "Beneficios"),
        ("requisitos_excluyentes_list", "Req. Excluyentes"),
        ("requisitos_deseables_list", "Req. Deseables"),
        ("jornada_laboral", "Jornada"),
        ("horario_flexible", "Horario Flexible")
    ]

    # HOJA 1: COMPARACIÓN LADO A LADO
    rows_comparacion = []

    for oferta in ofertas:
        v4_data = oferta['v4']['data'] if oferta['v4'] else {}
        v51_data = oferta['v51']['data'] if oferta['v51'] else {}

        row = {
            'ID': oferta['id_oferta'],
            'Título': oferta['titulo'],
            'Empresa': oferta['empresa'],
            'Localización': oferta['localizacion'],
            'URL': oferta['url_oferta'],
            'Fecha Publicación': oferta['fecha_publicacion'],
            '--- SCORES ---': '---',
            'QS v4.0': oferta['v4']['quality_score'] if oferta['v4'] else None,
            'QS v5.1': oferta['v51']['quality_score'] if oferta['v51'] else None,
            'Delta QS': (oferta['v51']['quality_score'] - oferta['v4']['quality_score']) if (oferta['v4'] and oferta['v51']) else None,
        }

        # Agregar campos comparados lado a lado
        for campo_key, campo_label in campos:
            v4_val = v4_data.get(campo_key)
            v51_val = v51_data.get(campo_key)

            # Formatear valores
            v4_display = formatear_lista(v4_val)
            v51_display = formatear_lista(v51_val)

            row[f'{campo_label} (v4.0)'] = v4_display
            row[f'{campo_label} (v5.1)'] = v51_display

            # Indicador de diferencia
            if v4_val != v51_val:
                if v4_val is None and v51_val is not None:
                    row[f'Δ {campo_label}'] = 'MEJORA'
                elif v4_val is not None and v51_val is None:
                    row[f'Δ {campo_label}'] = 'PERDIDA'
                else:
                    row[f'Δ {campo_label}'] = 'DIFERENTE'
            else:
                row[f'Δ {campo_label}'] = '='

        rows_comparacion.append(row)

    df_comparacion = pd.DataFrame(rows_comparacion)

    # HOJA 2: DESCRIPCIONES ORIGINALES
    rows_descripciones = []

    for oferta in ofertas:
        rows_descripciones.append({
            'ID': oferta['id_oferta'],
            'Título': oferta['titulo'],
            'Empresa': oferta['empresa'],
            'Descripción Original': oferta['descripcion']
        })

    df_descripciones = pd.DataFrame(rows_descripciones)

    # HOJA 3: SOLO v5.1 (para revisión más fácil)
    rows_v51 = []

    for oferta in ofertas:
        if not oferta['v51']:
            continue

        v51_data = oferta['v51']['data']

        row = {
            'ID': oferta['id_oferta'],
            'Título': oferta['titulo'],
            'Empresa': oferta['empresa'],
            'Quality Score': oferta['v51']['quality_score'],
        }

        for campo_key, campo_label in campos:
            val = v51_data.get(campo_key)
            row[campo_label] = formatear_lista(val)

        row['NOTAS'] = ''  # Columna para anotaciones manuales

        rows_v51.append(row)

    df_v51 = pd.DataFrame(rows_v51)

    # HOJA 4: SOLO DIFERENCIAS
    rows_diferencias = []

    for oferta in ofertas:
        if not oferta['v4'] or not oferta['v51']:
            continue

        v4_data = oferta['v4']['data']
        v51_data = oferta['v51']['data']

        tiene_diferencias = False
        campos_diferentes = []

        for campo_key, campo_label in campos:
            v4_val = v4_data.get(campo_key)
            v51_val = v51_data.get(campo_key)

            if v4_val != v51_val:
                tiene_diferencias = True

                tipo_dif = 'DIFERENTE'
                if v4_val is None and v51_val is not None:
                    tipo_dif = 'MEJORA'
                elif v4_val is not None and v51_val is None:
                    tipo_dif = 'PERDIDA'

                campos_diferentes.append(f"{campo_label}: {tipo_dif}")

        if tiene_diferencias:
            row = {
                'ID': oferta['id_oferta'],
                'Título': oferta['titulo'],
                'Empresa': oferta['empresa'],
                'QS v4.0': oferta['v4']['quality_score'],
                'QS v5.1': oferta['v51']['quality_score'],
                'Delta QS': oferta['v51']['quality_score'] - oferta['v4']['quality_score'],
                'Campos Diferentes': '; '.join(campos_diferentes),
                'OBSERVACIONES': ''  # Para anotaciones
            }
            rows_diferencias.append(row)

    df_diferencias = pd.DataFrame(rows_diferencias)

    # HOJA 5: RESUMEN ESTADÍSTICO
    total_ofertas = len(ofertas)
    con_v4 = sum(1 for o in ofertas if o['v4'])
    con_v51 = sum(1 for o in ofertas if o['v51'])

    stats_rows = [
        ['Métrica', 'Valor'],
        ['Total Ofertas en A/B Test', total_ofertas],
        ['Ofertas con v4.0', con_v4],
        ['Ofertas con v5.1', con_v51],
        ['', ''],
        ['Quality Score Promedio v4.0', sum(o['v4']['quality_score'] for o in ofertas if o['v4']) / con_v4 if con_v4 > 0 else 0],
        ['Quality Score Promedio v5.1', sum(o['v51']['quality_score'] for o in ofertas if o['v51']) / con_v51 if con_v51 > 0 else 0],
        ['', ''],
        ['Campos Analizados', len(campos)],
        ['', ''],
        ['ANÁLISIS POR CAMPO', ''],
        ['Campo', 'v4.0', 'v5.1', 'Delta']
    ]

    # Agregar stats por campo
    for campo_key, campo_label in campos:
        count_v4 = sum(1 for o in ofertas if o['v4'] and o['v4']['data'].get(campo_key) is not None)
        count_v51 = sum(1 for o in ofertas if o['v51'] and o['v51']['data'].get(campo_key) is not None)
        delta = count_v51 - count_v4

        stats_rows.append([campo_label, count_v4, count_v51, delta])

    df_stats = pd.DataFrame(stats_rows)

    # Guardar todo en Excel
    print(f"      Guardando Excel con {len(ofertas)} ofertas...")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Hoja 1: Comparación
        df_comparacion.to_excel(writer, sheet_name='Comparación v4 vs v5.1', index=False)

        # Hoja 2: Descripciones
        df_descripciones.to_excel(writer, sheet_name='Descripciones Originales', index=False)

        # Hoja 3: Solo v5.1
        df_v51.to_excel(writer, sheet_name='Extracción v5.1', index=False)

        # Hoja 4: Solo diferencias
        df_diferencias.to_excel(writer, sheet_name='Solo Diferencias', index=False)

        # Hoja 5: Estadísticas
        df_stats.to_excel(writer, sheet_name='Resumen Estadístico', index=False, header=False)

        # Ajustar anchos de columna
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]

            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 80)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Congelar primera fila
            worksheet.freeze_panes = 'A2'


def main():
    print("=" * 80)
    print("GENERADOR DE EXCEL PARA VALIDACIÓN HUMANA")
    print("=" * 80)
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
        if datos and datos.get('v51'):  # Solo incluir ofertas con v5.1
            ofertas.append(datos)

    conn.close()

    print(f"      [OK] {len(ofertas)} ofertas con datos completos")

    print()
    print("[3/3] Generando Excel...")
    output_file = Path(__file__).parent / "validacion_humana_v51.xlsx"
    generar_excel(ofertas, output_file)

    print(f"      [OK] Archivo generado: {output_file}")
    print()
    print("=" * 80)
    print("EXCEL DE VALIDACIÓN GENERADO EXITOSAMENTE")
    print("=" * 80)
    print()
    print(f"📊 Ofertas incluidas: {len(ofertas)}")
    print(f"📁 Archivo: {output_file.name}")
    print()
    print("Estructura del archivo:")
    print("  📄 Hoja 1: Comparación v4 vs v5.1 (lado a lado)")
    print("  📄 Hoja 2: Descripciones Originales (texto completo)")
    print("  📄 Hoja 3: Extracción v5.1 (solo nueva versión)")
    print("  📄 Hoja 4: Solo Diferencias (para revisión rápida)")
    print("  📄 Hoja 5: Resumen Estadístico")
    print()
    print("Indicadores en columnas Delta:")
    print("  MEJORA:     v5.1 agregó un campo que v4.0 no tenía")
    print("  PERDIDA:    v5.1 perdió un campo que v4.0 sí tenía")
    print("  DIFERENTE:  Ambos tienen valor pero difieren")
    print("  =:          Sin cambios")
    print()
    print("Instrucciones:")
    print("  1. Abre el archivo en Excel o LibreOffice")
    print("  2. Revisa la hoja 'Solo Diferencias' primero")
    print("  3. Para cada oferta con diferencias, ve a 'Comparación' y 'Descripciones'")
    print("  4. Anota tus observaciones en las columnas de NOTAS/OBSERVACIONES")
    print()


if __name__ == '__main__':
    main()
