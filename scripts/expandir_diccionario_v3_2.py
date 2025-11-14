#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Expansión del Diccionario v3.1 → v3.2

Integra términos descubiertos del análisis exhaustivo de 5,255 ofertas
en 8 categorías clave.

Fecha: 2025-10-31
Autor: Script generado por Claude Code
"""

import json
import pandas as pd
from datetime import datetime
import shutil
import os

# ============================================================================
# CONFIGURACION
# ============================================================================

DICT_ACTUAL = '../data/config/master_keywords.json'
DICT_BACKUP = '../data/config/master_keywords_v3.1_backup.json'
DICT_NUEVO = '../data/config/master_keywords_v3.2.json'

REPORTES_DIR = '../data/analysis/keywords/'
TIMESTAMP = '20251031_104953'

REPORTES = {
    'estudios': f'{REPORTES_DIR}terminos_faltantes_estudios_{TIMESTAMP}.csv',
    'experiencia': f'{REPORTES_DIR}terminos_faltantes_experiencia_{TIMESTAMP}.csv',
    'tareas': f'{REPORTES_DIR}terminos_faltantes_tareas_{TIMESTAMP}.csv',
    'skills_tecnicas': f'{REPORTES_DIR}terminos_faltantes_skills_tecnicas_{TIMESTAMP}.csv',
    'soft_skills': f'{REPORTES_DIR}terminos_faltantes_soft_skills_{TIMESTAMP}.csv',
    'idiomas': f'{REPORTES_DIR}terminos_faltantes_idiomas_{TIMESTAMP}.csv',
    'beneficios': f'{REPORTES_DIR}terminos_faltantes_beneficios_{TIMESTAMP}.csv',
    'modalidades': f'{REPORTES_DIR}terminos_faltantes_modalidades_{TIMESTAMP}.csv',
}

# Umbrales de frecuencia mínima para incluir términos
UMBRALES = {
    'estudios': 20,          # >= 20 menciones (>= 0.38%)
    'experiencia': 10,        # >= 10 menciones
    'tareas': 50,            # >= 50 menciones (>= 0.95%)
    'skills_tecnicas': 15,   # >= 15 menciones
    'soft_skills': 50,       # >= 50 menciones (>= 0.95%)
    'idiomas': 10,           # >= 10 menciones
    'beneficios': 20,        # >= 20 menciones
    'modalidades': 15,       # >= 15 menciones
}

# ============================================================================
# FUNCIONES
# ============================================================================

def cargar_diccionario(path):
    """Carga el diccionario JSON actual"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_diccionario(dict_data, path):
    """Guarda el diccionario JSON"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dict_data, f, indent=2, ensure_ascii=False)

def cargar_terminos_relevantes(reporte_path, umbral):
    """Carga términos que superan el umbral de frecuencia"""
    df = pd.read_csv(reporte_path, encoding='utf-8')
    # Filtrar por umbral
    df_filtrado = df[df['frecuencia'] >= umbral]
    # Devolver solo los términos (columna 'termino')
    return df_filtrado['termino'].tolist()

def limpiar_terminos(terminos, terminos_existentes):
    """
    Limpia términos:
    - Elimina duplicados
    - Elimina términos ya existentes en el diccionario
    - Elimina términos demasiado genéricos o problemáticos
    """
    # Términos a excluir (demasiado genéricos o problemáticos)
    excluir = {
        'completo', 'o', 'de', 'en', 'la', 'el', 'los', 'las',
        'medico', 'medica',  # Versiones sin tilde (ya tenemos "médico")
        'organizacion', 'comunicacion', 'capacitacion',  # Sin tilde
        'responsabilidad',  # Ya existe "responsable"
        'viaticos',  # Sin tilde
        '�',  # Caracteres mal codificados
    }

    terminos_limpios = []
    for termino in terminos:
        termino_lower = termino.lower().strip()

        # Saltar si está en la lista de exclusión
        if termino_lower in excluir:
            continue

        # Saltar si ya existe en el diccionario
        if termino_lower in terminos_existentes:
            continue

        # Saltar si tiene caracteres raros o está mal codificado
        if '�' in termino or len(termino) < 3:
            continue

        terminos_limpios.append(termino_lower)

    # Eliminar duplicados manteniendo orden
    return list(dict.fromkeys(terminos_limpios))

def expandir_diccionario():
    """Función principal"""
    print('='*70)
    print('EXPANSION DICCIONARIO v3.1 a v3.2')
    print('='*70)
    print()

    # 1. Backup del diccionario actual
    print(f'1. Creando backup: {DICT_BACKUP}')
    shutil.copy2(DICT_ACTUAL, DICT_BACKUP)
    print('   OK')
    print()

    # 2. Cargar diccionario actual
    print(f'2. Cargando diccionario v3.1: {DICT_ACTUAL}')
    dict_v3_1 = cargar_diccionario(DICT_ACTUAL)
    keywords_v3_1 = dict_v3_1.get('estrategias', {}).get('ultra_exhaustiva', {}).get('keywords', [])
    print(f'   Keywords actuales en ultra_exhaustiva: {len(keywords_v3_1)}')
    print()

    # Crear set de términos existentes para comparación rápida
    terminos_existentes = set(k.lower() for k in keywords_v3_1)

    # 3. Cargar y procesar cada categoría de términos nuevos
    print('3. Cargando términos descubiertos...')
    terminos_nuevos_por_categoria = {}

    for categoria, reporte_path in REPORTES.items():
        umbral = UMBRALES[categoria]
        print(f'   {categoria:20s} (umbral >= {umbral})', end=' ... ')

        # Cargar términos que superan umbral
        terminos_raw = cargar_terminos_relevantes(reporte_path, umbral)

        # Limpiar y filtrar
        terminos_limpios = limpiar_terminos(terminos_raw, terminos_existentes)

        terminos_nuevos_por_categoria[categoria] = terminos_limpios
        print(f'{len(terminos_limpios)} términos nuevos')

    print()

    # 4. Consolidar todos los términos nuevos
    print('4. Consolidando términos nuevos...')
    todos_terminos_nuevos = []
    for categoria, terminos in terminos_nuevos_por_categoria.items():
        todos_terminos_nuevos.extend(terminos)
        print(f'   {categoria:20s}: +{len(terminos):3d} términos')

    # Eliminar duplicados finales
    todos_terminos_nuevos_unicos = list(dict.fromkeys(todos_terminos_nuevos))
    print(f'\n   TOTAL UNICO: {len(todos_terminos_nuevos_unicos)} términos nuevos')
    print()

    # 5. Crear diccionario v3.2
    print('5. Creando diccionario v3.2...')
    dict_v3_2 = dict_v3_1.copy()

    # Actualizar metadatos
    dict_v3_2['version'] = '3.2'
    dict_v3_2['ultima_actualizacion'] = datetime.now().strftime('%Y-%m-%d')

    # Combinar keywords
    keywords_v3_2 = keywords_v3_1 + todos_terminos_nuevos_unicos
    print(f'   Keywords v3.1: {len(keywords_v3_1)}')
    print(f'   Nuevos:        {len(todos_terminos_nuevos_unicos)}')
    print(f'   Total v3.2:    {len(keywords_v3_2)}')
    print()

    # Actualizar estrategia ultra_exhaustiva
    dict_v3_2['estrategias']['ultra_exhaustiva']['keywords'] = keywords_v3_2
    dict_v3_2['estrategias']['ultra_exhaustiva']['descripcion'] = (
        f'Maxima cobertura ULTRA exhaustiva v3.2 - Analisis de 5,255 ofertas (~{len(keywords_v3_2)} keywords)'
    )

    # Crear nueva estrategia ultra_exhaustiva_v3_2 (top 1200 por relevancia)
    # Para v3.2, tomamos los primeros 1200 términos más relevantes
    # (asumiendo que los términos de v3.1 ya estaban ordenados por relevancia)
    keywords_top_1200 = keywords_v3_2[:1200] if len(keywords_v3_2) >= 1200 else keywords_v3_2

    dict_v3_2['estrategias']['ultra_exhaustiva_v3_2'] = {
        'descripcion': f'Top 1,200 keywords mas relevantes de v3.2 ({len(keywords_top_1200)} keywords)',
        'keywords': keywords_top_1200
    }

    # 6. Expandir categorías con términos específicos
    print('6. Expandiendo categorías específicas...')

    # Crear nuevas categorías si no existen
    if 'categorias' not in dict_v3_2:
        dict_v3_2['categorias'] = {}

    categorias_dict = dict_v3_2['categorias']

    # Agregar nuevos términos a categorías existentes o crear nuevas
    if 'Beneficios_Empresariales' not in categorias_dict:
        categorias_dict['Beneficios_Empresariales'] = terminos_nuevos_por_categoria.get('beneficios', [])[:50]
        print(f'   Nueva categoría: Beneficios_Empresariales ({len(categorias_dict["Beneficios_Empresariales"])} términos)')

    if 'Estudios_Requeridos' not in categorias_dict:
        categorias_dict['Estudios_Requeridos'] = terminos_nuevos_por_categoria.get('estudios', [])[:40]
        print(f'   Nueva categoría: Estudios_Requeridos ({len(categorias_dict["Estudios_Requeridos"])} términos)')

    if 'Soft_Skills_Expandidas' not in categorias_dict:
        categorias_dict['Soft_Skills_Expandidas'] = terminos_nuevos_por_categoria.get('soft_skills', [])[:30]
        print(f'   Nueva categoría: Soft_Skills_Expandidas ({len(categorias_dict["Soft_Skills_Expandidas"])} términos)')

    print()

    # 7. Guardar diccionario v3.2
    print(f'7. Guardando diccionario v3.2: {DICT_NUEVO}')
    guardar_diccionario(dict_v3_2, DICT_NUEVO)
    print('   OK')
    print()

    # 8. Resumen final
    print('='*70)
    print('RESUMEN DE EXPANSION')
    print('='*70)
    print(f'Diccionario v3.1:  {len(keywords_v3_1):,} keywords')
    print(f'Terminos nuevos:   {len(todos_terminos_nuevos_unicos):,} keywords')
    print(f'Diccionario v3.2:  {len(keywords_v3_2):,} keywords')
    print()
    print(f'Estrategias creadas:')
    print(f'  - ultra_exhaustiva:     {len(keywords_v3_2):,} keywords (todos)')
    print(f'  - ultra_exhaustiva_v3_2: {len(keywords_top_1200):,} keywords (top relevantes)')
    print()
    print(f'Categorias expandidas: {len(categorias_dict)} categorías')
    print()
    print('Archivos generados:')
    print(f'  - {DICT_BACKUP} (backup)')
    print(f'  - {DICT_NUEVO} (nuevo diccionario)')
    print()
    print('EXPANSION COMPLETADA')
    print('='*70)

if __name__ == '__main__':
    expandir_diccionario()
