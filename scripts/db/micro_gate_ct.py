#!/usr/bin/env python3
"""
MICRO-GATE CT (mini-spec SPEC_ct_verificacion_busqueda.md §3) — SOLO LECTURA.

Clasifica una muestra ALEATORIA de la franja [umbral, 2×umbral] de CT presunta_baja
por la vía NUEVA (presencia en el buscador) y contrasta contra la curva de
supervivencia medida: la franja DEBE dar ~20-25% vivas. Si da muy por encima
(tipo 86%, el error del intento 04-09) o muy por debajo (~5%), el discriminador
está mal y NO se activa.

NO escribe en BD. NO activa el cron. Lock-aware. Circuit-breaker ante bloqueo.
"""
import sys, argparse, time, random
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))
import database.verificador_bajas as vb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150, help="tamaño de la muestra")
    ap.add_argument("--umbral", type=int, default=63, help="umbral presunta_baja CT (días)")
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=20261008)
    args = ap.parse_args()

    v = vb.VerificadorBajas()
    if v.lock_tomado():
        print("ABORTADO: lock de scraping presente — no corro con scraping en curso.")
        return
    v.connect()
    v.delay_ct = args.delay

    lo, hi = args.umbral, 2 * args.umbral
    rows = v.conn.execute(f"""
        SELECT id_oferta, titulo, url_oferta,
               CAST(julianday('now') - julianday(fecha_ultimo_visto) AS INT) AS dias
        FROM ofertas
        WHERE portal='computrabajo' AND estado_ciclo='presunta_baja'
          AND julianday('now') - julianday(fecha_ultimo_visto) BETWEEN ? AND ?
    """, (lo, hi)).fetchall()
    v.close()
    random.seed(args.seed)
    random.shuffle(rows)
    muestra = rows[:args.n]
    print(f"franja [{lo},{hi}]d: {len(rows)} ofertas | muestra: {len(muestra)} | delay={args.delay}s")
    print("=" * 64)

    res = Counter()          # viva/caida/ambigua/error
    casos = Counter()        # señal cruda (caso)
    n_resultados = []
    bloqueos = 0
    procesadas = 0
    for i, (ido, titulo, url, dias) in enumerate(muestra, 1):
        time.sleep(args.delay)
        try:
            resultado, senal = v.clasificar_ct_busqueda(url, titulo, ido)
            bloqueos = 0
        except vb.BloqueoError as e:
            bloqueos += 1
            res["error"] += 1
            print(f"  [{i}] BLOQUEO ({bloqueos}/{v.max_bloqueos}): {e}")
            if bloqueos >= v.max_bloqueos:
                print(f"  CORTE: {v.max_bloqueos} bloqueos seguidos — gate PARCIAL.")
                break
            time.sleep(min(bloqueos * 10, 60))
            continue
        except Exception as e:
            res["error"] += 1
            print(f"  [{i}] error: {str(e)[:70]}")
            continue
        procesadas += 1
        res[resultado] += 1
        casos[senal.get("caso", resultado)] += 1
        if "n_resultados" in senal:
            n_resultados.append(senal["n_resultados"])
        if i % 20 == 0:
            print(f"  ...{i}/{len(muestra)}  viva={res['viva']} caida={res['caida']} amb={res['ambigua']}")

    print("=" * 64)
    viva, caida, amb = res["viva"], res["caida"], res["ambigua"]
    decididas = viva + caida
    print(f"CLASIFICADAS: {procesadas}  (viva={viva} caida={caida} ambigua={amb} error={res['error']})")
    if decididas:
        pct_dec = 100.0 * viva / decididas
        print(f"%VIVAS sobre decididas (viva/(viva+caida)): {pct_dec:.1f}%   [objetivo 20-25%]")
    if procesadas:
        print(f"%vivas sobre clasificadas (incl. ambiguas):  {100.0*viva/procesadas:.1f}%")
    print(f"ambiguas: {amb} ({100.0*amb/procesadas:.1f}% de clasificadas)" if procesadas else "")
    print(f"casos (señal cruda): {dict(casos)}")
    if n_resultados:
        n_resultados.sort()
        med = n_resultados[len(n_resultados)//2]
        print(f"n_resultados buscador: min={n_resultados[0]} mediana={med} max={n_resultados[-1]}")
    print("=" * 64)
    if decididas:
        band = "EN BANDA (20-25%) → vía sólida, apta para activar" if 18 <= pct_dec <= 28 \
            else ("SOBRE la banda (sobre-viva, tipo el error 04-09) → NO activar" if pct_dec > 28
                  else "BAJO la banda (sobre-caída) → NO activar")
        print(f"VEREDICTO GATE: {pct_dec:.1f}% → {band}")


if __name__ == "__main__":
    main()
