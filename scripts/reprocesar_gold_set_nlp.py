#!/usr/bin/env python3
"""
Reprocesar Gold Set con NLP actualizado + Skills Diccionario v2
===============================================================

Procesa las 49 ofertas del Gold Set y genera comparativa de métricas.
Exporta Excel para validación.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "02.5_nlp_extraction" / "scripts" / "patterns"))
sys.path.insert(0, str(project_root / "database"))

from regex_patterns_v4 import extract_all

# Database path
DB_PATH = project_root / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = project_root / "database" / "gold_set_manual_v2.json"


def load_gold_set_ids():
    """Carga los IDs del Gold Set"""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    ids = [int(item['id_oferta']) for item in gold_set]
    return ids


def get_ofertas_from_db(ids):
    """Obtiene las ofertas de la BD"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(ids))
    cursor.execute(f"""
        SELECT id_oferta, titulo, empresa, descripcion, localizacion, modalidad_trabajo
        FROM ofertas
        WHERE id_oferta IN ({placeholders})
    """, ids)

    ofertas = {row['id_oferta']: dict(row) for row in cursor.fetchall()}
    conn.close()
    return ofertas


def get_nlp_metricas_actuales(ids):
    """Obtiene métricas NLP actuales directamente de BD"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(ids))
    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN provincia IS NOT NULL AND provincia != '' THEN 1 ELSE 0 END) as provincia,
            SUM(CASE WHEN localidad IS NOT NULL AND localidad != '' THEN 1 ELSE 0 END) as localidad,
            SUM(CASE WHEN modalidad IS NOT NULL AND modalidad != '' THEN 1 ELSE 0 END) as modalidad,
            SUM(CASE WHEN nivel_seniority IS NOT NULL AND nivel_seniority != '' THEN 1 ELSE 0 END) as seniority
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    row = cursor.fetchone()
    conn.close()

    total = row[0] or 49
    return {
        'total': total,
        'provincia': {'count': row[1], 'pct': round(row[1]/total*100, 1)},
        'localidad': {'count': row[2], 'pct': round(row[2]/total*100, 1)},
        'modalidad': {'count': row[3], 'pct': round(row[3]/total*100, 1)},
        'nivel_seniority': {'count': row[4], 'pct': round(row[4]/total*100, 1)},
    }


def get_nlp_detalle(ids):
    """Obtiene detalle NLP para cada oferta"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(ids))
    cursor.execute(f"""
        SELECT id_oferta, provincia, localidad, modalidad, nivel_seniority,
               skills_tecnicas_list, soft_skills_list, tecnologias_list,
               area_funcional, experiencia_min_anios
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    nlp_data = {row['id_oferta']: dict(row) for row in cursor.fetchall()}
    conn.close()
    return nlp_data


def extraer_skills_regex(ofertas):
    """Extrae skills usando el nuevo pipeline con diccionario"""
    resultados = {}

    for id_oferta, oferta in ofertas.items():
        descripcion = oferta.get('descripcion', '') or ''
        titulo = oferta.get('titulo', '') or ''
        empresa = oferta.get('empresa', '') or ''

        resultado = extract_all(descripcion, titulo, empresa)

        resultados[id_oferta] = {
            'skills_tecnicas_regex': resultado.get('skills_tecnicas_regex', []),
            'soft_skills_regex': resultado.get('soft_skills_regex', []),
        }

    return resultados


def calcular_metricas_skills(skills_regex, total):
    """Calcula métricas de skills extraídas"""
    ofertas_con_skills = sum(1 for s in skills_regex.values() if s.get('skills_tecnicas_regex'))
    ofertas_con_soft = sum(1 for s in skills_regex.values() if s.get('soft_skills_regex'))
    total_skills = sum(len(s.get('skills_tecnicas_regex', [])) for s in skills_regex.values())
    total_soft = sum(len(s.get('soft_skills_regex', [])) for s in skills_regex.values())

    return {
        'skills_tecnicas': {
            'count': ofertas_con_skills,
            'pct': round(ofertas_con_skills/total*100, 1),
            'total_items': total_skills,
        },
        'soft_skills': {
            'count': ofertas_con_soft,
            'pct': round(ofertas_con_soft/total*100, 1),
            'total_items': total_soft,
        },
    }


def analizar_caso_angular(ofertas, skills_regex, nlp_detalle):
    """Análisis detallado del caso Angular Senior (ID 1117982053)"""
    id_angular = 1117982053

    if id_angular not in ofertas:
        return None

    oferta = ofertas[id_angular]
    skills = skills_regex.get(id_angular, {})
    nlp = nlp_detalle.get(id_angular, {})

    tecnologias_esperadas = [
        "angular", "typescript", "javascript", "html", "css", "scss", "sass",
        "git", "rest", "api", "agile", "scrum", "rxjs", "ngrx"
    ]

    skills_tec = skills.get('skills_tecnicas_regex', [])
    skills_lower = [s.lower() for s in skills_tec]

    encontradas = [t for t in tecnologias_esperadas if any(t in s for s in skills_lower)]
    faltantes = [t for t in tecnologias_esperadas if t not in encontradas]

    return {
        'id_oferta': id_angular,
        'titulo': oferta.get('titulo'),
        'empresa': oferta.get('empresa'),
        'skills_extraidas': skills_tec,
        'soft_skills_extraidas': skills.get('soft_skills_regex', []),
        'tecnologias_esperadas': len(tecnologias_esperadas),
        'encontradas': encontradas,
        'faltantes': faltantes,
        'cobertura': f"{len(encontradas)}/{len(tecnologias_esperadas)}",
        'nlp_modalidad': nlp.get('modalidad'),
        'nlp_seniority': nlp.get('nivel_seniority'),
    }


def exportar_excel(ofertas, nlp_detalle, skills_regex, metricas_nlp, metricas_skills, caso_angular):
    """Exporta resultados a Excel"""
    try:
        import pandas as pd
    except ImportError:
        print("  [WARN] pandas no disponible, saltando export Excel")
        return None

    # Hoja 1: Ofertas Originales
    ofertas_df = pd.DataFrame([
        {
            'id_oferta': id_o,
            'titulo': o.get('titulo'),
            'empresa': o.get('empresa'),
            'localizacion': o.get('localizacion'),
            'descripcion': (o.get('descripcion') or '')[:500] + '...',
        }
        for id_o, o in ofertas.items()
    ])

    # Hoja 2: NLP Extracción
    nlp_df = pd.DataFrame([
        {
            'id_oferta': id_o,
            'provincia': nlp.get('provincia'),
            'localidad': nlp.get('localidad'),
            'modalidad': nlp.get('modalidad'),
            'nivel_seniority': nlp.get('nivel_seniority'),
            'area_funcional': nlp.get('area_funcional'),
            'experiencia_min': nlp.get('experiencia_min_anios'),
            'skills_tecnicas_bd': nlp.get('skills_tecnicas_list'),
            'skills_tecnicas_regex': ', '.join(skills_regex.get(id_o, {}).get('skills_tecnicas_regex', [])),
            'soft_skills_regex': ', '.join(skills_regex.get(id_o, {}).get('soft_skills_regex', [])),
        }
        for id_o, nlp in nlp_detalle.items()
    ])

    # Hoja 3: Comparativa ANTES vs AHORA
    comparativa_data = [
        {'Campo': 'provincia', 'Antes (13/12)': '63%', 'Ahora': f"{metricas_nlp['provincia']['pct']}%",
         'Mejora': f"{metricas_nlp['provincia']['pct'] - 63:+.0f}%"},
        {'Campo': 'localidad', 'Antes (13/12)': '51%', 'Ahora': f"{metricas_nlp['localidad']['pct']}%",
         'Mejora': f"{metricas_nlp['localidad']['pct'] - 51:+.0f}%"},
        {'Campo': 'modalidad', 'Antes (13/12)': '84%', 'Ahora': f"{metricas_nlp['modalidad']['pct']}%",
         'Mejora': f"{metricas_nlp['modalidad']['pct'] - 84:+.0f}%"},
        {'Campo': 'nivel_seniority', 'Antes (13/12)': '88%', 'Ahora': f"{metricas_nlp['nivel_seniority']['pct']}%",
         'Mejora': f"{metricas_nlp['nivel_seniority']['pct'] - 88:+.0f}%"},
        {'Campo': 'skills_tecnicas (regex)', 'Antes (13/12)': '55%', 'Ahora': f"{metricas_skills['skills_tecnicas']['pct']}%",
         'Mejora': f"{metricas_skills['skills_tecnicas']['pct'] - 55:+.0f}%"},
        {'Campo': 'soft_skills (regex)', 'Antes (13/12)': '65%', 'Ahora': f"{metricas_skills['soft_skills']['pct']}%",
         'Mejora': f"{metricas_skills['soft_skills']['pct'] - 65:+.0f}%"},
    ]
    comparativa_df = pd.DataFrame(comparativa_data)

    # Guardar Excel
    output_path = project_root / "exports" / "MOL_Gold_Set_49_Validacion_POST_FIX.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        ofertas_df.to_excel(writer, sheet_name='1_Ofertas_Originales', index=False)
        nlp_df.to_excel(writer, sheet_name='2_NLP_Extraccion', index=False)
        comparativa_df.to_excel(writer, sheet_name='3_Comparativa', index=False)

    return output_path


def main():
    print("=" * 70)
    print("REPROCESAR GOLD SET CON NLP ACTUALIZADO + SKILLS DICCIONARIO v2")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. Cargar Gold Set
    print("\n[1/6] Cargando Gold Set...")
    ids = load_gold_set_ids()
    print(f"    {len(ids)} ofertas en Gold Set")

    # 2. Obtener ofertas de BD
    print("\n[2/6] Obteniendo ofertas de BD...")
    ofertas = get_ofertas_from_db(ids)
    print(f"    {len(ofertas)} ofertas encontradas")

    # 3. Obtener métricas NLP actuales
    print("\n[3/6] Obteniendo métricas NLP actuales...")
    metricas_nlp = get_nlp_metricas_actuales(ids)

    # 4. Obtener detalle NLP
    print("\n[4/6] Obteniendo detalle NLP...")
    nlp_detalle = get_nlp_detalle(ids)

    # 5. Extraer skills con diccionario
    print("\n[5/6] Extrayendo skills con diccionario...")
    skills_regex = extraer_skills_regex(ofertas)
    metricas_skills = calcular_metricas_skills(skills_regex, len(ofertas))
    print(f"    {metricas_skills['skills_tecnicas']['total_items']} skills técnicas extraídas")
    print(f"    {metricas_skills['soft_skills']['total_items']} soft skills extraídas")

    # 6. Analizar caso Angular
    print("\n[6/6] Analizando caso Angular Senior...")
    caso_angular = analizar_caso_angular(ofertas, skills_regex, nlp_detalle)

    # === RESULTADOS ===
    print("\n" + "=" * 70)
    print("MÉTRICAS DE COBERTURA GOLD SET (49 ofertas)")
    print("=" * 70)

    antes = {'provincia': 63, 'localidad': 51, 'modalidad': 84, 'nivel_seniority': 88,
             'skills_tecnicas': 55, 'soft_skills': 65}

    print(f"\n{'Campo':<25} {'Antes (13/12)':<15} {'Ahora':<15} {'Mejora':<10}")
    print("-" * 65)

    for campo in ['provincia', 'localidad', 'modalidad', 'nivel_seniority']:
        pct_antes = antes[campo]
        pct_ahora = metricas_nlp[campo]['pct']
        mejora = pct_ahora - pct_antes
        print(f"{campo:<25} {pct_antes}%{'':<10} {pct_ahora}%{'':<10} {mejora:+.0f}%")

    for campo in ['skills_tecnicas', 'soft_skills']:
        pct_antes = antes[campo]
        pct_ahora = metricas_skills[campo]['pct']
        mejora = pct_ahora - pct_antes
        print(f"{campo} (regex){'':<10} {pct_antes}%{'':<10} {pct_ahora}%{'':<10} {mejora:+.0f}%")

    # === CASO ANGULAR ===
    print("\n" + "=" * 70)
    print("CASO CRÍTICO: Angular Senior (ID 1117982053)")
    print("=" * 70)

    if caso_angular:
        print(f"\nTítulo: {caso_angular['titulo']}")
        print(f"Empresa: {caso_angular['empresa']}")
        print(f"NLP modalidad: {caso_angular['nlp_modalidad']}")
        print(f"NLP seniority: {caso_angular['nlp_seniority']}")
        print(f"\nCobertura tecnologías: {caso_angular['cobertura']}")
        print(f"\nSkills técnicas extraídas ({len(caso_angular['skills_extraidas'])}):")
        for s in caso_angular['skills_extraidas']:
            print(f"  - {s}")
        print(f"\nSoft skills ({len(caso_angular['soft_skills_extraidas'])}):")
        for s in caso_angular['soft_skills_extraidas'][:5]:
            print(f"  - {s}")
        print(f"\nEncontradas: {', '.join(caso_angular['encontradas'])}")
        print(f"Faltantes: {', '.join(caso_angular['faltantes'])}")

    # === TOP OFERTAS ===
    print("\n" + "=" * 70)
    print("TOP 5 OFERTAS CON MÁS SKILLS")
    print("=" * 70)

    ofertas_skills = [(id_o, len(skills_regex.get(id_o, {}).get('skills_tecnicas_regex', [])))
                      for id_o in ofertas.keys()]
    ofertas_skills.sort(key=lambda x: x[1], reverse=True)

    for id_o, count in ofertas_skills[:5]:
        titulo = ofertas[id_o].get('titulo', 'N/A')[:45]
        skills = skills_regex.get(id_o, {}).get('skills_tecnicas_regex', [])[:4]
        print(f"[{id_o}] {titulo} - {count} skills: {', '.join(skills)}")

    # === EXPORT EXCEL ===
    print("\n" + "=" * 70)
    print("EXPORTANDO EXCEL")
    print("=" * 70)

    excel_path = exportar_excel(ofertas, nlp_detalle, skills_regex, metricas_nlp, metricas_skills, caso_angular)
    if excel_path:
        print(f"Excel exportado: {excel_path}")

    # === RESUMEN ===
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Ofertas procesadas: {len(ofertas)}/49")
    print(f"Skills técnicas totales: {metricas_skills['skills_tecnicas']['total_items']}")
    print(f"Soft skills totales: {metricas_skills['soft_skills']['total_items']}")
    print(f"Promedio skills/oferta: {metricas_skills['skills_tecnicas']['total_items']/len(ofertas):.1f}")

    # Guardar JSON
    resultados = {
        'fecha': datetime.now().isoformat(),
        'metricas_nlp': metricas_nlp,
        'metricas_skills': metricas_skills,
        'caso_angular': caso_angular,
    }
    output_json = project_root / "metrics" / "gold_set_nlp_reprocesado.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nJSON guardado: {output_json}")


if __name__ == "__main__":
    main()
