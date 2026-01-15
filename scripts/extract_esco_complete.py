#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_esco_complete.py - Extraccion completa de ESCO del RDF
==============================================================

Extrae del RDF de ESCO v1.2.0:

1. OCUPACIONES (3,046)
   - URI, codigo ESCO (5244.1), label ES
   - Codigo ISCO (5244), label ISCO ES
   - Skills esenciales y opcionales asociadas

2. SKILLS (14,247)
   - URI, label ES, descripcion
   - Tipo: skill | knowledge | attitude
   - Jerarquia: broader_uri, broader_code, broader_label
   - Codigo de categoria (S1.5, T2.1, etc.)

3. CATEGORIAS DE SKILLS (509)
   - Codigos jerarquicos: S, S1, S1.5, S1.5.1
   - Labels en espanol
   - Estructura de arbol

4. RELACIONES OCUPACION-SKILL (134,822)
   - Essential skills por ocupacion
   - Optional skills por ocupacion

Output:
- database/embeddings/esco_occupations_full.json
- database/embeddings/esco_skills_full.json
- database/embeddings/esco_skill_hierarchy.json
- database/embeddings/esco_occupation_skills.json

Tiempo estimado: 20-40 minutos (RDF de 1.3 GB)

Uso:
    python scripts/extract_esco_complete.py
    python scripts/extract_esco_complete.py --only-skills
    python scripts/extract_esco_complete.py --only-relations
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from rdflib import Graph, Namespace, URIRef
    from rdflib.namespace import RDF, SKOS
except ImportError:
    print("ERROR: rdflib no instalado. Ejecutar: pip install rdflib")
    sys.exit(1)

# Rutas
RDF_PATH = Path(r"D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf")
OUTPUT_DIR = Path(__file__).parent.parent / "database" / "embeddings"

# Namespaces ESCO
ESCO = Namespace("http://data.europa.eu/esco/model#")


