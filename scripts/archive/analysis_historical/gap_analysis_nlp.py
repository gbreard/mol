# -*- coding: utf-8 -*-
"""
gap_analysis_nlp.py
===================
Genera análisis de gap entre NLP Schema v5 y la implementación actual.
"""

import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
SCHEMA_PATH = Path(__file__).parent.parent / 'docs' / 'NLP_SCHEMA_V5.md'
OUTPUT_PATH = Path(__file__).parent / 'GAP_ANALYSIS_NLP.md'

def get_current_columns():
    """Obtiene columnas actuales de ofertas_nlp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(ofertas_nlp)')
    cols = {row[1]: {'type': row[2], 'notnull': bool(row[3])} for row in cursor.fetchall()}
    conn.close()
    return cols

def get_data_coverage():
    """Obtiene estadísticas de cobertura de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total de registros
    cursor.execute('SELECT COUNT(*) FROM ofertas_nlp')
    total = cursor.fetchone()[0]

    # Obtener columnas
    cursor.execute('PRAGMA table_info(ofertas_nlp)')
    columns = [row[1] for row in cursor.fetchall()]

    coverage = {'_total': total}

    for col in columns:
        if col in ('id_oferta', 'created_at', 'updated_at'):
            continue
        try:
            # Para campos de texto
            cursor.execute(f'''
                SELECT
                    COUNT(CASE WHEN {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != 'null' THEN 1 END)
                FROM ofertas_nlp
            ''')
            count = cursor.fetchone()[0]
            coverage[col] = {'count': count, 'pct': round(100*count/total, 1) if total > 0 else 0}
        except:
            coverage[col] = {'count': 0, 'pct': 0}

    conn.close()
    return coverage

