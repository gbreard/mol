#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC E Fase 1 — Regeneración de embeddings de SKILLS con texto enriquecido.

Lee los datos ya extraídos del RDF ESCO:
  - database/embeddings/esco_skills_full.json (label + description + L1/L2 + broader + category)
  - database/embeddings/esco_skill_to_occupations.json (relación skill → ocupaciones con esco_code)

Genera:
  - database/embeddings/enriched/esco_skills_embeddings_full.npy (N × 1024 float32)
  - database/embeddings/enriched/esco_skills_metadata_full.json (con esco_codes_aplicable, texto_indexado)
  - database/embeddings/enriched/corpus_manifest.json (con checksum y timestamp)

NO toca producción. Los archivos quedan en enriched/ hasta Fase 3.

Uso:
    python3 scripts/embeddings/build_enriched_embeddings.py [--limit N] [--verbose]
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


def build_enriched_text(skill: dict, occ_relations: list) -> str:
    """Construye el texto enriquecido para embebber.

    Args:
        skill: registro de esco_skills_full.json (uri, label, description, L1, L2,
               category_label, broader_label, type)
        occ_relations: lista de (esco_code, label, relation) desde esco_skill_to_occupations

    Returns:
        Texto enriquecido UTF-8 para BGE-M3.
    """
    partes = []

    label = (skill.get('label') or '').strip()
    if not label:
        return ''
    partes.append(label)

    L1 = skill.get('L1') or ''
    L2 = skill.get('L2') or ''
    cat_label = (skill.get('category_label') or '').strip()
    if L1 and L2 and cat_label:
        partes.append(f'Categoría: {L1}.{L2} {cat_label}')
    elif cat_label:
        partes.append(f'Categoría: {cat_label}')

    broader = (skill.get('broader_label') or '').strip()
    if broader and broader.lower() != label.lower():
        partes.append(f'Tipo general: {broader}')

    # Top 3 ocupaciones essential_for, fallback a optional_for si no hay essential
    essential = [(code, lbl) for code, lbl, rel in occ_relations if rel == 'essential_for']
    optional = [(code, lbl) for code, lbl, rel in occ_relations if rel == 'optional_for']
    top_occs = essential[:3] if essential else optional[:3]
    if top_occs:
        occs_str = '; '.join(f'{lbl} ({code})' for code, lbl in top_occs)
        partes.append(f'Típica en: {occs_str}')

    desc = (skill.get('description') or '').strip()
    if desc:
        partes.append(desc[:500])

    return '\n'.join(partes)


