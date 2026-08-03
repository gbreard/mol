#!/usr/bin/env python3
"""SY-02 parche puntual — inserta en esco_skills las 10 URIs presentes en el
indice de embeddings (14.257) y ausentes del catalogo local (14.247).

Hallazgo del FRENTE F (2026-08-03): las 10 son conceptos ESCO OBSOLETOS
(iso-thes:status=obsolete en esco-v1.2.0.rdf, sin prefLabel es — solo en).
El load original del catalogo las excluyo con razon; el indice de embeddings
las retuvo y siguen atrayendo matches (la dominante, "mobile agriculture":
12.943 filas historicas + 10.230 del lote jul/2026 en ofertas_esco_skills_detalle).

Este parche hace resolver el JOIN (label visible, status='obsolete').
NO es el fix estructural: ese es sacarlas del indice de embeddings y
reconciliar corpus↔catalogo (deuda SY-02, toca matcher → otro frente).

Labels EN y status extraidos del RDF oficial:
/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf
Descripcion y type desde database/embeddings/esco_skills_metadata_full.json.

Idempotente (INSERT OR IGNORE). Uso: python scripts/db/fix_sy02_sync_10uris.py [--dry-run]
"""
import sqlite3, json, argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DB = REPO / 'database' / 'bumeran_scraping.db'
META = REPO / 'database' / 'embeddings' / 'esco_skills_metadata_full.json'

# extraido de esco-v1.2.0.rdf (2026-08-03): las 10 son status=obsolete, label solo EN
SY02 = {
    '68d17d2e-2761-438b-af13-0f8d107720d8': 'mobile agriculture',
    '8135ab3d-23ac-4cc3-bc0d-240e7b19a0f8': 'telehealth',
    '9f728a62-90c6-435e-80c9-4c8d67905eec': 'volunteering and third sector legal frameworks',
    'a11eec60-a39e-4c14-b926-60a356e4a1b6': 'be a role model',
    'a72f6969-d1b9-457e-91ab-c01945dc7920': 'six sigma',
    'ab0d774b-7a45-4c76-817f-cb1e35a28758': 'maritime law',
    'c44a3636-cd3e-41fc-ab05-75622dbd47ec': 'sustainable development goals',
    'cf9c66e0-cb2f-43fd-b5c2-dda1893364a8': 'apply modelling techniques in water engineering',
    'e7abc7da-30ba-46f2-b38c-a61c3d0034c1': 'use hydraulic modelling for water and wastewater management',
    'f2046c50-e9aa-4224-8fc0-ad5fc66e4b0e': 'volunteer management',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    midx = {m['uri']: m for m in json.load(open(META))}
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    antes = cur.execute(
        "SELECT COUNT(*) FROM ofertas_esco_skills_detalle d JOIN esco_skills s ON s.skill_uri = d.esco_skill_uri"
    ).fetchone()[0]
    print(f'filas de skills con JOIN resuelto ANTES: {antes}')

    ins = 0
    for uuid, label_en in SY02.items():
        uri = f'http://data.europa.eu/esco/skill/{uuid}'
        m = midx.get(uri, {})
        if args.dry_run:
            existe = cur.execute('SELECT 1 FROM esco_skills WHERE skill_uri=?', (uri,)).fetchone()
            print(f'  [dry] {uuid[:8]} {"ya existe" if existe else "se insertaria"}: {label_en}')
            continue
        cur.execute(
            '''INSERT OR IGNORE INTO esco_skills
               (skill_uri, skill_uuid, preferred_label_es, description_es, skill_type,
                skill_reusability_level, status)
               VALUES (?,?,?,?,?,?,?)''',
            (uri, uuid, label_en, m.get('description'), m.get('type'),
             m.get('reuse_level'), 'obsolete'))
        ins += cur.rowcount
    if not args.dry_run:
        conn.commit()
        despues = cur.execute(
            "SELECT COUNT(*) FROM ofertas_esco_skills_detalle d JOIN esco_skills s ON s.skill_uri = d.esco_skill_uri"
        ).fetchone()[0]
        print(f'insertadas: {ins}')
        print(f'filas de skills con JOIN resuelto DESPUES: {despues} (+{despues - antes})')
        faltan = cur.execute('''SELECT COUNT(DISTINCT d.esco_skill_uri) FROM ofertas_esco_skills_detalle d
                                LEFT JOIN esco_skills s ON s.skill_uri = d.esco_skill_uri
                                WHERE d.esco_skill_uri IS NOT NULL AND s.skill_uri IS NULL''').fetchone()[0]
        print(f'URIs aun fuera de catalogo (fabricadas historicas, pileta): {faltan}')
    conn.close()


if __name__ == '__main__':
    main()
