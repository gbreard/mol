#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC E Fase 1 — Regeneración de embeddings de OCUPACIONES ESCO con texto enriquecido.

Lee:
  - database/embeddings/esco_occupations_full.json (3,046 ocupaciones con esco_code + isco_code)
  - database/embeddings/esco_occupation_skills.json (skills essential + optional por ocupación)

Genera:
  - database/embeddings/enriched/esco_occupations_embeddings.npy (N × 1024 float32)
  - database/embeddings/enriched/esco_occupations_metadata.json (con esco_code como ID primario)
  - Actualiza corpus_manifest.json

NO toca producción (queda en enriched/).

Metadata nuevo pone esco_code como identificador primario; el ISCO se deriva.

Uso:
    python3 scripts/embeddings/build_enriched_occupations.py [--limit N] [--verbose]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def build_enriched_text(occ: dict, skills_rel: dict, isco_labels: dict) -> str:
    """Texto enriquecido para embebber.

    Args:
        occ: registro {uri, esco_code, esco_label, isco_code, isco_label}
        skills_rel: {'essential': [...], 'optional': [...]} para esta ocupación
        isco_labels: dict isco_code → label (para la jerarquía)

    Returns:
        Texto UTF-8.
    """
    partes = []

    label = (occ.get('esco_label') or '').strip()
    esco_code = (occ.get('esco_code') or '').strip()
    if not label:
        return ''

    # Encabezado con ESCO code
    if esco_code:
        partes.append(f'{label} [ESCO {esco_code}]')
    else:
        partes.append(label)

    # Jerarquía ISCO derivada del esco_code
    if esco_code:
        digits = esco_code.split('.')[0]  # primeros 4 dígitos
        isco_4 = digits if len(digits) == 4 else ''
        isco_3 = digits[:3] if len(digits) >= 3 else ''
        isco_2 = digits[:2] if len(digits) >= 2 else ''
        isco_1 = digits[:1] if len(digits) >= 1 else ''

        jerarquia_parts = []
        if isco_1:
            l = isco_labels.get(isco_1, '')
            jerarquia_parts.append(f'{isco_1}{" " + l if l else ""}')
        if isco_2 and isco_2 != isco_1:
            l = isco_labels.get(isco_2, '')
            jerarquia_parts.append(f'{isco_2}{" " + l if l else ""}')
        if isco_4:
            l = isco_labels.get(isco_4, '') or occ.get('isco_label', '')
            jerarquia_parts.append(f'{isco_4}{" " + l if l else ""}')
        if jerarquia_parts:
            partes.append(f'Jerarquía: {" > ".join(jerarquia_parts)}')

    # Top 5 skills esenciales (labels)
    essential = skills_rel.get('essential', [])
    if essential:
        top5 = essential[:5]
        skills_str = '; '.join(s.get('skill_label', '') for s in top5 if s.get('skill_label'))
        if skills_str:
            partes.append(f'Skills esenciales: {skills_str}')

    return '\n'.join(partes)


