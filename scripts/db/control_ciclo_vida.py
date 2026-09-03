#!/usr/bin/env python3
"""
Panel de control del ciclo de vida de ofertas (seguimiento del verificador).
Pensado para revisar el LUNES tras las 2ª verificaciones (vencido el gap de 72 h).

Muestra:
  1. Confirmadas por portal (presunta → baja_confirmada tras 2 caídas ≥72h).
  2. Resurrecciones en 2ª verificación (caída → viva: la oferta que dio caída
     una vez y viva en la 2ª → volvió a activa en vez de confirmar). Dato de §11.3.
  3. Tamaño restante de la cola (presunta_baja, y cuántas con count=1 esperando 2ª).
  4. Divergencia legacy↔ciclo (falsas bajas del legacy) — contexto Fase 5.

Uso: python3 scripts/db/control_ciclo_vida.py
"""
import sqlite3
import argparse
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "database" / "bumeran_scraping.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()
    c = sqlite3.connect(args.db, timeout=60)
    c.execute("PRAGMA busy_timeout=60000")
    q = c.execute

    print("=" * 64)
    print("PANEL CICLO DE VIDA — seguimiento del verificador")
    print("=" * 64)

    print("\n1) CONFIRMADAS por portal (baja_confirmada):")
    rows = q("SELECT portal, COUNT(*) FROM ofertas WHERE estado_ciclo='baja_confirmada' GROUP BY portal ORDER BY 2 DESC").fetchall()
    print("   " + (str(dict(rows)) if rows else "(ninguna todavía)"))

    print("\n2) RESURRECCIONES en 2ª verificación (caída→viva; §11.3):")
    # ofertas con ≥1 verificación 'caida' y una 'viva' posterior
    rows = q("""
        SELECT v.portal, COUNT(DISTINCT v.id_oferta)
        FROM verificaciones_baja v
        WHERE v.resultado='viva'
          AND EXISTS (SELECT 1 FROM verificaciones_baja v2
                      WHERE v2.id_oferta=v.id_oferta AND v2.resultado='caida' AND v2.fecha < v.fecha)
        GROUP BY v.portal ORDER BY 2 DESC""").fetchall()
    print("   " + (str(dict(rows)) if rows else "(ninguna todavía)"))
    total_viva = q("SELECT COUNT(*) FROM transiciones_ciclo_vida WHERE motivo='verificacion_viva'").fetchone()[0]
    print(f"   (resurrecciones totales por verificación, incl. 1ª: {total_viva:,})")

    print("\n3) COLA RESTANTE (presunta_baja):")
    for portal, n in q("SELECT portal, COUNT(*) FROM ofertas WHERE estado_ciclo='presunta_baja' GROUP BY portal ORDER BY 2 DESC").fetchall():
        c1 = q("SELECT COUNT(*) FROM ofertas WHERE estado_ciclo='presunta_baja' AND portal=? AND verificaciones_caida_count=1", (portal,)).fetchone()[0]
        print(f"   {portal:<13} total={n:>6,}  (count=1 esperando 2ª: {c1:,})")

    print("\n4) DISTRIBUCIÓN estado_ciclo:")
    print("   " + str(dict(q("SELECT estado_ciclo, COUNT(*) FROM ofertas WHERE estado_ciclo IS NOT NULL GROUP BY 1 ORDER BY 2 DESC").fetchall())))

    print("\n5) DIVERGENCIA legacy↔ciclo (falsas bajas del legacy, contexto Fase 5):")
    n = q("SELECT COUNT(*) FROM ofertas WHERE estado_oferta='baja' AND estado_ciclo='activa'").fetchone()[0]
    print(f"   legacy=baja pero ciclo=activa: {n:,}")
    c.close()


if __name__ == "__main__":
    main()
