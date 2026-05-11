#!/usr/bin/env python3
"""
SPEC U-1 Tarea 4 — Auto-validación C1 con 6 buckets ESCO multi-nivel.

Buckets (orden de evaluación):
  C1-1: misma URI ESCO + invariantes técnicos OK → validado_claude_C1
  C1-5: falla invariantes técnicos → pendiente_humano_C1 + razón
  C1-2a: cluster ESCO propio (Occupation ancestor común en L1-L2) → bandera 'cluster_esco_propio_uri_distinta'
  C1-2b: cluster ISCO 4-dig (IscoGroup C\d{4} común en L2) → bandera 'cluster_isco_4dig_uri_distinta'
  C1-3: ancestor común en L3-L4 (subgrupo) → bandera 'subgrupo_compartido_ocupacion_distinta'
  C1-4: cluster ESCO completamente distinto → pendiente_humano_C1 sin bandera

Set: las 8.179 ofertas con status='ok' del log de re-rematch.
Las 38 skipped_no_nlp quedan en en_revision sin tocar.
"""
import json, re, sqlite3, sys, unicodedata
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path('/mnt/d/OEDE/Webscrapping')
DB_PATH = str(ROOT / 'database/bumeran_scraping.db')
LOG_REMATCH = ROOT / 'logs/spec_u1_C1_re_rematch_20260508_190141.log'
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_LOG = ROOT / f'logs/spec_u1_C1_autovalidate_{TS}.log'
OUT_SUMMARY = ROOT / f'logs/spec_u1_C1_autovalidate_summary_{TS}.json'
OUT_BUCKETS = ROOT / f'logs/spec_u1_C1_buckets_{TS}.json'

ISCO_4DIG_PATTERN = re.compile(r'^C\d{4}$')


