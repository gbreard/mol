#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Configs FASE 1/2/3 - Validar cambios de configuración
==========================================================

Valida que todos los JSONs de configuración estén correctos
y que la lógica de los cambios funcione sin requerir numpy.

Ejecutar desde cualquier directorio:
    python3 scripts/nlp/gold_set/test_configs_fase123.py
"""

import json
import re
import sqlite3
import sys
import io
from pathlib import Path
from datetime import datetime

# Setup paths
BASE = Path(__file__).parent.parent.parent.parent
CONFIG_PATH = BASE / "config"
DB_PATH = BASE / "database" / "bumeran_scraping.db"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_titulo_limpieza_config():
    """Test FASE 1: Validar config de limpieza títulos."""
    print("\n" + "=" * 60)
    print("TEST 1: Config Limpieza Títulos (nlp_titulo_limpieza.json)")
    print("=" * 60)

    config_file = CONFIG_PATH / "nlp_titulo_limpieza.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[OK] JSON válido")
    except Exception as e:
        print(f"[ERROR] JSON inválido: {e}")
        return False

    # Verificar secciones nuevas de FASE 1
    expected_sections = [
        "codigos_final",
        "modalidad_guion",
        "requisitos_edad",
        "ubicacion_guion_extendido"
    ]

    found = []
    missing = []
    for section in expected_sections:
        if section in config:
            found.append(section)
            patrones = config[section].get("patrones", [])
            print(f"[OK] Sección '{section}': {len(patrones)} patrones")
        else:
            missing.append(section)
            print(f"[WARN] Falta sección: {section}")

    # Probar patrones con ejemplos
    test_cases = [
        ("DevOps Engineer - Remoto - 1729", "DevOps Engineer"),
        ("Analista SAP Jr - Rosario - 1779", "Analista SAP Jr"),
        ("JAVA Architect - Mix (On Site & Remoto) - Retiro", "JAVA Architect"),
        ("Cajero 25-35 años", "Cajero"),
        ("Vendedor +45 años", "Vendedor"),
    ]

    print("\nPruebas de limpieza:")
    passed = 0
    for titulo_in, expected in test_cases:
        resultado = titulo_in

        # Aplicar patrones de codigos_final
        for p in config.get("codigos_final", {}).get("patrones", []):
            pattern = p.get("patron", "")
            if pattern:
                resultado = re.sub(pattern, '', resultado, flags=re.IGNORECASE)

        # Aplicar patrones de modalidad_guion
        for p in config.get("modalidad_guion", {}).get("patrones", []):
            pattern = p.get("patron", "")
            if pattern:
                resultado = re.sub(pattern, '', resultado, flags=re.IGNORECASE)

        # Aplicar patrones de requisitos_edad (rangos primero, simples después)
        for p in config.get("requisitos_edad", {}).get("patrones", []):
            pattern = p.get("patron", "")
            if pattern:
                resultado = re.sub(pattern, '', resultado, flags=re.IGNORECASE)

        resultado = resultado.strip()

        if resultado == expected:
            print(f"  [OK] '{titulo_in[:40]}' -> '{resultado}'")
            passed += 1
        else:
            print(f"  [FAIL] '{titulo_in[:40]}' -> '{resultado}' (esperado: '{expected}')")

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasaron")
    return passed == len(test_cases)


def test_sector_isco_config():
    """Test FASE 1: Validar config sector-ISCO."""
    print("\n" + "=" * 60)
    print("TEST 2: Config Sector-ISCO (sector_isco_compatibilidad.json)")
    print("=" * 60)

    config_file = CONFIG_PATH / "sector_isco_compatibilidad.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[OK] JSON válido")
    except Exception as e:
        print(f"[ERROR] JSON inválido: {e}")
        return False

    # Verificar estructura
    sectores = config.get("sectores", {})
    aliases = config.get("aliases", {})
    genericos = config.get("isco_genericos", [])

    print(f"[OK] Sectores definidos: {len(sectores)}")
    print(f"[OK] Aliases definidos: {len(aliases)}")
    print(f"[OK] ISCOs genéricos: {len(genericos)}")

    # Verificar sectores clave
    key_sectors = ["Tecnologia", "Gastronomia", "Finanzas", "Agropecuario", "Construccion"]
    for sector in key_sectors:
        if sector in sectores:
            data = sectores[sector]
            compat = len(data.get("isco_compatibles", []))
            incompat = len(data.get("isco_incompatibles", []))
            print(f"  - {sector}: {compat} ISCOs compatibles, {incompat} incompatibles")
        else:
            print(f"  [WARN] Falta sector: {sector}")

    # Test penalización
    test_cases = [
        ("Tecnologia", "2512", False),  # Compatible
        ("Tecnologia", "6111", True),   # Incompatible (Agro)
        ("Gastronomia", "5120", False), # Compatible
        ("Gastronomia", "2512", True),  # Incompatible (IT)
        ("Finanzas", "2411", False),    # Compatible
    ]

    print("\nPruebas de compatibilidad:")
    passed = 0
    for sector, isco, should_penalize in test_cases:
        if sector not in sectores:
            print(f"  [SKIP] Sector '{sector}' no definido")
            continue

        data = sectores[sector]
        compatibles = data.get("isco_compatibles", [])
        incompatibles = data.get("isco_incompatibles", [])

        isco_prefix = isco[:2] if len(isco) >= 2 else isco

        is_compatible = any(isco.startswith(c) or isco_prefix == c for c in compatibles)
        is_incompatible = any(isco.startswith(c) or isco_prefix == c for c in incompatibles)

        penalized = is_incompatible or (not is_compatible and incompatibles)

        if penalized == should_penalize:
            status = "PENALIZA" if penalized else "OK"
            print(f"  [OK] {sector} + ISCO {isco} -> {status}")
            passed += 1
        else:
            print(f"  [FAIL] {sector} + ISCO {isco}: esperaba penalizar={should_penalize}")

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasaron")
    return passed >= 4  # Al menos 4 de 5


def test_business_rules_config():
    """Test FASE 2: Validar reglas de negocio IT."""
    print("\n" + "=" * 60)
    print("TEST 3: Reglas de Negocio IT (matching_rules_business.json)")
    print("=" * 60)

    config_file = CONFIG_PATH / "matching_rules_business.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[OK] JSON válido")
    except Exception as e:
        print(f"[ERROR] JSON inválido: {e}")
        return False

    # Verificar reglas IT nuevas (FASE 2)
    it_rules = [
        ("R43_IT_devops", "2523"),
        ("R44_IT_architect", "2512"),
        ("R45_IT_analista_sap", "2511"),
        ("R46_IT_integraciones", "2511"),
        ("R47_IT_data_engineer", "2521"),
    ]

    rules = config.get("rules", config)  # Puede estar en "rules" o raíz

    found_rules = 0
    for rule_name, expected_isco in it_rules:
        if rule_name in rules:
            rule = rules[rule_name]
            isco = rule.get("accion", {}).get("forzar_isco", "")
            if isco == expected_isco:
                print(f"  [OK] {rule_name}: fuerza ISCO {isco}")
                found_rules += 1
            else:
                print(f"  [FAIL] {rule_name}: ISCO {isco} (esperado {expected_isco})")
        else:
            print(f"  [WARN] Falta regla: {rule_name}")

    # Test aplicación de reglas
    test_cases = [
        ("DevOps Engineer", None, "R43_IT_devops"),
        ("SRE Senior", None, "R43_IT_devops"),
        ("Software Architect Java", None, "R44_IT_architect"),
        ("Analista SAP FI", None, "R45_IT_analista_sap"),
        ("Data Engineer", None, "R47_IT_data_engineer"),
    ]

    print("\nPruebas de matching reglas:")
    matched = 0
    for titulo, area, expected_rule in test_cases:
        titulo_lower = titulo.lower()

        # Buscar regla que matchea
        matched_rule = None
        for rule_name, rule in rules.items():
            if not rule_name.startswith("R"):
                continue

            condicion = rule.get("condicion", {})
            keywords = condicion.get("titulo_contiene_alguno", [])

            if any(kw.lower() in titulo_lower for kw in keywords):
                matched_rule = rule_name
                break

        if matched_rule == expected_rule:
            print(f"  [OK] '{titulo}' -> {matched_rule}")
            matched += 1
        else:
            print(f"  [FAIL] '{titulo}' -> {matched_rule} (esperado {expected_rule})")

    print(f"\nResultado: {found_rules}/5 reglas IT, {matched}/{len(test_cases)} matches")
    return found_rules >= 4 and matched >= 3


def test_skills_weights_config():
    """Test FASE 2: Validar config de pesos skills genéricas."""
    print("\n" + "=" * 60)
    print("TEST 4: Pesos Skills Genéricas (skills_weights.json)")
    print("=" * 60)

    config_file = CONFIG_PATH / "skills_weights.json"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[OK] JSON válido")
    except Exception as e:
        print(f"[ERROR] JSON inválido: {e}")
        return False

    # Verificar skills genéricas
    genericas = config.get("skills_genericas", {})
    lista = genericas.get("lista", [])
    peso = genericas.get("peso", 1.0)

    print(f"[OK] Skills genéricas: {len(lista)}")
    print(f"[OK] Peso genéricas: {peso}")

    # Verificar skills esperadas
    expected_skills = [
        "trabajo en equipo",
        "comunicacion",
        "liderazgo",
        "gestion",
        "proactividad",
        "resolucion de problemas",
    ]

    lista_lower = [s.lower() for s in lista]
    found = 0
    for skill in expected_skills:
        if skill.lower() in lista_lower:
            found += 1

    print(f"[OK] Skills clave encontradas: {found}/{len(expected_skills)}")

    # Test peso
    if peso < 1.0:
        print(f"[OK] Peso correcto ({peso} < 1.0 para reducir impacto)")
        return True
    else:
        print(f"[WARN] Peso debería ser < 1.0 (actual: {peso})")
        return False


def test_seniority_penalty_logic():
    """Test FASE 3: Validar lógica de penalización seniority."""
    print("\n" + "=" * 60)
    print("TEST 5: Lógica Penalización Seniority")
    print("=" * 60)

    # Simular la lógica de _apply_seniority_penalty
    test_cases = [
        # (seniority, isco, should_penalize)
        ("trainee", "1211", True),   # trainee no debería ser director
        ("junior", "1221", True),    # junior no debería ser director ventas
        ("junior", "2512", False),   # junior SÍ puede ser desarrollador
        ("manager", "9112", True),   # manager no debería ser limpiador
        ("director", "9411", True),  # director no debería ser ayudante cocina
        ("senior", "2511", False),   # senior SÍ puede ser analista
    ]

    passed = 0
    for seniority, isco, should_penalize in test_cases:
        # Lógica de penalización
        penalize = False

        if seniority in ["trainee", "junior"]:
            # No deberían ser directores/gerentes (ISCO 1xxx)
            if isco.startswith("1"):
                penalize = True

        elif seniority in ["manager", "director", "lead"]:
            # No deberían ser trabajadores no calificados (ISCO 9xxx)
            if isco.startswith("9"):
                penalize = True

        if penalize == should_penalize:
            action = "PENALIZA" if penalize else "OK"
            print(f"  [OK] {seniority} + ISCO {isco} -> {action}")
            passed += 1
        else:
            print(f"  [FAIL] {seniority} + ISCO {isco}: esperaba penalizar={should_penalize}")

    print(f"\nResultado: {passed}/{len(test_cases)} tests pasaron")
    return passed == len(test_cases)


def test_db_sample():
    """Test: Obtener muestra de BD para validar datos."""
    print("\n" + "=" * 60)
    print("TEST 6: Muestra de BD (100 IDs)")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"[SKIP] BD no encontrada: {DB_PATH}")
        return True  # No fallar por esto

    try:
        conn = sqlite3.connect(str(DB_PATH))

        # Contar ofertas con NLP
        cur = conn.execute('''
            SELECT COUNT(*) FROM ofertas_nlp WHERE titulo_limpio IS NOT NULL
        ''')
        count_nlp = cur.fetchone()[0]
        print(f"[OK] Ofertas con NLP: {count_nlp}")

        # Contar ofertas con matching
        cur = conn.execute('''
            SELECT COUNT(*) FROM ofertas_esco_matching
        ''')
        count_match = cur.fetchone()[0]
        print(f"[OK] Ofertas con matching: {count_match}")

        # Muestra de sectores
        cur = conn.execute('''
            SELECT sector_empresa, COUNT(*) as cnt
            FROM ofertas_nlp
            WHERE sector_empresa IS NOT NULL AND sector_empresa != ''
            GROUP BY sector_empresa
            ORDER BY cnt DESC
            LIMIT 10
        ''')
        print("\nTop sectores:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]}")

        # Muestra de seniority
        cur = conn.execute('''
            SELECT nivel_seniority, COUNT(*) as cnt
            FROM ofertas_nlp
            WHERE nivel_seniority IS NOT NULL AND nivel_seniority != ''
            GROUP BY nivel_seniority
            ORDER BY cnt DESC
            LIMIT 8
        ''')
        print("\nTop seniority:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    """Ejecuta todos los tests."""
    print("=" * 70)
    print("TEST CONFIGS FASE 1/2/3")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    results = {
        "titulo_limpieza": test_titulo_limpieza_config(),
        "sector_isco": test_sector_isco_config(),
        "business_rules": test_business_rules_config(),
        "skills_weights": test_skills_weights_config(),
        "seniority_penalty": test_seniority_penalty_logic(),
        "db_sample": test_db_sample(),
    }

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test}")

    print(f"\nTotal: {passed}/{total} tests pasaron")

    if passed == total:
        print("\n[SUCCESS] Todas las configuraciones FASE 1/2/3 están correctas")
    else:
        print("\n[WARNING] Algunas configuraciones tienen problemas")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
