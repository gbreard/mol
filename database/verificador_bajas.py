#!/usr/bin/env python3
"""
Verificador de bajas (Fase 4) — job local, MODO SOMBRA
======================================================

Toma la cola de `presunta_baja` (Navent + CT), verifica cada oferta por su vía
medida, y tras DOS caídas separadas ≥ gap la pasa a `baja_confirmada`. Una viva
la devuelve a `activa` (con reset y transición logueada → métrica resurrección).
Escribe SOLO estado_ciclo + verificaciones_baja + transiciones_ciclo_vida.
**Nunca toca estado_oferta** (legacy intacto hasta Fase 5).

Vías (taxonomía medida, exports/reportes/supervivencia/):
  - Navent (bumeran/zonajobs): POST /api/avisos/searchV2 con el título.
      id en resultados        → viva
      0 resultados            → caída
      resultados < tope, sin id → caída
      resultados == tope, sin id → ambigua → reintento query específica; si persiste, NO cuenta
  - ComputRabajo: REUTILIZA ComputrabajoScraper.scrapear_oferta_individual + ultimo_fallo (§11.9):
      ultimo_fallo redirect_listado / listado_seo → caída
      descripción real                            → viva
      http / excepcion / sin_metodo               → ambigua

Límites §11.4: searchV2 ≤2.500/día por portal; CT ≤4.000 (drenaje) / ≤1.000 (régimen).
Corte inmediato ante bloqueo (política Indeed). Lockfile-aware.
"""
import sqlite3, json, time, uuid, logging, argparse
from datetime import datetime, date, timedelta
from pathlib import Path
import requests

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
CONFIG = BASE_DIR / "config" / "scraping" / "ciclo_vida_ofertas.json"
LOCK_LOCAL = Path("/tmp/mol_scraping.lock")

NAVENT_SITE = {"bumeran": ("BMAR", "https://www.bumeran.com.ar"),
               "zonajobs": ("ZJAR", "https://www.zonajobs.com.ar")}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TOPE_SEARCHV2 = 100


