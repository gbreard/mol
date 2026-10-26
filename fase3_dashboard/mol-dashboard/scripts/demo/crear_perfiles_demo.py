"""DEMO-MIERCOLES 2.1 — crea los 5 perfiles DEMO por la misma API que usa la UI.

Replica /oficina-empleo/perfiles/nuevo:
  - Vía Ocupación: /api/occupations/search → skills de la ocupación
    (/api/esco-argentino o, si no hay perfil argentino, occupation_full_detail.json),
    con las esenciales pre-tildadas como en OccupationSkillPicker.
  - Vía texto libre: /api/skills-extract-from-text → "Confirmar todas".
  - POST /api/personas → POST /api/perfiles → POST /api/perfiles/{id}/skills.
No corrige lo que devuelve el texto libre: lo deja anotado en la salida.
  --rehacer borra los perfiles DEMO existentes (DELETE /api/perfiles/{id}) antes de crear.

Uso:
  python3 crear_perfiles_demo.py --base https://mol-nextjs.vercel.app --out salida.json
"""
import argparse
import json
import random
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ESCO_SKILL = 'http://data.europa.eu/esco/skill/'
ESCO_OCC = 'http://data.europa.eu/esco/occupation/'
# Niveles variados (sorteo con semilla por DNI); 'experto' habilitado por el SQL 075
NIVELES = ['basico', 'intermedio', 'avanzado', 'experto']
PESOS_NIVEL = [2, 4, 3, 1]
# Perfil realista: la persona destilda ~35% de las esenciales pre-tildadas
PCT_DESTILDADAS = 0.35
OCC_JSON = Path(__file__).resolve().parents[2] / 'public' / 'data' / 'occupation_full_detail.json'

PERFILES = [
    {'dni': 'DEMO-001', 'nombre': 'Demo Soldador', 'ubicacion': 'La Matanza, Buenos Aires',
     'ocupaciones': [('soldador', 'soldador/soldadora')],
     'textos': ['trabajé 6 años como soldador en un taller metalúrgico, leo planos, sueldo con MIG y MAG y armo estructuras metálicas',
                'también hago mantenimiento de las máquinas y uso amoladora y soldadora eléctrica']},
    {'dni': 'DEMO-002', 'nombre': 'Demo Repositora', 'ubicacion': 'Palermo, CABA',
     'ocupaciones': [('reponedor', 'reponedor/reponedora'), ('cajero', 'cajero/cajera')],
     'textos': ['trabajé en un supermercado reponiendo góndolas, controlando vencimientos, atendiendo la caja y cobrando a los clientes',
                'además armaba pedidos y hacía el inventario del depósito']},
    {'dni': 'DEMO-003', 'nombre': 'Demo Albañil', 'ubicacion': 'Córdoba Capital, Córdoba',
     'ocupaciones': [('albañil', 'albañil')],
     'textos': ['soy albañil, levanto paredes de ladrillo, hago revoques y coloco pisos y cerámicos',
                'también preparo la mezcla de cemento y hago contrapisos']},
    {'dni': 'DEMO-004', 'nombre': 'Demo Administrativa', 'ubicacion': 'Rosario, Santa Fe',
     'ocupaciones': [('empleado administrativo', 'empleado administrativo/empleada administrativa')],
     'textos': ['trabajé como auxiliar administrativa, manejo Excel, hago facturación, cargo datos y atiendo clientes por teléfono',
                'también llevaba la agenda, archivaba documentación y hacía pagos a proveedores']},
    {'dni': 'DEMO-005', 'nombre': 'Demo Desarrolladora', 'ubicacion': 'Belgrano, CABA',
     'ocupaciones': [('desarrollador de software', 'desarrollador de software/desarrolladora de software')],
     'textos': ['soy desarrolladora, programo en Python y JavaScript, armo APIs y trabajo con bases de datos SQL',
                'uso Git, escribo tests y trabajo con metodologías ágiles']},
]


def http(base, method, path, body=None, params=None):
    url = base + path + ('?' + urllib.parse.urlencode(params) if params else '')
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.read().decode()[:300]}


_occ_json = None
REHACER = False


def skills_de_ocupacion(base, occ_uri):
    """Igual que getSkillsForOccupation: esenciales ESCO (pre-tildadas) + opcionales, más las
    aprobadas para Argentina (pre-tildadas) que no estén ya en ESCO."""
    global _occ_json
    if _occ_json is None:
        _occ_json = json.loads(OCC_JSON.read_text())
    occ = _occ_json.get(occ_uri.rsplit('/', 1)[-1], {})
    sk = occ.get('skills', {})
    esco = ([{'uri': ESCO_SKILL + s['id'], 'label': s['label'], 'essential': True} for s in sk.get('essential', [])]
            + [{'uri': ESCO_SKILL + s['id'], 'label': s['label'], 'essential': False} for s in sk.get('optional', [])])
    status, data = http(base, 'GET', '/api/esco-argentino', params={'occupation': occ_uri})
    if status != 200 or not data.get('skills_consolidadas'):
        return esco, 'esco'
    vistos = {s['uri'] for s in esco}
    argentinas = []
    for s in data['skills_consolidadas']:
        uri = s.get('uri') or s.get('esco_uri')
        label = s.get('label') or s.get('label_normalized') or s.get('label_original')
        if uri and label and uri not in vistos:
            argentinas.append({'uri': uri, 'label': label,
                               'essential': s.get('source') in ('esco_common', 'mol_approved', 'argentina_approved')})
    return esco + argentinas, 'esco+argentino'


