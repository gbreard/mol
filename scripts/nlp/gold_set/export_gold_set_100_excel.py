# -*- coding: utf-8 -*-
"""
Exportar Gold Set NLP 100 a Excel
=================================
Genera un Excel con todos los campos NLP de las 100 ofertas del Gold Set NLP
para validación manual post-reprocesamiento con GAPS corregidos.
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
BASE_DIR = Path(__file__).parent.parent.parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 80)
    print("EXPORTAR GOLD SET NLP 100 A EXCEL")
    print("=" * 80)

    # Cargar Gold Set IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    print(f"\nGold Set NLP: {len(ids)} ofertas")

    # Conectar BD
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query - obtener todos los campos NLP + datos originales
    placeholders = ','.join(['?' for _ in ids])
    query = f"""
        SELECT
            n.id_oferta,
            o.titulo as titulo_original,
            o.empresa,
            o.localizacion as ubicacion_scraping,
            n.titulo_limpio,
            n.provincia,
            n.localidad,
            n.modalidad,
            n.nivel_seniority,
            n.area_funcional,
            n.experiencia_min_anios,
            n.experiencia_max_anios,
            n.tiene_gente_cargo,
            n.sector_empresa,
            n.tipo_contrato,
            n.jornada_laboral,
            n.salario_min,
            n.salario_max,
            n.moneda,
            n.nivel_educativo,
            n.skills_tecnicas_list,
            n.soft_skills_list,
            n.tecnologias_list,
            n.herramientas_list,
            n.tareas_explicitas,
            n.mision_rol,
            n.requerimiento_edad,
            n.requerimiento_sexo,
            n.nlp_version
        FROM ofertas_nlp n
        LEFT JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
        ORDER BY n.id_oferta
    """

    cursor.execute(query, ids)
    rows = cursor.fetchall()

    print(f"Registros encontrados: {len(rows)}")

    # Convertir a DataFrame
    data = [dict(row) for row in rows]
    df = pd.DataFrame(data)

    # Crear Excel con múltiples hojas
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"NLP_Gold_Set_100_{timestamp}.xlsx"

    with pd.ExcelWriter(str(output_file), engine='openpyxl') as writer:

        # Hoja 1: VALIDACION - campos clave para revisar
        cols_validacion = [
            'id_oferta', 'titulo_original', 'titulo_limpio',
            'ubicacion_scraping', 'provincia', 'localidad',
            'modalidad', 'nivel_seniority', 'area_funcional',
            'experiencia_min_anios', 'experiencia_max_anios',
            'nlp_version'
        ]
        cols_disponibles = [c for c in cols_validacion if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='01_Validacion', index=False)
        print(f"\n[1] Validación: {len(cols_disponibles)} columnas")

        # Hoja 2: UBICACION - verificar Capital Federal -> CABA
        cols_ubicacion = [
            'id_oferta', 'titulo_original', 'ubicacion_scraping',
            'provincia', 'localidad'
        ]
        cols_disponibles = [c for c in cols_ubicacion if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='02_Ubicacion', index=False)
        print(f"[2] Ubicación: {len(cols_disponibles)} columnas")

        # Hoja 3: EXPERIENCIA - verificar min <= max
        cols_exp = [
            'id_oferta', 'titulo_limpio', 'nivel_seniority',
            'experiencia_min_anios', 'experiencia_max_anios',
            'tiene_gente_cargo'
        ]
        cols_disponibles = [c for c in cols_exp if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='03_Experiencia', index=False)
        print(f"[3] Experiencia: {len(cols_disponibles)} columnas")

        # Hoja 4: SKILLS
        cols_skills = [
            'id_oferta', 'titulo_limpio', 'skills_tecnicas_list',
            'soft_skills_list', 'tecnologias_list', 'herramientas_list'
        ]
        cols_disponibles = [c for c in cols_skills if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='04_Skills', index=False)
        print(f"[4] Skills: {len(cols_disponibles)} columnas")

        # Hoja 5: TAREAS
        cols_tareas = [
            'id_oferta', 'titulo_limpio', 'tareas_explicitas', 'mision_rol'
        ]
        cols_disponibles = [c for c in cols_tareas if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='05_Tareas', index=False)
        print(f"[5] Tareas: {len(cols_disponibles)} columnas")

        # Hoja 6: REQUISITOS
        cols_req = [
            'id_oferta', 'titulo_limpio', 'nivel_educativo',
            'requerimiento_edad', 'requerimiento_sexo',
            'tipo_contrato', 'jornada_laboral'
        ]
        cols_disponibles = [c for c in cols_req if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='06_Requisitos', index=False)
        print(f"[6] Requisitos: {len(cols_disponibles)} columnas")

        # Hoja 7: SALARIO
        cols_salario = [
            'id_oferta', 'titulo_limpio', 'salario_min',
            'salario_max', 'moneda'
        ]
        cols_disponibles = [c for c in cols_salario if c in df.columns]
        df[cols_disponibles].to_excel(writer, sheet_name='07_Salario', index=False)
        print(f"[7] Salario: {len(cols_disponibles)} columnas")

        # Hoja 8: ESTADISTICAS DE COBERTURA
        stats = []
        campos_analizar = [
            'provincia', 'localidad', 'modalidad', 'nivel_seniority',
            'area_funcional', 'experiencia_min_anios', 'titulo_limpio',
            'skills_tecnicas_list', 'soft_skills_list', 'tareas_explicitas',
            'sector_empresa', 'nivel_educativo'
        ]
        for campo in campos_analizar:
            if campo in df.columns:
                total = len(df)
                # Contar vacíos: None, '', 'null', '[]'
                vacios = df[campo].isna().sum()
                vacios += (df[campo] == '').sum()
                vacios += (df[campo] == 'null').sum()
                vacios += (df[campo] == '[]').sum()
                completos = total - vacios
                pct = (completos / total * 100) if total > 0 else 0
                stats.append({
                    'campo': campo,
                    'total': total,
                    'completos': int(completos),
                    'vacios': int(vacios),
                    'cobertura_pct': round(pct, 1),
                    'estado': 'OK' if pct >= 80 else 'REVISAR' if pct >= 50 else 'CRITICO'
                })

        df_stats = pd.DataFrame(stats)
        df_stats.to_excel(writer, sheet_name='08_Estadisticas', index=False)
        print(f"[8] Estadísticas: {len(stats)} campos")

        # Hoja 9: RAW COMPLETO
        df.to_excel(writer, sheet_name='09_Raw_Completo', index=False)
        print(f"[9] Raw completo: {len(df.columns)} columnas")

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
