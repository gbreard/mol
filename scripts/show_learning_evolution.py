#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Show Learning Evolution v1.0 - Visualizar evolución del aprendizaje
====================================================================

Muestra timeline de cómo el sistema ha aprendido a lo largo de los runs.

Uso:
    python scripts/show_learning_evolution.py
    python scripts/show_learning_evolution.py --format json
    python scripts/show_learning_evolution.py --daily
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Paths
BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"


def get_conn() -> sqlite3.Connection:
    """Obtiene conexión a la BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_evolution_timeline() -> List[Dict]:
    """Obtiene timeline de evolución del aprendizaje."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT
            run_id,
            date(timestamp) as fecha,
            time(timestamp) as hora,
            matching_version,
            source,
            ofertas_count,
            reglas_negocio_count,
            reglas_validacion_count,
            sinonimos_count,
            delta_reglas,
            errores_detectados,
            errores_corregidos,
            metricas_precision
        FROM pipeline_runs
        ORDER BY timestamp ASC
    ''')

    timeline = []
    for row in cur.fetchall():
        timeline.append({
            "run_id": row["run_id"],
            "fecha": row["fecha"],
            "hora": row["hora"],
            "version": row["matching_version"],
            "source": row["source"],
            "ofertas": row["ofertas_count"] or 0,
            "reglas": row["reglas_negocio_count"] or 0,
            "validacion": row["reglas_validacion_count"] or 0,
            "sinonimos": row["sinonimos_count"] or 0,
            "delta": row["delta_reglas"] or 0,
            "errores_detectados": row["errores_detectados"] or 0,
            "errores_corregidos": row["errores_corregidos"] or 0,
            "precision": row["metricas_precision"]
        })

    conn.close()
    return timeline


def get_daily_summary() -> List[Dict]:
    """Obtiene resumen diario de aprendizaje."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT
            date(timestamp) as fecha,
            COUNT(*) as runs,
            SUM(ofertas_count) as ofertas_total,
            MIN(reglas_negocio_count) as reglas_inicio,
            MAX(reglas_negocio_count) as reglas_fin,
            SUM(delta_reglas) as reglas_agregadas,
            SUM(errores_corregidos) as errores_corregidos,
            MAX(metricas_precision) as mejor_precision
        FROM pipeline_runs
        GROUP BY date(timestamp)
        ORDER BY fecha ASC
    ''')

    summary = []
    for row in cur.fetchall():
        summary.append({
            "fecha": row["fecha"],
            "runs": row["runs"],
            "ofertas": row["ofertas_total"] or 0,
            "reglas_inicio": row["reglas_inicio"] or 0,
            "reglas_fin": row["reglas_fin"] or 0,
            "reglas_agregadas": row["reglas_agregadas"] or 0,
            "errores_corregidos": row["errores_corregidos"] or 0,
            "precision": row["mejor_precision"]
        })

    conn.close()
    return summary


