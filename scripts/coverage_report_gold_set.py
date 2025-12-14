# -*- coding: utf-8 -*-
"""
Reporte de Cobertura NLP - Gold Set
===================================

Genera reporte de cobertura de campos NLP para el Gold Set.
"""

import sqlite3
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Cargar Gold Set IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    ids = [str(g['id_oferta']) for g in gold_data]

    # Campos críticos organizados por bloque (Schema v5)
    campos_por_bloque = {
        "Empresa": ['sector_empresa', 'empresa_tamanio', 'rubro_empresa', 'cliente_final'],
        "Ubicacion": ['provincia', 'localidad', 'modalidad', 'requiere_movilidad_propia', 'zona_residencia_req'],
        "Experiencia": ['experiencia_min_anios', 'experiencia_max_anios', 'experiencia_excluyente', 'experiencia_sector'],
        "Educacion": ['nivel_educativo', 'titulo_requerido', 'nivel_educativo_excluyente', 'orientacion_estudios'],
        "Skills": ['skills_tecnicas_list', 'soft_skills_list', 'herramientas_list', 'conocimientos_especificos_list'],
        "Idiomas": ['idioma_principal', 'nivel_idioma_principal', 'idioma_excluyente'],
        "Rol": ['area_funcional', 'nivel_seniority', 'tiene_gente_cargo', 'mision_rol'],
        "Condiciones": ['tipo_contrato', 'jornada_laboral', 'horario_especifico', 'dias_trabajo_list'],
        "Compensacion": ['salario_min', 'salario_max', 'tiene_comisiones', 'tiene_bonos', 'pide_pretension_salarial'],
        "Beneficios": ['beneficios_list', 'tiene_cobertura_salud', 'tiene_capacitacion', 'tiene_crecimiento'],
        "Licencias": ['licencia_conducir', 'tipo_licencia', 'licencia_autoelevador'],
        "Calidad": ['calidad_redaccion', 'tiene_errores_tipeo', 'es_republica'],
        "Certificaciones": ['certificaciones_requeridas_json', 'certificaciones_deseables_list'],
        "Cond_Especiales": ['trabajo_nocturno', 'trabajo_turnos_rotativos', 'trabajo_en_altura']
    }

    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columnas_existentes = {row[1] for row in cursor.fetchall()}

    print("=" * 90)
    print("REPORTE DE COBERTURA - NLP Schema v5")
    print(f"Gold Set: {len(ids)} casos")
    print("=" * 90)
    print()

    # Mostrar distribución por nlp_version
    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f"""
        SELECT nlp_version, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
        GROUP BY nlp_version
        ORDER BY cnt DESC
    """, ids)

    print("Distribución por NLP Version:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} ofertas")
    print()

    # Header del reporte
    print(f"{'BLOQUE':<15} | {'CAMPO':<35} | {'CON_VALOR':>10} | {'NULL':>6} | {'%':>6}")
    print("-" * 90)

    total_campos = 0
    total_con_valor = 0
    total_evaluados = 0

    for bloque, campos in campos_por_bloque.items():
        for campo in campos:
            if campo not in columnas_existentes:
                print(f"{bloque:<15} | {campo:<35} | {'N/A':>10} | {'---':>6} | {'---':>6}  [NO EXISTE]")
                continue

            total_campos += 1

            query = f"""
                SELECT
                    COUNT(CASE WHEN [{campo}] IS NOT NULL AND [{campo}] != '' AND [{campo}] != '[]' THEN 1 END),
                    COUNT(CASE WHEN [{campo}] IS NULL OR [{campo}] = '' OR [{campo}] = '[]' THEN 1 END)
                FROM ofertas_nlp
                WHERE id_oferta IN ({placeholders})
            """
            cursor.execute(query, ids)
            row = cursor.fetchone()
            con_valor = row[0] or 0
            sin_valor = row[1] or 0
            total = con_valor + sin_valor

            if total == 0:
                print(f"{bloque:<15} | {campo:<35} | {'0':>10} | {'0':>6} | {'0.0%':>6}")
                continue

            pct = (con_valor / total * 100)
            total_con_valor += con_valor
            total_evaluados += total

            # Estado visual
            if pct >= 80:
                status = "OK"
            elif pct >= 50:
                status = "MEDIO"
            elif pct > 0:
                status = "BAJO"
            else:
                status = "VACIO"

            print(f"{bloque:<15} | {campo:<35} | {con_valor:>10} | {sin_valor:>6} | {pct:>5.1f}%  [{status}]")

    print("-" * 90)

    # Resumen
    pct_total = (total_con_valor / total_evaluados * 100) if total_evaluados > 0 else 0
    print()
    print("=" * 90)
    print("RESUMEN")
    print("=" * 90)
    print(f"  Campos evaluados:    {total_campos}")
    print(f"  Registros con valor: {total_con_valor}/{total_evaluados}")
    print(f"  Cobertura promedio:  {pct_total:.1f}%")
    print()

    # Identificar campos vacios (0% cobertura)
    print("CAMPOS VACIOS (0% cobertura) - Candidatos a mejorar en prompt:")
    print("-" * 60)

    campos_vacios = []
    for bloque, campos in campos_por_bloque.items():
        for campo in campos:
            if campo not in columnas_existentes:
                campos_vacios.append((bloque, campo, "NO_EXISTE"))
                continue

            query = f"""
                SELECT COUNT(CASE WHEN [{campo}] IS NOT NULL AND [{campo}] != '' AND [{campo}] != '[]' THEN 1 END)
                FROM ofertas_nlp
                WHERE id_oferta IN ({placeholders})
            """
            cursor.execute(query, ids)
            con_valor = cursor.fetchone()[0] or 0

            if con_valor == 0:
                campos_vacios.append((bloque, campo, "VACIO"))

    for bloque, campo, status in campos_vacios:
        print(f"  [{status:>9}] {bloque}.{campo}")

    conn.close()

    return campos_vacios


if __name__ == "__main__":
    main()
