#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_matching_esco_v2.py
===========================
Evaluación COMPLETA del matching ESCO con trazabilidad real.

Muestra para cada oferta:
1. Datos de la oferta original (título, descripción)
2. Ocupación ESCO asignada con código ISCO desglosado
3. Skills ESCO asociados (esenciales y opcionales)
4. Scores del matching
5. Contexto para evaluación manual
"""

import sqlite3
import os
import csv
import json
from datetime import datetime

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), 'bumeran_scraping.db')
OUTPUT_DIR = os.path.dirname(__file__)


def limpiar_texto(texto):
    """Limpia texto de caracteres no imprimibles en cp1252"""
    if not texto:
        return ''
    # Reemplaza caracteres problemáticos
    try:
        return texto.encode('cp1252', errors='ignore').decode('cp1252')
    except:
        return texto.encode('ascii', errors='ignore').decode('ascii')


def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def desglosar_isco(isco_code):
    """Desglosa código ISCO en sus 4 niveles jerárquicos"""
    if not isco_code or not isco_code.startswith('C'):
        return {'nivel1': None, 'nivel2': None, 'nivel3': None, 'nivel4': None}

    codigo = isco_code[1:]  # Quitar la 'C'
    return {
        'nivel1': codigo[0] if len(codigo) >= 1 else None,      # Gran grupo
        'nivel2': codigo[:2] if len(codigo) >= 2 else None,     # Subgrupo principal
        'nivel3': codigo[:3] if len(codigo) >= 3 else None,     # Subgrupo
        'nivel4': codigo[:4] if len(codigo) >= 4 else None,     # Grupo unitario
    }


# Diccionario de grupos ISCO-08 (nivel 1)
ISCO_NIVEL1 = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales científicos e intelectuales',
    '3': 'Técnicos y profesionales de nivel medio',
    '4': 'Personal de apoyo administrativo',
    '5': 'Trabajadores de servicios y vendedores',
    '6': 'Agricultores y trabajadores agropecuarios',
    '7': 'Oficiales, operarios y artesanos',
    '8': 'Operadores de instalaciones y máquinas',
    '9': 'Ocupaciones elementales',
    '0': 'Ocupaciones militares'
}


def obtener_skills_ocupacion(conn, occupation_uri):
    """Obtiene los skills asociados a una ocupación ESCO"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.relation_type, s.preferred_label_es, s.skill_type
        FROM esco_associations a
        JOIN esco_skills s ON a.skill_uri = s.skill_uri
        WHERE a.occupation_uri = ?
        ORDER BY a.relation_type, s.preferred_label_es
    """, (occupation_uri,))

    skills = {'essential': [], 'optional': []}
    for row in cursor.fetchall():
        rel_type = row['relation_type'] or 'optional'
        skill_name = row['preferred_label_es'] or 'Sin nombre'
        if rel_type in skills:
            skills[rel_type].append(skill_name)

    return skills


def obtener_muestra_completa(conn, n_por_rango=5):
    """Obtiene muestra estratificada con TODOS los datos necesarios"""
    cursor = conn.cursor()

    rangos = [
        ("BAJO", 0, 0.50),
        ("MEDIO-BAJO", 0.50, 0.60),
        ("MEDIO-ALTO", 0.60, 0.70),
        ("ALTO", 0.70, 1.0)
    ]

    muestras = []

    for nombre_rango, min_score, max_score in rangos:
        # Query completa con JOIN a ocupaciones ESCO
        cursor.execute("""
            SELECT
                m.id_oferta,
                o.titulo,
                o.descripcion,
                o.id_area,
                o.id_subarea,
                o.empresa,
                o.provincia_normalizada,
                m.esco_occupation_uri,
                m.esco_occupation_label,
                m.occupation_match_score,
                m.rerank_score,
                m.occupation_match_method,
                m.matching_version,
                eo.isco_code,
                eo.esco_code,
                eo.description_es as esco_description
            FROM ofertas_esco_matching m
            JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
            LEFT JOIN esco_occupations eo ON m.esco_occupation_uri = eo.occupation_uri
            WHERE m.occupation_match_score >= ? AND m.occupation_match_score < ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (min_score, max_score, n_por_rango))

        for row in cursor.fetchall():
            # Desglosar ISCO
            isco_desglose = desglosar_isco(row['isco_code'])

            # Obtener skills asociados
            skills = obtener_skills_ocupacion(conn, row['esco_occupation_uri'])

            muestras.append({
                'rango': nombre_rango,
                'id_oferta': row['id_oferta'],
                # Datos de la oferta
                'titulo_oferta': row['titulo'],
                'descripcion_oferta': row['descripcion'],
                'area': row['id_area'],
                'subarea': row['id_subarea'],
                'empresa': row['empresa'],
                'provincia': row['provincia_normalizada'],
                # Datos ESCO
                'esco_uri': row['esco_occupation_uri'],
                'esco_label': row['esco_occupation_label'],
                'esco_description': row['esco_description'],
                'esco_code': row['esco_code'],
                # Datos ISCO
                'isco_code': row['isco_code'],
                'isco_nivel1': isco_desglose['nivel1'],
                'isco_nivel1_nombre': ISCO_NIVEL1.get(isco_desglose['nivel1'], 'Desconocido'),
                'isco_nivel2': isco_desglose['nivel2'],
                'isco_nivel3': isco_desglose['nivel3'],
                'isco_nivel4': isco_desglose['nivel4'],
                # Skills
                'skills_esenciales': skills['essential'],
                'skills_opcionales': skills['optional'],
                # Scores
                'score_bge_m3': row['occupation_match_score'],
                'score_esco_xlm': row['rerank_score'],
                'metodo': row['occupation_match_method'],
                'version': row['matching_version'],
            })

    return muestras


