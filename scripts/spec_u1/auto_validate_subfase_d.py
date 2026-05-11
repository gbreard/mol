#!/usr/bin/env python3
"""
SPEC U-1 v3.1 sub-fase D — Tarea 4: Auto-validación con criterio B endurecido.

Buckets:
  1. validado_claude_subfaseD     — invariantes 1-3 OK + ISCO igual + label igual
  2. pendiente_humano_subfaseD    — invariantes 1-3 OK + ISCO igual + label DIFERENTE
                                    + bandera 'sub_ocupacion_bizarra_revisar' en notas_revision
  3. pendiente_humano_subfaseD    — ISCO post != ISCO pre (cambio de ocupación)
  4. pendiente_humano_subfaseD    — falla algún invariante (uri_no_canonica / label_drift_canonico /
                                    uri_vacia_residual)
  5. en_revision (sin tocar)      — las 7 sub-ofertas multi-position skipped_no_nlp

Lee log estructurado de Tarea 3 + valida invariantes contra catálogo ESCO + persiste
estado nuevo en BD producción.

Uso:
  python3 scripts/spec_u1/auto_validate_subfase_d.py
"""
import sys
import json
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path('/mnt/d/OEDE/Webscrapping')
DB_PATH = ROOT / 'database/bumeran_scraping.db'
LOG_REPROC = ROOT / 'logs/spec_u1_subfase_D_reprocesamiento_20260505_185426.log'
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_LOG = ROOT / f'logs/spec_u1_subfase_D_autovalidate_{TS}.log'
OUT_SUMMARY = ROOT / f'logs/spec_u1_subfase_D_autovalidate_summary_{TS}.json'


def normalize_label(s):
    """Normaliza para comparación: lower + sin acentos + strip."""
    if not s:
        return ''
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s


