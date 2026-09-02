"""Falsos negativos: duplicados que la heuristica pierde por titulo distinto."""
import sqlite3, re, json, random, difflib, unicodedata
from collections import defaultdict
from datetime import date
random.seed(3)
def norm(s):
    if not s: return ''
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r'\b(s\.?a\.?s?|s\.?r\.?l\.?|sa|srl|sas|ltda|inc|corp|group|grupo|argentina|arg)\b','',s)
    s=re.sub(r'[^a-z0-9 ]',' ',s); return re.sub(r'\s+',' ',s).strip()
def d(x):
    try: return date(*map(int,x.split('-')))
    except Exception: return None

c=sqlite3.connect('file:database/bumeran_scraping.db?mode=ro',uri=True)
rows=list(c.execute("""SELECT id_oferta,portal,titulo,empresa,date(COALESCE(fecha_publicacion_iso,scrapeado_en))
  FROM ofertas WHERE scrapeado_en >= date('now','-60 day') AND empresa IS NOT NULL AND TRIM(empresa)<>''"""))
bum=defaultdict(list)
for i,p,t,e,f in rows:
    if p=='bumeran': bum[norm(e)].append((i,t,f))

# 30 ofertas CT cuya empresa TIENE presencia en bumeran (si no, no hay nada que encontrar)
ct=[r for r in rows if r[1]=='computrabajo' and norm(r[3]) in bum]
print(f'ofertas CT (60d) con empresa presente tambien en Bumeran: {len(ct)}')
sel=random.sample(ct,min(30,len(ct)))
exactos=0; casi=0; nada=0; casos=[]
for i,p,t,e,f in sel:
    cands=bum[norm(e)]
    mejor=None
    for bi,bt,bf in cands:
        da,db=d(f),d(bf)
        if da and db and abs((da-db).days)>7: continue
        s=difflib.SequenceMatcher(None,norm(t),norm(bt)).ratio()
        if mejor is None or s>mejor[0]: mejor=(s,bi,bt,bf)
    if mejor is None: nada+=1; continue
    s,bi,bt,bf=mejor
    if s>=0.999: exactos+=1
    elif s>=0.60:
        casi+=1
        casos.append({'ct_id':i,'ct_titulo':t,'bum_id':bi,'bum_titulo':bt,'empresa':e,'sim':round(s,2)})
    else: nada+=1
print(f'  match de TITULO EXACTO (lo que la heuristica ya captura): {exactos}')
print(f'  match PARCIAL 0.60-0.99 (FALSO NEGATIVO de la heuristica): {casi}')
print(f'  sin candidato en ventana / titulo muy distinto: {nada}')
print()
print('=== ejemplos de falsos negativos (titulos distintos, misma empresa y fecha) ===')
for x in sorted(casos,key=lambda y:-y['sim'])[:12]:
    print(f"  sim={x['sim']} emp={x['empresa'][:28]!r}")
    print(f"     CT : {x['ct_titulo'][:70]!r}")
    print(f"     BUM: {x['bum_titulo'][:70]!r}")
json.dump(casos, open(f'{__import__("os").path.dirname(__file__)}/falsos_negativos.json','w'), ensure_ascii=False, indent=1)