def parse_schema_v5():
    """Parsea el schema v5 del markdown."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = {}
    current_block = None
    current_block_num = 0

    # Regex para encontrar bloques
    block_pattern = r'## Bloque (\d+): (.+)'
    field_pattern = r'\| (\w+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|'

    lines = content.split('\n')
    in_table = False

    for line in lines:
        # Detectar nuevo bloque
        block_match = re.match(block_pattern, line)
        if block_match:
            current_block_num = int(block_match.group(1))
            current_block = block_match.group(2).strip()
            blocks[current_block] = {'num': current_block_num, 'fields': []}
            in_table = False
            continue

        # Detectar inicio de tabla
        if current_block and '| Campo |' in line:
            in_table = True
            continue

        # Saltar separador de tabla
        if in_table and line.startswith('|--'):
            continue

        # Parsear campo de tabla
        if in_table and line.startswith('|') and current_block:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] and not parts[0].startswith('-'):
                field_name = parts[0]
                field_type = parts[1]
                field_example = parts[2]
                field_source = parts[3]

                blocks[current_block]['fields'].append({
                    'name': field_name,
                    'type': field_type,
                    'example': field_example,
                    'source': field_source
                })

        # Detectar fin de tabla
        if in_table and line.strip() == '---':
            in_table = False

    return blocks

def generate_gap_analysis():
    """Genera el análisis de gap completo."""

    print("Cargando datos...")
    current_cols = get_current_columns()
    coverage = get_data_coverage()
    schema_blocks = parse_schema_v5()

    total = coverage.get('_total', 0)

    # Mapeo de nombres (algunos campos tienen nombres diferentes)
    name_mapping = {
        'tech_skills': ['skills_tecnicas_list', 'hard_skills_list'],
        'soft_skills': ['soft_skills_list'],
        'herramientas': ['herramientas_list'],
        'idioma_principal': ['idiomas_list'],
        'beneficios': ['beneficios_list'],
        'tareas': ['tareas_list'],
        'tareas_explicitas': ['tareas_list'],
        'tareas_inferidas': [],
        'mision_rol': [],
        'titulo_requerido': ['nivel_educativo_especifico'],
        'conocimientos_especificos': ['conocimientos_list'],
        'perfil_actitudinal': [],
        'sistemas': [],
        'tecnologias': [],
        'marcas_especificas': [],
        'nivel_herramienta': [],
        'conocimiento_excluyente': [],
        'experiencia_descripcion': [],
        'experiencia_nivel_previo': [],
        'experiencia_areas': [],
        'experiencia_excluyente': [],
        'experiencia_valorada': [],
        'tipo_oferta': [],
        'calidad_texto': [],
        'largo_descripcion': [],
        'pasa_a_matching': [],
        'campos_con_fuente': [],
    }

    # Generar reporte
    report = []
    report.append("# Gap Analysis: NLP Schema v5 vs Implementación Actual")
    report.append("")
    report.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Total registros en ofertas_nlp:** {total:,}")
    report.append(f"**Columnas en BD:** {len(current_cols)}")
    report.append("")
    report.append("---")
    report.append("")

    # Resumen por bloque
    report.append("## Resumen por Bloque")
    report.append("")
    report.append("| # | Bloque | Campos Diseñados | Implementados | % | Con Datos |")
    report.append("|---|--------|------------------|---------------|---|-----------|")

    total_designed = 0
    total_implemented = 0
    block_details = {}

    for block_name, block_data in schema_blocks.items():
        designed = len(block_data['fields'])
        implemented = 0
        with_data = 0
        details = []

        for field in block_data['fields']:
            fname = field['name']
            total_designed += 1

            # Buscar en BD (nombre directo o mapeado)
            found_col = None
            if fname in current_cols:
                found_col = fname
            else:
                # Buscar en mapping
                alternatives = name_mapping.get(fname, [])
                for alt in alternatives:
                    if alt in current_cols:
                        found_col = alt
                        break

            if found_col:
                implemented += 1
                total_implemented += 1
                cov = coverage.get(found_col, {})
                pct = cov.get('pct', 0)
                if pct > 0:
                    with_data += 1
                details.append({
                    'schema_name': fname,
                    'db_name': found_col,
                    'status': 'OK',
                    'coverage_pct': pct,
                    'type_schema': field['type'],
                    'source': field['source']
                })
            else:
                details.append({
                    'schema_name': fname,
                    'db_name': None,
                    'status': 'FALTA',
                    'coverage_pct': 0,
                    'type_schema': field['type'],
                    'source': field['source']
                })

        block_details[block_name] = details
        pct_impl = round(100*implemented/designed, 0) if designed > 0 else 0
        report.append(f"| {block_data['num']} | {block_name} | {designed} | {implemented} | {pct_impl:.0f}% | {with_data} |")

    report.append("")
    report.append(f"**TOTAL:** {total_implemented}/{total_designed} campos implementados ({100*total_implemented/total_designed:.1f}%)")
    report.append("")
    report.append("---")
    report.append("")

    # Detalle por bloque
    report.append("## Detalle por Bloque")
    report.append("")

    for block_name, details in block_details.items():
        block_num = schema_blocks[block_name]['num']
        report.append(f"### Bloque {block_num}: {block_name}")
        report.append("")
        report.append("| Campo Schema | En BD | Col. BD | Cobertura | Tipo | Fuente |")
        report.append("|--------------|-------|---------|-----------|------|--------|")

        for d in details:
            status = "✓" if d['status'] == 'OK' else "✗"
            db_name = d['db_name'] if d['db_name'] else "-"
            cov = f"{d['coverage_pct']:.1f}%" if d['status'] == 'OK' else "-"
            report.append(f"| {d['schema_name']} | {status} | {db_name} | {cov} | {d['type_schema']} | {d['source']} |")

        report.append("")

    report.append("---")
    report.append("")

    # Campos críticos para matching
    report.append("## Campos Críticos para Matching")
    report.append("")
    report.append("| Prioridad | Campo | Estado | Cobertura | Impacto |")
    report.append("|-----------|-------|--------|-----------|---------|")

    critical_fields = [
        ('★★★★★', 'titulo', 'Determina ocupación'),
        ('★★★★★', 'tareas', 'Confirma ocupación'),
        ('★★★★★', 'area_funcional', 'Contexto sector'),
        ('★★★★★', 'nivel_seniority', 'Nivel jerárquico'),
        ('★★★★☆', 'tiene_gente_cargo', 'Jefe vs Individual'),
        ('★★★★☆', 'titulo_requerido', 'Ocupación específica'),
        ('★★★★☆', 'producto_servicio', 'Qué vende/produce'),
        ('★★★☆☆', 'tech_skills', 'Skills técnicas'),
        ('★★★☆☆', 'tecnologias', 'Stack técnico'),
        ('★★★☆☆', 'marcas_especificas', 'Conocimiento específico'),
        ('★★★☆☆', 'sector_empresa', 'Industria'),
        ('★★★☆☆', 'experiencia_nivel_previo', 'Nivel anterior'),
        ('★★☆☆☆', 'conocimientos_especificos', 'Dominio técnico'),
        ('★★☆☆☆', 'orientacion_estudios', 'Formación'),
        ('★☆☆☆☆', 'perfil_actitudinal', 'Contexto'),
    ]

    for priority, field, impact in critical_fields:
        # Buscar estado
        found = field in current_cols
        if not found:
            alternatives = name_mapping.get(field, [])
            for alt in alternatives:
                if alt in current_cols:
                    found = True
                    field_db = alt
                    break

        if found:
            cov = coverage.get(field_db if 'field_db' in dir() else field, {})
            cov_str = f"{cov.get('pct', 0):.1f}%"
            status = "✓ Implementado"
        else:
            cov_str = "-"
            status = "✗ FALTA"

        report.append(f"| {priority} | {field} | {status} | {cov_str} | {impact} |")

    report.append("")
    report.append("---")
    report.append("")

    # Cobertura de datos existentes
    report.append("## Cobertura de Datos (Campos Existentes)")
    report.append("")
    report.append("| Campo | Registros | % del Total |")
    report.append("|-------|-----------|-------------|")

    # Ordenar por cobertura descendente
    sorted_cov = sorted(
        [(k, v) for k, v in coverage.items() if k != '_total'],
        key=lambda x: x[1].get('pct', 0),
        reverse=True
    )

    for col, data in sorted_cov[:30]:  # Top 30
        report.append(f"| {col} | {data['count']:,} | {data['pct']:.1f}% |")

    report.append("")
    report.append("---")
    report.append("")

    # Campos faltantes críticos
    report.append("## Campos Faltantes Priorizados")
    report.append("")
    report.append("### Fase 1: Críticos (impactan matching)")
    report.append("")

    fase1 = ['tareas', 'area_funcional', 'nivel_seniority', 'titulo_requerido',
             'tecnologias', 'marcas_especificas', 'tiene_gente_cargo']

    for f in fase1:
        found = f in current_cols or any(alt in current_cols for alt in name_mapping.get(f, []))
        status = "✓" if found else "- [ ]"
        report.append(f"{status} `{f}`")

    report.append("")
    report.append("### Fase 2: Importantes")
    report.append("")

    fase2 = ['experiencia_nivel_previo', 'experiencia_areas', 'conocimientos_especificos',
             'producto_servicio', 'licencia_conducir']

    for f in fase2:
        found = f in current_cols or any(alt in current_cols for alt in name_mapping.get(f, []))
        status = "✓" if found else "- [ ]"
        report.append(f"{status} `{f}`")

    report.append("")
    report.append("### Fase 3: Calidad y Flags")
    report.append("")

    fase3 = ['tiene_requisitos_discriminatorios', 'calidad_redaccion', 'tipo_oferta',
             'certificaciones_requeridas']

    for f in fase3:
        found = f in current_cols or any(alt in current_cols for alt in name_mapping.get(f, []))
        status = "✓" if found else "- [ ]"
        report.append(f"{status} `{f}`")

    report.append("")
    report.append("---")
    report.append("")
    report.append("## Recomendaciones")
    report.append("")
    report.append("1. **Prioridad Alta:** Implementar extracción de `tareas[]` - impacto directo en matching ESCO")
    report.append("2. **Prioridad Alta:** Agregar `tiene_gente_cargo` para distinguir roles de liderazgo")
    report.append("3. **Prioridad Media:** Extraer `tecnologias[]` y `marcas_especificas[]` para skills técnicas")
    report.append("4. **Prioridad Media:** Mejorar detección de `nivel_seniority` desde título/descripción")
    report.append("5. **Calidad:** Implementar `tipo_oferta` para filtrar ofertas no-reales")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # Guardar reporte
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\nReporte guardado en: {OUTPUT_PATH}")
    print(f"\nResumen:")
    print(f"  - Campos diseñados (schema v5): {total_designed}")
    print(f"  - Campos implementados: {total_implemented}")
    print(f"  - % Implementación: {100*total_implemented/total_designed:.1f}%")

    return report

if __name__ == '__main__':
    generate_gap_analysis()