def get_learning_history() -> List[Dict]:
    """Obtiene historial de eventos de aprendizaje."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT *
        FROM learning_history
        ORDER BY timestamp DESC
        LIMIT 50
    ''')

    history = []
    for row in cur.fetchall():
        history.append(dict(row))

    conn.close()
    return history


def print_timeline_ascii(timeline: List[Dict]):
    """Imprime timeline en formato ASCII."""
    print("\n" + "=" * 80)
    print("EVOLUCION DEL APRENDIZAJE - Timeline")
    print("=" * 80)

    if not timeline:
        print("No hay datos de runs.")
        return

    # Calcular totales
    total_reglas_agregadas = sum(t["delta"] for t in timeline if t["delta"] > 0)
    total_errores_corregidos = sum(t["errores_corregidos"] for t in timeline)
    reglas_actuales = timeline[-1]["reglas"] if timeline else 0

    print(f"\nResumen:")
    print(f"  Total runs: {len(timeline)}")
    print(f"  Reglas actuales: {reglas_actuales}")
    print(f"  Reglas agregadas: +{total_reglas_agregadas}")
    print(f"  Errores corregidos: {total_errores_corregidos}")

    print(f"\n{'Fecha':<12} {'Hora':<6} {'Ver':<8} {'Reglas':>7} {'Delta':>7} {'Ofertas':>8} {'Source':<25}")
    print("-" * 80)

    current_date = None
    for t in timeline:
        # Separador por día
        if t["fecha"] != current_date:
            if current_date is not None:
                print("-" * 80)
            current_date = t["fecha"]

        delta_str = f"+{t['delta']}" if t["delta"] > 0 else str(t["delta"]) if t["delta"] < 0 else ""
        prec = f"{t['precision']:.0%}" if t["precision"] else ""

        print(f"{t['fecha']:<12} {t['hora'][:5]:<6} {t['version']:<8} {t['reglas']:>7} {delta_str:>7} {t['ofertas']:>8} {t['source'][:25]:<25}")

    print("=" * 80)


def print_daily_summary(summary: List[Dict]):
    """Imprime resumen diario."""
    print("\n" + "=" * 70)
    print("EVOLUCION DEL APRENDIZAJE - Resumen Diario")
    print("=" * 70)

    if not summary:
        print("No hay datos.")
        return

    print(f"\n{'Fecha':<12} {'Runs':>6} {'Ofertas':>8} {'Reglas':>10} {'+Reglas':>8} {'Errores':>8}")
    print("-" * 70)

    for s in summary:
        reglas = f"{s['reglas_inicio']}->{s['reglas_fin']}"
        agregadas = f"+{s['reglas_agregadas']}" if s["reglas_agregadas"] > 0 else ""
        corregidos = str(s["errores_corregidos"]) if s["errores_corregidos"] > 0 else ""

        print(f"{s['fecha']:<12} {s['runs']:>6} {s['ofertas']:>8} {reglas:>10} {agregadas:>8} {corregidos:>8}")

    # Totales
    total_runs = sum(s["runs"] for s in summary)
    total_ofertas = sum(s["ofertas"] for s in summary)
    total_reglas = sum(s["reglas_agregadas"] for s in summary)
    total_errores = sum(s["errores_corregidos"] for s in summary)

    print("-" * 70)
    print(f"{'TOTAL':<12} {total_runs:>6} {total_ofertas:>8} {'':>10} {'+'+str(total_reglas):>8} {total_errores:>8}")
    print("=" * 70)


def print_ascii_chart(timeline: List[Dict]):
    """Imprime gráfico ASCII de evolución de reglas."""
    if not timeline:
        return

    print("\n" + "=" * 60)
    print("GRAFICO: Evolucion de Reglas de Negocio")
    print("=" * 60)

    max_reglas = max(t["reglas"] for t in timeline)
    width = 40

    # Agrupar por día
    by_date = {}
    for t in timeline:
        if t["fecha"] not in by_date:
            by_date[t["fecha"]] = t["reglas"]
        by_date[t["fecha"]] = max(by_date[t["fecha"]], t["reglas"])

    for fecha, reglas in by_date.items():
        bar_len = int((reglas / max_reglas) * width) if max_reglas > 0 else 0
        bar = "#" * bar_len
        print(f"{fecha} |{bar:<{width}}| {reglas}")

    print("=" * 60)


def get_batch_summary() -> List[Dict]:
    """Obtiene resumen de lotes de aprendizaje."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT
            lote_id,
            nombre,
            estado,
            ofertas_total,
            reglas_inicio,
            reglas_fin,
            reglas_agregadas,
            tasa_aprendizaje,
            cobertura_estimada,
            fecha_inicio,
            fecha_fin
        FROM learning_batches
        ORDER BY fecha_inicio ASC
    ''')

    batches = []
    for row in cur.fetchall():
        batches.append({
            "lote_id": row[0],
            "nombre": row[1],
            "estado": row[2],
            "ofertas": row[3] or 0,
            "reglas_inicio": row[4] or 0,
            "reglas_fin": row[5] or 0,
            "reglas_agregadas": row[6] or 0,
            "tasa": row[7] or 0,
            "cobertura": row[8] or 0,
            "fecha_inicio": row[9],
            "fecha_fin": row[10]
        })

    conn.close()
    return batches


def print_batch_summary(batches: List[Dict]):
    """Imprime resumen de lotes con curva de convergencia."""
    print("\n" + "=" * 90)
    print("EVOLUCION DEL APRENDIZAJE POR LOTES")
    print("=" * 90)

    if not batches:
        print("No hay lotes registrados.")
        return

    # Leyenda de estados
    print("\nEstados: optimizacion -> listo_validacion -> en_validacion -> validado")
    print("         (rechazado vuelve a optimizacion)")

    # Tabla de lotes
    print(f"\n{'Lote':<25} {'Estado':<18} {'Ofertas':>7} {'Reglas':>10} {'Tasa':>7}")
    print("-" * 90)

    total_ofertas = 0
    total_reglas = 0

    # Iconos de estado
    estado_icons = {
        "optimizacion": "[OPT]",
        "listo_validacion": "[LISTO]",
        "en_validacion": "[HUMAN]",
        "validado": "[OK]",
        "rechazado": "[RECH]",
        "completado": "[COMP]"  # legacy
    }

    for b in batches:
        reglas_str = f"{b['reglas_inicio']}->{b['reglas_fin']}"
        tasa_str = f"{b['tasa']:.1f}%" if b['tasa'] else "-"
        estado = b.get('estado', 'desconocido')
        icon = estado_icons.get(estado, "[?]")

        print(f"{b['nombre'][:25]:<25} {icon + ' ' + estado:<18} {b['ofertas']:>7} {reglas_str:>10} {tasa_str:>7}")

        total_ofertas += b['ofertas']
        total_reglas += b['reglas_agregadas']

    print("-" * 90)
    print(f"{'TOTAL':<25} {'':<18} {total_ofertas:>7} {'+' + str(total_reglas):>10}")

    # Grafico de convergencia
    print("\n" + "=" * 90)
    print("CURVA DE CONVERGENCIA (Tasa de Aprendizaje)")
    print("=" * 90)
    print("\nTasa = Reglas nuevas / Ofertas del lote")
    print("Menor tasa = Sistema mas maduro (umbral convergencia: 5%)\n")

    max_tasa = max(b['tasa'] for b in batches) if batches else 1
    width = 40

    for b in batches:
        bar_len = int((b['tasa'] / max_tasa) * width) if max_tasa > 0 else 0
        bar = "#" * bar_len
        estado = b.get('estado', '')
        if b['tasa'] < 5:
            trend = "<< CONVERGIDO"
        elif b['tasa'] < 10:
            trend = "< Convergiendo"
        else:
            trend = ""
        print(f"{b['nombre'][:20]:<20} |{bar:<{width}}| {b['tasa']:>5.1f}% {trend}")

    # Flujo actual
    print("\n" + "-" * 90)
    print("FLUJO DE TRABAJO:")
    print("  1. OPTIMIZACION: Claude itera (procesa, detecta errores, crea reglas)")
    print("  2. CONVERGENCIA: Cuando tasa < 5%, listo para validacion humana")
    print("  3. VALIDACION: Humano revisa en Google Sheets")
    print("  4. RESULTADO: Validado (OK) o Rechazado (volver a 1)")

    # Estado actual
    print("\n" + "-" * 90)
    if batches:
        ultimo = batches[-1]
        ultima_tasa = ultimo.get('tasa', 0)
        ultimo_estado = ultimo.get('estado', 'desconocido')

        print(f"ULTIMO LOTE: {ultimo.get('nombre', 'N/A')}")
        print(f"  Estado: {ultimo_estado}")
        print(f"  Tasa: {ultima_tasa:.1f}%")

        if ultimo_estado == 'validado':
            print("  >> Sistema VALIDADO - Listo para produccion")
        elif ultimo_estado == 'en_validacion':
            print("  >> Esperando feedback humano...")
        elif ultimo_estado == 'listo_validacion':
            print("  >> Listo para enviar a validacion humana")
        elif ultimo_estado == 'optimizacion':
            if ultima_tasa < 5:
                print("  >> Puede pasar a validacion (tasa < 5%)")
            else:
                print(f"  >> Continuar optimizando (objetivo: tasa < 5%)")
        elif ultimo_estado == 'rechazado':
            print("  >> Reabrir y continuar optimizando")

    print("=" * 90)


def main():
    parser = argparse.ArgumentParser(
        description="Mostrar evolución del aprendizaje del sistema"
    )
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Formato de salida")
    parser.add_argument("--daily", action="store_true",
                        help="Mostrar resumen diario")
    parser.add_argument("--batches", action="store_true",
                        help="Mostrar resumen por lotes con convergencia")
    parser.add_argument("--chart", action="store_true",
                        help="Mostrar grafico ASCII")
    parser.add_argument("--history", action="store_true",
                        help="Mostrar historial de eventos")

    args = parser.parse_args()

    if args.format == "json":
        if args.daily:
            data = get_daily_summary()
        elif args.batches:
            data = get_batch_summary()
        elif args.history:
            data = get_learning_history()
        else:
            data = get_evolution_timeline()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        if args.batches:
            print_batch_summary(get_batch_summary())
        elif args.daily:
            print_daily_summary(get_daily_summary())
        elif args.history:
            history = get_learning_history()
            print("\nHistorial de Aprendizaje:")
            for h in history[:20]:
                print(f"  {h.get('timestamp', 'N/A')[:16]}: {h.get('evento_tipo', 'N/A')} - {h.get('descripcion', 'N/A')}")
        else:
            timeline = get_evolution_timeline()
            print_timeline_ascii(timeline)

            if args.chart:
                print_ascii_chart(timeline)


if __name__ == "__main__":
    main()
