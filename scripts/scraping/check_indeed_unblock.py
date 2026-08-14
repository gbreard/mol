#!/usr/bin/env python3
"""
Vigila si Indeed volvio a dejarnos scrapear — desde LOCAL y desde el VPS — y
dispara una corrida en la primera IP que este habilitada.

Por que dos IPs: el bloqueo es por IP, asi que cada una tiene su propio estado.
El VPS estuvo descartado desde 2026-03 por un diagnostico erroneo ("Cloudflare
bloqueo la IP"); en realidad tenia el fingerprint chrome, que es lo que
Cloudflare bloquea. Con firefox135 el VPS scrapea igual que local.

Formas de bloqueo observadas (ver memoria del proyecto):
  - 403 con ~28KB  -> challenge de Cloudflare (fingerprint TLS bloqueado)
  - 403 solo en /viewjob, listado 200 -> presupuesto de fichas agotado (~800-900
    por dia y por IP); decae en dias
  - 401 "Redirecting to login" -> Indeed exige sesion autenticada

Presupuesto: se limita cada corrida a MAX_KEYWORDS (~650 fichas) y se respeta un
COOLDOWN por IP, porque pasarse del presupuesto cuesta DIAS de bloqueo.
Las keywords se recorren por tramos rotativos: el archivo esta ordenado
alfabeticamente y sin offset se corre siempre la A-D.

Uso:
    python3 scripts/scraping/check_indeed_unblock.py
    python3 scripts/scraping/check_indeed_unblock.py --dry-run
    python3 scripts/scraping/check_indeed_unblock.py --solo-chequear
"""

import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "01_sources" / "indeed" / "scrapers"))

from curl_cffi import requests as cr           # noqa: E402
from bs4 import BeautifulSoup                  # noqa: E402
from supabase import create_client             # noqa: E402

ESTADO = PROJECT_ROOT / "data" / "indeed_scraping_state.json"
KEYWORDS_FILE = PROJECT_ROOT / "config" / "scraping" / "master_keywords.json"
VPS_HOST = 'root@187.124.150.28'

LISTADO = 'https://ar.indeed.com/jobs?q=cajero&l=Argentina&fromage=14'
HEADERS = {'Accept-Language': 'es-AR,es;q=0.9'}

COOLDOWN_HORAS = 72     # margen entre corridas de una misma IP
MAX_KEYWORDS = 250      # ~650 fichas por corrida (bajo el techo de ~800/dia)

PROBE = r'''
import json
from curl_cffi import requests as cr
from bs4 import BeautifulSoup
import time
out = {"listado": None, "detalle": None}
s = cr.Session(impersonate="firefox135")
lst = "%s"
try:
    r = s.get(lst, headers={"Accept-Language": "es-AR,es;q=0.9"}, timeout=25)
    out["listado"] = r.status_code
    if r.status_code == 200:
        jks = [e.get("data-jk") for e in BeautifulSoup(r.text, "html.parser").select("[data-jk]") if e.get("data-jk")]
        if jks:
            time.sleep(3)
            d = s.get("https://ar.indeed.com/viewjob?jk=" + jks[0],
                      headers={"Accept-Language": "es-AR,es;q=0.9", "Referer": lst}, timeout=25)
            out["detalle"] = d.status_code
            if d.status_code == 200 and not BeautifulSoup(d.text, "html.parser").select_one("#jobDescriptionText"):
                out["detalle"] = "200-sin-descripcion"
except Exception as e:
    out["error"] = type(e).__name__
print("PROBE:" + json.dumps(out))
''' % LISTADO


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def cargar_estado() -> dict:
    if ESTADO.exists():
        try:
            return json.loads(ESTADO.read_text())
        except Exception:
            pass
    return {}


def guardar_estado(estado: dict) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(estado, indent=2))


def total_keywords() -> int:
    try:
        data = json.loads(KEYWORDS_FILE.read_text(encoding='utf-8'))
        kws = data.get('estrategias', {}).get('exhaustiva', {}).get('keywords', [])
        return len([k for k in kws if k.strip()])
    except Exception:
        return 1072


def probe_local() -> dict:
    """Mismo chequeo que PROBE, corriendo en esta maquina."""
    out = {'listado': None, 'detalle': None}
    s = cr.Session(impersonate='firefox135')
    try:
        r = s.get(LISTADO, headers=HEADERS, timeout=25)
        out['listado'] = r.status_code
        if r.status_code == 200:
            jks = [e.get('data-jk') for e in BeautifulSoup(r.text, 'html.parser').select('[data-jk]')
                   if e.get('data-jk')]
            if jks:
                import time as _t
                _t.sleep(3)
                d = s.get(f'https://ar.indeed.com/viewjob?jk={jks[0]}',
                          headers={**HEADERS, 'Referer': LISTADO}, timeout=25)
                out['detalle'] = d.status_code
                if d.status_code == 200 and not BeautifulSoup(d.text, 'html.parser').select_one('#jobDescriptionText'):
                    out['detalle'] = '200-sin-descripcion'
    except Exception as e:
        out['error'] = type(e).__name__
    return out


