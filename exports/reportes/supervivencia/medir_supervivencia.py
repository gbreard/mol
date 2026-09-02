#!/usr/bin/env python3
"""Curva de supervivencia Bumeran/ZonaJobs via searchV2 (la API que ya usa el scraper).

El HTML de detalle NO sirve: ambos portales son SPA y devuelven el mismo shell
(~63 KB, sin <title>, sin JSON-LD) para avisos vivos y caidos. La unica senal
disponible es la PRESENCIA EN EL INDICE de busqueda.

Clasificacion:
  VIVA    -> el id aparece entre los resultados de buscar su titulo
  CAIDA   -> la busqueda devolvio menos resultados que el tope y el id no esta
             (busqueda exhaustiva para ese query: si estuviera publicado, estaria)
  AMBIGUA -> la busqueda llego al tope de resultados y el id no aparece: podria
             estar mas alla del tope. No se puede afirmar que cayo.
"""
import json, sys, time, uuid, random
import requests

CFG = {'bumeran': ('https://www.bumeran.com.ar', 'BMAR'),
       'zonajobs': ('https://www.zonajobs.com.ar', 'ZJAR')}
PAGE_SIZE = 100
SP = '/tmp/claude-1000/-mnt-d-OEDE-Webscrapping/15628eef-4c97-4f0f-b1a3-1ffa6ee67ffb/scratchpad'
MUESTRA = '/mnt/d/OEDE/Webscrapping/exports/reportes/supervivencia/muestra.json'


def headers(base, site):
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'es-AR,es;q=0.9',
            'Content-Type': 'application/json',
            'Referer': base + '/empleos-busqueda-ofertas.html', 'Origin': base,
            'x-site-id': site, 'x-pre-session-token': str(uuid.uuid4())}


def clasificar(sess, api, h, oferta):
    titulo = (oferta['titulo'] or '').strip()
    if not titulo:
        return {'clase': 'AMBIGUA', 'motivo': 'sin titulo en BD', 'n_resultados': None}
    payload = {'pageSize': PAGE_SIZE, 'page': 0, 'sort': 'RELEVANCE', 'query': titulo[:60]}
    try:
        r = sess.post(api, json=payload, headers=h, timeout=25)
        if r.status_code != 200:
            return {'clase': 'AMBIGUA', 'motivo': f'HTTP {r.status_code}', 'n_resultados': None}
        d = r.json()
        cont = d.get('content') or d.get('avisos') or []
        ids = {str(x.get('id')) for x in cont if isinstance(x, dict)}
        n = len(ids)
        if str(oferta['id_oferta']) in ids:
            return {'clase': 'VIVA', 'motivo': 'id presente en el indice', 'n_resultados': n}
        if n >= PAGE_SIZE:
            return {'clase': 'AMBIGUA', 'motivo': f'tope de {PAGE_SIZE} resultados alcanzado',
                    'n_resultados': n}
        return {'clase': 'CAIDA', 'motivo': f'ausente entre {n} resultados', 'n_resultados': n}
    except Exception as e:
        return {'clase': 'AMBIGUA', 'motivo': f'{type(e).__name__}', 'n_resultados': None}


if __name__ == '__main__':
    portal = sys.argv[1]
    base, site = CFG[portal]
    api = base + '/api/avisos/searchV2'
    h = headers(base, site)
    sess = requests.Session()
    muestra = json.load(open(MUESTRA))[portal]
    res = []
    print(f'=== {portal}: {len(muestra)} ofertas ===', flush=True)
    for i, o in enumerate(muestra, 1):
        c = clasificar(sess, api, h, o)
        r = {**o, **c}
        res.append(r)
        print(f"[{i:>3}/{len(muestra)}] {o['bucket']:<8} {o['id_oferta']:<12} "
              f"{c['clase']:<8} n={str(c['n_resultados']):<5} {c['motivo'][:40]}", flush=True)
        time.sleep(2 + random.uniform(0, 2))
    json.dump(res, open(f'{SP}/resultado_{portal}.json', 'w'), ensure_ascii=False, indent=1)
    print(f'--- guardado en {SP}/resultado_{portal}.json')
