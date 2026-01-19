#!/usr/bin/env python3
"""
Quality Analysis Script for NLP v6.0
=====================================

Analiza la calidad de las 6,531 ofertas procesadas con Hermes 3:8b
y genera reportes comprehensivos para determinar si proceder a FASE 2.

Métricas evaluadas:
- Coverage por cada uno de los 24 campos
- Quality score promedio y distribución
- Cobertura de 6 campos nuevos v6.0 vs targets
- Análisis por categoría
- Validación de arrays JSON

Outputs:
- quality_report_v6.0.csv (quality score por oferta)
- field_coverage_analysis.csv (coverage % por campo)
- category_performance.csv (performance por categoría)
- json_validation_errors.csv (errores de parsing JSON)
- quality_analysis_SUMMARY.md (reporte ejecutivo)

Uso:
    python quality_analysis_v6.py
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter
import statistics


class QualityAnalyzerV6:
    """Analizador de calidad para NLP v6.0"""

    # Definición de 24 campos del schema v6.0
    FIELD_DEFINITIONS = {
        # Campos CORE (críticos) - Target: >60% coverage
        'experiencia_min_anios': {'type': 'int', 'category': 'CORE', 'target': 60},
        'experiencia_max_anios': {'type': 'int', 'category': 'CORE', 'target': 60},
        'nivel_seniority': {'type': 'str', 'category': 'CORE', 'target': 60, 'new_v6': True},
        'skills_tecnicas_list': {'type': 'json_array', 'category': 'CORE', 'target': 60},
        'requisitos_excluyentes_list': {'type': 'json_array', 'category': 'CORE', 'target': 60},

        # Campos IMPORTANTES - Target: >40% coverage
        'sector_industria': {'type': 'str', 'category': 'IMPORTANT', 'target': 40, 'new_v6': True},
        'modalidad_trabajo': {'type': 'str', 'category': 'IMPORTANT', 'target': 40},
        'modalidad_contratacion': {'type': 'str', 'category': 'IMPORTANT', 'target': 40, 'new_v6': True},
        'soft_skills_list': {'type': 'json_array', 'category': 'IMPORTANT', 'target': 40},
        'beneficios_list': {'type': 'json_array', 'category': 'IMPORTANT', 'target': 40},
        'requisitos_deseables_list': {'type': 'json_array', 'category': 'IMPORTANT', 'target': 40},

        # Campos CONTEXTUALES - Target: >20% coverage
        'tecnologias_stack_list': {'type': 'json_array', 'category': 'CONTEXTUAL', 'target': 20, 'new_v6': True},
        'experiencia_cargo_previo': {'type': 'str', 'category': 'CONTEXTUAL', 'target': 20, 'new_v6': True},
        'disponibilidad_viajes': {'type': 'str', 'category': 'CONTEXTUAL', 'target': 20, 'new_v6': True},
        'certificaciones_list': {'type': 'json_array', 'category': 'CONTEXTUAL', 'target': 20},
        'formacion_requerida': {'type': 'str', 'category': 'CONTEXTUAL', 'target': 20},
        'jornada_laboral': {'type': 'str', 'category': 'CONTEXTUAL', 'target': 20},
        'tipo_puesto': {'type': 'str', 'category': 'CONTEXTUAL', 'target': 20},

        # Campos OPCIONALES - Target: >10% coverage
        'salario_min': {'type': 'int', 'category': 'OPTIONAL', 'target': 10},
        'salario_max': {'type': 'int', 'category': 'OPTIONAL', 'target': 10},
        'descripcion_empresa': {'type': 'str', 'category': 'OPTIONAL', 'target': 10},
        'vacantes': {'type': 'int', 'category': 'OPTIONAL', 'target': 10},
        'nivel_educativo': {'type': 'str', 'category': 'OPTIONAL', 'target': 10},
        'idiomas_requeridos': {'type': 'str', 'category': 'OPTIONAL', 'target': 10},
    }

    # Campos que son arrays JSON
    JSON_ARRAY_FIELDS = [
        'skills_tecnicas_list',
        'tecnologias_stack_list',
        'soft_skills_list',
        'certificaciones_list',
        'beneficios_list',
        'requisitos_excluyentes_list',
        'requisitos_deseables_list'
    ]

    # 6 campos nuevos v6.0
    NEW_V6_FIELDS = [
        'experiencia_cargo_previo',
        'tecnologias_stack_list',
        'sector_industria',
        'nivel_seniority',
        'modalidad_contratacion',
        'disponibilidad_viajes'
    ]

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.stats = {
            'total_offers': 0,
            'offers_processed_v6': 0,
            'avg_quality_score': 0,
            'field_coverage': {},
            'json_validation_errors': [],
            'quality_score_distribution': Counter(),
            'category_performance': {}
        }

    def analyze_all(self) -> Dict[str, Any]:
        """
        Ejecuta análisis completo de calidad

        Returns:
            Dict con todas las estadísticas
        """
        print("=" * 80)
        print("QUALITY ANALYSIS - NLP v6.0")
        print("=" * 80)
        print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base de datos: {self.db_path}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # PASO 1: Conteo general
            print("PASO 1: Conteo general de ofertas")
            print("-" * 80)

            cursor.execute("SELECT COUNT(*) FROM ofertas")
            self.stats['total_offers'] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT id_oferta)
                FROM ofertas_nlp_history
                WHERE nlp_version = '6.0.0'
            """)
            self.stats['offers_processed_v6'] = cursor.fetchone()[0]

            print(f"  Total ofertas en BD: {self.stats['total_offers']:,}")
            print(f"  Procesadas con v6.0.0: {self.stats['offers_processed_v6']:,}")
            print(f"  Coverage: {(self.stats['offers_processed_v6']/self.stats['total_offers'])*100:.1f}%\n")

            # PASO 2: Análisis de coverage por campo
            print("PASO 2: Coverage por campo (24 campos)")
            print("-" * 80)
            self._analyze_field_coverage(cursor)

            # PASO 3: Quality score distribution
            print("\nPASO 3: Distribución de Quality Score")
            print("-" * 80)
            self._analyze_quality_scores(cursor)

            # PASO 4: Validación de arrays JSON
            print("\nPASO 4: Validación de arrays JSON")
            print("-" * 80)
            self._validate_json_arrays(cursor)

            # PASO 5: Análisis por categoría (usando test set)
            print("\nPASO 5: Análisis por categoría")
            print("-" * 80)
            self._analyze_by_category(cursor)

            # PASO 6: Análisis específico de campos v6.0
            print("\nPASO 6: Análisis de 6 campos nuevos v6.0")
            print("-" * 80)
            self._analyze_v6_new_fields(cursor)

        finally:
            conn.close()

        return self.stats

    def _analyze_field_coverage(self, cursor):
        """Analiza coverage de cada campo"""

        print(f"\n{'Campo':<35} {'Coverage':>10} {'Target':>8} {'Status':>10}")
        print("-" * 80)

        # Cargar TODOS los extracted_data de una vez
        cursor.execute("""
            SELECT id_oferta, extracted_data
            FROM ofertas_nlp_history
            WHERE nlp_version = '6.0.0'
              AND extracted_data IS NOT NULL
        """)

        all_extracted_data = {}
        for id_oferta, extracted_json in cursor.fetchall():
            try:
                all_extracted_data[id_oferta] = json.loads(extracted_json)
            except:
                pass

        # Analizar coverage de cada campo
        for field, definition in self.FIELD_DEFINITIONS.items():
            # Contar ofertas con valor no-null
            count_non_null = sum(
                1 for data in all_extracted_data.values()
                if data.get(field) is not None
            )

            coverage_pct = (count_non_null / self.stats['offers_processed_v6'] * 100) if self.stats['offers_processed_v6'] > 0 else 0
            target = definition['target']

            # Determinar status
            if coverage_pct >= target:
                status = "OK"
            elif coverage_pct >= target * 0.8:
                status = "CLOSE"
            else:
                status = "LOW"

            self.stats['field_coverage'][field] = {
                'count': count_non_null,
                'coverage_pct': coverage_pct,
                'target': target,
                'status': status,
                'category': definition['category'],
                'new_v6': definition.get('new_v6', False)
            }

            # Marcar campos v6.0 con asterisco
            field_display = f"{field}*" if definition.get('new_v6') else field

            print(f"{field_display:<35} {coverage_pct:>9.1f}% {target:>7}% {status:>10}")

        # Resumen por categoría
        print("\n" + "-" * 80)
        print("RESUMEN POR CATEGORÍA DE CAMPO:")
        print("-" * 80)

        categories = defaultdict(list)
        for field, stats in self.stats['field_coverage'].items():
            categories[stats['category']].append(stats['coverage_pct'])

        for category in ['CORE', 'IMPORTANT', 'CONTEXTUAL', 'OPTIONAL']:
            if category in categories:
                avg_coverage = statistics.mean(categories[category])
                print(f"  {category:<15} Promedio: {avg_coverage:>6.1f}%")

    def _analyze_quality_scores(self, cursor):
        """Analiza distribución de quality scores"""

        cursor.execute("""
            SELECT id_oferta, quality_score
            FROM ofertas_nlp_history
            WHERE nlp_version = '6.0.0'
        """)

        quality_scores = []
        for id_oferta, quality_score in cursor.fetchall():
            quality_scores.append(quality_score)
            self.stats['quality_score_distribution'][quality_score] += 1

        if quality_scores:
            self.stats['avg_quality_score'] = statistics.mean(quality_scores)
            self.stats['median_quality_score'] = statistics.median(quality_scores)
            self.stats['min_quality_score'] = min(quality_scores)
            self.stats['max_quality_score'] = max(quality_scores)

            print(f"  Promedio: {self.stats['avg_quality_score']:.1f}/24 ({(self.stats['avg_quality_score']/24)*100:.1f}%)")
            print(f"  Mediana: {self.stats['median_quality_score']:.0f}/24")
            print(f"  Mínimo: {self.stats['min_quality_score']}/24")
            print(f"  Máximo: {self.stats['max_quality_score']}/24")

            # Distribución por rangos
            print("\n  Distribución por rangos:")
            ranges = {
                'Excelente (>17)': sum(1 for s in quality_scores if s > 17),
                'Bueno (14-17)': sum(1 for s in quality_scores if 14 <= s <= 17),
                'Aceptable (10-13)': sum(1 for s in quality_scores if 10 <= s <= 13),
                'Bajo (<10)': sum(1 for s in quality_scores if s < 10)
            }

            for range_name, count in ranges.items():
                pct = (count / len(quality_scores)) * 100
                print(f"    {range_name:<20} {count:>6} ({pct:>5.1f}%)")

    def _validate_json_arrays(self, cursor):
        """Valida que todos los arrays JSON sean parseables"""

        # Cargar TODOS los extracted_data
        cursor.execute("""
            SELECT id_oferta, extracted_data
            FROM ofertas_nlp_history
            WHERE nlp_version = '6.0.0'
              AND extracted_data IS NOT NULL
        """)

        all_extracted_data = {}
        for id_oferta, extracted_json in cursor.fetchall():
            try:
                all_extracted_data[id_oferta] = json.loads(extracted_json)
            except:
                pass

        total_errors = 0

        for field in self.JSON_ARRAY_FIELDS:
            field_errors = 0

            for id_oferta, data in all_extracted_data.items():
                json_value = data.get(field)

                if json_value is None:
                    continue

                # Verificar que sea string
                if not isinstance(json_value, str):
                    field_errors += 1
                    total_errors += 1
                    self.stats['json_validation_errors'].append({
                        'id_oferta': id_oferta,
                        'field': field,
                        'error_type': 'NOT_STRING',
                        'value': str(json_value)[:100]
                    })
                    continue

                # Intentar parsear JSON
                try:
                    parsed = json.loads(json_value)
                    if not isinstance(parsed, list):
                        field_errors += 1
                        total_errors += 1
                        self.stats['json_validation_errors'].append({
                            'id_oferta': id_oferta,
                            'field': field,
                            'error_type': 'NOT_ARRAY',
                            'value': json_value[:100]
                        })
                except json.JSONDecodeError as e:
                    field_errors += 1
                    total_errors += 1
                    self.stats['json_validation_errors'].append({
                        'id_oferta': id_oferta,
                        'field': field,
                        'error_type': 'INVALID_JSON',
                        'value': json_value[:100],
                        'error': str(e)
                    })

            status = "[OK] OK" if field_errors == 0 else f"[X] {field_errors} errors"
            print(f"  {field:<30} {status}")

        print(f"\n  Total errores JSON: {total_errors}")

        if total_errors > 0:
            print(f"  [!] {total_errors} campos JSON con errores de parsing")

    def _analyze_by_category(self, cursor):
        """Analiza performance por categoría usando el test set de 100 ofertas"""

        # Cargar categorías del test set
        test_csv = Path(self.db_path).parent / "selected_offers_100.csv"

        if not test_csv.exists():
            print("  [SKIP] selected_offers_100.csv no encontrado")
            return

        # Cargar categorías
        category_mapping = {}
        with open(test_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category_mapping[int(row['id_oferta'])] = row['categoria']

        # Analizar quality score por categoría
        cursor.execute("""
            SELECT id_oferta, quality_score
            FROM ofertas_nlp_history
            WHERE nlp_version = '6.0.0'
        """)

        category_scores = defaultdict(list)
        for id_oferta, quality_score in cursor.fetchall():
            if id_oferta in category_mapping:
                category = category_mapping[id_oferta]
                category_scores[category].append(quality_score)

        # Imprimir resultados
        print(f"\n{'Categoría':<25} {'Ofertas':>10} {'Avg Score':>12} {'Avg %':>10}")
        print("-" * 80)

        for category, scores in sorted(category_scores.items()):
            avg_score = statistics.mean(scores)
            avg_pct = (avg_score / 24) * 100

            self.stats['category_performance'][category] = {
                'count': len(scores),
                'avg_score': avg_score,
                'avg_pct': avg_pct,
                'min_score': min(scores),
                'max_score': max(scores)
            }

            print(f"{category:<25} {len(scores):>10} {avg_score:>11.1f}/24 {avg_pct:>9.1f}%")

    def _analyze_v6_new_fields(self, cursor):
        """Análisis específico de los 6 campos nuevos v6.0"""

        print(f"\n{'Campo v6.0':<35} {'Coverage':>10} {'Target':>8} {'Status':>10}")
        print("-" * 80)

        fields_meeting_target = 0

        for field in self.NEW_V6_FIELDS:
            stats = self.stats['field_coverage'].get(field)
            if stats:
                coverage = stats['coverage_pct']
                target = stats['target']
                status = stats['status']

                if coverage >= target:
                    fields_meeting_target += 1

                print(f"{field:<35} {coverage:>9.1f}% {target:>7}% {status:>10}")

        print("-" * 80)
        print(f"Campos v6.0 cumpliendo target: {fields_meeting_target}/6")

        if fields_meeting_target >= 4:
            print("[OK] CRITERIO CUMPLIDO: Al menos 4 de 6 campos cumplen target")
        else:
            print("[X] CRITERIO NO CUMPLIDO: Se requieren al menos 4 de 6 campos")

    def export_reports(self):
        """Exporta todos los reportes a CSV"""

        print("\n" + "=" * 80)
        print("EXPORTANDO REPORTES")
        print("=" * 80)

        output_dir = Path(self.db_path).parent

        # 1. quality_report_v6.0.csv
        self._export_quality_report(output_dir)

        # 2. field_coverage_analysis.csv
        self._export_field_coverage(output_dir)

        # 3. category_performance.csv
        self._export_category_performance(output_dir)

        # 4. json_validation_errors.csv
        self._export_json_errors(output_dir)

        print("\n[OK] Todos los reportes exportados")

    def _export_quality_report(self, output_dir: Path):
        """Exporta quality_report_v6.0.csv"""

        output_path = output_dir / "quality_report_v6.0.csv"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                h.id_oferta,
                o.titulo,
                h.quality_score,
                h.confidence_score,
                h.processing_time_ms,
                h.processed_at
            FROM ofertas_nlp_history h
            JOIN ofertas o ON h.id_oferta = o.id_oferta
            WHERE h.nlp_version = '6.0.0'
            ORDER BY h.quality_score DESC
        """)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id_oferta', 'titulo', 'quality_score', 'quality_pct',
                'confidence_score', 'processing_time_ms', 'processed_at'
            ])

            for row in cursor.fetchall():
                id_oferta, titulo, quality_score, confidence, proc_time, processed_at = row
                quality_pct = (quality_score / 24) * 100
                writer.writerow([
                    id_oferta, titulo, quality_score, f"{quality_pct:.1f}",
                    f"{confidence:.2f}" if confidence else "N/A",
                    proc_time, processed_at
                ])

        conn.close()
        print(f"  [1/4] {output_path.name}")

    def _export_field_coverage(self, output_dir: Path):
        """Exporta field_coverage_analysis.csv"""

        output_path = output_dir / "field_coverage_analysis.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'field', 'category', 'new_v6', 'count', 'coverage_pct',
                'target', 'status', 'meets_target'
            ])

            for field, stats in sorted(self.stats['field_coverage'].items()):
                meets_target = 'YES' if stats['coverage_pct'] >= stats['target'] else 'NO'
                writer.writerow([
                    field,
                    stats['category'],
                    'YES' if stats.get('new_v6') else 'NO',
                    stats['count'],
                    f"{stats['coverage_pct']:.2f}",
                    stats['target'],
                    stats['status'],
                    meets_target
                ])

        print(f"  [2/4] {output_path.name}")

    def _export_category_performance(self, output_dir: Path):
        """Exporta category_performance.csv"""

        output_path = output_dir / "category_performance.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'category', 'count', 'avg_score', 'avg_pct',
                'min_score', 'max_score'
            ])

            for category, stats in sorted(self.stats['category_performance'].items()):
                writer.writerow([
                    category,
                    stats['count'],
                    f"{stats['avg_score']:.2f}",
                    f"{stats['avg_pct']:.2f}",
                    stats['min_score'],
                    stats['max_score']
                ])

        print(f"  [3/4] {output_path.name}")

    def _export_json_errors(self, output_dir: Path):
        """Exporta json_validation_errors.csv"""

        output_path = output_dir / "json_validation_errors.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id_oferta', 'field', 'error_type', 'value', 'error_detail'
            ])

            for error in self.stats['json_validation_errors']:
                writer.writerow([
                    error['id_oferta'],
                    error['field'],
                    error['error_type'],
                    error['value'],
                    error.get('error', '')
                ])

        print(f"  [4/4] {output_path.name}")

    def generate_summary_report(self):
        """Genera reporte ejecutivo en Markdown"""

        print("\n" + "=" * 80)
        print("GENERANDO REPORTE EJECUTIVO")
        print("=" * 80)

        output_dir = Path(self.db_path).parent
        output_path = output_dir / "quality_analysis_SUMMARY.md"

        # Determinar escenario según decision tree
        scenario = self._determine_scenario()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_content(scenario))

        print(f"\n[OK] Reporte generado: {output_path.name}")
        print(f"\n{'=' * 80}")
        print(f"RECOMENDACIÓN FINAL: {scenario['name']}")
        print(f"{'=' * 80}")
        print(f"\n{scenario['recommendation']}\n")

    def _determine_scenario(self) -> Dict[str, str]:
        """Determina escenario según decision tree"""

        avg_quality_pct = (self.stats['avg_quality_score'] / 24) * 100

        # Contar campos críticos que cumplen target
        core_fields_ok = sum(
            1 for field, stats in self.stats['field_coverage'].items()
            if self.FIELD_DEFINITIONS[field]['category'] == 'CORE'
            and stats['coverage_pct'] >= stats['target']
        )

        # Contar campos v6.0 que cumplen target
        v6_fields_ok = sum(
            1 for field in self.NEW_V6_FIELDS
            if self.stats['field_coverage'][field]['coverage_pct'] >= self.stats['field_coverage'][field]['target']
        )

        # Decision tree
        if avg_quality_pct > 70 and core_fields_ok >= 4:
            return {
                'name': 'ESCENARIO A - CALIDAD EXCELENTE',
                'code': 'A',
                'recommendation': '[OK] PROCEDER DIRECTAMENTE A FASE 2 DASHBOARD',
                'details': 'La calidad de los datos es excelente. Se puede comenzar FASE 2 con confianza.'
            }
        elif avg_quality_pct >= 60 and core_fields_ok >= 3:
            return {
                'name': 'ESCENARIO B - CALIDAD BUENA',
                'code': 'B',
                'recommendation': '[OK] PROCEDER A FASE 2 con notas sobre campos débiles',
                'details': 'La calidad es buena. Se puede proceder a FASE 2, teniendo en cuenta las limitaciones en algunos campos.'
            }
        elif avg_quality_pct >= 50 and core_fields_ok >= 2:
            return {
                'name': 'ESCENARIO C - CALIDAD ACEPTABLE (Necesita mejora)',
                'code': 'C',
                'recommendation': '[!] REFINAR PROMPT v6.1, reprocesar ofertas con quality score <12, LUEGO FASE 2',
                'details': 'La calidad es aceptable pero mejorable. Se recomienda refinamiento antes de FASE 2.'
            }
        else:
            return {
                'name': 'ESCENARIO D - CALIDAD INSUFICIENTE',
                'code': 'D',
                'recommendation': '[X] MAJOR REVISION necesaria antes de continuar',
                'details': 'La calidad no cumple los estándares mínimos. Se requiere revisión profunda del sistema NLP.'
            }

    def _generate_markdown_content(self, scenario: Dict[str, str]) -> str:
        """Genera contenido del reporte en Markdown"""

        content = f"""# Quality Analysis Report - NLP v6.0
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Base de datos:** `{Path(self.db_path).name}`
**Modelo:** Hermes 3:8b

---

## RESUMEN EJECUTIVO

### Estadísticas Generales
- **Total ofertas en BD:** {self.stats['total_offers']:,}
- **Procesadas con v6.0:** {self.stats['offers_processed_v6']:,} ({(self.stats['offers_processed_v6']/self.stats['total_offers'])*100:.1f}%)
- **Quality Score Promedio:** {self.stats['avg_quality_score']:.1f}/24 ({(self.stats['avg_quality_score']/24)*100:.1f}%)
- **Quality Score Mediana:** {self.stats.get('median_quality_score', 0):.0f}/24
- **Rango:** {self.stats.get('min_quality_score', 0)} - {self.stats.get('max_quality_score', 0)}

### Criterios de Calidad Evaluados

| Criterio | Target | Resultado | Status |
|----------|--------|-----------|--------|
| Quality Score Promedio | >60% | {(self.stats['avg_quality_score']/24)*100:.1f}% | {'[OK] CUMPLE' if (self.stats['avg_quality_score']/24)*100 > 60 else '[X] NO CUMPLE'} |
| Campos CORE >60% coverage | 5/5 | {sum(1 for f, s in self.stats['field_coverage'].items() if self.FIELD_DEFINITIONS[f]['category'] == 'CORE' and s['coverage_pct'] >= 60)}/5 | {'[OK] CUMPLE' if sum(1 for f, s in self.stats['field_coverage'].items() if self.FIELD_DEFINITIONS[f]['category'] == 'CORE' and s['coverage_pct'] >= 60) >= 4 else '[X] NO CUMPLE'} |
| Campos v6.0 cumpliendo target | 4/6 | {sum(1 for f in self.NEW_V6_FIELDS if self.stats['field_coverage'][f]['coverage_pct'] >= self.stats['field_coverage'][f]['target'])}/6 | {'[OK] CUMPLE' if sum(1 for f in self.NEW_V6_FIELDS if self.stats['field_coverage'][f]['coverage_pct'] >= self.stats['field_coverage'][f]['target']) >= 4 else '[X] NO CUMPLE'} |
| Arrays JSON válidos | 100% | {((len(self.stats.get('json_validation_errors', [])) == 0) and '100%') or f'{100 - (len(self.stats.get("json_validation_errors", [])) / self.stats["offers_processed_v6"] * 100):.1f}%'} | {'[OK] CUMPLE' if len(self.stats.get('json_validation_errors', [])) == 0 else '[!] ERRORES'} |

---

## RECOMENDACIÓN FINAL

### {scenario['name']}

**DECISIÓN:** {scenario['recommendation']}

**Detalles:** {scenario['details']}

---

## ANÁLISIS DETALLADO

### 1. Coverage por Categoría de Campo

"""

        # Coverage por categoría
        categories = defaultdict(list)
        for field, stats in self.stats['field_coverage'].items():
            categories[stats['category']].append(stats['coverage_pct'])

        content += "| Categoría | Promedio Coverage | Campos | Target General |\n"
        content += "|-----------|-------------------|--------|----------------|\n"

        for category in ['CORE', 'IMPORTANT', 'CONTEXTUAL', 'OPTIONAL']:
            if category in categories:
                avg = statistics.mean(categories[category])
                count = len(categories[category])
                target_map = {'CORE': '>60%', 'IMPORTANT': '>40%', 'CONTEXTUAL': '>20%', 'OPTIONAL': '>10%'}
                content += f"| {category} | {avg:.1f}% | {count} | {target_map.get(category, 'N/A')} |\n"

        # Campos v6.0
        content += "\n### 2. Campos Nuevos v6.0\n\n"
        content += "| Campo | Coverage | Target | Status |\n"
        content += "|-------|----------|--------|--------|\n"

        for field in self.NEW_V6_FIELDS:
            stats = self.stats['field_coverage'][field]
            content += f"| `{field}` | {stats['coverage_pct']:.1f}% | {stats['target']}% | {stats['status']} |\n"

        # Distribución quality score
        content += "\n### 3. Distribución de Quality Score\n\n"
        content += "| Rango | Cantidad | Porcentaje |\n"
        content += "|-------|----------|------------|\n"

        total_offers = self.stats['offers_processed_v6']
        ranges = {
            'Excelente (>17)': sum(count for score, count in self.stats['quality_score_distribution'].items() if score > 17),
            'Bueno (14-17)': sum(count for score, count in self.stats['quality_score_distribution'].items() if 14 <= score <= 17),
            'Aceptable (10-13)': sum(count for score, count in self.stats['quality_score_distribution'].items() if 10 <= score <= 13),
            'Bajo (<10)': sum(count for score, count in self.stats['quality_score_distribution'].items() if score < 10)
        }

        for range_name, count in ranges.items():
            pct = (count / total_offers * 100) if total_offers > 0 else 0
            content += f"| {range_name} | {count:,} | {pct:.1f}% |\n"

        # Performance por categoría
        if self.stats['category_performance']:
            content += "\n### 4. Performance por Categoría (Test Set)\n\n"
            content += "| Categoría | Ofertas | Avg Score | Avg % |\n"
            content += "|-----------|---------|-----------|-------|\n"

            for category, perf in sorted(self.stats['category_performance'].items()):
                content += f"| {category} | {perf['count']} | {perf['avg_score']:.1f}/24 | {perf['avg_pct']:.1f}% |\n"

        # Errores JSON
        content += "\n### 5. Validación de Arrays JSON\n\n"

        if len(self.stats.get('json_validation_errors', [])) == 0:
            content += "[OK] **Todos los arrays JSON son válidos** (0 errores)\n"
        else:
            content += f"[!] **{len(self.stats['json_validation_errors'])} errores de parsing JSON encontrados**\n\n"
            content += "Ver archivo `json_validation_errors.csv` para detalles.\n"

        # Próximos pasos
        content += "\n---\n\n## PRÓXIMOS PASOS\n\n"

        if scenario['code'] == 'A':
            content += """
1. [OK] **INICIAR FASE 2 - Dashboard Renovado**
   - Comenzar con diseño de arquitectura
   - Definir visualizaciones basadas en campos disponibles
   - Timeline: 4 semanas
2. Monitorear campos con coverage <60% para futuras mejoras
3. Documentar limitaciones conocidas para el equipo de desarrollo
"""
        elif scenario['code'] == 'B':
            content += """
1. [OK] **PROCEDER A FASE 2** con las siguientes notas:
   - Identificar campos débiles y documentar limitaciones
   - Considerar visualizaciones alternativas para campos con baja coverage
   - Timeline: 4 semanas
2. Planificar mejoras incrementales para v6.1 en paralelo
3. Validar manualmente 50 ofertas para confirmar accuracy
"""
        elif scenario['code'] == 'C':
            content += """
1. [!] **REFINAR PROMPTS** antes de FASE 2:
   - Identificar campos con coverage <target
   - Revisar y mejorar prompts específicos
   - Crear v6.1 con mejoras
2. **REPROCESAR ofertas con quality score <12**
   - Identificar ~{sum(1 for s in self.stats['quality_score_distribution'] if s < 12)} ofertas
   - Aplicar prompts mejorados
3. **RE-ANALIZAR calidad** post-mejoras
4. **ENTONCES proceder a FASE 2** (si mejora es suficiente)
"""
        else:  # D
            content += """
1. [X] **MAJOR REVISION REQUERIDA**:
   - Investigar root causes de baja calidad
   - Considerar cambios estructurales:
     - ¿Modelo diferente?
     - ¿Más regex, menos LLM?
     - ¿Prompts completamente rediseñados?
     - ¿Datos de entrada tienen problemas?
2. Crear plan de remediación detallado
3. Re-testear con 100 ofertas antes de producción
4. Solo entonces considerar FASE 2
"""

        content += "\n---\n\n"
        content += f"**Reporte generado automáticamente por:** `quality_analysis_v6.py`  \n"
        content += f"**Timestamp:** {datetime.now().isoformat()}  \n"

        return content


def main():
    """Ejecuta el análisis completo"""

    db_path = Path(__file__).parent / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    # Inicializar analizador
    analyzer = QualityAnalyzerV6(str(db_path))

    try:
        # Ejecutar análisis
        results = analyzer.analyze_all()

        # Exportar reportes
        analyzer.export_reports()

        # Generar reporte ejecutivo
        analyzer.generate_summary_report()

        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO")
        print("=" * 80)
        print("\nARCHIVOS GENERADOS:")
        print("  1. quality_report_v6.0.csv - Quality score por oferta")
        print("  2. field_coverage_analysis.csv - Coverage % por campo")
        print("  3. category_performance.csv - Performance por categoría")
        print("  4. json_validation_errors.csv - Errores de JSON parsing")
        print("  5. quality_analysis_SUMMARY.md - Reporte ejecutivo con recomendación\n")

    except Exception as e:
        print(f"\nERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
