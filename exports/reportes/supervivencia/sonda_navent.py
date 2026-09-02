#!/usr/bin/env python3
"""Sonda de taxonomia: como se ve una oferta VIVA vs CAIDA en Bumeran/ZonaJobs.

Solo GET, con pausas. No escribe nada. Prueba dos vias por oferta:
  A) HTML de detalle   (la URL que guarda el scraper)
  B) API searchV2 filtrando por id, que es la via que el scraper YA conoce
Reporta status, redirects, tamano y marcadores de texto, para poder decidir
que senal usar como "baja confirmada".
"""
import json, re, sys, time
import requests

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
HEADERS = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9',
}

# Frases que suelen marcar un aviso dado de baja en plataformas Navent
MARCADORES_BAJA = [
    'no se encuentra disponible', 'ya no está disponible', 'ya no esta disponible',
    'aviso no disponible', 'finalizada', 'finalizado', 'expirada', 'expirado',
    'no encontramos', 'no existe', 'búsqueda finalizada', 'busqueda finalizada',
    'esta oferta ya no', 'aviso expirado', 'página no encontrada',
]
MARCADORES_VIVA = [
    'postularme', 'postularse', 'postulate', 'aplicar a este aviso',
    'descripción del puesto', 'requisitos',
]


def sondear(url, sess):
    r = {'url': url}
    try:
        resp = sess.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        r['status'] = resp.status_code
        r['url_final'] = resp.url
        r['redirigio'] = resp.url.rstrip('/') != url.rstrip('/')
        r['len'] = len(resp.text)
        cuerpo = resp.text.lower()
        r['marcadores_baja'] = [m for m in MARCADORES_BAJA if m in cuerpo]
        r['marcadores_viva'] = [m for m in MARCADORES_VIVA if m in cuerpo]
        m = re.search(r'<title[^>]*>(.*?)</title>', resp.text, re.S | re.I)
        r['title'] = re.sub(r'\s+', ' ', m.group(1)).strip()[:100] if m else ''
        # ¿trae JSON-LD JobPosting? senal fuerte de aviso publicado
        r['jobposting'] = '"@type": "JobPosting"' in resp.text or '"@type":"JobPosting"' in resp.text
    except Exception as e:
        r['status'] = None
        r['error'] = f'{type(e).__name__}: {e}'[:120]
    return r


if __name__ == '__main__':
    portal = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    muestra = json.load(open('/mnt/d/OEDE/Webscrapping/exports/reportes/supervivencia/muestra.json'))[portal]
    # tomar de los extremos: las mas nuevas (probablemente vivas) y las mas viejas
    sel = muestra[:n] + muestra[-n:]
    sess = requests.Session()
    print(f'=== SONDA {portal} — {len(sel)} ofertas (mitad bucket 0-2w, mitad 16+w) ===\n')
    for o in sel:
        d = sondear(o['url'], sess)
        print(f"[{o['bucket']:<8}] {o['id_oferta']}  ult_visto={o['fecha_ultimo_visto']}")
        print(f"    url    : {o['url'][:88]}")
        print(f"    status : {d.get('status')}  redirigio={d.get('redirigio')}  len={d.get('len')}  jobposting={d.get('jobposting')}")
        print(f"    title  : {d.get('title','')[:88]!r}")
        if d.get('redirigio'):
            print(f"    ->     : {d.get('url_final','')[:88]}")
        if d.get('marcadores_baja'):
            print(f"    BAJA?  : {d['marcadores_baja'][:4]}")
        if d.get('marcadores_viva'):
            print(f"    VIVA?  : {d['marcadores_viva'][:4]}")
        if d.get('error'):
            print(f"    ERROR  : {d['error']}")
        print()
        time.sleep(3)
