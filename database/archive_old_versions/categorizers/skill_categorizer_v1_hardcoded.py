#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Categorizer - Clasifica skills ESCO en categorías L1/L2 para dashboards.

Usa un enfoque de 3 capas:
1. Taxonomía oficial ESCO (esco_skills_taxonomy.json) - 14,247 skills con jerarquía
2. Mapeo manual (67 skills del Excel de validación)
3. Fallback a heurísticas de keywords (solo si no está en ESCO)

Categorías L1:
- S1: Comunicación
- S3: Asistencia (cliente, ventas, salud)
- S4: Gestión (admin, finanzas, procesos)
- S5: Trabajar con ordenadores (IT, digital)
- S6: Técnicas (mantenimiento, equipos)
- K: Conocimientos (teóricos)
- T: Transversales (soft skills)

Actualizado 2026-01-07: Integración con taxonomía oficial ESCO.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List

# Mapeo de skill groups ESCO -> categorías L1
# Basado en la jerarquía oficial ESCO v1.2.0
# IMPORTANTE: Nombres EXACTOS del RDF (incluyendo acentos y ortografía)
ESCO_GROUP_TO_L1 = {
    # S5 - Digital/IT
    "desarrollo y análisis de software y aplicaciones": {"L1": "S5", "es_digital": True},
    "diseño y administración de redes y bases de datos": {"L1": "S5", "es_digital": True},
    "utilizar herramientas de tecnología de la información": {"L1": "S5", "es_digital": True},
    "utilizar aparatos de comunicación": {"L1": "S5", "es_digital": True},
    "electrónica y automatización": {"L1": "S5", "es_digital": True},
    "técnicas audiovisuales y producción para medios de comunicación": {"L1": "S5", "es_digital": True},
    "manejar equipos audiovisuales operativos": {"L1": "S5", "es_digital": True},

    # S6 - Técnicas
    "mecánica y profesiones afines a la metalistería": {"L1": "S6", "es_digital": False},
    "electricidad y energía": {"L1": "S6", "es_digital": False},
    "instalar componentes de madera y de metal": {"L1": "S6", "es_digital": False},
    "materiales (vidrio, papel, plástico y madera)": {"L1": "S6", "es_digital": False},
    "procesamiento de alimentos": {"L1": "S6", "es_digital": False},
    "mantener equipos": {"L1": "S6", "es_digital": False},
    "operar maquinaria": {"L1": "S6", "es_digital": False},
    "conducir equipos de transporte": {"L1": "S6", "es_digital": False},
    "servicios de transporte": {"L1": "S6", "es_digital": False},
    "manejar maquinaria de transformación de alimentos": {"L1": "S6", "es_digital": False},
    "productos textiles (ropa, calzado y artículos de cuero)": {"L1": "S6", "es_digital": False},
    "construcción e ingeniería civil": {"L1": "S6", "es_digital": False},
    "ensamblar y fabricar productos": {"L1": "S6", "es_digital": False},
    "manejar máquinas de corte, rectificado y pulido": {"L1": "S6", "es_digital": False},
    "instalar y reparar aparatos eléctricos, electrónicos y de precisión": {"L1": "S6", "es_digital": False},
    "manejar equipos de conformación de metal, plástico o caucho": {"L1": "S6", "es_digital": False},
    "producción agrícola y ganadera": {"L1": "S6", "es_digital": False},
    "química": {"L1": "S6", "es_digital": False},

    # S4 - Gestión
    "gestión y administración": {"L1": "S4", "es_digital": False},
    "gestionar la calidad": {"L1": "S4", "es_digital": False},
    "dirigir actividades operativas": {"L1": "S4", "es_digital": False},
    "elaborar medidas y procedimientos operativos": {"L1": "S4", "es_digital": False},
    "planificar actos y programas": {"L1": "S4", "es_digital": False},
    "administrar recursos financieros": {"L1": "S4", "es_digital": False},
    "gestión de personal y de recursos humanos": {"L1": "S4", "es_digital": False},
    "hacer seguimiento de actividades operativas": {"L1": "S4", "es_digital": False},
    "mantener registros operativos": {"L1": "S4", "es_digital": False},
    "mercadotecnia y publicidad": {"L1": "S4", "es_digital": False},
    "analizar y evaluar información y datos": {"L1": "S4", "es_digital": False},

    # S3 - Asistencia (cliente, ventas, salud)
    "prestar asistencia médica, odontológica y de enfermería": {"L1": "S3", "es_digital": False},
    "diagnosticar afecciones de la salud": {"L1": "S3", "es_digital": False},
    "asistir a los clientes": {"L1": "S3", "es_digital": False},
    "vender productos y servicios": {"L1": "S3", "es_digital": False},
    "servicios de limpieza y mantenimiento de edificios": {"L1": "S3", "es_digital": False},
    "servicios de restauración": {"L1": "S3", "es_digital": False},
    "vender productos o servicios": {"L1": "S3", "es_digital": False},
    "promocionar productos, servicios o programas": {"L1": "S3", "es_digital": False},
    "tecnología de diagnóstico y tratamiento médico": {"L1": "S3", "es_digital": False},
    "terapia y rehabilitación": {"L1": "S3", "es_digital": False},
    "mantener y hacer respetar la seguridad física": {"L1": "S3", "es_digital": False},
    "hacer seguimiento de seguridad y protección": {"L1": "S3", "es_digital": False},

    # S1 - Comunicación
    "comunicar con otras personas": {"L1": "S1", "es_digital": False},
    "informar de hechos": {"L1": "S1", "es_digital": False},
    "hablar o señalar": {"L1": "S1", "es_digital": False},
    "redactar documentos e informes": {"L1": "S1", "es_digital": False},
    "escritura técnica o académica": {"L1": "S1", "es_digital": False},

    # K - Conocimientos
    "derecho": {"L1": "K", "es_digital": False},
    "medicina": {"L1": "K", "es_digital": False},
    "dominar idiomas": {"L1": "K", "es_digital": False},
    "matemáticas y estadísticas": {"L1": "K", "es_digital": False},
    "física y química": {"L1": "K", "es_digital": False},
    "biología": {"L1": "K", "es_digital": False},
    "contabilidad y auditoría": {"L1": "K", "es_digital": False},
    "economía y comercio": {"L1": "K", "es_digital": False},
    "aplicar conocimientos científicos y de ingeniería": {"L1": "K", "es_digital": False},
    "enseñar materias académicas o profesionales": {"L1": "K", "es_digital": False},

    # T - Transversales (soft skills)
    "pensar de manera crítica": {"L1": "T", "es_digital": False},
    "liderar a otras personas": {"L1": "T", "es_digital": False},
    "asesorar a otras personas": {"L1": "T", "es_digital": False},
    "instruir a otras personas": {"L1": "T", "es_digital": False},
    "trabajar con otras personas": {"L1": "T", "es_digital": False},
    "trabajar de forma independiente": {"L1": "T", "es_digital": False},
    "realizar estudios académicos o de mercado": {"L1": "T", "es_digital": False},
    "realizar cálculos": {"L1": "T", "es_digital": False},
    "decidir": {"L1": "T", "es_digital": False},
    "aplicar las normas de seguridad en el ámbito laboral": {"L1": "T", "es_digital": False},
    "cumplir los procedimientos operativos": {"L1": "T", "es_digital": False},
    "controlar la calidad de los productos": {"L1": "T", "es_digital": False},
    "ayudar a otras personas": {"L1": "T", "es_digital": False},
    "crear diseños o actuaciones artísticas": {"L1": "T", "es_digital": False},
    "procesar información, ideas y conceptos": {"L1": "T", "es_digital": False},
    "colaborar y servir de enlace": {"L1": "T", "es_digital": False},
    "trabajar en equipos": {"L1": "T", "es_digital": False},
    "cumplir los procedimientos de salud y seguridad": {"L1": "T", "es_digital": False},
    "crear exposiciones y decoraciones visuales": {"L1": "T", "es_digital": False},
    "realizar actividades artísticas o culturales": {"L1": "T", "es_digital": False},
}


