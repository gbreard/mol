#!/usr/bin/env python3
"""
Genera JSON jerárquico para Sunburst con drill-down.
Estructura: ESCO → L1 → L2 → items individuales (skill/knowledge)
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
SKILLS_FILE = Path(__file__).parent.parent.parent.parent / "database/embeddings/esco_skills_full.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/esco_skills_hierarchy.json"

# Labels para categorías L1
L1_LABELS = {
    "S1": "Comunicación y colaboración",
    "S2": "Gestión de información",
    "S3": "Asistencia y cuidado",
    "S4": "Gestión y administración",
    "S5": "Trabajo con ordenadores",
    "S6": "Manipulación y movimiento",
    "S7": "Construcción",
    "S8": "Trabajo con maquinaria",
    "T1": "Competencias básicas",
    "T2": "Pensamiento y razonamiento",
    "T3": "Autogestión",
    "T4": "Competencias sociales",
    "T5": "Competencias físicas",
    "T6": "Competencias para la vida",
}

def load_skills():
    """Carga skills desde JSON."""
    with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['skills']

def build_hierarchy(skills: dict) -> dict:
    """Construye jerarquía para Sunburst."""

    # Estructura: L1 → L2 → type → [items]
    hierarchy = defaultdict(lambda: defaultdict(lambda: {"skill": [], "knowledge": []}))
    l2_labels = {}

    for uri, skill in skills.items():
        l1 = skill.get('L1')
        l2 = skill.get('L2')
        skill_type = skill.get('type', 'skill')
        label = skill.get('label', 'Sin nombre')
        category_label = skill.get('category_label', '')

        if not l1 or not l2:
            continue

        # Guardar label de L2
        if l2 not in l2_labels and category_label:
            l2_labels[l2] = category_label

        hierarchy[l1][l2][skill_type].append({
            "name": label,
            "label": label,
            "type": skill_type,
            "value": 1
        })

    # Construir árbol
    root = {
        "name": "ESCO",
        "label": "Taxonomía ESCO",
        "children": []
    }

    # Ordenar L1
    for l1 in sorted(hierarchy.keys()):
        l1_node = {
            "name": l1,
            "label": L1_LABELS.get(l1, l1),
            "children": []
        }

        # Ordenar L2
        for l2 in sorted(hierarchy[l1].keys()):
            l2_data = hierarchy[l1][l2]
            l2_node = {
                "name": l2,
                "label": l2_labels.get(l2, l2),
                "children": []
            }

            # Agregar skills
            if l2_data["skill"]:
                l2_node["children"].append({
                    "name": f"{l2}_skills",
                    "label": "Skills",
                    "type": "skill",
                    "children": sorted(l2_data["skill"], key=lambda x: x["name"])
                })

            # Agregar knowledge
            if l2_data["knowledge"]:
                l2_node["children"].append({
                    "name": f"{l2}_knowledge",
                    "label": "Conocimientos",
                    "type": "knowledge",
                    "children": sorted(l2_data["knowledge"], key=lambda x: x["name"])
                })

            if l2_node["children"]:
                l1_node["children"].append(l2_node)

        if l1_node["children"]:
            root["children"].append(l1_node)

    return root

def calculate_stats(root: dict) -> dict:
    """Calcula estadísticas."""
    stats = {
        "total": 0,
        "skills": 0,
        "knowledge": 0,
        "l1_count": 0,
        "l2_count": 0
    }

    def count_recursive(node, depth=0):
        if "value" in node and node.get("type"):
            stats["total"] += 1
            if node["type"] == "skill":
                stats["skills"] += 1
            else:
                stats["knowledge"] += 1

        if depth == 1:
            stats["l1_count"] += 1
        elif depth == 2:
            stats["l2_count"] += 1

        for child in node.get("children", []):
            count_recursive(child, depth + 1)

    count_recursive(root)
    return stats

def main():
    print("Cargando skills ESCO...")
    skills = load_skills()
    print(f"  - {len(skills)} skills cargadas")

    print("Construyendo jerarquía...")
    root = build_hierarchy(skills)

    print("Calculando estadísticas...")
    stats = calculate_stats(root)
    print(f"  - Total: {stats['total']}")
    print(f"  - Skills: {stats['skills']}")
    print(f"  - Knowledge: {stats['knowledge']}")
    print(f"  - Categorias L1: {stats['l1_count']}")
    print(f"  - Subcategorias L2: {stats['l2_count']}")

    # Guardar
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado en: {OUTPUT_FILE}")
    print(f"Tamaño: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