def normalize_label(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s


def label_matches_canonical(label_post, cat):
    """label_post coincide con preferred o alt_labels del catálogo."""
    if not cat:
        return False
    label_post_norm = normalize_label(label_post)
    if label_post_norm == cat['preferred_norm']:
        return True
    if label_post_norm in cat['alt_norms']:
        return True
    # Variantes género: "X/Y" — comparar partes
    if '/' in cat['preferred_label']:
        for parte in cat['preferred_label'].split('/'):
            if normalize_label(parte) == label_post_norm:
                return True
    if '/' in label_post:
        for parte in label_post.split('/'):
            pn = normalize_label(parte)
            if pn == cat['preferred_norm'] or pn in cat['alt_norms']:
                return True
    return False


def main():
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    fh = open(OUT_LOG, 'w', encoding='utf-8')

    print(f"=== SPEC U-1 Tarea 4 — Auto-validación C1 ===")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Log: {OUT_LOG}")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    # 1. Cargar catálogo esco_occupations + alt_labels
    print("\nCargando catálogo ESCO...")
    uri_to_cat = {}
    for r in con.execute("SELECT occupation_uri, preferred_label_es FROM esco_occupations"):
        if r['occupation_uri']:
            uri_to_cat[r['occupation_uri']] = {
                'preferred_label': r['preferred_label_es'] or '',
                'preferred_norm': normalize_label(r['preferred_label_es'] or ''),
                'alt_norms': set(),
            }
    for r in con.execute("SELECT occupation_uri, label FROM esco_occupation_alternative_labels"):
        if r['occupation_uri'] in uri_to_cat:
            uri_to_cat[r['occupation_uri']]['alt_norms'].add(normalize_label(r['label'] or ''))
    print(f"  catálogo: {len(uri_to_cat)} URIs canónicas")

    # 2. Cargar ancestros multi-nivel en memoria
    print("Cargando esco_occupation_ancestors...")
    # Para cada occupation_uri, lista de (level, ancestor_uri, type, isco_code)
    anc_by_uri = defaultdict(list)
    for r in con.execute("""
        SELECT occupation_uri, ancestor_uri, ancestor_level, ancestor_type, ancestor_isco_code
        FROM esco_occupation_ancestors
        ORDER BY occupation_uri, ancestor_level
    """):
        anc_by_uri[r['occupation_uri']].append({
            'uri': r['ancestor_uri'],
            'level': r['ancestor_level'],
            'type': r['ancestor_type'],
            'isco_code': r['ancestor_isco_code'],
        })
    print(f"  ancestros: {sum(len(v) for v in anc_by_uri.values())} entradas, {len(anc_by_uri)} ocupaciones")

    # 3. Cargar offers ok del log C1
    print(f"Cargando offers del log re-rematch...")
    offers = []
    with open(LOG_REMATCH) as f:
        for line in f:
            try: d = json.loads(line)
            except: continue
            if d.get('event') == 'offer' and d.get('status') == 'ok':
                offers.append(d)
    print(f"  ofertas con status=ok: {len(offers)}")

    # 4. Helpers para ancestros
    def get_ancestors_set(uri, levels):
        """Set de ancestor_uri en los niveles especificados."""
        result = set()
        for a in anc_by_uri.get(uri, []):
            if a['level'] in levels:
                result.add(a['uri'])
        return result

    def get_ancestors_filtered(uri, levels, type_filter=None, isco_pattern=None):
        """Set de ancestor_uri en niveles, filtrado por tipo y/o pattern del isco_code."""
        result = set()
        for a in anc_by_uri.get(uri, []):
            if a['level'] not in levels:
                continue
            if type_filter and a['type'] != type_filter:
                continue
            if isco_pattern and not (a['isco_code'] and isco_pattern.match(a['isco_code'])):
                continue
            result.add(a['uri'])
        return result

    # 5. Clasificar ofertas en buckets
    buckets = defaultdict(list)
    for d in offers:
        uri_pre = d.get('esco_uri_pre') or ''
        uri_post = d.get('esco_uri_post') or ''
        label_pre = d.get('esco_label_pre') or ''
        label_post = d.get('esco_label_post') or ''
        isco_pre = d.get('_isco_pre')
        isco_post = d.get('_isco_post')

        # Invariantes técnicos
        cat_post = uri_to_cat.get(uri_post)
        canonica_ok = cat_post is not None
        label_ok = canonica_ok and label_matches_canonical(label_post, cat_post)
        uri_post_no_vacia = bool(uri_post)

        # 1) C1-1: misma URI Y invariantes OK
        if uri_post and uri_post == uri_pre and canonica_ok and label_ok:
            buckets['C1-1'].append({**d, 'reason': None})
            continue

        # 2) C1-5: falla invariantes
        if not uri_post_no_vacia:
            buckets['C1-5'].append({**d, 'reason': 'uri_vacia_residual'})
            continue
        if not canonica_ok:
            buckets['C1-5'].append({**d, 'reason': 'uri_no_canonica'})
            continue
        if not label_ok:
            buckets['C1-5'].append({**d, 'reason': 'label_drift_canonico'})
            continue
        # caso edge: uri_post == uri_pre pero solo falla un invariante — caería arriba
        # ahora todas las URIs son distintas

        # Para clusters, calculamos ancestros pre y post
        # Buckets en orden de prioridad:
        # 3) C1-2a: Occupation común en L1-L2
        # Nota: L1 = la propia ocupación. Para que "haya un Occupation común en L1-L2" significa:
        #   ancestor pre tipo Occupation en L1-L2 ∩ ancestor post tipo Occupation en L1-L2 ≠ ∅
        # Esto incluye: post.uri_post == algun_ancestor_pre tipo Occupation, o viceversa.
        anc_pre_occ_l12 = get_ancestors_filtered(uri_pre, [1, 2], type_filter='Occupation')
        anc_post_occ_l12 = get_ancestors_filtered(uri_post, [1, 2], type_filter='Occupation')
        if anc_pre_occ_l12 & anc_post_occ_l12:
            buckets['C1-2a'].append({**d, 'reason': None,
                                      'ancestor_comun': list(anc_pre_occ_l12 & anc_post_occ_l12)[:1]})
            continue

        # 4) C1-2b: IscoGroup 4-dig común en L2
        anc_pre_isco4_l2 = get_ancestors_filtered(uri_pre, [2], type_filter='IscoGroup',
                                                    isco_pattern=ISCO_4DIG_PATTERN)
        anc_post_isco4_l2 = get_ancestors_filtered(uri_post, [2], type_filter='IscoGroup',
                                                     isco_pattern=ISCO_4DIG_PATTERN)
        if anc_pre_isco4_l2 & anc_post_isco4_l2:
            buckets['C1-2b'].append({**d, 'reason': None,
                                      'ancestor_comun': list(anc_pre_isco4_l2 & anc_post_isco4_l2)[:1]})
            continue

        # 5) C1-3: ancestor común en L3-L4 pero NO en L1-L2
        anc_pre_l34 = get_ancestors_set(uri_pre, [3, 4])
        anc_post_l34 = get_ancestors_set(uri_post, [3, 4])
        if anc_pre_l34 & anc_post_l34:
            buckets['C1-3'].append({**d, 'reason': None,
                                    'ancestor_comun': list(anc_pre_l34 & anc_post_l34)[:1]})
            continue

        # 6) C1-4: sin ancestor común en L1-L4
        buckets['C1-4'].append({**d, 'reason': None})

    # 6. Persistir estados en BD
    print("\nPersistiendo estados en BD...")
    write_con = sqlite3.connect(DB_PATH)
    now_iso = datetime.now().isoformat()
    n_persistidos = {}

    # C1-1: validado_claude_C1
    for d in buckets['C1-1']:
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'validado_claude_C1',
                validado_timestamp = ?,
                validado_por = 'claude_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = NULL
            WHERE id_oferta = ?
        """, (now_iso, '[SPEC U-1 C1] auto-validado: misma URI ESCO pre/post + invariantes OK', d['id_oferta']))
    n_persistidos['C1-1'] = len(buckets['C1-1'])

    # C1-2a: pendiente_humano_C1 + bandera 'cluster_esco_propio_uri_distinta'
    for d in buckets['C1-2a']:
        nota = (f"[SPEC U-1 C1][cluster_esco_propio_uri_distinta] URI cambió pero hay Occupation común L1-L2. "
                f"pre='{(d.get('esco_label_pre') or '')[:50]}' post='{(d.get('esco_label_post') or '')[:50]}'")
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = ?
            WHERE id_oferta = ?
        """, (nota, 'cluster_esco_propio_uri_distinta', d['id_oferta']))
    n_persistidos['C1-2a'] = len(buckets['C1-2a'])

    # C1-2b: pendiente_humano_C1 + bandera 'cluster_isco_4dig_uri_distinta'
    for d in buckets['C1-2b']:
        nota = (f"[SPEC U-1 C1][cluster_isco_4dig_uri_distinta] URI cambió, comparten ISCO 4-dig en L2. "
                f"pre='{(d.get('esco_label_pre') or '')[:50]}' post='{(d.get('esco_label_post') or '')[:50]}'")
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = ?
            WHERE id_oferta = ?
        """, (nota, 'cluster_isco_4dig_uri_distinta', d['id_oferta']))
    n_persistidos['C1-2b'] = len(buckets['C1-2b'])

    # C1-3: pendiente_humano_C1 + bandera 'subgrupo_compartido_ocupacion_distinta'
    for d in buckets['C1-3']:
        nota = (f"[SPEC U-1 C1][subgrupo_compartido_ocupacion_distinta] URI cambió, ancestro común L3-L4 (subgrupo ISCO). "
                f"pre='{(d.get('esco_label_pre') or '')[:50]}' post='{(d.get('esco_label_post') or '')[:50]}'")
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = ?
            WHERE id_oferta = ?
        """, (nota, 'subgrupo_compartido_ocupacion_distinta', d['id_oferta']))
    n_persistidos['C1-3'] = len(buckets['C1-3'])

    # C1-4: pendiente_humano_C1 sin bandera
    for d in buckets['C1-4']:
        nota = (f"[SPEC U-1 C1][cluster_distinto] URI cambió, sin ancestro común L1-L4 (cambio de familia ocupacional). "
                f"pre='{(d.get('esco_label_pre') or '')[:50]}' post='{(d.get('esco_label_post') or '')[:50]}'")
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = NULL
            WHERE id_oferta = ?
        """, (nota, d['id_oferta']))
    n_persistidos['C1-4'] = len(buckets['C1-4'])

    # C1-5: pendiente_humano_C1 con razón específica
    for d in buckets['C1-5']:
        nota = f"[SPEC U-1 C1][FALLA_INVARIANTE: {d['reason']}] uri_post='{(d.get('esco_uri_post') or '')[-12:]}' label_post='{(d.get('esco_label_post') or '')[:50]}'"
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_C1',
                notas_revision = ?,
                bandera_spec_w_C1 = NULL
            WHERE id_oferta = ?
        """, (nota, d['id_oferta']))
    n_persistidos['C1-5'] = len(buckets['C1-5'])

    write_con.commit()

    # Razones específicas en C1-5
    razones_c15 = Counter(d['reason'] for d in buckets['C1-5'])

    summary = {
        'event': 'summary',
        'timestamp': now_iso,
        'log_input': str(LOG_REMATCH),
        'offers_input_ok': len(offers),
        'buckets': {
            'C1-1_auto_validado': n_persistidos['C1-1'],
            'C1-2a_cluster_esco_propio_uri_distinta': n_persistidos['C1-2a'],
            'C1-2b_cluster_isco_4dig_uri_distinta': n_persistidos['C1-2b'],
            'C1-3_subgrupo_compartido_ocupacion_distinta': n_persistidos['C1-3'],
            'C1-4_cluster_esco_distinto': n_persistidos['C1-4'],
            'C1-5_falla_invariantes': n_persistidos['C1-5'],
        },
        'C1-5_razones': dict(razones_c15),
        'total_persistido': sum(n_persistidos.values()),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    # Dump de buckets para spot-check posterior
    detail = {k: [d['id_oferta'] for d in v] for k, v in buckets.items()}
    OUT_BUCKETS.write_text(json.dumps(detail, ensure_ascii=False))

    # Imprimir summary
    print()
    print("=" * 70)
    print("SUMMARY TAREA 4 — C1 Auto-validación")
    print("=" * 70)
    for k, v in summary['buckets'].items():
        pct = v * 100 / max(1, len(offers))
        print(f"  {k:48} {v:>5}  ({pct:5.1f}%)")
    print(f"\n  C1-5 razones: {summary['C1-5_razones']}")
    print(f"  Total persistido: {summary['total_persistido']}/{len(offers)}")

    fh.close()
    write_con.close()
    con.close()
    return summary, buckets


if __name__ == '__main__':
    main()
