import sqlite3, re, unicodedata
from collections import defaultdict, Counter

def norm(s):
    if not s: return ''
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
    s = s.lower()
    s = re.sub(r'\b(s\.?a\.?s?|s\.?r\.?l\.?|sa|srl|sas|ltda|inc|corp|group|grupo|argentina|arg)\b','',s)
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    return re.sub(r'\s+',' ',s).strip()

c=sqlite3.connect('file:database/bumeran_scraping.db?mode=ro',uri=True)
filas=list(c.execute("""SELECT id_oferta,portal,titulo,empresa,provincia_normalizada,
    date(fecha_publicacion_iso), date(scrapeado_en) FROM ofertas"""))
print('corpus:', len(filas))

print()
print('=== cobertura de campos por portal ===')
por=defaultdict(lambda: Counter())
for i,p,t,e,pr,fp,se in filas:
    por[p]['n']+=1
    if not e or not e.strip(): por[p]['empresa_vacia']+=1
    if not pr: por[p]['prov_vacia']+=1
    if not fp: por[p]['fecha_pub_vacia']+=1
print(f'{"portal":<14}{"n":>7}{"emp.vacia":>11}{"prov.vacia":>12}{"fpub.vacia":>12}')
for p,v in sorted(por.items(), key=lambda x:-x[1]['n']):
    n=v['n']
    print(f'{p:<14}{n:>7}{v["empresa_vacia"]:>7} ({100*v["empresa_vacia"]/n:>3.0f}%){v["prov_vacia"]:>8} ({100*v["prov_vacia"]/n:>3.0f}%){v["fecha_pub_vacia"]:>8} ({100*v["fecha_pub_vacia"]/n:>3.0f}%)')

# --- duplicacion exacta (titulo+empresa normalizados) entre portales distintos ---
idx=defaultdict(list)
for i,p,t,e,pr,fp,se in filas:
    if not e or not e.strip(): continue
    k=(norm(t), norm(e))
    if not k[0] or not k[1]: continue
    idx[k].append((i,p,pr,fp,se))

pares=Counter(); ofertas_en_dup=defaultdict(set); ejemplos=[]
for k,v in idx.items():
    portales={x[1] for x in v}
    if len(portales)<2: continue
    for a in v:
        for b in v:
            if a[1]<b[1]:
                pares[(a[1],b[1])]+=1
                ofertas_en_dup[a[1]].add(a[0]); ofertas_en_dup[b[1]].add(b[0])
                if len(ejemplos)<400: ejemplos.append((k,a,b))
print()
print('=== DUPLICACION EXACTA (titulo+empresa normalizados), CORPUS COMPLETO ===')
print(f'{"par de portales":<32}{"pares":>8}')
for (a,b),n in pares.most_common():
    print(f'  {a} <-> {b:<18}{n:>8}')
print()
print('ofertas involucradas por portal:')
for p in sorted(ofertas_en_dup, key=lambda x:-len(ofertas_en_dup[x])):
    n=por[p]['n']
    print(f'  {p:<14}{len(ofertas_en_dup[p]):>7} de {n} ({100*len(ofertas_en_dup[p])/n:.1f}%)')
import json
json.dump([{'clave':list(k),'a':list(a),'b':list(b)} for k,a,b in ejemplos],
          open('/tmp/claude-1000/-mnt-d-OEDE-Webscrapping/15628eef-4c97-4f0f-b1a3-1ffa6ee67ffb/scratchpad/ejemplos_exactos.json','w'))
