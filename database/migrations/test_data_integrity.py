#!/usr/bin/env python3
"""
Tests de Integridad de Datos - FASE 1 Migración
================================================

Valida integridad de la base de datos antes y después de la migración.
Detecta inconsistencias, duplicados, problemas de encoding, etc.

Uso:
    python test_data_integrity.py
    python test_data_integrity.py --db /path/to/database.db
    python test_data_integrity.py --report
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import hashlib


class DataIntegrityTester:
    """Tester de integridad de datos para base de datos de scraping"""

    def __init__(self, db_path: Path):
        """
        Args:
            db_path: Path a la base de datos a testear
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'database': str(self.db_path),
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_warnings': 0,
            'issues': []
        }

    def connect(self):
        """Conecta a la base de datos"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Cierra conexión"""
        if self.conn:
            self.conn.close()

    def log_issue(self, severity: str, test: str, message: str, details: dict = None):
        """
        Registra un issue encontrado

        Args:
            severity: 'PASS', 'FAIL', 'WARNING'
            test: Nombre del test
            message: Descripción del issue
            details: Dict con detalles adicionales
        """
        issue = {
            'severity': severity,
            'test': test,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        if details:
            issue['details'] = details

        self.results['issues'].append(issue)

        if severity == 'PASS':
            self.results['tests_passed'] += 1
        elif severity == 'FAIL':
            self.results['tests_failed'] += 1
        elif severity == 'WARNING':
            self.results['tests_warnings'] += 1

    # ========================================================================
    # TEST 1: INTEGRIDAD BÁSICA DE SCHEMA
    # ========================================================================

    def test_schema_integrity(self):
        """Verifica integridad básica del schema"""
        print("[TEST 1] Verificando integridad del schema...")

        cursor = self.conn.cursor()

        # 1.1 Verificar que existen tablas críticas
        expected_tables = [
            'ofertas',
            'ofertas_nlp',
            'esco_occupations',
            'esco_skills',
            'ofertas_esco_matching'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing_tables = [t for t in expected_tables if t not in existing_tables]

        if missing_tables:
            self.log_issue(
                'FAIL',
                'schema_tables',
                f'Faltan {len(missing_tables)} tablas críticas',
                {'missing_tables': missing_tables}
            )
        else:
            self.log_issue(
                'PASS',
                'schema_tables',
                f'Todas las {len(expected_tables)} tablas críticas existen'
            )

        # 1.2 Ejecutar PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]

        if result == "ok":
            self.log_issue('PASS', 'pragma_integrity', 'PRAGMA integrity_check: OK')
        else:
            self.log_issue('FAIL', 'pragma_integrity', f'PRAGMA integrity_check falló: {result}')

    # ========================================================================
    # TEST 2: OFERTAS - DUPLICADOS Y NULLS
    # ========================================================================

    def test_ofertas_integrity(self):
        """Verifica integridad de la tabla ofertas"""
        print("[TEST 2] Verificando integridad de ofertas...")

        cursor = self.conn.cursor()

        # 2.1 Contar ofertas totales
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_ofertas = cursor.fetchone()[0]

        print(f"   Total ofertas: {total_ofertas:,}")

        # 2.2 Verificar duplicados por id_oferta
        cursor.execute("""
            SELECT id_oferta, COUNT(*) as count
            FROM ofertas
            GROUP BY id_oferta
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()

        if duplicates:
            self.log_issue(
                'FAIL',
                'ofertas_duplicates',
                f'Encontrados {len(duplicates)} id_oferta duplicados',
                {'duplicates': [dict(row) for row in duplicates[:10]]}
            )
        else:
            self.log_issue('PASS', 'ofertas_duplicates', 'Sin duplicados en id_oferta')

        # 2.3 Verificar campos críticos NULL
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE id_oferta IS NULL OR titulo IS NULL
        """)
        nulls = cursor.fetchone()[0]

        if nulls > 0:
            self.log_issue('FAIL', 'ofertas_nulls', f'{nulls} ofertas con id_oferta o titulo NULL')
        else:
            self.log_issue('PASS', 'ofertas_nulls', 'Sin NULLs en campos críticos')

        # 2.4 Verificar ofertas sin descripción
        cursor.execute("SELECT COUNT(*) FROM ofertas WHERE descripcion IS NULL OR descripcion = ''")
        sin_descripcion = cursor.fetchone()[0]

        if sin_descripcion > 0:
            porcentaje = (sin_descripcion / total_ofertas) * 100
            self.log_issue(
                'WARNING',
                'ofertas_sin_descripcion',
                f'{sin_descripcion} ofertas sin descripción ({porcentaje:.1f}%)',
                {'count': sin_descripcion, 'percentage': porcentaje}
            )
        else:
            self.log_issue('PASS', 'ofertas_sin_descripcion', '100% ofertas tienen descripción')

    # ========================================================================
    # TEST 3: OFERTAS_NLP - COBERTURA Y CALIDAD
    # ========================================================================

    def test_nlp_coverage(self):
        """Verifica cobertura y calidad de procesamiento NLP"""
        print("[TEST 3] Verificando cobertura NLP...")

        cursor = self.conn.cursor()

        # 3.1 Contar ofertas con NLP
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_ofertas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
        total_nlp = cursor.fetchone()[0]

        cobertura = (total_nlp / total_ofertas) * 100 if total_ofertas > 0 else 0

        if cobertura >= 95:
            self.log_issue(
                'PASS',
                'nlp_coverage',
                f'Cobertura NLP: {cobertura:.1f}% ({total_nlp}/{total_ofertas})'
            )
        elif cobertura >= 80:
            self.log_issue(
                'WARNING',
                'nlp_coverage',
                f'Cobertura NLP baja: {cobertura:.1f}%',
                {'ofertas_totales': total_ofertas, 'ofertas_nlp': total_nlp}
            )
        else:
            self.log_issue(
                'FAIL',
                'nlp_coverage',
                f'Cobertura NLP crítica: {cobertura:.1f}%',
                {'ofertas_totales': total_ofertas, 'ofertas_nlp': total_nlp}
            )

        # 3.2 Verificar campos vacíos en NLP
        cursor.execute("""
            SELECT
                SUM(CASE WHEN experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) as con_experiencia,
                SUM(CASE WHEN nivel_educativo IS NOT NULL THEN 1 ELSE 0 END) as con_educacion,
                SUM(CASE WHEN skills_tecnicas_list IS NOT NULL THEN 1 ELSE 0 END) as con_skills_tecnicas,
                SUM(CASE WHEN soft_skills_list IS NOT NULL THEN 1 ELSE 0 END) as con_soft_skills,
                COUNT(*) as total
            FROM ofertas_nlp
        """)

        row = cursor.fetchone()
        stats = {
            'experiencia': (row[0] / row[4]) * 100 if row[4] > 0 else 0,
            'educacion': (row[1] / row[4]) * 100 if row[4] > 0 else 0,
            'skills_tecnicas': (row[2] / row[4]) * 100 if row[4] > 0 else 0,
            'soft_skills': (row[3] / row[4]) * 100 if row[4] > 0 else 0
        }

        print(f"   Cobertura por campo:")
        print(f"      Experiencia:     {stats['experiencia']:.1f}%")
        print(f"      Educación:       {stats['educacion']:.1f}%")
        print(f"      Skills técnicas: {stats['skills_tecnicas']:.1f}%")
        print(f"      Soft skills:     {stats['soft_skills']:.1f}%")

        # Calcular efectividad promedio
        efectividad_promedio = sum(stats.values()) / len(stats)

        if efectividad_promedio >= 80:
            self.log_issue(
                'PASS',
                'nlp_effectiveness',
                f'Efectividad NLP: {efectividad_promedio:.1f}%',
                stats
            )
        elif efectividad_promedio >= 60:
            self.log_issue(
                'WARNING',
                'nlp_effectiveness',
                f'Efectividad NLP baja: {efectividad_promedio:.1f}%',
                stats
            )
        else:
            self.log_issue(
                'FAIL',
                'nlp_effectiveness',
                f'Efectividad NLP crítica: {efectividad_promedio:.1f}%',
                stats
            )

    # ========================================================================
    # TEST 4: ESCO - INTEGRIDAD Y COBERTURA
    # ========================================================================

    def test_esco_integrity(self):
        """Verifica integridad de tablas ESCO"""
        print("[TEST 4] Verificando integridad ESCO...")

        cursor = self.conn.cursor()

        # 4.1 Contar registros ESCO
        cursor.execute("SELECT COUNT(*) FROM esco_occupations")
        total_occupations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM esco_skills")
        total_skills = cursor.fetchone()[0]

        print(f"   ESCO Occupations: {total_occupations:,}")
        print(f"   ESCO Skills:      {total_skills:,}")

        # 4.2 CRITICAL: Verificar bug de skills
        if total_skills < 100:
            self.log_issue(
                'FAIL',
                'esco_skills_count',
                f'CRITICAL BUG: Solo {total_skills} skills (esperado: ~13,890)',
                {
                    'actual': total_skills,
                    'expected': 13890,
                    'bug_location': 'populate_esco_from_rdf.py líneas 200-300'
                }
            )
        elif total_skills < 10000:
            self.log_issue(
                'WARNING',
                'esco_skills_count',
                f'Skills incompletas: {total_skills} (esperado: ~13,890)',
                {'actual': total_skills, 'expected': 13890}
            )
        else:
            self.log_issue(
                'PASS',
                'esco_skills_count',
                f'ESCO skills completas: {total_skills:,}'
            )

        # 4.3 Verificar ocupaciones con skills asociadas
        cursor.execute("""
            SELECT COUNT(DISTINCT occupation_uri)
            FROM esco_occupation_essential_skills
        """)
        occupations_with_skills = cursor.fetchone()[0]

        if total_occupations > 0:
            porcentaje = (occupations_with_skills / total_occupations) * 100

            if porcentaje >= 80:
                self.log_issue(
                    'PASS',
                    'esco_occupation_skills',
                    f'{porcentaje:.1f}% ocupaciones con skills asociadas'
                )
            else:
                self.log_issue(
                    'WARNING',
                    'esco_occupation_skills',
                    f'Solo {porcentaje:.1f}% ocupaciones con skills',
                    {'with_skills': occupations_with_skills, 'total': total_occupations}
                )

    # ========================================================================
    # TEST 5: MATCHING - OFERTAS ↔ ESCO
    # ========================================================================

    def test_esco_matching(self):
        """Verifica matching entre ofertas y ESCO"""
        print("[TEST 5] Verificando matching ESCO...")

        cursor = self.conn.cursor()

        # 5.1 Contar ofertas con matching
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_ofertas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT oferta_id) FROM ofertas_esco_matching")
        ofertas_matched = cursor.fetchone()[0]

        cobertura = (ofertas_matched / total_ofertas) * 100 if total_ofertas > 0 else 0

        if cobertura >= 90:
            self.log_issue(
                'PASS',
                'esco_matching_coverage',
                f'Cobertura matching: {cobertura:.1f}% ({ofertas_matched}/{total_ofertas})'
            )
        elif cobertura >= 70:
            self.log_issue(
                'WARNING',
                'esco_matching_coverage',
                f'Cobertura matching baja: {cobertura:.1f}%',
                {'matched': ofertas_matched, 'total': total_ofertas}
            )
        else:
            self.log_issue(
                'FAIL',
                'esco_matching_coverage',
                f'Cobertura matching crítica: {cobertura:.1f}%',
                {'matched': ofertas_matched, 'total': total_ofertas}
            )

        # 5.2 Verificar confianza de matching
        cursor.execute("""
            SELECT
                AVG(occupation_confidence) as avg_occupation_conf,
                AVG(skills_confidence) as avg_skills_conf
            FROM ofertas_esco_matching
        """)

        row = cursor.fetchone()
        if row[0] is not None:
            avg_occupation = row[0] * 100
            avg_skills = row[1] * 100 if row[1] else 0

            print(f"   Confianza promedio:")
            print(f"      Occupation: {avg_occupation:.1f}%")
            print(f"      Skills:     {avg_skills:.1f}%")

            if avg_occupation >= 70:
                self.log_issue(
                    'PASS',
                    'esco_matching_confidence',
                    f'Confianza matching: {avg_occupation:.1f}%'
                )
            else:
                self.log_issue(
                    'WARNING',
                    'esco_matching_confidence',
                    f'Confianza matching baja: {avg_occupation:.1f}%'
                )

    # ========================================================================
    # TEST 6: ENCODING Y TEXTO
    # ========================================================================

    def test_encoding_issues(self):
        """Detecta problemas de encoding"""
        print("[TEST 6] Verificando encoding...")

        cursor = self.conn.cursor()

        # 6.1 Buscar caracteres mal encodificados comunes
        problematic_patterns = [
            ('Ã³', 'ó'),  # órdenes → Ã³rdenes
            ('Ã¡', 'á'),  # análisis → anÃ¡lisis
            ('Ã©', 'é'),  # café → cafÃ©
            ('Ã±', 'ñ'),  # español → espaÃ±ol
            ('â€', '"'),  # comillas
        ]

        total_encoding_issues = 0

        for bad_char, _ in problematic_patterns:
            cursor.execute(f"""
                SELECT COUNT(*) FROM ofertas
                WHERE titulo LIKE '%{bad_char}%' OR descripcion LIKE '%{bad_char}%'
            """)
            count = cursor.fetchone()[0]
            total_encoding_issues += count

        if total_encoding_issues == 0:
            self.log_issue('PASS', 'encoding_issues', 'Sin problemas de encoding detectados')
        else:
            self.log_issue(
                'WARNING',
                'encoding_issues',
                f'{total_encoding_issues} ofertas con posibles problemas de encoding',
                {'count': total_encoding_issues}
            )

    # ========================================================================
    # TEST 7: CONSISTENCIA TEMPORAL
    # ========================================================================

    def test_temporal_consistency(self):
        """Verifica consistencia de fechas"""
        print("[TEST 7] Verificando consistencia temporal...")

        cursor = self.conn.cursor()

        # 7.1 Verificar fechas futuras (imposibles)
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE fecha_publicacion > datetime('now')
        """)
        future_dates = cursor.fetchone()[0]

        if future_dates > 0:
            self.log_issue(
                'FAIL',
                'temporal_future_dates',
                f'{future_dates} ofertas con fecha_publicacion en el futuro'
            )
        else:
            self.log_issue('PASS', 'temporal_future_dates', 'Sin fechas futuras detectadas')

        # 7.2 Verificar rango razonable (últimos 2 años)
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE fecha_publicacion < datetime('now', '-2 years')
        """)
        very_old = cursor.fetchone()[0]

        if very_old > 0:
            cursor.execute("SELECT COUNT(*) FROM ofertas")
            total = cursor.fetchone()[0]
            porcentaje = (very_old / total) * 100

            self.log_issue(
                'WARNING',
                'temporal_very_old',
                f'{very_old} ofertas con más de 2 años ({porcentaje:.1f}%)'
            )

    # ========================================================================
    # MÉTODO PRINCIPAL
    # ========================================================================

    def run_all_tests(self):
        """Ejecuta todos los tests de integridad"""
        print("=" * 70)
        print("TESTS DE INTEGRIDAD DE DATOS")
        print("=" * 70)
        print(f"Base de datos: {self.db_path}")
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            self.connect()

            # Ejecutar tests
            self.test_schema_integrity()
            self.test_ofertas_integrity()
            self.test_nlp_coverage()
            self.test_esco_integrity()
            self.test_esco_matching()
            self.test_encoding_issues()
            self.test_temporal_consistency()

        finally:
            self.close()

        # Reporte final
        print()
        print("=" * 70)
        print("REPORTE FINAL")
        print("=" * 70)
        print(f"Tests ejecutados: {self.results['tests_passed'] + self.results['tests_failed'] + self.results['tests_warnings']}")
        print(f"  [PASS]    {self.results['tests_passed']}")
        print(f"  [FAIL]    {self.results['tests_failed']}")
        print(f"  [WARNING] {self.results['tests_warnings']}")
        print()

        # Mostrar issues críticos
        if self.results['tests_failed'] > 0:
            print("ISSUES CRÍTICOS (FAIL):")
            for issue in self.results['issues']:
                if issue['severity'] == 'FAIL':
                    print(f"  ❌ [{issue['test']}] {issue['message']}")
            print()

        # Mostrar warnings
        if self.results['tests_warnings'] > 0:
            print("WARNINGS:")
            for issue in self.results['issues']:
                if issue['severity'] == 'WARNING':
                    print(f"  ⚠️  [{issue['test']}] {issue['message']}")
            print()

        # Conclusión
        if self.results['tests_failed'] == 0:
            print("✅ INTEGRIDAD VERIFICADA - Base de datos en buen estado")
            return 0
        else:
            print("❌ ISSUES CRÍTICOS DETECTADOS - Revisar antes de migración")
            return 1

    def export_report(self, output_path: Path):
        """Exporta reporte completo a JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"[OK] Reporte exportado: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Tests de integridad de datos para base de datos de scraping'
    )
    parser.add_argument(
        '--db',
        default='D:/OEDE/Webscrapping/database/bumeran_scraping.db',
        help='Path a la base de datos (default: database/bumeran_scraping.db)'
    )
    parser.add_argument(
        '--report',
        help='Path para exportar reporte JSON'
    )

    args = parser.parse_args()

    # Ejecutar tests
    tester = DataIntegrityTester(db_path=Path(args.db))
    exit_code = tester.run_all_tests()

    # Exportar reporte si se solicita
    if args.report:
        tester.export_report(Path(args.report))

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
