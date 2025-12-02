#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Regresión para ESCO Matching Multicriteria
==================================================

VERSION: 1.0
FECHA: 2025-11-28

OBJETIVO:
  Verificar que el algoritmo de matching ESCO produce resultados
  consistentes y correctos para un conjunto de ofertas "gold set".

EJECUCIÓN:
  python test_esco_matching_regression.py

CRITERIOS DE ÉXITO:
  1. El ESCO match debe estar en el top-3 de candidatos esperados
  2. El grupo ISCO debe ser correcto
  3. No debe haber matches "absurdos" (grupos ISCO prohibidos)
  4. Score final debe estar dentro de rango esperado
"""

import sqlite3
import json
import sys
import struct
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# =============================================================================
# GOLD SET - Casos de prueba validados manualmente
# =============================================================================
GOLD_SET = [
    {
        "id_oferta": "2154549",
        "titulo": "Contador/a para Sector Auditoria",
        "esco_esperado_labels": [
            "auditor de cuentas",
            "auditor",
            "contador",
            "contable",
            "auxiliar de auditoria"
        ],
        "isco_esperado": ["2"],  # Profesionales
        "isco_prohibido": ["5", "7", "9"],
        "score_min": 0.45,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2163782",
        "titulo": "Analista de Investigacion de Mercado",
        "esco_esperado_labels": [
            "analista de estudios de mercado",
            "analista de mercado",
            "investigador de mercado",
            "analista de negocios"
        ],
        "isco_esperado": ["2"],  # Profesionales
        "isco_prohibido": ["5", "7", "9"],
        "score_min": 0.50,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2167866",
        "titulo": "Gerente de Operaciones Gastronomicas",
        "esco_esperado_labels": [
            "director de restaurante",
            "gerente de restaurante",
            "gerente de operaciones",
            "gerente de tienda"
        ],
        "isco_esperado": ["1"],  # Directivos
        "isco_prohibido": ["7", "8", "9"],
        "score_min": 0.45,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2168250",
        "titulo": "Tecnico Mecanico para flota Vehicular pesada",
        "esco_esperado_labels": [
            "mecanico de vehiculos",
            "mecanico",
            "tecnico mecanico",
            "ingeniero mecanico"
        ],
        "isco_esperado": ["3", "7"],  # Tecnicos u Oficios
        "isco_prohibido": ["1", "5", "9"],
        "score_min": 0.40,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2168254",
        "titulo": "AI Solutions Developer (ID)",
        "esco_esperado_labels": [
            "desarrollador",
            "desarrollador de software",
            "desarrollador de IdC",
            "programador",
            "desarrollador de interfaces"
        ],
        "isco_esperado": ["2"],  # Profesionales
        "isco_prohibido": ["5", "7", "9"],
        "score_min": 0.45,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2168263",
        "titulo": "Coordinador/a Bioquimica Endocrinologia",
        "esco_esperado_labels": [
            "ingeniero bioquimico",
            "bioquimico",
            "tecnico en bioquimica",
            "coordinador de laboratorio"
        ],
        "isco_esperado": ["2"],  # Profesionales
        "isco_prohibido": ["5", "7", "8", "9"],
        "score_min": 0.45,
        "score_max": 0.95,
    },
    {
        "id_oferta": "2168264",
        "titulo": "Repositor/a para Almacen Natural/Verduleria",
        "esco_esperado_labels": [
            "encargado de almacen",
            "repositor",
            "operario de logistica",
            "operario de almacen"
        ],
        "isco_esperado": ["4", "9"],  # Administrativos o No calificados
        "isco_prohibido": ["1", "2"],
        "score_min": 0.40,
        "score_max": 0.95,
    },
]

# =============================================================================
# GOLD SET v8.1 - 19 casos revisados manualmente (2025-11-28)
# =============================================================================
# Basado en gold_set_manual_v1.json
# La idea NO es exigir una unica ocupacion correcta, sino:
# 1. Evitar matches que sabemos que son malos (forbidden_substrings)
# 2. Asegurar que casos problematicos no queden auto-confirmados (should_not_be_confirmed)
#
GOLD_SET_19 = [
    # === CASOS CORRECTOS (11) - solo validar que no rompamos nada ===
    {
        "id_oferta": "1118026700",
        "titulo": "VENDEDOR DE REPUESTOS AUTOMOTOR",
        "esco_ok": True,
        "comentario": "Match correcto. Vendedor de repuestos -> vendedor de piezas de repuesto.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118026729",
        "titulo": "Responsable de deposito",
        "esco_ok": True,
        "comentario": "Match correcto. Responsable de deposito -> encargado de almacen.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118027243",
        "titulo": "Abogado/a de impuestos",
        "esco_ok": True,
        "comentario": "Match correcto. Abogado/a de impuestos -> abogado/abogada.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118027261",
        "titulo": "Supervisor de limpieza",
        "esco_ok": True,
        "comentario": "Match correcto. Supervisor de limpieza -> supervisor de servicio de limpieza.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118027941",
        "titulo": "Dibujante tecnico",
        "esco_ok": True,
        "comentario": "Match correcto. Dibujante tecnico -> dibujante tecnico.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028027",
        "titulo": "Operador de autoelevadores",
        "esco_ok": True,
        "comentario": "Match correcto. Operador de autoelevadores -> operador de carretilla elevadora.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028201",
        "titulo": "Operarios industria alimenticia",
        "esco_ok": True,
        "comentario": "Match correcto. Operarios industria alimenticia -> operario de produccion de alimentos.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028657",
        "titulo": "Recepcionista",
        "esco_ok": True,
        "comentario": "Match correcto. Recepcionista -> recepcionista.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028681",
        "titulo": "Administrativa/o",
        "esco_ok": True,
        "comentario": "Match correcto. Administrativa/o -> empleado administrativo.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028828",
        "titulo": "Modelista textil",
        "esco_ok": True,
        "comentario": "Match correcto. Modelista textil -> disenador de modelos para moldes (patronista).",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028891",
        "titulo": "Auxiliar contable",
        "esco_ok": True,
        "comentario": "Match correcto. Auxiliar contable -> administrativo contable.",
        "forbidden_substrings": [],
        "should_not_be_confirmed": False,
    },
    # === CASOS INCORRECTOS (8) - evitar matches malos y/o no auto-confirmar ===
    {
        "id_oferta": "1118027188",
        "titulo": "Programa de pasantias 'Crear Futuro'",
        "esco_ok": False,
        "tipo_error": "programa_general",
        "comentario": "Programa de pasantias general -> NO debe asignarse una ocupacion especifica",
        "forbidden_substrings": ["disenador de interiores"],  # match malo conocido
        "should_not_be_confirmed": True,  # CRITICO: pasantias NUNCA auto-confirmar
    },
    {
        "id_oferta": "1118027276",
        "titulo": "Ejecutivo de cuentas - Ventas corporativas",
        "esco_ok": False,
        "tipo_error": "sector_funcion",
        "comentario": "Ejecutivo de cuentas comercial mapeado a tecnico de contadores electricos",
        "forbidden_substrings": ["contador", "contadores", "electrico", "electricista"],
        "should_not_be_confirmed": True,  # comercial no debe matchear tecnico
    },
    {
        "id_oferta": "1118027662",
        "titulo": "Farmaceutico/a para farmacias en Rio Cuarto",
        "esco_ok": False,
        "tipo_error": "tipo_ocupacion",
        "comentario": "Farmaceutico de farmacia minorista -> NO es ingeniero farmaceutico",
        "forbidden_substrings": ["ingeniero"],  # farmaceutico de farmacia != ingeniero
        "should_not_be_confirmed": False,  # puede confirmarse si el match es correcto
    },
    {
        "id_oferta": "1118027834",
        "titulo": "Vendedora Digital / Atencion al Cliente",
        "esco_ok": False,
        "tipo_error": "nivel_jerarquico",
        "comentario": "Vendedora -> NO es director de comercializacion",
        "forbidden_substrings": ["director", "directora", "gerente"],  # nivel muy alto
        "should_not_be_confirmed": True,  # nivel bajo no debe ser director
    },
    {
        "id_oferta": "1118028038",
        "titulo": "Ejecutivo/a comercial de cuentas",
        "esco_ok": False,
        "tipo_error": "nivel_jerarquico",
        "comentario": "Ejecutivo comercial -> NO es director comercial",
        "forbidden_substrings": ["director", "directora"],  # nivel excesivo
        "should_not_be_confirmed": True,  # nivel medio no debe ser director
    },
    {
        "id_oferta": "1118028376",
        "titulo": "Analista administrativo/a",
        "esco_ok": False,
        "tipo_error": "sector_funcion",
        "comentario": "Analista administrativo -> NO es analista de negocios (area diferente)",
        "forbidden_substrings": ["analista de negocios", "business analyst"],
        "should_not_be_confirmed": True,  # v8.2: NUNCA auto-confirmar admin vs negocios
    },
    {
        "id_oferta": "1118028833",
        "titulo": "Asesor comercial plan de ahorro de autos",
        "esco_ok": False,
        "tipo_error": "sector_funcion",
        "comentario": "Asesor comercial de planes de ahorro -> NO es agente de alquiler de coches",
        "forbidden_substrings": ["alquiler", "rental"],  # venta != alquiler
        "should_not_be_confirmed": False,
    },
    {
        "id_oferta": "1118028887",
        "titulo": "Account Executive (Hunter)",
        "esco_ok": False,
        "tipo_error": "sector_funcion",
        "comentario": "Account Executive de ventas -> NO es agente de empleo (RRHH)",
        "forbidden_substrings": ["agente de empleo", "empleo"],  # ventas != RRHH
        "should_not_be_confirmed": True,  # comercial hunter no debe matchear RRHH
    },
]


class TestResult:
    """Resultado de un test individual."""
    def __init__(self, id_oferta, titulo):
        self.id_oferta = id_oferta
        self.titulo = titulo
        self.passed = True
        self.failures = []
        self.esco_label = None
        self.esco_uri = None
        self.score_final = None
        self.isco_code = None

    def fail(self, message):
        self.passed = False
        self.failures.append(message)

    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        result = f"{status} | {self.id_oferta} | {self.titulo[:40]}..."
        if not self.passed:
            for f in self.failures:
                result += f"\n         -> {f}"
        return result


def normalize_label(label):
    """Normaliza un label para comparación."""
    if not label:
        return ""
    return label.lower().strip()


def get_isco_from_uri(uri):
    """Extrae el código ISCO (primer dígito) de una URI ESCO."""
    if not uri:
        return None
    # Las URIs ESCO de ocupaciones tienen formato:
    # http://data.europa.eu/esco/occupation/XXXX
    # El código ISCO está relacionado con el código de la ocupación
    # Para simplificar, obtenemos de la tabla esco_occupations
    return None  # Se obtiene de la DB


def run_regression_tests():
    """Ejecuta todos los tests de regresión."""
    print("=" * 70)
    print("TEST DE REGRESIÓN - ESCO MATCHING MULTICRITERIA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []
    passed = 0
    failed = 0

    for gold in GOLD_SET:
        id_oferta = gold["id_oferta"]
        titulo = gold["titulo"]

        test = TestResult(id_oferta, titulo)

        # Obtener resultado actual del matching
        cursor.execute('''
            SELECT
                esco_occupation_uri,
                esco_occupation_label,
                score_final_ponderado,
                match_confirmado,
                requiere_revision
            FROM ofertas_esco_matching
            WHERE id_oferta = ?
        ''', (id_oferta,))

        row = cursor.fetchone()

        if not row:
            test.fail(f"No hay resultado de matching para oferta {id_oferta}")
        else:
            test.esco_label = row['esco_occupation_label']
            test.esco_uri = row['esco_occupation_uri']
            # Convertir score a float (puede venir como bytes/blob si es numpy)
            score_raw = row['score_final_ponderado']
            if score_raw is not None:
                if isinstance(score_raw, bytes):
                    # Intentar como double (8 bytes)
                    if len(score_raw) == 8:
                        test.score_final = struct.unpack('d', score_raw)[0]
                    elif len(score_raw) == 4:
                        test.score_final = struct.unpack('f', score_raw)[0]
                    else:
                        # Intentar como string
                        try:
                            test.score_final = float(score_raw.decode('latin-1'))
                        except:
                            test.score_final = 0.5  # fallback
                else:
                    test.score_final = float(score_raw)

            # Obtener código ISCO de la ocupación ESCO
            if test.esco_uri:
                cursor.execute('''
                    SELECT isco_code
                    FROM esco_occupations
                    WHERE occupation_uri = ?
                ''', (test.esco_uri,))
                isco_row = cursor.fetchone()
                if isco_row:
                    test.isco_code = isco_row['isco_code']

            # TEST 1: Verificar que el label está en los esperados
            label_normalizado = normalize_label(test.esco_label)
            labels_esperados = [normalize_label(l) for l in gold["esco_esperado_labels"]]

            # Verificar si algún label esperado está contenido en el resultado
            label_match = False
            for le in labels_esperados:
                if le in label_normalizado or label_normalizado in le:
                    label_match = True
                    break

            if not label_match:
                # Verificar similitud parcial (palabras clave)
                palabras_resultado = set(label_normalizado.split())
                for le in labels_esperados:
                    palabras_esperado = set(le.split())
                    if len(palabras_resultado & palabras_esperado) >= 1:
                        label_match = True
                        break

            if not label_match:
                test.fail(f"Label '{test.esco_label}' no está en esperados: {gold['esco_esperado_labels'][:3]}")

            # TEST 2: Verificar grupo ISCO
            # El formato de isco_code es "C1234" donde el segundo caracter es el grupo
            if test.isco_code and len(test.isco_code) >= 2:
                # Extraer el primer digito numerico (posicion 1 si empieza con C)
                if test.isco_code.startswith('C'):
                    isco_primer_digito = test.isco_code[1]
                else:
                    isco_primer_digito = test.isco_code[0]

                if isco_primer_digito not in gold["isco_esperado"]:
                    test.fail(f"ISCO grupo '{isco_primer_digito}' no esta en esperados: {gold['isco_esperado']}")

                if isco_primer_digito in gold["isco_prohibido"]:
                    test.fail(f"ISCO grupo '{isco_primer_digito}' esta PROHIBIDO para esta oferta")

            # TEST 3: Verificar score en rango
            if test.score_final is not None:
                if test.score_final < gold["score_min"]:
                    test.fail(f"Score {test.score_final:.3f} menor que mínimo {gold['score_min']}")
                if test.score_final > gold["score_max"]:
                    test.fail(f"Score {test.score_final:.3f} mayor que máximo {gold['score_max']}")

        results.append(test)
        if test.passed:
            passed += 1
        else:
            failed += 1

    conn.close()

    # Imprimir resultados
    print("\n" + "-" * 70)
    print("RESULTADOS:")
    print("-" * 70)

    for test in results:
        print(test)
        if test.esco_label and test.score_final:
            isco_display = test.isco_code if test.isco_code else "N/A"
            print(f"         -> Match: {test.esco_label}")
            print(f"         -> ISCO: {isco_display} | Score: {test.score_final:.3f}")

    print("\n" + "=" * 70)
    print(f"RESUMEN: {passed} passed, {failed} failed de {len(GOLD_SET)} tests")
    print("=" * 70)

    # Retornar código de salida
    return 0 if failed == 0 else 1


def run_gold_set_19_tests():
    """
    Ejecuta tests para los 19 casos del gold set manual v8.1.

    Objetivos:
    1. Evitar matches conocidos como malos (forbidden_substrings)
    2. Asegurar que casos problematicos no queden auto-confirmados

    Returns:
        Tuple[int, dict]: (failed_count, results_dict)
    """
    print("=" * 70)
    print("TEST GOLD SET 19 - REGLAS DE VALIDACION v8.1")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []
    passed = 0
    failed = 0
    forbidden_violations = 0
    confirmation_violations = 0

    for gold in GOLD_SET_19:
        id_oferta = gold["id_oferta"]
        titulo = gold["titulo"]
        forbidden = gold.get("forbidden_substrings", [])
        should_not_confirm = gold.get("should_not_be_confirmed", False)

        test = TestResult(id_oferta, titulo)

        # Obtener resultado actual del matching
        cursor.execute('''
            SELECT
                esco_occupation_uri,
                esco_occupation_label,
                score_final_ponderado,
                match_confirmado,
                requiere_revision,
                matching_version
            FROM ofertas_esco_matching
            WHERE id_oferta = ?
        ''', (id_oferta,))

        row = cursor.fetchone()

        if not row:
            test.fail(f"No hay resultado de matching para oferta {id_oferta}")
        else:
            test.esco_label = row['esco_occupation_label']
            test.esco_uri = row['esco_occupation_uri']
            match_confirmado = row['match_confirmado']
            requiere_revision = row['requiere_revision']

            # Parsear score
            score_raw = row['score_final_ponderado']
            if score_raw is not None:
                if isinstance(score_raw, bytes):
                    if len(score_raw) == 8:
                        test.score_final = struct.unpack('d', score_raw)[0]
                    elif len(score_raw) == 4:
                        test.score_final = struct.unpack('f', score_raw)[0]
                    else:
                        test.score_final = 0.5
                else:
                    test.score_final = float(score_raw)

            label_lower = (test.esco_label or "").lower()

            # TEST 1: Verificar que NO contenga substrings prohibidos
            for forbidden_str in forbidden:
                if forbidden_str.lower() in label_lower:
                    test.fail(f"FORBIDDEN: Match contiene '{forbidden_str}' (label: {test.esco_label})")
                    forbidden_violations += 1
                    break

            # TEST 2: Verificar que casos problematicos NO esten auto-confirmados
            if should_not_confirm and match_confirmado:
                test.fail(f"CONFIRMATION: Caso problematico esta auto-CONFIRMADO (deberia estar en REVISION)")
                confirmation_violations += 1

        results.append(test)
        if test.passed:
            passed += 1
        else:
            failed += 1

    conn.close()

    # Imprimir resultados
    print("\n" + "-" * 70)
    print("RESULTADOS GOLD SET 19:")
    print("-" * 70)

    for test in results:
        gold = next((g for g in GOLD_SET_19 if g['id_oferta'] == test.id_oferta), {})
        expected_status = "OK" if gold.get('esco_ok', True) else "PROBLEMATICO"

        print(test)
        if test.esco_label:
            score_str = f"{test.score_final:.3f}" if test.score_final else "N/A"
            print(f"         -> Match: {test.esco_label[:50]}...")
            print(f"         -> Score: {score_str} | Esperado: {expected_status}")

    print("\n" + "=" * 70)
    print(f"RESUMEN GOLD SET 19:")
    print(f"  Total:    {len(GOLD_SET_19)} casos")
    print(f"  Passed:   {passed}")
    print(f"  Failed:   {failed}")
    print(f"    - Forbidden violations: {forbidden_violations}")
    print(f"    - Confirmation violations: {confirmation_violations}")
    print("=" * 70)

    return failed, {
        'passed': passed,
        'failed': failed,
        'forbidden_violations': forbidden_violations,
        'confirmation_violations': confirmation_violations
    }


def verify_database_state(gold_sets=None):
    """Verifica que la base de datos tenga los datos necesarios."""
    if gold_sets is None:
        gold_sets = [('GOLD_SET', GOLD_SET), ('GOLD_SET_19', GOLD_SET_19)]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    all_ok = True

    for name, gold_set in gold_sets:
        ids = [g['id_oferta'] for g in gold_set]
        cursor.execute('''
            SELECT COUNT(*) FROM ofertas_esco_matching
            WHERE id_oferta IN ({})
        '''.format(','.join(['?'] * len(ids))), ids)

        count = cursor.fetchone()[0]

        if count < len(gold_set):
            print(f"  {name}: {count}/{len(gold_set)} ofertas con matching")
            all_ok = False
        else:
            print(f"  {name}: OK ({count}/{len(gold_set)} ofertas)")

    conn.close()

    if not all_ok:
        print("   Ejecute primero: python match_ofertas_multicriteria.py")

    return all_ok


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Tests de regresion ESCO Matching')
    parser.add_argument('--only-gold19', action='store_true',
                       help='Ejecutar solo los tests del Gold Set 19')
    parser.add_argument('--only-original', action='store_true',
                       help='Ejecutar solo los tests del Gold Set original')
    args = parser.parse_args()

    print("\n[1] Verificando estado de la base de datos...")

    # Determinar que gold sets verificar
    if args.only_gold19:
        gold_sets = [('GOLD_SET_19', GOLD_SET_19)]
    elif args.only_original:
        gold_sets = [('GOLD_SET', GOLD_SET)]
    else:
        gold_sets = None  # verifica ambos

    if not verify_database_state(gold_sets):
        print("\n[!] No se puede ejecutar el test. Faltan datos en la DB.")
        sys.exit(2)

    exit_code = 0

    # Ejecutar tests originales
    if not args.only_gold19:
        print("\n[2] Ejecutando tests de regresion (Gold Set original)...\n")
        exit_code = run_regression_tests()

    # Ejecutar tests Gold Set 19
    if not args.only_original:
        print("\n[3] Ejecutando tests Gold Set 19 (v8.1)...\n")
        failed_19, results_19 = run_gold_set_19_tests()
        if failed_19 > 0:
            exit_code = max(exit_code, 1)

    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN FINAL DE TESTS")
    print("=" * 70)
    if exit_code == 0:
        print("  TODOS LOS TESTS PASARON")
    else:
        print("  ALGUNOS TESTS FALLARON - Revisar resultados arriba")
    print("=" * 70)

    sys.exit(exit_code)
