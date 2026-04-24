"""Prototipo SPEC E — comparar embeddings viejos vs enriquecidos sobre caso Cyn.

Paso 1: armar subset de ~500 skills (metalúrgico + plástico + dominios ajenos como control)
Paso 2: generar texto enriquecido (label + L1/L2 + broader + description + ocupaciones)
Paso 3: embeddings con BGE-M3
Paso 4: correr matching sobre ofertas Cyn con ambos sets, comparar top-K
"""
import json, numpy as np, sys, time
from collections import defaultdict
sys.path.insert(0, 'database'); sys.path.insert(0, 'config')

# 1) Cargar fuentes RDF
print('Cargando fuentes RDF extraídas...')
with open('database/embeddings/esco_skills_full.json') as f:
    skills_full = json.load(f)['skills']

with open('database/embeddings/esco_skill_to_occupations.json') as f:
    s2o = json.load(f)['skill_to_occupations']

# Construir mapeos
skill_to_esco_codes = defaultdict(list)  # skill_uri → [(esco_code, label, relation)]
for sk_uri, data in s2o.items():
    for rel in ('essential_for','optional_for'):
        for occ in data.get(rel, []):
            code = occ.get('esco_code','')
            lbl = occ.get('label','')
            if code:
                skill_to_esco_codes[sk_uri].append((code, lbl, rel))

# 2) Seleccionar subset: skills relacionadas a 7214.* (metalúrgico) + 8142.* (plástico) + muestra de otros dominios
def es_dominio(codes, prefijo):
    return any(c.startswith(prefijo) for c, _, _ in codes)

subset_uris = set()
metal_uris = {u for u in skill_to_esco_codes if es_dominio(skill_to_esco_codes[u], '7214')}
plastico_uris = {u for u in skill_to_esco_codes if es_dominio(skill_to_esco_codes[u], '8142')}
# Dominios ajenos para verificar que NO aparezcan
textil_uris = {u for u in skill_to_esco_codes if es_dominio(skill_to_esco_codes[u], '7318')}  # textil
enfermeria_uris = {u for u in skill_to_esco_codes if es_dominio(skill_to_esco_codes[u], '2221')}  # enfermería

print(f'Skills metalúrgicas (7214.*): {len(metal_uris)}')
print(f'Skills plástico (8142.*): {len(plastico_uris)}')
print(f'Skills textiles (7318.*) - dominio ajeno: {len(textil_uris)}')
print(f'Skills enfermería (2221.*) - dominio ajeno: {len(enfermeria_uris)}')

subset_uris = metal_uris | plastico_uris | textil_uris | enfermeria_uris
# También asegurar las que había en BD para poder comparar
offending_uris = set()
# Skills random que Cyn marcó como malas — aseguremos que estén en el subset para comparar
problemas_labels = {
    'producir diseños textiles', 'equipos de acuicultura', 'animación de partículas',
    'estudiar fotografías aéreas', 'principios de la enfermería', 'mecanografiar textos',
    'normas de higiene alimentaria', 'moldear masas', 'manejar perforadoras',
    'quitar tejados', 'evaluar el tratamiento de radioterapia', 'cultivar plancton',
    'fabricación de joyas', 'interpretar idiomas en conferencias',
}
for uri, sk in skills_full.items():
    if sk.get('label','').lower() in problemas_labels:
        offending_uris.add(uri)
subset_uris |= offending_uris
print(f'Skills "ruido" conocido agregadas: {len(offending_uris)}')
print(f'TOTAL subset: {len(subset_uris):,} skills')