def build_metadata_record(occ: dict, skills_rel: dict, texto_indexado: str) -> dict:
    """Registro de metadata nuevo — esco_code como identificador primario."""
    esco_code = occ.get('esco_code', '')
    # Jerarquía ISCO derivada
    digits = esco_code.split('.')[0] if esco_code else ''
    isco_4 = digits if len(digits) == 4 else ''
    isco_3 = digits[:3] if len(digits) >= 3 else ''
    isco_2 = digits[:2] if len(digits) >= 2 else ''
    isco_1 = digits[:1] if len(digits) >= 1 else ''

    essential_uris = [s.get('skill_uri', '') for s in skills_rel.get('essential', []) if s.get('skill_uri')]
    optional_uris = [s.get('skill_uri', '') for s in skills_rel.get('optional', []) if s.get('skill_uri')]

    return {
        'uri': occ.get('uri', ''),
        'esco_code': esco_code,
        'esco_label': occ.get('esco_label', ''),
        'label': occ.get('esco_label', ''),  # compat con código viejo
        'isco_4dig': isco_4,
        'isco_3dig': isco_3,
        'isco_2dig': isco_2,
        'isco_1dig': isco_1,
        'isco_code': occ.get('isco_code', isco_4),
        'isco_label': occ.get('isco_label', ''),
        'skills_esenciales_uris': essential_uris,
        'skills_optativas_uris': optional_uris,
        'n_skills_esenciales': len(essential_uris),
        'n_skills_optativas': len(optional_uris),
        'texto_indexado': texto_indexado,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    occ_full_path = ROOT / 'database/embeddings/esco_occupations_full.json'
    occ_skills_path = ROOT / 'database/embeddings/esco_occupation_skills.json'
    out_dir = ROOT / 'database/embeddings/enriched'
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'[build-occ] Leyendo {occ_full_path.name}...')
    with open(occ_full_path) as f:
        occ_data = json.load(f)
    occupations = occ_data['occupations']  # lista
    isco_labels = occ_data.get('isco_labels', {})
    print(f'[build-occ] Ocupaciones: {len(occupations):,}')
    print(f'[build-occ] ISCO labels: {len(isco_labels):,}')

    print(f'[build-occ] Leyendo {occ_skills_path.name}...')
    with open(occ_skills_path) as f:
        occ_skills = json.load(f)['occupation_skills']

    # Procesar
    occupations_sorted = sorted(occupations, key=lambda o: o.get('uri', ''))
    if args.limit:
        occupations_sorted = occupations_sorted[:args.limit]

    textos = []
    metadatos = []
    sin_skills = 0
    for occ in occupations_sorted:
        uri = occ.get('uri', '')
        skills_rel = occ_skills.get(uri, {'essential': [], 'optional': []})
        if not skills_rel.get('essential') and not skills_rel.get('optional'):
            sin_skills += 1
        texto = build_enriched_text(occ, skills_rel, isco_labels)
        textos.append(texto)
        metadatos.append(build_metadata_record(occ, skills_rel, texto))

    print(f'[build-occ] Sin skills asociadas: {sin_skills}/{len(occupations_sorted)}')

    # BGE-M3
    print('[build-occ] Cargando BGE-M3...')
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('BAAI/bge-m3')

    print(f'[build-occ] Generando embeddings...')
    t0 = time.time()
    import numpy as np
    embeddings = model.encode(
        textos,
        normalize_embeddings=True,
        batch_size=args.batch_size,
        show_progress_bar=args.verbose,
    ).astype(np.float32)
    dt = time.time() - t0
    print(f'[build-occ] shape {embeddings.shape} en {dt:.1f}s')

    # Verificar
    assert embeddings.shape[1] == 1024
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)

    # Guardar
    emb_out = out_dir / 'esco_occupations_embeddings.npy'
    meta_out = out_dir / 'esco_occupations_metadata.json'
    np.save(emb_out, embeddings)
    with open(meta_out, 'w', encoding='utf-8') as f:
        json.dump(metadatos, f, ensure_ascii=False, indent=1)

    # Actualizar manifest (mantener skills si ya existe)
    manifest_out = out_dir / 'corpus_manifest.json'
    manifest = {}
    if manifest_out.exists():
        with open(manifest_out) as f:
            manifest = json.load(f)
    manifest['esco_occupations'] = {
        'file': 'esco_occupations_embeddings.npy',
        'shape': list(embeddings.shape),
        'model': 'BAAI/bge-m3',
        'model_revision': '5617a9f61b028005a4858fdac845db406aefb181',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'generated_by': 'LOCAL:spec_e_fase_1',
        'source_table': 'esco_occupations_enriched',
        'source_count': int(embeddings.shape[0]),
        'normalize': True,
        'source_enriched': True,
        'checksum_sha256': sha256_file(emb_out),
        'enrichment_fields': [
            'esco_label_with_code', 'isco_hierarchy_1_2_4', 'top_5_essential_skills',
        ],
    }
    with open(manifest_out, 'w') as f:
        json.dump(manifest, f, indent=2)

    sz_mb = os.path.getsize(emb_out) / 1024 / 1024
    print(f'[build-occ] OK — {sz_mb:.1f} MB embeddings')


if __name__ == '__main__':
    main()
