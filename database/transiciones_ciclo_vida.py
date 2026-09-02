#!/usr/bin/env python3
"""
Motor de transiciones del ciclo de vida (Fase 3 — MODO SOMBRA)
==============================================================

Corre en el post-sync local (después del detectar_bajas legacy, que sigue
encendido y mantiene fecha_ultimo_visto + estado_oferta). Este motor escribe
SÓLO columnas propias: estado_ciclo, contadores de verificación, fecha_baja_*,
y las tablas transiciones_ciclo_vida / divergencia_ciclo_log.
**NUNCA toca estado_oferta ni fecha_baja legacy** → producción visible no cambia
hasta Fase 5.

Transiciones (SPEC §1.2 + addendum 2026-09-02):
  - reaparición: estado_ciclo no-activa + visto en corrida (fecha_ultimo_visto
    reciente) → activa + reset de contadores. Registra la transición (alimenta
    la métrica de resurrección §11.3).
  - activa → presunta_baja: Navent (bumeran/zonajobs) + computrabajo, cuando
    (hoy - fecha_ultimo_visto) >= umbral del portal (config).
  - Portal Empleo → baja_confirmada: ausente en 2 corridas COMPLETAS (§11.7),
    leyendo corridas_scraping.completa.
  - CABA: NO se confirma todavía — corridas_scraping se escribe en el VPS y no
    se sincroniza a local (limitación documentada; §11.7 escape hatch).
  - Indeed: NO se infiere — keyword_source no se persiste en ofertas y el
    state-file no da cobertura de pasadas (§11.8 escape hatch).

Divergencia (bonus modo-sombra): registra por corrida cuántas bajas del legacy
el nuevo modelo considera activas (falsas bajas del muestreo).
"""
import sqlite3
import json
import logging
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
CONFIG = BASE_DIR / "config" / "scraping" / "ciclo_vida_ofertas.json"
STATE = BASE_DIR / "data" / "ciclo_vida_state.json"

NAVENT_CT = {"bumeran", "zonajobs", "computrabajo"}
BAJAS_ESTADOS = ("presunta_baja", "baja_confirmada", "baja_inferida", "baja_no_verificada")


