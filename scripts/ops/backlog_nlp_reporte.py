#!/usr/bin/env python3
"""
backlog_nlp_reporte.py — reporte corto de progreso de la corrida del backlog NLP.

Lee el checkpoint.jsonl que deja cada tanda y resume: cuanto se comio, a que
ritmo, cuanto falta y la proyeccion. Con --final agrega el desglose por tanda.

Uso: python3 scripts/ops/backlog_nlp_reporte.py --rundir <dir> [--final]
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rundir", required=True)
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args()

    ckpt = Path(args.rundir) / "checkpoint.jsonl"
    if not ckpt.exists():
        print("(sin tandas registradas todavia)")
        return

    filas = [json.loads(l) for l in ckpt.read_text().splitlines() if l.strip()]
    if not filas:
        print("(sin tandas registradas todavia)")
        return

    total_proc = sum(f["procesadas"] for f in filas)
    total_seg = sum(f["duracion_seg"] for f in filas)
    inicial = filas[0]["remanente_antes"]
    restante = filas[-1]["remanente_despues"]
    ritmo = total_proc / total_seg * 3600 if total_seg else 0
    horas_falta = restante / ritmo if ritmo else float("inf")
    u = filas[-1]

    print(f"  PROGRESO: {inicial - restante}/{inicial} comidas "
          f"({(inicial - restante) / inicial * 100:.1f}%) | quedan {restante}")
    print(f"  ULTIMA TANDA {u['tanda']}: {u['procesadas']}/{u['seleccionadas']} en "
          f"{u['duracion_seg']/60:.0f} min ({u['ofertas_por_hora']}/h) | "
          f"avisos {u['fecha_mas_nueva']} .. {u['fecha_mas_vieja']}")
    print(f"  RITMO ACUMULADO: {ritmo:.0f} ofertas/h en {len(filas)} tandas "
          f"({total_seg/3600:.1f} h) | faltan ~{horas_falta:.0f} h "
          f"(~{horas_falta/24:.1f} dias de corrida)")

    if args.final:
        print("\n  Tanda | procesadas/sel |   min |   of/h | remanente | avisos hasta")
        for f in filas:
            print(f"  {f['tanda']:5d} | {f['procesadas']:6d}/{f['seleccionadas']:<7d} | "
                  f"{f['duracion_seg']/60:5.0f} | {f['ofertas_por_hora'] or 0:6.0f} | "
                  f"{f['remanente_despues']:9d} | {(f['fecha_mas_vieja'] or '')[:10]}")
        fallidas = sum(f["seleccionadas"] - f["procesadas"] for f in filas)
        print(f"\n  No procesadas dentro de las tandas (reintentan solas en la "
              f"siguiente seleccion): {fallidas}")


if __name__ == "__main__":
    main()
