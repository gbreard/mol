#!/usr/bin/env python3
"""
Recómputo del ciclo de vida (Fase 2)
====================================

Reclasifica el estado_ciclo de TODAS las ofertas con la definición nueva
(SPEC_ciclo_vida_ofertas.md §5 + addendum 2026-09-02), operando SOLO sobre
`portal` y `fecha_ultimo_visto` (con fallback fecha_baja/scrapeado_en).
NUNCA usa url_oferta (ver nota issue 2026-09-02: 5.359 zonajobs con url de
bumeran — irrelevante acá).

REVERSIBLE: cada fila queda en recompute_ciclo_vida_log con estado anterior.
No toca legacy estado_oferta/fecha_baja (dual-write recién en Fase 3).

Modos:
  --mode dry-run   (default) calcula y muestra distribución + contraste, NO escribe
  --mode apply     escribe estado_ciclo + fecha_baja terminal + log (run_id único)
  --mode rollback  --run-id X [--limit N]   restaura estado_ciclo = anterior
  --mode reapply   --run-id X [--limit N]   restaura estado_ciclo = nuevo (del log)
"""
import sqlite3, argparse, json
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = BASE_DIR / "database" / "bumeran_scraping.db"
CONFIG = BASE_DIR / "config" / "scraping" / "ciclo_vida_ofertas.json"

# Estimados de la spec §5.1 (ref 2026-09-02) para contraste, sobre estado_oferta='baja'
ESTIMADOS = {"activa": 17698, "presunta_baja": 19125, "baja_no_verificada": 58637, "baja_inferida": 19083}
TOLERANCIA = 0.03


def cargar_config():
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    return c["portales"], c.get("ventana_verificable_factor", 2), c.get("_default", {})


def _parse(d):
    try:
        return date.fromisoformat(str(d)[:10])
    except Exception:
        return None


def clasificar(portal, estado_oferta, fecha_base, ref, portales, factor):
    """Devuelve estado_ciclo_nuevo. Solo usa portal + fecha_base (nunca url)."""
    if portal == "indeed":
        # No verificable: activa si estaba activa, inferida si estaba baja.
        return "activa" if estado_oferta == "activa" else "baja_inferida"
    cfg = portales.get(portal)
    if not cfg or cfg.get("umbral_presunta_baja_dias") is None:
        return "activa" if estado_oferta == "activa" else "baja_no_verificada"
    u = cfg["umbral_presunta_baja_dias"]
    ant = (ref - fecha_base).days if fecha_base else 99999
    if ant < u:
        return "activa"
    if ant < factor * u:
        return "presunta_baja"
    return "baja_no_verificada"


def calcular(conn, ref, portales, factor):
    """Stream de todas las ofertas → lista (id, portal, estado_oferta, fecha_base, ant, nuevo)."""
    rows = conn.execute("""
        SELECT id_oferta, portal, estado_oferta,
               COALESCE(fecha_ultimo_visto, fecha_baja, substr(scrapeado_en,1,10))
        FROM ofertas""").fetchall()
    out = []
    for ido, portal, eo, fb in rows:
        fbd = _parse(fb)
        ant = (ref - fbd).days if fbd else None
        nuevo = clasificar(portal, eo, fbd, ref, portales, factor)
        out.append((ido, portal, eo, str(fb) if fb else None, ant, nuevo))
    return out


def resumen(calc):
    from collections import Counter
    total = Counter(r[5] for r in calc)
    bajas = Counter(r[5] for r in calc if r[2] == "baja")
    activas = Counter(r[5] for r in calc if r[2] == "activa")
    return total, bajas, activas


def contraste(bajas):
    print("\n=== CONTRASTE (reclasificación de estado_oferta='baja') vs spec §5.1 ===")
    ok = True
    for k, est in ESTIMADOS.items():
        real = bajas.get(k, 0)
        desv = abs(real - est) / est if est else 0
        flag = "OK" if desv <= TOLERANCIA else "⚠ FUERA DE ±3%"
        if desv > TOLERANCIA:
            ok = False
        print(f"  {k:<22} real={real:>7,}  estimado={est:>7,}  desv={desv*100:4.1f}%  {flag}")
    return ok