def main():
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    fh = open(OUT_LOG, 'w', encoding='utf-8')

    # 1. Cargar offers del log de Tarea 3
    print(f"Leyendo log de reprocesamiento: {LOG_REPROC}")
    offers = []
    skipped = []
    with open(LOG_REPROC) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get('event') != 'offer':
                continue
            if d.get('status') == 'ok':
                offers.append(d)
            elif d.get('status') == 'skipped_no_nlp':
                skipped.append(d)

    print(f"Offers ok: {len(offers)}  skipped: {len(skipped)}")

    # 2. Cargar catálogo ESCO completo en memoria
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    print("Cargando catálogo ESCO en memoria...")
    uri_to_occupation = {}
    for r in con.execute("SELECT occupation_uri, preferred_label_es FROM esco_occupations"):
        if r['occupation_uri']:
            uri_to_occupation[r['occupation_uri']] = {
                'preferred_label': r['preferred_label_es'] or '',
                'preferred_norm': normalize_label(r['preferred_label_es'] or ''),
                'alt_norms': set(),
            }
    print(f"  preferred_label cargados: {len(uri_to_occupation)}")

    for r in con.execute("SELECT occupation_uri, label FROM esco_occupation_alternative_labels"):
        if r['occupation_uri'] in uri_to_occupation:
            uri_to_occupation[r['occupation_uri']]['alt_norms'].add(normalize_label(r['label'] or ''))
    n_alt = sum(len(o['alt_norms']) for o in uri_to_occupation.values())
    print(f"  alt_labels cargados: {n_alt}")

    # 3. Clasificar cada offer
    buckets = {
        'b1_validado_claude_subfaseD': [],
        'b2_sub_ocupacion_bizarra': [],
        'b3_cambio_isco': [],
        'b4_uri_no_canonica': [],
        'b4_label_drift_canonico': [],
        'b4_uri_vacia_residual': [],
    }

    for d in offers:
        uri_post = d.get('uri_post') or ''
        label_post = d.get('label_post') or ''
        label_pre = d.get('label_pre') or ''
        isco_post = d.get('isco_post') or ''
        isco_pre = d.get('isco_pre') or ''
        cambio_isco = (isco_pre or '') != (isco_post or '')

        # Invariante 1: URI poblada
        if not uri_post:
            buckets['b4_uri_vacia_residual'].append(d)
            continue

        # Invariante 2: URI canónica (en esco_occupations)
        cat = uri_to_occupation.get(uri_post)
        if cat is None:
            buckets['b4_uri_no_canonica'].append(d)
            continue

        # Invariante 3: label_post coincide con preferred o alt del catálogo
        label_post_norm = normalize_label(label_post)
        label_match = (label_post_norm == cat['preferred_norm']) or (label_post_norm in cat['alt_norms'])
        # Comparar también la primera variante género: "X/Y" → comparar contra la izquierda y la derecha
        if not label_match and '/' in cat['preferred_label']:
            for parte in cat['preferred_label'].split('/'):
                if normalize_label(parte) == label_post_norm:
                    label_match = True
                    break
        if not label_match and '/' in label_post:
            for parte in label_post.split('/'):
                pn = normalize_label(parte)
                if pn == cat['preferred_norm'] or pn in cat['alt_norms']:
                    label_match = True
                    break
        if not label_match:
            buckets['b4_label_drift_canonico'].append(d)
            continue

        # Invariantes 1-3 OK. Ahora determinar bucket 1 / 2 / 3
        if cambio_isco:
            buckets['b3_cambio_isco'].append(d)
            continue

        # ISCO igual. Comparar label pre vs post (criterio B endurecido)
        if normalize_label(label_pre) == normalize_label(label_post):
            buckets['b1_validado_claude_subfaseD'].append(d)
        else:
            buckets['b2_sub_ocupacion_bizarra'].append(d)

    # 4. Persistir estados en BD producción
    print("\nPersistiendo estados en BD producción...")
    write_con = sqlite3.connect(str(DB_PATH))
    now_iso = datetime.now().isoformat()

    n_persistidos = {}

    # Bucket 1
    for d in buckets['b1_validado_claude_subfaseD']:
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'validado_claude_subfaseD',
                validado_timestamp = ?,
                validado_por = 'claude_subfaseD',
                notas_revision = ?
            WHERE id_oferta = ?
        """, (now_iso, '[SPEC U-1 sub-fase D] auto-validado: URI cubrió hueco sin cambiar label ni ISCO', d['id_oferta']))

    n_persistidos['b1'] = len(buckets['b1_validado_claude_subfaseD'])

    # Bucket 2 — bandera SPEC W
    for d in buckets['b2_sub_ocupacion_bizarra']:
        nota = f"[SPEC U-1 sub-fase D][BANDERA_W: sub_ocupacion_bizarra_revisar] ISCO {d.get('isco_pre')} mantenido pero label drift: '{(d.get('label_pre') or '')[:60]}' → '{(d.get('label_post') or '')[:60]}'"
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_subfaseD',
                notas_revision = ?
            WHERE id_oferta = ?
        """, (nota, d['id_oferta']))
    n_persistidos['b2'] = len(buckets['b2_sub_ocupacion_bizarra'])

    # Bucket 3 — cambio de ISCO
    for d in buckets['b3_cambio_isco']:
        nota = f"[SPEC U-1 sub-fase D][CAMBIO_ISCO] {d.get('isco_pre')} → {d.get('isco_post')} | método: {d.get('method_post')}"
        write_con.execute("""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'pendiente_humano_subfaseD',
                notas_revision = ?
            WHERE id_oferta = ?
        """, (nota, d['id_oferta']))
    n_persistidos['b3'] = len(buckets['b3_cambio_isco'])

    # Bucket 4 — invariantes
    for razon, key in [
        ('uri_no_canonica', 'b4_uri_no_canonica'),
        ('label_drift_canonico', 'b4_label_drift_canonico'),
        ('uri_vacia_residual', 'b4_uri_vacia_residual'),
    ]:
        for d in buckets[key]:
            nota = f"[SPEC U-1 sub-fase D][FALLA_INVARIANTE: {razon}] uri_post='{(d.get('uri_post') or '')[-12:]}' label_post='{(d.get('label_post') or '')[:60]}'"
            write_con.execute("""
                UPDATE ofertas_esco_matching
                SET estado_validacion = 'pendiente_humano_subfaseD',
                    notas_revision = ?
                WHERE id_oferta = ?
            """, (nota, d['id_oferta']))
        n_persistidos[key] = len(buckets[key])

    write_con.commit()
    write_con.close()

    # 5. Summary y dump
    summary = {
        'event': 'summary',
        'timestamp': now_iso,
        'log_input': str(LOG_REPROC),
        'offers_input_ok': len(offers),
        'offers_input_skipped': len(skipped),
        'b1_validado_claude_subfaseD': n_persistidos['b1'],
        'b2_sub_ocupacion_bizarra (bandera SPEC W)': n_persistidos['b2'],
        'b3_cambio_isco': n_persistidos['b3'],
        'b4_uri_no_canonica': n_persistidos['b4_uri_no_canonica'],
        'b4_label_drift_canonico': n_persistidos['b4_label_drift_canonico'],
        'b4_uri_vacia_residual': n_persistidos['b4_uri_vacia_residual'],
        'b5_skipped_multi_position (en_revision intacto)': len(skipped),
        'total_input': len(offers) + len(skipped),
        'total_persistido': sum(n_persistidos.values()),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    # Dump detallado de IDs por bucket
    detail = {key: [d['id_oferta'] for d in offers_in_bucket] for key, offers_in_bucket in buckets.items()}
    detail['b5_skipped'] = [d['id_oferta'] for d in skipped]
    (OUT_LOG.parent / f'spec_u1_subfase_D_buckets_{TS}.json').write_text(json.dumps(detail, ensure_ascii=False))

    # Imprimir summary
    print("\n" + "=" * 70)
    print("SUMMARY TAREA 4")
    print("=" * 70)
    for k, v in summary.items():
        print(f"  {k:50} {v}")

    fh.close()
    return summary, buckets, skipped


if __name__ == '__main__':
    main()
