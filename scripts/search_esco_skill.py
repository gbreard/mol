#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search ESCO Skills v1.0
=======================

CLI helper para buscar skills ESCO por keywords múltiples.
Útil para mapear skills argentinas a URIs ESCO manualmente.

Uso:
    # Buscar skills que contengan todas las palabras
    python scripts/search_esco_skill.py "manicura" "esmaltado"

    # Ver top N
    python scripts/search_esco_skill.py --top 20 "farmacia" "stock"

    # Buscar en alt labels también
    python scripts/search_esco_skill.py --include-alt "psicotécnico"
"""
import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"


def search(keywords, top=10, include_alt=True):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Construir WHERE: AND de LIKE para cada keyword
    where_parts = []
    params = []
    for kw in keywords:
        where_parts.append("LOWER(preferred_label_es) LIKE ?")
        params.append(f"%{kw.lower()}%")

    # Preferred labels
    sql = f"""SELECT skill_uri, preferred_label_es, 'preferred' AS source
              FROM esco_skills
              WHERE {' AND '.join(where_parts)}
              LIMIT ?"""
    c.execute(sql, params + [top])
    results = list(c.fetchall())

    if include_alt and len(results) < top:
        # Alt labels
        where_alt = []
        params_alt = []
        for kw in keywords:
            where_alt.append("LOWER(al.label) LIKE ?")
            params_alt.append(f"%{kw.lower()}%")
        sql2 = f"""SELECT al.skill_uri, s.preferred_label_es || ' | alt: ' || al.label, 'alt' AS source
                   FROM esco_skill_alternative_labels al
                   JOIN esco_skills s ON s.skill_uri = al.skill_uri
                   WHERE {' AND '.join(where_alt)}
                   LIMIT ?"""
        c.execute(sql2, params_alt + [top - len(results)])
        existing_uris = {r[0] for r in results}
        for row in c.fetchall():
            if row[0] not in existing_uris:
                results.append(row)

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('keywords', nargs='+', help='Palabras que deben aparecer (AND)')
    ap.add_argument('--top', type=int, default=10)
    ap.add_argument('--include-alt', action='store_true', default=True)
    ap.add_argument('--only-preferred', action='store_true')
    args = ap.parse_args()

    results = search(args.keywords, top=args.top, include_alt=(not args.only_preferred))

    if not results:
        print(f"Sin resultados para {args.keywords}")
        return
    for uri, label, src in results:
        tag = '📌' if src == 'preferred' else '~'
        print(f"{tag} [{src:<9}] {label}")
        print(f"  URI: {uri}")


if __name__ == "__main__":
    main()
