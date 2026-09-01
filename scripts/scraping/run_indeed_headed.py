#!/usr/bin/env python3
"""
Indeed Argentina - Runner HEADED (local, bajo xvfb)
===================================================

Corre el motor headed (IndeedScraperHeaded) sobre un tramo de keywords por
`proximo_offset` del state-file, mapea e inserta en la MISMA BD y con el MISMO
esquema que run_indeed_vps.py (compat total con el pipeline).

DEBE correr bajo un display:
    xvfb-run -a /usr/bin/python3 scripts/scraping/run_indeed_headed.py [...]

Modo tramo diario (produccion):
    xvfb-run -a /usr/bin/python3 scripts/scraping/run_indeed_headed.py --max-keywords 90

Modo prototipo / gate (corrida real contra BD, no avanza el offset):
    xvfb-run -a /usr/bin/python3 scripts/scraping/run_indeed_headed.py \
        --max-keywords 20 --no-advance --prototipo

D1: el preflight NO-GO loggea fecha+motivo en el state-file (ultimo_nogo /
    ultimo_nogo_motivo). En GO se limpian.
"""

import sys
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "indeed" / "scrapers"))
sys.path.insert(0, str(BASE_DIR / "scripts" / "scraping"))
sys.path.insert(0, str(BASE_DIR))

from indeed_scraper_headed import IndeedScraperHeaded          # noqa: E402
from run_indeed_vps import mapear_oferta_para_bd, insertar_en_bd  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_DB = str(BASE_DIR / "database" / "bumeran_scraping.db")
DEFAULT_STATE = str(BASE_DIR / "data" / "indeed_scraping_state.json")
KEYWORDS_FILE = str(BASE_DIR / "config" / "scraping" / "master_keywords.json")


