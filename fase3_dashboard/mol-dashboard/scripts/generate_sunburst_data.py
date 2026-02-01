#!/usr/bin/env python3
"""
Genera JSON jerarquico para Sunburst con drill-down.
Estructura: ESCO -> L1 -> L2 -> items individuales (skill/knowledge)

Para K (Knowledge): agrupa por tematica usando broader_label
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Paths
SKILLS_FILE = Path(__file__).parent.parent.parent.parent / "database/embeddings/esco_skills_full.json"
OUTPUT_FILE = Path(__file__).parent.parent / "public/data/esco_skills_hierarchy.json"

# Labels para categorias L1
L1_LABELS = {
    "S1": "Comunicacion y colaboracion",
    "S2": "Gestion de informacion",
    "S3": "Asistencia y cuidado",
    "S4": "Gestion y administracion",
    "S5": "Trabajo con ordenadores",
    "S6": "Manipulacion y movimiento",
    "S7": "Construccion",
    "S8": "Trabajo con maquinaria",
    "T1": "Competencias basicas",
    "T2": "Pensamiento y razonamiento",
    "T3": "Autogestion",
    "T4": "Competencias sociales",
    "T5": "Competencias fisicas",
    "T6": "Competencias para la vida",
    # K subcategorias (creadas por nosotros)
    "K1": "Tecnologia e Informatica",
    "K2": "Medicina y Salud",
    "K3": "Derecho y Legislacion",
    "K4": "Ingenieria y Construccion",
    "K5": "Negocios y Finanzas",
    "K6": "Ciencias Naturales",
    "K7": "Industria y Manufactura",
    "K8": "Arte y Comunicacion",
    "K9": "Transporte y Logistica",
    "K10": "Agricultura y Alimentacion",
    "K11": "Educacion y Sociedad",
    "K12": "Otros Conocimientos",
}

# Mapeo de broader_label a subcategoria K
BROADER_TO_K_CATEGORY = {
    # K1: Tecnologia e Informatica
    "desarrollo y analisis de software y aplicaciones": "K1",
    "diseno y administracion de redes y bases de datos": "K1",
    "uso de computadores": "K1",
    "electronica y automatizacion": "K1",
    "tecnologias de la informacion": "K1",
    "programacion informatica": "K1",
    "sistemas informaticos": "K1",
    "seguridad informatica": "K1",
    "inteligencia artificial": "K1",

    # K2: Medicina y Salud
    "medicina": "K2",
    "tecnologia de diagnostico y tratamiento medico": "K2",
    "terapia y rehabilitacion": "K2",
    "enfermeria y parteria": "K2",
    "psicologia": "K2",
    "farmacia": "K2",
    "salud publica": "K2",
    "odontologia": "K2",
    "veterinaria": "K2",
    "salud y proteccion laboral": "K2",
    "ciencias de la salud": "K2",
    "anatomia": "K2",

    # K3: Derecho y Legislacion
    "derecho": "K3",
    "legislacion": "K3",
    "ciencias politicas": "K3",
    "administracion publica": "K3",
    "seguridad y defensa": "K3",

    # K4: Ingenieria y Construccion
    "construccion e ingenieria civil": "K4",
    "mecanica y profesiones afines a la metalisteria": "K4",
    "electricidad y energia": "K4",
    "ingenieria y procesos quimicos": "K4",
    "arquitectura": "K4",
    "ingenieria mecanica": "K4",
    "ingenieria electrica": "K4",

    # K5: Negocios y Finanzas
    "gestion y administracion": "K5",
    "gestion financiera, administracion bancaria y seguros": "K5",
    "mercadotecnia y publicidad": "K5",
    "ventas al por mayor y al por menor": "K5",
    "contabilidad y auditoria": "K5",
    "economia": "K5",
    "recursos humanos": "K5",
    "comercio internacional": "K5",

    # K6: Ciencias Naturales
    "biologia": "K6",
    "quimica": "K6",
    "fisica": "K6",
    "matematicas": "K6",
    "ciencias de la tierra": "K6",
    "medio ambiente": "K6",
    "meteorologia": "K6",
    "estadistica": "K6",

    # K7: Industria y Manufactura
    "productos textiles (ropa, calzado y articulos de cuero)": "K7",
    "materiales (vidrio, papel, plastico y madera)": "K7",
    "mineria y extraccion": "K7",
    "metalurgia": "K7",
    "fabricacion": "K7",
    "control de calidad": "K7",

    # K8: Arte y Comunicacion
    "tecnicas audiovisuales y produccion para medios de comunicacion": "K8",
    "musica y artes escenicas": "K8",
    "artes visuales": "K8",
    "diseno": "K8",
    "periodismo": "K8",
    "relaciones publicas": "K8",
    "idiomas": "K8",
    "traduccion": "K8",

    # K9: Transporte y Logistica
    "servicios de transporte": "K9",
    "vehiculos, barcos y aeronaves motorizadas": "K9",
    "logistica": "K9",
    "aviacion": "K9",
    "navegacion maritima": "K9",

    # K10: Agricultura y Alimentacion
    "procesamiento de alimentos": "K10",
    "produccion agricola y ganadera": "K10",
    "horticultura": "K10",
    "silvicultura": "K10",
    "pesca": "K10",
    "gastronomia": "K10",

    # K11: Educacion y Sociedad
    "educacion": "K11",
    "trabajo social": "K11",
    "sociologia": "K11",
    "historia": "K11",
    "filosofia": "K11",
    "religion": "K11",
    "deportes": "K11",
    "turismo y hosteleria": "K11",
}

def normalize_text(text):
    """Normaliza texto para comparacion."""
    if not text:
        return ""
    # Remover acentos basico
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    text = text.lower()
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def get_k_category(broader_label):
    """Obtiene la subcategoria K basada en broader_label."""
    if not broader_label:
        return "K12"  # Otros

    normalized = normalize_text(broader_label)

    # Buscar match exacto o parcial
    for pattern, category in BROADER_TO_K_CATEGORY.items():
        pattern_norm = normalize_text(pattern)
        if pattern_norm in normalized or normalized in pattern_norm:
            return category

    # Buscar por palabras clave
    keywords_to_category = {
        "software": "K1", "informatica": "K1", "datos": "K1", "web": "K1", "digital": "K1",
        "medic": "K2", "salud": "K2", "hospital": "K2", "clinic": "K2", "farmac": "K2",
        "derecho": "K3", "legal": "K3", "ley": "K3", "juridic": "K3",
        "construccion": "K4", "ingenier": "K4", "electric": "K4", "mecanica": "K4",
        "finanz": "K5", "banco": "K5", "contab": "K5", "gestion": "K5", "negocio": "K5",
        "biolog": "K6", "quimic": "K6", "fisic": "K6", "ciencia": "K6",
        "textil": "K7", "material": "K7", "fabric": "K7", "industri": "K7",
        "arte": "K8", "music": "K8", "medio": "K8", "comunicacion": "K8",
        "transport": "K9", "vehiculo": "K9", "logistic": "K9", "aviacion": "K9",
        "aliment": "K10", "agricul": "K10", "ganader": "K10", "cocina": "K10",
        "educacion": "K11", "social": "K11", "deporte": "K11", "turismo": "K11",
    }

    for keyword, category in keywords_to_category.items():
        if keyword in normalized:
            return category

    return "K12"  # Otros

def load_skills():
    """Carga skills desde JSON."""
    with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['skills']

def build_hierarchy(skills: dict) -> dict:
    """Construye jerarquia para Sunburst."""

    # Estructura: L1 -> L2 -> type -> [items]
    hierarchy = defaultdict(lambda: defaultdict(lambda: {"skill": [], "knowledge": []}))
    l2_labels = {}

    for uri, skill in skills.items():
        l1 = skill.get('L1')
        l2 = skill.get('L2')
        skill_type = skill.get('type', 'skill')
        label = skill.get('label', 'Sin nombre')
        category_label = skill.get('category_label', '')
        broader_label = skill.get('broader_label', '')

        # Para items sin L1 (327 sin clasificar), saltar
        if not l1:
            continue

        # Para K (Knowledge), crear subcategorias basadas en broader_label
        if l1 == 'K':
            k_cat = get_k_category(broader_label)
            l1 = k_cat
            l2 = k_cat
            category_label = L1_LABELS.get(k_cat, "Otros Conocimientos")

        if not l2:
            l2 = l1

        # Guardar label de L2
        if l2 not in l2_labels and category_label:
            l2_labels[l2] = category_label

        hierarchy[l1][l2][skill_type].append({
            "name": label,
            "label": label,
            "type": skill_type,
            "value": 1
        })

    # Construir arbol
    root = {
        "name": "ESCO",
        "label": "Taxonomia ESCO",
        "children": []
    }

    # Ordenar L1: primero S, luego T, luego K
    def sort_key(l1):
        if l1.startswith('S'):
            return (0, l1)
        elif l1.startswith('T'):
            return (1, l1)
        elif l1.startswith('K'):
            return (2, l1)
        else:
            return (3, l1)

    for l1 in sorted(hierarchy.keys(), key=sort_key):
        l1_node = {
            "name": l1,
            "label": L1_LABELS.get(l1, l1),
            "children": []
        }

        # Ordenar L2
        for l2 in sorted(hierarchy[l1].keys()):
            l2_data = hierarchy[l1][l2]

            # Si L1 == L2 (como en K subcategorias), no crear nodo L2 separado
            if l1 == l2:
                # Agregar skills directamente a L1
                if l2_data["skill"]:
                    l1_node["children"].append({
                        "name": f"{l1}_skills",
                        "label": "Skills",
                        "type": "skill",
                        "children": sorted(l2_data["skill"], key=lambda x: x["name"])
                    })
                if l2_data["knowledge"]:
                    l1_node["children"].append({
                        "name": f"{l1}_knowledge",
                        "label": "Conocimientos",
                        "type": "knowledge",
                        "children": sorted(l2_data["knowledge"], key=lambda x: x["name"])
                    })
            else:
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
    """Calcula estadisticas."""
    stats = {
        "total": 0,
        "skills": 0,
        "knowledge": 0,
        "l1_count": 0,
        "l2_count": 0,
        "k_categorized": 0
    }

    def count_recursive(node, depth=0):
        if "value" in node and node.get("type"):
            stats["total"] += 1
            if node["type"] == "skill":
                stats["skills"] += 1
            else:
                stats["knowledge"] += 1

        name = node.get("name", "")
        if depth == 1:
            stats["l1_count"] += 1
            if name.startswith("K"):
                stats["k_categorized"] += 1
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

    print("Construyendo jerarquia (con K subcategorizado)...")
    root = build_hierarchy(skills)

    print("Calculando estadisticas...")
    stats = calculate_stats(root)
    print(f"  - Total: {stats['total']}")
    print(f"  - Skills: {stats['skills']}")
    print(f"  - Knowledge: {stats['knowledge']}")
    print(f"  - Categorias L1: {stats['l1_count']}")
    print(f"  - Subcategorias L2: {stats['l2_count']}")
    print(f"  - Subcategorias K creadas: {stats['k_categorized']}")

    # Guardar
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado en: {OUTPUT_FILE}")
    print(f"Tamano: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
