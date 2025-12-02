#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression Test NLP v8.0 - Anti-Alucinación
============================================

VERSION: 1.0.0
FECHA: 2025-11-27

Este test valida que el pipeline NLP v8.0 NO produzca alucinaciones conocidas:
1. Excel vs Excelentes - NO debe extraer "Excel" de "Excelentes"
2. Parafraseo de soft skills - NO debe convertir "proactivo" → "proactividad"
3. Inventar requisitos - NO debe inventar "Título de Contador" de "contador"
4. Verificación texto_original - El texto debe existir LITERALMENTE en la descripción

Uso:
    python test_nlp_v8_regression.py
    python test_nlp_v8_regression.py --verbose
"""

import sys
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))
scripts_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"
nlp_dir = Path(__file__).parent.parent / "02.5_nlp_extraction"
prompts_dir = nlp_dir / "prompts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(nlp_dir))
sys.path.insert(0, str(prompts_dir))

from prompts.extraction_prompt_v8 import build_prompt

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:14b"


@dataclass
class TestCase:
    """Representa un caso de test anti-alucinación"""
    name: str
    description: str
    titulo: str
    # Items que NO deben aparecer (alucinaciones)
    forbidden_items: Dict[str, List[str]]
    # Items que SÍ deben aparecer (obligatorios)
    required_items: Dict[str, List[str]]
    # Texto que NO debe estar en texto_original (porque no existe)
    forbidden_texto_original: List[str]


# =============================================================================
# CASOS DE TEST - ALUCINACIONES CONOCIDAS
# =============================================================================

TEST_CASES = [
    # -------------------------------------------------------------------------
    # TEST 1: Excel vs Excelentes - El clásico falso positivo
    # -------------------------------------------------------------------------
    TestCase(
        name="Excel_vs_Excelentes",
        titulo="Analista de Datos",
        description="""
        Buscamos Analista de Datos para importante empresa.

        Requisitos:
        - Excelentes habilidades analíticas y de resolución de problemas
        - Excelente capacidad de comunicación verbal y escrita
        - 3 años de experiencia en análisis de datos

        Ofrecemos:
        - Excelente clima laboral
        - Prepaga
        """,
        forbidden_items={
            "skills_tecnicas_list": ["Excel", "excel", "EXCEL"],
            "tecnologias_stack_list": ["Excel", "excel", "EXCEL"],
        },
        required_items={
            "soft_skills_list": ["habilidades analíticas", "comunicación", "resolución de problemas"],
        },
        forbidden_texto_original=["Excel", "excel", "EXCEL"],
    ),

    # -------------------------------------------------------------------------
    # TEST 2: No parafrasear soft skills
    # -------------------------------------------------------------------------
    TestCase(
        name="No_Parafrasear_Soft_Skills",
        titulo="Ejecutivo de Ventas",
        description="""
        Buscamos Ejecutivo de Ventas para zona norte.

        Perfil:
        - Ser proactivo
        - Organizado
        - Gran capacidad negociadora
        - Excelente manejo de relacionesinterpersonales

        Beneficios:
        - Comisiones atractivas
        """,
        forbidden_items={
            "soft_skills_list": [
                "proactividad",  # NO: debe ser "proactivo"
                "organización",  # NO: debe ser "organizado"
                "capacidad de negociación",  # NO: debe ser "gran capacidad negociadora"
                "relaciones interpersonales",  # NO: debe mantener "relacionesinterpersonales" (error original)
            ],
        },
        required_items={
            "soft_skills_list": ["proactivo", "organizado"],
        },
        forbidden_texto_original=[
            "proactividad",
            "organización",
            "capacidad de negociación",
        ],
    ),

    # -------------------------------------------------------------------------
    # TEST 3: No inventar requisitos
    # -------------------------------------------------------------------------
    TestCase(
        name="No_Inventar_Requisitos",
        titulo="Contador para Estudio Contable",
        description="""
        Buscamos contador para estudio contable ubicado en microcentro.

        Tareas:
        - Liquidación de sueldos
        - Armado de balances
        - Atención a clientes

        Se ofrece:
        - Horario de lunes a viernes
        - Buen clima laboral
        """,
        forbidden_items={
            "requisitos_list": [
                "Título de Contador Público",
                "Titulo de Contador",
                "Contador Público Nacional",
                "CPN",
                "experiencia",  # No menciona experiencia
            ],
            "certificaciones_list": [
                "Contador Público",
                "CPN",
            ],
        },
        required_items={
            "responsabilidades_list": ["Liquidación de sueldos", "balances", "clientes"],
        },
        forbidden_texto_original=[
            "Título de Contador",
            "Contador Público",
            "experiencia",
        ],
    ),

    # -------------------------------------------------------------------------
    # TEST 4: No inventar tecnologías por sector
    # -------------------------------------------------------------------------
    TestCase(
        name="No_Inventar_Tecnologias",
        titulo="Administrativo Contable",
        description="""
        Importante empresa busca Administrativo Contable.

        Requisitos:
        - Secundario completo
        - Buena presencia
        - Responsabilidad

        Funciones:
        - Manejo de caja chica
        - Archivo de documentación
        - Atención telefónica
        """,
        forbidden_items={
            "skills_tecnicas_list": [
                "Excel",  # No lo menciona
                "Word",   # No lo menciona
                "SAP",    # No lo menciona
                "Tango",  # No lo menciona
            ],
            "tecnologias_stack_list": [
                "Excel", "Word", "SAP", "Tango",
            ],
        },
        required_items={
            "requisitos_list": ["Secundario completo"],
            "soft_skills_list": ["Responsabilidad", "presencia"],
        },
        forbidden_texto_original=[
            "Excel", "Word", "SAP", "Tango",
        ],
    ),

    # -------------------------------------------------------------------------
    # TEST 5: Extracción correcta con tecnologías explícitas
    # -------------------------------------------------------------------------
    TestCase(
        name="Extraccion_Correcta_IT",
        titulo="Desarrollador Python Senior",
        description="""
        Empresa de tecnología busca Desarrollador Python Senior.

        Requisitos:
        - Python y/o Node.js (al menos uno a nivel productivo)
        - Experiencia con PostgreSQL o MySQL
        - Docker y Kubernetes (deseable)
        - 5 años de experiencia en desarrollo

        Stack:
        - Backend: Python, FastAPI
        - Base de datos: PostgreSQL
        - Contenedores: Docker

        Beneficios:
        - 100% remoto
        - Prepaga
        """,
        forbidden_items={
            # No debería inventar tecnologías que no están
            "skills_tecnicas_list": [
                "Java", "C#", ".NET", "React", "Angular",
            ],
        },
        required_items={
            "skills_tecnicas_list": ["Python", "Node.js", "PostgreSQL", "Docker"],
            "tecnologias_stack_list": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "beneficios_list": ["remoto", "Prepaga"],
        },
        forbidden_texto_original=[
            "Java", "C#", ".NET", "React", "Angular",
        ],
    ),

    # -------------------------------------------------------------------------
    # TEST 6: Texto vacío o mínimo
    # -------------------------------------------------------------------------
    TestCase(
        name="Texto_Minimo",
        titulo="Empleado",
        description="""
        Se busca empleado.
        Presentarse con CV.
        """,
        forbidden_items={
            # No debería inventar NADA
            "skills_tecnicas_list": ["Excel", "Word", "Office"],
            "soft_skills_list": ["proactivo", "dinámico", "responsable"],
            "requisitos_list": ["experiencia", "título", "secundario"],
            "beneficios_list": ["prepaga", "obra social"],
            "certificaciones_list": ["cualquier cosa"],
        },
        required_items={
            # Listas vacías son aceptables
        },
        forbidden_texto_original=[
            "Excel", "experiencia", "proactivo", "prepaga",
        ],
    ),
]


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación (minúsculas, sin acentos extra)"""
    if not text:
        return ""
    # Normalización NFKC
    text = unicodedata.normalize("NFKC", text)
    # Minúsculas
    text = text.lower()
    # Espacios múltiples a uno
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def call_ollama(prompt: str) -> dict:
    """Llama a Ollama y retorna el JSON parseado"""
    import requests

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.1,
            "num_ctx": 4096,
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        raw_response = result.get("response", "")

        # Extraer JSON de la respuesta
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            return json.loads(json_match.group())
        return {}

    except Exception as e:
        print(f"  ERROR Ollama: {e}")
        return {}


