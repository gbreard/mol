"""
Pipeline integrado: Matching + Validación Autónoma

Este script ejecuta el flujo completo:
1. Matching (match_ofertas_v3.py)
2. Auto-validación (auto_validator.py) - persiste errores en BD
3. Auto-corrección (auto_corrector.py) - actualiza estado en BD
4. Reporte de patrones para Claude
5. (Opcional) Export Markdown para feedback humano

Uso:
    python scripts/run_validated_pipeline.py --limit 100
    python scripts/run_validated_pipeline.py --ids 123,456,789
    python scripts/run_validated_pipeline.py --only-pending
    python scripts/run_validated_pipeline.py --limit 50 --export-markdown

Version: 2.0
Fecha: 2026-01-16
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from database.match_ofertas_v3 import run_matching_pipeline
from database.auto_validator import AutoValidator, validar_ofertas_desde_bd
from database.auto_corrector import AutoCorrector, procesar_validacion_completa


def run_full_pipeline(
    limit: int = None,
    ids: list = None,
    only_pending: bool = False,
    skip_matching: bool = False,
    export_markdown: bool = False,
    verbose: bool = True
) -> dict:
    """
    Ejecuta el pipeline completo con validación.

    Args:
        limit: Limite de ofertas
        ids: IDs específicos
        only_pending: Solo ofertas pendientes de matching
        skip_matching: Saltar matching, solo validar
        export_markdown: Exportar Markdown para feedback humano
        verbose: Mostrar progreso

    Returns:
        Resultados del pipeline
    """
    resultados = {
        "timestamp": datetime.now().isoformat(),
        "matching": None,
        "validacion": None,
        "correccion": None,
        "patrones_claude": None,
        "markdown_export": None
    }

    # PASO 1: Matching (si no se salta)
    if not skip_matching:
        if verbose:
            print("=" * 60)
            print("PASO 1: MATCHING")
            print("=" * 60)

        try:
            stats = run_matching_pipeline(
                offer_ids=ids,
                limit=limit,
                only_pending=only_pending,
                verbose=verbose
            )
            resultados["matching"] = stats

            # Obtener IDs procesados para validar
            if stats.get("processed_ids"):
                ids = stats["processed_ids"]

            if verbose:
                print(f"\nMatching completado: {stats.get('total_processed', 0)} ofertas")

        except Exception as e:
            print(f"Error en matching: {e}")
            return resultados

    # PASO 2: Validación
    if verbose:
        print("\n" + "=" * 60)
        print("PASO 2: AUTO-VALIDACIÓN")
        print("=" * 60)

    validacion = validar_ofertas_desde_bd(limit=limit, ids=ids)
    resultados["validacion"] = validacion

    if verbose:
        print(f"Total validadas: {validacion['total']}")
        print(f"Sin errores: {validacion['sin_errores']}")
        print(f"Con errores: {validacion['con_errores']}")

    if validacion['con_errores'] == 0:
        if verbose:
            print("\nTodas las ofertas pasaron validación.")
            print("Estado: LISTO PARA DASHBOARD")
        return resultados

    # PASO 3: Auto-corrección
    if verbose:
        print("\n" + "=" * 60)
        print("PASO 3: AUTO-CORRECCIÓN")
        print("=" * 60)

    # Procesar correcciones
    db_path = str(Path(__file__).parent.parent / "database" / "bumeran_scraping.db")

    import sqlite3
    conn = sqlite3.connect(db_path)
    corrector = AutoCorrector(db_conn=conn)

    correccion = corrector.procesar_errores(validacion)
    resultados["correccion"] = correccion

    conn.close()

    if verbose:
        print(f"Auto-corregidos: {len(correccion['auto_corregidos'])}")
        print(f"Escalados a Claude: {len(correccion['escalados_claude'])}")
        print(f"Sin acción: {len(correccion['sin_accion'])}")

    # PASO 4: Generar reporte para Claude (si hay errores)
    if correccion['patrones_para_claude']:
        if verbose:
            print("\n" + "=" * 60)
            print("PASO 4: PATRONES PARA CLAUDE")
            print("=" * 60)

        resultados["patrones_claude"] = correccion['patrones_para_claude']

        # Guardar reporte
        output_path = corrector.guardar_cola_claude()
        if verbose:
            print(f"\nReporte guardado en: {output_path}")
            print("\n" + corrector.obtener_reporte_claude())

    # Resumen final
    if verbose:
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)

        total = validacion['total']
        ok = validacion['sin_errores'] + len(correccion['auto_corregidos'])
        pendiente_claude = len(correccion['escalados_claude'])

        print(f"Total ofertas: {total}")
        print(f"Listas para dashboard: {ok} ({100*ok/total:.1f}%)")
        print(f"Requieren regla nueva: {pendiente_claude} ({100*pendiente_claude/total:.1f}%)")

        if pendiente_claude > 0:
            print("\nACCIÓN REQUERIDA: Revisar patrones y crear reglas en config/*.json")
        else:
            print("\nEstado: LISTO PARA DASHBOARD")

    # PASO 5: Export Markdown (opcional)
    if export_markdown:
        if verbose:
            print("\n" + "=" * 60)
            print("PASO 5: EXPORT MARKDOWN")
            print("=" * 60)

        try:
            from scripts.exports.export_validation_markdown import export_validation_markdown

            # Usar los IDs procesados o un límite
            export_ids = ids if ids else None
            export_limit = limit if not ids else None

            md_path = export_validation_markdown(
                offer_ids=export_ids,
                limit=export_limit,
                output_dir="validation"
            )
            resultados["markdown_export"] = str(md_path)

            if verbose:
                print(f"Markdown exportado: {md_path}")
                print("\nPara feedback humano:")
                print("  1. git add validation/")
                print("  2. git commit -m 'validation: feedback pendiente'")
                print("  3. git push")
                print("  4. Editar en GitHub (columnas resultado, isco_correcto, comentario)")

        except Exception as e:
            print(f"Error exportando Markdown: {e}")
            resultados["markdown_export"] = f"Error: {e}"

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Pipeline integrado con validación")
    parser.add_argument("--limit", type=int, help="Limite de ofertas")
    parser.add_argument("--ids", type=str, help="IDs separados por coma")
    parser.add_argument("--only-pending", action="store_true", help="Solo ofertas pendientes")
    parser.add_argument("--skip-matching", action="store_true", help="Saltar matching, solo validar")
    parser.add_argument("--export-markdown", action="store_true", help="Exportar Markdown para feedback humano")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")

    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else None

    resultados = run_full_pipeline(
        limit=args.limit,
        ids=ids,
        only_pending=args.only_pending,
        skip_matching=args.skip_matching,
        export_markdown=args.export_markdown,
        verbose=not args.quiet
    )

    # Exit code basado en resultado
    if resultados.get("patrones_claude"):
        sys.exit(1)  # Hay errores que requieren atención
    sys.exit(0)


if __name__ == "__main__":
    main()