def imprimir_muestra_detallada(muestras):
    """Imprime cada muestra con formato detallado para evaluación"""

    rango_actual = None

    for i, m in enumerate(muestras, 1):
        # Separador de rango
        if m['rango'] != rango_actual:
            rango_actual = m['rango']
            print("\n" + "=" * 80)
            print(f"  RANGO: {rango_actual}")
            print("=" * 80)

        print(f"\n{'-' * 80}")
        print(f"MUESTRA #{i}")
        print(f"{'-' * 80}")

        # === OFERTA ORIGINAL ===
        print(f"\n>> OFERTA ORIGINAL (ID: {m['id_oferta']})")
        print(f"  Titulo:    {limpiar_texto(m['titulo_oferta'])}")
        print(f"  Empresa:   {limpiar_texto(m['empresa'])}")
        print(f"  Provincia: {m['provincia']}")
        print(f"  Area:      {m['area']} / {m['subarea']}")

        # Descripcion (primeros 600 chars)
        desc = limpiar_texto((m['descripcion_oferta'] or '')[:600].replace('\n', ' '))
        if len(m['descripcion_oferta'] or '') > 600:
            desc += '...'
        print(f"\n  Descripcion:")
        # Dividir en lineas de 70 chars
        for j in range(0, len(desc), 70):
            print(f"    {desc[j:j+70]}")

        # === CLASIFICACION ESCO ===
        print(f"\n>> CLASIFICACION ESCO ASIGNADA")
        print(f"  Ocupacion: {limpiar_texto(m['esco_label'])}")
        print(f"  URI:       {m['esco_uri']}")
        print(f"  Codigo:    {m['esco_code']}")

        # Descripcion ESCO
        if m['esco_description']:
            esco_desc = limpiar_texto(m['esco_description'][:300])
            if len(m['esco_description']) > 300:
                esco_desc += '...'
            print(f"  Descripcion ESCO:")
            for j in range(0, len(esco_desc), 70):
                print(f"    {esco_desc[j:j+70]}")

        # === JERARQUIA ISCO ===
        print(f"\n>> JERARQUIA ISCO-08")
        print(f"  Codigo ISCO: {m['isco_code']}")
        print(f"  |-- Nivel 1 (Gran grupo):        {m['isco_nivel1']} - {m['isco_nivel1_nombre']}")
        print(f"  |-- Nivel 2 (Subgrupo principal): {m['isco_nivel2']}")
        print(f"  |-- Nivel 3 (Subgrupo):           {m['isco_nivel3']}")
        print(f"  +-- Nivel 4 (Grupo unitario):     {m['isco_nivel4']}")

        # === SKILLS ESCO ===
        print(f"\n>> SKILLS ESCO ASOCIADOS")
        print(f"  Skills Esenciales ({len(m['skills_esenciales'])}):")
        for skill in m['skills_esenciales'][:8]:  # Max 8
            print(f"    * {limpiar_texto(skill)}")
        if len(m['skills_esenciales']) > 8:
            print(f"    ... (+{len(m['skills_esenciales']) - 8} mas)")

        print(f"  Skills Opcionales ({len(m['skills_opcionales'])}):")
        for skill in m['skills_opcionales'][:5]:  # Max 5
            print(f"    - {limpiar_texto(skill)}")
        if len(m['skills_opcionales']) > 5:
            print(f"    ... (+{len(m['skills_opcionales']) - 5} mas)")

        # === SCORES ===
        print(f"\n>> SCORES DEL MATCHING")
        print(f"  Score BGE-M3 (similarity):  {m['score_bge_m3']:.4f}")
        rerank_str = f"{m['score_esco_xlm']:.4f}" if m['score_esco_xlm'] else 'N/A'
        print(f"  Score ESCO-XLM (rerank):    {rerank_str}")
        print(f"  Metodo:                     {m['metodo']}")
        print(f"  Version:                    {m['version']}")

        # === EVALUACION ===
        print(f"\n>> EVALUACION MANUAL")
        print(f"  [ ] CORRECTO   - La ocupacion ESCO coincide semanticamente")
        print(f"  [ ] PARCIAL    - Relacionado pero no exacto")
        print(f"  [ ] INCORRECTO - No hay relacion clara")
        print(f"  Notas: _______________________________________________")


