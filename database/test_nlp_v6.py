#!/usr/bin/env python3
"""
Test Script para NLP v6.0
==========================

Script de testing para validar la extracción NLP v6.0 con 6 campos nuevos.

Testing EXTENDIDO con 100 ofertas estratégicamente seleccionadas:
- 15 IT Backend (Python/Java/.NET/Node)
- 10 IT Frontend (React/Angular/Vue)
- 10 IT Fullstack
- 8 DevOps/QA/Infraestructura
- 12 Gerenciales/Liderazgo
- 10 Junior/Trainee/Pasantías
- 10 Senior/Experto
- 10 Remoto/Híbrido
- 8 Comercial/Ventas
- 7 Finanzas/Contabilidad

Uso:
    python test_nlp_v6.py
"""

import sys
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List

# Agregar paths para imports
sys.path.insert(0, str(Path(__file__).parent))

from process_nlp_from_db_v6 import NLPExtractorV6


# IDs de ofertas seleccionadas para testing (100 ofertas estratégicas)
# Generado por: select_strategic_offers.py
TEST_OFFER_IDS = [
    2157405, 2162477, 2163289, 2163314, 2163768, 2163987, 2164340, 2164365, 2164920, 2165059,
    2165170, 2165394, 2165945, 2166204, 2166572, 2167698, 2167844, 1117881181, 1117928810, 1117941245,
    1117942606, 1117947639, 1117947690, 1117949821, 1117951568, 1117951965, 1117952023, 1117954926, 1117958199, 1117959738,
    1117965415, 1117968008, 1117968882, 1117971352, 1117971468, 1117972256, 1117974065, 1117974741, 1117974745, 1117980370,
    1117981864, 1117983013, 1117983014, 1117983086, 1117985472, 1117985908, 1117987296, 1117988532, 1117990457, 1117992260,
    1117997428, 1117997884, 1117999065, 1117999834, 1118000684, 1118000738, 1118005251, 1118005752, 1118007244, 1118008131,
    1118008440, 1118010316, 1118010580, 1118010785, 1118012494, 1118014402, 1118015287, 1118016102, 1118016962, 1118016967,
    1118019755, 1118020747, 1118022410, 1118022885, 1118024749, 1118024902, 1118024906, 1118024942, 1118025062, 1118026907,
    1118026908, 1118028057, 1118028271, 1118028663, 1118031118, 1118032081, 1118032180, 1118032737, 1118032845, 1118033649,
    1118034021, 1118035833, 1118036737, 1118037066, 1118037360, 1118037362, 1118038095, 1118039379, 1118040267, 1118040538,
]


def validate_extraction(result: Dict[str, Any], oferta_id: int) -> Dict[str, Any]:
    """
    Valida un resultado de extracción NLP v6.0

    Args:
        result: Resultado de la extracción
        oferta_id: ID de la oferta

    Returns:
        Dict con estadísticas de validación
    """
    validation = {
        "oferta_id": oferta_id,
        "total_fields": 24,
        "fields_present": 0,
        "fields_null": 0,
        "new_fields_v6": {},
        "json_arrays_valid": True,
        "errors": []
    }

    if not result or "extracted_data" not in result:
        validation["errors"].append("No extracted_data in result")
        return validation

    data = result["extracted_data"]

    # Contar campos presentes vs null
    for key, value in data.items():
        if value is not None:
            validation["fields_present"] += 1
        else:
            validation["fields_null"] += 1

    # Validar 6 campos nuevos v6.0
    new_fields = [
        "experiencia_cargo_previo",
        "tecnologias_stack_list",
        "sector_industria",
        "nivel_seniority",
        "modalidad_contratacion",
        "disponibilidad_viajes"
    ]

    for field in new_fields:
        value = data.get(field)
        validation["new_fields_v6"][field] = {
            "present": field in data,
            "value": value,
            "type": type(value).__name__ if value is not None else "null"
        }

    # Validar que arrays JSON sean strings válidos
    json_array_fields = [
        "skills_tecnicas_list",
        "tecnologias_stack_list",
        "soft_skills_list",
        "certificaciones_list",
        "beneficios_list",
        "requisitos_excluyentes_list",
        "requisitos_deseables_list"
    ]

    for field in json_array_fields:
        value = data.get(field)
        if value is not None:
            if not isinstance(value, str):
                validation["json_arrays_valid"] = False
                validation["errors"].append(f"{field} no es string: {type(value)}")
            else:
                try:
                    parsed = json.loads(value)
                    if not isinstance(parsed, list):
                        validation["json_arrays_valid"] = False
                        validation["errors"].append(f"{field} no es array JSON")
                except:
                    validation["json_arrays_valid"] = False
                    validation["errors"].append(f"{field} JSON inválido")

    # Validar quality_score
    if "quality_score" in result:
        validation["quality_score"] = result["quality_score"]
        validation["quality_percentage"] = (result["quality_score"] / 24) * 100

    return validation


def print_field_value(field: str, value: Any, indent: str = "  "):
    """Imprime un campo de forma legible"""
    if value is None:
        print(f"{indent}{field}: null")
    elif isinstance(value, str) and value.startswith("["):
        # Es un JSON array
        try:
            parsed = json.loads(value)
            if len(parsed) > 0:
                print(f"{indent}{field}: {parsed} ({len(parsed)} items)")
            else:
                print(f"{indent}{field}: [] (vacío)")
        except:
            print(f"{indent}{field}: {value}")
    else:
        print(f"{indent}{field}: {value}")


