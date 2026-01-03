#!/usr/bin/env python3
"""
Script para seleccionar ofertas estratégicas para testing NLP v6.0
==================================================================

Selecciona 100 ofertas REALES de la BD distribuidas estratégicamente
por categorías para testing comprehensivo de NLP v6.0.

Criterios de selección:
- 10 categorías con keywords reales
- Distribución balanceada según disponibilidad
- Excluye 10 IDs del test anterior
- Solo ofertas con descripción > 300 caracteres
- Muestreo aleatorio dentro de cada categoría

Uso:
    python select_strategic_offers.py

Output:
    - selected_offers_100.csv (100 ofertas seleccionadas)
    - Reporte de distribución por categoría
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict


class StrategicOfferSelector:
    """Selector estratégico de ofertas para testing"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.selected_offers = []
        self.stats = defaultdict(int)

        # IDs del test anterior (10 ofertas) - EXCLUIR
        self.EXCLUDE_IDS = [
            1118010700,  # Programador/a de Centro de mecanizado zona Bernal
            1118031067,  # Programador Fullstack (Vue.js y .NET)
            2166883,     # Programador Backend
            1095,        # Desarrollador Senior Python
            59858,       # Analista de Marketing Digital
            1117971556,  # Gerente de Ventas Regional
            1117971648,  # Ejecutivo de Cuentas Senior
            1117976839,  # Jefe de Administración y Finanzas
            1117976851,  # Analista Contable Sr
            1117976959,  # Coordinador de Operaciones
        ]

        # Definición de categorías con keywords y targets
        self.CATEGORIES = {
            'IT_Backend': {
                'keywords_titulo': ['backend', 'python', 'java', '.net', 'node', 'api'],
                'keywords_desc': ['backend', 'python', 'java', 'node.js', 'api rest', 'microservicios'],
                'target': 15,
                'description': 'Desarrollo Backend (Python/Java/.NET/Node)'
            },
            'IT_Frontend': {
                'keywords_titulo': ['frontend', 'react', 'angular', 'vue', 'javascript', 'ui'],
                'keywords_desc': ['frontend', 'react', 'angular', 'vue', 'javascript', 'css', 'html'],
                'target': 10,
                'description': 'Desarrollo Frontend (React/Angular/Vue)'
            },
            'IT_Fullstack': {
                'keywords_titulo': ['fullstack', 'full stack', 'full-stack'],
                'keywords_desc': ['fullstack', 'full stack', 'frontend y backend'],
                'target': 10,
                'description': 'Desarrollo Fullstack'
            },
            'IT_DevOps': {
                'keywords_titulo': ['devops', 'sre', 'infraestructura', 'cloud', 'aws', 'azure', 'qa', 'tester'],
                'keywords_desc': ['devops', 'kubernetes', 'docker', 'aws', 'azure', 'ci/cd', 'qa', 'testing'],
                'target': 8,
                'description': 'DevOps/QA/Infraestructura'
            },
            'Gerencial': {
                'keywords_titulo': ['gerente', 'director', 'jefe', 'coordinador', 'supervisor', 'líder'],
                'keywords_desc': ['gerente', 'director', 'liderazgo', 'equipo', 'gestión'],
                'target': 12,
                'description': 'Posiciones Gerenciales/Liderazgo'
            },
            'Junior_Trainee': {
                'keywords_titulo': ['junior', 'trainee', 'pasante', 'sin experiencia', 'estudiante'],
                'keywords_desc': ['junior', 'trainee', 'sin experiencia', 'primer empleo', 'estudiante'],
                'target': 10,
                'description': 'Junior/Trainee/Pasantías'
            },
            'Senior': {
                'keywords_titulo': ['senior', 'sr.', 'sr ', 'experto', 'especialista'],
                'keywords_desc': ['senior', 'años de experiencia', 'experto', 'especialista'],
                'target': 10,
                'description': 'Posiciones Senior/Experto'
            },
            'Remoto': {
                'keywords_titulo': ['remoto', 'remote', 'home office', 'híbrido'],
                'keywords_desc': ['remoto', 'remote', 'home office', 'trabajo remoto', 'híbrido', 'teletrabajo'],
                'target': 10,
                'description': 'Modalidad Remoto/Híbrido'
            },
            'Comercial': {
                'keywords_titulo': ['ventas', 'comercial', 'vendedor', 'ejecutivo de cuentas', 'account'],
                'keywords_desc': ['ventas', 'comercial', 'vendedor', 'clientes', 'cartera'],
                'target': 8,
                'description': 'Ventas/Comercial'
            },
            'Finanzas': {
                'keywords_titulo': ['finanzas', 'contable', 'contador', 'tesorero', 'analista financiero'],
                'keywords_desc': ['finanzas', 'contable', 'contador', 'balance', 'contabilidad'],
                'target': 7,
                'description': 'Finanzas/Contabilidad'
            }
        }

    def select_offers(self) -> Dict[str, Any]:
        """
        Selecciona ofertas estratégicamente distribuidas

        Returns:
            Dict con ofertas seleccionadas y estadísticas
        """
        print("=" * 70)
        print("SELECCION ESTRATEGICA DE OFERTAS PARA TESTING NLP V6.0")
        print("=" * 70)
        print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base de datos: {self.db_path}")
        print(f"Target: 100 ofertas distribuidas en 10 categorías\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar total de ofertas disponibles
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE descripcion IS NOT NULL
            AND LENGTH(descripcion) > 300
            AND id_oferta NOT IN ({})
        """.format(','.join(map(str, self.EXCLUDE_IDS))))

        total_available = cursor.fetchone()[0]
        print(f"[INFO] Ofertas disponibles (desc > 300 chars): {total_available:,}")
        print(f"[INFO] IDs excluidos del test anterior: {len(self.EXCLUDE_IDS)}\n")

        # Seleccionar por categoría
        print("PASO 1: Selección por categoría")
        print("-" * 70)

        selected_ids = set()
        category_results = {}

        for cat_name, cat_config in self.CATEGORIES.items():
            print(f"\n[{cat_name}] {cat_config['description']}")
            print(f"  Target: {cat_config['target']} ofertas")

            # Construir WHERE clause para keywords en título
            titulo_clauses = [
                f"titulo LIKE '%{kw}%' COLLATE NOCASE"
                for kw in cat_config['keywords_titulo']
            ]

            # Construir WHERE clause para keywords en descripción
            desc_clauses = [
                f"descripcion LIKE '%{kw}%' COLLATE NOCASE"
                for kw in cat_config['keywords_desc']
            ]

            # Construir exclude clause
            exclude_all = list(self.EXCLUDE_IDS) + list(selected_ids)
            exclude_clause = f"id_oferta NOT IN ({','.join(map(str, exclude_all))})"

            # Query de selección
            query = f"""
                SELECT
                    id_oferta,
                    titulo,
                    LENGTH(descripcion) as desc_len
                FROM ofertas
                WHERE (
                    ({' OR '.join(titulo_clauses)})
                    OR
                    ({' OR '.join(desc_clauses)})
                )
                AND {exclude_clause}
                AND descripcion IS NOT NULL
                AND LENGTH(descripcion) > 300
                ORDER BY RANDOM()
                LIMIT {cat_config['target']}
            """

            cursor.execute(query)
            results = cursor.fetchall()

            if len(results) < cat_config['target']:
                print(f"  [ADVERTENCIA] Solo {len(results)} ofertas encontradas (target: {cat_config['target']})")
            else:
                print(f"  [OK] {len(results)} ofertas seleccionadas")

            # Guardar resultados
            category_offers = []
            for id_oferta, titulo, desc_len in results:
                selected_ids.add(id_oferta)
                offer_data = {
                    'id_oferta': id_oferta,
                    'titulo': titulo,
                    'desc_len': desc_len,
                    'categoria': cat_name,
                    'descripcion_categoria': cat_config['description']
                }
                category_offers.append(offer_data)
                self.selected_offers.append(offer_data)

            category_results[cat_name] = {
                'count': len(results),
                'target': cat_config['target'],
                'offers': category_offers
            }

            # Mostrar muestra de 2 títulos
            if len(results) >= 2:
                print(f"  Muestra:")
                print(f"    - {results[0][1][:60]}...")
                print(f"    - {results[1][1][:60]}...")

        conn.close()

        # Estadísticas finales
        print("\n" + "=" * 70)
        print("PASO 2: Resumen de selección")
        print("=" * 70)
        print(f"\nTotal ofertas seleccionadas: {len(self.selected_offers)}")
        print(f"IDs únicos: {len(selected_ids)}\n")

        print("Distribución por categoría:")
        print("-" * 70)
        print(f"{'Categoría':<20} {'Target':>8} {'Obtenido':>10} {'%':>8}")
        print("-" * 70)

        total_target = 0
        total_obtenido = 0

        for cat_name, results in category_results.items():
            total_target += results['target']
            total_obtenido += results['count']
            percentage = (results['count'] / results['target'] * 100) if results['target'] > 0 else 0
            print(f"{cat_name:<20} {results['target']:>8} {results['count']:>10} {percentage:>7.1f}%")

        print("-" * 70)
        print(f"{'TOTAL':<20} {total_target:>8} {total_obtenido:>10} {(total_obtenido/total_target*100):>7.1f}%")

        return {
            'selected_offers': self.selected_offers,
            'category_results': category_results,
            'total_selected': len(self.selected_offers),
            'total_target': total_target
        }

    def export_to_csv(self, output_path: str):
        """Exporta ofertas seleccionadas a CSV"""
        print("\n" + "=" * 70)
        print("PASO 3: Exportar a CSV")
        print("=" * 70)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'id_oferta',
                'titulo',
                'desc_len',
                'categoria',
                'descripcion_categoria'
            ])

            # Datos
            for offer in self.selected_offers:
                writer.writerow([
                    offer['id_oferta'],
                    offer['titulo'],
                    offer['desc_len'],
                    offer['categoria'],
                    offer['descripcion_categoria']
                ])

        print(f"\n[OK] Archivo exportado: {output_path}")
        print(f"[OK] {len(self.selected_offers)} ofertas guardadas\n")

    def get_ids_list(self) -> List[int]:
        """Retorna lista de IDs para usar en test_nlp_v6.py"""
        return sorted([offer['id_oferta'] for offer in self.selected_offers])


def main():
    """Ejecuta la selección estratégica"""

    db_path = Path(__file__).parent / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    # Inicializar selector
    selector = StrategicOfferSelector(str(db_path))

    try:
        # Seleccionar ofertas
        results = selector.select_offers()

        # Exportar a CSV
        output_csv = Path(__file__).parent / "selected_offers_100.csv"
        selector.export_to_csv(str(output_csv))

        # Mostrar lista de IDs para copiar a test_nlp_v6.py
        ids_list = selector.get_ids_list()

        print("=" * 70)
        print("PASO 4: IDs seleccionados para test_nlp_v6.py")
        print("=" * 70)
        print("\nCopia estos IDs a test_nlp_v6.py:")
        print("-" * 70)
        print("TEST_OFFER_IDS = [")

        # Formatear en líneas de 10 IDs
        for i in range(0, len(ids_list), 10):
            chunk = ids_list[i:i+10]
            ids_str = ', '.join(map(str, chunk))
            print(f"    {ids_str},")

        print("]")
        print("-" * 70)
        print(f"\nTotal IDs: {len(ids_list)}")

        # Próximos pasos
        print("\n" + "=" * 70)
        print("PROXIMOS PASOS")
        print("=" * 70)
        print("\n1. Revisar archivo CSV: selected_offers_100.csv")
        print("2. Copiar lista de IDs a test_nlp_v6.py")
        print("3. Ejecutar: python test_nlp_v6.py")
        print("4. Analizar resultados y cobertura por categoría\n")

        # Validación final
        if results['total_selected'] < results['total_target']:
            print("[ADVERTENCIA] No se alcanzó el target de 100 ofertas")
            print(f"  Target: {results['total_target']}")
            print(f"  Obtenido: {results['total_selected']}")
            print(f"  Faltante: {results['total_target'] - results['total_selected']}\n")
        else:
            print(f"[OK] Target alcanzado: {results['total_selected']}/{results['total_target']} ofertas\n")

    except Exception as e:
        print(f"\nERROR FATAL: {str(e)}")
        raise


if __name__ == "__main__":
    main()