# 3) Construir texto enriquecido por skill
def texto_enriquecido(sk_uri):
    """Texto completo para embedder: label + categoría + broader + ocupaciones + descripción."""
    sk = skills_full.get(sk_uri, {})
    partes = []
    label = sk.get('label','').strip()
    if not label: return ''
    partes.append(label)
    
    # Categoría L1/L2
    L1 = sk.get('L1','')
    L2 = sk.get('L2','')
    cat_label = sk.get('category_label','')
    if L1 and L2 and cat_label:
        partes.append(f'Categoría: {L1}.{L2} {cat_label}')
    
    # Broader (skill padre)
    broader = sk.get('broader_label','')
    if broader and broader != label:
        partes.append(f'Tipo general: {broader}')
    
    # Top-3 ocupaciones donde aplica (con esco_code)
    codes = skill_to_esco_codes.get(sk_uri, [])
    # Priorizar essential
    essential = [(c,l) for c,l,r in codes if r == 'essential_for'][:3]
    if essential:
        occ_str = '; '.join(f'{l} ({c})' for c,l in essential)
        partes.append(f'Típica en: {occ_str}')
    
    # Descripción
    desc = sk.get('description','').strip()
    if desc:
        partes.append(desc[:400])  # limitar a 400 chars para no explotar
    
    return '\n'.join(partes)

# Samples del texto enriquecido
print('\n--- Muestras de texto enriquecido ---')
for uri in list(subset_uris)[:3]:
    print(f'\n[{skills_full[uri].get("label","?")[:40]}]')
    print(texto_enriquecido(uri)[:400])

# 4) Generar embeddings
print('\n\nCargando BGE-M3...')
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')

subset_list = sorted(subset_uris)
print(f'Generando embeddings para {len(subset_list)} skills...')
textos_enriquecidos = [texto_enriquecido(u) for u in subset_list]
t0 = time.time()
emb_nuevos = model.encode(textos_enriquecidos, normalize_embeddings=True, show_progress_bar=True, batch_size=32)
print(f'Tiempo: {time.time()-t0:.1f}s')

# Cargar embeddings viejos y subsetar
print('\nCargando embeddings viejos...')
emb_viejos_full = np.load('database/embeddings/esco_skills_embeddings_full.npy')
metadata_old = json.load(open('database/embeddings/esco_skills_metadata_full.json'))
uri_to_idx_old = {m['uri']: i for i, m in enumerate(metadata_old)}

idx_old = [uri_to_idx_old.get(u, -1) for u in subset_list]
missing = [u for u,i in zip(subset_list, idx_old) if i == -1]
print(f'  Faltan en metadata viejo: {len(missing)} / {len(subset_list)}')
# Filtrar a los que estén en ambos
validos = [(u, i, i_old) for i, (u, i_old) in enumerate(zip(subset_list, idx_old)) if i_old != -1]
emb_viejos_sub = np.stack([emb_viejos_full[i_old] for _, _, i_old in validos])
emb_nuevos_sub = np.stack([emb_nuevos[i_new] for _, i_new, _ in validos])
uris_validas = [u for u,_,_ in validos]
labels_validas = [skills_full[u].get('label','') for u in uris_validas]
print(f'Subset alineado: {len(uris_validas)} skills')

# 5) CASO CYN: tareas de operario metalúrgico
print('\n' + '='*75)
print('COMPARACION: Embeddings viejos (solo label) vs Nuevos (enriquecidos)')
print('='*75)

tareas_metal = [
    'Tareas de montaje',
    'Manejo de herramientas manuales', 
    'Conocimiento de soldadura'
]
tareas_plastico = [
    'Operación de maquinaria automática o semi-automática',
    'Manejo u operación de máquinas de estiro-soplado',
    'Procesamiento de plásticos: control de calidad en línea',
]

def top_k(emb_pool, labels_pool, tarea, k=5):
    t_e = model.encode(tarea, normalize_embeddings=True)
    sims = emb_pool @ t_e
    top = np.argsort(sims)[-k:][::-1]
    return [(labels_pool[int(i)], float(sims[int(i)])) for i in top]

for nombre, tareas in [('METALURGICO 7214', tareas_metal), ('PLASTICO 8142', tareas_plastico)]:
    print(f'\n\n=== {nombre} ===')
    for tarea in tareas:
        print(f'\n  Tarea: "{tarea}"')
        print(f'  {"VIEJO (label solo)":50} | NUEVO (enriquecido)')
        v_top = top_k(emb_viejos_sub, labels_validas, tarea, k=5)
        n_top = top_k(emb_nuevos_sub, labels_validas, tarea, k=5)
        for (vl, vs), (nl, ns) in zip(v_top, n_top):
            print(f'  {vs:.3f} {vl[:43]:43} | {ns:.3f} {nl[:50]}')