class TransicionesCicloVida:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        cfg = json.loads(Path(CONFIG).read_text(encoding="utf-8"))
        self.portales = cfg["portales"]
        self.factor = cfg.get("ventana_verificable_factor", 2)
        self.conn = None
        self.stats = {"reaparecidas": 0, "a_presunta": 0, "pe_confirmadas": 0,
                      "divergencia": 0, "transiciones": 0}

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, timeout=120)
        self.conn.execute("PRAGMA busy_timeout=120000")

    def close(self):
        if self.conn:
            self.conn.close()

    # ---- state (última corrida del motor) ----
    def _last_run(self):
        try:
            return json.loads(Path(STATE).read_text()).get("last_run")
        except Exception:
            return None

    def _save_run(self, ts):
        Path(STATE).parent.mkdir(parents=True, exist_ok=True)
        Path(STATE).write_text(json.dumps({"last_run": ts}, indent=2))

    def _log_transicion(self, ido, portal, desde, hacia, motivo, ts, dry):
        self.stats["transiciones"] += 1
        if not dry:
            self.conn.execute(
                "INSERT INTO transiciones_ciclo_vida (id_oferta,portal,estado_desde,estado_hacia,motivo,fecha) VALUES (?,?,?,?,?,?)",
                (ido, portal, desde, hacia, motivo, ts))

    # ---- 1) reaparición → activa (con reset) ----
    def _reaparicion(self, ts, desde_corrida, dry):
        rows = self.conn.execute(f"""
            SELECT id_oferta, portal, estado_ciclo FROM ofertas
            WHERE estado_ciclo IN {BAJAS_ESTADOS}
              AND fecha_ultimo_visto >= ?""", (desde_corrida,)).fetchall()
        for ido, portal, desde in rows:
            self.stats["reaparecidas"] += 1
            if not dry:
                self.conn.execute("""UPDATE ofertas SET estado_ciclo='activa',
                    verificaciones_caida_count=0, fecha_primera_verificacion_caida=NULL,
                    fecha_baja_estimada=NULL, fecha_baja_intervalo_desde=NULL,
                    fecha_baja_intervalo_hasta=NULL, fecha_baja_incertidumbre_dias=NULL
                    WHERE id_oferta=?""", (ido,))
            self._log_transicion(ido, portal, desde, "activa", "scraping_reaparece", ts, dry)

    # ---- 2) activa → presunta_baja (Navent + CT) ----
    def _a_presunta(self, ref, ts, dry):
        for portal in NAVENT_CT:
            u = self.portales.get(portal, {}).get("umbral_presunta_baja_dias")
            if not u:
                continue
            limite = (ref - _dias(u)).isoformat()
            rows = self.conn.execute("""
                SELECT id_oferta FROM ofertas
                WHERE estado_ciclo='activa' AND portal=? AND fecha_ultimo_visto IS NOT NULL
                  AND substr(fecha_ultimo_visto,1,10) <= ?""", (portal, limite)).fetchall()
            for (ido,) in rows:
                self.stats["a_presunta"] += 1
                if not dry:
                    self.conn.execute("UPDATE ofertas SET estado_ciclo='presunta_baja' WHERE id_oferta=?", (ido,))
                self._log_transicion(ido, portal, "activa", "presunta_baja", "umbral", ts, dry)

    # ---- 3) Portal Empleo → baja_confirmada por 2 corridas completas ----
    def _pe_confirmadas(self, ts, dry):
        completas = self.conn.execute("""
            SELECT fecha FROM corridas_scraping
            WHERE portal='portalempleo' AND completa=1 ORDER BY fecha DESC LIMIT 2""").fetchall()
        if len(completas) < 2:
            logger.info("  PE: <2 corridas completas registradas — no se confirma (§11.7)")
            return
        segunda = completas[1][0]  # la 2ª más reciente: ausente desde antes de ésta = ausente en 2 completas
        rows = self.conn.execute("""
            SELECT id_oferta, fecha_ultimo_visto FROM ofertas
            WHERE portal='portalempleo' AND estado_ciclo IN ('activa','presunta_baja')
              AND fecha_ultimo_visto IS NOT NULL AND fecha_ultimo_visto < ?""", (segunda,)).fetchall()
        for ido, fuv in rows:
            self.stats["pe_confirmadas"] += 1
            desde, hasta = str(fuv)[:10], str(segunda)[:10]
            estimada, inc = _intervalo(desde, hasta)
            if not dry:
                self.conn.execute("""UPDATE ofertas SET estado_ciclo='baja_confirmada',
                    fecha_baja_intervalo_desde=?, fecha_baja_intervalo_hasta=?,
                    fecha_baja_estimada=?, fecha_baja_incertidumbre_dias=? WHERE id_oferta=?""",
                    (desde, hasta, estimada, inc, ido))
            self._log_transicion(ido, "portalempleo", "presunta_baja", "baja_confirmada", "2a_ausencia", ts, dry)

    # ---- bonus: divergencia legacy vs ciclo ----
    def _divergencia(self, ts, dry):
        n = self.conn.execute(
            "SELECT COUNT(*) FROM ofertas WHERE estado_oferta='baja' AND estado_ciclo='activa'").fetchone()[0]
        tot = self.conn.execute("SELECT COUNT(*) FROM ofertas WHERE estado_oferta='baja'").fetchone()[0]
        self.stats["divergencia"] = n
        det = dict(self.conn.execute("""SELECT portal, COUNT(*) FROM ofertas
            WHERE estado_oferta='baja' AND estado_ciclo='activa' GROUP BY portal""").fetchall())
        if not dry:
            self.conn.execute(
                "INSERT INTO divergencia_ciclo_log (fecha,n_legacy_baja_ciclo_activa,n_legacy_baja_total,detalle_json) VALUES (?,?,?,?)",
                (ts, n, tot, json.dumps(det, ensure_ascii=False)))

    def ejecutar(self, dry_run=False):
        ts = datetime.now().isoformat()
        ref = datetime.now().date()
        last = self._last_run()
        # "visto en corrida" = fecha_ultimo_visto desde el último run del motor (o desde hoy si primer run)
        desde_corrida = last or ref.isoformat()

        self._reaparicion(ts, desde_corrida, dry_run)
        self._a_presunta(ref, ts, dry_run)
        self._pe_confirmadas(ts, dry_run)
        self._divergencia(ts, dry_run)

        if not dry_run:
            self.conn.commit()
            self._save_run(ts)
        logger.info(f"Transiciones ciclo de vida (dry={dry_run}): {self.stats}")
        return self.stats


def _dias(n):
    from datetime import timedelta
    return timedelta(days=n)


def _intervalo(desde, hasta):
    try:
        d0, d1 = date.fromisoformat(desde), date.fromisoformat(hasta)
        mid = d0 + (d1 - d0) / 2
        return mid.isoformat(), (d1 - d0).days // 2
    except Exception:
        return desde, None


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    m = TransicionesCicloVida(args.db)
    m.connect()
    stats = m.ejecutar(dry_run=args.dry_run)
    m.close()
    print("RESULTADO:" + json.dumps(stats))