def cargar_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def guardar_state(path: str, state: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


def total_keywords() -> int:
    data = json.loads(Path(KEYWORDS_FILE).read_text(encoding='utf-8'))
    kws = data.get('estrategias', {}).get('exhaustiva', {}).get('keywords', [])
    return len([k for k in kws if k.strip()])


def registrar_nogo(state_path: str, state: dict, motivo: str) -> None:
    """D1: preserva 'desde cuando esta bloqueado'."""
    loc = state.setdefault('local', {})
    if not loc.get('ultimo_nogo'):
        loc['ultimo_nogo'] = datetime.now().isoformat()
    loc['ultimo_nogo_motivo'] = motivo
    guardar_state(state_path, state)


def limpiar_nogo(state: dict) -> None:
    loc = state.setdefault('local', {})
    loc.pop('ultimo_nogo', None)
    loc.pop('ultimo_nogo_motivo', None)


def main():
    ap = argparse.ArgumentParser(description="Indeed headed runner (local, xvfb)")
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--state', default=DEFAULT_STATE)
    ap.add_argument('--offset', type=int, default=None, help='override de proximo_offset')
    ap.add_argument('--max-keywords', type=int, default=90)
    ap.add_argument('--fromage', type=int, default=14)
    ap.add_argument('--delay', type=float, default=5.0)
    ap.add_argument('--detail-delay', type=float, default=4.0)
    ap.add_argument('--max-fichas', type=int, default=900)
    ap.add_argument('--no-advance', action='store_true', help='no mover proximo_offset (prototipo)')
    ap.add_argument('--dry-run', action='store_true', help='no inserta en BD')
    ap.add_argument('--headless', action='store_true', help='SOLO debug: forzar headless (se bloquea)')
    ap.add_argument('--prototipo', action='store_true', help='imprime metricas del gate + D2')
    args = ap.parse_args()

    state = cargar_state(args.state)
    total = total_keywords()
    offset = args.offset if args.offset is not None else (state.get('local', {}) or {}).get('proximo_offset', 0)
    if offset >= total:
        offset = 0

    logger.info("=" * 60)
    logger.info(f"Indeed HEADED runner — tramo {offset + 1}..{offset + args.max_keywords} de {total}")
    logger.info(f"BD: {args.db}")
    logger.info("=" * 60)

    scraper = IndeedScraperHeaded(
        delay=args.delay, detail_delay=args.detail_delay, fetch_details=True,
        max_fichas=args.max_fichas, headless=args.headless,
    )

    ofertas = scraper.scrape_with_keywords_file(
        KEYWORDS_FILE, estrategia='exhaustiva', fromage=args.fromage,
        max_keywords=args.max_keywords, offset=offset,
    )

    st = scraper.stats

    # D1: NO-GO
    if scraper.preflight_ok is False:
        registrar_nogo(args.state, state, scraper.nogo_motivo or 'desconocido')
        logger.error(f"NO-GO ({scraper.nogo_motivo}). Nada que insertar. State actualizado.")
        _print_resumen(args, offset, ofertas, st, gate=None, insertadas=0)
        return

    # GO: limpiar marca de bloqueo
    limpiar_nogo(state)

    # insertar
    insertadas = 0
    if ofertas and not args.dry_run:
        mapeadas = [mapear_oferta_para_bd(o) for o in ofertas if o]
        mapeadas = [m for m in mapeadas if m]
        res = insertar_en_bd(mapeadas, args.db)
        insertadas = res['insertadas']
        logger.info(f"Insertadas={res['insertadas']} dup={res['duplicadas']} err={res['errores']} "
                    f"total_indeed={res['total_indeed']}")
    elif args.dry_run:
        logger.info("DRY-RUN: no se inserta")

    # avanzar offset (produccion)
    if not args.no_advance and not args.dry_run:
        nuevo = offset + args.max_keywords
        if nuevo >= total:
            nuevo = 0
        loc = state.setdefault('local', {})
        loc['ultima_corrida'] = datetime.now().isoformat()
        loc['proximo_offset'] = nuevo
    guardar_state(args.state, state)

    gate = _gate(ofertas, st) if args.prototipo else None
    _print_resumen(args, offset, ofertas, st, gate=gate, insertadas=insertadas)


def _gate(ofertas, st) -> dict:
    tarjetas = st['tarjetas_unicas'] or 1
    con_desc = st['con_descripcion']
    rendimiento = con_desc / tarjetas
    nav = st['nav_total'] or 1
    fallo = (st['challenges'] + st['blocked']) / nav
    minutos = st['elapsed_seg'] / 60.0
    # Presupuesto de tiempo escalado por Nº de keywords (preserva 20kw<=25min;
    # 90kw<=112.5min < 2h). Evita el "GO":false engañoso en tramos grandes.
    budget_min = round(max(st['keywords'], 1) * 1.25, 1)
    # D2 sobre las ofertas conservadas (con descripcion)
    n = len(ofertas) or 1
    con_jsonld = sum(1 for o in ofertas if o.get('_jsonld'))
    f_jsonld = sum(1 for o in ofertas if o.get('_fecha_source') == 'jsonld')
    f_listado = sum(1 for o in ofertas if o.get('_fecha_source') == 'listado')
    f_none = sum(1 for o in ofertas if o.get('_fecha_source') == 'none')
    return {
        'rendimiento': round(rendimiento, 3), 'rendimiento_ok': rendimiento >= 0.75,
        'con_descripcion': con_desc, 'tarjetas_unicas': st['tarjetas_unicas'],
        'fallo_challenge_blocked': round(fallo, 3), 'fallo_ok': fallo < 0.15,
        'minutos': round(minutos, 1), 'tiempo_budget_min': budget_min,
        'tiempo_ok': minutos <= budget_min,
        # D2:
        'pct_con_jsonld': round(con_jsonld / n, 3),
        'pct_con_fecha': round((f_jsonld + f_listado) / n, 3),
        'pct_fecha_jsonld': round(f_jsonld / n, 3),
        'pct_fecha_listado': round(f_listado / n, 3),
        'pct_sin_fecha': round(f_none / n, 3),
        'GO': (rendimiento >= 0.75) and (fallo < 0.15) and (minutos <= budget_min),
    }


def _print_resumen(args, offset, ofertas, st, gate, insertadas):
    print("\n" + "=" * 60)
    print("RESUMEN INDEED HEADED")
    print("=" * 60)
    print(json.dumps({
        'tramo_desde': offset + 1, 'max_keywords': args.max_keywords,
        'keywords_corridas': st['keywords'], 'tarjetas_unicas': st['tarjetas_unicas'],
        'fichas_intentadas': st['fichas_intentadas'], 'con_descripcion': st['con_descripcion'],
        'insertadas_bd': insertadas,
        'nav_total': st['nav_total'], 'challenges': st['challenges'], 'blocked': st['blocked'],
        'elapsed_seg': st['elapsed_seg'],
    }, indent=2, ensure_ascii=False))
    if gate is not None:
        print("\n--- GATE + D2 ---")
        print("GATE:" + json.dumps(gate, ensure_ascii=False))


if __name__ == '__main__':
    main()
