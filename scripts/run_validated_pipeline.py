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

SISTEMA DE PRIORIDAD (v3.1):
- Con --limit: Selecciona ofertas por prioridad (fecha + vacantes + permanencia)
- Persiste estado en tabla ofertas_prioridad
- Bloquea avance si hay errores pendientes del lote anterior
- Ver estado: python scripts/get_priority_batch.py --queue-status

Uso:
    python scripts/run_validated_pipeline.py --limit 100           # Por prioridad
    python scripts/run_validated_pipeline.py --limit 100 --no-priority  # Sin prioridad
    python scripts/run_validated_pipeline.py --ids 123,456,789     # IDs especificos
    python scripts/run_validated_pipeline.py --only-pending
    python scripts/run_validated_pipeline.py --skip-nlp            # Solo matching

Version: 3.3
Fecha: 2026-02-13

Cambios v3.3:
- PASO 1.5b: Auto-correccion + escalamiento Claude para errores NLP gate
- Flujo completo: Validar NLP → Auto-corregir → Re-validar → Escalar a Claude
- Misma logica que PASO 3-4 (matching) replicada para NLP pre-matching

Cambios v3.2:
- PASO 1.5: NLP Validation Gate (nlp_validator.py) entre NLP y Matching
- Ofertas con errores critico/alto quedan bloqueadas (no entran a matching)
- Genera extraction_report en metrics/
"""

import argparse
import json
import sys
import io
import sqlite3
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows subprocess
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (ValueError, AttributeError, OSError):
    pass


def safe_print(*args, **kwargs):
    """Print function that handles closed stdout gracefully."""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass


# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from database.match_ofertas_v3 import run_matching_pipeline
from database.auto_validator import AutoValidator, validar_ofertas_desde_bd
from database.auto_corrector import AutoCorrector
from database.nlp_validator import NLPValidator
from scripts.sync_learnings import sync_learnings_yaml

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_errores_bloqueantes() -> set:
    """Carga lista de error_ids que bloquean transición a validado_claude."""
    try:
        vr = json.loads((CONFIG_DIR / "validation_rules.json").read_text(encoding='utf-8'))
        return set(vr.get("politica_transicion", {}).get("errores_bloqueantes", []))
    except Exception:
        # Fallback conservador: todo bloquea
        return {"V02_isco_nulo_score_bajo", "V10_match_score_muy_bajo", "NV02_sector_no_canonico"}


def auto_transicionar_pendientes(ids: list, verbose: bool = False) -> dict:
    """
    PASO 4.5: Transiciona ofertas de 'pendiente' a 'validado_claude'
    si no tienen errores bloqueantes.

    Returns: {evaluadas, transicionadas, bloqueadas, ids_bloqueados}
    """
    bloqueantes = _load_errores_bloqueantes()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    str_ids = [str(i) for i in ids]
    placeholders = ','.join(['?'] * len(str_ids))

    # Get offers that are still pendiente
    pendientes = conn.execute(f"""
        SELECT id_oferta FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders})
        AND estado_validacion = 'pendiente'
    """, str_ids).fetchall()

    pendiente_ids = [r['id_oferta'] for r in pendientes]
    if not pendiente_ids:
        conn.close()
        return {"evaluadas": 0, "transicionadas": 0, "bloqueadas": 0, "ids_bloqueados": []}

    # Find which have blocking errors
    ph2 = ','.join(['?'] * len(pendiente_ids))
    blocked = conn.execute(f"""
        SELECT DISTINCT id_oferta FROM validation_errors
        WHERE id_oferta IN ({ph2})
        AND resuelto = 0
        AND error_id IN ({','.join(['?'] * len(bloqueantes))})
    """, pendiente_ids + list(bloqueantes)).fetchall()

    blocked_ids = set(r['id_oferta'] for r in blocked)
    to_transition = [oid for oid in pendiente_ids if oid not in blocked_ids]

    # Transition in batch
    timestamp = datetime.now().isoformat()
    if to_transition:
        ph3 = ','.join(['?'] * len(to_transition))
        conn.execute(f"""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'validado_claude',
                validado_timestamp = ?,
                validado_por = 'auto_transicion'
            WHERE id_oferta IN ({ph3})
            AND estado_validacion = 'pendiente'
        """, [timestamp] + to_transition)
        conn.commit()

    conn.close()

    result = {
        "evaluadas": len(pendiente_ids),
        "transicionadas": len(to_transition),
        "bloqueadas": len(blocked_ids),
        "ids_bloqueados": list(blocked_ids)[:20],
    }

    if verbose and blocked_ids:
        safe_print(f"  IDs bloqueados: {', '.join(list(blocked_ids)[:5])}{'...' if len(blocked_ids) > 5 else ''}")

    return result


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
        safe_print(f"Procesando NLP para {len(ids)} ofertas...")

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
                safe_print("\n" + "=" * 60)
                safe_print(f"ITERACION {nlp_iteration}")
                safe_print("=" * 60)

        # PASO 1: NLP (si no se salta)
        if not skip_nlp and nlp_iteration == 1:
            if verbose:
                safe_print("=" * 60)
                safe_print("PASO 1: NLP")
                safe_print("=" * 60)

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
                    safe_print(f"Ofertas sin NLP: {len(nlp_ids)}")
                try:
                    nlp_result = run_nlp_for_ids(nlp_ids, verbose=verbose)
                    resultados["nlp"] = nlp_result
                    if verbose:
                        safe_print(f"NLP completado: {nlp_result.get('processed', 0)} ofertas")
                except Exception as e:
                    safe_print(f"Error en NLP: {e}")
                    # Continuar con matching si NLP falla
            else:
                if verbose:
                    safe_print("No hay ofertas pendientes de NLP")

        # PASO 1.5: NLP VALIDATION (GATE) + AUTO-CORRECCION + ESCALAMIENTO
        if verbose:
            safe_print("\n" + "=" * 60)
            safe_print("PASO 1.5: NLP VALIDATION (GATE)")
            safe_print("=" * 60)

        nlp_validator = NLPValidator(verbose=verbose)
        current_run_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        nlp_validation = nlp_validator.validar_desde_bd(
            ids=ids_to_process,
            limit=limit if not ids_to_process else None,
            persist=True,
            run_id=current_run_id,
            update_gate=True
        )
        resultados["nlp_validation"] = {
            "total": nlp_validation["total"],
            "gate_pass": nlp_validation["gate_pass_count"],
            "gate_block": nlp_validation["gate_block_count"],
            "errores_por_severidad": nlp_validation.get("errores_por_severidad", {})
        }

        if verbose:
            safe_print(f"NLP Gate: {nlp_validation['gate_pass_count']} aprobados, "
                       f"{nlp_validation['gate_block_count']} bloqueados")

        # Si no hubo ofertas para validar (ej: skip-nlp con IDs sin NLP), skip gate
        if nlp_validation["total"] == 0:
            if verbose:
                safe_print("Sin ofertas NLP para validar - saltando gate")
        else:
            # PASO 1.5b: AUTO-CORRECCION NLP (misma logica que PASO 4 para matching)
            nlp_errores_count = nlp_validation.get("gate_block_count", 0)
            if nlp_errores_count > 0:
                if verbose:
                    safe_print("\n--- PASO 1.5b: AUTO-CORRECCION NLP ---")

                conn_nlp = sqlite3.connect(str(DB_PATH))
                nlp_corrector = AutoCorrector(db_conn=conn_nlp, validator=nlp_validator)
                nlp_correccion = nlp_corrector.procesar_errores(nlp_validation)
                resultados["nlp_correccion"] = nlp_correccion

                auto_corregidos = len(nlp_correccion.get('auto_corregidos', []))
                escalados = len(nlp_correccion.get('escalados_claude', []))

                if verbose:
                    safe_print(f"NLP Auto-corregidos: {auto_corregidos}")
                    safe_print(f"NLP Escalados a Claude: {escalados}")

                # Re-validar ofertas corregidas para ver si ahora pasan el gate
                ids_corregidos = list(set(nlp_correccion.get('auto_corregidos', [])))
                if ids_corregidos:
                    if verbose:
                        safe_print(f"Re-validando {len(ids_corregidos)} ofertas corregidas...")

                    re_validation = nlp_validator.validar_desde_bd(
                        ids=ids_corregidos,
                        persist=True,
                        run_id=current_run_id,
                        update_gate=True
                    )
                    desbloqueados = re_validation.get("gate_pass_count", 0)
                    if verbose and desbloqueados > 0:
                        safe_print(f"Desbloqueadas por correccion: {desbloqueados}")

                    # Actualizar contadores
                    resultados["nlp_validation"]["gate_pass"] = (
                        nlp_validation["gate_pass_count"] + desbloqueados
                    )
                    resultados["nlp_validation"]["gate_block"] = (
                        nlp_validation["gate_block_count"] - desbloqueados
                    )

                    # Agregar IDs desbloqueados a los aprobados
                    if re_validation.get("ids_aprobados"):
                        nlp_validation["ids_aprobados"] = (
                            nlp_validation.get("ids_aprobados", []) + re_validation["ids_aprobados"]
                        )

                # Guardar cola Claude para errores NLP (si hay patrones)
                if nlp_correccion.get('patrones_para_claude'):
                    resultados["nlp_patrones_claude"] = nlp_correccion['patrones_para_claude']
                    nlp_cola_path = nlp_corrector.guardar_cola_claude()
                    if verbose:
                        safe_print(f"NLP Cola Claude guardada: {nlp_cola_path}")

                conn_nlp.close()

            # Solo aprobados entran a matching
            if nlp_validation.get("ids_aprobados"):
                ids_to_process = [str(x) for x in nlp_validation["ids_aprobados"]]
            elif not ids_to_process:
                # Si no teníamos IDs específicos, dejar que matching use limit
                pass
            else:
                # Todos bloqueados
                if verbose:
                    safe_print("WARN: Todas las ofertas bloqueadas por NLP gate. No hay nada para matching.")
                break

        # Guardar extraction report
        if nlp_validation.get("extraction_report"):
            try:
                metrics_dir = Path(__file__).parent.parent / "metrics"
                metrics_dir.mkdir(exist_ok=True)
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M')
                report_path = metrics_dir / f"nlp_extraction_report_{timestamp_str}.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(nlp_validation["extraction_report"], f, indent=2, ensure_ascii=False)
                if verbose:
                    safe_print(f"Extraction report: {report_path}")
            except Exception as e:
                if verbose:
                    safe_print(f"WARN: Error guardando extraction report: {e}")

        # =========================================================
        # PASO 1.6: MULTI-POSITION DETECTION
        # =========================================================
        if not skip_matching and ids_to_process:
            if verbose:
                safe_print("\n" + "=" * 60)
                safe_print("PASO 1.6: MULTI-POSITION DETECTION")
                safe_print("=" * 60)

            try:
                from database.limpiar_titulos import expandir_ofertas_multi_perfil

                mp_result = expandir_ofertas_multi_perfil(
                    ids=ids_to_process,
                    dry_run=False,
                    usar_llm=True
                )
                resultados["multi_position"] = mp_result

                # Agregar IDs de sub-ofertas al lote de matching
                if mp_result.get('ids_nuevos'):
                    ids_to_process.extend(mp_result['ids_nuevos'])

                if verbose:
                    detected = mp_result.get('multi_perfil', 0)
                    nuevos = mp_result.get('nuevos', 0)
                    safe_print(f"Multi-posición: {detected} detectadas, {nuevos} sub-ofertas creadas")

            except Exception as e:
                safe_print(f"Warning: Error en multi-position detection: {e}")

        # PASO 2: Matching (si no se salta)
        if not skip_matching:
            if verbose:
                safe_print("\n" + "=" * 60)
                safe_print("PASO 2: MATCHING")
                safe_print("=" * 60)

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
                    safe_print(f"\nMatching completado: {stats.get('total_processed', 0)} ofertas")

            except Exception as e:
                safe_print(f"Error en matching: {e}")
                return resultados

        # PASO 3: Validacion
        if verbose:
            safe_print("\n" + "=" * 60)
            safe_print("PASO 3: VALIDACION")
            safe_print("=" * 60)

        # Obtener run_id del matching para tracking
        current_run_id = (resultados.get("matching") or {}).get("run_id")

        validacion = validar_ofertas_desde_bd(
            limit=limit,
            ids=ids_to_process,
            run_id=current_run_id
        )
        resultados["validacion"] = validacion

        if verbose:
            safe_print(f"Total validadas: {validacion['total']}")
            safe_print(f"Sin errores: {validacion['sin_errores']}")
            safe_print(f"Con errores: {validacion['con_errores']}")

        if validacion['con_errores'] == 0:
            if verbose:
                safe_print("\nTodas las ofertas pasaron validacion.")
            break  # Salir del loop

        # PASO 4: Auto-correccion
        if verbose:
            safe_print("\n" + "=" * 60)
            safe_print("PASO 4: AUTO-CORRECCION")
            safe_print("=" * 60)

        conn = sqlite3.connect(str(DB_PATH))
        corrector = AutoCorrector(db_conn=conn)
        correccion = corrector.procesar_errores(validacion)
        resultados["correccion"] = correccion

        # Actualizar pipeline_runs con contadores de errores
        if current_run_id:
            errores_detectados = validacion.get('con_errores', 0)
            errores_corregidos = len(correccion.get('auto_corregidos', []))
            errores_escalados = len(correccion.get('escalados_claude', []))

            conn.execute('''
                UPDATE pipeline_runs
                SET errores_detectados = ?,
                    errores_corregidos = ?,
                    errores_escalados = ?
                WHERE run_id = ?
            ''', (errores_detectados, errores_corregidos, errores_escalados, current_run_id))
            conn.commit()

        conn.close()

        if verbose:
            safe_print(f"Auto-corregidos: {len(correccion['auto_corregidos'])}")
            safe_print(f"Escalados a Claude: {len(correccion['escalados_claude'])}")

        # PASO 4.5: Auto-transición pendiente → validado_claude
        if ids_to_process:
            if verbose:
                safe_print("\n" + "=" * 60)
                safe_print("PASO 4.5: AUTO-TRANSICION")
                safe_print("=" * 60)

            try:
                transicion = auto_transicionar_pendientes(ids_to_process, verbose=verbose)
                resultados["transicion"] = transicion
                if verbose:
                    safe_print(f"Transicionadas: {transicion['transicionadas']}/{transicion['evaluadas']}")
                    if transicion['bloqueadas'] > 0:
                        safe_print(f"Bloqueadas: {transicion['bloqueadas']} (errores bloqueantes)")
            except Exception as e:
                safe_print(f"Error en auto-transición: {e}")

        # PASO 5: Verificar errores NLP para reprocesar
        ids_nlp_errors = get_ids_with_nlp_errors()

        # Filtrar solo los que estamos procesando
        if ids_to_process:
            ids_to_process_set = set(str(x) for x in ids_to_process)
            ids_nlp_errors = [x for x in ids_nlp_errors if str(x) in ids_to_process_set]

        if ids_nlp_errors and nlp_iteration < max_nlp_iterations and not skip_nlp:
            if verbose:
                safe_print(f"\n{len(ids_nlp_errors)} ofertas con errores NLP - reprocesando...")

            # Reprocesar NLP para estos IDs
            try:
                nlp_result = run_nlp_for_ids(ids_nlp_errors, verbose=verbose)
                if verbose:
                    safe_print(f"NLP reprocesado: {nlp_result.get('processed', 0)} ofertas")

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
                safe_print(f"Error reprocesando NLP: {e}")
                # Continuar sin reprocesar

        # Si llegamos aqui, no hay mas errores NLP para reprocesar
        break

    # === FIN DEL LOOP ===

    # PASO 6: Generar reporte para Claude (si hay errores)
    if resultados.get("correccion") and resultados["correccion"].get('patrones_para_claude'):
        if verbose:
            safe_print("\n" + "=" * 60)
            safe_print("PASO 6: PATRONES PARA CLAUDE")
            safe_print("=" * 60)

        resultados["patrones_claude"] = resultados["correccion"]['patrones_para_claude']

        conn = sqlite3.connect(str(DB_PATH))
        corrector = AutoCorrector(db_conn=conn)
        output_path = corrector.guardar_cola_claude()
        conn.close()

        if verbose:
            safe_print(f"Reporte guardado en: {output_path}")

    # Resumen final
    if verbose:
        safe_print("\n" + "=" * 60)
        safe_print("RESUMEN FINAL")
        safe_print("=" * 60)

        if resultados.get("validacion"):
            total = resultados["validacion"]['total']
            ok = resultados["validacion"]['sin_errores']
            if resultados.get("correccion"):
                ok += len(resultados["correccion"].get('auto_corregidos', []))

            safe_print(f"Total ofertas: {total}")
            safe_print(f"Listas para dashboard: {ok} ({100*ok/total:.1f}%)" if total > 0 else "")
            safe_print(f"Iteraciones NLP: {nlp_iteration}")

    # PASO 7: Export Excel para validacion humana
    if verbose:
        safe_print("\n" + "=" * 60)
        safe_print("PASO 7: EXPORT EXCEL")
        safe_print("=" * 60)

    try:
        from scripts.exports.export_validation_excel import export_validation

        excel_path = export_validation(
            etapa="completo",
            offer_ids=ids_to_process if ids_to_process else None,
            limit=limit if not ids_to_process else None
        )
        resultados["excel_export"] = str(excel_path)

        if verbose:
            safe_print(f"Excel exportado: {excel_path}")

    except Exception as e:
        safe_print(f"Warning: Error exportando Excel: {e}")
        resultados["excel_export"] = f"Error: {e}"

    # PASO 8: Sincronizar learnings.yaml
    if verbose:
        safe_print("\n" + "=" * 60)
        safe_print("PASO 8: SYNC LEARNINGS.YAML")
        safe_print("=" * 60)

    try:
        sync_learnings_yaml(verbose=verbose)
        resultados["learnings_sync"] = True
    except Exception as e:
        safe_print(f"Warning: Error sincronizando learnings.yaml: {e}")
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

    # Nuevos argumentos para sistema de prioridad
    parser.add_argument("--no-priority", action="store_true", help="Desactivar seleccion por prioridad")
    parser.add_argument("--force-new-batch", action="store_true", help="Forzar nuevo lote ignorando errores pendientes")

    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else None

    # === SISTEMA DE PRIORIDAD ===
    if args.limit and not args.ids and not args.no_priority:
        from scripts.get_priority_batch import (
            get_connection as get_priority_conn,
            refresh_priorities,
            get_next_batch_from_db,
            mark_batch_as_processing,
            mark_batch_as_completed,
            check_pending_errors_block
        )

        conn = get_priority_conn()

        # 1. Verificar si hay errores bloqueantes
        block_info = check_pending_errors_block(conn)
        if block_info['blocked'] and not args.force_new_batch:
            safe_print("=" * 60)
            safe_print(f"[BLOQUEADO] Lote {block_info['lote']} tiene {block_info['errores']} errores sin resolver")
            safe_print("=" * 60)
            safe_print(f"\nIDs con error: {','.join(block_info['ids'][:10])}")
            safe_print(f"\nOpciones:")
            safe_print(f"  1. Resolver errores: --ids {','.join(block_info['ids'])}")
            safe_print(f"  2. Forzar nuevo lote: --force-new-batch")
            conn.close()
            sys.exit(1)

        # 2. Recalcular prioridades
        if not args.quiet:
            safe_print("Recalculando prioridades...")
        result = refresh_priorities(conn)
        if not args.quiet:
            safe_print(f"  Nuevas: {result['nuevas']}, Actualizadas: {result['actualizadas']}")

        # 3. Obtener lote ordenado por prioridad
        batch = get_next_batch_from_db(conn, size=args.limit)
        if not batch:
            safe_print("No hay ofertas pendientes de procesar.")
            conn.close()
            sys.exit(0)

        ids = [str(o['id_oferta']) for o in batch]
        lote_id = f"lote_{datetime.now().strftime('%Y%m%d_%H%M')}"

        # 4. Marcar como en_proceso
        mark_batch_as_processing(conn, ids, lote_id)
        if not args.quiet:
            safe_print(f"Lote {lote_id}: {len(ids)} ofertas (score {batch[0]['score_total']:.3f} - {batch[-1]['score_total']:.3f})")

        conn.close()

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

    # === MARCAR LOTE COMO COMPLETADO ===
    if args.limit and not args.ids and not args.no_priority:
        from scripts.get_priority_batch import (
            get_connection as get_priority_conn,
            mark_batch_as_completed
        )
        conn = get_priority_conn()
        # ids ya está definido desde el sistema de prioridad
        mark_batch_as_completed(conn, ids)
        if not args.quiet:
            safe_print(f"\nLote marcado como procesado: {len(ids)} ofertas")
        conn.close()

    # Exit code basado en resultado
    if resultados.get("patrones_claude"):
        sys.exit(1)  # Hay errores que requieren atencion
    sys.exit(0)


if __name__ == "__main__":
    main()