def crear(base, p):
    out = {'dni': p['dni'], 'nombre': p['nombre'], 'ubicacion': p['ubicacion'], 'ocupaciones': [], 'texto_libre': []}
    skills, vistas = [], set()
    rnd = random.Random(p['dni'])

    def agregar(uri, label, source):
        if uri in vistas:
            return
        vistas.add(uri)
        skills.append({'uri': uri, 'label': label, 'source': source})

    ocupaciones = []
    for query, label_esperado in p['ocupaciones']:
        _, res = http(base, 'GET', '/api/occupations/search', params={'q': query, 'limit': 10})
        occ = next((r for r in res.get('results', []) if r['label'] == label_esperado), None)
        if not occ:
            raise SystemExit(f"{p['dni']}: no encontré la ocupación '{label_esperado}' buscando '{query}'")
        occ_skills, fuente = skills_de_ocupacion(base, occ['uri'])
        pre_tildadas = [s for s in occ_skills if s['essential']]
        destildadas = set(rnd.sample(range(len(pre_tildadas)), round(len(pre_tildadas) * PCT_DESTILDADAS)))
        esenciales = [s for i, s in enumerate(pre_tildadas) if i not in destildadas]
        for s in esenciales:
            agregar(s['uri'], s['label'], 'ocupacion')
        ocupaciones.append({'id': occ['id'], 'label': occ['label'], 'isco_code': occ['isco_code']})
        out['ocupaciones'].append({'label': occ['label'], 'isco': occ['isco_code'], 'fuente_skills': fuente,
                                   'skills_ofrecidas': len(occ_skills), 'pre_tildadas': len(pre_tildadas),
                                   'agregadas': len(esenciales)})

    for texto in p['textos']:
        status, ext = http(base, 'POST', '/api/skills-extract-from-text', body={'text': texto})
        nuevas = [r for r in ext.get('results', []) if r['uri'] not in vistas]
        for r in nuevas:
            agregar(r['uri'], r['label'], 'texto')
        out['texto_libre'].append({'texto': texto, 'method': ext.get('method'), 'keywords': ext.get('keywords'),
                                   'competencias': [r['label'] for r in ext.get('results', [])],
                                   'agregadas': [r['label'] for r in nuevas]})

    status, persona = http(base, 'POST', '/api/personas',
                           body={'nombre': p['nombre'], 'dni': p['dni'], 'ubicacion': p['ubicacion']})
    if status not in (200, 201):
        raise SystemExit(f"{p['dni']}: error creando persona {status} {persona}")
    _, existentes = http(base, 'GET', '/api/perfiles', params={'persona_id': persona['id']})
    if REHACER and isinstance(existentes, list):
        for viejo in existentes:
            status, res = http(base, 'DELETE', f"/api/perfiles/{viejo['id']}")
            if status != 200:
                raise SystemExit(f"{p['dni']}: error borrando perfil {viejo['id']} {status} {res}")
        out['borrados'] = len(existentes)
        existentes = []
    if isinstance(existentes, list) and existentes:
        perfil = existentes[0]
        _, detalle = http(base, 'GET', '/api/perfiles', params={'id': perfil['id']})
        if detalle.get('skills'):
            out['perfil_id'] = perfil['id']
            out['nota'] = 'ya existía un perfil con skills para esta persona; no se tocó'
            return out
        out['nota'] = 'se reutilizó un perfil vacío de una corrida anterior'
    else:
        status, perfil = http(base, 'POST', '/api/perfiles', body={'persona_id': persona['id'], 'ocupaciones': ocupaciones})
        if status != 201:
            raise SystemExit(f"{p['dni']}: error creando perfil {status} {perfil}")

    via = {'ocupacion': 'ocupacion', 'texto': 'texto'}
    rows = [{'skill_uri': s['uri'], 'skill_label': s['label'], 'via_captura': via[s['source']],
             'estado': 'confirmada', 'confianza': 0.8, 'nivel': rnd.choices(NIVELES, PESOS_NIVEL)[0], 'certificado': False}
            for s in skills]
    status, res = http(base, 'POST', f"/api/perfiles/{perfil['id']}/skills", body={'skills': rows})
    if status not in (200, 201):
        raise SystemExit(f"{p['dni']}: error guardando skills {status} {res}")

    out.update({'persona_id': persona['id'], 'perfil_id': perfil['id'], 'skills_total': len(rows),
                'skills_por_via': {v: sum(1 for r in rows if r['via_captura'] == v) for v in ('ocupacion', 'texto')},
                'niveles': {n: sum(1 for r in rows if r['nivel'] == n) for n in NIVELES}})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='https://mol-nextjs.vercel.app')
    ap.add_argument('--out', required=True)
    ap.add_argument('--rehacer', action='store_true', help='borra (por la API) los perfiles DEMO existentes y los vuelve a crear')
    ap.add_argument('--solo', help='DNIs a procesar, separados por coma (default: los 5)')
    args = ap.parse_args()
    global REHACER
    REHACER = args.rehacer
    resultados = []
    solo = set(args.solo.split(',')) if args.solo else None
    for p in PERFILES:
        if solo and p['dni'] not in solo:
            continue
        r = crear(args.base.rstrip('/'), p)
        resultados.append(r)
        print(f"{r['dni']}: perfil {r.get('perfil_id')} · {r.get('skills_total', '-')} skills {r.get('skills_por_via', '')} {r.get('nota', '')}",
              file=sys.stderr)
    Path(args.out).write_text(json.dumps(resultados, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
