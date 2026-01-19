#!/usr/bin/env python3
"""
Test NLP Postprocessor con Gold Set
====================================

Compara resultados ANTES y DESPUES del postprocesamiento
para las 49 ofertas del Gold Set.

Errores criticos a verificar:
  - ID 1118027243: TRUE en campos texto
  - ID 1118026729: FALSO\nCapital Federal
  - ID 1117984105: experiencia=35 (era edad)
  - ID 1118023904: experiencia=20 (era edad)
  - ID 1118026700: ubicacion no parseada

Uso:
    python scripts/test_nlp_postprocessor_gold_set.py
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from nlp_postprocessor import NLPPostprocessor


# IDs criticos con errores conocidos
IDS_CRITICOS = {
    "1118027243": {"error": "TRUE en campos texto", "campos": ["provincia", "localidad", "modalidad"]},
    "1118026729": {"error": "FALSO\\nCapital Federal", "campos": ["provincia", "localidad"]},
    "1117984105": {"error": "experiencia=35 (era edad 35-50)", "campos": ["experiencia_min_anios"]},
    "1118023904": {"error": "experiencia=20 (era edad 20-45)", "campos": ["experiencia_min_anios"]},
    "1118026700": {"error": "ubicacion no parseada", "campos": ["provincia", "localidad"]},
}


def load_gold_set_ids() -> list:
    """Carga IDs del Gold Set"""
    gold_set_path = Path(__file__).parent.parent / "database" / "gold_set_manual_v2.json"

    if gold_set_path.exists():
        with open(gold_set_path, "r", encoding="utf-8") as f:
            gold_set = json.load(f)
            # El gold set es una lista directa de objetos
            if isinstance(gold_set, list):
                return [str(item.get("id_oferta")) for item in gold_set]
            # O un objeto con propiedad "ofertas"
            return [str(item.get("id_oferta")) for item in gold_set.get("ofertas", [])]

    # Fallback: IDs conocidos
    return list(IDS_CRITICOS.keys())


def get_ofertas_from_db(ids: list) -> dict:
    """Obtiene ofertas de la BD"""
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(ids))
    # Nota: columna es "localizacion" no "ubicacion"
    query = f"""
        SELECT id_oferta, titulo, empresa, localizacion as ubicacion, descripcion
        FROM ofertas
        WHERE id_oferta IN ({placeholders})
    """
    cursor.execute(query, ids)

    ofertas = {}
    for row in cursor.fetchall():
        ofertas[str(row["id_oferta"])] = dict(row)

    conn.close()
    return ofertas


def get_nlp_from_db(ids: list) -> dict:
    """Obtiene datos NLP actuales de la BD"""
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(ids))
    query = f"""
        SELECT *
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """
    cursor.execute(query, ids)

    nlp_data = {}
    for row in cursor.fetchall():
        nlp_data[str(row["id_oferta"])] = dict(row)

    conn.close()
    return nlp_data


def simulate_before_after(ofertas: dict, nlp_data: dict, pp: NLPPostprocessor) -> dict:
    """
    Simula el procesamiento antes/despues del postprocesador
    """
    results = {}

    for id_oferta, oferta in ofertas.items():
        nlp = nlp_data.get(id_oferta, {})
        descripcion = oferta.get("descripcion", "")

        # ANTES: datos crudos de NLP
        before = {
            "provincia": nlp.get("provincia"),
            "localidad": nlp.get("localidad"),
            "modalidad": nlp.get("modalidad"),
            "nivel_seniority": nlp.get("nivel_seniority"),
            "area_funcional": nlp.get("area_funcional"),
            "experiencia_min_anios": nlp.get("experiencia_min_anios"),
        }

        # Simular preprocesamiento
        row_data = {
            "ubicacion": oferta.get("ubicacion", ""),
            "empresa": oferta.get("empresa", ""),
            "titulo": oferta.get("titulo", ""),
        }
        pre_data = pp.preprocess(row_data)

        # DESPUES: aplicar postprocesamiento
        after_data = before.copy()

        # Agregar datos preprocesados
        for campo, valor in pre_data.items():
            if after_data.get(campo) is None and valor is not None:
                after_data[campo] = valor

        after = pp.postprocess(after_data, descripcion)

        # Detectar cambios
        changes = []
        for campo in before:
            if before[campo] != after.get(campo):
                changes.append({
                    "campo": campo,
                    "antes": before[campo],
                    "despues": after.get(campo),
                })

        results[id_oferta] = {
            "titulo": oferta.get("titulo", "")[:50],
            "ubicacion_raw": oferta.get("ubicacion", ""),
            "before": before,
            "after": after,
            "changes": changes,
            "is_critical": id_oferta in IDS_CRITICOS,
            "critical_info": IDS_CRITICOS.get(id_oferta),
        }

    return results


def print_report(results: dict):
    """Imprime reporte comparativo"""
    print("=" * 80)
    print("REPORTE: NLP POSTPROCESSOR - GOLD SET")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Total ofertas: {len(results)}")
    print()

    # Resumen de cambios
    total_changes = 0
    campos_mejorados = {}

    for id_oferta, data in results.items():
        for change in data["changes"]:
            total_changes += 1
            campo = change["campo"]
            campos_mejorados[campo] = campos_mejorados.get(campo, 0) + 1

    print("-" * 80)
    print("RESUMEN DE CAMBIOS")
    print("-" * 80)
    print(f"Total cambios: {total_changes}")
    for campo, count in sorted(campos_mejorados.items(), key=lambda x: -x[1]):
        print(f"  {campo}: {count} cambios")
    print()

    # Casos criticos
    print("-" * 80)
    print("CASOS CRITICOS (errores conocidos)")
    print("-" * 80)

    for id_oferta in IDS_CRITICOS:
        data = results.get(id_oferta)
        if not data:
            print(f"\n[!] {id_oferta}: NO ENCONTRADO EN BD")
            continue

        critical = data["critical_info"]
        print(f"\n[{id_oferta}] {critical['error']}")
        print(f"  Titulo: {data['titulo']}")

        for change in data["changes"]:
            if change["campo"] in critical["campos"]:
                status = "CORREGIDO" if change["despues"] not in [None, True, False, "TRUE", "FALSE"] else "PENDIENTE"
                print(f"  [{status}] {change['campo']}: {change['antes']} -> {change['despues']}")

        if not data["changes"]:
            print("  [SIN CAMBIOS]")

    # Todos los cambios
    print()
    print("-" * 80)
    print("TODOS LOS CAMBIOS")
    print("-" * 80)

    for id_oferta, data in results.items():
        if data["changes"]:
            print(f"\n[{id_oferta}] {data['titulo']}")
            if data["ubicacion_raw"]:
                print(f"  ubicacion_raw: '{data['ubicacion_raw']}'")
            for change in data["changes"]:
                print(f"  {change['campo']}: {change['antes']} -> {change['despues']}")

    # Metricas finales
    print()
    print("=" * 80)
    print("METRICAS")
    print("=" * 80)

    # Calcular cobertura antes/despues
    campos_check = ["provincia", "localidad", "modalidad", "nivel_seniority", "area_funcional"]

    for campo in campos_check:
        antes_ok = sum(1 for r in results.values() if r["before"].get(campo) not in [None, "", True, False])
        despues_ok = sum(1 for r in results.values() if r["after"].get(campo) not in [None, "", True, False])
        mejora = despues_ok - antes_ok
        mejora_str = f"+{mejora}" if mejora > 0 else str(mejora)

        print(f"{campo}:")
        print(f"  Antes:   {antes_ok}/{len(results)} ({100*antes_ok/len(results):.1f}%)")
        print(f"  Despues: {despues_ok}/{len(results)} ({100*despues_ok/len(results):.1f}%) [{mejora_str}]")


def main():
    print("Cargando Gold Set...")
    gold_set_ids = load_gold_set_ids()
    print(f"IDs en Gold Set: {len(gold_set_ids)}")

    print("Cargando ofertas de BD...")
    ofertas = get_ofertas_from_db(gold_set_ids)
    print(f"Ofertas encontradas: {len(ofertas)}")

    print("Cargando datos NLP de BD...")
    nlp_data = get_nlp_from_db(gold_set_ids)
    print(f"Registros NLP encontrados: {len(nlp_data)}")

    print("Inicializando postprocesador...")
    pp = NLPPostprocessor(verbose=False)

    print("Simulando antes/despues...")
    results = simulate_before_after(ofertas, nlp_data, pp)

    print()
    print_report(results)


if __name__ == "__main__":
    main()