def build_metadata_record(skill: dict, occ_relations: list, texto_indexado: str) -> dict:
    """Construye el registro de metadata nuevo con esco_codes_aplicable."""
    esco_codes = sorted({code for code, _, _ in occ_relations})
    return {
        'uri': skill.get('uri', ''),
        'label': skill.get('label', ''),
        'description': skill.get('description', ''),
        'type': skill.get('type', 'skill'),
        'L1': skill.get('L1', ''),
        'L2': skill.get('L2', ''),
        'category_code': skill.get('category_code', ''),
        'category_label': skill.get('category_label', ''),
        'broader_uri': skill.get('broader_uri', ''),
        'broader_label': skill.get('broader_label', ''),
        'esco_codes_aplicable': esco_codes,
        'n_occupations': len(esco_codes),
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
    parser.add_argument('--limit', type=int, default=None,
                        help='Procesar solo N skills (para pruebas)')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Batch size para BGE-M3')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    skills_full_path = ROOT / 'database/embeddings/esco_skills_full.json'
    s2o_path = ROOT / 'database/embeddings/esco_skill_to_occupations.json'
    out_dir = ROOT / 'database/embeddings/enriched'
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'[build] Leyendo {skills_full_path.name}...')
    with open(skills_full_path) as f:
        skills_data = json.load(f)
    skills = skills_data['skills']
    print(f'[build] Skills disponibles: {len(skills):,}')

    print(f'[build] Leyendo {s2o_path.name}...')
    with open(s2o_path) as f:
        s2o = json.load(f)['skill_to_occupations']

    # Construir mapa skill_uri → [(esco_code, label, relation)]
    from collections import defaultdict
    skill_to_occs = defaultdict(list)
    for sk_uri, data in s2o.items():
        for rel_key, rel_name in (('essential_for', 'essential_for'), ('optional_for', 'optional_for')):
            for occ in data.get(rel_key, []):
                code = occ.get('esco_code', '')
                lbl = occ.get('label', '')
                if code:
                    skill_to_occs[sk_uri].append((code, lbl, rel_name))

    # Ordenar URIs para reproducibilidad
    uris = sorted(skills.keys())
    if args.limit:
        uris = uris[:args.limit]
    print(f'[build] A procesar: {len(uris):,} skills')

    # Construir textos y metadatos
    print('[build] Construyendo textos enriquecidos...')
    textos = []
    metadatos = []
    skills_sin_ocupaciones = 0
    for uri in uris:
        skill = skills.get(uri, {})
        occ_rel = skill_to_occs.get(uri, [])
        if not occ_rel:
            skills_sin_ocupaciones += 1
        texto = build_enriched_text(skill, occ_rel)
        textos.append(texto)
        metadatos.append(build_metadata_record(skill, occ_rel, texto))

    print(f'[build] Skills sin ocupaciones asociadas: {skills_sin_ocupaciones:,} ({skills_sin_ocupaciones*100/max(len(uris),1):.1f}%)')

    # Cargar modelo y generar embeddings
    print('[build] Cargando BGE-M3...')
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('BAAI/bge-m3')

    print(f'[build] Generando embeddings (batch={args.batch_size})...')
    t0 = time.time()
    import numpy as np
    embeddings = model.encode(
        textos,
        normalize_embeddings=True,
        batch_size=args.batch_size,
        show_progress_bar=args.verbose,
    ).astype(np.float32)
    dt = time.time() - t0
    print(f'[build] Embeddings generados: shape {embeddings.shape} en {dt:.1f}s '
          f'({dt/max(len(uris),1)*1000:.1f}ms/skill)')

    # Verificaciones
    assert embeddings.shape[1] == 1024, f'Dimensión inesperada: {embeddings.shape}'
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), f'Norma no unitaria: min={norms.min()}, max={norms.max()}'
    print(f'[build] Verificado: norma unitaria (min={norms.min():.6f}, max={norms.max():.6f})')

    # Guardar archivos
    emb_out = out_dir / 'esco_skills_embeddings_full.npy'
    meta_out = out_dir / 'esco_skills_metadata_full.json'
    print(f'[build] Guardando {emb_out}...')
    np.save(emb_out, embeddings)
    print(f'[build] Guardando {meta_out}...')
    with open(meta_out, 'w', encoding='utf-8') as f:
        json.dump(metadatos, f, ensure_ascii=False, indent=1)

    # Manifest
    manifest_out = out_dir / 'corpus_manifest.json'
    manifest = {
        'esco_skills': {
            'file': 'esco_skills_embeddings_full.npy',
            'shape': list(embeddings.shape),
            'model': 'BAAI/bge-m3',
            'model_revision': '5617a9f61b028005a4858fdac845db406aefb181',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'generated_by': 'LOCAL:spec_e_fase_1',
            'source_table': 'esco_skills_enriched',
            'source_count': int(embeddings.shape[0]),
            'normalize': True,
            'source_enriched': True,
            'checksum_sha256': sha256_file(emb_out),
            'enrichment_fields': [
                'label', 'L1_L2_category', 'broader_label',
                'top_3_occupations_with_esco_code', 'description_500chars',
            ],
        },
    }
    with open(manifest_out, 'w') as f:
        json.dump(manifest, f, indent=2)

    sz_mb = os.path.getsize(emb_out) / 1024 / 1024
    print(f'[build] OK — {sz_mb:.1f} MB embeddings')
    print(f'[build] Checksum: {manifest["esco_skills"]["checksum_sha256"][:16]}...')


if __name__ == '__main__':
    main()