def probe_vps() -> dict:
    """Mismo chequeo, ejecutado en el VPS por ssh."""
    try:
        r = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', VPS_HOST, 'python3 -'],
            input=PROBE, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {'error': 'ssh-timeout'}
    for linea in (r.stdout or '').splitlines():
        if linea.startswith('PROBE:'):
            try:
                return json.loads(linea[len('PROBE:'):])
            except Exception:
                break
    return {'error': 'sin-respuesta'}


def habilitada(res: dict) -> bool:
    """Solo sirve si podemos leer la ficha: sin descripcion no alimenta el NLP."""
    return res.get('listado') == 200 and res.get('detalle') == 200


def en_cooldown(estado: dict, ip: str) -> bool:
    ultima = (estado.get(ip) or {}).get('ultima_corrida')
    if not ultima:
        return False
    try:
        falta = datetime.fromisoformat(ultima) + timedelta(hours=COOLDOWN_HORAS) - datetime.now()
    except Exception:
        return False
    if falta.total_seconds() > 0:
        log(f"  {ip}: en cooldown, faltan {falta.total_seconds()/3600:.0f}h")
        return True
    return False


def proximo_offset(estado: dict, ip: str) -> int:
    off = (estado.get(ip) or {}).get('proximo_offset', 0)
    return 0 if off >= total_keywords() else off


def avanzar(estado: dict, ip: str, offset: int) -> None:
    nuevo = offset + MAX_KEYWORDS
    if nuevo >= total_keywords():
        nuevo = 0
        log(f"  {ip}: tramo completo, la proxima vuelve al principio")
    estado.setdefault(ip, {})
    estado[ip]['ultima_corrida'] = datetime.now().isoformat()
    estado[ip]['proximo_offset'] = nuevo
    guardar_estado(estado)


def lanzar_local(offset: int, dry_run: bool) -> None:
    """Encola el comando para que lo tome el poller local."""
    cfg = json.loads((PROJECT_ROOT / "config" / "supabase_config.json").read_text())
    client = create_client(cfg['url'], cfg['service_role_key'])

    en_curso = client.table('pipeline_commands').select('id') \
        .eq('comando', 'scrape_indeed') \
        .in_('estado', ['pendiente', 'ejecutando']).limit(1).execute()
    if en_curso.data:
        log("  local: ya hay un scrape_indeed pendiente/ejecutando")
        return

    if dry_run:
        log(f"  [DRY-RUN] local: encolaria scrape_indeed (offset {offset})")
        return

    r = client.table('pipeline_commands').insert({
        'comando': 'scrape_indeed',
        'estado': 'pendiente',
        'params': {'motivo': 'desbloqueo detectado', 'offset': offset},
        'creado_por': 'check-indeed-unblock',
    }).execute()
    log(f"  local: scrape_indeed encolado ({r.data[0]['id']})")


def lanzar_vps(offset: int, dry_run: bool) -> None:
    cmd = (f"cd /opt/mol && nohup setsid python3 scripts/scraping/run_indeed_vps.py "
           f"--offset {offset} --max-keywords {MAX_KEYWORDS} --delay 5 --detail-delay 8 "
           f"> /tmp/indeed_auto_$(date +%Y%m%d_%H%M).log 2>&1 < /dev/null &")
    if dry_run:
        log(f"  [DRY-RUN] vps: {cmd}")
        return
    ya = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', VPS_HOST,
                         'pgrep -f "[r]un_indeed_vps" >/dev/null && echo SI || echo NO'],
                        capture_output=True, text=True, timeout=60)
    if 'SI' in (ya.stdout or ''):
        log("  vps: ya hay una corrida en curso")
        return
    subprocess.run(['ssh', '-o', 'ConnectTimeout=15', VPS_HOST, cmd],
                   capture_output=True, text=True, timeout=90)
    log(f"  vps: corrida lanzada (tramo {offset + 1}-{offset + MAX_KEYWORDS})")


def main():
    parser = argparse.ArgumentParser(description="Vigila el desbloqueo de Indeed (local + VPS)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--solo-chequear", action="store_true",
                        help="Reporta el estado de las dos IPs y no lanza nada")
    args = parser.parse_args()

    estado = cargar_estado()

    resultados = {'local': probe_local(), 'vps': probe_vps()}
    for ip, res in resultados.items():
        detalle = res.get('detalle')
        listado = res.get('listado')
        if res.get('error'):
            log(f"{ip:5}: ERROR {res['error']}")
        elif habilitada(res):
            log(f"{ip:5}: HABILITADA (listado 200, ficha 200)")
        elif listado == 200:
            log(f"{ip:5}: solo listado (ficha={detalle}) — presupuesto de fichas agotado")
        elif listado == 401:
            log(f"{ip:5}: pide login (401) — bloqueo duro")
        else:
            log(f"{ip:5}: bloqueada (listado={listado})")

    if args.solo_chequear:
        return

    for ip in ('vps', 'local'):   # el VPS primero: no depende de esta maquina
        if not habilitada(resultados[ip]):
            continue
        if en_cooldown(estado, ip):
            continue
        offset = proximo_offset(estado, ip)
        log(f"{ip}: lanzando corrida desde keyword {offset + 1}")
        if ip == 'vps':
            lanzar_vps(offset, args.dry_run)
        else:
            lanzar_local(offset, args.dry_run)
        if not args.dry_run:
            avanzar(estado, ip, offset)
        return

    log("Ninguna IP habilitada para bajar fichas — no se lanza nada")


if __name__ == "__main__":
    main()
