#!/usr/bin/env python3
"""
Chequea si Indeed volvio a permitir el endpoint de DETALLE (/viewjob) y, si si,
encola una corrida de scraping.

Contexto: el bloqueo de Indeed tiene dos formas distintas.
  (a) fingerprint TLS bloqueado -> 403 en listado Y detalle; se arregla rotando
      fingerprint (ya lo hace indeed_scraper.py solo).
  (b) rate-limit de IP sobre /viewjob -> el LISTADO responde 200 y solo el
      DETALLE da 403, con TODOS los fingerprints. No hay fix por codigo: decae
      con el tiempo. Mientras dure, una corrida solo traeria ofertas sin
      descripcion (inutiles para el NLP), asi que el scraper aborta.

Este chequeo cuesta 2 requests. Corre por cron cada 6h: en cuanto el detalle
responde 200, encola `scrape_indeed` y el poller hace el resto.

Uso:
    python3 scripts/scraping/check_indeed_unblock.py
    python3 scripts/scraping/check_indeed_unblock.py --dry-run
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "01_sources" / "indeed" / "scrapers"))

from curl_cffi import requests as cr           # noqa: E402
from bs4 import BeautifulSoup                  # noqa: E402
from supabase import create_client             # noqa: E402

LISTADO = 'https://ar.indeed.com/jobs?q=cajero&l=Argentina&fromage=14'
HEADERS = {'Accept-Language': 'es-AR,es;q=0.9'}


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def detalle_disponible() -> bool:
    """True si podemos leer la ficha de una oferta (con descripcion)."""
    s = cr.Session(impersonate='firefox135')
    try:
        r = s.get(LISTADO, headers=HEADERS, timeout=25)
    except Exception as e:
        log(f"listado ERROR: {e}")
        return False

    if r.status_code != 200:
        log(f"listado HTTP {r.status_code} — bloqueo amplio, sigue esperando")
        return False

    soup = BeautifulSoup(r.text, 'html.parser')
    jks = [e.get('data-jk') for e in soup.select('[data-jk]') if e.get('data-jk')]
    if not jks:
        log("listado sin job_keys — no se puede evaluar")
        return False

    try:
        d = s.get(f'https://ar.indeed.com/viewjob?jk={jks[0]}',
                  headers={**HEADERS, 'Referer': LISTADO}, timeout=25)
    except Exception as e:
        log(f"detalle ERROR: {e}")
        return False

    if d.status_code != 200:
        log(f"detalle HTTP {d.status_code} — sigue bloqueado")
        return False

    tiene_desc = bool(BeautifulSoup(d.text, 'html.parser').select_one('#jobDescriptionText'))
    log(f"detalle HTTP 200, descripcion={'SI' if tiene_desc else 'NO'}")
    return tiene_desc


def encolar_scraping(dry_run: bool) -> None:
    cfg = json.loads((PROJECT_ROOT / "config" / "supabase_config.json").read_text())
    client = create_client(cfg['url'], cfg['service_role_key'])

    en_curso = client.table('pipeline_commands').select('id') \
        .eq('comando', 'scrape_indeed') \
        .in_('estado', ['pendiente', 'ejecutando']).limit(1).execute()
    if en_curso.data:
        log("ya hay un scrape_indeed pendiente/ejecutando — no encolo otro")
        return

    if dry_run:
        log("[DRY-RUN] encolaria scrape_indeed")
        return

    r = client.table('pipeline_commands').insert({
        'comando': 'scrape_indeed',
        'estado': 'pendiente',
        'params': {'motivo': 'detalle desbloqueado — corrida automatica'},
        'creado_por': 'check-indeed-unblock',
    }).execute()
    log(f"DESBLOQUEADO — scrape_indeed encolado: {r.data[0]['id']}")


def main():
    parser = argparse.ArgumentParser(description="Chequeo de desbloqueo de Indeed")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if detalle_disponible():
        encolar_scraping(args.dry_run)
    else:
        log("Indeed sigue sin permitir el detalle — no se encola nada")


if __name__ == "__main__":
    main()
