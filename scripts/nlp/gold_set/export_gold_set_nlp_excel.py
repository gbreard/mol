# -*- coding: utf-8 -*-
"""
Exportar estado NLP del Gold Set a Excel
=========================================
Genera un Excel con todos los campos NLP de las 49 ofertas del Gold Set
para verificar que el postprocessor está funcionando correctamente.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("Instalando pandas...")
    import subprocess
    subprocess.run(["pip", "install", "pandas", "openpyxl"], check=True)
    import pandas as pd

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 80)
    print("EXPORTAR GOLD SET NLP A EXCEL")
    print("=" * 80)

    # Cargar Gold Set
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    ids = [str(item['id_oferta']) for item in gold_set]
    print(f"\nGold Set: {len(ids)} ofertas")

    # Conectar BD
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Campos NLP clave a exportar
    campos_clave = [
        'id_oferta', 'titulo_limpio', 'provincia', 'localidad',
        'modalidad', 'nivel_seniority', 'area_funcional',
        'experiencia_min_anios', 'experiencia_max_anios',
        'tiene_gente_cargo', 'sector_empresa', 'tipo_contrato',
        'jornada_laboral', 'rango_salarial_min', 'rango_salarial_max',
        'nivel_educativo_minimo', 'skills_tecnicas_list', 'soft_skills_list',
        'tareas_explicitas', 'mision_rol', 'nlp_version'
    ]

    # Query
    placeholders = ','.join(['?' for _ in ids])
    query = f"""
        SELECT
            n.*,
            o.titulo as titulo_original,
            o.empresa,
            o.localizacion as ubicacion_original
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
    """

    cursor.execute(query, ids)
    rows = cursor.fetchall()

    print(f"Registros encontrados en ofertas_nlp: {len(rows)}")

    # Convertir a DataFrame
    data = []
    for row in rows:
        row_dict = dict(row)
        # Agregar info del Gold Set (esco_ok, comentario)
        gold_item = next((g for g in gold_set if str(g['id_oferta']) == str(row_dict['id_oferta'])), {})
        row_dict['gold_set_esco_ok'] = gold_item.get('esco_ok', None)
        row_dict['gold_set_comentario'] = gold_item.get('comentario', '')
        row_dict['gold_set_tipo_error'] = gold_item.get('tipo_error', '')
        data.append(row_dict)

    df = pd.DataFrame(data)

    # Crear Excel con múltiples hojas
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"gold_set_nlp_{timestamp}.xlsx"

    with pd.ExcelWriter(str(output_file), engine='openpyxl') as writer:

        # Hoja 1: Resumen campos clave
        cols_resumen = [
            'id_oferta', 'titulo_original', 'titulo_limpio',
            'provincia', 'localidad', 'modalidad', 'nivel_seniority',
            'area_funcional', 'experiencia_min_anios',
            'gold_set_esco_ok', 'gold_set_tipo_error'
        ]
        cols_disponibles = [c for c in cols_resumen if c in df.columns]
        df_resumen = df[cols_disponibles].copy()
        df_resumen.to_excel(writer, sheet_name='01_Resumen', index=False)
        print(f"\n[1] Resumen: {len(cols_disponibles)} columnas")

        # Hoja 2: Campos de ubicación
        cols_ubicacion = [
            'id_oferta', 'titulo_original', 'ubicacion_original',
            'provincia', 'localidad', 'pais', 'zona_trabajo'
        ]
        cols_disponibles = [c for c in cols_ubicacion if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='02_Ubicacion', index=False)
        print(f"[2] Ubicación: {len(cols_disponibles)} columnas")

        # Hoja 3: Campos de experiencia/seniority
        cols_exp = [
            'id_oferta', 'titulo_limpio', 'nivel_seniority',
            'experiencia_min_anios', 'experiencia_max_anios',
            'experiencia_texto', 'tiene_gente_cargo'
        ]
        cols_disponibles = [c for c in cols_exp if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='03_Experiencia', index=False)
        print(f"[3] Experiencia: {len(cols_disponibles)} columnas")

        # Hoja 4: Skills
        cols_skills = [
            'id_oferta', 'titulo_limpio', 'skills_tecnicas_list',
            'soft_skills_list', 'tecnologias_list', 'idiomas_list'
        ]
        cols_disponibles = [c for c in cols_skills if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='04_Skills', index=False)
        print(f"[4] Skills: {len(cols_disponibles)} columnas")

        # Hoja 5: Campos inferidos (postprocessor)
        cols_inferidos = [
            'id_oferta', 'titulo_limpio', 'modalidad', 'nivel_seniority',
            'area_funcional', 'sector_empresa', 'tipo_contrato', 'jornada_laboral'
        ]
        cols_disponibles = [c for c in cols_inferidos if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='05_Campos_Inferidos', index=False)
        print(f"[5] Campos inferidos: {len(cols_disponibles)} columnas")

        # Hoja 6: Gold Set validación
        cols_gold = [
            'id_oferta', 'titulo_original', 'gold_set_esco_ok',
            'gold_set_tipo_error', 'gold_set_comentario'
        ]
        cols_disponibles = [c for c in cols_gold if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='06_Gold_Set_Validacion', index=False)
        print(f"[6] Gold Set: {len(cols_disponibles)} columnas")

        # Hoja 7: Estadísticas de cobertura
        stats = []
        campos_analizar = [
            'provincia', 'localidad', 'modalidad', 'nivel_seniority',
            'area_funcional', 'experiencia_min_anios', 'titulo_limpio',
            'skills_tecnicas_list', 'soft_skills_list', 'sector_empresa'
        ]
        for campo in campos_analizar:
            if campo in df.columns:
                total = len(df)
                vacios = df[campo].isna().sum() + (df[campo] == '').sum() + (df[campo] == 'null').sum()
                completos = total - vacios
                pct = (completos / total * 100) if total > 0 else 0
                stats.append({
                    'campo': campo,
                    'total': total,
                    'completos': completos,
                    'vacios': vacios,
                    'cobertura_pct': round(pct, 1),
                    'estado': 'OK' if pct >= 80 else 'REVISAR' if pct >= 50 else 'CRITICO'
                })

        df_stats = pd.DataFrame(stats)
        df_stats.to_excel(writer, sheet_name='07_Estadisticas', index=False)
        print(f"[7] Estadísticas: {len(stats)} campos analizados")

        # Hoja 8: Todos los campos (raw)
        df.to_excel(writer, sheet_name='08_Raw_Completo', index=False)
        print(f"[8] Raw completo: {len(df.columns)} columnas")

    conn.close()

    print(f"\n{'=' * 80}")
    print(f"Excel generado: {output_file}")
    print(f"{'=' * 80}")

    # Mostrar estadísticas en consola
    print("\nESTADISTICAS DE COBERTURA:")
    print("-" * 50)
    for stat in stats:
        emoji = "[OK]" if stat['estado'] == 'OK' else "[!]" if stat['estado'] == 'REVISAR' else "[X]"
        print(f"  {emoji} {stat['campo']}: {stat['cobertura_pct']}% ({stat['completos']}/{stat['total']})")

    return str(output_file)


if __name__ == "__main__":
    main()
