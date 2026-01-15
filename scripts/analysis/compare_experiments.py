#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare Experiments - Comparador de Experimentos MOL
=====================================================

VERSION: 1.0.0
FECHA: 2025-12-07
ISSUE: MOL-48

Herramienta CLI para comparar resultados de experimentos guardados.

Uso:
    # Comparar dos experimentos
    python compare_experiments.py baseline_v83 candidate_v84

    # Listar experimentos disponibles
    python compare_experiments.py --list

    # Ver historial del gold set
    python compare_experiments.py --gold-set-history

    # Ver ultimo run del gold set
    python compare_experiments.py --last-run
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

# Import experiment logger
try:
    from experiment_logger import ExperimentLogger, METRICS_DIR
except ImportError:
    # Si se ejecuta desde otro directorio
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from experiment_logger import ExperimentLogger, METRICS_DIR


def list_experiments(logger: ExperimentLogger, tag: str = None):
    """Lista todos los experimentos disponibles"""
    experiments = logger.list_experiments(tag=tag)

    if not experiments:
        print("No hay experimentos guardados.")
        print("Ejecuta test_gold_set_manual.py o usa logger.log_experiment() para crear uno.")
        return

    print("\n" + "=" * 70)
    print("EXPERIMENTOS DISPONIBLES")
    print("=" * 70)

    for exp in experiments:
        print(f"\n  {exp['name']}")
        print(f"    ID:        {exp['id']}")
        print(f"    Fecha:     {exp['timestamp'][:19]}")
        if exp.get('tags'):
            print(f"    Tags:      {', '.join(exp['tags'])}")
        print(f"    Metricas:")
        for metric, value in exp.get('metrics', {}).items():
            if isinstance(value, float):
                print(f"      - {metric}: {value:.4f}")
            else:
                print(f"      - {metric}: {value}")

    print("\n" + "=" * 70)
    print(f"Total: {len(experiments)} experimentos")


def show_gold_set_history(limit: int = 10):
    """Muestra el historial de ejecuciones del gold set"""
    history_file = METRICS_DIR / "gold_set_history.json"

    if not history_file.exists():
        print("No hay historial del gold set.")
        print("Ejecuta test_gold_set_manual.py para crear el primer registro.")
        return

    try:
        history = json.loads(history_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Error leyendo historial del gold set.")
        return

    if not history:
        print("Historial vacio.")
        return

    # Ordenar por timestamp descendente
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    print("\n" + "=" * 70)
    print("HISTORIAL GOLD SET")
    print("=" * 70)

    for run in history[:limit]:
        print(f"\n  {run['timestamp'][:19]}")
        print(f"    Version:   {run.get('version', 'unknown')}")
        print(f"    Precision: {run['precision']:.1f}%")
        print(f"    Correctos: {run['correct']}/{run['total']}")
        if run.get('errors_by_type'):
            print(f"    Errores:")
            for tipo, count in run['errors_by_type'].items():
                print(f"      - {tipo}: {count}")
        if run.get('notes'):
            print(f"    Notas:     {run['notes']}")

    print("\n" + "=" * 70)
    print(f"Mostrando ultimos {min(limit, len(history))} de {len(history)} runs")


def show_last_run():
    """Muestra el ultimo run del gold set"""
    history_file = METRICS_DIR / "gold_set_history.json"

    if not history_file.exists():
        print("No hay historial del gold set.")
        return

    try:
        history = json.loads(history_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Error leyendo historial del gold set.")
        return

    if not history:
        print("Historial vacio.")
        return

    # Ultimo run
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    run = history[0]

    print("\n" + "=" * 70)
    print("ULTIMO RUN GOLD SET")
    print("=" * 70)
    print(f"  Fecha:     {run['timestamp'][:19]}")
    print(f"  Version:   {run.get('version', 'unknown')}")
    print(f"  Precision: {run['precision']:.1f}%")
    print(f"  Correctos: {run['correct']}/{run['total']}")
    print(f"  Incorrectos: {run['incorrect']}")

    if run.get('errors_by_type'):
        print(f"\n  Errores por tipo:")
        for tipo, count in sorted(run['errors_by_type'].items(), key=lambda x: -x[1]):
            print(f"    - {tipo}: {count}")

    if run.get('notes'):
        print(f"\n  Notas: {run['notes']}")

    print("=" * 70)


def show_timing_stats():
    """Muestra estadisticas de timing agregadas"""
    timing_file = METRICS_DIR / "timing_logs.jsonl"

    if not timing_file.exists():
        print("No hay logs de timing.")
        return

    # Leer todos los logs
    timings = {}
    with open(timing_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                component = entry.get('component', 'unknown')
                duration = entry.get('duration_ms', 0)

                if component not in timings:
                    timings[component] = []
                timings[component].append(duration)
            except json.JSONDecodeError:
                continue

    if not timings:
        print("No hay datos de timing.")
        return

    print("\n" + "=" * 70)
    print("ESTADISTICAS DE TIMING")
    print("=" * 70)

    for component, values in sorted(timings.items()):
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        total = sum(values)

        print(f"\n  {component}:")
        print(f"    Count:  {len(values)}")
        print(f"    Avg:    {avg:.1f}ms")
        print(f"    Min:    {min_val:.1f}ms")
        print(f"    Max:    {max_val:.1f}ms")
        print(f"    Total:  {total:.1f}ms ({total/1000:.1f}s)")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Comparador de experimentos MOL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python compare_experiments.py baseline_v83 candidate_v84
  python compare_experiments.py --list
  python compare_experiments.py --list --tag matching
  python compare_experiments.py --gold-set-history
  python compare_experiments.py --last-run
  python compare_experiments.py --timing
        """
    )

    parser.add_argument("experiments", nargs='*',
                        help="Nombres de experimentos a comparar (2 requeridos)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="Listar experimentos disponibles")
    parser.add_argument("--tag", "-t", type=str,
                        help="Filtrar por tag (con --list)")
    parser.add_argument("--gold-set-history", "-g", action="store_true",
                        help="Mostrar historial del gold set")
    parser.add_argument("--last-run", action="store_true",
                        help="Mostrar ultimo run del gold set")
    parser.add_argument("--timing", action="store_true",
                        help="Mostrar estadisticas de timing")
    parser.add_argument("--limit", type=int, default=10,
                        help="Limite de items a mostrar (default: 10)")

    args = parser.parse_args()

    logger = ExperimentLogger()

    # Opciones de listado
    if args.list:
        list_experiments(logger, tag=args.tag)
        return

    if args.gold_set_history:
        show_gold_set_history(limit=args.limit)
        return

    if args.last_run:
        show_last_run()
        return

    if args.timing:
        show_timing_stats()
        return

    # Comparacion de experimentos
    if len(args.experiments) != 2:
        parser.print_help()
        print("\nError: Se requieren exactamente 2 experimentos para comparar.")
        print("Usa --list para ver experimentos disponibles.")
        return

    name_a, name_b = args.experiments

    try:
        logger.compare_experiments(name_a, name_b)
    except ValueError as e:
        print(f"Error: {e}")
        print("Usa --list para ver experimentos disponibles.")


if __name__ == "__main__":
    main()
