#!/usr/bin/env python3
"""
Script de Validación de Calidad de Datos para Dashboard Shiny
=============================================================

Valida que los datos en la base de datos cumplen con los requisitos
mínimos de calidad antes de generar el CSV para el dashboard Shiny.

Niveles de validación:
- CRÍTICO: Bloquea generación de CSV si falla
- IMPORTANTE: Genera alertas pero permite continuar
- ADVERTENCIA: Información para monitoreo

Uso:
    python validate_shiny_data_quality.py
    python validate_shiny_data_quality.py --nivel critico
    python validate_shiny_data_quality.py --json
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ValidationRule:
    """Regla de validación"""
    column: str
    description: str
    threshold: float
    level: str  # 'critico', 'importante', 'advertencia'
    check_type: str  # 'not_null', 'not_empty', 'valid_format', 'boolean_true'


class DataQualityValidator:
    """Validador de calidad de datos para Dashboard Shiny"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "bumeran_scraping.db"

        self.db_path = Path(db_path)
        self.conn = None
        self.results = {
            'critico': [],
            'importante': [],
            'advertencia': []
        }
        self.stats = {}

    def conectar_db(self):
        """Conecta a la base de datos"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)

    def obtener_total_ofertas(self) -> int:
        """Obtiene el total de ofertas en la base de datos"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        return cursor.fetchone()[0]

    def validar_columna_no_nula(self, tabla: str, columna: str) -> Tuple[int, int]:
        """
        Valida que una columna no sea NULL

        Returns:
            (total_rows, non_null_rows)
        """
        cursor = self.conn.cursor()

        # Total de filas
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cursor.fetchone()[0]

        # Filas con valor no nulo
        cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {columna} IS NOT NULL")
        non_null = cursor.fetchone()[0]

        return total, non_null

    def validar_columna_no_vacia(self, tabla: str, columna: str) -> Tuple[int, int]:
        """
        Valida que una columna no esté vacía (NULL o string vacío)

        Returns:
            (total_rows, non_empty_rows)
        """
        cursor = self.conn.cursor()

        # Total de filas
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cursor.fetchone()[0]

        # Filas con valor no vacío
        cursor.execute(f"""
            SELECT COUNT(*) FROM {tabla}
            WHERE {columna} IS NOT NULL
            AND TRIM({columna}) != ''
        """)
        non_empty = cursor.fetchone()[0]

        return total, non_empty

    def validar_boolean_true(self, tabla: str, columna: str) -> Tuple[int, int]:
        """
        Valida que una columna booleana sea TRUE

        Returns:
            (total_rows, true_rows)
        """
        cursor = self.conn.cursor()

        # Total de filas
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cursor.fetchone()[0]

        # Filas con valor TRUE (puede ser 1, 'True', 'true', etc.)
        cursor.execute(f"""
            SELECT COUNT(*) FROM {tabla}
            WHERE {columna} IN (1, 'True', 'true', 'TRUE')
        """)
        true_count = cursor.fetchone()[0]

        return total, true_count

    def validar_join_esco(self) -> Tuple[int, int]:
        """
        Valida cuántas ofertas tienen match ESCO

        Returns:
            (total_ofertas, ofertas_con_esco)
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT o.id_oferta)
            FROM ofertas o
            INNER JOIN ofertas_esco_matching oem ON o.id_oferta = oem.id_oferta
            WHERE oem.esco_occupation_uri IS NOT NULL
        """)
        con_esco = cursor.fetchone()[0]

        return total, con_esco

    def validar_skills_esco_json(self) -> Tuple[int, int, int]:
        """
        Valida cuántas ofertas tienen skills ESCO en JSON

        Returns:
            (total, con_esenciales, con_opcionales)
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ofertas_esco_matching
            WHERE esco_skills_esenciales_json IS NOT NULL
            AND esco_skills_esenciales_json != 'null'
            AND esco_skills_esenciales_json != '[]'
        """)
        con_esenciales = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM ofertas_esco_matching
            WHERE esco_skills_opcionales_json IS NOT NULL
            AND esco_skills_opcionales_json != 'null'
            AND esco_skills_opcionales_json != '[]'
        """)
        con_opcionales = cursor.fetchone()[0]

        return total, con_esenciales, con_opcionales

    def validar_fechas_validas(self) -> Tuple[int, int]:
        """
        Valida que las fechas sean válidas

        Returns:
            (total, fechas_validas)
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total = cursor.fetchone()[0]

        # Intentar parsear fechas y contar las válidas
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE fecha_publicacion_datetime IS NOT NULL
            AND fecha_publicacion_datetime != ''
            AND date(fecha_publicacion_datetime) IS NOT NULL
        """)
        validas = cursor.fetchone()[0]

        return total, validas

    def ejecutar_validaciones(self):
        """Ejecuta todas las validaciones definidas"""

        print("=" * 64)
        print("VALIDACIÓN DE CALIDAD DE DATOS PARA DASHBOARD SHINY")
        print("=" * 64)
        print()

        print("[1/4] Conectando a base de datos...")
        self.conectar_db()
        total_ofertas = self.obtener_total_ofertas()
        print(f"      ✓ Conexión exitosa: {self.db_path.name}")
        print(f"      Total de ofertas: {total_ofertas:,}")
        print()

        print("[2/4] Validando completitud de datos...")
        print()

        # ==================== NIVEL CRÍTICO ====================
        print("NIVEL CRÍTICO (bloquea generación si falla):")
        print()

        # ESCO Occupation Label
        total, con_esco = self.validar_join_esco()
        porcentaje = (con_esco / total * 100) if total > 0 else 0
        umbral = 95.0
        pasado = porcentaje >= umbral

        self.results['critico'].append({
            'check': 'ESCO Occupation Match',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{con_esco:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} claude_esco_label:  {porcentaje:5.1f}% poblado ({con_esco:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        # ISCO Nivel 1
        total, non_null = self.validar_columna_no_nula("ofertas", "isco_nivel1")
        porcentaje = (non_null / total * 100) if total > 0 else 0
        umbral = 95.0
        pasado = porcentaje >= umbral

        self.results['critico'].append({
            'check': 'ISCO Nivel 1',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{non_null:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} isco_nivel1:        {porcentaje:5.1f}% poblado ({non_null:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        # Título
        total, non_empty = self.validar_columna_no_vacia("ofertas", "titulo")
        porcentaje = (non_empty / total * 100) if total > 0 else 0
        umbral = 100.0
        pasado = porcentaje >= umbral

        self.results['critico'].append({
            'check': 'Titulo',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{non_empty:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} titulo:            {porcentaje:5.1f}% poblado ({non_empty:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        # Fecha publicación
        total, validas = self.validar_fechas_validas()
        porcentaje = (validas / total * 100) if total > 0 else 0
        umbral = 100.0
        pasado = porcentaje >= umbral

        self.results['critico'].append({
            'check': 'Fecha Publicación',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{validas:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} fecha_publicacion:  {porcentaje:5.1f}% válido ({validas:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        print()

        # ==================== NIVEL IMPORTANTE ====================
        print("NIVEL IMPORTANTE (genera alertas):")
        print()

        # ESCO Skills Esenciales
        total, con_esenciales, con_opcionales = self.validar_skills_esco_json()
        porcentaje_esen = (con_esenciales / total * 100) if total > 0 else 0
        umbral = 50.0
        pasado = porcentaje_esen >= umbral

        self.results['importante'].append({
            'check': 'ESCO Skills Esenciales JSON',
            'passed': pasado,
            'value': porcentaje_esen,
            'threshold': umbral,
            'count': f"{con_esenciales:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} esco_skills_esenciales: {porcentaje_esen:5.1f}% poblado ({con_esenciales:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        # ESCO Skills Opcionales
        porcentaje_opc = (con_opcionales / total * 100) if total > 0 else 0
        umbral = 50.0
        pasado = porcentaje_opc >= umbral

        self.results['importante'].append({
            'check': 'ESCO Skills Opcionales JSON',
            'passed': pasado,
            'value': porcentaje_opc,
            'threshold': umbral,
            'count': f"{con_opcionales:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} esco_skills_opcionales:  {porcentaje_opc:5.1f}% poblado ({con_opcionales:,}/{total:,}) - {estado} (umbral: {umbral}%)")

        # Soft Skills (de NLP)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT o.id_oferta)
            FROM ofertas o
            INNER JOIN ofertas_nlp_history onh ON o.id_oferta = onh.id_oferta
            WHERE onh.is_active = 1
            AND json_extract(onh.extracted_data, '$.soft_skills_list') IS NOT NULL
            AND json_extract(onh.extracted_data, '$.soft_skills_list') != 'null'
            AND json_extract(onh.extracted_data, '$.soft_skills_list') != '[]'
        """)
        con_soft_skills = cursor.fetchone()[0]
        porcentaje = (con_soft_skills / total_ofertas * 100) if total_ofertas > 0 else 0
        umbral = 80.0
        pasado = porcentaje >= umbral

        self.results['importante'].append({
            'check': 'Soft Skills (NLP)',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{con_soft_skills:,}/{total_ofertas:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} soft_skills (NLP):      {porcentaje:5.1f}% poblado ({con_soft_skills:,}/{total_ofertas:,}) - {estado} (umbral: {umbral}%)")

        # Skills Técnicas (de NLP)
        cursor.execute("""
            SELECT COUNT(DISTINCT o.id_oferta)
            FROM ofertas o
            INNER JOIN ofertas_nlp_history onh ON o.id_oferta = onh.id_oferta
            WHERE onh.is_active = 1
            AND json_extract(onh.extracted_data, '$.skills_tecnicas_list') IS NOT NULL
            AND json_extract(onh.extracted_data, '$.skills_tecnicas_list') != 'null'
            AND json_extract(onh.extracted_data, '$.skills_tecnicas_list') != '[]'
        """)
        con_tech_skills = cursor.fetchone()[0]
        porcentaje = (con_tech_skills / total_ofertas * 100) if total_ofertas > 0 else 0
        umbral = 60.0
        pasado = porcentaje >= umbral

        self.results['importante'].append({
            'check': 'Skills Técnicas (NLP)',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{con_tech_skills:,}/{total_ofertas:,}"
        })

        simbolo = "✓" if pasado else "✗"
        estado = "PASA" if pasado else "FALLA"
        print(f"  {simbolo} skills_tecnicas (NLP):  {porcentaje:5.1f}% poblado ({con_tech_skills:,}/{total_ofertas:,}) - {estado} (umbral: {umbral}%)")

        print()

        # ==================== NIVEL ADVERTENCIA ====================
        print("NIVEL ADVERTENCIA (informativo):")
        print()

        # Empresa
        total, non_empty = self.validar_columna_no_vacia("ofertas", "empresa")
        porcentaje = (non_empty / total * 100) if total > 0 else 0
        umbral = 90.0
        pasado = porcentaje >= umbral

        self.results['advertencia'].append({
            'check': 'Empresa',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{non_empty:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "⚠"
        estado = "PASA" if pasado else "BAJO"
        print(f"  {simbolo} empresa:             {porcentaje:5.1f}% poblado ({non_empty:,}/{total:,}) - {estado}")

        # Localización
        total, non_empty = self.validar_columna_no_vacia("ofertas", "localizacion")
        porcentaje = (non_empty / total * 100) if total > 0 else 0
        umbral = 80.0
        pasado = porcentaje >= umbral

        self.results['advertencia'].append({
            'check': 'Localización',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{non_empty:,}/{total:,}"
        })

        simbolo = "✓" if pasado else "⚠"
        estado = "PASA" if pasado else "BAJO"
        print(f"  {simbolo} localizacion:        {porcentaje:5.1f}% poblado ({non_empty:,}/{total:,}) - {estado}")

        # Nivel Educativo
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT o.id_oferta)
            FROM ofertas o
            INNER JOIN ofertas_nlp_history onh ON o.id_oferta = onh.id_oferta
            WHERE onh.is_active = 1
            AND json_extract(onh.extracted_data, '$.nivel_educativo') IS NOT NULL
            AND json_extract(onh.extracted_data, '$.nivel_educativo') != 'null'
            AND json_extract(onh.extracted_data, '$.nivel_educativo') != ''
        """)
        con_nivel_edu = cursor.fetchone()[0]
        porcentaje = (con_nivel_edu / total_ofertas * 100) if total_ofertas > 0 else 0
        umbral = 40.0
        pasado = porcentaje >= umbral

        self.results['advertencia'].append({
            'check': 'Nivel Educativo',
            'passed': pasado,
            'value': porcentaje,
            'threshold': umbral,
            'count': f"{con_nivel_edu:,}/{total_ofertas:,}"
        })

        simbolo = "✓" if pasado else "⚠"
        estado = "PASA" if pasado else "BAJO"
        print(f"  {simbolo} nivel_educativo (NLP): {porcentaje:5.1f}% poblado ({con_nivel_edu:,}/{total_ofertas:,}) - {estado}")

        print()

        # ==================== RESUMEN ====================
        print("[3/4] Generando resumen...")
        print()

        criticos_pasados = sum(1 for r in self.results['critico'] if r['passed'])
        criticos_total = len(self.results['critico'])

        importantes_pasados = sum(1 for r in self.results['importante'] if r['passed'])
        importantes_total = len(self.results['importante'])

        advertencias_pasadas = sum(1 for r in self.results['advertencia'] if r['passed'])
        advertencias_total = len(self.results['advertencia'])

        # Determinar resultado general
        if criticos_pasados < criticos_total:
            resultado = "ERROR CRÍTICO"
            exit_code = 2
        elif importantes_pasados < importantes_total:
            resultado = "ADVERTENCIA"
            exit_code = 1
        else:
            resultado = "OK"
            exit_code = 0

        self.stats = {
            'total_ofertas': total_ofertas,
            'criticos_pasados': criticos_pasados,
            'criticos_total': criticos_total,
            'importantes_pasados': importantes_pasados,
            'importantes_total': importantes_total,
            'advertencias_pasadas': advertencias_pasadas,
            'advertencias_total': advertencias_total,
            'resultado': resultado,
            'exit_code': exit_code
        }

        print("=" * 64)
        print(f"RESULTADO: {resultado}")
        print("=" * 64)
        print()

        simbolo_crit = "✓" if criticos_pasados == criticos_total else "✗"
        print(f"{simbolo_crit} Validaciones CRÍTICAS:    {criticos_pasados}/{criticos_total} PASADAS")

        simbolo_imp = "✓" if importantes_pasados == importantes_total else "✗"
        print(f"{simbolo_imp} Validaciones IMPORTANTES: {importantes_pasados}/{importantes_total} PASADAS")

        simbolo_adv = "✓" if advertencias_pasadas == advertencias_total else "⚠"
        print(f"{simbolo_adv} Validaciones ADVERTENCIA:  {advertencias_pasadas}/{advertencias_total} PASADAS")
        print()

        # ==================== ACCIONES RECOMENDADAS ====================
        print("[4/4] Acciones recomendadas...")
        print()

        if con_esenciales == 0 or con_opcionales == 0:
            print("ACCIÓN REQUERIDA: ESCO Skills no están pobladas")
            print("  Las columnas esco_skills_esenciales_json y esco_skills_opcionales_json")
            print("  en la tabla ofertas_esco_matching están vacías.")
            print()
            print("  Soluciones:")
            print("  1. Modificar match_ofertas_to_esco.py para poblar skills")
            print("  2. Crear y ejecutar: python database/populate_esco_skills_in_db.py")
            print("  3. Verificar tabla esco_occupation_skills está poblada")
            print()
            print("  Impacto en Dashboard:")
            print("  - La sección 'Análisis de Skills ESCO' aparecerá vacía")
            print("  - Los infoBoxes de skills mostrarán 0")
            print("  - Los gráficos de skills estarán en blanco")
            print()

        if criticos_pasados < criticos_total:
            print("ERROR: Validaciones CRÍTICAS fallaron. NO generar CSV.")
            print("       El dashboard no funcionará correctamente.")
            print()
        elif importantes_pasados < importantes_total:
            print("ADVERTENCIA: Validaciones IMPORTANTES fallaron.")
            print("             El CSV puede generarse con flag --force,")
            print("             pero algunas secciones del dashboard estarán incompletas.")
            print()
        else:
            print("✓ Todos los checks pasaron. El CSV puede generarse sin problemas.")
            print()

        return exit_code

    def exportar_json(self) -> str:
        """Exporta resultados a JSON"""
        return json.dumps({
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'results': self.results
        }, indent=2)

    def cerrar(self):
        """Cierra conexión a base de datos"""
        if self.conn:
            self.conn.close()


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Validador de calidad de datos para Dashboard Shiny')
    parser.add_argument('--nivel', choices=['critico', 'importante', 'advertencia'],
                       help='Validar solo un nivel específico')
    parser.add_argument('--json', action='store_true',
                       help='Exportar resultados en formato JSON')
    parser.add_argument('--db', type=str,
                       help='Ruta a la base de datos (por defecto: database/bumeran_scraping.db)')

    args = parser.parse_args()

    try:
        validator = DataQualityValidator(db_path=args.db)
        exit_code = validator.ejecutar_validaciones()

        if args.json:
            print()
            print("JSON Output:")
            print(validator.exportar_json())

        validator.cerrar()

        sys.exit(exit_code)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