def exportar_csv_completo(muestras, filename='evaluacion_esco_completa.csv'):
    """Exporta todas las muestras a CSV con todos los campos"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'rango', 'id_oferta',
            'titulo_oferta', 'descripcion_oferta', 'empresa', 'provincia', 'area', 'subarea',
            'esco_uri', 'esco_label', 'esco_description', 'esco_code',
            'isco_code', 'isco_nivel1', 'isco_nivel1_nombre', 'isco_nivel2', 'isco_nivel3', 'isco_nivel4',
            'skills_esenciales', 'skills_opcionales',
            'score_bge_m3', 'score_esco_xlm', 'metodo', 'version',
            'evaluacion', 'notas'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in muestras:
            row = {
                'rango': m['rango'],
                'id_oferta': m['id_oferta'],
                'titulo_oferta': m['titulo_oferta'],
                'descripcion_oferta': (m['descripcion_oferta'] or '')[:2000],
                'empresa': m['empresa'],
                'provincia': m['provincia'],
                'area': m['area'],
                'subarea': m['subarea'],
                'esco_uri': m['esco_uri'],
                'esco_label': m['esco_label'],
                'esco_description': m['esco_description'],
                'esco_code': m['esco_code'],
                'isco_code': m['isco_code'],
                'isco_nivel1': m['isco_nivel1'],
                'isco_nivel1_nombre': m['isco_nivel1_nombre'],
                'isco_nivel2': m['isco_nivel2'],
                'isco_nivel3': m['isco_nivel3'],
                'isco_nivel4': m['isco_nivel4'],
                'skills_esenciales': ' | '.join(m['skills_esenciales'][:10]),
                'skills_opcionales': ' | '.join(m['skills_opcionales'][:10]),
                'score_bge_m3': f"{m['score_bge_m3']:.4f}",
                'score_esco_xlm': f"{m['score_esco_xlm']:.4f}" if m['score_esco_xlm'] else '',
                'metodo': m['metodo'],
                'version': m['version'],
                'evaluacion': '',
                'notas': ''
            }
            writer.writerow(row)

    return filepath


def main():
    print("\n" + "=" * 80)
    print("  EVALUACIÓN COMPLETA DEL MATCHING ESCO")
    print("  Pipeline: BGE-M3 + ESCO-XLM (Híbrido)")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    conn = conectar_db()
    print(f"\n[OK] Conectado a: {DB_PATH}")

    # Obtener muestra completa (5 por rango = 20 total)
    print("\n[...] Obteniendo muestra estratificada con datos completos...")
    muestras = obtener_muestra_completa(conn, n_por_rango=5)
    print(f"[OK] {len(muestras)} muestras obtenidas")

    # Imprimir detalle
    imprimir_muestra_detallada(muestras)

    # Exportar CSV
    csv_path = exportar_csv_completo(muestras)

    # Resumen
    print("\n" + "=" * 80)
    print("  RESUMEN")
    print("=" * 80)
    print(f"  Muestras generadas: {len(muestras)}")
    print(f"  CSV exportado: {csv_path}")
    print("\n  El CSV incluye:")
    print("    - Datos completos de la oferta original")
    print("    - Ocupación ESCO con URI y código")
    print("    - Jerarquía ISCO-08 (4 niveles)")
    print("    - Skills esenciales y opcionales")
    print("    - Scores del matching")
    print("    - Columnas para evaluación manual")
    print("=" * 80)

    conn.close()


if __name__ == '__main__':
    main()
