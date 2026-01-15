#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Análisis Exhaustivo de Ofertas - Expansión Diccionario v3.2

Analiza 5,255 ofertas consolidadas para extraer términos laborales faltantes
en 8 categorías clave.

Categorías analizadas:
1. Estudios requeridos
2. Experiencia laboral
3. Tareas y responsabilidades
4. Skills técnicas (hard skills)
5. Soft skills
6. Idiomas
7. Beneficios
8. Modalidades de trabajo

Fecha: 2025-10-31
Autor: Script generado por Claude Code
"""

import pandas as pd
import re
import json
from collections import Counter
from datetime import datetime
import os

# ============================================================================
# CONFIGURACION
# ============================================================================

INPUT_CSV = '../01_sources/bumeran/data/raw/bumeran_consolidado_5255_ofertas.csv'
OUTPUT_DIR = '../data/analysis/keywords/'
DICT_ACTUAL = '../data/config/master_keywords_v3.1.json'

# Crear directorio de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# PATRONES REGEX PARA EXTRACCION
# ============================================================================

# 1. ESTUDIOS
PATRONES_ESTUDIOS = {
    'carreras': [
        r'ingeniería?\s+(?:en\s+)?(\w+(?:\s+\w+)?)',
        r'licenciatura\s+en\s+(\w+(?:\s+\w+)?)',
        r'contador\s+p[uú]blico',
        r'tecnicatura\s+(?:en\s+)?(\w+(?:\s+\w+)?)',
        r't[eé]cnico\s+(?:superior\s+)?(?:en\s+)?(\w+(?:\s+\w+)?)',
        r'analista\s+de\s+sistemas',
        r'abogad[oa]',
        r'm[eé]dic[oa]',
        r'enfermer[oa]',
    ],
    'niveles': [
        r'secundario\s+completo',
        r'terciario\s+(?:completo|en\s+curso)',
        r'universitario\s+(?:completo|en\s+curso)',
        r'estudiante\s+(?:avanzado|de)',
        r'graduado',
        r't[ií]tulo\s+(?:universitario|terciario)',
        r'posgrado',
        r'maestr[ií]a',
    ],
    'marcadores': [
        r'excluyente',
        r'indispensable',
        r'obligatorio',
        r'deseable',
    ]
}

# 2. EXPERIENCIA
PATRONES_EXPERIENCIA = {
    'anos': [
        r'(\d+)\s*[aá]ños?\s+(?:de\s+)?experiencia',
        r'experiencia\s+(?:de\s+)?(\d+)\s*[aá]ños?',
        r'm[íi]nimo\s+(\d+)\s*[aá]ños?',
        r'(\d+)\+?\s*[aá]ños?',
        r'entre\s+(\d+)\s*y\s*(\d+)\s*[aá]ños?',
    ],
    'niveles': [
        r'\b(?:junior|jr\.?)\b',
        r'\b(?:semi[\s-]?senior|ssr|semi sr)\b',
        r'\b(?:senior|sr\.?)\b',
        r'\btrainee\b',
        r'\bpasante\b',
    ],
    'contexto': [
        r'experiencia\s+(?:comprobable|previa|demostrable)',
        r'sin\s+experiencia',
        r'primera\s+experiencia',
    ]
}

# 3. TAREAS - Verbos de acción comunes
VERBOS_ACCION = [
    'realizar', 'gestionar', 'coordinar', 'analizar', 'colaborar',
    'supervisar', 'dirigir', 'liderar', 'planificar', 'organizar',
    'desarrollar', 'implementar', 'ejecutar', 'controlar', 'evaluar',
    'diseñar', 'crear', 'elaborar', 'preparar', 'mantener',
    'administrar', 'monitorear', 'verificar', 'revisar', 'atender',
    'confeccionar', 'seguimiento', 'búsqueda', 'negociación',
    'liquidar', 'cargar', 'procesar', 'registrar', 'archivar'
]

# 4. SKILLS TECNICAS - Patrones generales
PATRONES_SKILLS = {
    'software': [
        r'\b(?:SAP|ERP|CRM|WMS|TMS)\b',
        r'\bExcel\s+(?:b[aá]sico|intermedio|avanzado)\b',
        r'\b(?:Word|PowerPoint|Outlook)\b',
        r'\b(?:Tango|Bejerman|Siap)\b',
        r'\b(?:AutoCAD|SolidWorks|Revit)\b',
    ],
    'lenguajes': [
        r'\b(?:Python|JavaScript|Java|C#|PHP|Ruby|Golang|TypeScript)\b',
        r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Oracle)\b',
    ],
    'frameworks': [
        r'\b(?:React|Angular|Vue|Django|Flask|Spring|\.NET)\b',
        r'\b(?:Node\.js|Express)\b',
    ],
    'herramientas': [
        r'\b(?:Git|Docker|Kubernetes|Jenkins)\b',
        r'\b(?:AWS|Azure|Google Cloud|GCP)\b',
    ],
    'metodologias': [
        r'\bISO\s+\d+',
        r'\b(?:Agile|Scrum|Kanban|Lean|Kaizen|DMAIC)\b',
        r'\b5\s+porqu[eé]s?\b',
        r'\b(?:Ishikawa|diagrama\s+causa[\s-]efecto)\b',
    ]
}

# 5. SOFT SKILLS - Términos comunes
SOFT_SKILLS_PATTERNS = [
    r'(?:habilidades?\s+de\s+)?comunicaci[oó]n',
    r'liderazgo',
    r'trabajo\s+en\s+equipo',
    r'proactiv[oa]',
    r'organizaci[oó]n',
    r'atenci[oó]n\s+al\s+detalle',
    r'resoluci[oó]n\s+de\s+problemas',
    r'pensamiento\s+cr[ií]tico',
    r'orientaci[oó]n\s+a\s+resultados',
    r'adaptabilidad',
    r'creatividad',
    r'iniciativa',
    r'responsabilidad',
    r'compromiso',
    r'habilidades?\s+interpersonales',
    r'capacidad\s+anal[ií]tica',
    r'negociaci[oó]n',
    r'planificaci[oó]n',
]

# 6. IDIOMAS
PATRONES_IDIOMAS = {
    'idiomas': [
        r'ingl[eé]s',
        r'portugu[eé]s',
        r'alem[aá]n',
        r'franc[eé]s',
        r'italiano',
        r'chino',
    ],
    'niveles': [
        r'(?:nivel\s+)?b[aá]sico',
        r'(?:nivel\s+)?intermedio',
        r'(?:nivel\s+)?avanzado',
        r'fluido',
        r'nativo',
        r'conversacional',
        r'profesional',
    ]
}

# 7. BENEFICIOS
PATRONES_BENEFICIOS = [
    r'OSDE\s+\d+',
    r'Swiss Medical',
    r'prepaga',
    r'obra\s+social',
    r'comedor',
    r'vi[aá]ticos',
    r'tarjeta\s+de\s+almuerzo',
    r'Gympass',
    r'gimnasio',
    r'bono',
    r'comisiones',
    r'aguinaldo',
    r'estacionamiento',
    r'descuentos',
    r'capacitaci[oó]n',
    r'd[ií]as?\s+(?:de\s+)?(?:wellbeing|bienestar)',
]

# 8. MODALIDADES
PATRONES_MODALIDADES = [
    r'(?:lunes\s+a\s+viernes|L\s+a\s+V)',
    r'\d+hs?\s+a\s+\d+hs?',
    r'turno\s+(?:ma[nñ]ana|tarde|noche)',
    r'horario\s+(?:flexible|rotativo)',
    r'h[ií]brido\s+\d+x\d+',
    r'\d+\s+d[ií]as?\s+(?:de\s+)?oficina',
    r'part[\s-]?time',
    r'\d+\s+horas\s+semanales',
]

# ============================================================================
# FUNCIONES DE EXTRACCION
# ============================================================================

def limpiar_texto(texto):
    """Normaliza texto para análisis"""
    if pd.isna(texto):
        return ""
    texto = str(texto).lower()
    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def extraer_estudios(descripcion):
    """Extrae menciones de estudios requeridos"""
    texto = limpiar_texto(descripcion)
    resultados = []

    # Buscar carreras
    for patron in PATRONES_ESTUDIOS['carreras']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    # Buscar niveles
    for patron in PATRONES_ESTUDIOS['niveles']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

def extraer_experiencia(descripcion):
    """Extrae menciones de experiencia laboral"""
    texto = limpiar_texto(descripcion)
    resultados = []

    # Buscar años de experiencia
    for patron in PATRONES_EXPERIENCIA['anos']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                resultados.extend([f"{m} años" for m in matches[0] if m])
            else:
                resultados.extend([f"{m} años" for m in matches])

    # Buscar niveles
    for patron in PATRONES_EXPERIENCIA['niveles']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

def extraer_tareas(descripcion):
    """Extrae verbos de acción de tareas"""
    texto = limpiar_texto(descripcion)
    resultados = []

    for verbo in VERBOS_ACCION:
        # Buscar el verbo en infinitivo o conjugado
        patron = rf'\b{verbo}(?:r|ndo|ci[oó]n)?\b'
        if re.search(patron, texto, re.IGNORECASE):
            resultados.append(verbo)

    return resultados

def extraer_skills_tecnicas(descripcion):
    """Extrae menciones de skills técnicas"""
    texto = limpiar_texto(descripcion)
    resultados = []

    for categoria, patrones in PATRONES_SKILLS.items():
        for patron in patrones:
            matches = re.findall(patron, texto, re.IGNORECASE)
            resultados.extend(matches)

    return resultados

def extraer_soft_skills(descripcion):
    """Extrae menciones de soft skills"""
    texto = limpiar_texto(descripcion)
    resultados = []

    for patron in SOFT_SKILLS_PATTERNS:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

def extraer_idiomas(descripcion):
    """Extrae menciones de idiomas y niveles"""
    texto = limpiar_texto(descripcion)
    resultados = []

    # Buscar idiomas
    for patron in PATRONES_IDIOMAS['idiomas']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    # Buscar niveles de idioma
    for patron in PATRONES_IDIOMAS['niveles']:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

def extraer_beneficios(descripcion):
    """Extrae menciones de beneficios"""
    texto = limpiar_texto(descripcion)
    resultados = []

    for patron in PATRONES_BENEFICIOS:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

def extraer_modalidades(descripcion):
    """Extrae menciones de modalidades de trabajo"""
    texto = limpiar_texto(descripcion)
    resultados = []

    for patron in PATRONES_MODALIDADES:
        matches = re.findall(patron, texto, re.IGNORECASE)
        resultados.extend(matches)

    return resultados

# ============================================================================
# FUNCION PRINCIPAL
# ============================================================================

def analizar_ofertas():
    """Función principal de análisis"""
    print('='*70)
    print('ANALISIS EXHAUSTIVO DE OFERTAS - Expansión Diccionario v3.2')
    print('='*70)
    print()

    # Cargar datos
    print(f'Cargando ofertas desde: {INPUT_CSV}')
    df = pd.read_csv(INPUT_CSV, encoding='utf-8')
    print(f'Total ofertas cargadas: {len(df):,}')
    print()

    # Verificar campo descripcion
    df_validas = df[df['descripcion'].notna()]
    print(f'Ofertas con descripción válida: {len(df_validas):,}')
    print()

    # Inicializar contenedores
    all_estudios = []
    all_experiencia = []
    all_tareas = []
    all_skills_tecnicas = []
    all_soft_skills = []
    all_idiomas = []
    all_beneficios = []
    all_modalidades = []

    # Procesar cada oferta
    print('Procesando ofertas...')
    for idx, row in df_validas.iterrows():
        descripcion = row['descripcion']

        # Extraer cada categoría
        all_estudios.extend(extraer_estudios(descripcion))
        all_experiencia.extend(extraer_experiencia(descripcion))
        all_tareas.extend(extraer_tareas(descripcion))
        all_skills_tecnicas.extend(extraer_skills_tecnicas(descripcion))
        all_soft_skills.extend(extraer_soft_skills(descripcion))
        all_idiomas.extend(extraer_idiomas(descripcion))
        all_beneficios.extend(extraer_beneficios(descripcion))
        all_modalidades.extend(extraer_modalidades(descripcion))

        # Mostrar progreso cada 500 ofertas
        if (idx + 1) % 500 == 0:
            print(f'  Procesadas {idx + 1:,} ofertas...')

    print(f'  Procesadas {len(df_validas):,} ofertas COMPLETADO')
    print()

    # Contar frecuencias
    print('Contando frecuencias...')
    counter_estudios = Counter(all_estudios)
    counter_experiencia = Counter(all_experiencia)
    counter_tareas = Counter(all_tareas)
    counter_skills = Counter(all_skills_tecnicas)
    counter_soft = Counter(all_soft_skills)
    counter_idiomas = Counter(all_idiomas)
    counter_beneficios = Counter(all_beneficios)
    counter_modalidades = Counter(all_modalidades)
    print()

    # Generar reportes
    print('Generando reportes...')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    categorias = {
        'estudios': (counter_estudios, 100),
        'experiencia': (counter_experiencia, 50),
        'tareas': (counter_tareas, 150),
        'skills_tecnicas': (counter_skills, 200),
        'soft_skills': (counter_soft, 60),
        'idiomas': (counter_idiomas, 20),
        'beneficios': (counter_beneficios, 80),
        'modalidades': (counter_modalidades, 50),
    }

    reportes_generados = {}

    for nombre, (counter, top_n) in categorias.items():
        # Top N más frecuentes
        top_items = counter.most_common(top_n)

        # Crear DataFrame
        df_reporte = pd.DataFrame(top_items, columns=['termino', 'frecuencia'])
        df_reporte['porcentaje'] = (df_reporte['frecuencia'] / len(df_validas) * 100).round(2)

        # Guardar CSV
        output_file = os.path.join(OUTPUT_DIR, f'terminos_faltantes_{nombre}_{timestamp}.csv')
        df_reporte.to_csv(output_file, index=False, encoding='utf-8')
        print(f'  OK {output_file}')

        # Guardar info para reporte consolidado
        reportes_generados[nombre] = {
            'total_menciones': len([item for item in counter.elements()]),
            'terminos_unicos': len(counter),
            'top_10': [{'termino': t, 'frecuencia': f} for t, f in top_items[:10]]
        }

    print()

    # Generar reporte consolidado JSON
    reporte_consolidado = {
        'fecha_analisis': datetime.now().isoformat(),
        'ofertas_analizadas': len(df_validas),
        'total_ofertas': len(df),
        'rango_temporal': {
            'inicio': df['fecha_publicacion_iso'].min(),
            'fin': df['fecha_publicacion_iso'].max(),
        },
        'categorias': reportes_generados,
        'archivos_generados': list(categorias.keys())
    }

    json_file = os.path.join(OUTPUT_DIR, f'analisis_completo_v3_2_{timestamp}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(reporte_consolidado, f, indent=2, ensure_ascii=False)
    print(f'Reporte consolidado JSON: {json_file}')
    print()

    # Resumen
    print('='*70)
    print('RESUMEN DEL ANALISIS')
    print('='*70)
    for nombre, info in reportes_generados.items():
        print(f'{nombre:20s}: {info["total_menciones"]:,} menciones, {info["terminos_unicos"]:,} términos únicos')
    print()
    print('ANALISIS COMPLETADO')
    print('='*70)

if __name__ == '__main__':
    analizar_ofertas()
