#!/usr/bin/env python3
"""
Extrae reusability level y green flag de skills ESCO usando SPARQL sobre rdflib.
"""

import rdflib
import json
import os
import time

RDF_PATH = "/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf"

def main():
    print(f"Cargando RDF ({os.path.getsize(RDF_PATH) / 1024 / 1024:.0f} MB)...")
    g = rdflib.Graph()
    start = time.time()
    g.parse(RDF_PATH, format='xml')
    print(f"Cargado en {time.time()-start:.0f}s — {len(g):,} triples")

    # ── Query 1: Reusability levels ───────────────────────────────────────────
    print("\nExtrayendo reusability levels...")
    query_reuse = """
    PREFIX esco: <http://data.europa.eu/esco/model#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?skill ?reuseLevel WHERE {
        ?skill esco:skillReuseLevel ?reuseConcept .
        ?reuseConcept a skos:Concept .
        FILTER(STRSTARTS(STR(?reuseConcept), "http://data.europa.eu/esco/skill-reuse-level/"))
        BIND(REPLACE(STR(?reuseConcept), "http://data.europa.eu/esco/skill-reuse-level/", "") AS ?reuseLevel)
    }
    """

    skills_reuse = {}
    for row in g.query(query_reuse):
        uri = str(row.skill)
        level = str(row.reuseLevel)
        if "/esco/skill/" in uri:
            skills_reuse[uri] = level

    print(f"  Skills con reusability: {len(skills_reuse)}")
    from collections import Counter
    reuse_dist = Counter(skills_reuse.values())
    for level, count in sorted(reuse_dist.items(), key=lambda x: -x[1]):
        print(f"    {level:25} {count:>6}")

    # ── Query 2: Green skills ─────────────────────────────────────────────────
    print("\nExtrayendo green skills...")
    query_green = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?skill WHERE {
        ?skill skos:inScheme <http://data.europa.eu/esco/concept-scheme/green> .
        FILTER(STRSTARTS(STR(?skill), "http://data.europa.eu/esco/skill/"))
    }
    """

    skills_green = set()
    for row in g.query(query_green):
        skills_green.add(str(row.skill))

    print(f"  Skills green: {len(skills_green)}")

    # ── Query 3: Digital skills (por si acaso) ────────────────────────────────
    print("\nExtrayendo digital skills...")
    query_digital = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?skill WHERE {
        ?skill skos:inScheme <http://data.europa.eu/esco/concept-scheme/digital> .
        FILTER(STRSTARTS(STR(?skill), "http://data.europa.eu/esco/skill/"))
    }
    """

    skills_digital = set()
    for row in g.query(query_digital):
        skills_digital.add(str(row.skill))

    print(f"  Skills digital: {len(skills_digital)}")

    # ── Save ──────────────────────────────────────────────────────────────────
    output = {
        "extracted_from": "esco-v1.2.0.rdf",
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "skills_reuse": skills_reuse,
        "skills_green": sorted(skills_green),
        "skills_digital": sorted(skills_digital),
        "stats": {
            "total_with_reuse": len(skills_reuse),
            "total_green": len(skills_green),
            "total_digital": len(skills_digital),
            "reuse_distribution": dict(reuse_dist),
        }
    }

    out_path = "exports/esco_skills_rdf_extract.json"
    os.makedirs("exports", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado: {out_path}")
    print(f"Total time: {time.time()-start:.0f}s")


if __name__ == "__main__":
    main()