class ESCOExtractor:
    """Extractor completo de datos ESCO del RDF."""

    def __init__(self, rdf_path: Path):
        self.rdf_path = rdf_path
        self.graph = None

        # Datos extraidos
        self.occupations = {}      # uri -> {code, label, isco_code, isco_label}
        self.skills = {}           # uri -> {label, type, broader_uri, broader_code}
        self.skill_hierarchy = {}  # uri -> {code, label, parent_uri, children}
        self.occupation_skills = {} # occupation_uri -> {essential: [], optional: []}
        self.isco_labels = {}      # isco_code -> label

    def load_rdf(self):
        """Carga el grafo RDF."""
        print(f"\n[1/5] Cargando RDF ({self.rdf_path.stat().st_size / 1024 / 1024:.0f} MB)...")
        print("      Esto puede tomar 10-20 minutos...")

        self.graph = Graph()
        self.graph.parse(str(self.rdf_path), format='xml')
        print(f"      OK: {len(self.graph):,} tripletas cargadas")

    def extract_occupations(self):
        """Extrae ocupaciones ESCO con codigos."""
        print("\n[2/5] Extrayendo ocupaciones...")

        g = self.graph

        # Buscar todas las ocupaciones (tienen tipo escom:Occupation)
        for s in g.subjects(RDF.type, ESCO.Occupation):
            uri = str(s)

            if '/esco/occupation/' not in uri:
                continue

            # Label en espanol
            label_es = ""
            for label in g.objects(s, SKOS.prefLabel):
                if hasattr(label, 'language') and label.language == 'es':
                    label_es = str(label)
                    break

            # Codigo ESCO (notation)
            esco_code = ""
            for notation in g.objects(s, SKOS.notation):
                code = str(notation)
                if '.' in code or code.isdigit():
                    esco_code = code
                    break

            # Derivar ISCO
            if esco_code:
                isco_code = esco_code.split('.')[0] if '.' in esco_code else esco_code[:4]
            else:
                isco_code = ""

            self.occupations[uri] = {
                'uri': uri,
                'esco_code': esco_code,
                'esco_label': label_es,
                'isco_code': isco_code,
                'isco_label': ''  # Se llena despues
            }

        # Extraer labels ISCO
        print("      Extrayendo labels ISCO...")
        for s, p, o in g.triples((None, SKOS.notation, None)):
            uri = str(s)
            code = str(o)

            if '/esco/isco/C' in uri and len(code) == 4 and code.isdigit():
                # Buscar label ES
                for label in g.objects(s, SKOS.prefLabel):
                    if hasattr(label, 'language') and label.language == 'es':
                        self.isco_labels[code] = str(label)
                        break

        # Asignar ISCO labels a ocupaciones
        for uri, occ in self.occupations.items():
            isco_code = occ['isco_code']
            if isco_code in self.isco_labels:
                occ['isco_label'] = self.isco_labels[isco_code]

        print(f"      OK: {len(self.occupations):,} ocupaciones, {len(self.isco_labels)} grupos ISCO")

    def extract_skill_hierarchy(self):
        """Extrae la jerarquia de categorias de skills (S, S1, S1.5, etc.)."""
        print("\n[3/5] Extrayendo jerarquia de skills...")

        g = self.graph

        # Primero encontrar todos los nodos con codigos tipo S, S1, K, T, etc.
        skill_categories = {}

        for s, p, o in g.triples((None, SKOS.notation, None)):
            uri = str(s)
            code = str(o)

            # Filtrar codigos de skills (S, S1, S1.5, K, K1, T, T1, etc.)
            if '/esco/skill/' in uri:
                # Verificar que es un codigo de categoria (no de skill individual)
                if code and (code[0] in 'SKT' or code.startswith('A')):
                    # Label ES
                    label_es = ""
                    for label in g.objects(s, SKOS.prefLabel):
                        if hasattr(label, 'language') and label.language == 'es':
                            label_es = str(label)
                            break

                    # Broader (padre)
                    broader_uri = None
                    broader_code = None
                    for broader in g.objects(s, SKOS.broader):
                        broader_uri = str(broader)
                        # Buscar codigo del padre
                        for bc in g.objects(broader, SKOS.notation):
                            broader_code = str(bc)
                            break
                        break

                    skill_categories[uri] = {
                        'uri': uri,
                        'code': code,
                        'label': label_es,
                        'broader_uri': broader_uri,
                        'broader_code': broader_code,
                        'children': []
                    }

        # Construir relaciones padre-hijo
        for uri, cat in skill_categories.items():
            if cat['broader_uri'] and cat['broader_uri'] in skill_categories:
                skill_categories[cat['broader_uri']]['children'].append(uri)

        self.skill_hierarchy = skill_categories

        # Contar por nivel
        levels = defaultdict(int)
        for cat in skill_categories.values():
            code = cat['code']
            level = code.count('.') + 1
            levels[level] += 1

        print(f"      OK: {len(skill_categories)} categorias")
        print(f"      Nivel 1 (S, K, T): {levels[1]}")
        print(f"      Nivel 2 (S1, K1): {levels[2]}")
        print(f"      Nivel 3 (S1.5): {levels[3]}")
        print(f"      Nivel 4+ (S1.5.1): {sum(v for k,v in levels.items() if k >= 4)}")

    def _walk_hierarchy_for_code(self, start_uri, max_depth=10):
        """
        Camina hacia arriba en la jerarquia hasta encontrar un nodo con codigo.
        Retorna (code, label, category_uri) o (None, None, None).
        """
        g = self.graph
        current_uri = start_uri
        visited = set()

        for _ in range(max_depth):
            if current_uri in visited:
                break
            visited.add(current_uri)

            # Buscar codigo en nodo actual
            for notation in g.objects(URIRef(current_uri), SKOS.notation):
                code = str(notation)
                # Verificar que es codigo de categoria (S, S1, S1.5, K, T, A)
                if code and code[0] in 'SKTA' and (len(code) <= 2 or '.' in code):
                    # Obtener label
                    label = ""
                    for l in g.objects(URIRef(current_uri), SKOS.prefLabel):
                        if hasattr(l, 'language') and l.language == 'es':
                            label = str(l)
                            break
                    return code, label, current_uri

            # Subir al broader
            next_uri = None
            for broader in g.objects(URIRef(current_uri), SKOS.broader):
                next_uri = str(broader)
                break

            if not next_uri:
                break
            current_uri = next_uri

        return None, None, None

    def extract_skills(self):
        """Extrae skills individuales con su jerarquia."""
        print("\n[4/5] Extrayendo skills...")

        g = self.graph

        # Buscar skills por tipo
        skill_count = 0
        knowledge_count = 0
        with_l1_count = 0

        for s in g.subjects(RDF.type, ESCO.Skill):
            uri = str(s)

            if '/esco/skill/' not in uri:
                continue

            # Label ES
            label_es = ""
            for label in g.objects(s, SKOS.prefLabel):
                if hasattr(label, 'language') and label.language == 'es':
                    label_es = str(label)
                    break

            # Descripcion ES
            desc_es = ""
            for desc in g.objects(s, SKOS.definition):
                if hasattr(desc, 'language') and desc.language == 'es':
                    desc_es = str(desc)
                    break

            # Tipo (skill, knowledge)
            skill_type = "skill"
            for type_obj in g.objects(s, ESCO.skillType):
                skill_type = str(type_obj).split('/')[-1]
                break

            # Broader directo (categoria padre)
            broader_uri = None
            broader_label = None
            for broader in g.objects(s, SKOS.broader):
                broader_uri = str(broader)
                for bl in g.objects(broader, SKOS.prefLabel):
                    if hasattr(bl, 'language') and bl.language == 'es':
                        broader_label = str(bl)
                        break
                break

            # Caminar hacia arriba para encontrar el codigo de categoria
            category_code = None
            category_label = None
            category_uri = None
            L1 = None
            L2 = None

            if broader_uri:
                category_code, category_label, category_uri = self._walk_hierarchy_for_code(broader_uri)

            if category_code:
                parts = category_code.split('.')
                L1 = parts[0] if parts else None
                L2 = '.'.join(parts[:2]) if len(parts) >= 2 else category_code
                with_l1_count += 1

            self.skills[uri] = {
                'uri': uri,
                'label': label_es,
                'description': desc_es,
                'type': skill_type,
                'broader_uri': broader_uri,
                'broader_label': broader_label,
                'category_uri': category_uri,
                'category_code': category_code,
                'category_label': category_label,
                'L1': L1,
                'L2': L2
            }

            if skill_type == 'knowledge':
                knowledge_count += 1
            else:
                skill_count += 1

        print(f"      OK: {len(self.skills):,} skills totales")
        print(f"      - Skills: {skill_count:,}")
        print(f"      - Knowledge: {knowledge_count:,}")
        print(f"      - Con categoria L1: {with_l1_count:,} ({100*with_l1_count/len(self.skills):.1f}%)")

    def extract_occupation_skills(self):
        """Extrae relaciones ocupacion-skill (essential/optional)."""
        print("\n[5/5] Extrayendo relaciones ocupacion-skill...")

        g = self.graph

        # Inicializar para todas las ocupaciones
        for uri in self.occupations:
            self.occupation_skills[uri] = {
                'essential': [],
                'optional': []
            }

        # Essential skills
        essential_count = 0
        for s, p, o in g.triples((None, ESCO.relatedEssentialSkill, None)):
            occ_uri = str(s)
            skill_uri = str(o)

            if occ_uri in self.occupation_skills:
                # Obtener info del skill
                skill_info = self.skills.get(skill_uri, {})
                self.occupation_skills[occ_uri]['essential'].append({
                    'skill_uri': skill_uri,
                    'skill_label': skill_info.get('label', ''),
                    'L1': skill_info.get('L1'),
                    'L2': skill_info.get('L2')
                })
                essential_count += 1

        # Optional skills
        optional_count = 0
        for s, p, o in g.triples((None, ESCO.relatedOptionalSkill, None)):
            occ_uri = str(s)
            skill_uri = str(o)

            if occ_uri in self.occupation_skills:
                skill_info = self.skills.get(skill_uri, {})
                self.occupation_skills[occ_uri]['optional'].append({
                    'skill_uri': skill_uri,
                    'skill_label': skill_info.get('label', ''),
                    'L1': skill_info.get('L1'),
                    'L2': skill_info.get('L2')
                })
                optional_count += 1

        print(f"      OK: {essential_count:,} essential + {optional_count:,} optional = {essential_count + optional_count:,} relaciones")

        # Estadisticas
        occs_with_skills = sum(1 for o in self.occupation_skills.values()
                              if o['essential'] or o['optional'])
        avg_essential = essential_count / len(self.occupations) if self.occupations else 0
        avg_optional = optional_count / len(self.occupations) if self.occupations else 0

        print(f"      Ocupaciones con skills: {occs_with_skills}")
        print(f"      Promedio essential/ocupacion: {avg_essential:.1f}")
        print(f"      Promedio optional/ocupacion: {avg_optional:.1f}")

    def save_outputs(self, output_dir: Path):
        """Guarda los JSONs de salida."""
        print("\n[6/5] Guardando archivos...")

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()

        # 1. Ocupaciones
        occupations_file = output_dir / "esco_occupations_full.json"
        occupations_data = {
            'version': '1.2.0',
            'source': 'esco-v1.2.0.rdf',
            'extracted_at': timestamp,
            'total_occupations': len(self.occupations),
            'total_isco_groups': len(self.isco_labels),
            'occupations': list(self.occupations.values()),
            'isco_labels': self.isco_labels
        }
        with open(occupations_file, 'w', encoding='utf-8') as f:
            json.dump(occupations_data, f, ensure_ascii=False, indent=2)
        print(f"      {occupations_file.name}: {len(self.occupations):,} ocupaciones")

        # 2. Skills
        skills_file = output_dir / "esco_skills_full.json"
        skills_data = {
            'version': '1.2.0',
            'source': 'esco-v1.2.0.rdf',
            'extracted_at': timestamp,
            'total_skills': len(self.skills),
            'skills': self.skills
        }
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(skills_data, f, ensure_ascii=False, indent=2)
        print(f"      {skills_file.name}: {len(self.skills):,} skills")

        # 3. Jerarquia de skills
        hierarchy_file = output_dir / "esco_skill_hierarchy.json"
        hierarchy_data = {
            'version': '1.2.0',
            'source': 'esco-v1.2.0.rdf',
            'extracted_at': timestamp,
            'total_categories': len(self.skill_hierarchy),
            'categories': self.skill_hierarchy,
            # Crear indice por codigo para lookup rapido
            'by_code': {cat['code']: uri for uri, cat in self.skill_hierarchy.items()}
        }
        with open(hierarchy_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy_data, f, ensure_ascii=False, indent=2)
        print(f"      {hierarchy_file.name}: {len(self.skill_hierarchy)} categorias")

        # 4. Relaciones ocupacion-skill
        relations_file = output_dir / "esco_occupation_skills.json"
        relations_data = {
            'version': '1.2.0',
            'source': 'esco-v1.2.0.rdf',
            'extracted_at': timestamp,
            'total_occupations': len(self.occupation_skills),
            'total_relations': sum(
                len(o['essential']) + len(o['optional'])
                for o in self.occupation_skills.values()
            ),
            'occupation_skills': self.occupation_skills
        }
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)
        print(f"      {relations_file.name}: {relations_data['total_relations']:,} relaciones")

        # Crear indice de skill -> ocupaciones (para matching inverso)
        skill_to_occupations_file = output_dir / "esco_skill_to_occupations.json"
        skill_to_occs = defaultdict(lambda: {'essential_for': [], 'optional_for': []})

        for occ_uri, skills in self.occupation_skills.items():
            occ_info = self.occupations.get(occ_uri, {})
            occ_data = {
                'uri': occ_uri,
                'esco_code': occ_info.get('esco_code', ''),
                'label': occ_info.get('esco_label', '')
            }

            for skill in skills['essential']:
                skill_to_occs[skill['skill_uri']]['essential_for'].append(occ_data)
            for skill in skills['optional']:
                skill_to_occs[skill['skill_uri']]['optional_for'].append(occ_data)

        skill_to_occs_data = {
            'version': '1.2.0',
            'source': 'esco-v1.2.0.rdf',
            'extracted_at': timestamp,
            'description': 'Indice inverso: dado un skill, que ocupaciones lo requieren',
            'total_skills': len(skill_to_occs),
            'skill_to_occupations': dict(skill_to_occs)
        }
        with open(skill_to_occupations_file, 'w', encoding='utf-8') as f:
            json.dump(skill_to_occs_data, f, ensure_ascii=False, indent=2)
        print(f"      {skill_to_occupations_file.name}: indice inverso skill->ocupaciones")

    def run(self, output_dir: Path):
        """Ejecuta la extraccion completa."""
        start_time = datetime.now()

        print("=" * 70)
        print("EXTRACCION COMPLETA ESCO")
        print(f"Fecha: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.load_rdf()
        self.extract_occupations()
        self.extract_skill_hierarchy()
        self.extract_skills()
        self.extract_occupation_skills()
        self.save_outputs(output_dir)

        elapsed = datetime.now() - start_time

        print("\n" + "=" * 70)
        print("RESUMEN")
        print("=" * 70)
        print(f"  Ocupaciones: {len(self.occupations):,}")
        print(f"  Skills: {len(self.skills):,}")
        print(f"  Categorias skill: {len(self.skill_hierarchy)}")
        print(f"  Relaciones ocu-skill: {sum(len(o['essential']) + len(o['optional']) for o in self.occupation_skills.values()):,}")
        print(f"  Tiempo total: {elapsed}")
        print(f"  Output: {output_dir}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Extraccion completa de ESCO del RDF')
    parser.add_argument('--rdf', type=str, default=str(RDF_PATH),
                        help='Path al archivo RDF de ESCO')
    parser.add_argument('--output', type=str, default=str(OUTPUT_DIR),
                        help='Directorio de salida')

    args = parser.parse_args()

    rdf_path = Path(args.rdf)
    output_dir = Path(args.output)

    if not rdf_path.exists():
        print(f"ERROR: RDF no encontrado: {rdf_path}")
        sys.exit(1)

    extractor = ESCOExtractor(rdf_path)
    extractor.run(output_dir)


if __name__ == "__main__":
    main()
