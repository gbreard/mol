# -*- coding: utf-8 -*-
"""
Medir Cobertura NLP v10 - Gold Set
==================================

Genera reporte de cobertura comparativo antes/después de v10.
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
    gold_ids = [str(g['id_oferta']) for g in gold_data]
    placeholders = ','.join(['?'] * len(gold_ids))

    # Campos críticos organizados por bloque
    campos = [
        # Bloque: Empresa
        ("Empresa", "sector_empresa", "TEXT"),
        ("Empresa", "rubro_empresa", "TEXT"),
        ("Empresa", "es_tercerizado", "INT"),
        ("Empresa", "empresa_tamanio", "TEXT"),

        # Bloque: Ubicación
        ("Ubicacion", "provincia", "TEXT"),
        ("Ubicacion", "localidad", "TEXT"),
        ("Ubicacion", "modalidad", "TEXT"),
        ("Ubicacion", "requiere_movilidad_propia", "INT"),

        # Bloque: Experiencia
        ("Experiencia", "experiencia_min_anios", "INT"),
        ("Experiencia", "experiencia_max_anios", "INT"),
        ("Experiencia", "experiencia_excluyente", "INT"),

        # Bloque: Educación
        ("Educacion", "nivel_educativo", "TEXT"),
        ("Educacion", "titulo_requerido", "TEXT"),
        ("Educacion", "nivel_educativo_excluyente", "INT"),

        # Bloque: Skills
        ("Skills", "skills_tecnicas_list", "JSON"),
        ("Skills", "soft_skills_list", "JSON"),
        ("Skills", "herramientas_list", "JSON"),
        ("Skills", "perfil_actitudinal_list", "JSON"),

        # Bloque: Idiomas
        ("Idiomas", "idioma_principal", "TEXT"),
        ("Idiomas", "nivel_idioma_principal", "TEXT"),
        ("Idiomas", "idioma_excluyente", "INT"),

        # Bloque: Rol
        ("Rol", "area_funcional", "TEXT"),
        ("Rol", "nivel_seniority", "TEXT"),
        ("Rol", "tiene_gente_cargo", "INT"),
        ("Rol", "mision_rol", "TEXT"),
        ("Rol", "tareas_explicitas", "JSON"),

        # Bloque: Condiciones
        ("Condiciones", "tipo_contrato", "TEXT"),
        ("Condiciones", "jornada_laboral", "TEXT"),
        ("Condiciones", "horario_especifico", "TEXT"),

        # Bloque: Compensación
        ("Compensacion", "salario_min", "INT"),
        ("Compensacion", "salario_max", "INT"),
        ("Compensacion", "tiene_comisiones", "INT"),
        ("Compensacion", "tiene_bonos", "INT"),

        # Bloque: Beneficios
        ("Beneficios", "beneficios_list", "JSON"),
        ("Beneficios", "tiene_cobertura_salud", "INT"),
        ("Beneficios", "tiene_capacitacion", "INT"),

        # Bloque: Metadatos
        ("Metadatos", "tipo_oferta", "TEXT"),
        ("Metadatos", "calidad_texto", "TEXT"),

        # Bloque: Licencias
        ("Licencias", "licencia_conducir", "INT"),
        ("Licencias", "tipo_licencia", "TEXT"),

        # Bloque: Calidad
        ("Calidad", "tiene_requisitos_discriminatorios", "INT"),
        ("Calidad", "calidad_redaccion", "TEXT"),
        ("Calidad", "es_republica", "INT"),

        # Bloque: Certificaciones
        ("Certificaciones", "certificaciones_requeridas_json", "JSON"),

        # Bloque: Cond. Especiales
        ("Cond_Especiales", "trabajo_nocturno", "INT"),
        ("Cond_Especiales", "trabajo_turnos_rotativos", "INT"),
    ]

    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columnas_existentes = {row[1] for row in cursor.fetchall()}

    print("=" * 100)
    print("REPORTE DE COBERTURA NLP v10.0.0 - GOLD SET (49 casos)")
    print("=" * 100)
    print()

    # Header
    print(f"{'BLOQUE':<15} | {'CAMPO':<35} | {'CON_VALOR':>10} | {'%':>7} | {'ESTADO':<8}")
    print("-" * 100)

    total_campos = 0
    total_con_valor = 0
    resultados = []

    current_bloque = ""
    for bloque, campo, tipo in campos:
        if campo not in columnas_existentes:
            continue

        total_campos += 1

        # Condición para considerar "con valor"
        if tipo == "JSON":
            condition = f"[{campo}] IS NOT NULL AND [{campo}] != '' AND [{campo}] != '[]'"
        elif tipo == "INT":
            condition = f"[{campo}] IS NOT NULL"
        else:
            condition = f"[{campo}] IS NOT NULL AND [{campo}] != ''"

        query = f"""
            SELECT COUNT(CASE WHEN {condition} THEN 1 END) as con_valor
            FROM ofertas_nlp
            WHERE nlp_version = '10.0.0' AND id_oferta IN ({placeholders})
        """
        cursor.execute(query, gold_ids)
        con_valor = cursor.fetchone()[0] or 0
        total_con_valor += con_valor

        pct = (con_valor / 49 * 100) if 49 > 0 else 0

        # Estado
        if pct >= 80:
            estado = "OK"
        elif pct >= 50:
            estado = "MEDIO"
        elif pct > 0:
            estado = "BAJO"
        else:
            estado = "VACIO"

        # Mostrar bloque solo cuando cambia
        bloque_show = bloque if bloque != current_bloque else ""
        current_bloque = bloque

        print(f"{bloque_show:<15} | {campo:<35} | {con_valor:>10} | {pct:>6.1f}% | [{estado}]")

        resultados.append({
            "bloque": bloque,
            "campo": campo,
            "con_valor": con_valor,
            "total": 49,
            "pct": pct,
            "estado": estado
        })

    print("-" * 100)

    # Resumen por bloque
    print()
    print("=" * 100)
    print("RESUMEN POR BLOQUE")
    print("=" * 100)

    bloques = {}
    for r in resultados:
        if r["bloque"] not in bloques:
            bloques[r["bloque"]] = {"total": 0, "con_valor": 0}
        bloques[r["bloque"]]["total"] += 49
        bloques[r["bloque"]]["con_valor"] += r["con_valor"]

    for bloque, data in bloques.items():
        pct = (data["con_valor"] / data["total"] * 100) if data["total"] > 0 else 0
        print(f"  {bloque:<20}: {pct:>6.1f}%")

    # Total general
    pct_total = (total_con_valor / (total_campos * 49) * 100) if total_campos > 0 else 0
    print()
    print(f"  COBERTURA TOTAL: {pct_total:.1f}%")
    print()

    # Campos vacíos
    print("=" * 100)
    print("CAMPOS VACIOS (0%) - Revisar prompt")
    print("=" * 100)
    for r in resultados:
        if r["pct"] == 0:
            print(f"  - {r['bloque']}.{r['campo']}")

    # Campos con buena cobertura
    print()
    print("=" * 100)
    print("CAMPOS CON BUENA COBERTURA (>80%)")
    print("=" * 100)
    for r in resultados:
        if r["pct"] >= 80:
            print(f"  - {r['bloque']}.{r['campo']}: {r['pct']:.1f}%")

    conn.close()
    return resultados


if __name__ == "__main__":
    main()
