#!/usr/bin/env python3
"""
Extrae reusability level y green flag de cada skill desde el RDF de ESCO.
Usa streaming XML SAX (no carga todo en memoria).
"""

import xml.sax
import json
import os
import time
from collections import Counter


RDF_PATH = "/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf"


class ESCOSkillHandler(xml.sax.ContentHandler):
    """
    SAX handler que extrae datos de skills del RDF de ESCO.

    Estructura del RDF:
    - Skills son <skos:Concept rdf:about="http://data.europa.eu/esco/skill/UUID">
    - Green: <skos:inScheme rdf:resource=".../concept-scheme/green"/>
    - Reuse: <esco:skillReuseLevel> contiene <skos:Concept rdf:about=".../skill-reuse-level/LEVEL">
    - Los bloques están anidados, así que trackeamos profundidad.
    """

    def __init__(self):
        super().__init__()
        self.skills_reuse = {}
        self.skills_green = set()

        # Parser state
        self._stack = []           # tag stack for nesting
        self._current_skill = None # URI of current skill being parsed
        self._in_reuse_block = False
        self._skill_depth = 0      # depth at which skill was opened

    def startElement(self, name, attrs):
        self._stack.append(name)

        # Detect a skill concept
        if name == "skos:Concept":
            about = attrs.get("rdf:about", "")
            if "/esco/skill/" in about and not self._current_skill:
                self._current_skill = about
                self._skill_depth = len(self._stack)

        # Inside a skill, detect skillReuseLevel block
        if name == "esco:skillReuseLevel" and self._current_skill:
            self._in_reuse_block = True

        # Reuse level concept inside skillReuseLevel
        if name == "skos:Concept" and self._in_reuse_block:
            about = attrs.get("rdf:about", "")
            if "skill-reuse-level/" in about:
                level = about.split("skill-reuse-level/")[-1]
                self.skills_reuse[self._current_skill] = level

        # Green scheme membership (direct attribute form)
        if name == "skos:inScheme" and self._current_skill:
            resource = attrs.get("rdf:resource", "")
            if "concept-scheme/green" in resource:
                self.skills_green.add(self._current_skill)

        # Green scheme definition (nested form - ConceptScheme inside inScheme)
        if name == "skos:ConceptScheme" and self._current_skill:
            about = attrs.get("rdf:about", "")
            if "concept-scheme/green" in about:
                self.skills_green.add(self._current_skill)

    def endElement(self, name):
        if name == "esco:skillReuseLevel":
            self._in_reuse_block = False

        # Close skill when we return to the depth where it was opened
        if name == "skos:Concept" and self._current_skill:
            if len(self._stack) == self._skill_depth:
                self._current_skill = None
                self._skill_depth = 0

        if self._stack:
            self._stack.pop()

    def characters(self, content):
        pass


def main():
    print(f"Parseando RDF: {RDF_PATH}")
    print(f"Tamaño: {os.path.getsize(RDF_PATH) / 1024 / 1024:.0f} MB")

    handler = ESCOSkillHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    start = time.time()
    parser.parse(RDF_PATH)
    elapsed = time.time() - start

    print(f"\nParseado en {elapsed:.0f}s")
    print(f"Skills con reusability: {len(handler.skills_reuse)}")
    print(f"Skills green: {len(handler.skills_green)}")

    # Distribution
    reuse_dist = Counter(handler.skills_reuse.values())
    print(f"\nReusability distribution:")
    for level, count in sorted(reuse_dist.items(), key=lambda x: -x[1]):
        print(f"  {level:25} {count:>6}")

    # Save
    output = {
        "extracted_from": "esco-v1.2.0.rdf",
        "skills_reuse": handler.skills_reuse,
        "skills_green": sorted(handler.skills_green),
        "stats": {
            "total_with_reuse": len(handler.skills_reuse),
            "total_green": len(handler.skills_green),
            "reuse_distribution": dict(reuse_dist),
        }
    }

    out_path = "exports/esco_skills_rdf_extract.json"
    os.makedirs("exports", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado: {out_path}")


if __name__ == "__main__":
    main()
