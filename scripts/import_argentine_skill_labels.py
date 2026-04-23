#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Argentine Skill Labels v1.0
===================================

Inserta los mappings de config/argentine_skills_mapping.json en la tabla
esco_skill_alternative_labels con label_type='argentine_mol'.

Así cuando scripts/inject_skills_from_issues.py busca skills con LIKE en
esco_skill_alternative_labels, encuentra también los términos argentinos.

Uso:
    python scripts/import_argentine_skill_labels.py --dry-run
    python scripts/import_argentine_skill_labels.py
"""
import argparse
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
MAPPING_PATH = BASE_DIR / "config" / "argentine_skills_mapping.json"
LABEL_TYPE = 'argentine_mol'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    mapping = json.load(open(MAPPING_PATH, encoding='utf-8'))
    rows = mapping['mappings']
    print(f"Mappings en JSON: {len(rows)}")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    inserted = 0
    skipped = 0
    for r in rows:
        arg_label = r['arg'].lower().strip()
        uri = r['uri']
        # Verificar URI existe en esco_skills
        c.execute("SELECT 1 FROM esco_skills WHERE skill_uri = ? LIMIT 1", (uri,))
        if not c.fetchone():
            print(f"  [SKIP] URI no existe: {uri} para '{arg_label}'")
            skipped += 1
            continue
        # Verificar no duplicado
        c.execute("""SELECT 1 FROM esco_skill_alternative_labels
                     WHERE skill_uri = ? AND LOWER(label) = ? LIMIT 1""", (uri, arg_label))
        if c.fetchone():
            skipped += 1
            continue

        if not args.dry_run:
            c.execute("""INSERT INTO esco_skill_alternative_labels (skill_uri, label, label_type)
                         VALUES (?, ?, ?)""", (uri, arg_label, LABEL_TYPE))
        inserted += 1

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f"\nInsertados: {inserted}")
    print(f"Saltados (ya existen o URI inválida): {skipped}")
    if args.dry_run:
        print("[DRY-RUN] Sin cambios.")


if __name__ == "__main__":
    main()