class SkillCategorizer:
    """Clasifica skills ESCO en categorías L1/L2 para dashboards."""

    def __init__(self, config_path: str = None, taxonomy_path: str = None):
        """
        Inicializa el categorizador.

        Args:
            config_path: Ruta al archivo de configuración JSON para mapeo manual.
                        Si es None, usa config/skill_categories.json
            taxonomy_path: Ruta al archivo de taxonomía ESCO.
                          Si es None, usa config/esco_skills_taxonomy.json
        """
        base_path = Path(__file__).parent.parent / "config"

        if config_path is None:
            config_path = base_path / "skill_categories.json"
        if taxonomy_path is None:
            taxonomy_path = base_path / "esco_skills_taxonomy.json"

        self.config_path = Path(config_path)
        self.taxonomy_path = Path(taxonomy_path)

        self._load_taxonomy()
        self._load_config()

    def _load_taxonomy(self):
        """Carga la taxonomía oficial ESCO."""
        self.taxonomy = {}
        self.esco_available = False

        if self.taxonomy_path.exists():
            try:
                with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.taxonomy = data.get("skills", {})
                    self.esco_available = True
                    print(f"[SkillCategorizer] Taxonomía ESCO cargada: {len(self.taxonomy):,} skills")
            except Exception as e:
                print(f"[SkillCategorizer] WARN: No se pudo cargar taxonomía ESCO: {e}")

    def _load_config(self):
        """Carga la configuración desde JSON."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.categorias_L1 = config.get("categorias_L1", {})
        self.categorias_L2 = config.get("categorias_L2", {})
        self.mapeo_skills = config.get("mapeo_skills", {})
        self.heuristicas = config.get("heuristicas", {})
        self.default = config.get("default", {"L1": "T", "L2": None, "es_digital": False})

        # Pre-compilar patterns para eficiencia
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compila regex patterns para cada categoría."""
        self.patterns = {}

        # Orden de prioridad: más específicas primero
        # Técnicas (S6) antes que Digitales (S5) para evitar falsos positivos
        priority_order = [
            "keywords_tecnicas",      # S6 - electricidad, mantenimiento
            "keywords_conocimientos", # K - normativas, idiomas
            "keywords_asistencia",    # S3 - cliente, ventas, salud
            "keywords_gestion",       # S4 - inventario, contable
            "keywords_comunicacion",  # S1 - redacción
            "keywords_digitales",     # S5 - software, programación
            "keywords_transversales"  # T - soft skills (último para no capturar todo)
        ]

        for categoria in priority_order:
            if categoria not in self.heuristicas:
                continue
            data = self.heuristicas[categoria]
            keywords = data.get("keywords", [])
            if keywords:
                # Crear pattern que matchee cualquier keyword
                pattern = '|'.join(re.escape(kw) for kw in keywords)
                self.patterns[categoria] = {
                    "pattern": re.compile(pattern, re.IGNORECASE),
                    "L1": data.get("L1"),
                    "es_digital": data.get("es_digital", False),
                    "L2_subclasificacion": data.get("L2_subclasificacion", {})
                }

    def _get_category_from_taxonomy(self, skill_uri: str) -> Optional[Dict]:
        """
        Busca la categoría L1 usando la jerarquía oficial ESCO.

        Camina hacia arriba en la jerarquía (broader_uri) hasta encontrar
        un skill group mapeado a L1.
        """
        if not self.esco_available or skill_uri not in self.taxonomy:
            return None

        # Buscar en la jerarquía (máximo 5 niveles)
        current_uri = skill_uri
        visited = set()

        for _ in range(5):
            if current_uri in visited:
                break
            visited.add(current_uri)

            skill_data = self.taxonomy.get(current_uri)
            if not skill_data:
                break

            # Verificar si el LABEL ACTUAL está mapeado (para skill groups de nivel superior)
            current_label = skill_data.get("label")
            if current_label and current_label in ESCO_GROUP_TO_L1:
                mapping = ESCO_GROUP_TO_L1[current_label]
                return {
                    "L1": mapping["L1"],
                    "es_digital": mapping["es_digital"],
                    "broader_label": current_label
                }

            # Verificar si el broader_label está mapeado
            broader_label = skill_data.get("broader_label")
            if broader_label and broader_label in ESCO_GROUP_TO_L1:
                mapping = ESCO_GROUP_TO_L1[broader_label]
                return {
                    "L1": mapping["L1"],
                    "es_digital": mapping["es_digital"],
                    "broader_label": broader_label
                }

            # Subir un nivel
            broader_uri = skill_data.get("broader_uri")
            if not broader_uri:
                break
            current_uri = broader_uri

        # Si llegamos aquí, usar skill_type para conocimientos
        skill_data = self.taxonomy.get(skill_uri, {})
        if skill_data.get("type") == "knowledge":
            return {"L1": "K", "es_digital": False, "broader_label": None}

        return None

    def categorize(self, skill_uri: str, skill_label: str) -> Dict:
        """
        Categoriza una skill ESCO.

        Args:
            skill_uri: URI ESCO de la skill
            skill_label: Label en español de la skill

        Returns:
            Dict con:
            - L1: Código de categoría nivel 1 (ej: "S5")
            - L1_nombre: Nombre de la categoría L1 (ej: "Trabajar con ordenadores")
            - L2: Código de categoría nivel 2 (ej: "S5.1") o None
            - L2_nombre: Nombre de la categoría L2 o None
            - es_digital: Boolean indicando si es skill digital
            - metodo: "esco_taxonomy", "manual", "heuristica", o "default"
        """
        # 1. Lookup en taxonomía oficial ESCO (NUEVO - prioridad máxima)
        esco_result = self._get_category_from_taxonomy(skill_uri)
        if esco_result:
            return self._build_result(
                L1=esco_result["L1"],
                L2=None,  # TODO: mapear L2 desde jerarquía
                es_digital=esco_result["es_digital"],
                metodo="esco_taxonomy"
            )

        # 2. Lookup en mapeo manual (67 skills validadas)
        if skill_uri in self.mapeo_skills:
            mapping = self.mapeo_skills[skill_uri]
            return self._build_result(
                L1=mapping["L1"],
                L2=mapping.get("L2"),
                es_digital=mapping.get("es_digital", False),
                metodo="manual"
            )

        # 3. Fallback: Clasificación por heurísticas de keywords
        label_lower = skill_label.lower() if skill_label else ""

        for categoria, data in self.patterns.items():
            if data["pattern"].search(label_lower):
                L1 = data["L1"]
                es_digital = data["es_digital"]

                # Determinar L2 si hay subclasificación
                L2 = self._determine_L2(label_lower, data["L2_subclasificacion"])

                return self._build_result(
                    L1=L1,
                    L2=L2,
                    es_digital=es_digital,
                    metodo="heuristica"
                )

        # 4. Default: Transversal
        return self._build_result(
            L1=self.default["L1"],
            L2=self.default["L2"],
            es_digital=self.default["es_digital"],
            metodo="default"
        )

    def _determine_L2(self, label_lower: str, L2_subclasificacion: Dict) -> Optional[str]:
        """Determina el código L2 basado en keywords."""
        if not L2_subclasificacion:
            return None

        for L2_code, keywords in L2_subclasificacion.items():
            for kw in keywords:
                if kw.lower() in label_lower:
                    return L2_code

        return None

    def _build_result(self, L1: str, L2: Optional[str], es_digital: bool, metodo: str) -> Dict:
        """Construye el resultado con nombres."""
        return {
            "L1": L1,
            "L1_nombre": self.categorias_L1.get(L1, "Desconocido"),
            "L2": L2,
            "L2_nombre": self.categorias_L2.get(L2) if L2 else None,
            "es_digital": es_digital,
            "metodo": metodo
        }

    def categorize_batch(self, skills: List[Dict]) -> List[Dict]:
        """
        Categoriza un lote de skills.

        Args:
            skills: Lista de dicts con 'skill_uri' y 'skill_esco'

        Returns:
            Lista de skills con categorías agregadas
        """
        for skill in skills:
            categoria = self.categorize(
                skill_uri=skill.get("skill_uri", ""),
                skill_label=skill.get("skill_esco", "")
            )
            skill.update(categoria)

        return skills

    def get_summary(self, skills: List[Dict]) -> Dict:
        """
        Genera resumen de categorías para un conjunto de skills.

        Args:
            skills: Lista de skills ya categorizadas

        Returns:
            Dict con conteos por L1, L2, y digitales
        """
        summary = {
            "por_L1": {},
            "por_L2": {},
            "digitales_count": 0,
            "total": len(skills)
        }

        for skill in skills:
            L1 = skill.get("L1", "T")
            L2 = skill.get("L2")
            es_digital = skill.get("es_digital", False)

            # Contar por L1
            if L1 not in summary["por_L1"]:
                summary["por_L1"][L1] = 0
            summary["por_L1"][L1] += 1

            # Contar por L2
            if L2:
                if L2 not in summary["por_L2"]:
                    summary["por_L2"][L2] = 0
                summary["por_L2"][L2] += 1

            # Contar digitales
            if es_digital:
                summary["digitales_count"] += 1

        return summary


# Singleton para evitar recargar config múltiples veces
_categorizer_instance = None

def get_categorizer() -> SkillCategorizer:
    """Obtiene instancia singleton del categorizador."""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = SkillCategorizer()
    return _categorizer_instance


if __name__ == "__main__":
    # Test básico
    categorizer = SkillCategorizer()

    test_skills = [
        ("http://data.europa.eu/esco/skill/programming", "utilizar lenguajes de programación"),
        ("http://example.com/skill/unknown", "trabajar en equipo de forma colaborativa"),
        ("http://example.com/skill/digital", "utilizar software de análisis de datos"),
        ("http://example.com/skill/sales", "técnicas de venta y atención al cliente"),
        ("http://example.com/skill/electrical", "instalación eléctrica residencial"),
    ]

    print("Test de categorización:")
    print("=" * 80)

    for uri, label in test_skills:
        result = categorizer.categorize(uri, label)
        print(f"\nSkill: {label}")
        print(f"  L1: {result['L1']} - {result['L1_nombre']}")
        print(f"  L2: {result['L2']} - {result['L2_nombre']}")
        print(f"  Digital: {result['es_digital']}")
        print(f"  Método: {result['metodo']}")