def verify_item_in_description(item: dict, description: str) -> bool:
    """Verifica si texto_original está en la descripción"""
    texto_original = item.get("texto_original", "")
    if not texto_original:
        return False

    # Normalizar ambos
    desc_norm = normalize_text(description)
    texto_norm = normalize_text(texto_original)

    # Verificar substring
    return texto_norm in desc_norm


def extract_values_from_list(items: list) -> List[str]:
    """Extrae valores de una lista de items {valor, texto_original}"""
    values = []
    for item in items:
        if isinstance(item, dict):
            val = item.get("valor", "")
            if val:
                values.append(val.lower())
        elif isinstance(item, str):
            values.append(item.lower())
    return values


def run_test_case(test_case: TestCase, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Ejecuta un caso de test y retorna (passed, errors)
    """
    errors = []

    print(f"\n{'='*60}")
    print(f"TEST: {test_case.name}")
    print(f"{'='*60}")
    print(f"Título: {test_case.titulo}")
    print(f"Descripción: {test_case.description[:100]}...")

    # Construir prompt y llamar al LLM
    prompt = build_prompt(test_case.description)
    result = call_ollama(prompt)

    if not result:
        errors.append("No se pudo obtener respuesta del LLM")
        return False, errors

    if verbose:
        print(f"\nRespuesta LLM:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # VERIFICACIÓN 1: Items prohibidos (NO deben aparecer)
    print("\n[VERIFICANDO ITEMS PROHIBIDOS]")
    for campo, forbidden_values in test_case.forbidden_items.items():
        items = result.get(campo, [])
        extracted_values = extract_values_from_list(items)

        for forbidden in forbidden_values:
            forbidden_lower = forbidden.lower()
            for extracted in extracted_values:
                if forbidden_lower in extracted or extracted in forbidden_lower:
                    error = f"ALUCINACIÓN: '{forbidden}' encontrado en {campo}"
                    errors.append(error)
                    print(f"  FAIL: {error}")

    # VERIFICACIÓN 2: Items requeridos (SÍ deben aparecer)
    print("\n[VERIFICANDO ITEMS REQUERIDOS]")
    for campo, required_values in test_case.required_items.items():
        items = result.get(campo, [])
        extracted_values = extract_values_from_list(items)

        for required in required_values:
            required_lower = required.lower()
            found = any(
                required_lower in ext or ext in required_lower
                for ext in extracted_values
            )
            if not found:
                error = f"MISSING: '{required}' no encontrado en {campo}"
                errors.append(error)
                print(f"  WARN: {error}")
            else:
                print(f"  OK: '{required}' encontrado en {campo}")

    # VERIFICACIÓN 3: texto_original debe existir en descripción
    print("\n[VERIFICANDO TEXTO_ORIGINAL]")
    for campo in result:
        if not campo.endswith("_list"):
            continue
        items = result.get(campo, [])
        for item in items:
            if isinstance(item, dict):
                texto_orig = item.get("texto_original", "")
                valor = item.get("valor", "")
                if texto_orig:
                    if not verify_item_in_description(item, test_case.description):
                        error = f"TEXTO_ORIGINAL NO EXISTE: '{texto_orig}' en {campo}"
                        errors.append(error)
                        print(f"  FAIL: {error}")
                    else:
                        if verbose:
                            print(f"  OK: '{valor}' tiene texto_original válido")

    # VERIFICACIÓN 4: texto_original prohibido (word boundary check)
    print("\n[VERIFICANDO TEXTO_ORIGINAL PROHIBIDO]")
    for campo in result:
        if not campo.endswith("_list"):
            continue
        items = result.get(campo, [])
        for item in items:
            if isinstance(item, dict):
                texto_orig = item.get("texto_original", "")
                valor = item.get("valor", "")
                for forbidden in test_case.forbidden_texto_original:
                    # Word boundary check - "Excel" no debe matchear "Excelentes"
                    pattern = r'\b' + re.escape(forbidden) + r'\b'
                    if re.search(pattern, texto_orig, re.IGNORECASE):
                        error = f"TEXTO_ORIGINAL PROHIBIDO: '{forbidden}' en {campo} (valor: {valor})"
                        errors.append(error)
                        print(f"  FAIL: {error}")
                    # También verificar en valor
                    if re.search(pattern, valor, re.IGNORECASE):
                        error = f"VALOR PROHIBIDO: '{forbidden}' en {campo}"
                        errors.append(error)
                        print(f"  FAIL: {error}")

    # Resultado
    passed = len(errors) == 0
    status = "PASSED" if passed else "FAILED"
    print(f"\n>>> RESULTADO: {status} ({len(errors)} errores)")

    return passed, errors


def main():
    """Ejecuta todos los tests de regresión"""
    import argparse

    parser = argparse.ArgumentParser(description="Regression Test NLP v8.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument("--test", "-t", type=str, help="Ejecutar solo un test específico")
    args = parser.parse_args()

    print("="*70)
    print("REGRESSION TEST NLP v8.0 - ANTI-ALUCINACIÓN")
    print("="*70)
    print(f"Modelo: {OLLAMA_MODEL}")
    print(f"Tests a ejecutar: {len(TEST_CASES)}")
    print()

    # Verificar que Ollama esté disponible
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(OLLAMA_MODEL.split(":")[0] in m for m in models):
            print(f"WARNING: Modelo {OLLAMA_MODEL} no encontrado")
            print(f"Modelos disponibles: {models}")
    except:
        print("ERROR: Ollama no está disponible en localhost:11434")
        sys.exit(1)

    results = []

    for test_case in TEST_CASES:
        if args.test and args.test not in test_case.name:
            continue
        passed, errors = run_test_case(test_case, verbose=args.verbose)
        results.append({
            "name": test_case.name,
            "passed": passed,
            "errors": errors,
        })

    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\nTests ejecutados: {total}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"Tasa de éxito: {(passed/total)*100:.1f}%")

    if failed > 0:
        print("\n--- TESTS FALLIDOS ---")
        for r in results:
            if not r["passed"]:
                print(f"\n{r['name']}:")
                for err in r["errors"]:
                    print(f"  - {err}")

    print("\n" + "="*70)
    if failed == 0:
        print("TODOS LOS TESTS PASARON - Pipeline anti-alucinación OK")
    else:
        print(f"HAY {failed} TESTS FALLIDOS - Revisar pipeline")
    print("="*70)

    # Exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
