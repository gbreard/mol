"""
Pipeline integrado FASE 2: NLP + Matching + Validacion

Este script ejecuta el flujo completo de procesamiento:
1. NLP (si hay ofertas sin NLP o con errores NLP)
2. Matching
3. Validacion (detecta errores NLP + Matching)
4. Auto-correccion
5. Si hay errores NLP -> reprocesar NLP -> volver a paso 2
6. Reporte de patrones para Claude
7. Export Excel validacion
8. Sync learnings.yaml

Uso:
    python scripts/run_validated_pipeline.py --limit 100
    python scripts/run_validated_pipeline.py --ids 123,456,789
    python scripts/run_validated_pipeline.py --only-pending
    python scripts/run_validated_pipeline.py --skip-nlp  # solo matching

Version: 3.0
Fecha: 2026-01-19
"""

import argparse
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from database.match_ofertas_v3 import run_matching_pipeline
from database.auto_validator import AutoValidator, validar_ofertas_desde_bd
from database.auto_corrector import AutoCorrector
from scripts.sync_learnings import sync_learnings_yaml

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"


def get_ids_with_nlp_errors() -> list:
    """Obtiene IDs de ofertas con errores NLP sin resolver (excluye validadas)."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('''
        SELECT DISTINCT ve.id_oferta FROM validation_errors ve
        LEFT JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta
        WHERE ve.resuelto = 0
        AND ve.error_tipo LIKE 'error_nlp_%'
        AND (m.estado_validacion IS NULL OR m.estado_validacion != 'validado')
    ''')
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def get_ids_without_nlp(limit: int = None) -> list:
    """Obtiene IDs de ofertas que no tienen NLP procesado (excluye validadas)."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    query = '''
        SELECT o.id_oferta FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE n.id_oferta IS NULL
        AND (m.estado_validacion IS NULL OR m.estado_validacion != 'validado')
    '''
    if limit:
        query += f' LIMIT {limit}'
    cur.execute(query)
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def run_nlp_for_ids(ids: list, verbose: bool = True) -> dict:
    """Ejecuta NLP para los IDs especificados."""
    if not ids:
        return {"processed": 0}

    if verbose:
        print(f"Procesando NLP para {len(ids)} ofertas...")

    # Importar y ejecutar NLP usando la clase NLPExtractorV11
    from database.process_nlp_from_db_v11 import NLPExtractorV11

    extractor = NLPExtractorV11(verbose=verbose)
    # Convertir IDs a strings (el extractor espera List[str])
    ids_str = [str(x) for x in ids]
    result = extractor.process_batch(ids_especificos=ids_str, save_to_db=True)
    return result


def run_full_pipeline(
    limit: int = None,
    ids: list = None,
    only_pending: bool = False,
    skip_nlp: bool = False,
    skip_matching: bool = False,
    export_markdown: bool = False,
    max_nlp_iterations: int = 2,
    verbose: bool = True
) -> dict:
    """
    Ejecuta el pipeline completo de Fase 2.

    Args:
        limit: Limite de ofertas
        ids: IDs especificos
        only_pending: Solo ofertas pendientes de matching
        skip_nlp: Saltar procesamiento NLP
        skip_matching: Saltar matching, solo validar
        export_markdown: Exportar Markdown para feedback humano
        max_nlp_iterations: Maximo de iteraciones NLP (evitar loops infinitos)
        verbose: Mostrar progreso

    Returns:
        Resultados del pipeline
    """
    resultados = {
        "timestamp": datetime.now().isoformat(),
        "nlp": None,
        "matching": None,
        "validacion": None,
        "correccion": None,
        "patrones_claude": None,
        "nlp_iterations": 0,
        "excel_export": None
    }

    nlp_iteration = 0
    ids_to_process = ids

    # === LOOP PRINCIPAL ===
    while True:
        nlp_iteration += 1
        resultados["nlp_iterations"] = nlp_iteration

        if verbose:
            if nlp_iteration > 1:
                print("\n" + "=" * 60)
                print(f"ITERACION {nlp_iteration}")
                print("=" * 60)

        # PASO 1: NLP (si no se salta)
        if not skip_nlp and nlp_iteration == 1:
            if verbose:
                print("=" * 60)
                print("PASO 1: NLP")
                print("=" * 60)

            # Determinar que ofertas necesitan NLP
            nlp_ids = []

            if ids_to_process:
                # Si hay IDs especificos, verificar cuales necesitan NLP
                conn = sqlite3.connect(str(DB_PATH))
                cur = conn.cursor()
                placeholders = ','.join(['?'] * len(ids_to_process))
                cur.execute(f'''
                    SELECT o.id_oferta FROM ofertas o
                    LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
                    WHERE o.id_oferta IN ({placeholders})
                    AND n.id_oferta IS NULL
                ''', ids_to_process)
                nlp_ids = [row[0] for row in cur.fetchall()]
                conn.close()
            else:
                # Obtener ofertas sin NLP
                nlp_ids = get_ids_without_nlp(limit=limit)

            if nlp_ids:
                if verbose:
                    print(f"Ofertas sin NLP: {len(nlp_ids)}")
                try:
                    nlp_result = run_nlp_for_ids(nlp_ids, verbose=verbose)
                    resultados["nlp"] = nlp_result
                    if verbose:
                        print(f"NLP completado: {nlp_result.get('processed', 0)} ofertas")
                except Exception as e:
                    print(f"Error en NLP: {e}")
                    # Continuar con matching si NLP falla
            else:
                if verbose:
                    print("No hay ofertas pendientes de NLP")

        # PASO 2: Matching (si no se salta)
        if not skip_matching:
            if verbose:
                print("\n" + "=" * 60)
                print("PASO 2: MATCHING")
                print("=" * 60)

            try:
                stats = run_matching_pipeline(
                    offer_ids=ids_to_process,
                    limit=limit,
                    only_pending=only_pending,
                    verbose=verbose
                )
                resultados["matching"] = stats

                # Obtener IDs procesados para validar
                if stats.get("processed_ids"):
                    ids_to_process = stats["processed_ids"]

                if verbose:
                    print(f"\nMatching completado: {stats.get('total_processed', 0)} ofertas")

            except Exception as e:
                print(f"Error en matching: {e}")
                return resultados

        # PASO 3: Validacion
        if verbose:
            print("\n" + "=" * 60)
            print("PASO 3: VALIDACION")
            print("=" * 60)

        validacion = validar_ofertas_desde_bd(limit=limit, ids=ids_to_process)
        resultados["validacion"] = validacion

        if verbose:
            print(f"Total validadas: {validacion['total']}")
            print(f"Sin errores: {validacion['sin_errores']}")
            print(f"Con errores: {validacion['con_errores']}")

        if validacion['con_errores'] == 0:
            if verbose:
                print("\nTodas las ofertas pasaron validacion.")
            break  # Salir del loop

        # PASO 4: Auto-correccion
        if verbose:
            print("\n" + "=" * 60)
            print("PASO 4: AUTO-CORRECCION")
            print("=" * 60)

        conn = sqlite3.connect(str(DB_PATH))
        corrector = AutoCorrector(db_conn=conn)
        correccion = corrector.procesar_errores(validacion)
        resultados["correccion"] = correccion
        conn.close()

        if verbose:
            print(f"Auto-corregidos: {len(correccion['auto_corregidos'])}")
            print(f"Escalados a Claude: {len(correccion['escalados_claude'])}")

        # PASO 5: Verificar errores NLP para reprocesar
        ids_nlp_errors = get_ids_with_nlp_errors()

        # Filtrar solo los que estamos procesando
        if ids_to_process:
            ids_to_process_set = set(str(x) for x in ids_to_process)
            ids_nlp_errors = [x for x in ids_nlp_errors if str(x) in ids_to_process_set]

        if ids_nlp_errors and nlp_iteration < max_nlp_iterations and not skip_nlp:
            if verbose:
                print(f"\n{len(ids_nlp_errors)} ofertas con errores NLP - reprocesando...")

            # Reprocesar NLP para estos IDs
            try:
                nlp_result = run_nlp_for_ids(ids_nlp_errors, verbose=verbose)
                if verbose:
                    print(f"NLP reprocesado: {nlp_result.get('processed', 0)} ofertas")

                # Marcar errores como resueltos para volver a validar
                conn = sqlite3.connect(str(DB_PATH))
                placeholders = ','.join(['?'] * len(ids_nlp_errors))
                conn.execute(f'''
                    UPDATE validation_errors
                    SET resuelto = 1, notas = 'Reprocesado NLP iteracion {nlp_iteration}'
                    WHERE id_oferta IN ({placeholders})
                    AND error_tipo LIKE 'error_nlp_%'
                    AND resuelto = 0
                ''', ids_nlp_errors)
                conn.commit()
                conn.close()

                # Volver a iterar (matching + validacion)
                ids_to_process = ids_nlp_errors
                skip_nlp = True  # Ya reprocesamos NLP, no volver a hacerlo
                continue

            except Exception as e:
                print(f"Error reprocesando NLP: {e}")
                # Continuar sin reprocesar

        # Si llegamos aqui, no hay mas errores NLP para reprocesar
        break

    # === FIN DEL LOOP ===

    # PASO 6: Generar reporte para Claude (si hay errores)
    if resultados.get("correccion") and resultados["correccion"].get('patrones_para_claude'):
        if verbose:
            print("\n" + "=" * 60)
            print("PASO 6: PATRONES PARA CLAUDE")
            print("=" * 60)

        resultados["patrones_claude"] = resultados["correccion"]['patrones_para_claude']

        conn = sqlite3.connect(str(DB_PATH))
        corrector = AutoCorrector(db_conn=conn)
        output_path = corrector.guardar_cola_claude()
        conn.close()

        if verbose:
            print(f"Reporte guardado en: {output_path}")

    # Resumen final
    if verbose:
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)

        if resultados.get("validacion"):
            total = resultados["validacion"]['total']
            ok = resultados["validacion"]['sin_errores']
            if resultados.get("correccion"):
                ok += len(resultados["correccion"].get('auto_corregidos', []))

            print(f"Total ofertas: {total}")
            print(f"Listas para dashboard: {ok} ({100*ok/total:.1f}%)" if total > 0 else "")
            print(f"Iteraciones NLP: {nlp_iteration}")

    # PASO 7: Export Excel para validacion humana
    if verbose:
        print("\n" + "=" * 60)
        print("PASO 7: EXPORT EXCEL")
        print("=" * 60)

    try:
        from scripts.exports.export_validation_excel import export_validation

        excel_path = export_validation(
            etapa="completo",
            offer_ids=ids_to_process if ids_to_process else None,
            limit=limit if not ids_to_process else None
        )
        resultados["excel_export"] = str(excel_path)

        if verbose:
            print(f"Excel exportado: {excel_path}")

    except Exception as e:
        print(f"Warning: Error exportando Excel: {e}")
        resultados["excel_export"] = f"Error: {e}"

    # PASO 8: Sincronizar learnings.yaml
    if verbose:
        print("\n" + "=" * 60)
        print("PASO 8: SYNC LEARNINGS.YAML")
        print("=" * 60)

    try:
        sync_learnings_yaml(verbose=verbose)
        resultados["learnings_sync"] = True
    except Exception as e:
        print(f"Warning: Error sincronizando learnings.yaml: {e}")
        resultados["learnings_sync"] = False

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Pipeline Fase 2: NLP + Matching + Validacion")
    parser.add_argument("--limit", type=int, help="Limite de ofertas")
    parser.add_argument("--ids", type=str, help="IDs separados por coma")
    parser.add_argument("--only-pending", action="store_true", help="Solo ofertas pendientes")
    parser.add_argument("--skip-nlp", action="store_true", help="Saltar NLP, solo matching")
    parser.add_argument("--skip-matching", action="store_true", help="Saltar matching, solo validar")
    parser.add_argument("--export-markdown", action="store_true", help="Exportar Markdown")
    parser.add_argument("--max-nlp-iterations", type=int, default=2, help="Max iteraciones NLP")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")

    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else None

    resultados = run_full_pipeline(
        limit=args.limit,
        ids=ids,
        only_pending=args.only_pending,
        skip_nlp=args.skip_nlp,
        skip_matching=args.skip_matching,
        export_markdown=args.export_markdown,
        max_nlp_iterations=args.max_nlp_iterations,
        verbose=not args.quiet
    )

    # Exit code basado en resultado
    if resultados.get("patrones_claude"):
        sys.exit(1)  # Hay errores que requieren atencion
    sys.exit(0)


if __name__ == "__main__":
    main()
