#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Argentine Skill Labels v1.1
===================================

Inserta los mappings de config/sinonimos_skills_argentinos.json (sección
tareas_a_skills) en la tabla esco_skill_alternative_labels con
label_type='argentine_mol'.

El archivo JSON mapea término_argentino → label_ESCO_es (no URI). Este
script busca la URI de cada label en esco_skills y arma el insert.

Así el diccionario argentino queda disponible en DOS lugares:
  1. config/sinonimos_skills_argentinos.json — usado por skills_implicit_extractor
     durante matching
  2. esco_skill_alternative_labels — usado por inject_skills_from_issues
     durante resolución de issues

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
MAPPING_PATH = BASE_DIR / "config" / "sinonimos_skills_argentinos.json"
LABEL_TYPE = 'argentine_mol'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    mapping = json.load(open(MAPPING_PATH, encoding='utf-8'))
    tareas = mapping.get('tareas_a_skills', {})
    print(f"Términos en tareas_a_skills: {len(tareas)}")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    inserted = 0
    skipped_existing = 0
    skipped_no_uri = 0

    for arg_term, esco_label in tareas.items():
        arg_label = arg_term.lower().strip()
        # Buscar URI por label ESCO
        c.execute("SELECT skill_uri FROM esco_skills WHERE LOWER(preferred_label_es) = ? LIMIT 1",
                  (esco_label.lower(),))
        row = c.fetchone()
        if not row:
            # Intentar en alt_labels (por si el label ya es un alt)
            c.execute("""SELECT skill_uri FROM esco_skill_alternative_labels
                         WHERE LOWER(label) = ? LIMIT 1""", (esco_label.lower(),))
            row = c.fetchone()
        if not row:
            skipped_no_uri += 1
            continue
        uri = row[0]

        # Verificar no duplicado
        c.execute("""SELECT 1 FROM esco_skill_alternative_labels
                     WHERE skill_uri = ? AND LOWER(label) = ? LIMIT 1""", (uri, arg_label))
        if c.fetchone():
            skipped_existing += 1
            continue

        if not args.dry_run:
            c.execute("""INSERT INTO esco_skill_alternative_labels (skill_uri, label, label_type)
                         VALUES (?, ?, ?)""", (uri, arg_label, LABEL_TYPE))
        inserted += 1

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f"\nInsertados: {inserted}")
    print(f"Saltados (ya existen): {skipped_existing}")
    print(f"Saltados (ESCO label no encontrado): {skipped_no_uri}")
    if args.dry_run:
        print("[DRY-RUN] Sin cambios.")


if __name__ == "__main__":
    main()
