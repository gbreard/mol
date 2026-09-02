import sqlite3, re, json, random, unicodedata
from collections import defaultdict, Counter
from datetime import date
random.seed(11)

def norm(s):
    if not s: return ''
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r'\b(s\.?a\.?s?|s\.?r\.?l\.?|sa|srl|sas|ltda|inc|corp|group|grupo|argentina|arg)\b','',s)
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def d(x):
    try: return date(*map(int,x.split('-')))
    except Exception: return None

c=sqlite3.connect('file:database/bumeran_scraping.db?mode=ro',uri=True)
filas=list(c.execute("""SELECT id_oferta,portal,titulo,empresa,
   date(COALESCE(fecha_publicacion_iso,scrapeado_en)), substr(COALESCE(descripcion,''),1,200)
   FROM ofertas WHERE scrapeado_en >= date('now','-60 day')"""))
print('corpus ultimos 60 dias:', len(filas))
print('  por portal:', dict(Counter(f[1] for f in filas)))

idx=defaultdict(list)
for i,p,t,e,f,desc in filas:
    if not e or not e.strip(): continue
    k=(norm(t),norm(e))
    if not k[0] or not k[1]: continue
    idx[k].append((i,p,f,t,e,desc))

VENTANA=7
pares=[]; matriz=Counter(); involucradas=defaultdict(set)
for k,v in idx.items():
    for ii in range(len(v)):
        for jj in range(ii+1,len(v)):
            a,b=v[ii],v[jj]
            if a[1]==b[1]: continue                      # mismo portal: no es cross-portal
            da,db=d(a[2]),d(b[2])
            if da and db and abs((da-db).days)>VENTANA: continue
            par=tuple(sorted([a[1],b[1]]))
            matriz[par]+=1
            involucradas[a[1]].add(a[0]); involucradas[b[1]].add(b[0])
            pares.append({'clave_titulo':k[0],'clave_empresa':k[1],
                          'a':{'id':a[0],'portal':a[1],'fecha':a[2],'titulo':a[3],'empresa':a[4],'desc':a[5]},
                          'b':{'id':b[0],'portal':b[1],'fecha':b[2],'titulo':b[3],'empresa':b[4],'desc':b[5]}})
print()
print('=== MATRIZ de duplicacion fuerte (60 dias, |fecha| <= 7d) ===')
for (a,b),n in matriz.most_common():
    print(f'  {a:<14} x {b:<14} {n:>6}')
print(f'  TOTAL pares: {len(pares)}')
print()
tot=Counter(f[1] for f in filas)
print('ofertas involucradas / corpus 60d por portal:')
for p in sorted(involucradas,key=lambda x:-len(involucradas[x])):
    print(f'  {p:<14}{len(involucradas[p]):>6} de {tot[p]:<6} ({100*len(involucradas[p])/tot[p]:.1f}%)')
tot_inv=sum(len(v) for v in involucradas.values())
print(f'  TOTAL         {tot_inv:>6} de {len(filas):<6} ({100*tot_inv/len(filas):.1f}% del corpus reciente)')
json.dump(pares, open(f'{__import__("os").path.dirname(__file__)}/pares_fuertes.json','w'), ensure_ascii=False)
val=random.sample(pares,min(50,len(pares)))
json.dump(val, open(f'{__import__("os").path.dirname(__file__)}/validar_50.json','w'), ensure_ascii=False, indent=1)
print(f'\nguardados {len(pares)} pares; muestra de {len(val)} para validacion manual')