def aplicar(conn, calc, ref):
    run_id = "recompute_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    ts = datetime.now().isoformat()
    terminal_fecha = {"baja_no_verificada", "baja_inferida"}
    log_rows, upd_rows, upd_fecha = [], [], []
    for ido, portal, eo, fb, ant, nuevo in calc:
        log_rows.append((run_id, ido, eo, None, nuevo, fb, ant, ts))
        upd_rows.append((nuevo, ido))
        if nuevo in terminal_fecha and fb:
            # intervalo abierto: desde=último visto, sin cota superior; estimada=desde
            upd_fecha.append((fb, fb, ido))
    conn.executemany("UPDATE ofertas SET estado_ciclo=? WHERE id_oferta=?", upd_rows)
    conn.executemany(
        "UPDATE ofertas SET fecha_baja_intervalo_desde=?, fecha_baja_estimada=? WHERE id_oferta=?",
        upd_fecha)
    conn.executemany("""INSERT INTO recompute_ciclo_vida_log
        (run_id,id_oferta,estado_oferta_anterior,estado_ciclo_anterior,estado_ciclo_nuevo,
         fecha_ultimo_visto_usada,antiguedad_dias,timestamp) VALUES (?,?,?,?,?,?,?,?)""", log_rows)
    conn.commit()
    return run_id, len(upd_rows), len(upd_fecha)


def rollback(conn, run_id, columna, limit):
    """columna='estado_ciclo_anterior' (rollback) | 'estado_ciclo_nuevo' (reapply)."""
    lim = f"LIMIT {int(limit)}" if limit else ""
    ids = [r[0] for r in conn.execute(
        f"SELECT id_oferta FROM recompute_ciclo_vida_log WHERE run_id=? ORDER BY id {lim}", (run_id,))]
    for ido in ids:
        val = conn.execute(
            f"SELECT {columna} FROM recompute_ciclo_vida_log WHERE run_id=? AND id_oferta=? ORDER BY id DESC LIMIT 1",
            (run_id, ido)).fetchone()[0]
        conn.execute("UPDATE ofertas SET estado_ciclo=? WHERE id_oferta=?", (val, ido))
    conn.commit()
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--mode", default="dry-run", choices=["dry-run", "apply", "rollback", "reapply"])
    ap.add_argument("--run-id")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    ref = datetime.now().date()

    if args.mode in ("rollback", "reapply"):
        col = "estado_ciclo_anterior" if args.mode == "rollback" else "estado_ciclo_nuevo"
        ids = rollback(conn, args.run_id, col, args.limit)
        print(f"{args.mode}: {len(ids)} filas run_id={args.run_id} → estado_ciclo={col}")
        print("  ids:", ids[:10], "..." if len(ids) > 10 else "")
        return

    portales, factor, _ = cargar_config()
    print(f"Recómputo ciclo de vida — modo={args.mode}  ref={ref}  factor={factor}")
    calc = calcular(conn, ref, portales, factor)
    total, bajas, activas = resumen(calc)
    print(f"\nfilas procesadas: {len(calc):,}")
    print("distribución estado_ciclo (TOTAL):", dict(total))
    print("  de las que eran 'activa' legacy:", dict(activas))
    ok = contraste(bajas)

    if args.mode == "dry-run":
        print("\nDRY-RUN: no se escribió nada." + ("" if ok else "  ⚠ HAY DESVÍO > ±3% — FRENAR."))
        return

    if not ok:
        print("\n❌ ABORTADO: contraste fuera de ±3%. No se escribe. Explicar la brecha antes.")
        return
    run_id, n, nf = aplicar(conn, calc, ref)
    print(f"\n✅ APLICADO run_id={run_id}  estado_ciclo actualizado={n:,}  fecha_baja terminal={nf:,}")


if __name__ == "__main__":
    main()