def main():
    """Ejecuta el testing de NLP v6.0"""

    print("=" * 80)
    print("TESTING NLP v6.0 - Validación con 10 ofertas diversas")
    print("=" * 80)
    print(f"\nOfertas a procesar: {len(TEST_OFFER_IDS)}")
    print(f"Campos a extraer: 24 (18 v5 + 6 nuevos v6)\n")

    # Inicializar extractor
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    extractor = NLPExtractorV6(db_path=str(db_path), verbose=True)

    # Conectar a BD
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Estadísticas globales
    global_stats = {
        "total_processed": 0,
        "total_success": 0,
        "total_errors": 0,
        "avg_quality_score": 0,
        "new_fields_coverage": {field: 0 for field in [
            "experiencia_cargo_previo",
            "tecnologias_stack_list",
            "sector_industria",
            "nivel_seniority",
            "modalidad_contratacion",
            "disponibilidad_viajes"
        ]},
        "validations": []
    }

    # Procesar cada oferta
    for i, oferta_id in enumerate(TEST_OFFER_IDS, 1):
        print("\n" + "=" * 80)
        print(f"[{i}/{len(TEST_OFFER_IDS)}] Procesando oferta {oferta_id}")
        print("=" * 80)

        # Obtener oferta
        cursor.execute("""
            SELECT id_oferta, titulo, descripcion
            FROM ofertas
            WHERE id_oferta = ?
        """, (oferta_id,))

        row = cursor.fetchone()
        if not row:
            print(f"ERROR: Oferta {oferta_id} no encontrada")
            global_stats["total_errors"] += 1
            continue

        id_o, titulo, descripcion = row
        print(f"Título: {titulo}")
        print(f"Descripción: {len(descripcion)} caracteres\n")

        # Ejecutar extracción
        try:
            result = extractor.process_oferta(id_o, titulo, descripcion)

            if result:
                global_stats["total_success"] += 1

                # Validar resultado
                validation = validate_extraction(result, oferta_id)
                global_stats["validations"].append(validation)

                # Mostrar resultados
                print(f"\nRESULTADO:")
                print(f"  Quality Score: {result['quality_score']}/24 ({validation.get('quality_percentage', 0):.1f}%)")
                print(f"  Confidence: {result['confidence_score']:.2f}")
                print(f"  Processing Time: {result['processing_time_ms']}ms")

                # Mostrar campos nuevos v6.0
                print(f"\nCAMPOS NUEVOS v6.0:")
                for field, info in validation["new_fields_v6"].items():
                    value = info["value"]
                    print_field_value(field, value, "  ")

                # Contar cobertura de campos nuevos
                for field, info in validation["new_fields_v6"].items():
                    if info["value"] is not None:
                        global_stats["new_fields_coverage"][field] += 1

                # Errores de validación
                if validation["errors"]:
                    print(f"\nERRORES DE VALIDACIÓN:")
                    for error in validation["errors"]:
                        print(f"  - {error}")
                else:
                    print(f"\nValidación: OK")

            else:
                print(f"ERROR: Extracción falló")
                global_stats["total_errors"] += 1

        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            global_stats["total_errors"] += 1

        global_stats["total_processed"] += 1

    conn.close()

    # Reporte final
    print("\n\n" + "=" * 80)
    print("REPORTE FINAL - NLP v6.0 Testing")
    print("=" * 80)

    print(f"\n1. ESTADÍSTICAS GENERALES:")
    print(f"   - Total procesadas: {global_stats['total_processed']}")
    print(f"   - Éxitos: {global_stats['total_success']}")
    print(f"   - Errores: {global_stats['total_errors']}")
    print(f"   - Tasa de éxito: {(global_stats['total_success']/global_stats['total_processed'])*100:.1f}%")

    if global_stats["validations"]:
        avg_quality = sum(v["quality_score"] for v in global_stats["validations"]) / len(global_stats["validations"])
        print(f"\n2. QUALITY SCORE:")
        print(f"   - Promedio: {avg_quality:.1f}/24 ({(avg_quality/24)*100:.1f}%)")
        print(f"   - Mínimo: {min(v['quality_score'] for v in global_stats['validations'])}")
        print(f"   - Máximo: {max(v['quality_score'] for v in global_stats['validations'])}")

        print(f"\n3. COBERTURA DE CAMPOS NUEVOS v6.0:")
        total_ofertas = len(global_stats["validations"])
        for field, count in global_stats["new_fields_coverage"].items():
            coverage_pct = (count / total_ofertas) * 100
            print(f"   - {field:30} {count}/{total_ofertas} ({coverage_pct:.1f}%)")

        print(f"\n4. VALIDACIONES:")
        json_valid_count = sum(1 for v in global_stats["validations"] if v["json_arrays_valid"])
        print(f"   - Arrays JSON válidos: {json_valid_count}/{len(global_stats['validations'])}")

        total_errors = sum(len(v["errors"]) for v in global_stats["validations"])
        print(f"   - Total de errores: {total_errors}")

    print("\n" + "=" * 80)
    print("TESTING COMPLETADO")
    print("=" * 80)

    # Objetivo: >60% quality score promedio, >40% cobertura campos nuevos
    if global_stats["validations"]:
        avg_quality = sum(v["quality_score"] for v in global_stats["validations"]) / len(global_stats["validations"])
        avg_coverage = sum(global_stats["new_fields_coverage"].values()) / (len(global_stats["new_fields_coverage"]) * total_ofertas) * 100

        print(f"\nOBJETIVOS:")
        print(f"  Quality Score >60%: {'✓ CUMPLIDO' if (avg_quality/24)*100 > 60 else '✗ NO CUMPLIDO'} ({(avg_quality/24)*100:.1f}%)")
        print(f"  Cobertura nuevos campos >40%: {'✓ CUMPLIDO' if avg_coverage > 40 else '✗ NO CUMPLIDO'} ({avg_coverage:.1f}%)")


if __name__ == "__main__":
    main()
