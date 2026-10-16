#!/usr/bin/env python3
"""
Backfill one-time de fecha_ultimo_visto = scrapeado_en para ofertas LEGADO.

Contexto (issue 2026-10-14): ~4.119 ofertas (todos los portales salvo Indeed)
tienen fecha_ultimo_visto NULL. Diagnóstico: LEGADO — scraping viejo (ene-jun
2026), 0 NULL en inserts recientes (≥2026-10) → el camino actual
(detectar_bajas_integrado.actualizar_fecha_ultimo_visto) sí setea el campo; estas
son de antes de que se mantuviera. Sin fecha_ultimo_visto no pueden envejecer ni
confirmarse → quedan congeladas en presunta_baja para siempre.

Fix: fecha_ultimo_visto = scrapeado_en (proxy correcto del "último visto" para una
oferta scrapeada una vez y nunca re-vista). Toca SOLO filas con fecha_ultimo_visto
NULL y scrapeado_en no-NULL. NO toca estado_oferta ni estado_ciclo (esos los
recalcula el motor de transiciones / verificador después, al poder envejecerlas).

Uso: backfill_fecha_ultimo_visto.py [--apply]   (default dry-run)
"""
import sqlite3, argparse
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "database" / "bumeran_scraping.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="aplica el UPDATE (default: dry-run)")
    args = ap.parse_args()
    c = sqlite3.connect(str(DB))

    objetivo = c.execute("""SELECT COUNT(*) FROM ofertas
        WHERE fecha_ultimo_visto IS NULL AND scrapeado_en IS NOT NULL""").fetchone()[0]
    sin_proxy = c.execute("""SELECT COUNT(*) FROM ofertas
        WHERE fecha_ultimo_visto IS NULL AND scrapeado_en IS NULL""").fetchone()[0]

    print("=== backfill fecha_ultimo_visto = scrapeado_en (LEGADO) ===")
    print(f"a backfillear (NULL con scrapeado_en): {objetivo}")
    print(f"NO backfilleable (ambos NULL): {sin_proxy}")
    print("por portal:")
    for p, n in c.execute("""SELECT portal, COUNT(*) FROM ofertas
        WHERE fecha_ultimo_visto IS NULL AND scrapeado_en IS NOT NULL
        GROUP BY portal ORDER BY 2 DESC""").fetchall():
        print(f"  {str(p):14} {n}")

    if not args.apply:
        print("\n[DRY-RUN] nada escrito. Correr con --apply para aplicar.")
        c.close()
        return

    cur = c.execute("""UPDATE ofertas SET fecha_ultimo_visto = scrapeado_en
        WHERE fecha_ultimo_visto IS NULL AND scrapeado_en IS NOT NULL""")
    c.commit()
    print(f"\n[APLICADO] filas actualizadas: {cur.rowcount}")
    rest = c.execute("SELECT COUNT(*) FROM ofertas WHERE fecha_ultimo_visto IS NULL").fetchone()[0]
    print(f"NULL restantes (ambos NULL, no backfilleables): {rest}")
    c.close()


if __name__ == "__main__":
    main()