class VerificadorBajas:
    def __init__(self, db_path=DB_PATH, regimen=False):
        cfg = json.loads(Path(CONFIG).read_text(encoding="utf-8"))
        self.portales = cfg["portales"]
        self.gap = timedelta(hours=cfg.get("verificacion_gap_horas", 72))
        self.n_confirmar = cfg.get("verificaciones_para_confirmar", 2)
        self.regimen = regimen
        self.db_path = str(db_path)
        self.conn = None
        self._sessions = {}
        self._ct = None
        self.delay_navent = 1.0
        self.delay_ct = 3.0
        self.max_bloqueos = 5
        self.stats = {}

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, timeout=120)
        self.conn.execute("PRAGMA busy_timeout=120000")

    def close(self):
        if self.conn:
            self.conn.close()

    def lock_tomado(self):
        return LOCK_LOCAL.exists()

    def tope(self, portal):
        cfg = self.portales.get(portal, {})
        key = "tope_diario_regimen" if self.regimen else "tope_diario"
        return cfg.get(key) or cfg.get("tope_diario") or 1000

    # ---------- cola ----------
    def cola(self, portal, limit):
        ahora = datetime.now()
        gap_lim = (ahora - self.gap).isoformat()
        rows = self.conn.execute("""
            SELECT id_oferta, portal, titulo, url_oferta, verificaciones_caida_count,
                   fecha_ultimo_visto, fecha_primera_verificacion_caida
            FROM ofertas
            WHERE estado_ciclo='presunta_baja' AND portal=?
              AND (verificaciones_caida_count = 0
                   OR (verificaciones_caida_count = 1
                       AND (fecha_ultima_verificacion IS NULL OR fecha_ultima_verificacion <= ?)))
            ORDER BY fecha_ultimo_visto ASC
            LIMIT ?""", (portal, gap_lim, limit)).fetchall()
        return rows

    # ---------- vías ----------
    def _session_navent(self, portal):
        if portal not in self._sessions:
            site, base = NAVENT_SITE[portal]
            s = requests.Session()
            s.headers.update({"User-Agent": UA, "Accept": "application/json",
                              "Accept-Language": "es-AR,es;q=0.9", "x-site-id": site,
                              "x-pre-session-token": str(uuid.uuid4()),
                              "Referer": f"{base}/", "Origin": base})
            try:
                s.get(base, timeout=10)
            except Exception:
                pass
            self._sessions[portal] = (s, base)
        return self._sessions[portal]

    def _searchv2(self, portal, query):
        s, base = self._session_navent(portal)
        payload = {"filterData": {"filtros": [], "tipoDetalle": "full", "busquedaExtendida": False},
                   "page": 0, "pageSize": TOPE_SEARCHV2, "sort": "RELEVANCE", "query": query}
        r = s.post(f"{base}/api/avisos/searchV2", json=payload, timeout=15)
        if r.status_code != 200:
            return None, r.status_code
        return r.json(), 200

    def clasificar_navent(self, portal, titulo, target_id):
        """Devuelve (resultado, senal_dict). Puede lanzar para el circuit-breaker."""
        q = (titulo or "")[:60]
        data, status = self._searchv2(portal, q)
        if data is None:
            raise BloqueoError(f"searchV2 {portal} status={status}")
        content = data.get("content", []) or []
        ids = {str(o.get("id")) for o in content}
        presente = str(target_id) in ids
        n = len(content)
        senal = {"n_resultados": n, "id_presente": presente, "query": q}
        if presente:
            return "viva", senal
        if n == 0:
            return "caida", {**senal, "caso": "cero_resultados"}
        if n < TOPE_SEARCHV2:
            return "caida", {**senal, "caso": "menos_que_tope_sin_id"}
        # n == tope y sin id → ambigua → reintento con query más específica (título completo)
        q2 = (titulo or "")[:120]
        if q2 != q:
            time.sleep(self.delay_navent)
            data2, status2 = self._searchv2(portal, q2)
            if data2 is not None:
                c2 = data2.get("content", []) or []
                if str(target_id) in {str(o.get("id")) for o in c2}:
                    return "viva", {**senal, "reintento": True}
                if len(c2) < TOPE_SEARCHV2:
                    return "caida", {**senal, "reintento": True, "caso": "reintento_menos_tope"}
        return "ambigua", {**senal, "caso": "tope_alcanzado"}

    def clasificar_ct(self, url):
        if self._ct is None:
            import sys
            sys.path.insert(0, str(BASE_DIR / "01_sources" / "computrabajo" / "scrapers"))
            from computrabajo_scraper import ComputRabajoScraper
            self._ct = ComputRabajoScraper()
        datos = self._ct.scrapear_oferta_individual(url)
        fallo = getattr(self._ct, "ultimo_fallo", None)
        if fallo in ("redirect_listado", "listado_seo"):
            return "caida", {"ultimo_fallo": fallo}
        if datos and datos.get("descripcion"):
            return "viva", {"desc_len": len(datos["descripcion"])}
        if fallo == "http":
            raise BloqueoError("CT http")
        return "ambigua", {"ultimo_fallo": fallo}

    # ---------- aplicar resultado ----------
    def _aplicar(self, ido, portal, fecha_ultimo_visto, n_prev, primera_caida, resultado, senal, ts, dry):
        if not dry:
            self.conn.execute(
                "INSERT INTO verificaciones_baja (id_oferta,portal,fecha,via,resultado,senal_cruda) VALUES (?,?,?,?,?,?)",
                (ido, portal, ts, "searchv2" if portal in NAVENT_SITE else "html_detalle",
                 resultado, json.dumps(senal, ensure_ascii=False)))
        if resultado == "viva":
            if not dry:
                self.conn.execute("""UPDATE ofertas SET estado_ciclo='activa', verificaciones_caida_count=0,
                    fecha_primera_verificacion_caida=NULL, fecha_ultima_verificacion=? WHERE id_oferta=?""", (ts, ido))
                self._transicion(ido, portal, "presunta_baja", "activa", "verificacion_viva", ts)
        elif resultado == "caida":
            nuevo = n_prev + 1
            if nuevo >= self.n_confirmar:
                desde = str(fecha_ultimo_visto)[:10]
                hasta = str(primera_caida or ts)[:10]
                est, inc = _intervalo(desde, hasta)
                if not dry:
                    self.conn.execute("""UPDATE ofertas SET estado_ciclo='baja_confirmada',
                        verificaciones_caida_count=?, fecha_ultima_verificacion=?,
                        fecha_baja_intervalo_desde=?, fecha_baja_intervalo_hasta=?,
                        fecha_baja_estimada=?, fecha_baja_incertidumbre_dias=? WHERE id_oferta=?""",
                        (nuevo, ts, desde, hasta, est, inc, ido))
                    self._transicion(ido, portal, "presunta_baja", "baja_confirmada", "verificacion_caida", ts)
            else:
                if not dry:
                    self.conn.execute("""UPDATE ofertas SET verificaciones_caida_count=?,
                        fecha_ultima_verificacion=?,
                        fecha_primera_verificacion_caida=COALESCE(fecha_primera_verificacion_caida,?)
                        WHERE id_oferta=?""", (nuevo, ts, ts, ido))
        # ambigua: no cambia contadores

    def _transicion(self, ido, portal, desde, hacia, motivo, ts):
        self.conn.execute(
            "INSERT INTO transiciones_ciclo_vida (id_oferta,portal,estado_desde,estado_hacia,motivo,fecha) VALUES (?,?,?,?,?,?)",
            (ido, portal, desde, hacia, motivo, ts))

    # ---------- run ----------
    def ejecutar(self, dry_run=False, limit_por_portal=None, portales=None):
        if self.lock_tomado():
            logger.warning("lock de scraping presente — el verificador NO corre")
            return {"abortado": "lock"}
        portales = portales or ["bumeran", "zonajobs", "computrabajo"]
        for portal in portales:
            tope = min(limit_por_portal or self.tope(portal), self.tope(portal))
            rows = self.cola(portal, tope)
            st = {"cola": len(rows), "viva": 0, "caida": 0, "ambigua": 0, "confirmadas": 0, "error": 0}
            self.stats[portal] = st
            if dry_run:
                continue
            bloqueos = 0
            for ido, p, titulo, url, n_prev, fuv, primera in rows:
                delay = self.delay_navent if portal in NAVENT_SITE else self.delay_ct
                time.sleep(delay)
                ts = datetime.now().isoformat()
                try:
                    if portal in NAVENT_SITE:
                        resultado, senal = self.clasificar_navent(portal, titulo, ido)
                    else:
                        resultado, senal = self.clasificar_ct(url)
                    bloqueos = 0
                except BloqueoError as e:
                    bloqueos += 1
                    st["error"] += 1
                    logger.warning(f"  bloqueo {portal} ({bloqueos}/{self.max_bloqueos}): {e}")
                    if bloqueos >= self.max_bloqueos:
                        logger.error(f"  CORTE {portal}: {self.max_bloqueos} bloqueos — sigue mañana")
                        break
                    continue
                except Exception as e:
                    st["error"] += 1
                    logger.warning(f"  error verificando {ido}: {str(e)[:80]}")
                    continue
                st[resultado] += 1
                prev_estado = self.conn.execute("SELECT estado_ciclo FROM ofertas WHERE id_oferta=?", (ido,)).fetchone()[0]
                self._aplicar(ido, portal, fuv, n_prev, primera, resultado, senal, ts, dry_run)
                nuevo_estado = self.conn.execute("SELECT estado_ciclo FROM ofertas WHERE id_oferta=?", (ido,)).fetchone()[0]
                if nuevo_estado == "baja_confirmada" and prev_estado != "baja_confirmada":
                    st["confirmadas"] += 1
            if not dry_run:
                self.conn.commit()
        return self.stats


class BloqueoError(Exception):
    pass


def _intervalo(desde, hasta):
    try:
        d0, d1 = date.fromisoformat(desde), date.fromisoformat(hasta)
        return (d0 + (d1 - d0) / 2).isoformat(), (d1 - d0).days // 2
    except Exception:
        return desde, None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, help="tope por portal en esta corrida")
    ap.add_argument("--portales", help="csv: bumeran,zonajobs,computrabajo")
    ap.add_argument("--regimen", action="store_true")
    args = ap.parse_args()
    v = VerificadorBajas(args.db, regimen=args.regimen)
    v.connect()
    portales = args.portales.split(",") if args.portales else None
    stats = v.ejecutar(dry_run=args.dry_run, limit_por_portal=args.limit, portales=portales)
    v.close()
    print("RESULTADO:" + json.dumps(stats, ensure_ascii=False))
